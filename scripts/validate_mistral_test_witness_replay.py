"""Independently validate Mistral test witness vectors without a model."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_reader_input_freeze_common import compact_document
from scripts.validate_mistral_test_a0_query import (
    DATASETS,
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_TEST_POOL_MANIFEST_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
    asset_member_paths,
    current_manifest_member_paths,
    load_test_assets,
    object_sha,
    read_rows,
    require,
    sha256,
    source_pair,
    validate_selected_manifest,
    validate_manifest,
    validate_test_binding,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_ASSET_MANIFEST_SHA256 = (
    "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
)
EXPECTED_POSITIONS = 18
OPERATIONS = ("a0", "repair_query", "a1", "L00", "L01", "L10", "L11")
CELLS = OPERATIONS[3:]
EXPECTED_OPERATIONS = EXPECTED_POSITIONS * len(OPERATIONS)
VECTOR_SIZE = 32_768
VECTOR_BYTES = VECTOR_SIZE * 4


def validate_prior(
    root: Path, stage: str, status: str,
    data_name: str, data_hash_field: str,
) -> Path:
    namespace = root / stage
    validate_manifest(namespace)
    value = json.loads((
        root / f"{stage}_validation/VALIDATION.json"
    ).read_text(encoding="utf-8"))
    require(
        value.get("status") == status
        and value.get("producer_receipt_sha256")
        == sha256(namespace / "STAGE_RECEIPT.json")
        and value.get(data_hash_field) == sha256(namespace / data_name)
        and value.get("call_journal_sha256")
        == sha256(namespace / "CALL_JOURNAL.jsonl")
        and value.get("test_gold_values_read") == 0,
        "PRIOR_VALIDATION_BINDING:" + stage,
    )
    return namespace


def witness_positions(rows: list[dict]) -> list[int]:
    cells: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        require(row.get("cohort") == "test" and row.get("role") == "test",
                "TEST_ONLY")
        cells.setdefault(
            (row["dataset"], row["retriever"]), [],
        ).append(row["position"])
    require(len(cells) == 9 and all(values for values in cells.values()),
            "NINE_CELLS")
    result = sorted({
        value for values in cells.values()
        for value in (min(values), max(values))
    })
    require(len(result) == EXPECTED_POSITIONS, "WITNESS_POSITIONS")
    return result


def reconstruct_e1(
    e0: list[dict], payload: dict, assets: dict[str, dict[str, dict]],
    dataset: str,
) -> list[dict]:
    inserted_id = payload["inserted_document_id"]
    matches = [
        row for row in payload["ranking"]
        if row["document_id"] == inserted_id
    ]
    require(
        len(matches) == 1
        and matches[0]["rank"] == payload["inserted_candidate_rank"],
        "INSERTED_RANK",
    )
    documents = assets[dataset]["documents"]
    require(inserted_id in documents, "INSERTED_DOCUMENT_MEMBERSHIP")
    inserted = compact_document(documents[inserted_id], 5)
    e1 = [*e0[:4], inserted]
    require(
        [row["document_id"] for row in e0] == payload["e0_ids"]
        and [row["document_id"] for row in e1] == payload["e1_ids"]
        and payload["replaced_document_id"] == e0[4]["document_id"],
        "E1_BINDING",
    )
    return e1


def render_evidence(evidence: list[dict]) -> str:
    require(
        len(evidence) == 5
        and [row["rank"] for row in evidence] == [1, 2, 3, 4, 5],
        "EVIDENCE_SCHEMA",
    )
    headers = [
        f"[Evidence {row['rank']} | id={row['document_id']} | "
        f"title={row['title']}]\n"
        for row in evidence
    ]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = 16_000 - sum(
        len(separator) + len(header)
        for separator, header in zip(separators, headers, strict=True)
    )
    require(remaining >= 0, "EVIDENCE_HEADERS")
    chunks = []
    for separator, header, row in zip(
            separators, headers, evidence, strict=True):
        body = str(row["text"]).strip()
        included = body[:remaining]
        remaining -= len(included)
        chunks.append(separator + header + included)
    return "".join(chunks)


def selected_target_id(
    tokenizer, template: str, question: str,
    evidence: list[dict], answer: str,
) -> int:
    user = template.format(
        question=question, evidence=render_evidence(evidence),
    )
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )
    prompt_ids = [
        int(value) for value in
        tokenizer(prompt, add_special_tokens=False)["input_ids"]
    ]
    full_ids = [
        int(value) for value in
        tokenizer(prompt + answer, add_special_tokens=False)["input_ids"]
    ]
    require(
        full_ids[:len(prompt_ids)] == prompt_ids
        and len(full_ids) > len(prompt_ids),
        "TARGET_PREFIX",
    )
    return full_ids[len(prompt_ids)]


def vector_log_probability(vector: np.ndarray, selected: int) -> float:
    require(
        vector.dtype == np.float32 and vector.shape == (VECTOR_SIZE,)
        and np.isfinite(vector).all() and 0 <= selected < VECTOR_SIZE,
        "VECTOR_SCHEMA",
    )
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
    pending = None
    completed = {}
    recoveries = 0
    for event in events:
        if event["event"] == "intent":
            require(pending is None, "OVERLAPPING_INTENT")
            pending = event
        elif event["event"] == "resume_pending":
            require(
                pending is not None
                and event["operation_key"] == pending["operation_key"]
                and event["input_sha256"] == pending["input_sha256"],
                "RESUME_EVENT",
            )
            recoveries += 1
        else:
            require(
                event["event"] == "result" and pending is not None
                and event["operation_key"] == pending["operation_key"],
                "RESULT_EVENT",
            )
            row = row_map[event["operation_key"]]
            require(
                event["operation"] == pending["operation"] == row["operation"]
                and event["result_sha256"] == object_sha(row),
                "RESULT_HASH",
            )
            completed[event["operation_key"]] = event
            pending = None
    require(pending is None and set(completed) == set(row_map),
            "COMPLETE_EVENTS")
    return recoveries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original, asset, root = (
        args.project_root.resolve(), args.asset.resolve(),
        args.test_root.resolve(),
    )
    output = (
        args.output.resolve() if args.output else
        (root / "witness_replay_validation/VALIDATION.json").resolve()
    )
    require(
        original == ORIGINAL_ROOT.resolve()
        and root == TEST_ROOT.resolve()
        and output
        == (root / "witness_replay_validation/VALIDATION.json").resolve()
        and not output.exists(),
        "FIXED_ROOTS_OR_OUTPUT",
    )
    require(
        sha256(asset / "ASSET_MANIFEST.json")
        == EXPECTED_ASSET_MANIFEST_SHA256,
        "ASSET_MANIFEST_PIN",
    )
    a0_stage = validate_prior(
        root, "a0_query",
        "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY",
        "GENERATION_RECEIPTS.jsonl", "generation_receipts_sha256",
    )
    repair_stage = validate_prior(
        root, "repair",
        "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_REPAIR",
        "REPAIR_BINDINGS.jsonl", "repair_bindings_sha256",
    )
    a1_stage = validate_prior(
        root, "a1_likelihood",
        "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_A1_LIKELIHOOD",
        "MODEL_RECEIPTS.jsonl", "model_receipts_sha256",
    )
    namespace = root / "witness_replay"
    validate_manifest(namespace)
    stage = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8",
    ))
    require(
        stage.get("status")
        == "PASS_MISTRAL_TEST_WITNESS_REPLAY_PENDING_INDEPENDENT"
        and stage.get("completed_operations") == EXPECTED_OPERATIONS
        and stage.get("raw_vector_bytes")
        == EXPECTED_OPERATIONS * VECTOR_BYTES,
        "PRODUCER_STATUS",
    )
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(
        encoding="utf-8",
    ))
    require(
        freeze.get("source_commit") == stage.get("source_commit")
        and freeze.get("status")
        == "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_WITNESS_REPLAY"
        and freeze.get("expected_positions") == EXPECTED_POSITIONS
        and freeze.get("operations") == list(OPERATIONS)
        and freeze.get("expected_operations") == EXPECTED_OPERATIONS
        and freeze.get("vector_size") == VECTOR_SIZE
        and freeze.get("expected_raw_vector_bytes")
        == EXPECTED_OPERATIONS * VECTOR_BYTES
        and freeze.get("test_gold_access") == "FORBIDDEN",
        "EXECUTABLE_FREEZE",
    )
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(
            path.is_file() and path.stat().st_size == item["size_bytes"]
            and sha256(path) == item["sha256"],
            "FROZEN_INPUT",
        )
    frozen_paths = {
        Path(item["path"]).resolve() for item in freeze["inputs"]
    }
    require(len(frozen_paths) == len(freeze["inputs"]),
            "UNIQUE_FROZEN_INPUTS")
    preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
    pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
    input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
    pool_relatives = tuple(
        f"{folder}/{dataset}.jsonl"
        for folder in ("pools", "runtime") for dataset in DATASETS
    ) + ("INDEPENDENT_VALIDATION.json",)
    required_inputs = {
        *{path.resolve() for path in validate_selected_manifest(
            preparation, EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
            ("TRACE_MANIFEST_PRIVATE.jsonl",),
        )},
        *{path.resolve() for path in validate_selected_manifest(
            pool_root, EXPECTED_TEST_POOL_MANIFEST_SHA256, pool_relatives,
        )},
        *current_manifest_member_paths(
            input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
        ),
        *current_manifest_member_paths(
            a0_stage, sha256(a0_stage / "SHA256_MANIFEST.json"),
        ),
        *current_manifest_member_paths(
            repair_stage, sha256(repair_stage / "SHA256_MANIFEST.json"),
        ),
        *current_manifest_member_paths(
            a1_stage, sha256(a1_stage / "SHA256_MANIFEST.json"),
        ),
        *asset_member_paths(asset),
        (root / "a0_query_validation/VALIDATION.json").resolve(),
        (root / "repair_validation/VALIDATION.json").resolve(),
        (root / "a1_likelihood_validation/VALIDATION.json").resolve(),
        (REPO / "scripts/run_mistral_test_witness_replay.py").resolve(),
        Path(__file__).resolve(),
        (REPO / "scripts/mistral_development_acquisition_common.py").resolve(),
        (REPO / "scripts/mistral_reader_input_freeze_common.py").resolve(),
        (REPO / "scripts/run_mistral_test_a0_query.py").resolve(),
        (REPO / "scripts/run_mistral_test_a1_likelihood.py").resolve(),
        (REPO / "scripts/validate_mistral_test_a0_query.py").resolve(),
        (REPO / "src/arbitration/mistral_reader_runtime.py").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_WITNESS_INPUT_GRAPH_AMENDMENT_2026-09-17.md").resolve(),
        (original / "prompts/baseline_v1.txt").resolve(),
        (original / "prompts/repair_missing_v1.txt").resolve(),
        Path(sys.executable).resolve(),
    }
    require(required_inputs == frozen_paths, "NONEXACT_FROZEN_INPUT_GRAPH")
    rows = read_rows(namespace / "WITNESS_RECEIPTS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(rows) == EXPECTED_OPERATIONS, "WITNESS_ROW_COUNT")
    recoveries = validate_journal(rows, events)
    a0_map = {
        row["operation_key"]: row["payload"]
        for row in read_rows(a0_stage / "GENERATION_RECEIPTS.jsonl")
    }
    repair_map = {
        row["payload"]["position"]: row["payload"]
        for row in read_rows(repair_stage / "REPAIR_BINDINGS.jsonl")
    }
    a1_map = {
        row["operation_key"]: row["payload"]
        for row in read_rows(a1_stage / "MODEL_RECEIPTS.jsonl")
    }
    require(
        len(a0_map) == 36_000
        and len(repair_map) == 18_000
        and len(a1_map) == 90_000,
        "CANONICAL_COUNTS",
    )

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        asset,
        use_fast=True,
        local_files_only=True,
        trust_remote_code=False,
        legacy=False,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    require(
        tokenizer.is_fast
        and type(tokenizer).__name__ == "LlamaTokenizerFast"
        and tokenizer.vocab_size == VECTOR_SIZE,
        "TOKENIZER_IDENTITY",
    )
    template = (
        original / "prompts/baseline_v1.txt"
    ).read_text(encoding="utf-8")
    traces = read_rows(preparation / "TRACE_MANIFEST_PRIVATE.jsonl")
    test_rows = validate_test_binding(
        traces,
        read_rows(input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"),
    )
    positions = witness_positions(test_rows)
    require(stage.get("witness_positions") == positions,
            "WITNESS_POSITION_BINDING")
    assets = load_test_assets(pool_root)
    maximum_error = 0.0
    checks = 0

    for witness_index, position in enumerate(positions):
        trace = traces[position]
        require(trace["position"] == test_rows[position]["position"] == position,
                "POSITION")
        dataset = trace["dataset"]
        question, private_e0 = source_pair(trace, assets)
        private_e1 = reconstruct_e1(
            private_e0, repair_map[position], assets, dataset,
        )
        a0 = a0_map[f"{position:05d}:a0"]["parsed_text"]
        a1 = a1_map[f"{position:05d}:a1"]["parsed_text"]
        branches = {
            "L00": (private_e0, a0),
            "L01": (private_e1, a0),
            "L10": (private_e0, a1),
            "L11": (private_e1, a1),
        }
        for operation_index, operation in enumerate(OPERATIONS):
            sequence = witness_index * len(OPERATIONS) + operation_index
            row = rows[sequence]
            payload = row["payload"]
            canonical = (
                a0_map[f"{position:05d}:{operation}"]
                if operation in {"a0", "repair_query"}
                else a1_map[f"{position:05d}:{operation}"]
            )
            expected_key = f"replay:{position:05d}:{operation}"
            operation_type = "likelihood" if operation in CELLS else operation
            require(
                row["sequence"] == sequence
                and row["operation_key"] == expected_key
                and row["operation"] == operation_type,
                "ROW_ORDER",
            )
            require(
                payload["position"] == position
                and payload["operation"] == operation
                and payload["operation_type"] == operation_type
                and payload["canonical_payload_sha256"] == object_sha(canonical)
                and payload["replay_receipt"] == canonical,
                "CANONICAL_REPLAY",
            )
            vector_meta = payload["vector"]
            vector_path = (namespace / vector_meta["path"]).resolve()
            require(
                vector_path.is_relative_to(namespace.resolve())
                and vector_meta["path"]
                == f"vectors/{position:05d}_{operation}.f32"
                and vector_path.stat().st_size
                == vector_meta["size_bytes"] == VECTOR_BYTES
                and sha256(vector_path) == vector_meta["sha256"]
                and vector_meta["dtype"] == "float32"
                and vector_meta["shape"] == [VECTOR_SIZE]
                and vector_meta["byte_order"] == "little",
                "VECTOR_BINDING",
            )
            vector = np.fromfile(vector_path, dtype="<f4")
            if operation in {"a0", "repair_query", "a1"}:
                selected = canonical["generated_token_ids"][0]
                expected_log_probability = (
                    canonical["chosen_log_probabilities"][0]
                )
            else:
                evidence, answer = branches[operation]
                selected = selected_target_id(
                    tokenizer, template, question, evidence, answer,
                )
                expected_log_probability = (
                    canonical["chosen_log_probabilities"][0]
                )
            recomputed = vector_log_probability(vector, selected)
            error = abs(recomputed - expected_log_probability)
            maximum_error = max(maximum_error, error)
            require(
                payload["selected_token_id"] == selected
                and payload["canonical_selected_log_probability"]
                == expected_log_probability
                and abs(payload["recomputed_log_probability_float64"]
                        - recomputed) <= 1e-12
                and error <= 2e-4,
                "SOFTMAX_RECOMPUTATION",
            )
            evidence = (
                private_e0 if operation in {"a0", "repair_query"}
                else private_e1 if operation == "a1"
                else branches[operation][0]
            )
            input_value = {
                "position": position,
                "operation": operation,
                "canonical_payload_sha256": object_sha(canonical),
                "question": question,
                "evidence": evidence,
                "answer": (
                    None if operation not in CELLS
                    else branches[operation][1]
                ),
            }
            require(row["input_sha256"] == object_sha(input_value),
                    "INPUT_HASH")
            checks += 24

    require(
        stage.get("project_gold_values_read") == 0
        and stage.get("test_gold_values_read") == 0
        and stage.get("scientific_fits") == 0
        and stage.get("test_input_rows_read") == EXPECTED_POSITIONS
        and stage.get("bge_model_loads") == 0
        and stage.get("nli_model_loads") == 0,
        "ZERO_FORBIDDEN_ACCESS",
    )
    result = {
        "status": "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_WITNESS_REPLAY",
        "cas_q3_status": "NOT READY",
        "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "witness_receipts_sha256": sha256(
            namespace / "WITNESS_RECEIPTS.jsonl",
        ),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "witness_positions": positions,
        "vectors_validated": EXPECTED_OPERATIONS,
        "raw_vector_bytes": EXPECTED_OPERATIONS * VECTOR_BYTES,
        "maximum_log_probability_error": maximum_error,
        "recovery_events": recoveries,
        "model_loads": 0,
        "model_forwards": 0,
        "project_gold_values_read": 0,
        "test_gold_values_read": 0,
        "scientific_fits": 0,
        "test_input_rows_read": EXPECTED_POSITIONS,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(
        json.dumps(
            result, sort_keys=True, indent=2, allow_nan=False,
        ).encode("utf-8") + b"\n"
    )
    print(result["status"], checks, flush=True)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
