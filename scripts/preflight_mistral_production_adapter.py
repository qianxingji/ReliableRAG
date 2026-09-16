"""Execute one invented-only exact-model gate for the production adapter."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal,
    MistralNF4Reader,
    REVISION,
    canonical,
    object_sha256,
    require,
)


REPO = Path(__file__).resolve().parents[1]
ASSET_MANIFEST_SHA256 = "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
EXPECTED_VERSIONS = {
    "torch": "2.7.1+cu128", "transformers": "4.53.2",
    "accelerate": "1.8.1", "bitsandbytes": "0.50.2",
    "sentencepiece": "0.2.1", "protobuf": "7.36.1",
    "numpy": "2.2.6", "psutil": "7.0.0",
}
EXPECTED_OPERATION_KEYS = (
    "invented:a0", "invented:repair_query", "invented:a1",
    "invented:L00", "invented:L01", "invented:L10", "invented:L11",
)
MAX_WITNESS_BYTES = 8 * 1024 * 1024
MAX_GPU_RESERVED_BYTES = 14 * 1024 ** 3
MAX_PROCESS_PEAK_BYTES = 20 * 1024 ** 3
MAX_WALL_SECONDS = 20 * 60


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha256(value: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(value, dtype="<f4").tobytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical(row) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_json(path: Path, value: object) -> None:
    require(not path.exists(), "REFUSE_OVERWRITE:" + str(path))
    with path.open("xb") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def record(path: Path) -> dict[str, object]:
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}


def evidence(city: str, country: str) -> list[dict[str, object]]:
    facts = (
        ("Geography", f"{city} is the capital of {country}."),
        ("Rivers", "Northport is located beside the invented River Azure."),
        ("People", "Ada was born in Northport in this synthetic fixture."),
        ("Institutions", "The Example Institute is in Southville."),
        ("History", "All names in this fixture are invented except the city-country fact."),
    )
    return [
        {"rank": index, "document_id": f"fixture-{index}", "title": title, "text": text,
         "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(), "score": float(6 - index)}
        for index, (title, text) in enumerate(facts, 1)
    ]


def seal(output: Path) -> None:
    files = []
    for path in sorted(output.rglob("*")):
        if path.is_file():
            row = record(path)
            row["path"] = path.relative_to(output).as_posix()
            files.append(row)
    write_json(output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files,
        "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--answer-prompt", required=True, type=Path)
    parser.add_argument("--repair-prompt", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--attempt-log", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    asset, overlay = args.asset.resolve(), args.overlay.resolve()
    answer_prompt, repair_prompt = args.answer_prompt.resolve(), args.repair_prompt.resolve()
    protocol, attempt_log, output = args.protocol.resolve(), args.attempt_log.resolve(), args.output.resolve()
    require(not output.exists(), "OUTPUT_EXISTS")
    require(asset.is_dir() and overlay.is_dir(), "RUNTIME_PATHS")
    require(sha256(asset / "ASSET_MANIFEST.json") == ASSET_MANIFEST_SHA256, "ASSET_MANIFEST")
    require(answer_prompt.is_file() and repair_prompt.is_file() and protocol.is_file(), "CONTROL_FILES")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    if attempt_log.exists():
        prior = [json.loads(line) for line in attempt_log.read_text(encoding="utf-8").splitlines() if line]
        require(not any(row.get("event") == "adapter_preflight_started" for row in prior), "ONE_ATTEMPT_ONLY")
    required_environment = {
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false",
        "PYTHONHASHSEED": "0", "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
    }
    require(all(os.environ.get(key) == value for key, value in required_environment.items()), "FROZEN_ENVIRONMENT")
    resolved = [Path(value).resolve() for value in sys.path if value]
    require(overlay in resolved, "OVERLAY_NOT_ON_SYS_PATH")
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    append_jsonl(attempt_log, {
        "event": "adapter_preflight_started", "utc": utc_now(), "source_commit": commit,
        "protocol_sha256": sha256(protocol), "project_rows_read": 0, "gold_values_read": 0,
        "scientific_fits": 0,
    })
    reader = None
    journal = None
    result: dict[str, object] = {"status": "FAIL", "cas_q3_status": "NOT READY"}
    try:
        import importlib.metadata
        import psutil
        import torch

        versions = {name: importlib.metadata.version(name) for name in EXPECTED_VERSIONS}
        require(versions == EXPECTED_VERSIONS, "VERSION_SET")
        # On this Windows/PyTorch build, reset_peak_memory_stats(0) rejects the
        # integer device until a concrete CUDA device has been initialized.
        # Querying its properties is metadata-only and precedes every model load.
        device_properties = torch.cuda.get_device_properties(0)
        require(device_properties.name == "NVIDIA GeForce RTX 5060 Ti", "GPU_IDENTITY")
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(0)
        gpu_free_before, gpu_total = (int(value) for value in torch.cuda.mem_get_info(0))
        ram_before = int(psutil.virtual_memory().available)
        process = psutil.Process()
        e0, e1 = evidence("Paris", "France"), evidence("Lyon", "France")
        question = "Which city is identified as the capital in the evidence?"
        reader = MistralNF4Reader(asset=asset, answer_prompt=answer_prompt, repair_prompt=repair_prompt)
        reader.load()
        journal = DurableOperationJournal(output / "CALL_JOURNAL.jsonl", resume=False)
        receipt_path = output / "OPERATION_RECEIPTS.jsonl"
        receipt_count = 0
        witnesses: dict[str, np.ndarray] = {}
        receipts: dict[str, dict] = {}

        def run_generation(key: str, stage: str, evidence_rows: list[dict]) -> dict:
            nonlocal receipt_count
            inputs = {"stage": stage, "question": question, "evidence": evidence_rows}
            input_hash = object_sha256(inputs)
            require(not journal.begin(operation_key=key, operation=stage, input_sha256=input_hash), "FRESH_CALL_EXPECTED")
            generated = reader.generate(
                stage=stage, question=question, evidence=evidence_rows,
                capture_full_vocab_first_step=True,
            )
            require(generated.first_step_logits is not None, "EMPTY_GENERATION_WITNESS")
            row = {"operation_key": key, "operation": stage, "input_sha256": input_hash, "receipt": generated.receipt}
            append_jsonl(receipt_path, row); receipt_count += 1
            journal.complete(operation_key=key, result_sha256=object_sha256(row))
            witnesses[key.replace(":", "_") + "_first_step_logits_f32"] = np.asarray(
                generated.first_step_logits, dtype="<f4"
            )
            receipts[key] = row
            return generated.receipt

        a0 = run_generation("invented:a0", "a0", e0)
        repair = run_generation("invented:repair_query", "repair_query", e0)
        a1 = run_generation("invented:a1", "a1", e1)
        require(a0["parsed_text"] and a1["parsed_text"] and repair["parsed_text"], "NONEMPTY_PARSED_OUTPUTS")

        likelihood_specs = (
            ("invented:L00", e0, a0["parsed_text"]),
            ("invented:L01", e1, a0["parsed_text"]),
            ("invented:L10", e0, a1["parsed_text"]),
            ("invented:L11", e1, a1["parsed_text"]),
        )
        for key, evidence_rows, answer in likelihood_specs:
            inputs = {"cell": key[-3:], "question": question, "evidence": evidence_rows, "answer": answer}
            input_hash = object_sha256(inputs)
            require(not journal.begin(operation_key=key, operation="likelihood", input_sha256=input_hash),
                    "FRESH_CALL_EXPECTED")
            scored = reader.likelihood(
                question=question, evidence=evidence_rows, answer=answer,
                capture_full_vocab_first_target=True,
            )
            require(scored.first_target_logits is not None, "EMPTY_LIKELIHOOD_WITNESS")
            row = {"operation_key": key, "operation": "likelihood", "input_sha256": input_hash,
                   "receipt": scored.receipt}
            append_jsonl(receipt_path, row); receipt_count += 1
            journal.complete(operation_key=key, result_sha256=object_sha256(row))
            witnesses[key.replace(":", "_") + "_first_target_logits_f32"] = np.asarray(
                scored.first_target_logits, dtype="<f4"
            )
            receipts[key] = row
        journal.close(); journal = None
        require(tuple(receipts) == EXPECTED_OPERATION_KEYS and receipt_count == 7, "OPERATION_ORDER")
        model_forwards = reader.model_forward_calls
        reader.close(); reader = None
        torch.cuda.synchronize()
        allocated_after_close = int(torch.cuda.memory_allocated(0))
        require(allocated_after_close < 1024 ** 3, "MODEL_NOT_RELEASED")
        witness_path = output / "FULL_VOCAB_WITNESS.npz"
        np.savez_compressed(witness_path, **witnesses)
        require(witness_path.stat().st_size <= MAX_WITNESS_BYTES, "WITNESS_SIZE")
        peak_reserved = int(torch.cuda.max_memory_reserved(0))
        peak_allocated = int(torch.cuda.max_memory_allocated(0))
        wall = time.perf_counter() - started
        process_peak = int(process.memory_info().peak_wset)
        require(peak_reserved <= MAX_GPU_RESERVED_BYTES, "GPU_PEAK_RESERVED")
        require(process_peak <= MAX_PROCESS_PEAK_BYTES, "PROCESS_PEAK")
        require(wall <= MAX_WALL_SECONDS, "WALL_TIME")
        result = {
            "schema_version": 1,
            "status": "PASS_MISTRAL_PRODUCTION_ADAPTER_INVENTED_PREFLIGHT_PENDING_INDEPENDENT",
            "scientific_status": "NO_PROJECT_DATA_OR_GOLD_OR_FIT",
            "cas_q3_status": "NOT READY", "source_commit": commit,
            "repo_id": "mistralai/Mistral-7B-Instruct-v0.3", "revision": REVISION,
            "protocol_sha256": sha256(protocol),
            "adapter_source": record(REPO / "src/arbitration/mistral_reader_runtime.py"),
            "producer_source": record(Path(__file__)), "versions": versions,
            "asset_manifest_sha256": ASSET_MANIFEST_SHA256,
            "operation_keys": list(receipts), "operation_count": len(receipts),
            "generation_calls": 3, "likelihood_calls": 4,
            "model_loads": 1, "model_unloads": 1, "model_forward_calls": model_forwards,
            "project_rows_read": 0, "gold_values_read": 0, "scientific_fits": 0,
            "answer_outputs": {"a0": a0["parsed_text"], "a1": a1["parsed_text"]},
            "repair_query": repair["parsed_text"], "repair_parser_fallback": repair["parser_fallback"],
            "witness": record(witness_path),
            "witness_arrays": {
                name: {"shape": list(value.shape), "dtype": str(value.dtype), "sha256_float32_le": array_sha256(value)}
                for name, value in witnesses.items()
            },
            "receipts": record(receipt_path), "journal": record(output / "CALL_JOURNAL.jsonl"),
            "resources": {
                "gpu_free_before_bytes": gpu_free_before, "gpu_total_bytes": gpu_total,
                "gpu_name": device_properties.name,
                "host_ram_available_before_bytes": ram_before,
                "gpu_peak_reserved_bytes": peak_reserved, "gpu_peak_allocated_bytes": peak_allocated,
                "gpu_allocated_after_close_bytes": allocated_after_close,
                "process_peak_working_set_bytes": process_peak, "wall_seconds": wall,
            },
        }
        write_json(output / "REPORT.json", result)
        seal(output)
        append_jsonl(attempt_log, {
            "event": "adapter_preflight_passed", "utc": utc_now(),
            "source_commit": commit, "report_sha256": sha256(output / "REPORT.json"),
            "witness_sha256": sha256(witness_path), "project_rows_read": 0,
            "gold_values_read": 0, "scientific_fits": 0,
        })
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        result.update(
            status="FAIL_MISTRAL_PRODUCTION_ADAPTER_INVENTED_PREFLIGHT",
            error_type=type(exc).__name__, diagnostic=str(exc), traceback=traceback.format_exc(),
            project_rows_read=0, gold_values_read=0, scientific_fits=0,
        )
        if journal is not None:
            journal.close()
        if reader is not None:
            reader.close()
        write_json(output / "FAILURE.json", result)
        seal(output)
        append_jsonl(attempt_log, {
            "event": "adapter_preflight_failed", "utc": utc_now(),
            "source_commit": commit, "error_type": type(exc).__name__, "diagnostic": str(exc),
            "project_rows_read": 0, "gold_values_read": 0, "scientific_fits": 0,
        })
        print(result["status"], result["diagnostic"], flush=True)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
