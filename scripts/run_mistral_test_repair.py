"""Run/resume BGE-only repair retrieval for the frozen Mistral test traces."""
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

from scripts.empirical_runtime_io import CPU_TEST_SHA, native_runtime, restore_dataset
from scripts.mistral_development_acquisition_common import (
    DurableLedger,
    read_jsonl,
    record,
    recover_or_execute,
    sha256,
    verify_manifest,
    write_json_durable,
)
from scripts.run_mistral_test_a0_query import (
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_INPUT_LEDGER_SHA256,
    EXPECTED_TEST_POOL_MANIFEST_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
    EXPECTED_TEST_TRACE_SHA256,
    acquire_gpu_mutex,
    validate_selected_manifest,
    validate_test_binding,
)
from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal,
    object_sha256,
    require,
    text_sha256,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_RETRIEVAL_MANIFEST_SHA256 = (
    "81b9c7163adf669a828bd2ef772e14fecbda727cf596bced45856a1e699a354d"
)
EXPECTED_BGE_PREFLIGHT_MANIFEST_SHA256 = (
    "3861f34c6add005baa1889d36679b740c90677d0fbbbc04ea85ab8b5cc6a2b3d"
)
EXPECTED_TRACES = 18_000
EXPECTED_DENSE_QUERY_FORWARDS = 12_000
MIN_DISK_FREE_BYTES = 30 * 1024 ** 3
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    require(manifest_path.is_file(), "MANIFEST_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("status") == "PASS"
            and manifest.get("exact_recursive_coverage") is True,
            "MANIFEST_STATUS")
    members = set()
    for item in manifest.get("files", []):
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace.resolve()) and path not in members,
                "MANIFEST_PATH")
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_a0_gate(root: Path) -> tuple[Path, Path]:
    namespace = root / "a0_query"
    validation = root / "a0_query_validation/VALIDATION.json"
    validate_manifest(namespace)
    require(validation.is_file(), "A0_QUERY_ACCEPTANCE_REQUIRED")
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    acceptance = json.loads(validation.read_text(encoding="utf-8"))
    require(receipt.get("status")
            == "PASS_MISTRAL_TEST_A0_QUERY_PENDING_INDEPENDENT"
            and receipt.get("completed_traces") == EXPECTED_TRACES
            and receipt.get("logical_operations") == EXPECTED_TRACES * 2
            and receipt.get("project_gold_values_read") == 0
            and receipt.get("test_gold_values_read") == 0,
            "A0_QUERY_RECEIPT")
    require(acceptance.get("status")
            == "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY"
            and acceptance.get("producer_receipt_sha256")
            == sha256(namespace / "STAGE_RECEIPT.json")
            and acceptance.get("generation_receipts_sha256")
            == sha256(namespace / "GENERATION_RECEIPTS.jsonl")
            and acceptance.get("call_journal_sha256")
            == sha256(namespace / "CALL_JOURNAL.jsonl")
            and acceptance.get("gold_values_read") == 0
            and acceptance.get("test_gold_values_read") == 0,
            "A0_QUERY_ACCEPTANCE")
    return namespace, validation


def bge_asset_records(preflight: Path, original: Path) -> list[dict]:
    receipt = json.loads((preflight / "GPU_PREFLIGHT.json").read_text(
        encoding="utf-8"
    ))
    require(receipt.get("status") == "PASS_BGE_GPU_SYNTHETIC_ONLY"
            and receipt.get("actual_backend", {}).get("revision") == BGE_REVISION
            and receipt.get("benchmark_embedding_forward_calls") == 0
            and receipt.get("fresh_gold_values_materialized") == 0,
            "BGE_PREFLIGHT_STATUS")
    freeze = json.loads((preflight / "EXECUTABLE_FREEZE.json").read_text(
        encoding="utf-8"
    ))
    model_root = (original / "data/models/huggingface"
                  / "models--BAAI--bge-base-en-v1.5"
                  / "snapshots" / BGE_REVISION).resolve()
    selected = []
    for item in freeze["inputs"]:
        path = Path(item["path"]).resolve()
        if path.is_relative_to(model_root):
            require(path.is_file() and path.stat().st_size == item["size_bytes"]
                    and sha256(path) == item["sha256"], "BGE_ASSET_MEMBER")
            selected.append({"path": str(path), "size_bytes": item["size_bytes"],
                             "sha256": item["sha256"]})
    require(len(selected) == 6 and len({item["path"] for item in selected}) == 6,
            "BGE_ASSET_FILE_COUNT")
    return selected


def query_object(native, payload: dict):
    render = payload["render"]
    return native.GeneratedRepairQuery(
        payload["raw_text"], payload["parsed_text"],
        payload["parser_fallback"], payload["input_tokens"],
        payload["output_tokens"], render["context_truncated"],
        render["context_budget_characters"],
        tuple(render["ordered_passed_document_ids"]),
        tuple(render["per_document_truncated"]), 0.0, False, False, 1,
    )


def evidence_rows(evidence) -> list[dict]:
    return [row.as_private_dict() for row in evidence]


def validate_repair_payload(payload: dict, trace: dict) -> None:
    require(payload["dataset"] == trace["dataset"]
            and payload["retriever"] == trace["retriever"]
            and payload["sample_id"] == trace["sample_id"]
            and payload["position"] == trace["position"]
            and payload["role"] == "test", "REPAIR_IDENTITY")
    ranking = payload["ranking"]
    require(len(ranking) == 50
            and [row["rank"] for row in ranking] == list(range(1, 51))
            and len({row["document_id"] for row in ranking}) == 50,
            "REPAIR_RANKING")
    require(len(payload["e0_ids"]) == len(payload["e1_ids"]) == 5
            and payload["e0_ids"] == trace["original_top5_ids"]
            and payload["e1_ids"][:4] == payload["e0_ids"][:4]
            and payload["e1_ids"][4] == payload["inserted_document_id"]
            and payload["replaced_document_id"] == payload["e0_ids"][4]
            and payload["inserted_document_id"] not in payload["e0_ids"],
            "REPAIR_REPLACEMENT")
    inserted = [row for row in ranking
                if row["document_id"] == payload["inserted_document_id"]]
    require(len(inserted) == 1
            and inserted[0]["rank"] == payload["inserted_candidate_rank"],
            "REPAIR_INSERTED_RANK")
    expected_components = ({"bm25", "dense"}
                           if trace["retriever"] == "hybrid"
                           else {trace["retriever"]})
    require(set(payload["component_rankings"]) == expected_components,
            "REPAIR_COMPONENTS")
    require((payload["dense_query_vector"] is None)
            == (trace["retriever"] == "bm25")
            and (payload["dense_query_vector"] is None
                 or len(payload["dense_query_vector"]) == 768),
            "REPAIR_VECTOR")
    require(payload["requested_depth"] == 50
            and payload["replacement_position_zero_based"] == 4
            and payload["repair_retrieval_calls"] == 1
            and payload["fail_closed_reason"] is None,
            "REPAIR_CONTROLS")


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path)
            item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files,
        "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    original, root = args.project_root.resolve(), args.test_root.resolve()
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve(),
            "FIXED_ROOTS")
    a0_stage, a0_validation = validate_a0_gate(root)
    stage_output = root / "repair"
    require(not any((stage_output / name).exists() for name in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json",
                     "SHA256_MANIFEST.json")), "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    ).strip(), "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    started = time.perf_counter()
    mutex = bge = journal = ledger = None
    completed = 0
    modes = collections.Counter()
    counters = collections.Counter()
    result = {
        "status": "FAIL", "cas_q3_status": "NOT READY",
        "source_commit": commit, "stage": "repair",
        "gold_values_read": 0, "test_gold_values_read": 0,
        "scientific_fits": 0, "test_input_rows_read": 0,
        "mistral_model_loads": 0, "nli_model_loads": 0,
    }
    try:
        if not args.resume:
            stage_output.mkdir(parents=True, exist_ok=False)
        import psutil
        require(psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES,
                "DISK_FREE_ADMISSION")
        mutex = acquire_gpu_mutex()
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(input_freeze / "SHA256_MANIFEST.json")
                == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
                and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256,
                "INPUT_FREEZE_PIN")
        preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
        pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        retrieval = REPO / "outputs/cas_q2/empirical_retrieval_v1"
        preflight = REPO / "outputs/cas_q2/empirical_retrieval_gpu_preflight_v1"
        trace_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
        require(sha256(trace_path) == EXPECTED_TEST_TRACE_SHA256,
                "TEST_TRACE_PIN")
        pool_relatives = tuple(
            f"{folder}/{dataset}.jsonl"
            for folder in ("pools", "runtime") for dataset in DATASETS
        ) + ("INDEPENDENT_VALIDATION.json",)
        cpu_tests = REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1"
        paths = [
            *validate_selected_manifest(
                preparation, EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
                ("TRACE_MANIFEST_PRIVATE.jsonl",),
            ),
            *validate_selected_manifest(
                pool_root, EXPECTED_TEST_POOL_MANIFEST_SHA256, pool_relatives,
            ),
            *verify_manifest(retrieval, EXPECTED_RETRIEVAL_MANIFEST_SHA256),
            *verify_manifest(preflight,
                             EXPECTED_BGE_PREFLIGHT_MANIFEST_SHA256),
            *verify_manifest(cpu_tests, CPU_TEST_SHA),
            *verify_manifest(input_freeze,
                             EXPECTED_INPUT_FREEZE_MANIFEST_SHA256),
            *verify_manifest(
                a0_stage, sha256(a0_stage / "SHA256_MANIFEST.json")
            ),
            a0_validation,
            Path(__file__), REPO / "scripts/validate_mistral_test_repair.py",
            REPO / "scripts/empirical_runtime_io.py",
            REPO / "scripts/empirical_retrieval_io.py",
            REPO / "scripts/empirical_pool_io.py",
            REPO / "scripts/empirical_runtime_contract.py",
            REPO / "scripts/replay_roa_original.py",
            REPO / "scripts/verify_roa_artifacts.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/run_mistral_test_a0_query.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/SHA256_MANIFEST.json",
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/runtime_support.py",
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/native_runtime.py",
        ]
        records = [record(path) for path in sorted(
            {Path(path).resolve() for path in paths}, key=str
        )]
        assets = bge_asset_records(preflight, original)
        by_path = {item["path"]: item for item in [*records, *assets]}
        require(len(by_path) == len(records) + len(assets),
                "UNIQUE_REPAIR_INPUTS")
        input_records = [by_path[path] for path in sorted(by_path)]
        freeze = {
            "status": "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_REPAIR",
            "source_commit": commit, "stage": "repair",
            "expected_traces": EXPECTED_TRACES,
            "expected_dense_query_forwards": EXPECTED_DENSE_QUERY_FORWARDS,
            "retrieval_depth": 50, "replacement_position_zero_based": 4,
            "test_gold_access": "FORBIDDEN", "inputs": input_records,
            "scope": "test same-retriever repair only; Mistral/NLI/Gold/fit/document re-embedding forbidden",
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                    "RESUME_FREEZE_MISMATCH")
        else:
            write_json_durable(freeze_path, freeze)

        wrapper, native, nodes, boundary = native_runtime(original)
        traces = list(read_jsonl(trace_path))
        frozen_rows = validate_test_binding(traces, read_jsonl(frozen_ledger))
        a0_rows = list(read_jsonl(a0_stage / "GENERATION_RECEIPTS.jsonl"))
        query_map = {row["payload"]["position"]: row["payload"]
                     for row in a0_rows if row["operation"] == "repair_query"}
        require(len(query_map) == EXPECTED_TRACES, "QUERY_COUNT")
        result["test_input_rows_read"] = EXPECTED_TRACES
        journal = DurableOperationJournal(
            stage_output / "CALL_JOURNAL.jsonl", resume=args.resume
        )
        ledger = DurableLedger(
            stage_output / "REPAIR_BINDINGS.jsonl", resume=args.resume
        )
        bge = native.ExactLocalBGEBackend(
            model_cache_dir=original / "data/models/huggingface"
        )
        bge._ensure_loaded()
        counters["bge_model_loads"] = 1
        require(bge.model.config._commit_hash == BGE_REVISION
                and bge.dimension == 768, "BGE_IDENTITY")

        class QueryOnlyBackend:
            dimension = 768

            def __init__(self):
                self.last = None

            def encode_queries(self, texts):
                require(type(texts) is list and len(texts) == 1,
                        "SINGLE_QUERY")
                counters["bge_query_forwards_current_process"] += 1
                self.last = bge.encode_queries(texts)
                return self.last

            def encode_documents(self, *_args, **_kwargs):
                raise RuntimeError("DOCUMENT_REEMBEDDING_FORBIDDEN")

        backend = QueryOnlyBackend()
        runner = native.ProspectiveRunner()
        runner.protocol = native.FrozenProtocol()
        current_dataset = None
        data = None
        for trace, frozen_row in zip(traces, frozen_rows, strict=True):
            dataset, retriever, sample_id = (
                trace["dataset"], trace["retriever"], trace["sample_id"]
            )
            if dataset != current_dataset:
                data = restore_dataset(dataset, native, backend)
                current_dataset = dataset
            e0 = wrapper.original_evidence(trace, data, native)
            query_payload = query_map[trace["position"]]
            require(query_payload["dataset"] == dataset
                    and query_payload["retriever"] == retriever
                    and query_payload["sample_id"] == sample_id
                    and query_payload["role"] == frozen_row["role"] == "test",
                    "QUERY_TRACE_BINDING")
            query = query_object(native, query_payload)
            key = f"{trace['position']:05d}:repair_retrieval"
            input_value = {
                "dataset": dataset, "retriever": retriever,
                "sample_id": sample_id, "position": trace["position"],
                "query": query.search_query, "e0": evidence_rows(e0),
                "depth": 50, "replacement_position_zero_based": 4,
            }
            input_hash = object_sha256(input_value)

            def execute(trace=trace, query=query, e0=e0):
                data["components"].clear()
                backend.last = None
                ranking = []

                def rank(query_text, method, depth):
                    require(method == retriever and depth == 50,
                            "SAME_RETRIEVER_DEPTH")
                    value = data["router"].rank(query_text, method, depth)
                    ranking.extend(value)
                    return value

                e1, inserted, _diagnostics = runner._repair(
                    types.SimpleNamespace(rank=rank), query, retriever, e0
                )
                components = data["components"]
                require(len(components) == (2 if retriever == "hybrid" else 1),
                        "COMPONENT_COUNT")
                payload = {
                    "dataset": dataset, "retriever": retriever,
                    "sample_id": sample_id, "position": trace["position"],
                    "role": "test", "query_sha256": text_sha256(query.search_query),
                    "ranking": [{"document_id": row.document_id,
                                 "rank": row.rank, "score": float(row.score)}
                                for row in ranking],
                    "component_rankings": (
                        {"bm25": components[0], "dense": components[1]}
                        if retriever == "hybrid" else {retriever: components[0]}
                    ),
                    "dense_query_vector": (None if backend.last is None
                                           else backend.last[0].tolist()),
                    "e0_ids": [row.document_id for row in e0],
                    "e1_ids": [row.document_id for row in e1],
                    "inserted_document_id": inserted.document_id,
                    "inserted_candidate_rank": inserted.rank,
                    "replaced_document_id": e0[4].document_id,
                    "replacement_position_zero_based": 4,
                    "requested_depth": 50, "repair_retrieval_calls": 1,
                    "pool_sha256": data["binding"]["pool_sha256"],
                    "fail_closed_reason": None,
                }
                validate_repair_payload(payload, trace)
                return payload

            row, mode = recover_or_execute(
                journal=journal, ledger=ledger, key=key,
                operation="repair_retrieval", input_sha256=input_hash,
                execute=execute,
            )
            validate_repair_payload(row["payload"], trace)
            modes[mode] += 1
            completed += 1
            if completed % 10 == 0:
                print(json.dumps({"stage": "test_repair",
                                  "completed_traces": completed,
                                  "expected_traces": EXPECTED_TRACES},
                                 sort_keys=True), flush=True)
        require(completed == EXPECTED_TRACES
                and len(ledger.rows) == EXPECTED_TRACES, "COMPLETE_COUNTS")
        logical_dense = sum(
            row["payload"]["retriever"] in {"dense", "hybrid"}
            for row in ledger.rows
        )
        require(logical_dense == EXPECTED_DENSE_QUERY_FORWARDS,
                "BGE_LOGICAL_QUERY_COUNT")
        require(journal.pending is None
                and len(journal.completed) == EXPECTED_TRACES,
                "JOURNAL_COUNT")
        bge.close(); bge = None
        counters["bge_model_unloads"] = 1
        import torch
        gc.collect(); torch.cuda.empty_cache()
        allocated_after = int(torch.cuda.memory_allocated(0))
        require(allocated_after < 1024 ** 3, "BGE_NOT_RELEASED")
        journal.close(); journal = None
        ledger.close(); ledger = None
        for item in input_records:
            require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update({
            "status": "PASS_MISTRAL_TEST_REPAIR_PENDING_INDEPENDENT",
            "completed_traces": completed, "operation_modes": dict(modes),
            "counters": dict(counters),
            "logical_dense_query_forwards": logical_dense,
            "cuda_allocated_after_close_bytes": allocated_after,
            "elapsed_seconds": elapsed, "native_ast_nodes": nodes,
            "generation_boundary": boundary,
            "repair_bindings": record(stage_output / "REPAIR_BINDINGS.jsonl"),
            "call_journal": record(stage_output / "CALL_JOURNAL.jsonl"),
            "gold_values_read": 0, "test_gold_values_read": 0,
            "scientific_fits": 0, "test_input_rows_read": EXPECTED_TRACES,
            "mistral_model_loads": 0, "nli_model_loads": 0,
        })
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        result.update({
            "status": "FAIL_MISTRAL_TEST_REPAIR",
            "error_type": type(exc).__name__, "diagnostic": str(exc),
            "traceback": traceback.format_exc(),
            "completed_traces": completed, "operation_modes": dict(modes),
            "counters": dict(counters),
            "elapsed_seconds": time.perf_counter() - started,
        })
        if bge is not None:
            try: bge.close()
            except Exception: pass
        if journal is not None:
            try: journal.close()
            except Exception: pass
        if ledger is not None:
            try: ledger.close()
            except Exception: pass
        if stage_output.is_dir() and not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result)
            seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True)
        return 2
    finally:
        if mutex is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(mutex)
            except Exception:
                pass


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
