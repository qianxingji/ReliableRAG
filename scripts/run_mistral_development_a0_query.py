"""Run/resume the formal Mistral development a0 + repair-query stage."""

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
import types

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    DurableLedger, compact_generation_receipt, read_jsonl, record,
    recover_or_execute, sha256, validate_development_binding, write_json_durable,
)
from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal, MistralNF4Reader, object_sha256, require,
)


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q3"
EXPECTED_INPUT_FREEZE_MANIFEST_SHA256 = "588b4d86fb6048ade1bba52731829496772d62fd522a260a7a4c60ec584586ca"
EXPECTED_INPUT_LEDGER_SHA256 = "538970511fe517a21ef7baee4dc5eb216ce748b2c2222b3960c356a53a12f8ac"
EXPECTED_ASSET_MANIFEST_SHA256 = "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
EXPECTED_RUNTIME_MANIFEST_SHA256 = "0e831d2807ee48197029f03f8ed1e18381a60bc5fc25327edccc8d8486b6cefb"
EXPECTED_POOL_MANIFEST_SHA256 = "f53575bc7b9514f33a235f8380520b99c2faac4cb8b6d78533fc42cb08f377b8"
EXPECTED_RETRIEVAL_MANIFEST_SHA256 = "15a18dc5c2a61a83171add05be2cb989813ab023ffea8a035cb1ba42dacdf651"
EXPECTED_TRACES = 13_500
EXPECTED_OPERATIONS = EXPECTED_TRACES * 2
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60
MIN_DISK_FREE_BYTES = 30 * 1024 ** 3


def _import_file(name: str, path: Path):
    module = types.ModuleType(name); module.__file__ = str(path); module.__package__ = ""
    sys.modules[name] = module
    payload = path.read_bytes()
    exec(compile(payload.decode("utf-8-sig"), str(path), "exec"), module.__dict__)
    return module


def load_original_native(original: Path):
    frozen = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    support = _import_file("runtime_support", frozen / "runtime_support.py")
    require(support.ROOT == original, "ORIGINAL_RUNTIME_ROOT")
    _import_file("retrieval_support", original / "outputs/daa_v2_fresh_v1/retrieval_freeze/retrieval_support.py")
    loader = _import_file("mistral_development_original_native_runtime", frozen / "native_runtime.py")
    loader.import_file = _import_file
    native, nodes, boundary = loader.accepted()
    tested = json.loads((frozen / "SYNTHETIC_TEST_RESULT_V2.json").read_text(encoding="utf-8"))
    require(tested["status"] == "PASS" and tested["tests_run"] == 22
            and not tested["errors"] and not tested["failures"], "ORIGINAL_NATIVE_TESTS")
    require(nodes == tested["accepted_ast_nodes"] and boundary == tested["boundary"], "ORIGINAL_NATIVE_ASSEMBLY")
    return loader, native, nodes, boundary


def validate_manifest_pin(path: Path, expected: str) -> dict:
    require(path.is_file() and sha256(path) == expected, "MANIFEST_PIN:" + str(path))
    return record(path)


def validate_asset_manifest(asset: Path) -> list[dict]:
    manifest_path = asset / "ASSET_MANIFEST.json"
    require(sha256(manifest_path) == EXPECTED_ASSET_MANIFEST_SHA256, "ASSET_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = []
    require(value.get("selected_file_count") == 14, "ASSET_MANIFEST_FILE_COUNT")
    for item in value["selected_files"]:
        path = (asset / item["path"]).resolve()
        require(path.is_relative_to(asset) and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "ASSET_MEMBER:" + item["path"])
        records.append({"path": str(path), "size_bytes": item["size_bytes"], "sha256": item["sha256"]})
    require(len(records) == 14, "ASSET_SELECTED_FILE_COUNT")
    return [record(manifest_path), *records]


def acquire_gpu_mutex():
    require(os.name == "nt", "WINDOWS_HOST_REQUIRED")
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, "Local\\ReliableRAG_Mistral_Development_Acquisition")
    require(handle, "GPU_MUTEX_CREATE")
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(handle)
        raise RuntimeError("GPU_MUTEX_ALREADY_HELD")
    return handle


def evidence_rows(evidence) -> list[dict]:
    return [row.as_private_dict() for row in evidence]


def validate_frozen_receipt(payload: dict, frozen: dict, stage: str) -> None:
    require(stage in {"a0", "repair_query"} and payload["stage"] == stage, "FROZEN_STAGE")
    expected = frozen["answer" if stage == "a0" else "repair_query"]
    require(payload["prompt_sha256"] == expected["prompt_sha256"], "FROZEN_PROMPT_HASH")
    require(payload["input_token_ids_sha256"] == expected["input_token_ids_sha256"], "FROZEN_TOKEN_HASH")
    require(payload["input_tokens"] == expected["input_tokens"], "FROZEN_TOKEN_COUNT")
    render = payload["render"]
    require(render["context_truncated"] == expected["context_truncated"]
            and render["per_document_truncated"] == expected["per_document_truncated"], "FROZEN_RENDER")


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
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    require(all(part not in args.output_name for part in ("/", "\\", ".."))
            and args.output_name, "SAFE_OUTPUT_NAME")
    original = args.project_root.resolve(); asset = args.asset.resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve(), "FIXED_PROJECT_ROOT")
    root = (OUTPUT_PARENT / args.output_name).resolve(); require(root.parent == OUTPUT_PARENT.resolve(), "OUTPUT_CONTAINMENT")
    stage_output = root / "a0_query"
    require(not any((stage_output / value).exists() for value in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json", "SHA256_MANIFEST.json")), "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not root.exists(), "OUTPUT_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    started = time.perf_counter(); reader = journal = ledger = None; mutex = None
    completed = 0; modes = collections.Counter(); result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "a0_query", "project_gold_values_read": 0, "scientific_fits": 0,
        "test_rows_read": 0, "model_loads": 0, "model_unloads": 0,
    }
    try:
        if not args.resume:
            stage_output.mkdir(parents=True, exist_ok=False)
        import psutil
        require(psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES, "DISK_FREE_ADMISSION")
        mutex = acquire_gpu_mutex()
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        require(sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256, "INPUT_FREEZE_MANIFEST")
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256, "INPUT_FREEZE_LEDGER")
        runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
        manifest_records = [
            validate_manifest_pin(runtime_root / "SHA256_MANIFEST.json", EXPECTED_RUNTIME_MANIFEST_SHA256),
            validate_manifest_pin(original / "outputs/daa_v2_fresh_v1/pool_freeze/SHA256_MANIFEST.json", EXPECTED_POOL_MANIFEST_SHA256),
            validate_manifest_pin(original / "outputs/daa_v2_fresh_v1/retrieval_freeze/SHA256_MANIFEST.json", EXPECTED_RETRIEVAL_MANIFEST_SHA256),
            record(input_manifest), record(frozen_ledger),
        ]
        asset_records = validate_asset_manifest(asset)
        control_paths = [
            Path(__file__), REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_ACQUISITION_PROTOCOL_2026-09-17.md",
            original / "prompts/baseline_v1.txt", original / "prompts/repair_missing_v1.txt",
            runtime_root / "runtime_support.py", runtime_root / "native_runtime.py",
            runtime_root / "RUNTIME_CONFIG_FREEZE.json", runtime_root / "SYNTHETIC_TEST_RESULT_V2.json",
            runtime_root / "trace_manifest.jsonl",
        ]
        input_records = manifest_records + asset_records + [record(path) for path in control_paths]
        freeze = {
            "status": "FROZEN_BEFORE_FORMAL_A0_QUERY", "source_commit": commit,
            "stage": "a0_query", "expected_traces": EXPECTED_TRACES,
            "expected_operations": EXPECTED_OPERATIONS, "inputs": input_records,
            "environment": {key: os.environ.get(key) for key in (
                "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY",
                "TOKENIZERS_PARALLELISM", "PYTHONHASHSEED", "CUBLAS_WORKSPACE_CONFIG",
            )},
            "host": platform.platform(), "python": str(Path(sys.executable).resolve()),
            "scope": "development a0 and repair query only; no test, Gold, fit, repair retrieval, a1, likelihood or NLI",
        }
        freeze_path = root / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze, "RESUME_FREEZE_MISMATCH")
        else:
            write_json_durable(freeze_path, freeze)
        loader, native, nodes, boundary = load_original_native(original)
        traces = list(read_jsonl(runtime_root / "trace_manifest.jsonl"))
        frozen_rows = list(read_jsonl(frozen_ledger))
        development = validate_development_binding(traces, frozen_rows)
        frozen_index = {
            (row["dataset"], row["retriever"], row["sample_id"]): row for row in development
        }
        require(len(frozen_index) == EXPECTED_TRACES, "FROZEN_INDEX")
        journal = DurableOperationJournal(stage_output / "CALL_JOURNAL.jsonl", resume=args.resume)
        ledger = DurableLedger(stage_output / "GENERATION_RECEIPTS.jsonl", resume=args.resume)
        require(len(ledger.rows) <= EXPECTED_OPERATIONS, "RESUME_LEDGER_COUNT")
        reader = MistralNF4Reader(
            asset=asset, answer_prompt=original / "prompts/baseline_v1.txt",
            repair_prompt=original / "prompts/repair_missing_v1.txt",
        )
        reader.load(); result["model_loads"] = 1

        class NoEmbeddingBackend:
            dimension = 768
            def encode_queries(self, *_args, **_kwargs):
                raise RuntimeError("BGE_QUERY_FORBIDDEN_IN_A0_QUERY_STAGE")
            def encode_documents(self, *_args, **_kwargs):
                raise RuntimeError("DOCUMENT_EMBEDDING_FORBIDDEN")

        backend = NoEmbeddingBackend(); current_dataset = None; data = None
        for trace in traces:
            dataset, retriever, sample_id = trace["dataset"], trace["retriever"], trace["sample_id"]
            if dataset != current_dataset:
                data = loader.restore_dataset(dataset, native, backend); current_dataset = dataset
            question = data["questions"][sample_id]
            e0 = loader.original_evidence(trace, data, native); private_e0 = evidence_rows(e0)
            frozen = frozen_index[(dataset, retriever, sample_id)]
            for operation in ("a0", "repair_query"):
                key = f"{trace['position']:05d}:{operation}"
                input_value = {
                    "dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                    "position": trace["position"], "role": frozen["role"],
                    "operation": operation, "question": question, "evidence": private_e0,
                }
                input_hash = object_sha256(input_value)
                def execute(operation=operation, trace=trace, frozen=frozen):
                    generated = reader.generate(stage=operation, question=question, evidence=private_e0)
                    payload = compact_generation_receipt(generated.receipt)
                    validate_frozen_receipt(payload, frozen, operation)
                    payload.update({
                        "dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                        "position": trace["position"], "role": frozen["role"],
                        "question_sha256": object_sha256(question),
                        "evidence_sha256": object_sha256(private_e0),
                    })
                    return payload
                row, mode = recover_or_execute(
                    journal=journal, ledger=ledger, key=key, operation=operation,
                    input_sha256=input_hash, execute=execute,
                )
                validate_frozen_receipt(row["payload"], frozen, operation)
                modes[mode] += 1
            completed += 1
            if completed % 10 == 0:
                print(json.dumps({"stage": "a0_query", "completed_traces": completed,
                                  "expected_traces": EXPECTED_TRACES}, sort_keys=True), flush=True)
        require(completed == EXPECTED_TRACES and len(ledger.rows) == EXPECTED_OPERATIONS, "COMPLETE_OPERATION_COUNT")
        require(journal.pending is None and len(journal.completed) == EXPECTED_OPERATIONS, "COMPLETE_JOURNAL_COUNT")
        model_forwards = reader.model_forward_calls
        reader.close(); reader = None; result["model_unloads"] = 1
        import torch
        gc.collect(); torch.cuda.empty_cache()
        allocated_after_close = int(torch.cuda.memory_allocated(0))
        require(allocated_after_close < 1024 ** 3, "MISTRAL_NOT_RELEASED")
        journal.close(); journal = None; ledger.close(); ledger = None
        for before in input_records:
            require(record(before["path"]) == before, "INPUT_CHANGED:" + str(before["path"]))
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_DEVELOPMENT_A0_QUERY_PENDING_INDEPENDENT",
            completed_traces=completed, logical_operations=EXPECTED_OPERATIONS,
            operation_modes=dict(modes), physical_model_forwards=model_forwards,
            gpu_allocated_after_close_bytes=allocated_after_close,
            elapsed_seconds=elapsed, input_records=len(input_records),
            native_ast_nodes=nodes, generation_boundary=boundary,
            generation_receipts=record(stage_output / "GENERATION_RECEIPTS.jsonl"),
            call_journal=record(stage_output / "CALL_JOURNAL.jsonl"),
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        result.update(
            status="FAIL_MISTRAL_DEVELOPMENT_A0_QUERY", error_type=type(exc).__name__,
            diagnostic=str(exc), traceback=traceback.format_exc(), completed_traces=completed,
            operation_modes=dict(modes), elapsed_seconds=time.perf_counter() - started,
        )
        if reader is not None:
            try: reader.close()
            except Exception: pass
        if journal is not None:
            try: journal.close()
            except Exception: pass
        if ledger is not None:
            try: ledger.close()
            except Exception: pass
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
