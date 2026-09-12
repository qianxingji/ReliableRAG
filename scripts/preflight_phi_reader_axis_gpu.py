"""Single-use invented-only Phi generation and likelihood GPU preflight."""
from __future__ import annotations

import argparse
import gc
import importlib.metadata
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from scripts.empirical_retrieval_io import import_file
from scripts.empirical_runtime_io import native_runtime
from scripts.phi_reader_preflight_common import (
    EXPECTED_WEIGHT_BYTES,
    OUT,
    PHI_MODEL,
    PHI_RELATIVE,
    PHI_REVISION,
    REPO,
    RUNTIME_SEED,
    compact_evidence,
    configure_environment,
    configure_torch,
    invented_evidence,
    invented_evidence_rows,
    load,
    object_sha,
    record,
    require,
    seal,
    validate_logit_witness,
    write_json,
)
from scripts.phi_reader_preflight_guard import compact as compact_boundary
from scripts.phi_reader_preflight_guard import install as install_boundary


class LogitWitness:
    """Observe selected answer logits and normalizers without changing output."""

    def __init__(self, scorer):
        self.scorer = scorer
        self.current = None
        self.records = []
        self.forward_calls = 0
        self.hook = scorer.model.register_forward_hook(self._forward, with_kwargs=True)

    def _forward(self, model, args, kwargs, output):
        import torch

        require(self.current is not None, "unexpected Phi likelihood forward")
        prepared = self.current
        ids = kwargs["input_ids"]
        mask = kwargs["attention_mask"]
        positions_all = kwargs["position_ids"]
        require(ids.shape[0] == 1 and ids[0].tolist() == prepared["input_ids"], "likelihood input IDs")
        require(mask[0].tolist() == [1] * len(prepared["input_ids"]), "likelihood attention mask")
        require(positions_all[0].tolist() == list(range(len(prepared["input_ids"]))), "likelihood position IDs")
        require(kwargs["use_cache"] is False and torch.is_inference_mode_enabled() and not torch.is_grad_enabled(), "likelihood inference mode")
        prompt = len(prepared["prompt_ids"])
        answer = len(prepared["answer_ids"])
        positions = torch.arange(prompt - 1, prompt + answer - 1, device=ids.device)
        targets = ids[0, prompt : prompt + answer]
        logits = output.logits[0, positions, :].float()
        chosen = logits.gather(1, targets[:, None]).squeeze(1)
        normalizers = torch.logsumexp(logits, dim=-1)
        values = chosen - normalizers
        self.forward_calls += 1
        row = {
            "forward_ordinal": self.forward_calls,
            "cache_key": prepared["cache_key"],
            "input_token_ids": prepared["input_ids"],
            "attention_mask": mask[0].tolist(),
            "position_ids": positions_all[0].tolist(),
            "answer_token_ids": prepared["answer_ids"],
            "answer_prediction_positions": positions.tolist(),
            "chosen_logits": chosen.cpu().tolist(),
            "log_normalizers": normalizers.cpu().tolist(),
            "token_log_probabilities": values.cpu().tolist(),
            "prompt_token_count": prompt,
            "answer_token_count": answer,
            "truncation": bool(prepared["truncation"]),
            "prompt_sha256": prepared["prompt_sha256"],
            "answer_sha256": prepared["answer_sha256"],
            "evidence_hash": prepared["evidence_hash"],
            "model_revision": self.scorer.resolved_revision,
        }
        validate_logit_witness(row)
        self.records.append(row)
        return None

    def score_one(self, item):
        prepared = self.scorer._prepare(item)
        exists = self.scorer._cache_path(prepared["cache_key"]).exists()
        before = self.forward_calls
        self.current = prepared
        try:
            result = self.scorer.score([item])[0]
        finally:
            self.current = None
        require(self.forward_calls - before == (0 if exists else 1), "likelihood cache/forward chronology")
        return prepared, result

    def close(self):
        self.hook.remove()


def source_paths(original: Path, nodes: list[dict]) -> list[Path]:
    paths = [
        REPO / "scripts/phi_reader_preflight_common.py",
        REPO / "scripts/phi_reader_preflight_guard.py",
        REPO / "scripts/preflight_phi_reader_axis_gpu.py",
        REPO / "scripts/validate_phi_reader_axis_preflight.py",
        REPO / "docs/cas_q2/PHI_READER_REPLICATION_PROTOCOL_V1.md",
        REPO / "docs/cas_q2/PHI_READER_PREFLIGHT_EXECUTION_CONTRACT.md",
        REPO / "docs/cas_q2/P0_3_READER_AXIS_AVAILABILITY_RESULTS.json",
        REPO / "scripts/empirical_runtime_io.py",
        original / "src/scoring/reader_likelihood.py",
        original / "src/phase10/adapters.py",
        original / "src/phase10/contracts.py",
        original / "src/generation/parsing.py",
        original / "prompts/baseline_v1.txt",
        original / "prompts/repair_missing_v1.txt",
        original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/native_runtime.py",
        original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/runtime_support.py",
        original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json",
        original / "outputs/daa_v2_fresh_v1/retrieval_freeze/native_retrieval.py",
        original / "outputs/daa_v2_fresh_v1/retrieval_freeze/retrieval_support.py",
        REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1/SHA256_MANIFEST.json",
    ]
    for row in nodes:
        path = original / row.get("path", "")
        if path.is_file():
            paths.append(path)
    paths.extend(path for path in (original / PHI_RELATIVE).iterdir() if path.is_file())
    return sorted(set(path.resolve() for path in paths))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    original = args.project_root.resolve()
    require(not OUT.exists(), "single-use Phi preflight namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit Phi preflight first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    OUT.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    result = {
        "status": "FAIL",
        "cas_q2_status": "NOT READY",
        "source_commit": commit,
        "model_loads": 0,
        "logical_generation_calls": 0,
        "generation_forward_calls": 0,
        "likelihood_forward_calls": 0,
        "benchmark_rows_read": 0,
        "scientific_fit_calls": 0,
        "gold_reads": 0,
    }
    boundary = None
    reader = scorer = observer = None
    records = []
    try:
        environment = configure_environment(OUT)
        import torch
        import transformers

        configure_torch(torch)
        wrapper, native, nodes, generation_boundary = native_runtime(original)
        likelihood_module = import_file("phi_reader_likelihood_source", original / "src/scoring/reader_likelihood.py")
        paths = source_paths(original, nodes)
        records = [record(path) for path in paths]
        snapshot_records = [row for row in records if Path(row["path"]).is_relative_to(original / PHI_RELATIVE)]
        index = load(original / PHI_RELATIVE / "model.safetensors.index.json")
        require(index["metadata"]["total_size"] == EXPECTED_WEIGHT_BYTES and len(snapshot_records) == 20, "pinned Phi snapshot inventory")
        write_json(OUT / "EXECUTABLE_FREEZE.json", {
            "source_commit": commit,
            "command": sys.argv,
            "environment": environment,
            "versions": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "numpy", "safetensors")},
            "inputs": records,
            "native_ast_nodes": nodes,
            "generation_boundary": generation_boundary,
            "reader": {"model": PHI_MODEL, "revision": PHI_REVISION, "runtime_seed": RUNTIME_SEED},
            "scope": "Four invented generations and two invented likelihood forwards; zero benchmark/Gold/fit",
        })
        boundary = install_boundary(original, OUT, paths)

        reader = native.HFProspectiveReaderAdapter(
            reader="phi",
            model_cache_dir=original / "data/models/huggingface",
            answer_prompt_path=original / "prompts/baseline_v1.txt",
            repair_prompt_path=original / "prompts/repair_missing_v1.txt",
            max_answer_tokens=48,
            max_query_tokens=64,
            maximum_likelihood_length=8192,
            context_budget_characters=16000,
        )
        reader._ensure_loaded()
        result["model_loads"] += 1
        require(reader.model.__class__.__name__ == "Phi3ForCausalLM", "Phi model class")
        require(reader.model.config._commit_hash == PHI_REVISION and str(next(reader.model.parameters()).dtype) == "torch.bfloat16", "Phi revision/dtype")
        generation_forwards = 0

        def count_generation(model, args, kwargs):
            nonlocal generation_forwards
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled() and not model.training, "generation inference mode")
            generation_forwards += 1

        hook = reader.model.register_forward_pre_hook(count_generation, with_kwargs=True)
        short = invented_evidence(native)
        long = invented_evidence(native, long=True)
        key = native.TraceKey("phi", "hotpotqa", "invented-phi-reader-preflight", "bm25")
        observations = []
        for label, kind, evidence in (("short_1", "answer", short), ("short_2", "answer", short), ("repair", "query", short), ("long", "answer", long)):
            if kind == "answer":
                value = reader.generate_answer(key=key, question="In the invented toy scene, what color is the paper cog?", evidence=evidence, state="e0")
            else:
                value = reader.generate_repair_query(key=key, question="In the invented toy scene, what color is the paper cog?", evidence=evidence)
            result["logical_generation_calls"] += 1
            observations.append({"label": label, "kind": kind, "long_evidence": evidence is long,
                "capture": dict(reader._generation_capture), "result": asdict(value)})
        hook.remove()
        result["generation_forward_calls"] = generation_forwards
        require(observations[0]["capture"] == observations[1]["capture"], "exact repeated greedy generation capture")
        repeat_a = {k: v for k, v in observations[0]["result"].items() if k != "latency_ms"}
        repeat_b = {k: v for k, v in observations[1]["result"].items() if k != "latency_ms"}
        require(repeat_a == repeat_b, "exact repeated parsed generation")
        require(observations[-1]["capture"]["render"]["context_truncated"] is True, "16k character boundary exercised")
        generation_peak = int(torch.cuda.max_memory_allocated())
        write_json(OUT / "GENERATION_WITNESSES.json", {"observations": observations,
            "invented_evidence_hashes": {"short_rows": object_sha(invented_evidence_rows()),
                "long_rows": object_sha(invented_evidence_rows(long=True))}})
        reader.close()
        reader = None
        gc.collect()
        torch.cuda.empty_cache()

        configure_torch(torch)
        config = {
            "model_name": PHI_MODEL,
            "revision": PHI_REVISION,
            "model_cache_dir": str(original / "data/models/huggingface"),
            "cache_dir": str(OUT / "cache/likelihood"),
            "answer_prompt_path": str(original / "prompts/baseline_v1.txt"),
            "dtype": "bfloat16",
            "batch_size": 1,
            "max_length": 8192,
            "context_budget_characters": 16000,
            "require_cuda": True,
        }
        scorer = likelihood_module.ReaderLikelihoodScorer(config)
        result["model_loads"] += 1
        require(scorer.model.__class__.__name__ == "Phi3ForCausalLM" and scorer.resolved_revision == PHI_REVISION, "Phi likelihood model identity")
        observer = LogitWitness(scorer)
        short_item = {"question": "In the invented toy scene, what color is the paper cog?", "answer": "silver", "evidence": invented_evidence_rows()}
        long_item = {"question": "In the invented toy scene, what color is the paper cog?", "answer": "silver", "evidence": invented_evidence_rows(long=True)}
        scored = []
        for label, item in (("short_miss", short_item), ("short_hit", short_item), ("long_miss", long_item)):
            prepared, value = observer.score_one(item)
            scored.append({"label": label, "prepared": {k: prepared[k] for k in ("prompt_ids", "answer_ids", "input_ids", "prompt_sha256", "evidence_ids", "evidence_hash", "answer_sha256", "cache_key", "truncation")}, "result": asdict(value)})
        result["likelihood_forward_calls"] = observer.forward_calls
        require(scorer.calls == observer.forward_calls == 2 and scorer.cache_hits == 1, "two misses and one exact cache hit")
        require(len(scored[-1]["prepared"]["input_ids"]) == 8192 and scored[-1]["prepared"]["truncation"], "8192-token scoring boundary exercised")
        require(scored[1]["result"]["cache_hit"] is True and scored[1]["result"]["latency_seconds"] == 0.0, "cache-hit receipt")
        write_json(OUT / "LIKELIHOOD_WITNESSES.json", {"config": {k: v for k, v in config.items() if k not in {"cache_dir", "model_cache_dir"}},
            "model_metadata": scorer.metadata, "scored": scored, "forward_witnesses": observer.records})
        observer.close()
        observer = None
        scorer.model = None
        scorer = None
        gc.collect()
        torch.cuda.empty_cache()

        for row in records:
            require(record(Path(row["path"])) == row, "preflight input changed")
        require(boundary is not None and not boundary["denied"], "Phi preflight boundary")
        likelihood_peak = int(torch.cuda.max_memory_allocated())
        result.update(status="PASS_PHI_READER_GPU_INVENTED_ONLY", invented_only=True,
            exact_repeat_generation=True, long_generation_character_boundary=True,
            long_likelihood_token_boundary=8192, likelihood_cache_hits=1,
            generation_peak_allocated_cuda_bytes=generation_peak,
            likelihood_peak_allocated_cuda_bytes=likelihood_peak,
            peak_allocated_cuda_bytes=max(generation_peak, likelihood_peak),
            source_inputs_unchanged=True,
            limitation="Invented compatibility only; no benchmark execution, quality result, or long-run memory guarantee")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    finally:
        if observer is not None:
            observer.close()
        if reader is not None:
            reader.close()
        if scorer is not None:
            scorer.model = None
        if boundary is not None:
            result["execution_boundary"] = compact_boundary(boundary)
        result["elapsed_seconds"] = time.perf_counter() - started
        write_json(OUT / "BUILD_RECEIPT.json", result)
        seal(OUT)
    print(result["status"], result.get("diagnostic", ""), flush=True)
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
