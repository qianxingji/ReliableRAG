"""Independent tokenizer-only validation of Mistral development answer semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_mistral_development_a0_query import (
    canonical, object_sha, read_rows, require, sha256,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_TRACES = 13_500
EXPECTED_ANSWERS = 27_000
EXPECTED_BATCHES = 1_689
BATCH_SIZE = 16
DIMENSION = 768
VECTOR_BYTES_PER_ANSWER = DIMENSION * 4
DATASET_ORDER = ("hotpotqa", "2wikimultihopqa", "musique")
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
BGE_PREFLIGHT_SHA256 = "f29a5ad13c2d8ce6cab3bb6331bd315837c70907fa9d71725339af07baeb5790"
BGE_INVENTORY_SHA256 = "1a52cb26692f2407b59ea4233a9f1b3b63a200a2b04fc33cff416ea7acfc2712"


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    require(manifest["status"] == "PASS" and manifest["exact_recursive_coverage"] is True,
            "MANIFEST_STATUS")
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members, "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_witness(root: Path) -> Path:
    namespace = root / "witness_replay"; validate_manifest(namespace)
    validation_path = root / "witness_replay_validation/VALIDATION.json"
    value = json.loads(validation_path.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_WITNESS_REPLAY"
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value["witness_receipts_sha256"] == sha256(namespace / "WITNESS_RECEIPTS.jsonl")
            and value["call_journal_sha256"] == sha256(namespace / "CALL_JOURNAL.jsonl"),
            "WITNESS_VALIDATION_BINDING")
    witness_freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    frozen_inputs = {Path(item["path"]).resolve(): item for item in witness_freeze["inputs"]}
    for stage in ("a0_query", "repair", "a1_likelihood"):
        for path in (root / stage / "SHA256_MANIFEST.json",
                     root / f"{stage}_validation/VALIDATION.json"):
            resolved = path.resolve(); item = frozen_inputs.get(resolved)
            require(item is not None and resolved.stat().st_size == item["size_bytes"]
                    and sha256(resolved) == item["sha256"],
                    "WITNESS_FROZEN_PRIOR:" + stage)
    return validation_path


def validate_bge_assets(original: Path):
    preflight = original / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/PREFLIGHT_INPUT_VERIFICATION.json"
    require(sha256(preflight) == BGE_PREFLIGHT_SHA256, "BGE_PREFLIGHT_PIN")
    value = json.loads(preflight.read_text(encoding="utf-8"))
    inventory = value["parents"]["runtime_model_inventory"]["bge_dense_encoder"]
    require(inventory["status"] == "PASS" and inventory["revision"] == BGE_REVISION
            and inventory["inventory_sha256"] == BGE_INVENTORY_SHA256
            and inventory["file_count"] == 6 and inventory["total_size_bytes"] == 438_899_684,
            "BGE_INVENTORY")
    snapshot = (original / inventory["snapshot_relative_path"]).resolve()
    for item in inventory["file_inventory"]:
        path = (snapshot / item["path"]).resolve()
        require(path.is_relative_to(snapshot) and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "BGE_ASSET:" + item["path"])
    return snapshot, preflight


def validate_journal(rows: list[dict], events: list[dict]) -> int:
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_BATCH_ROWS")
    pending = None; completed = {}; recoveries = 0
    for sequence, event in enumerate(events):
        require(event["sequence"] == sequence, "JOURNAL_SEQUENCE")
        key = event["operation_key"]
        if event["event"] == "intent":
            require(pending is None and key not in completed
                    and event["operation"] == "answer_semantic_batch",
                    "JOURNAL_INTENT")
            pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None and key == pending["operation_key"]
                    and event["operation"] == pending["operation"]
                    and event["input_sha256"] == pending["input_sha256"],
                    "JOURNAL_RESUME")
            recoveries += 1
        else:
            require(event["event"] == "result" and pending is not None
                    and key == pending["operation_key"] and key in row_map,
                    "JOURNAL_RESULT")
            row = row_map[key]
            require(event["operation"] == pending["operation"] == row["operation"]
                    and pending["input_sha256"] == row["input_sha256"]
                    and event["result_sha256"] == object_sha(row), "JOURNAL_RESULT_HASH")
            completed[key] = event; pending = None
    require(pending is None and set(completed) == set(row_map), "COMPLETE_JOURNAL")
    return recoveries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original, root, output = (args.project_root.resolve(), args.root.resolve(),
                              args.output.resolve())
    require(original == Path("E:/paper/ReliableRAG").resolve() and not output.exists(),
            "FIXED_ROOT_OR_OUTPUT")
    witness_validation = validate_witness(root)
    for prior in (root / "a0_query", root / "a1_likelihood"):
        validate_manifest(prior)
    snapshot, preflight = validate_bge_assets(original)

    namespace = root / "answer_semantics"; validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "PASS_MISTRAL_DEVELOPMENT_ANSWER_SEMANTICS_PENDING_INDEPENDENT"
            and receipt["completed_batches"] == receipt["logical_bge_forwards"] == EXPECTED_BATCHES
            and receipt["completed_traces"] == EXPECTED_TRACES
            and receipt["answer_vectors"] == EXPECTED_ANSWERS
            and receipt["raw_vector_bytes"] == EXPECTED_ANSWERS * VECTOR_BYTES_PER_ANSWER
            and receipt["bge_model_loads"] == receipt["bge_model_unloads"] == 1
            and receipt["mistral_model_loads"] == receipt["nli_model_loads"] == 0
            and receipt["gold_values_read"] == receipt["scientific_fits"]
            == receipt["test_rows_read"] == 0, "PRODUCER_STATUS")
    require(sum(receipt["operation_modes"].values()) == EXPECTED_BATCHES
            and 0 <= receipt["observed_bge_forwards_current_process"] <= EXPECTED_BATCHES,
            "PRODUCER_FORWARD_ACCOUNTING")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"]
            and freeze["stage"] == "answer_semantics"
            and freeze["expected_traces"] == EXPECTED_TRACES
            and freeze["expected_answers"] == EXPECTED_ANSWERS
            and freeze["expected_batches"] == EXPECTED_BATCHES
            and freeze["batch_size"] == BATCH_SIZE and freeze["dimension"] == DIMENSION,
            "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "FROZEN_INPUT")
    frozen_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(preflight.resolve() in frozen_paths and witness_validation.resolve() in frozen_paths,
            "FROZEN_PREREQUISITES")

    batch_rows = read_rows(namespace / "BATCH_RECEIPTS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    semantic_rows_file = read_rows(namespace / "SEMANTIC_ROWS.jsonl")
    require(len(batch_rows) == EXPECTED_BATCHES
            and len(semantic_rows_file) == EXPECTED_TRACES, "OUTPUT_COUNTS")
    recoveries = validate_journal(batch_rows, events)

    traces = read_rows(original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/trace_manifest.jsonl")
    frozen_rows = [row for row in read_rows(
        REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl"
    ) if row.get("cohort") == "development"]
    require(len(traces) == len(frozen_rows) == EXPECTED_TRACES, "SOURCE_COUNTS")
    roles = {}
    for position, (trace, frozen) in enumerate(zip(traces, frozen_rows, strict=True)):
        require(trace["position"] == frozen["position"] == position
                and (trace["dataset"], trace["retriever"], trace["sample_id"])
                == (frozen["dataset"], frozen["retriever"], frozen["sample_id"])
                and frozen["role"] in {"fit", "cal"}, "SOURCE_BINDING")
        roles[position] = frozen["role"]
    a0_rows = read_rows(root / "a0_query/GENERATION_RECEIPTS.jsonl")
    a1_rows = read_rows(root / "a1_likelihood/MODEL_RECEIPTS.jsonl")
    a0_map = {row["payload"]["position"]: row["payload"]
              for row in a0_rows if row["operation"] == "a0"}
    a1_map = {row["payload"]["position"]: row["payload"]
              for row in a1_rows if row["operation"] == "a1"}
    require(len(a0_rows) == 27_000 and len(a1_rows) == 67_500
            and len(a0_map) == len(a1_map) == EXPECTED_TRACES, "ANSWER_SOURCE_COUNTS")

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, use_fast=True, local_files_only=True, trust_remote_code=False,
    )
    all_semantic_rows = []; maximum_norm_error = 0.0; checks = 0; global_batch = 0
    require(tuple(dict.fromkeys(trace["dataset"] for trace in traces)) == DATASET_ORDER,
            "CANONICAL_DATASET_ORDER")
    for dataset in DATASET_ORDER:
        dataset_traces = [trace for trace in traces if trace["dataset"] == dataset]
        require(len(dataset_traces) == 4_500, "DATASET_TRACE_COUNT")
        texts, bindings = [], []
        for trace in dataset_traces:
            for state, source in (("a0", a0_map), ("a1", a1_map)):
                answer = source[trace["position"]]["parsed_text"]
                texts.append(answer)
                bindings.append({
                    "dataset": dataset, "retriever": trace["retriever"],
                    "sample_id": trace["sample_id"], "position": trace["position"],
                    "role": roles[trace["position"]], "answer_state": state,
                    "answer_sha256": text_sha(answer),
                })
        require(len(texts) == len(bindings) == 9_000, "DATASET_ANSWER_COUNT")
        for batch_index, start in enumerate(range(0, len(texts), BATCH_SIZE)):
            row = batch_rows[global_batch]; payload = row["payload"]
            batch_texts = texts[start:start + BATCH_SIZE]
            batch_bindings = bindings[start:start + BATCH_SIZE]
            key = f"semantic:{dataset}:{batch_index:04d}"
            input_value = {"dataset": dataset, "batch_index": batch_index,
                           "texts": batch_texts, "bindings": batch_bindings}
            require(row["sequence"] == global_batch and row["operation_key"] == key
                    and row["operation"] == "answer_semantic_batch"
                    and row["input_sha256"] == object_sha(input_value), "BATCH_ROW_IDENTITY")
            require(payload["dataset"] == dataset and payload["batch_index"] == batch_index
                    and payload["global_batch_index"] == global_batch
                    and payload["bindings"] == batch_bindings
                    and payload["model_forward_calls"] == 1, "BATCH_PAYLOAD_IDENTITY")
            tokenized = tokenizer(
                batch_texts, padding=True, truncation=True,
                max_length=512, return_tensors="pt",
            )
            token_fields = {name: tensor.tolist() for name, tensor in tokenized.items()}
            require(payload["token_fields"] == token_fields
                    and set(token_fields) == {"input_ids", "token_type_ids", "attention_mask"},
                    "TOKEN_FIELDS")
            row_count = len(batch_texts)
            require(0 < row_count <= BATCH_SIZE and row_count % 2 == 0
                    and payload["vector_shape"] == [row_count, DIMENSION], "VECTOR_SHAPE")
            meta = payload["vector"]
            vector_path = (namespace / meta["path"]).resolve()
            require(vector_path.is_relative_to(namespace)
                    and meta["path"] == f"vectors/{dataset}_{batch_index:04d}.f32"
                    and vector_path.stat().st_size == meta["size_bytes"]
                    == row_count * VECTOR_BYTES_PER_ANSWER
                    and sha256(vector_path) == meta["sha256"]
                    and meta["dtype"] == "float32"
                    and meta["shape"] == [row_count, DIMENSION]
                    and meta["byte_order"] == sys.byteorder, "VECTOR_BINDING")
            vectors = np.fromfile(vector_path, dtype=np.float32).reshape(row_count, DIMENSION)
            require(np.isfinite(vectors).all(), "VECTOR_FINITE")
            norm_error = float(np.max(np.abs(np.linalg.norm(
                vectors.astype(np.float64), axis=1
            ) - 1.0)))
            maximum_norm_error = max(maximum_norm_error, norm_error)
            require(norm_error <= 0.01, "VECTOR_NORMALIZATION")
            require(len(payload["semantic_rows"]) == row_count // 2, "SEMANTIC_PAIR_COUNT")
            for pair_index, semantic in enumerate(payload["semantic_rows"]):
                left, right = batch_bindings[2 * pair_index], batch_bindings[2 * pair_index + 1]
                require(left["position"] == right["position"]
                        and left["answer_state"] == "a0" and right["answer_state"] == "a1",
                        "PAIR_ORDER")
                similarity = float(vectors[2 * pair_index] @ vectors[2 * pair_index + 1])
                expected_semantic = {
                    "dataset": left["dataset"], "retriever": left["retriever"],
                    "sample_id": left["sample_id"], "position": left["position"],
                    "role": left["role"], "a0_sha256": left["answer_sha256"],
                    "a1_sha256": right["answer_sha256"],
                    "vector_rows": [2 * pair_index, 2 * pair_index + 1],
                    "answer_semantic_agreement": similarity,
                }
                require(math.isfinite(similarity) and semantic == expected_semantic,
                        "SEMANTIC_DOT_PRODUCT")
                all_semantic_rows.append(semantic); checks += 30
            global_batch += 1
        require(batch_index == 562, "DATASET_BATCH_COUNT")
    require(global_batch == EXPECTED_BATCHES, "GLOBAL_BATCH_COUNT")
    all_semantic_rows.sort(key=lambda row: row["position"])
    require(all_semantic_rows == semantic_rows_file
            and [row["position"] for row in all_semantic_rows] == list(range(EXPECTED_TRACES)),
            "FLATTENED_SEMANTIC_ROWS")
    result = {
        "status": "PASS_INDEPENDENT_TOKENIZER_ONLY_MISTRAL_DEVELOPMENT_ANSWER_SEMANTICS",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "batch_receipts_sha256": sha256(namespace / "BATCH_RECEIPTS.jsonl"),
        "semantic_rows_sha256": sha256(namespace / "SEMANTIC_ROWS.jsonl"),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "batches_validated": EXPECTED_BATCHES, "vectors_validated": EXPECTED_ANSWERS,
        "raw_vector_bytes": EXPECTED_ANSWERS * VECTOR_BYTES_PER_ANSWER,
        "maximum_vector_norm_error": maximum_norm_error,
        "recovery_events": recoveries, "tokenizer_loads": 1,
        "model_loads": 0, "model_forwards": 0,
        "gold_values_read": 0, "scientific_fits": 0, "test_rows_read": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
