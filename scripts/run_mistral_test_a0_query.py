"""Run/resume formal Mistral test a0 and repair-query acquisition."""
from __future__ import annotations

import argparse
import collections
import gc
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    DurableLedger,
    compact_generation_receipt,
    read_jsonl,
    record,
    recover_or_execute,
    sha256,
    verify_manifest,
    write_json_durable,
)
from scripts.mistral_reader_input_freeze_common import compact_document
from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal,
    MistralNF4Reader,
    object_sha256,
    require,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_INPUT_FREEZE_MANIFEST_SHA256 = (
    "588b4d86fb6048ade1bba52731829496772d62fd522a260a7a4c60ec584586ca"
)
EXPECTED_INPUT_LEDGER_SHA256 = (
    "538970511fe517a21ef7baee4dc5eb216ce748b2c2222b3960c356a53a12f8ac"
)
EXPECTED_ASSET_MANIFEST_SHA256 = (
    "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
)
EXPECTED_TEST_PREPARATION_MANIFEST_SHA256 = (
    "7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258"
)
EXPECTED_TEST_POOL_MANIFEST_SHA256 = (
    "4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98"
)
EXPECTED_TEST_TRACE_SHA256 = (
    "87d5aff0bc77da76624b541326c523d41b00fa6c84ecefd4d6a050de66b25a29"
)
EXPECTED_TRACES = 18_000
EXPECTED_QUESTIONS = 6_000
EXPECTED_QUESTIONS_PER_CELL = 2_000
EXPECTED_OPERATIONS = EXPECTED_TRACES * 2
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60
MIN_DISK_FREE_BYTES = 30 * 1024 ** 3
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")


def validate_asset_manifest(asset: Path) -> list[dict]:
    manifest_path = asset / "ASSET_MANIFEST.json"
    require(sha256(manifest_path) == EXPECTED_ASSET_MANIFEST_SHA256,
            "ASSET_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = []
    require(value.get("selected_file_count") == 14,
            "ASSET_MANIFEST_FILE_COUNT")
    for item in value["selected_files"]:
        path = (asset / item["path"]).resolve()
        require(path.is_relative_to(asset.resolve())
                and path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"],
                "ASSET_MEMBER:" + item["path"])
        records.append({"path": str(path), "size_bytes": item["size_bytes"],
                        "sha256": item["sha256"]})
    require(len(records) == 14, "ASSET_SELECTED_FILE_COUNT")
    return [record(manifest_path), *records]


def validate_selected_manifest(
    namespace: Path, expected_manifest_sha256: str, relatives: tuple[str, ...],
) -> list[Path]:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest_path) == expected_manifest_sha256,
            "SELECTED_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {item["path"]: item for item in value["files"]}
    require(len(entries) == len(value["files"])
            and set(relatives) <= set(entries), "SELECTED_MANIFEST_MEMBERS")
    paths = []
    for relative in relatives:
        item = entries[relative]
        path = (namespace / relative).resolve()
        require(path.is_relative_to(namespace.resolve()) and path.is_file()
                and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"],
                "SELECTED_MANIFEST_MEMBER:" + relative)
        paths.append(path)
    return [manifest_path.resolve(), *paths]


def acquire_gpu_mutex():
    require(os.name == "nt", "WINDOWS_HOST_REQUIRED")
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(
        None, False, "Local\\ReliableRAG_Mistral_Development_Acquisition"
    )
    require(handle, "GPU_MUTEX_CREATE")
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(handle)
        raise RuntimeError("GPU_MUTEX_ALREADY_HELD")
    return handle


def validate_frozen_receipt(payload: dict, frozen: dict, stage: str) -> None:
    require(stage in {"a0", "repair_query"} and payload["stage"] == stage,
            "FROZEN_STAGE")
    expected = frozen["answer" if stage == "a0" else "repair_query"]
    require(payload["prompt_sha256"] == expected["prompt_sha256"],
            "FROZEN_PROMPT_HASH")
    require(payload["input_token_ids_sha256"]
            == expected["input_token_ids_sha256"], "FROZEN_TOKEN_HASH")
    require(payload["input_tokens"] == expected["input_tokens"],
            "FROZEN_TOKEN_COUNT")
    render = payload["render"]
    require(render["context_truncated"] == expected["context_truncated"]
            and render["per_document_truncated"]
            == expected["per_document_truncated"], "FROZEN_RENDER")


def validate_test_binding(traces: list[dict], frozen_rows) -> list[dict]:
    test_rows = [row for row in frozen_rows if row.get("cohort") == "test"]
    require(len(traces) == len(test_rows) == EXPECTED_TRACES,
            "TEST_TRACE_COUNT")
    cells = collections.Counter()
    groups = collections.Counter()
    identities = set()
    for position, (trace, frozen) in enumerate(zip(
            traces, test_rows, strict=True)):
        require(trace["position"] == frozen["position"] == position,
                "TEST_POSITION")
        identity = (trace["dataset"], trace["retriever"], trace["sample_id"])
        require(identity == (frozen["dataset"], frozen["retriever"],
                             frozen["sample_id"])
                and identity not in identities, "TEST_IDENTITY")
        identities.add(identity)
        require(frozen.get("role") == "test", "TEST_ROLE")
        require(object_sha256(trace["original_top5_ids"])
                == frozen["original_top5_ids_sha256"],
                "ORIGINAL_TOP5_BINDING")
        cells[(identity[0], identity[1])] += 1
        groups[(identity[0], identity[2])] += 1
    require(all(cells[(dataset, retriever)] == EXPECTED_QUESTIONS_PER_CELL
                for dataset in DATASETS for retriever in RETRIEVERS),
            "BALANCED_TEST_CELLS")
    require(len(groups) == EXPECTED_QUESTIONS
            and all(value == 3 for value in groups.values()),
            "TEST_QUESTION_SIBLINGS")
    return test_rows


def load_test_assets(pool_root: Path) -> dict[str, dict[str, dict]]:
    result = {}
    for dataset in DATASETS:
        document_rows = list(read_jsonl(pool_root / "pools" / f"{dataset}.jsonl"))
        runtime_rows = list(read_jsonl(pool_root / "runtime" / f"{dataset}.jsonl"))
        require(all(set(row) == {"content_hash", "dataset", "id", "sentences",
                                 "title"}
                    and row["dataset"] == dataset for row in document_rows),
                "TEST_DOCUMENT_SCHEMA:" + dataset)
        require(all(set(row) == {"dataset", "documents", "id", "question", "split"}
                    and row["dataset"] == dataset for row in runtime_rows),
                "TEST_RUNTIME_SCHEMA:" + dataset)
        documents = {row["id"]: row for row in document_rows}
        questions = {row["id"]: row["question"] for row in runtime_rows}
        require(len(documents) == len(document_rows)
                and len(questions) == len(runtime_rows),
                "UNIQUE_TEST_ASSET_IDS:" + dataset)
        result[dataset] = {"documents": documents, "questions": questions}
    return result


def source_pair(trace: dict, assets: dict[str, dict[str, dict]]) -> tuple[str, list[dict]]:
    dataset, sample_id = trace["dataset"], trace["sample_id"]
    require(dataset in assets and sample_id in assets[dataset]["questions"],
            "TEST_QUESTION_MEMBERSHIP")
    documents = assets[dataset]["documents"]
    ids = trace["original_top5_ids"]
    require(type(ids) is list and len(ids) == 5 and len(set(ids)) == 5
            and all(document_id in documents for document_id in ids),
            "TEST_EVIDENCE_MEMBERSHIP")
    evidence = [compact_document(documents[document_id], rank)
                for rank, document_id in enumerate(ids, 1)]
    return assets[dataset]["questions"][sample_id], evidence


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
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    original, asset, root = (args.project_root.resolve(), args.asset.resolve(),
                             args.test_root.resolve())
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve(),
            "FIXED_ROOTS")
    stage_output = root / "a0_query"
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
    reader = journal = ledger = mutex = None
    completed = 0
    modes = collections.Counter()
    result = {
        "status": "FAIL", "cas_q3_status": "NOT READY",
        "source_commit": commit, "stage": "a0_query",
        "project_gold_values_read": 0, "test_gold_values_read": 0,
        "scientific_fits": 0, "test_input_rows_read": 0,
        "model_loads": 0, "model_unloads": 0,
    }
    try:
        if not args.resume:
            stage_output.mkdir(parents=True, exist_ok=False)
        import psutil
        require(psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES,
                "DISK_FREE_ADMISSION")
        mutex = acquire_gpu_mutex()
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
                and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256,
                "INPUT_FREEZE_PIN")
        preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
        pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        trace_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
        require(sha256(trace_path) == EXPECTED_TEST_TRACE_SHA256,
                "TEST_TRACE_PIN")
        pool_relatives = tuple(
            f"{folder}/{dataset}.jsonl"
            for folder in ("pools", "runtime") for dataset in DATASETS
        )
        source_paths = [
            *validate_selected_manifest(
                preparation, EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
                ("TRACE_MANIFEST_PRIVATE.jsonl",),
            ),
            *validate_selected_manifest(
                pool_root, EXPECTED_TEST_POOL_MANIFEST_SHA256, pool_relatives,
            ),
            *verify_manifest(input_freeze,
                             EXPECTED_INPUT_FREEZE_MANIFEST_SHA256),
        ]
        asset_records = validate_asset_manifest(asset)
        control_paths = [
            Path(__file__), REPO / "scripts/validate_mistral_test_a0_query.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/mistral_reader_input_freeze_common.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_TEST_A0_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            original / "prompts/baseline_v1.txt",
            original / "prompts/repair_missing_v1.txt",
            Path(sys.executable),
        ]
        unique_paths = sorted({Path(path).resolve()
                               for path in [*source_paths, *control_paths]}, key=str)
        input_records = [record(path) for path in unique_paths] + asset_records
        require(len({item["path"] for item in input_records})
                == len(input_records), "UNIQUE_EXECUTION_INPUTS")
        freeze = {
            "status": "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_A0_QUERY",
            "source_commit": commit, "stage": "a0_query",
            "expected_traces": EXPECTED_TRACES,
            "expected_operations": EXPECTED_OPERATIONS,
            "test_gold_access": "FORBIDDEN", "inputs": input_records,
            "environment": {key: os.environ.get(key) for key in (
                "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
                "HF_HUB_DISABLE_TELEMETRY", "TOKENIZERS_PARALLELISM",
                "PYTHONHASHSEED", "CUBLAS_WORKSPACE_CONFIG",
            )},
            "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "scope": "test a0 and repair query only; no Gold, fit, repair retrieval, a1, likelihood or NLI",
        }
        freeze_path = root / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                    "RESUME_FREEZE_MISMATCH")
        else:
            write_json_durable(freeze_path, freeze)

        traces = list(read_jsonl(trace_path))
        frozen = validate_test_binding(traces, read_jsonl(frozen_ledger))
        assets = load_test_assets(pool_root)
        result["test_input_rows_read"] = EXPECTED_TRACES
        journal = DurableOperationJournal(
            stage_output / "CALL_JOURNAL.jsonl", resume=args.resume
        )
        ledger = DurableLedger(
            stage_output / "GENERATION_RECEIPTS.jsonl", resume=args.resume
        )
        require(len(ledger.rows) <= EXPECTED_OPERATIONS,
                "RESUME_LEDGER_COUNT")
        reader = MistralNF4Reader(
            asset=asset, answer_prompt=original / "prompts/baseline_v1.txt",
            repair_prompt=original / "prompts/repair_missing_v1.txt",
        )
        reader.load()
        result["model_loads"] = 1
        for trace, frozen_row in zip(traces, frozen, strict=True):
            dataset, retriever, sample_id = (
                trace["dataset"], trace["retriever"], trace["sample_id"]
            )
            question, evidence = source_pair(trace, assets)
            for operation in ("a0", "repair_query"):
                key = f"{trace['position']:05d}:{operation}"
                input_value = {
                    "dataset": dataset, "retriever": retriever,
                    "sample_id": sample_id, "position": trace["position"],
                    "role": "test", "operation": operation,
                    "question": question, "evidence": evidence,
                }
                input_hash = object_sha256(input_value)

                def execute(operation=operation, frozen_row=frozen_row):
                    generated = reader.generate(
                        stage=operation, question=question, evidence=evidence
                    )
                    payload = compact_generation_receipt(generated.receipt)
                    validate_frozen_receipt(payload, frozen_row, operation)
                    payload.update({
                        "dataset": dataset, "retriever": retriever,
                        "sample_id": sample_id, "position": trace["position"],
                        "role": "test",
                        "question_sha256": object_sha256(question),
                        "evidence_sha256": object_sha256(evidence),
                    })
                    return payload

                row, mode = recover_or_execute(
                    journal=journal, ledger=ledger, key=key,
                    operation=operation, input_sha256=input_hash,
                    execute=execute,
                )
                validate_frozen_receipt(row["payload"], frozen_row, operation)
                modes[mode] += 1
            completed += 1
            if completed % 10 == 0:
                print(json.dumps({"stage": "test_a0_query",
                                  "completed_traces": completed,
                                  "expected_traces": EXPECTED_TRACES},
                                 sort_keys=True), flush=True)
        require(completed == EXPECTED_TRACES
                and len(ledger.rows) == EXPECTED_OPERATIONS,
                "COMPLETE_OPERATION_COUNT")
        require(journal.pending is None
                and len(journal.completed) == EXPECTED_OPERATIONS,
                "COMPLETE_JOURNAL_COUNT")
        model_forwards = reader.model_forward_calls
        reader.close(); reader = None
        result["model_unloads"] = 1
        import torch
        gc.collect(); torch.cuda.empty_cache()
        allocated_after_close = int(torch.cuda.memory_allocated(0))
        require(allocated_after_close < 1024 ** 3, "MISTRAL_NOT_RELEASED")
        journal.close(); journal = None
        ledger.close(); ledger = None
        for item in input_records:
            require(record(item["path"]) == item,
                    "INPUT_CHANGED:" + str(item["path"]))
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update({
            "status": "PASS_MISTRAL_TEST_A0_QUERY_PENDING_INDEPENDENT",
            "completed_traces": completed,
            "logical_operations": EXPECTED_OPERATIONS,
            "operation_modes": dict(modes),
            "physical_model_forwards": model_forwards,
            "gpu_allocated_after_close_bytes": allocated_after_close,
            "elapsed_seconds": elapsed,
            "input_records": len(input_records),
            "generation_receipts": record(
                stage_output / "GENERATION_RECEIPTS.jsonl"
            ),
            "call_journal": record(stage_output / "CALL_JOURNAL.jsonl"),
            "project_gold_values_read": 0, "test_gold_values_read": 0,
            "scientific_fits": 0, "test_input_rows_read": EXPECTED_TRACES,
        })
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        result.update({
            "status": "FAIL_MISTRAL_TEST_A0_QUERY",
            "error_type": type(exc).__name__, "diagnostic": str(exc),
            "traceback": traceback.format_exc(),
            "completed_traces": completed,
            "operation_modes": dict(modes),
            "elapsed_seconds": time.perf_counter() - started,
        })
        if reader is not None:
            try: reader.close()
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
