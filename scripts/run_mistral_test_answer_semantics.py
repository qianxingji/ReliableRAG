"""Run/resume label-blind BGE answer semantics for sealed Mistral test pairs."""

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
    DurableLedger,
    read_jsonl,
    record,
    recover_or_execute,
    sha256,
    verify_manifest,
    write_json_durable,
)
from scripts.mistral_development_scoring_common import (
    DurableStageJournal,
    write_bytes_once,
)
from scripts.run_mistral_development_a0_query import (
    EXPECTED_RUNTIME_MANIFEST_SHA256,
    load_original_native,
    validate_manifest_pin,
)
from scripts.run_mistral_test_a0_query import (
    DATASETS,
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_INPUT_LEDGER_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
    EXPECTED_TEST_TRACE_SHA256,
    acquire_gpu_mutex,
    validate_selected_manifest,
    validate_test_binding,
)
from src.arbitration.mistral_reader_runtime import (
    object_sha256,
    require,
    text_sha256,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_ANSWERS = 36_000
EXPECTED_BATCHES = 2_250
BATCH_SIZE = 16
DIMENSION = 768
VECTOR_BYTES_PER_ANSWER = DIMENSION * 4
DATASET_ORDER = DATASETS
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
BGE_PREFLIGHT_SHA256 = (
    "f29a5ad13c2d8ce6cab3bb6331bd315837c70907fa9d71725339af07baeb5790"
)
BGE_INVENTORY_SHA256 = (
    "1a52cb26692f2407b59ea4233a9f1b3b63a200a2b04fc33cff416ea7acfc2712"
)
MIN_DISK_FREE_BYTES = 30 * 1024 ** 3
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60


def validate_witness_gate(root: Path) -> tuple[Path, Path]:
    namespace = root / "witness_replay"
    validation = root / "witness_replay_validation/VALIDATION.json"
    require(
        (namespace / "SHA256_MANIFEST.json").is_file()
        and validation.is_file(),
        "WITNESS_ACCEPTANCE_REQUIRED",
    )
    verify_manifest(namespace, sha256(namespace / "SHA256_MANIFEST.json"))
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(
        value["status"]
        == "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_WITNESS_REPLAY"
        and value["producer_receipt_sha256"]
        == sha256(namespace / "STAGE_RECEIPT.json")
        and value["witness_receipts_sha256"]
        == sha256(namespace / "WITNESS_RECEIPTS.jsonl")
        and value["call_journal_sha256"]
        == sha256(namespace / "CALL_JOURNAL.jsonl")
        and value["project_gold_values_read"] == 0
        and value["test_gold_values_read"] == 0
        and value["scientific_fits"] == 0,
        "WITNESS_VALIDATION_BINDING",
    )
    witness_freeze = json.loads(
        (namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8")
    )
    frozen_inputs = {
        Path(item["path"]).resolve(): item for item in witness_freeze["inputs"]
    }
    for stage in ("a0_query", "repair", "a1_likelihood"):
        for path in (
            root / stage / "SHA256_MANIFEST.json",
            root / f"{stage}_validation/VALIDATION.json",
        ):
            resolved = path.resolve()
            require(
                resolved in frozen_inputs
                and record(resolved) == frozen_inputs[resolved],
                "WITNESS_FROZEN_PRIOR:" + stage,
            )
    return namespace, validation


def validate_bge_assets(original: Path) -> tuple[Path, list[dict]]:
    preflight = (
        original
        / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight"
        / "PREFLIGHT_INPUT_VERIFICATION.json"
    )
    require(sha256(preflight) == BGE_PREFLIGHT_SHA256, "BGE_PREFLIGHT_PIN")
    value = json.loads(preflight.read_text(encoding="utf-8"))
    inventory = value["parents"]["runtime_model_inventory"]["bge_dense_encoder"]
    require(
        inventory["status"] == "PASS"
        and inventory["revision"] == BGE_REVISION
        and inventory["inventory_sha256"] == BGE_INVENTORY_SHA256
        and inventory["file_count"] == 6
        and inventory["total_size_bytes"] == 438_899_684,
        "BGE_INVENTORY",
    )
    snapshot = (original / inventory["snapshot_relative_path"]).resolve()
    records = [record(preflight)]
    for item in inventory["file_inventory"]:
        path = (snapshot / item["path"]).resolve()
        require(
            path.is_relative_to(snapshot)
            and path.stat().st_size == item["size_bytes"]
            and sha256(path) == item["sha256"],
            "BGE_ASSET:" + item["path"],
        )
        records.append(record(path))
    require(len(records) == 7, "BGE_ASSET_COUNT")
    return snapshot, records


def validate_semantic_payload(
    payload: dict,
    *,
    dataset: str,
    batch_index: int,
    global_batch_index: int,
    bindings: list[dict],
    token_fields: dict,
    stage_output: Path,
) -> None:
    require(
        payload["dataset"] == dataset
        and payload["batch_index"] == batch_index
        and payload["global_batch_index"] == global_batch_index
        and payload["bindings"] == bindings,
        "SEMANTIC_BATCH_IDENTITY",
    )
    row_count = len(bindings)
    require(
        0 < row_count <= BATCH_SIZE
        and row_count % 2 == 0
        and payload["vector_shape"] == [row_count, DIMENSION],
        "SEMANTIC_BATCH_SHAPE",
    )
    require(
        payload["token_fields"] == token_fields
        and set(token_fields)
        == {"input_ids", "token_type_ids", "attention_mask"}
        and all(len(value) == row_count for value in token_fields.values())
        and len({len(row) for value in token_fields.values() for row in value})
        == 1
        and 0 < len(token_fields["input_ids"][0]) <= 512
        and payload["model_forward_calls"] == 1,
        "SEMANTIC_TOKEN_FIELDS",
    )
    vector = payload["vector"]
    path = (stage_output / vector["path"]).resolve()
    require(
        path.is_relative_to(stage_output)
        and path.stat().st_size
        == vector["size_bytes"]
        == row_count * VECTOR_BYTES_PER_ANSWER
        and sha256(path) == vector["sha256"]
        and vector["dtype"] == "float32"
        and vector["shape"] == [row_count, DIMENSION]
        and vector["byte_order"] == "little",
        "SEMANTIC_VECTOR_BINDING",
    )
    values = np.fromfile(path, dtype="<f4").reshape(row_count, DIMENSION)
    require(np.isfinite(values).all(), "SEMANTIC_VECTOR_FINITE")
    norms = np.linalg.norm(values.astype(np.float64), axis=1)
    require(
        np.max(np.abs(norms - 1.0)) <= 0.01,
        "SEMANTIC_VECTOR_NORMALIZATION",
    )
    require(
        len(payload["semantic_rows"]) == row_count // 2,
        "SEMANTIC_PAIR_COUNT",
    )
    for pair_index, row in enumerate(payload["semantic_rows"]):
        similarity = float(
            values[2 * pair_index] @ values[2 * pair_index + 1]
        )
        require(
            math.isfinite(similarity)
            and row["answer_semantic_agreement"] == similarity,
            "SEMANTIC_DOT_PRODUCT",
        )


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path)
            item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(
        stage_output / "SHA256_MANIFEST.json",
        {
            "status": "PASS",
            "files": files,
            "excludes_only": "SHA256_MANIFEST.json",
            "exact_recursive_coverage": True,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    original, root = args.project_root.resolve(), args.test_root.resolve()
    require(
        original == ORIGINAL_ROOT.resolve()
        and root == TEST_ROOT.resolve()
        and sys.byteorder == "little",
        "FIXED_ROOTS_OR_BYTE_ORDER",
    )
    witness_stage, witness_validation = validate_witness_gate(root)
    a0_stage, a1_stage = root / "a0_query", root / "a1_likelihood"
    a0_validation = root / "a0_query_validation/VALIDATION.json"
    a1_validation = root / "a1_likelihood_validation/VALIDATION.json"
    repair_stage = root / "repair"
    repair_validation = root / "repair_validation/VALIDATION.json"
    for stage, validation in (
        (a0_stage, a0_validation),
        (repair_stage, repair_validation),
        (a1_stage, a1_validation),
    ):
        verify_manifest(stage, sha256(stage / "SHA256_MANIFEST.json"))
        require(validation.is_file(), "PRIOR_VALIDATION_MISSING")
    stage_output = root / "answer_semantics"
    require(
        not any(
            (stage_output / name).exists()
            for name in (
                "STAGE_RECEIPT.json",
                "STAGE_FAILURE.json",
                "SHA256_MANIFEST.json",
            )
        ),
        "TERMINAL_STAGE_IMMUTABLE",
    )
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(
        not subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=REPO, text=True
        ).strip(),
        "COMMIT_BEFORE_EXECUTION",
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    started = time.perf_counter()
    bge = hook = journal = ledger = mutex = None
    completed = 0
    modes = collections.Counter()
    observed_forwards = 0
    result: dict[str, object] = {
        "status": "FAIL",
        "cas_q3_status": "NOT READY",
        "source_commit": commit,
        "stage": "answer_semantics",
        "project_gold_values_read": 0,
        "test_gold_values_read": 0,
        "test_outcome_values_read": 0,
        "scientific_fits": 0,
        "test_input_rows_read": 0,
        "mistral_model_loads": 0,
        "nli_model_loads": 0,
        "bge_model_loads": 0,
        "bge_model_unloads": 0,
    }
    try:
        if not args.resume:
            stage_output.mkdir(parents=True, exist_ok=False)
        import psutil

        require(
            psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES,
            "DISK_FREE_ADMISSION",
        )
        mutex = acquire_gpu_mutex()
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(
            sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
            and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256,
            "INPUT_FREEZE_PIN",
        )
        preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
        trace_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
        require(sha256(trace_path) == EXPECTED_TEST_TRACE_SHA256, "TEST_TRACE_PIN")
        source_paths = [
            *validate_selected_manifest(
                preparation,
                EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
                ("TRACE_MANIFEST_PRIVATE.jsonl",),
            ),
            *verify_manifest(input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256),
        ]
        for stage, validation in (
            (a0_stage, a0_validation),
            (repair_stage, repair_validation),
            (a1_stage, a1_validation),
            (witness_stage, witness_validation),
        ):
            source_paths.extend(
                verify_manifest(stage, sha256(stage / "SHA256_MANIFEST.json"))
            )
            source_paths.append(validation)
        _snapshot, bge_records = validate_bge_assets(original)
        runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
        retrieval_support = (
            original
            / "outputs/daa_v2_fresh_v1/retrieval_freeze/retrieval_support.py"
        )
        source_paths.append(
            Path(
                validate_manifest_pin(
                    runtime_root / "SHA256_MANIFEST.json",
                    EXPECTED_RUNTIME_MANIFEST_SHA256,
                )["path"]
            )
        )
        control_paths = [
            Path(__file__),
            REPO / "scripts/validate_mistral_test_answer_semantics.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/mistral_development_scoring_common.py",
            REPO / "scripts/run_mistral_development_a0_query.py",
            REPO / "scripts/run_mistral_test_a0_query.py",
            REPO / "scripts/validate_mistral_test_a0_query.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_TEST_ANSWER_SEMANTICS_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            runtime_root / "runtime_support.py",
            runtime_root / "native_runtime.py",
            runtime_root / "SYNTHETIC_TEST_RESULT_V2.json",
            retrieval_support,
            Path(sys.executable),
        ]
        unique_paths = sorted(
            {Path(path).resolve() for path in [*source_paths, *control_paths]},
            key=str,
        )
        input_records = [record(path) for path in unique_paths]
        existing = {item["path"] for item in input_records}
        input_records.extend(
            item for item in bge_records if item["path"] not in existing
        )
        require(
            len({item["path"] for item in input_records}) == len(input_records),
            "UNIQUE_EXECUTION_INPUTS",
        )
        freeze = {
            "status": "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_ANSWER_SEMANTICS",
            "source_commit": commit,
            "stage": "answer_semantics",
            "expected_traces": EXPECTED_TRACES,
            "expected_answers": EXPECTED_ANSWERS,
            "expected_batches": EXPECTED_BATCHES,
            "expected_raw_vector_bytes": (
                EXPECTED_ANSWERS * VECTOR_BYTES_PER_ANSWER
            ),
            "batch_size": BATCH_SIZE,
            "dimension": DIMENSION,
            "byte_order": "little",
            "test_gold_access": "FORBIDDEN",
            "test_outcome_access": "FORBIDDEN",
            "scientific_fit_access": "FORBIDDEN",
            "inputs": input_records,
            "environment": {
                key: os.environ.get(key)
                for key in (
                    "HF_HUB_OFFLINE",
                    "TRANSFORMERS_OFFLINE",
                    "HF_HUB_DISABLE_TELEMETRY",
                    "TOKENIZERS_PARALLELISM",
                    "PYTHONHASHSEED",
                    "CUBLAS_WORKSPACE_CONFIG",
                )
            },
            "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "scope": (
                "test a0/a1 document-mode BGE only; "
                "Mistral/NLI/Gold/outcome/fit/tuning forbidden"
            ),
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(
                json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                "RESUME_FREEZE_MISMATCH",
            )
        else:
            write_json_durable(freeze_path, freeze)

        _wrapper, native, nodes, boundary = load_original_native(original)
        traces = list(read_jsonl(trace_path))
        test_rows = validate_test_binding(traces, read_jsonl(frozen_ledger))
        result["test_input_rows_read"] = EXPECTED_TRACES
        a0_rows = list(read_jsonl(a0_stage / "GENERATION_RECEIPTS.jsonl"))
        a1_rows = list(read_jsonl(a1_stage / "MODEL_RECEIPTS.jsonl"))
        require(
            len(a0_rows) == 36_000 and len(a1_rows) == 90_000,
            "ANSWER_SOURCE_ROW_COUNTS",
        )
        a0_map = {
            row["payload"]["position"]: row["payload"]
            for row in a0_rows
            if row["operation"] == "a0"
        }
        a1_map = {
            row["payload"]["position"]: row["payload"]
            for row in a1_rows
            if row["operation"] == "a1"
        }
        require(
            len(a0_map) == len(a1_map) == EXPECTED_TRACES,
            "ANSWER_SOURCE_COUNTS",
        )
        journal = DurableStageJournal(
            stage_output / "CALL_JOURNAL.jsonl",
            resume=args.resume,
            allowed_operations={"answer_semantic_batch"},
        )
        ledger = DurableLedger(
            stage_output / "BATCH_RECEIPTS.jsonl", resume=args.resume
        )
        bge = native.ExactLocalBGEBackend(
            model_cache_dir=original / "data/models/huggingface"
        )
        bge._ensure_loaded()
        result["bge_model_loads"] = 1
        require(
            bge.model.__class__.__name__ == "BertModel"
            and bge.model.config._commit_hash == BGE_REVISION
            and str(next(bge.model.parameters()).dtype) == "torch.bfloat16"
            and not bge.model.training
            and bge.dimension == DIMENSION,
            "BGE_IDENTITY",
        )
        observer = {"active": False, "expected": None, "calls": 0}

        def observe(_module, _args, kwargs):
            import torch

            require(
                observer["active"]
                and torch.is_inference_mode_enabled()
                and not torch.is_grad_enabled()
                and not bge.model.training,
                "BGE_FORWARD_CONTEXT",
            )
            actual = {
                name: tensor.detach().cpu().tolist()
                for name, tensor in kwargs.items()
            }
            require(actual == observer["expected"], "BGE_TOKEN_BINDING")
            observer["calls"] += 1

        hook = bge.model.register_forward_pre_hook(observe, with_kwargs=True)
        require(
            tuple(dict.fromkeys(trace["dataset"] for trace in traces))
            == DATASET_ORDER,
            "CANONICAL_DATASET_ORDER",
        )
        global_batch = 0
        for dataset in DATASET_ORDER:
            dataset_traces = [
                trace for trace in traces if trace["dataset"] == dataset
            ]
            require(len(dataset_traces) == 6_000, "DATASET_TRACE_COUNT")
            texts, bindings = [], []
            for trace in dataset_traces:
                for state, source in (("a0", a0_map), ("a1", a1_map)):
                    answer = source[trace["position"]]["parsed_text"]
                    texts.append(answer)
                    bindings.append(
                        {
                            "dataset": dataset,
                            "retriever": trace["retriever"],
                            "sample_id": trace["sample_id"],
                            "position": trace["position"],
                            "role": test_rows[trace["position"]]["role"],
                            "answer_state": state,
                            "answer_sha256": text_sha256(answer),
                        }
                    )
            require(
                len(texts) == len(bindings) == 12_000,
                "DATASET_ANSWER_COUNT",
            )
            for batch_index, start in enumerate(
                range(0, len(texts), BATCH_SIZE)
            ):
                batch_texts = texts[start : start + BATCH_SIZE]
                batch_bindings = bindings[start : start + BATCH_SIZE]
                key = f"semantic:{dataset}:{batch_index:04d}"
                input_value = {
                    "dataset": dataset,
                    "batch_index": batch_index,
                    "texts": batch_texts,
                    "bindings": batch_bindings,
                }
                expected = bge.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                )
                expected_token_fields = {
                    name: tensor.tolist() for name, tensor in expected.items()
                }

                def execute(
                    dataset=dataset,
                    batch_index=batch_index,
                    global_batch_index=global_batch,
                    batch_texts=batch_texts,
                    batch_bindings=batch_bindings,
                    token_fields=expected_token_fields,
                ):
                    nonlocal observed_forwards
                    before = observer["calls"]
                    observer.update(active=True, expected=token_fields)
                    try:
                        vectors = bge.encode_documents(batch_texts)
                    finally:
                        observer["active"] = False
                    require(
                        observer["calls"] == before + 1,
                        "ONE_BGE_FORWARD_PER_BATCH",
                    )
                    observed_forwards += 1
                    require(
                        vectors.dtype == np.float32
                        and vectors.shape == (len(batch_texts), DIMENSION)
                        and np.isfinite(vectors).all(),
                        "BGE_VECTOR_SCHEMA",
                    )
                    encoded = np.ascontiguousarray(vectors, dtype="<f4")
                    relative = (
                        Path("vectors") / f"{dataset}_{batch_index:04d}.f32"
                    )
                    write_bytes_once(
                        stage_output / relative, encoded.tobytes(order="C")
                    )
                    vector_record = record(stage_output / relative)
                    vector_record["path"] = relative.as_posix()
                    vector_record.update(
                        dtype="float32",
                        shape=[len(batch_texts), DIMENSION],
                        byte_order="little",
                    )
                    semantic_rows = []
                    for pair_index in range(len(batch_texts) // 2):
                        left = batch_bindings[2 * pair_index]
                        right = batch_bindings[2 * pair_index + 1]
                        require(
                            left["position"] == right["position"]
                            and left["answer_state"] == "a0"
                            and right["answer_state"] == "a1",
                            "BGE_PAIR_ORDER",
                        )
                        similarity = float(
                            encoded[2 * pair_index]
                            @ encoded[2 * pair_index + 1]
                        )
                        require(math.isfinite(similarity), "BGE_SEMANTIC_FINITE")
                        semantic_rows.append(
                            {
                                "dataset": left["dataset"],
                                "retriever": left["retriever"],
                                "sample_id": left["sample_id"],
                                "position": left["position"],
                                "role": left["role"],
                                "a0_sha256": left["answer_sha256"],
                                "a1_sha256": right["answer_sha256"],
                                "vector_rows": [
                                    2 * pair_index,
                                    2 * pair_index + 1,
                                ],
                                "answer_semantic_agreement": similarity,
                            }
                        )
                    return {
                        "dataset": dataset,
                        "batch_index": batch_index,
                        "global_batch_index": global_batch_index,
                        "bindings": batch_bindings,
                        "token_fields": token_fields,
                        "vector_shape": list(encoded.shape),
                        "vector": vector_record,
                        "semantic_rows": semantic_rows,
                        "model_forward_calls": 1,
                    }

                row, mode = recover_or_execute(
                    journal=journal,
                    ledger=ledger,
                    key=key,
                    operation="answer_semantic_batch",
                    input_sha256=object_sha256(input_value),
                    execute=execute,
                )
                validate_semantic_payload(
                    row["payload"],
                    dataset=dataset,
                    batch_index=batch_index,
                    global_batch_index=global_batch,
                    bindings=batch_bindings,
                    token_fields=expected_token_fields,
                    stage_output=stage_output,
                )
                modes[mode] += 1
                completed += 1
                global_batch += 1
                if completed % 50 == 0:
                    print(
                        json.dumps(
                            {
                                "stage": "answer_semantics",
                                "completed_batches": completed,
                                "expected_batches": EXPECTED_BATCHES,
                            },
                            sort_keys=True,
                        ),
                        flush=True,
                    )
            require(batch_index == 749, "DATASET_BATCH_COUNT")
        require(
            completed == EXPECTED_BATCHES
            and global_batch == EXPECTED_BATCHES
            and len(ledger.rows) == EXPECTED_BATCHES,
            "COMPLETE_BATCH_COUNT",
        )
        semantic_rows = [
            item
            for row in ledger.rows
            for item in row["payload"]["semantic_rows"]
        ]
        semantic_rows.sort(key=lambda row: row["position"])
        require(
            len(semantic_rows) == EXPECTED_TRACES
            and [row["position"] for row in semantic_rows]
            == list(range(EXPECTED_TRACES)),
            "SEMANTIC_ROW_ORDER",
        )
        semantic_raw = b"".join(
            json.dumps(
                row,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
            for row in semantic_rows
        )
        write_bytes_once(stage_output / "SEMANTIC_ROWS.jsonl", semantic_raw)
        require(
            journal.pending is None
            and len(journal.completed) == EXPECTED_BATCHES,
            "COMPLETE_JOURNAL_COUNT",
        )
        hook.remove()
        hook = None
        bge.close()
        bge = None
        result["bge_model_unloads"] = 1
        import torch

        gc.collect()
        torch.cuda.empty_cache()
        allocated_after = int(torch.cuda.memory_allocated(0))
        require(allocated_after < 1024 ** 3, "BGE_NOT_RELEASED")
        journal.close()
        journal = None
        ledger.close()
        ledger = None
        for item in input_records:
            require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_TEST_ANSWER_SEMANTICS_PENDING_INDEPENDENT",
            completed_batches=completed,
            logical_bge_forwards=EXPECTED_BATCHES,
            observed_bge_forwards_current_process=observed_forwards,
            operation_modes=dict(modes),
            completed_traces=EXPECTED_TRACES,
            answer_vectors=EXPECTED_ANSWERS,
            raw_vector_bytes=EXPECTED_ANSWERS * VECTOR_BYTES_PER_ANSWER,
            cuda_allocated_after_close_bytes=allocated_after,
            elapsed_seconds=elapsed,
            native_ast_nodes=nodes,
            generation_boundary=boundary,
            batch_receipts=record(stage_output / "BATCH_RECEIPTS.jsonl"),
            semantic_rows=record(stage_output / "SEMANTIC_ROWS.jsonl"),
            call_journal=record(stage_output / "CALL_JOURNAL.jsonl"),
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        result.update(
            status="FAIL_MISTRAL_TEST_ANSWER_SEMANTICS",
            error_type=type(exc).__name__,
            diagnostic=str(exc),
            traceback=traceback.format_exc(),
            completed_batches=completed,
            observed_bge_forwards_current_process=observed_forwards,
            operation_modes=dict(modes),
            elapsed_seconds=time.perf_counter() - started,
        )
        if hook is not None:
            try:
                hook.remove()
            except Exception:
                pass
        if bge is not None:
            try:
                bge.close()
            except Exception:
                pass
        if journal is not None:
            try:
                journal.close()
            except Exception:
                pass
        if ledger is not None:
            try:
                ledger.close()
            except Exception:
                pass
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
