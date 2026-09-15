"""Native canonical reader/repair acquisition and the prospectively fixed bounded replay."""
import argparse
import collections
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import types

from scripts.empirical_runtime_io import (REPO, OUT, GPU_OUT, PREPARATION, bound_inputs, native_runtime,
    restore_dataset, make_reader, check_models, source_paths, read_rows, record, require, load, verify_namespace)
from scripts.empirical_runtime_contract import canonical, sha_json, trace_key
from scripts.empirical_runtime_guard import guard
from scripts.empirical_retrieval_io import configure_environment, boundary_record, seal
from scripts.replay_roa_original import write_json
from scripts.verify_roa_artifacts import digest


class DurableLedger:
    def __init__(self, path):
        self.stream = path.open("xb"); self.count = 0
    def append(self, row):
        self.stream.write(canonical(row)+b"\n"); self.stream.flush(); os.fsync(self.stream.fileno()); self.count += 1
    def close(self):
        if not self.stream.closed: self.stream.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--preparation-manifest-sha256", required=True)
    p.add_argument("--gpu-manifest-sha256", required=True)
    p.add_argument("--mode", choices=("canonical", "replay"), required=True)
    args = p.parse_args(); root = args.project_root.resolve(); base = OUT if args.mode == "canonical" else OUT / "replay"
    require(not base.exists(), "No scientific pass overwrite or automatic retry")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    base.mkdir(parents=True, exist_ok=False)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, mode=args.mode, scientific_fit_calls=0,
        fresh_gold_values_materialized=0, original_question_retrieval_calls=0, document_embedding_calls=0, bm25_structure_rebuild_calls=0)
    reader = bge = boundary = None; streams = {}; counters = collections.Counter(); failclosed = collections.Counter()
    completed = 0; phase = dict(stage="initializing", position=None); started = time.perf_counter()
    try:
        environment = configure_environment(base); platform_metadata = platform.uname()._asdict()
        import torch
        import transformers
        cfg, paths = bound_inputs(root, args.preparation_manifest_sha256)
        paths += verify_namespace(GPU_OUT, args.gpu_manifest_sha256)
        require(load(GPU_OUT / "GPU_PREFLIGHT.json")["status"] == "PASS_JOINT_READER_GPU_SYNTHETIC_ONLY", "Joint GPU preflight required")
        for e in load(GPU_OUT / "EXECUTABLE_FREEZE.json")["inputs"]:
            require(record(Path(e["path"])) == e, "Joint preflight source/input changed")
        wrapper, native, nodes, prefix = native_runtime(root)
        traces = read_rows(PREPARATION / ("TRACE_MANIFEST_PRIVATE.jsonl" if args.mode == "canonical" else "REPLAY_SUBSET_PRIVATE.jsonl"))
        expected = 18000 if args.mode == "canonical" else 180
        require(len(traces) == expected, "Frozen pass count")
        reference = {}; names = ("generation_receipts.jsonl", "repair_bindings.jsonl", "branch_provenance.jsonl", "canonical_branches.jsonl")
        if args.mode == "replay":
            previous = load(OUT / "BUILD_RECEIPT.json")
            require(previous["status"] == "GENERATED_PENDING_REPLAY_AND_INDEPENDENT", "Canonical completion required")
            manifest = load(OUT / "EXECUTION_MANIFEST.json")
            paths.append(OUT / "EXECUTION_MANIFEST.json")
            for e in manifest["files"]:
                q = OUT / e["path"]; require(digest(q) == e["sha256"] and q.stat().st_size == e["size_bytes"], "Canonical payload changed")
                paths.append(q)
            keys = {trace_key(t) for t in traces}
            for name in names:
                selected = {}
                with (OUT / name).open(encoding="utf-8") as reference_stream:
                    for line in reference_stream:
                        row = json.loads(line)
                        if trace_key(row) in keys:
                            key = (*trace_key(row), row["stage"]) if name == "generation_receipts.jsonl" else trace_key(row)
                            require(key not in selected, "Duplicate canonical reference")
                            selected[key] = row
                reference[name] = selected
        paths += source_paths() + [Path(sys.executable)]
        records = [record(p) for p in sorted(set(paths))]
        write_json(base / "EXECUTABLE_FREEZE.json", dict(source_commit=commit, command=sys.argv, inputs=records,
            environment=environment, platform_metadata=platform_metadata, native_ast_nodes=nodes, generation_boundary=prefix,
            runtime_config_sha256=cfg["runtime_config_sha256"], mode=args.mode, expected_traces=expected,
            preparation_manifest_sha256=args.preparation_manifest_sha256, gpu_manifest_sha256=args.gpu_manifest_sha256))
        boundary = guard(root, base, paths)
        bge = native.ExactLocalBGEBackend(model_cache_dir=root / "data/models/huggingface"); bge._ensure_loaded()
        reader = make_reader(native, root); reader._ensure_loaded(); actual = check_models(reader, bge, cfg)
        def reader_forward(model, args):
            require(phase["stage"] in {"a0", "repair_query", "a1"}, "Reader stage boundary")
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled() and not model.training, "Reader inference only")
            counters["qwen_forward_calls"] += 1; counters[phase["stage"]+"_forward_calls"] += 1
        def bge_forward(model, args):
            require(phase["stage"] == "repair_retrieval" and torch.is_inference_mode_enabled() and not torch.is_grad_enabled() and not model.training, "Repair embedding boundary")
            counters["bge_query_forward_calls"] += 1
        qhook = reader.model.register_forward_pre_hook(reader_forward); bhook = bge.model.register_forward_pre_hook(bge_forward)
        class QueryOnly:
            dimension = 768
            def encode_queries(self, texts):
                require(phase["stage"] == "repair_retrieval" and type(texts) is list and len(texts) == 1, "Single repair query only")
                counters["repair_query_embedding_calls"] += 1; self.last = bge.encode_queries(texts); return self.last
            def encode_documents(self, *args, **kwargs): raise RuntimeError("Document re-embedding forbidden")
        backend = QueryOnly(); runner = native.ProspectiveRunner(); runner.protocol = native.FrozenProtocol()
        streams = {name: DurableLedger(base / name) for name in names}
        def append(name, row):
            streams[name].append(row)
            if args.mode == "replay":
                key = (*trace_key(row), row["stage"]) if name == "generation_receipts.jsonl" else trace_key(row)
                require(key in reference[name] and canonical(row) == canonical(reference[name][key]), "Bounded runtime replay mismatch; preserve both")
        def generate(trace, question, evidence, stage):
            phase["stage"] = stage; before = counters["qwen_forward_calls"]; counters[stage+"_generation_calls"] += 1
            key = native.TraceKey("qwen", trace["dataset"], trace["sample_id"], trace["retriever"])
            value = (reader.generate_repair_query(key=key, question=question, evidence=evidence) if stage == "repair_query" else
                reader.generate_answer(key=key, question=question, evidence=evidence, state="e0" if stage == "a0" else "e1"))
            rec = dict(dataset=trace["dataset"], retriever=trace["retriever"], sample_id=trace["sample_id"], position=trace["position"], stage=stage,
                **reader._generation_capture, parsed_text=value.search_query if stage == "repair_query" else value.parsed_text,
                parser_fallback=value.parser_fallback if stage == "repair_query" else None, logical_generation_calls=1,
                qwen_forward_calls=counters["qwen_forward_calls"]-before, runtime_config_sha256=cfg["runtime_config_sha256"])
            append("generation_receipts.jsonl", rec); counters[stage+"_generation_completed"] += 1
            if stage != "repair_query":
                runner._validate_generation(value, stage, evidence)
                if not value.parsed_text: failclosed["empty_"+stage+"_retained"] += 1
            elif value.parser_fallback: failclosed["native_repair_parser_fallback_retained"] += 1
            return value
        current = None; data = None
        for trace in traces:
            dataset, retriever, sid = trace_key(trace); phase["position"] = trace["position"]
            if dataset != current:
                data = None; data = restore_dataset(dataset, native, backend); current = dataset
            question = data["questions"][sid]; e0 = wrapper.original_evidence(trace, data, native)
            a0 = generate(trace, question, e0, "a0"); query = generate(trace, question, e0, "repair_query")
            phase["stage"] = "repair_retrieval"; data["components"].clear(); backend.last = None
            counters["repair_retrieval_calls"] += 1; counters["repair_"+retriever+"_calls"] += 1; ranked = []
            def rank(query_text, method, depth):
                rows = data["router"].rank(query_text, method, depth); ranked.extend(rows); return rows
            e1, inserted, diagnostics = runner._repair(types.SimpleNamespace(rank=rank), query, retriever, e0)
            components = data["components"]
            require(len(components) == (2 if retriever == "hybrid" else 1), "Native component count")
            repair = dict(dataset=dataset, retriever=retriever, sample_id=sid, position=trace["position"],
                query_sha256=wrapper.tsha(query.search_query), ranking=[dict(document_id=r.document_id, rank=r.rank, score=float(r.score)) for r in ranked],
                component_rankings=dict(bm25=components[0], dense=components[1]) if retriever == "hybrid" else {retriever: components[0]},
                dense_query_vector=None if backend.last is None else backend.last[0].tolist(), e0_ids=[x.document_id for x in e0],
                e1_ids=[x.document_id for x in e1], inserted_document_id=inserted.document_id, inserted_candidate_rank=inserted.rank,
                replaced_document_id=e0[4].document_id, replacement_position_zero_based=4, requested_depth=50, repair_retrieval_calls=1,
                pool_sha256=data["binding"]["pool_sha256"], fail_closed_reason=None)
            append("repair_bindings.jsonl", repair); counters["repair_retrieval_completed"] += 1
            a1 = generate(trace, question, e1, "a1")
            branch = dict(dataset=dataset, retriever=retriever, sample_id=sid, question=question, a0=a0.parsed_text, a1=a1.parsed_text,
                evidence0=[x.text for x in e0], evidence1=[x.text for x in e1])
            require(set(branch) == wrapper.BRANCH_FIELDS, "Method-independent branch schema")
            provenance = dict(dataset=dataset, retriever=retriever, sample_id=sid, position=trace["position"],
                original_top5_row_sha256=trace["original_top5_row_sha256"], e0=[x.as_private_dict() for x in e0], e1=[x.as_private_dict() for x in e1],
                question_sha256=wrapper.tsha(question), canonical_row_sha256=sha_json(branch), runtime_config_sha256=cfg["runtime_config_sha256"],
                repair_binding_row_sha256=sha_json(repair), pool_sha256=data["binding"]["pool_sha256"])
            append("branch_provenance.jsonl", provenance); append("canonical_branches.jsonl", branch); completed += 1
            if completed % 10 == 0: print("RUNTIME_TRACES", args.mode, completed, expected, flush=True)
        require(completed == expected and all(counters[s+"_generation_completed"] == expected for s in ("a0", "repair_query", "a1")), "Complete generations")
        require(counters["repair_retrieval_completed"] == expected and counters["repair_query_embedding_calls"] == counters["bge_query_forward_calls"] == expected*2//3, "Repair counts")
        for stream in streams.values(): stream.close()
        qhook.remove(); bhook.remove(); reader.close(); bge.close(); reader = bge = None
        for e in records: require(record(Path(e["path"])) == e, "Runtime input/source changed")
        require(not boundary["denied"], "Runtime execution boundary")
        result.update(status="GENERATED_PENDING_REPLAY_AND_INDEPENDENT" if args.mode == "canonical" else "PASS_BOUNDED_REPLAY_PENDING_INDEPENDENT",
            actual_backend=actual, native_ast_nodes=nodes, generation_boundary=prefix, source_inputs_unchanged=True,
            artifacts=[record(base/name) for name in names], generation_failure_count=0, repair_failure_count=0,
            stratum_counts={d:{r:sum((t["dataset"],t["retriever"])==(d,r) for t in traces) for r in ("bm25","dense","hybrid")}
                            for d in ("hotpotqa","2wikimultihopqa","musique")})
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    finally:
        for stream in streams.values(): stream.close()
        if reader is not None: reader.close()
        if bge is not None: bge.close()
    if boundary is not None: result["execution_boundary"] = boundary_record(boundary)
    result.update(completed_traces=completed, phase=phase, execution_counters=dict(counters), fail_closed_counts=dict(failclosed), elapsed_seconds=time.perf_counter()-started)
    write_json(base / "BUILD_RECEIPT.json", result); seal(base, "EXECUTION_MANIFEST.json")
    print(result["status"], result.get("diagnostic", "")); return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
