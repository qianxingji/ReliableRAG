"""Canonical native original-question retrieval, bound to the accepted empirical pools."""
import argparse
import collections
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from scripts.empirical_retrieval_io import (REPO, OUT, GPU_OUT, POOL, DATASETS, RETRIEVERS, REV, inputs,
    native_retrieval, configure_environment, guard, boundary_record, source_paths, seal, record, require,
    verify_namespace, load, checked)
from scripts.replay_roa_original import write_json
from scripts.verify_roa_artifacts import digest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--gpu-manifest-sha256", required=True)
    args = p.parse_args(); root = args.project_root.resolve()
    require(not OUT.exists(), "Single-use canonical retrieval namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    OUT.mkdir(parents=True, exist_ok=False)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, scientific_fit_calls=0,
        reader_generation_calls=0, fresh_gold_values_materialized=0, datasets={})
    backend = None; boundary = None; counters = collections.Counter(); started = time.perf_counter()
    try:
        environment = configure_environment(OUT); platform_metadata = platform.uname()._asdict()
        import numpy as np
        import torch
        import transformers
        cfg, pre, paths = inputs(root)
        paths += verify_namespace(GPU_OUT, args.gpu_manifest_sha256)
        gpu = load(GPU_OUT / "GPU_PREFLIGHT.json")
        require(gpu["status"] == "PASS_BGE_GPU_SYNTHETIC_ONLY" and gpu["synthetic_embedding_forward_calls"] == 2, "GPU preflight acceptance")
        for e in load(GPU_OUT / "EXECUTABLE_FREEZE.json")["inputs"]:
            require(record(Path(e["path"])) == e, "GPU preflight inputs changed")
        packages = {k: importlib.metadata.version(k) for k in cfg["environment"]["packages"]}
        require(packages == cfg["environment"]["packages"], "Packages changed")
        wrapper, native, nodes = native_retrieval(root)
        config = pre["retriever_config"]
        paths += source_paths() + [Path(sys.executable)]
        bound = [record(q) for q in sorted(set(paths))]
        write_json(OUT / "EXECUTABLE_FREEZE.json", dict(source_commit=commit, command=sys.argv, inputs=bound,
            environment=environment, platform_metadata=platform_metadata, packages=packages, native_ast_nodes=nodes,
            config=config, gpu_preflight_manifest_sha256=args.gpu_manifest_sha256, scope="18000 original-query traces only"))
        boundary = guard(root, OUT, paths)
        backend = native.ExactLocalBGEBackend(model_cache_dir=root / "data/models/huggingface")
        backend._ensure_loaded()
        phase = {"kind": "documents", "dataset": None}
        def forward(model, args):
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled() and not model.training, "Inference boundary")
            counters["embedding_forward_calls"] += 1
            counters["embedding_forward_" + phase["kind"]] += 1
            if phase["kind"] == "documents" and counters["embedding_forward_documents"] % 100 == 0:
                print("DOCUMENT_BATCHES", phase["dataset"], counters["embedding_forward_documents"], flush=True)
        handle = backend.model.register_forward_pre_hook(forward)
        actual = dict(device=str(backend.device), model_class=backend.model.__class__.__name__, revision=backend.model.config._commit_hash,
            dtype=str(next(backend.model.parameters()).dtype), deterministic=torch.are_deterministic_algorithms_enabled(),
            tf32=torch.backends.cuda.matmul.allow_tf32, dimension=backend.dimension, document_batch_size=backend.batch_size,
            query_batch_size=1, eval_mode=not backend.model.training)
        require(actual["revision"] == REV and actual["dtype"] == "torch.bfloat16" and actual["deterministic"] and not actual["tf32"], "Native backend settings")
        class Capture:
            dimension = 768
            def encode_queries(self, texts):
                require(type(texts) is list and len(texts) == 1, "Native query batch")
                counters["embedding_query_rows"] += 1; phase["kind"] = "queries"
                self.last = backend.encode_queries(texts)
                return self.last
        captured = Capture()
        def save_array(path, array):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream: np.save(stream, np.ascontiguousarray(array), allow_pickle=False)
        def rows(path, values):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                for value in values: stream.write(wrapper.canonical(value) + b"\n")
        for dataset in DATASETS:
            docs = [json.loads(x) for x in (POOL / "pools" / (dataset + ".jsonl")).read_text(encoding="utf-8").splitlines()]
            runtime = [json.loads(x) for x in (POOL / "runtime" / (dataset + ".jsonl")).read_text(encoding="utf-8").splitlines()]
            binding = load(POOL / "INDEPENDENT_VALIDATION.json")["datasets"][dataset]
            require(len(runtime) == 2000 and len(docs) == binding["documents"], "Frozen pool coverage")
            corpus = native.Corpus(tuple(native.IndexedDocument(id=d["id"], dataset=dataset, title=d["title"],
                sentences=tuple(d["sentences"]), content_hash=d["content_hash"]) for d in docs), binding["corpus_fingerprint"])
            index = OUT / "indexes" / dataset; index.mkdir(parents=True)
            bm25 = native.FastBM25Index(corpus, native.BM25Config(**config["bm25"]))
            write_json(index / "bm25_structure.json", wrapper.bm25_payload(bm25)); counters["bm25_structure_builds"] += 1
            phase.update(kind="documents", dataset=dataset)
            matrix = backend.encode_documents([d.text for d in corpus.documents])
            counters["embedding_document_rows"] += len(docs)
            require(matrix.shape == (len(docs), 768) and matrix.dtype == np.float32 and np.isfinite(matrix).all(), "Document embeddings")
            save_array(index / "document_embeddings.npy", matrix)
            router = wrapper.bind_router(native, dataset, corpus, captured, matrix, bm25, config)
            dense_queries = []; hybrid_queries = []; ledger = {r: [] for r in RETRIEVERS}; top = []
            for position, row in enumerate(runtime):
                for retriever in RETRIEVERS:
                    ranked = router.rank(row["question"], retriever, 5 if retriever == "hybrid" else 100)
                    value = wrapper.ranking_record(dataset, row["id"], retriever, ranked)
                    ledger[retriever].append(value); top.append(wrapper.top5_record(value))
                    counters["original_retrieval_calls"] += 1; counters["original_" + retriever + "_calls"] += 1
                    if retriever == "dense": dense_queries.append(captured.last[0].copy())
                    if retriever == "hybrid": hybrid_queries.append(captured.last[0].copy())
                require(np.array_equal(dense_queries[-1], hybrid_queries[-1]), "Paired query exact determinism")
                if (position + 1) % 100 == 0: print("QUESTIONS_RETRIEVED", dataset, position + 1, flush=True)
            save_array(index / "query_embeddings_dense.npy", np.stack(dense_queries))
            save_array(index / "query_embeddings_hybrid.npy", np.stack(hybrid_queries))
            for retriever in RETRIEVERS: rows(OUT / "rankings" / (dataset + "_" + retriever + ".jsonl"), ledger[retriever])
            rows(OUT / "top5" / (dataset + ".jsonl"), top)
            result["datasets"][dataset] = dict(questions=2000, traces=6000, pool_documents=len(docs), corpus_fingerprint=corpus.fingerprint)
            del matrix, router, bm25, corpus, docs, runtime, ledger, top, dense_queries, hybrid_queries
        handle.remove(); backend.close(); backend = None
        expected = dict(bm25_structure_builds=3, embedding_document_rows=54716, embedding_forward_documents=3422,
            embedding_query_rows=12000, embedding_forward_queries=12000, embedding_forward_calls=15422,
            original_retrieval_calls=18000, original_bm25_calls=6000, original_dense_calls=6000, original_hybrid_calls=6000)
        require(dict(counters) == expected, "Canonical execution counts")
        for e in bound: require(record(Path(e["path"])) == e, "Canonical input changed")
        require(not boundary["denied"], "Canonical execution denial")
        result.update(status="RETRIEVED_PENDING_INDEPENDENT", actual_backend=actual, source_inputs_unchanged=True)
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    finally:
        if backend is not None: backend.close()
    if boundary is not None: result["execution_boundary"] = boundary_record(boundary)
    result.update(execution_counters=dict(counters), elapsed_seconds=time.perf_counter()-started)
    write_json(OUT / "BUILD_RECEIPT.json", result); seal(OUT, "EXECUTION_MANIFEST.json")
    print(result["status"], result.get("diagnostic", ""), flush=True)
    return 0 if result["status"] == "RETRIEVED_PENDING_INDEPENDENT" else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
