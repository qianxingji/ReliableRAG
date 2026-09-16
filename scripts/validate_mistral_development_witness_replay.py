"""Independent tokenizer-only validation of Mistral development witness replay."""

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
    load_original_native, object_sha, read_rows, require, sha256,
)


REPO = Path(__file__).resolve().parents[1]
POSITIONS = 18
OPERATIONS = ("a0", "repair_query", "a1", "L00", "L01", "L10", "L11")
CELLS = OPERATIONS[3:]
EXPECTED_OPERATIONS = POSITIONS * len(OPERATIONS)
VECTOR_SIZE = 32_768
VECTOR_BYTES = VECTOR_SIZE * 4


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members, "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_prior(root: Path, stage: str, status: str,
                   data_name: str, data_hash_field: str) -> Path:
    namespace = root / stage; validate_manifest(namespace)
    value = json.loads((root / f"{stage}_validation/VALIDATION.json").read_text(encoding="utf-8"))
    require(value["status"] == status
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value[data_hash_field] == sha256(namespace / data_name)
            and value["call_journal_sha256"] == sha256(namespace / "CALL_JOURNAL.jsonl"),
            "PRIOR_VALIDATION_BINDING:" + stage)
    return namespace


def witness_positions(rows: list[dict]) -> list[int]:
    cells: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        require(row.get("cohort") == "development", "DEVELOPMENT_ONLY")
        cells.setdefault((row["dataset"], row["retriever"]), []).append(row["position"])
    require(len(cells) == 9 and all(values for values in cells.values()), "NINE_CELLS")
    result = sorted({value for values in cells.values() for value in (min(values), max(values))})
    require(len(result) == POSITIONS, "WITNESS_POSITIONS")
    return result


def reconstruct_e1(native, e0, payload: dict, data: dict):
    inserted_id = payload["inserted_document_id"]
    matches = [row for row in payload["ranking"] if row["document_id"] == inserted_id]
    require(len(matches) == 1 and matches[0]["rank"] == payload["inserted_candidate_rank"],
            "INSERTED_RANK")
    source = data["documents"][inserted_id]
    inserted = native.RankedDocument(
        5, inserted_id, source.content_hash, float(matches[0]["score"]),
        source.title, source.text,
    )
    e1 = tuple((*e0[:4], inserted))
    require([row.document_id for row in e1] == payload["e1_ids"], "E1_BINDING")
    return e1


def evidence_rows(evidence) -> list[dict]:
    return [row.as_private_dict() for row in evidence]


def render_evidence(evidence: list[dict]) -> str:
    headers = [
        f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n"
        for row in evidence
    ]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = 16_000 - sum(
        len(separator) + len(header)
        for separator, header in zip(separators, headers, strict=True)
    )
    chunks = []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip(); included = body[:remaining]
        remaining -= len(included); chunks.append(separator + header + included)
    return "".join(chunks)


def selected_target_id(tokenizer, template: str, question: str,
                       evidence: list[dict], answer: str) -> int:
    user = template.format(question=question, evidence=render_evidence(evidence))
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}], tokenize=False,
        add_generation_prompt=True,
    )
    prompt_ids = [int(value) for value in tokenizer(prompt, add_special_tokens=False)["input_ids"]]
    full_ids = [int(value) for value in tokenizer(prompt + answer, add_special_tokens=False)["input_ids"]]
    require(full_ids[:len(prompt_ids)] == prompt_ids and len(full_ids) > len(prompt_ids),
            "TARGET_PREFIX")
    return full_ids[len(prompt_ids)]


def vector_log_probability(vector: np.ndarray, selected: int) -> float:
    require(vector.dtype == np.float32 and vector.shape == (VECTOR_SIZE,)
            and np.isfinite(vector).all() and 0 <= selected < VECTOR_SIZE,
            "VECTOR_SCHEMA")
    maximum = float(np.max(vector))
    normalizer = maximum + math.log(math.fsum(
        float(math.exp(float(value) - maximum)) for value in vector
    ))
    result = float(vector[selected]) - normalizer
    require(math.isfinite(result), "VECTOR_LOG_PROBABILITY")
    return result


def validate_journal(rows: list[dict], events: list[dict]) -> int:
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_ROWS")
    pending = None; completed = {}; recoveries = 0
    for event in events:
        if event["event"] == "intent":
            require(pending is None, "OVERLAPPING_INTENT"); pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None and event["operation_key"] == pending["operation_key"]
                    and event["input_sha256"] == pending["input_sha256"], "RESUME_EVENT")
            recoveries += 1
        else:
            require(event["event"] == "result" and pending is not None
                    and event["operation_key"] == pending["operation_key"], "RESULT_EVENT")
            row = row_map[event["operation_key"]]
            require(event["operation"] == pending["operation"] == row["operation"]
                    and event["result_sha256"] == object_sha(row), "RESULT_HASH")
            completed[event["operation_key"]] = event; pending = None
    require(pending is None and set(completed) == set(row_map), "COMPLETE_EVENTS")
    return recoveries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original, asset = args.project_root.resolve(), args.asset.resolve()
    root, output = args.root.resolve(), args.output.resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve() and not output.exists(),
            "FIXED_ROOT_OR_OUTPUT")
    a0_stage = validate_prior(
        root, "a0_query", "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY",
        "GENERATION_RECEIPTS.jsonl", "generation_receipts_sha256",
    )
    repair_stage = validate_prior(
        root, "repair", "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_REPAIR",
        "REPAIR_BINDINGS.jsonl", "repair_bindings_sha256",
    )
    a1_stage = validate_prior(
        root, "a1_likelihood", "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_A1_LIKELIHOOD",
        "MODEL_RECEIPTS.jsonl", "model_receipts_sha256",
    )
    namespace = root / "witness_replay"; validate_manifest(namespace)
    stage = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(stage["status"] == "PASS_MISTRAL_DEVELOPMENT_WITNESS_REPLAY_PENDING_INDEPENDENT"
            and stage["completed_operations"] == EXPECTED_OPERATIONS
            and stage["raw_vector_bytes"] == EXPECTED_OPERATIONS * VECTOR_BYTES,
            "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == stage["source_commit"]
            and freeze["expected_operations"] == EXPECTED_OPERATIONS, "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "FROZEN_INPUT")
    rows = read_rows(namespace / "WITNESS_RECEIPTS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(rows) == EXPECTED_OPERATIONS, "WITNESS_ROW_COUNT")
    recoveries = validate_journal(rows, events)
    a0_map = {row["operation_key"]: row["payload"]
              for row in read_rows(a0_stage / "GENERATION_RECEIPTS.jsonl")}
    repair_map = {row["payload"]["position"]: row["payload"]
                  for row in read_rows(repair_stage / "REPAIR_BINDINGS.jsonl")}
    a1_map = {row["operation_key"]: row["payload"]
              for row in read_rows(a1_stage / "MODEL_RECEIPTS.jsonl")}
    require(len(a0_map) == 27_000 and len(repair_map) == 13_500 and len(a1_map) == 67_500,
            "CANONICAL_COUNTS")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        asset, use_fast=True, local_files_only=True, trust_remote_code=False, legacy=False,
    )
    tokenizer.pad_token = tokenizer.eos_token; tokenizer.padding_side = "left"
    template = (original / "prompts/baseline_v1.txt").read_text(encoding="utf-8")
    runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    traces = read_rows(runtime_root / "trace_manifest.jsonl")
    frozen_rows = [row for row in read_rows(
        REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl"
    ) if row.get("cohort") == "development"]
    positions = witness_positions(frozen_rows)
    require(stage["witness_positions"] == positions, "WITNESS_POSITION_BINDING")
    loader, native = load_original_native(original)

    class NoEmbeddingBackend:
        dimension = 768
        def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")
        def encode_documents(self, *_args, **_kwargs): raise RuntimeError("DOCUMENT_EMBEDDING_FORBIDDEN")

    backend = NoEmbeddingBackend(); current_dataset = None; data = None
    maximum_error = 0.0; checks = 0
    for witness_index, position in enumerate(positions):
        trace, frozen = traces[position], frozen_rows[position]
        require(trace["position"] == frozen["position"] == position, "POSITION")
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
        for operation_index, operation in enumerate(OPERATIONS):
            sequence = witness_index * len(OPERATIONS) + operation_index
            row = rows[sequence]; payload = row["payload"]
            canonical = (a0_map[f"{position:05d}:{operation}"]
                         if operation in {"a0", "repair_query"}
                         else a1_map[f"{position:05d}:{operation}"])
            expected_key = f"replay:{position:05d}:{operation}"
            operation_type = "likelihood" if operation in CELLS else operation
            require(row["sequence"] == sequence and row["operation_key"] == expected_key
                    and row["operation"] == operation_type, "ROW_ORDER")
            require(payload["position"] == position and payload["operation"] == operation
                    and payload["operation_type"] == operation_type
                    and payload["canonical_payload_sha256"] == object_sha(canonical)
                    and payload["replay_receipt"] == canonical, "CANONICAL_REPLAY")
            vector_meta = payload["vector"]
            vector_path = (namespace / vector_meta["path"]).resolve()
            require(vector_path.is_relative_to(namespace)
                    and vector_meta["path"] == f"vectors/{position:05d}_{operation}.f32"
                    and vector_path.stat().st_size == vector_meta["size_bytes"] == VECTOR_BYTES
                    and sha256(vector_path) == vector_meta["sha256"]
                    and vector_meta["dtype"] == "float32"
                    and vector_meta["shape"] == [VECTOR_SIZE], "VECTOR_BINDING")
            vector = np.fromfile(vector_path, dtype=np.float32)
            if operation in {"a0", "repair_query", "a1"}:
                selected = canonical["generated_token_ids"][0]
                expected_log_probability = canonical["chosen_log_probabilities"][0]
            else:
                evidence, answer = branches[operation]
                selected = selected_target_id(tokenizer, template, question, evidence, answer)
                expected_log_probability = canonical["chosen_log_probabilities"][0]
            recomputed = vector_log_probability(vector, selected)
            error = abs(recomputed - expected_log_probability); maximum_error = max(maximum_error, error)
            require(payload["selected_token_id"] == selected
                    and payload["canonical_selected_log_probability"] == expected_log_probability
                    and abs(payload["recomputed_log_probability_float64"] - recomputed) <= 1e-12
                    and error <= 2e-4, "SOFTMAX_RECOMPUTATION")
            evidence = (private_e0 if operation in {"a0", "repair_query"}
                        else private_e1 if operation == "a1" else branches[operation][0])
            input_value = {
                "position": position, "operation": operation,
                "canonical_payload_sha256": object_sha(canonical),
                "question": question, "evidence": evidence,
                "answer": None if operation not in CELLS else branches[operation][1],
            }
            require(row["input_sha256"] == object_sha(input_value), "INPUT_HASH")
            checks += 24
    require(stage["gold_values_read"] == stage["scientific_fits"] == stage["test_rows_read"] == 0
            and stage["bge_model_loads"] == stage["nli_model_loads"] == 0, "ZERO_FORBIDDEN_ACCESS")
    result = {
        "status": "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_WITNESS_REPLAY",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "witness_receipts_sha256": sha256(namespace / "WITNESS_RECEIPTS.jsonl"),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "witness_positions": positions, "vectors_validated": EXPECTED_OPERATIONS,
        "raw_vector_bytes": EXPECTED_OPERATIONS * VECTOR_BYTES,
        "maximum_log_probability_error": maximum_error,
        "recovery_events": recoveries, "model_loads": 0, "model_forwards": 0,
        "gold_values_read": 0, "scientific_fits": 0, "test_rows_read": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
