"""Run/resume the BGE-only development repair-retrieval stage."""

from __future__ import annotations

import argparse
import collections
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import types

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    DurableLedger, read_jsonl, record, recover_or_execute, sha256,
    validate_development_binding, verify_manifest, write_json_durable,
)
from scripts.run_mistral_development_a0_query import (
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256, EXPECTED_INPUT_LEDGER_SHA256,
    EXPECTED_POOL_MANIFEST_SHA256, EXPECTED_RETRIEVAL_MANIFEST_SHA256,
    EXPECTED_RUNTIME_MANIFEST_SHA256, acquire_gpu_mutex, evidence_rows,
    load_original_native, validate_manifest_pin,
)
from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal, object_sha256, require, text_sha256,
)


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q3"
EXPECTED_TRACES = 13_500
EXPECTED_DENSE_QUERY_FORWARDS = 9_000
MIN_DISK_FREE_BYTES = 30 * 1024 ** 3
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"


def query_object(native, payload: dict):
    render = payload["render"]
    return native.GeneratedRepairQuery(
        payload["raw_text"], payload["parsed_text"], payload["parser_fallback"],
        payload["input_tokens"], payload["output_tokens"], render["context_truncated"],
        render["context_budget_characters"], tuple(render["ordered_passed_document_ids"]),
        tuple(render["per_document_truncated"]), 0.0, False, False, 1,
    )


def validate_repair_payload(payload: dict, trace: dict) -> None:
    require(payload["dataset"] == trace["dataset"] and payload["retriever"] == trace["retriever"]
            and payload["sample_id"] == trace["sample_id"] and payload["position"] == trace["position"],
            "REPAIR_IDENTITY")
    ranking = payload["ranking"]
    require(len(ranking) == 50 and [row["rank"] for row in ranking] == list(range(1, 51))
            and len({row["document_id"] for row in ranking}) == 50, "REPAIR_RANKING")
    require(len(payload["e0_ids"]) == len(payload["e1_ids"]) == 5
            and payload["e0_ids"] == trace["original_top5_ids"]
            and payload["e1_ids"][:4] == payload["e0_ids"][:4]
            and payload["e1_ids"][4] == payload["inserted_document_id"]
            and payload["replaced_document_id"] == payload["e0_ids"][4]
            and payload["inserted_document_id"] not in payload["e0_ids"], "REPAIR_REPLACEMENT")
    inserted_rows = [row for row in ranking if row["document_id"] == payload["inserted_document_id"]]
    require(len(inserted_rows) == 1
            and inserted_rows[0]["rank"] == payload["inserted_candidate_rank"],
            "REPAIR_INSERTED_RANK")
    expected_components = {"bm25", "dense"} if trace["retriever"] == "hybrid" else {trace["retriever"]}
    require(set(payload["component_rankings"]) == expected_components, "REPAIR_COMPONENTS")
    require((payload["dense_query_vector"] is None) == (trace["retriever"] == "bm25")
            and (payload["dense_query_vector"] is None or len(payload["dense_query_vector"]) == 768),
            "REPAIR_VECTOR")
    require(payload["requested_depth"] == 50 and payload["replacement_position_zero_based"] == 4
            and payload["repair_retrieval_calls"] == 1 and payload["fail_closed_reason"] is None,
            "REPAIR_CONTROLS")


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            row = record(path); row["path"] = path.relative_to(stage_output).as_posix(); files.append(row)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files,
        "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    original = args.project_root.resolve(); root = (OUTPUT_PARENT / args.output_name).resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve() and root.parent == OUTPUT_PARENT.resolve(), "FIXED_ROOTS")
    a0_stage = root / "a0_query"; validation = root / "a0_query_validation/VALIDATION.json"
    require((a0_stage / "SHA256_MANIFEST.json").is_file() and validation.is_file(), "A0_QUERY_ACCEPTANCE_REQUIRED")
    a0_receipt = json.loads((a0_stage / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    validation_receipt = json.loads(validation.read_text(encoding="utf-8"))
    require(a0_receipt["status"] == "PASS_MISTRAL_DEVELOPMENT_A0_QUERY_PENDING_INDEPENDENT"
             and validation_receipt["status"] == "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY",
             "A0_QUERY_STATUS")
    verify_manifest(a0_stage, sha256(a0_stage / "SHA256_MANIFEST.json"))
    require(validation_receipt["producer_receipt_sha256"] == sha256(a0_stage / "STAGE_RECEIPT.json")
            and validation_receipt["generation_receipts_sha256"] == sha256(a0_stage / "GENERATION_RECEIPTS.jsonl")
            and validation_receipt["call_journal_sha256"] == sha256(a0_stage / "CALL_JOURNAL.jsonl"),
            "A0_QUERY_VALIDATION_BINDING")
    stage_output = root / "repair"
    require(not any((stage_output / name).exists() for name in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json", "SHA256_MANIFEST.json")), "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    started = time.perf_counter(); mutex = bge = journal = ledger = None; completed = 0
    modes = collections.Counter(); counters = collections.Counter()
    result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "repair", "gold_values_read": 0, "scientific_fits": 0,
        "test_rows_read": 0, "mistral_model_loads": 0, "nli_model_loads": 0,
    }
    try:
        if not args.resume: stage_output.mkdir(parents=True, exist_ok=False)
        import psutil
        require(psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES, "DISK_FREE_ADMISSION")
        mutex = acquire_gpu_mutex()
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        require(sha256(input_freeze / "SHA256_MANIFEST.json") == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
                "INPUT_FREEZE_MANIFEST")
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256, "INPUT_FREEZE_LEDGER")
        runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
        input_records = [
            validate_manifest_pin(runtime_root / "SHA256_MANIFEST.json", EXPECTED_RUNTIME_MANIFEST_SHA256),
            validate_manifest_pin(original / "outputs/daa_v2_fresh_v1/pool_freeze/SHA256_MANIFEST.json", EXPECTED_POOL_MANIFEST_SHA256),
            validate_manifest_pin(original / "outputs/daa_v2_fresh_v1/retrieval_freeze/SHA256_MANIFEST.json", EXPECTED_RETRIEVAL_MANIFEST_SHA256),
            record(frozen_ledger), record(a0_stage / "SHA256_MANIFEST.json"), record(validation),
            record(Path(__file__)), record(REPO / "scripts/mistral_development_acquisition_common.py"),
            record(REPO / "scripts/run_mistral_development_a0_query.py"),
            record(REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_ACQUISITION_PROTOCOL_2026-09-17.md"),
        ]
        freeze = {"status": "FROZEN_BEFORE_FORMAL_REPAIR", "source_commit": commit,
                  "expected_traces": EXPECTED_TRACES, "expected_dense_query_forwards": EXPECTED_DENSE_QUERY_FORWARDS,
                  "inputs": input_records,
                  "scope": "development same-retriever repair only; Mistral/NLI/Gold/test/fit forbidden"}
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume: require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze, "RESUME_FREEZE_MISMATCH")
        else: write_json_durable(freeze_path, freeze)
        loader, native, nodes, _boundary = load_original_native(original)
        traces = list(read_jsonl(runtime_root / "trace_manifest.jsonl"))
        frozen_rows = list(read_jsonl(frozen_ledger))
        development = validate_development_binding(traces, frozen_rows)
        role_by_position = {row["position"]: row["role"] for row in development}
        a0_rows = list(read_jsonl(a0_stage / "GENERATION_RECEIPTS.jsonl"))
        query_map = {row["operation_key"]: row["payload"] for row in a0_rows if row["operation"] == "repair_query"}
        require(len(query_map) == EXPECTED_TRACES, "QUERY_COUNT")
        journal = DurableOperationJournal(stage_output / "CALL_JOURNAL.jsonl", resume=args.resume)
        ledger = DurableLedger(stage_output / "REPAIR_BINDINGS.jsonl", resume=args.resume)
        bge = native.ExactLocalBGEBackend(model_cache_dir=original / "data/models/huggingface")
        bge._ensure_loaded(); counters["bge_model_loads"] = 1
        require(bge.model.config._commit_hash == BGE_REVISION and bge.dimension == 768, "BGE_IDENTITY")

        class QueryOnlyBackend:
            dimension = 768
            def __init__(self): self.last = None
            def encode_queries(self, texts):
                require(type(texts) is list and len(texts) == 1, "SINGLE_QUERY")
                counters["bge_query_forwards_current_process"] += 1
                self.last = bge.encode_queries(texts); return self.last
            def encode_documents(self, *_args, **_kwargs):
                raise RuntimeError("DOCUMENT_REEMBEDDING_FORBIDDEN")

        backend = QueryOnlyBackend(); runner = native.ProspectiveRunner(); runner.protocol = native.FrozenProtocol()
        current_dataset = None; data = None
        for trace in traces:
            dataset, retriever, sample_id = trace["dataset"], trace["retriever"], trace["sample_id"]
            if dataset != current_dataset:
                data = loader.restore_dataset(dataset, native, backend); current_dataset = dataset
            e0 = loader.original_evidence(trace, data, native); query_payload = query_map[f"{trace['position']:05d}:repair_query"]
            query = query_object(native, query_payload)
            key = f"{trace['position']:05d}:repair_retrieval"
            input_value = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                           "position": trace["position"], "query": query.search_query,
                           "e0": evidence_rows(e0), "depth": 50, "replacement_position_zero_based": 4}
            input_hash = object_sha256(input_value)
            def execute(trace=trace, query=query, e0=e0):
                data["components"].clear(); backend.last = None; ranking = []
                def rank(query_text, method, depth):
                    require(method == retriever and depth == 50, "SAME_RETRIEVER_DEPTH")
                    value = data["router"].rank(query_text, method, depth); ranking.extend(value); return value
                e1, inserted, _diagnostics = runner._repair(types.SimpleNamespace(rank=rank), query, retriever, e0)
                components = data["components"]
                require(len(components) == (2 if retriever == "hybrid" else 1), "COMPONENT_COUNT")
                payload = {
                    "dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                    "position": trace["position"], "role": role_by_position[trace["position"]],
                    "query_sha256": text_sha256(query.search_query),
                    "ranking": [{"document_id": row.document_id, "rank": row.rank, "score": float(row.score)} for row in ranking],
                    "component_rankings": ({"bm25": components[0], "dense": components[1]}
                        if retriever == "hybrid" else {retriever: components[0]}),
                    "dense_query_vector": None if backend.last is None else backend.last[0].tolist(),
                    "e0_ids": [row.document_id for row in e0], "e1_ids": [row.document_id for row in e1],
                    "inserted_document_id": inserted.document_id, "inserted_candidate_rank": inserted.rank,
                    "replaced_document_id": e0[4].document_id, "replacement_position_zero_based": 4,
                    "requested_depth": 50, "repair_retrieval_calls": 1,
                    "pool_sha256": data["binding"]["pool_sha256"], "fail_closed_reason": None,
                }
                validate_repair_payload(payload, trace); return payload
            row, mode = recover_or_execute(
                journal=journal, ledger=ledger, key=key, operation="repair_retrieval",
                input_sha256=input_hash, execute=execute,
            )
            validate_repair_payload(row["payload"], trace); modes[mode] += 1; completed += 1
            if completed % 10 == 0:
                print(json.dumps({"stage": "repair", "completed_traces": completed,
                                  "expected_traces": EXPECTED_TRACES}, sort_keys=True), flush=True)
        require(completed == EXPECTED_TRACES and len(ledger.rows) == EXPECTED_TRACES, "COMPLETE_COUNTS")
        logical_dense_queries = sum(
            row["payload"]["retriever"] in {"dense", "hybrid"} for row in ledger.rows
        )
        require(logical_dense_queries == EXPECTED_DENSE_QUERY_FORWARDS, "BGE_LOGICAL_QUERY_COUNT")
        require(journal.pending is None and len(journal.completed) == EXPECTED_TRACES, "JOURNAL_COUNT")
        bge.close(); bge = None; counters["bge_model_unloads"] = 1
        import torch
        gc.collect(); torch.cuda.empty_cache(); allocated_after = int(torch.cuda.memory_allocated(0))
        require(allocated_after < 1024 ** 3, "BGE_NOT_RELEASED")
        journal.close(); journal = None; ledger.close(); ledger = None
        for item in input_records: require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started; require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(status="PASS_MISTRAL_DEVELOPMENT_REPAIR_PENDING_INDEPENDENT",
                      completed_traces=completed, operation_modes=dict(modes), counters=dict(counters),
                      logical_dense_query_forwards=logical_dense_queries,
                      cuda_allocated_after_close_bytes=allocated_after, elapsed_seconds=elapsed,
                      native_ast_nodes=nodes, repair_bindings=record(stage_output / "REPAIR_BINDINGS.jsonl"),
                      call_journal=record(stage_output / "CALL_JOURNAL.jsonl"))
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result); seal(stage_output)
        print(result["status"], flush=True); return 0
    except Exception as exc:
        result.update(status="FAIL_MISTRAL_DEVELOPMENT_REPAIR", error_type=type(exc).__name__,
                      diagnostic=str(exc), traceback=traceback.format_exc(), completed_traces=completed,
                      operation_modes=dict(modes), counters=dict(counters), elapsed_seconds=time.perf_counter() - started)
        if bge is not None:
            try: bge.close()
            except Exception: pass
        if journal is not None:
            try: journal.close()
            except Exception: pass
        if ledger is not None:
            try: ledger.close()
            except Exception: pass
        write_json_durable(stage_output / "STAGE_FAILURE.json", result); seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True); return 2
    finally:
        if mutex is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(mutex)
            except Exception: pass


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
