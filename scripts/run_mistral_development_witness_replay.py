"""Replay 18 frozen development witnesses and save first-token FP32 logits."""

from __future__ import annotations

import argparse
import collections
import gc
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    DurableLedger, LIKELIHOOD_CELLS, compact_generation_receipt,
    compact_likelihood_receipt, frozen_witness_positions, read_jsonl, record,
    recover_or_execute, sha256, validate_development_binding, verify_manifest,
    write_json_durable,
)
from scripts.run_mistral_development_a0_query import (
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256, EXPECTED_INPUT_LEDGER_SHA256,
    EXPECTED_POOL_MANIFEST_SHA256, EXPECTED_RETRIEVAL_MANIFEST_SHA256,
    EXPECTED_RUNTIME_MANIFEST_SHA256, acquire_gpu_mutex, evidence_rows,
    load_original_native, validate_asset_manifest,
)
from scripts.run_mistral_development_a1_likelihood import reconstruct_e1
from scripts.run_mistral_development_repair import legacy_manifest_member_paths
from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal, MistralNF4Reader, object_sha256, require,
)


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q3"
EXPECTED_POSITIONS = 18
OPERATIONS = ("a0", "repair_query", "a1", "L00", "L01", "L10", "L11")
EXPECTED_OPERATIONS = EXPECTED_POSITIONS * len(OPERATIONS)
VECTOR_SIZE = 32_768
VECTOR_BYTES = VECTOR_SIZE * 4
MIN_DISK_FREE_BYTES = 30 * 1024 ** 3
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60


def stage_validation_binding(root: Path, stage: str, expected_status: str,
                             data_name: str, data_hash_field: str) -> tuple[Path, Path]:
    namespace = root / stage
    validation = root / f"{stage}_validation/VALIDATION.json"
    require((namespace / "SHA256_MANIFEST.json").is_file() and validation.is_file(),
            "PRIOR_STAGE_MISSING:" + stage)
    verify_manifest(namespace, sha256(namespace / "SHA256_MANIFEST.json"))
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == expected_status
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value[data_hash_field] == sha256(namespace / data_name)
            and value["call_journal_sha256"] == sha256(namespace / "CALL_JOURNAL.jsonl"),
            "PRIOR_VALIDATION_BINDING:" + stage)
    return namespace, validation


def vector_log_probability(vector: np.ndarray, selected_token_id: int) -> float:
    require(vector.dtype == np.float32 and vector.shape == (VECTOR_SIZE,)
            and np.isfinite(vector).all(), "VECTOR_SCHEMA")
    require(0 <= selected_token_id < VECTOR_SIZE, "SELECTED_TOKEN_ID")
    maximum = float(np.max(vector))
    log_normalizer = maximum + math.log(math.fsum(
        float(math.exp(float(value) - maximum)) for value in vector
    ))
    value = float(vector[selected_token_id]) - log_normalizer
    require(math.isfinite(value), "VECTOR_LOG_PROBABILITY")
    return value


def write_vector_once(path: Path, vector: np.ndarray) -> dict:
    value = np.asarray(vector, dtype=np.float32)
    require(value.shape == (VECTOR_SIZE,) and np.isfinite(value).all(), "VECTOR_SCHEMA")
    raw = value.tobytes(order="C")
    require(len(raw) == VECTOR_BYTES, "VECTOR_BYTE_COUNT")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == raw, "EXISTING_VECTOR_MISMATCH")
    else:
        with path.open("xb") as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    value_record = record(path)
    require(value_record["size_bytes"] == VECTOR_BYTES, "VECTOR_RECORD_SIZE")
    value_record.update(dtype="float32", shape=[VECTOR_SIZE], byte_order=sys.byteorder)
    return value_record


def validate_witness_payload(payload: dict, *, position: int, operation: str,
                             canonical_payload: dict, vector_root: Path) -> None:
    require(payload["position"] == position and payload["operation"] == operation,
            "WITNESS_IDENTITY")
    require(payload["canonical_payload_sha256"] == object_sha256(canonical_payload)
            and payload["replay_receipt"] == canonical_payload, "WITNESS_CANONICAL_MATCH")
    vector = payload["vector"]
    path = (vector_root / vector["path"]).resolve()
    require(path.is_relative_to(vector_root) and path.stat().st_size == vector["size_bytes"] == VECTOR_BYTES
            and sha256(path) == vector["sha256"] and vector["dtype"] == "float32"
            and vector["shape"] == [VECTOR_SIZE], "WITNESS_VECTOR_BINDING")
    values = np.fromfile(path, dtype=np.float32)
    recomputed = vector_log_probability(values, payload["selected_token_id"])
    require(abs(recomputed - payload["recomputed_log_probability_float64"]) <= 1e-12
            and abs(recomputed - payload["canonical_selected_log_probability"]) <= 2e-4,
            "WITNESS_LOG_PROBABILITY")


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
    original, asset = args.project_root.resolve(), args.asset.resolve()
    root = (OUTPUT_PARENT / args.output_name).resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve()
            and root.parent == OUTPUT_PARENT.resolve(), "FIXED_ROOTS")
    a0_stage, a0_validation = stage_validation_binding(
        root, "a0_query", "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY",
        "GENERATION_RECEIPTS.jsonl", "generation_receipts_sha256",
    )
    repair_stage, repair_validation = stage_validation_binding(
        root, "repair", "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_REPAIR",
        "REPAIR_BINDINGS.jsonl", "repair_bindings_sha256",
    )
    a1_stage, a1_validation = stage_validation_binding(
        root, "a1_likelihood", "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_A1_LIKELIHOOD",
        "MODEL_RECEIPTS.jsonl", "model_receipts_sha256",
    )
    stage_output = root / "witness_replay"
    require(not any((stage_output / name).exists() for name in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json", "SHA256_MANIFEST.json")),
            "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    started = time.perf_counter(); reader = journal = ledger = mutex = None
    completed = 0; modes = collections.Counter()
    result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "witness_replay", "gold_values_read": 0, "scientific_fits": 0,
        "test_rows_read": 0, "bge_model_loads": 0, "nli_model_loads": 0,
        "model_loads": 0, "model_unloads": 0,
    }
    try:
        if not args.resume: stage_output.mkdir(parents=True, exist_ok=False)
        import psutil
        require(psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES, "DISK_FREE_ADMISSION")
        mutex = acquire_gpu_mutex()
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
                and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256, "INPUT_FREEZE")
        runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
        pool_root = original / "outputs/daa_v2_fresh_v1/pool_freeze"
        retrieval_root = original / "outputs/daa_v2_fresh_v1/retrieval_freeze"
        paths = [
            *legacy_manifest_member_paths(
                original, runtime_root, EXPECTED_RUNTIME_MANIFEST_SHA256,
            ),
            *legacy_manifest_member_paths(
                original, pool_root, EXPECTED_POOL_MANIFEST_SHA256,
            ),
            *legacy_manifest_member_paths(
                original, retrieval_root, EXPECTED_RETRIEVAL_MANIFEST_SHA256,
            ),
            *verify_manifest(
                input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
            ),
            *verify_manifest(
                a0_stage, sha256(a0_stage / "SHA256_MANIFEST.json"),
            ),
            root / "EXECUTABLE_FREEZE.json",
            a0_validation,
            *verify_manifest(
                repair_stage, sha256(repair_stage / "SHA256_MANIFEST.json"),
            ),
            repair_validation,
            *verify_manifest(
                a1_stage, sha256(a1_stage / "SHA256_MANIFEST.json"),
            ),
            a1_validation,
        ]
        control_paths = [
            Path(__file__), REPO / "scripts/validate_mistral_development_witness_replay.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/run_mistral_development_a0_query.py",
            REPO / "scripts/validate_mistral_development_a0_query.py",
            REPO / "scripts/run_mistral_development_repair.py",
            REPO / "scripts/validate_mistral_development_repair.py",
            REPO / "scripts/run_mistral_development_a1_likelihood.py",
            REPO / "scripts/validate_mistral_development_a1_likelihood.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_ACQUISITION_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_REPAIR_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_A1_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_WITNESS_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            original / "prompts/baseline_v1.txt", original / "prompts/repair_missing_v1.txt",
            runtime_root / "runtime_support.py", runtime_root / "native_runtime.py",
            runtime_root / "RUNTIME_CONFIG_FREEZE.json", runtime_root / "SYNTHETIC_TEST_RESULT_V2.json",
            runtime_root / "trace_manifest.jsonl",
        ]
        records = [record(path) for path in sorted(
            {Path(path).resolve() for path in [*paths, *control_paths]}, key=str
        )]
        assets = validate_asset_manifest(asset)
        by_path = {item["path"]: item for item in [*records, *assets]}
        require(len(by_path) == len(records) + len(assets),
                "UNIQUE_WITNESS_INPUTS")
        input_records = [by_path[path] for path in sorted(by_path)]
        freeze = {
            "status": "FROZEN_BEFORE_FORMAL_WITNESS_REPLAY", "source_commit": commit,
            "stage": "witness_replay", "expected_positions": EXPECTED_POSITIONS,
            "operations": list(OPERATIONS), "expected_operations": EXPECTED_OPERATIONS,
            "vector_size": VECTOR_SIZE, "expected_raw_vector_bytes": EXPECTED_OPERATIONS * VECTOR_BYTES,
            "inputs": input_records,
            "environment": {key: os.environ.get(key) for key in (
                "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY",
                "TOKENIZERS_PARALLELISM", "PYTHONHASHSEED", "CUBLAS_WORKSPACE_CONFIG",
            )},
            "host": platform.platform(), "python": str(Path(sys.executable).resolve()),
            "scope": "18 frozen development positions; exact replay only; BGE/NLI/Gold/test/fit forbidden",
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume: require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                                "RESUME_FREEZE_MISMATCH")
        else: write_json_durable(freeze_path, freeze)
        loader, native, nodes, boundary = load_original_native(original)
        traces = list(read_jsonl(runtime_root / "trace_manifest.jsonl"))
        frozen_rows = list(read_jsonl(frozen_ledger))
        development = validate_development_binding(traces, frozen_rows)
        positions = frozen_witness_positions(development)
        require(len(positions) == EXPECTED_POSITIONS, "WITNESS_POSITION_COUNT")
        a0_rows = list(read_jsonl(a0_stage / "GENERATION_RECEIPTS.jsonl"))
        a0_map = {row["operation_key"]: row["payload"] for row in a0_rows}
        repair_rows = list(read_jsonl(repair_stage / "REPAIR_BINDINGS.jsonl"))
        repair_map = {row["payload"]["position"]: row["payload"] for row in repair_rows}
        a1_rows = list(read_jsonl(a1_stage / "MODEL_RECEIPTS.jsonl"))
        a1_map = {row["operation_key"]: row["payload"] for row in a1_rows}
        require(len(a0_map) == 27_000 and len(repair_map) == 13_500 and len(a1_map) == 67_500,
                "CANONICAL_ROW_COUNTS")
        journal = DurableOperationJournal(stage_output / "CALL_JOURNAL.jsonl", resume=args.resume)
        ledger = DurableLedger(stage_output / "WITNESS_RECEIPTS.jsonl", resume=args.resume)
        require(len(ledger.rows) <= EXPECTED_OPERATIONS, "RESUME_LEDGER_COUNT")
        reader = MistralNF4Reader(
            asset=asset, answer_prompt=original / "prompts/baseline_v1.txt",
            repair_prompt=original / "prompts/repair_missing_v1.txt",
        )
        reader.load(); result["model_loads"] = 1

        class NoEmbeddingBackend:
            dimension = 768
            def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN_IN_WITNESS_REPLAY")
            def encode_documents(self, *_args, **_kwargs): raise RuntimeError("DOCUMENT_EMBEDDING_FORBIDDEN")

        backend = NoEmbeddingBackend(); current_dataset = None; data = None
        for position in positions:
            trace, frozen = traces[position], development[position]
            dataset, retriever, sample_id = trace["dataset"], trace["retriever"], trace["sample_id"]
            if dataset != current_dataset:
                data = loader.restore_dataset(dataset, native, backend); current_dataset = dataset
            question = data["questions"][sample_id]
            e0 = loader.original_evidence(trace, data, native)
            e1 = reconstruct_e1(native, e0, repair_map[position], data)
            private_e0, private_e1 = evidence_rows(e0), evidence_rows(e1)
            a0 = a0_map[f"{position:05d}:a0"]["parsed_text"]
            a1 = a1_map[f"{position:05d}:a1"]["parsed_text"]
            branches = {
                "L00": (private_e0, a0), "L01": (private_e1, a0),
                "L10": (private_e0, a1), "L11": (private_e1, a1),
            }
            for operation in OPERATIONS:
                canonical_payload = (
                    a0_map[f"{position:05d}:{operation}"] if operation in {"a0", "repair_query"}
                    else a1_map[f"{position:05d}:{operation}"]
                )
                replay_key = f"replay:{position:05d}:{operation}"
                operation_type = "likelihood" if operation in LIKELIHOOD_CELLS else operation
                input_value = {
                    "position": position, "operation": operation,
                    "canonical_payload_sha256": object_sha256(canonical_payload),
                    "question": question,
                    "evidence": (private_e0 if operation in {"a0", "repair_query"}
                                 else private_e1 if operation == "a1" else branches[operation][0]),
                    "answer": None if operation not in LIKELIHOOD_CELLS else branches[operation][1],
                }
                def execute(operation=operation, operation_type=operation_type,
                            canonical_payload=canonical_payload, question=question,
                            private_e0=private_e0, private_e1=private_e1,
                            trace=trace, frozen=frozen, branches=branches):
                    if operation in {"a0", "repair_query", "a1"}:
                        evidence = private_e0 if operation in {"a0", "repair_query"} else private_e1
                        generated = reader.generate(
                            stage=operation, question=question, evidence=evidence,
                            capture_full_vocab_first_step=True,
                        )
                        replay = compact_generation_receipt(generated.receipt)
                        replay.update({
                            "dataset": trace["dataset"], "retriever": trace["retriever"],
                            "sample_id": trace["sample_id"], "position": trace["position"],
                            "role": frozen["role"], "question_sha256": object_sha256(question),
                            "evidence_sha256": object_sha256(evidence),
                        })
                        vector = generated.first_step_logits
                        require(replay["generated_token_ids"], "EMPTY_GENERATION_WITNESS")
                        selected_token_id = replay["generated_token_ids"][0]
                        canonical_probability = replay["chosen_log_probabilities"][0]
                    else:
                        evidence, answer = branches[operation]
                        scored = reader.likelihood(
                            question=question, evidence=evidence, answer=answer,
                            capture_full_vocab_first_target=True,
                        )
                        target_ids = scored.receipt["target_token_ids"]
                        replay = compact_likelihood_receipt(scored.receipt, cell=operation)
                        replay.update({
                            "dataset": trace["dataset"], "retriever": trace["retriever"],
                            "sample_id": trace["sample_id"], "position": trace["position"],
                            "role": frozen["role"], "question_sha256": object_sha256(question),
                            "evidence_sha256": object_sha256(evidence),
                        })
                        vector = scored.first_target_logits
                        selected_token_id = target_ids[0]
                        canonical_probability = replay["chosen_log_probabilities"][0]
                    require(replay == canonical_payload and vector is not None,
                            "REPLAY_NOT_CANONICAL")
                    relative = Path("vectors") / f"{position:05d}_{operation}.f32"
                    vector_record = write_vector_once(stage_output / relative, vector)
                    vector_record["path"] = relative.as_posix()
                    recomputed = vector_log_probability(np.asarray(vector, dtype=np.float32), selected_token_id)
                    require(abs(recomputed - canonical_probability) <= 2e-4,
                            "REPLAY_VECTOR_PROBABILITY")
                    return {
                        "position": position, "operation": operation,
                        "operation_type": operation_type,
                        "canonical_payload_sha256": object_sha256(canonical_payload),
                        "replay_receipt": replay, "vector": vector_record,
                        "selected_token_id": int(selected_token_id),
                        "canonical_selected_log_probability": float(canonical_probability),
                        "recomputed_log_probability_float64": recomputed,
                    }
                row, mode = recover_or_execute(
                    journal=journal, ledger=ledger, key=replay_key,
                    operation=operation_type, input_sha256=object_sha256(input_value),
                    execute=execute,
                )
                validate_witness_payload(row["payload"], position=position,
                                         operation=operation, canonical_payload=canonical_payload,
                                         vector_root=stage_output)
                modes[mode] += 1; completed += 1
                print(json.dumps({"stage": "witness_replay", "completed_operations": completed,
                                  "expected_operations": EXPECTED_OPERATIONS}, sort_keys=True), flush=True)
        require(completed == EXPECTED_OPERATIONS and len(ledger.rows) == EXPECTED_OPERATIONS,
                "COMPLETE_OPERATION_COUNT")
        require(journal.pending is None and len(journal.completed) == EXPECTED_OPERATIONS,
                "COMPLETE_JOURNAL_COUNT")
        physical_forwards = reader.model_forward_calls
        reader.close(); reader = None; result["model_unloads"] = 1
        import torch
        gc.collect(); torch.cuda.empty_cache(); allocated_after = int(torch.cuda.memory_allocated(0))
        require(allocated_after < 1024 ** 3, "MISTRAL_NOT_RELEASED")
        journal.close(); journal = None; ledger.close(); ledger = None
        for item in input_records: require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started; require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_DEVELOPMENT_WITNESS_REPLAY_PENDING_INDEPENDENT",
            witness_positions=positions, completed_operations=completed,
            logical_operations=EXPECTED_OPERATIONS, operation_modes=dict(modes),
            physical_model_forwards=physical_forwards,
            raw_vector_bytes=EXPECTED_OPERATIONS * VECTOR_BYTES,
            cuda_allocated_after_close_bytes=allocated_after, elapsed_seconds=elapsed,
            native_ast_nodes=nodes, generation_boundary=boundary,
            witness_receipts=record(stage_output / "WITNESS_RECEIPTS.jsonl"),
            call_journal=record(stage_output / "CALL_JOURNAL.jsonl"),
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result); seal(stage_output)
        print(result["status"], flush=True); return 0
    except Exception as exc:
        result.update(status="FAIL_MISTRAL_DEVELOPMENT_WITNESS_REPLAY",
                      error_type=type(exc).__name__, diagnostic=str(exc),
                      traceback=traceback.format_exc(), completed_operations=completed,
                      operation_modes=dict(modes), elapsed_seconds=time.perf_counter() - started)
        if reader is not None:
            try: reader.close()
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
