"""Emit numeric-only Mistral test outcomes after the action seal is accepted."""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_outcome_native import authenticate, native
from scripts.empirical_pool_io import checked
from scripts.mistral_development_acquisition_common import (
    read_jsonl,
    record,
    sha256,
    write_json_durable,
)
from scripts.verify_roa_artifacts import relative_path, safe_file
from src.arbitration.mistral_reader_runtime import canonical


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_QUESTIONS = 6_000
EXPECTED_DATASET_QUESTIONS = 2_000
EXPECTED_A0_OPERATIONS = 36_000
EXPECTED_A1_OPERATIONS = 90_000
EXPECTED_METRIC_VALUES = 72_000
METRIC_FIELDS = ("a0_em", "a1_em", "a0_f1", "a1_f1")
OUTCOME_FIELDS = frozenset({
    "dataset", "retriever", "sample_id", *METRIC_FIELDS,
})
MAX_STAGE_SECONDS = 2 * 60 * 60


def require(value, message):
    if not value:
        raise RuntimeError(message)


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    require(manifest_path.is_file(), "PREDECESSOR_MANIFEST_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("status") == "PASS"
            and manifest.get("exact_recursive_coverage") is True,
            "PREDECESSOR_MANIFEST_STATUS")
    members = set()
    for item in manifest.get("files", []):
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace.resolve()) and path not in members,
                "PREDECESSOR_MANIFEST_PATH")
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"],
                "PREDECESSOR_MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()},
            "PREDECESSOR_MANIFEST_COVERAGE")


def validate_action_gate(root: Path) -> tuple[Path, Path]:
    namespace = root / "action_seal"
    validation = root / "action_seal_validation/VALIDATION.json"
    validate_manifest(namespace)
    require(validation.is_file(), "ACTION_ACCEPTANCE_REQUIRED")
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    acceptance = json.loads(validation.read_text(encoding="utf-8"))
    require(receipt.get("status")
            == "PASS_MISTRAL_TEST_ACTION_SEAL_PENDING_INDEPENDENT"
            and receipt.get("N_all") == EXPECTED_TRACES
            and receipt.get("test_gold_values_read") == 0
            and receipt.get("test_outcome_values_read") == 0
            and receipt.get("action_budget_tuned") is False,
            "ACTION_RECEIPT")
    require(acceptance.get("status")
            == "PASS_INDEPENDENT_MISTRAL_TEST_ACTION_SEAL"
            and acceptance.get("producer_manifest_sha256")
            == sha256(namespace / "SHA256_MANIFEST.json")
            and acceptance.get("producer_receipt_sha256")
            == sha256(namespace / "STAGE_RECEIPT.json")
            and acceptance.get("action_rows_sha256")
            == sha256(namespace / "ACTION_ROWS.jsonl")
            and acceptance.get("validated_rows") == EXPECTED_TRACES
            and acceptance.get("test_gold_values_read") == 0
            and acceptance.get("test_outcome_values_read") == 0
            and acceptance.get("action_budget_tuned") is False,
            "ACTION_ACCEPTANCE")
    return namespace, validation


def validate_answer_source(
    root: Path,
    stage: str,
    row_file: str,
    expected_status: str,
    expected_acceptance: str,
    expected_operations: int,
    validation_hash_field: str,
    producer_gold_field: str,
) -> tuple[Path, Path]:
    namespace = root / stage
    validation = root / f"{stage}_validation/VALIDATION.json"
    validate_manifest(namespace)
    require(validation.is_file(), "ANSWER_SOURCE_ACCEPTANCE_REQUIRED")
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    acceptance = json.loads(validation.read_text(encoding="utf-8"))
    require(receipt.get("status") == expected_status
            and receipt.get("completed_traces") == EXPECTED_TRACES
            and receipt.get("logical_operations") == expected_operations
            and receipt.get(producer_gold_field) == 0
            and receipt.get("scientific_fits") == 0,
            "ANSWER_SOURCE_RECEIPT")
    require(acceptance.get("status") == expected_acceptance
            and acceptance.get("producer_receipt_sha256")
            == sha256(namespace / "STAGE_RECEIPT.json")
            and acceptance.get(validation_hash_field)
            == sha256(namespace / row_file)
            and acceptance.get("gold_values_read") == 0
            and acceptance.get("scientific_fits") == 0,
            "ANSWER_SOURCE_ACCEPTANCE")
    return namespace, validation


def test_action_scope(rows: list[dict]) -> set[tuple[str, str]]:
    require(len(rows) == EXPECTED_TRACES, "TEST_ACTION_COUNT")
    identities = set()
    cells = collections.Counter()
    groups = collections.Counter()
    expected_fields = {
        "dataset", "retriever", "sample_id", "eligible", "scores", "actions",
        "forced_keep_reason",
    }
    for row in rows:
        require(type(row) is dict and set(row) == expected_fields,
                "TEST_ACTION_SCHEMA")
        identity = (row["dataset"], row["retriever"], row["sample_id"])
        require(identity not in identities, "UNIQUE_TEST_ACTION_IDENTITY")
        identities.add(identity)
        cells[(row["dataset"], row["retriever"])] += 1
        groups[(row["dataset"], row["sample_id"])] += 1
    datasets = ("hotpotqa", "2wikimultihopqa", "musique")
    retrievers = ("bm25", "dense", "hybrid")
    require(all(cells[(dataset, retriever)] == EXPECTED_DATASET_QUESTIONS
                for dataset in datasets for retriever in retrievers),
            "BALANCED_TEST_ACTION_CELLS")
    require(len(groups) == EXPECTED_QUESTIONS
            and all(value == 3 for value in groups.values()),
            "TEST_ACTION_SIBLINGS")
    return set(groups)


def test_references(root: Path, spec: dict, selected: set[tuple[str, str]],
                    cursor_type, readers, parquet) -> tuple[dict, dict]:
    references, counters = {}, {}
    for dataset in sorted(spec["sources"]):
        source = spec["sources"][dataset]
        wanted = {sample_id for name, sample_id in selected if name == dataset}
        require(len(wanted) == EXPECTED_DATASET_QUESTIONS,
                "TEST_DATASET_REFERENCE_SCOPE")
        path = checked(safe_file(root, relative_path(source["path"])),
                       source["sha256"], source["size_bytes"])
        if source["format"] == "parquet":
            values, receipt = readers.parquet_references(path, wanted, parquet)
        else:
            require(source["format"] in {"json", "jsonl"},
                    "REFERENCE_SERIALIZATION")
            values, receipt = readers.json_references(
                lambda: path.open("rb"), wanted, id_field=source["id_field"],
                json_lines=source["format"] == "jsonl",
                aliases=source["aliases"], Cursor=cursor_type,
            )
        require(receipt["source_rows"] == source["row_count"]
                and receipt["selected_question_labels"]
                == EXPECTED_DATASET_QUESTIONS
                and receipt["unselected_reference_python_values_materialized"] == 0
                and len(values) == EXPECTED_DATASET_QUESTIONS
                and set(values) == wanted, "TEST_REFERENCE_COVERAGE")
        checked(path, source["sha256"], source["size_bytes"])
        references.update({(dataset, sample_id): values[sample_id]
                           for sample_id in values})
        counters[dataset] = receipt
    require(set(references) == selected and len(references) == EXPECTED_QUESTIONS,
            "EXACT_TEST_REFERENCE_SET")
    return references, counters


def metric_values(metric, a0: str, a1: str, references: list[str]) -> dict:
    require(type(a0) is str and type(a1) is str
            and type(references) is list and references
            and all(type(value) is str for value in references),
            "OUTCOME_METRIC_INPUT")
    result = {
        "a0_em": int(metric.exact_match(a0, references)),
        "a1_em": int(metric.exact_match(a1, references)),
        "a0_f1": float(metric.token_f1(a0, references)),
        "a1_f1": float(metric.token_f1(a1, references)),
    }
    require(result["a0_em"] in (0, 1) and result["a1_em"] in (0, 1)
            and all(math.isfinite(result[name]) and 0.0 <= result[name] <= 1.0
                    for name in ("a0_f1", "a1_f1")),
            "OUTCOME_METRIC_RANGE")
    return result


def answer_maps(a0_path: Path, a1_path: Path) -> tuple[dict, dict]:
    a0_rows = list(read_jsonl(a0_path))
    a1_rows = list(read_jsonl(a1_path))
    require(len(a0_rows) == 2 * EXPECTED_TRACES
            and len(a1_rows) == 5 * EXPECTED_TRACES,
            "ANSWER_SOURCE_OPERATION_COUNTS")
    a0_map = {row["payload"]["position"]: row["payload"]
              for row in a0_rows if row["operation"] == "a0"}
    a1_map = {row["payload"]["position"]: row["payload"]
              for row in a1_rows if row["operation"] == "a1"}
    require(len(a0_map) == len(a1_map) == EXPECTED_TRACES,
            "ANSWER_SOURCE_COUNTS")
    return a0_map, a1_map


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


def failure_locations(exc: BaseException) -> list[dict]:
    rows = []
    current = exc.__traceback__
    while current is not None:
        rows.append({"file": current.tb_frame.f_code.co_filename,
                     "line": current.tb_lineno,
                     "function": current.tb_frame.f_code.co_name})
        current = current.tb_next
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    args = parser.parse_args()
    original, root = args.project_root.resolve(), args.test_root.resolve()
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve(),
            "FIXED_ROOTS")
    stage_output = root / "test_outcomes"
    require(not stage_output.exists(), "SINGLE_USE_TEST_OUTCOME_NAMESPACE")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    ).strip(), "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    started = time.perf_counter()
    result = {
        "status": "FAIL", "cas_q3_status": "NOT READY",
        "source_commit": commit, "stage": "test_outcomes",
        "gold_access_started": False, "test_gold_metric_values_read": 0,
        "gold_question_labels_materialized": 0,
        "gold_reference_strings_materialized": 0,
        "raw_reference_strings_written": 0, "scientific_fits": 0,
        "neural_model_loads": 0, "model_forwards": 0,
        "action_budget_tuned": False,
    }
    try:
        action, action_validation = validate_action_gate(root)
        a0, a0_validation = validate_answer_source(
            root, "a0_query", "GENERATION_RECEIPTS.jsonl",
            "PASS_MISTRAL_TEST_A0_QUERY_PENDING_INDEPENDENT",
            "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY",
            EXPECTED_A0_OPERATIONS, "generation_receipts_sha256",
            "project_gold_values_read",
        )
        a1, a1_validation = validate_answer_source(
            root, "a1_likelihood", "MODEL_RECEIPTS.jsonl",
            "PASS_MISTRAL_TEST_A1_LIKELIHOOD_PENDING_INDEPENDENT",
            "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_A1_LIKELIHOOD",
            EXPECTED_A1_OPERATIONS, "model_receipts_sha256", "gold_values_read",
        )
        stage_output.mkdir(parents=True, exist_ok=False)
        require(all(name not in sys.modules for name in
                    ("torch", "transformers", "sklearn")),
                "MODEL_RUNTIME_ALREADY_LOADED")

        spec, pre_gold, authenticated_paths, arrow_files = authenticate(original)
        require(sys.version == pre_gold["environment"]["python"],
                "OUTCOME_PYTHON_IDENTITY")
        import numpy as np
        require(np.__version__ == pre_gold["environment"]["numpy"],
                "OUTCOME_NUMPY_IDENTITY")
        metric, cursor_type, readers, definitions = native(original, spec)
        input_paths = [
            action / "SHA256_MANIFEST.json", action_validation,
            a0 / "SHA256_MANIFEST.json", a0_validation,
            a1 / "SHA256_MANIFEST.json", a1_validation,
            Path(__file__), REPO / "scripts/validate_mistral_test_outcomes.py",
            REPO / "scripts/empirical_outcome_native.py",
            REPO / "scripts/empirical_outcome_independent.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            *authenticated_paths,
        ]
        unique_paths = sorted({path.resolve() for path in input_paths}, key=str)
        input_records = [record(path) for path in unique_paths]
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_TEST_GOLD_ACCESS",
            "source_commit": commit, "stage": "test_outcomes",
            "expected_traces": EXPECTED_TRACES,
            "expected_questions": EXPECTED_QUESTIONS,
            "expected_questions_per_dataset": EXPECTED_DATASET_QUESTIONS,
            "expected_metric_values": EXPECTED_METRIC_VALUES,
            "metric_fields": list(METRIC_FIELDS),
            "output_fields": sorted(OUTCOME_FIELDS),
            "action_manifest_sha256": sha256(action / "SHA256_MANIFEST.json"),
            "action_receipt_sha256": sha256(action / "STAGE_RECEIPT.json"),
            "action_rows_sha256": sha256(action / "ACTION_ROWS.jsonl"),
            "answer_receipts": {
                "a0": sha256(a0 / "GENERATION_RECEIPTS.jsonl"),
                "a1": sha256(a1 / "MODEL_RECEIPTS.jsonl"),
            },
            "inputs": input_records, "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "python_version": sys.version, "numpy_version": np.__version__,
            "native_definition_hashes": definitions,
            "authenticated_arrow_package_files": arrow_files,
            "raw_reference_output": "FORBIDDEN",
            "parameter_tuning": "FORBIDDEN",
        }
        write_json_durable(stage_output / "EXECUTABLE_FREEZE.json", freeze)

        action_rows = list(read_jsonl(action / "ACTION_ROWS.jsonl"))
        selected = test_action_scope(action_rows)
        marker = {
            "status": "TEST_GOLD_ACCESS_STARTED_AFTER_ACCEPTED_ACTION_SEAL",
            "action_manifest_sha256": freeze["action_manifest_sha256"],
            "action_receipt_sha256": freeze["action_receipt_sha256"],
            "action_rows_sha256": freeze["action_rows_sha256"],
            "selected_question_count": EXPECTED_QUESTIONS,
            "selected_ids_sha256": sha256_bytes(canonical(sorted(selected))),
            "raw_references_may_not_be_written": True,
        }
        write_json_durable(stage_output / "GOLD_ACCESS_STARTED.json", marker)
        result.update(gold_access_started=True,
                      test_gold_metric_values_read=None,
                      gold_question_labels_materialized=None,
                      gold_reference_strings_materialized=None)

        package = original / "tmp/daa_v2_hotpot_full_column_reader"
        sys.path.insert(0, str(package))
        import pyarrow
        import pyarrow.parquet as pq
        require(Path(pyarrow.__file__).resolve() == package / "pyarrow/__init__.py"
                and pyarrow.__version__ == pre_gold["environment"]["pyarrow"]
                == "20.0.0", "OUTCOME_PYARROW_IDENTITY")
        references, source_receipts = test_references(
            original, spec, selected, cursor_type, readers, pq,
        )
        reference_strings = sum(len(values) for values in references.values())
        result.update(gold_question_labels_materialized=len(references),
                      gold_reference_strings_materialized=reference_strings)

        a0_map, a1_map = answer_maps(
            a0 / "GENERATION_RECEIPTS.jsonl", a1 / "MODEL_RECEIPTS.jsonl"
        )
        outcome_rows = []
        transitions = collections.Counter()
        for position, action_row in enumerate(action_rows):
            a0_payload, a1_payload = a0_map[position], a1_map[position]
            identity = {name: action_row[name]
                        for name in ("dataset", "retriever", "sample_id")}
            require(all(a0_payload[name] == value for name, value in identity.items())
                    and all(a1_payload[name] == value
                            for name, value in identity.items())
                    and a0_payload["position"] == a1_payload["position"] == position
                    and a0_payload["role"] == a1_payload["role"] == "test",
                    "ANSWER_ACTION_IDENTITY")
            values = metric_values(
                metric, a0_payload["parsed_text"], a1_payload["parsed_text"],
                references[(identity["dataset"], identity["sample_id"])],
            )
            row = {**identity, **values}
            require(set(row) == OUTCOME_FIELDS, "NUMERIC_ONLY_OUTCOME_SCHEMA")
            outcome_rows.append(row)
            transitions[f"{values['a0_em']}{values['a1_em']}"] += 1
        require(len(outcome_rows) == EXPECTED_TRACES, "OUTCOME_ROW_COUNT")
        outcome_path = stage_output / "TEST_OUTCOMES.jsonl"
        raw = b"".join(canonical(row) + b"\n" for row in outcome_rows)
        with outcome_path.open("xb") as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        for item in input_records:
            require(record(item["path"]) == item, "INPUT_CHANGED")
        require(all(name not in sys.modules for name in
                    ("torch", "transformers", "sklearn")),
                "MODEL_RUNTIME_LOADED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update({
            "status": "PASS_MISTRAL_TEST_OUTCOMES_PENDING_INDEPENDENT",
            "completed_traces": EXPECTED_TRACES,
            "test_questions": EXPECTED_QUESTIONS,
            "test_gold_metric_values_read": EXPECTED_METRIC_VALUES,
            "metric_values_emitted": EXPECTED_METRIC_VALUES,
            "em_transition_counts": dict(transitions),
            "source_reader_receipts": source_receipts,
            "unselected_reference_python_values_materialized": 0,
            "test_outcomes": record(outcome_path),
            "raw_reference_strings_written": 0,
            "scientific_fits": 0, "neural_model_loads": 0,
            "model_forwards": 0, "action_budget_tuned": False,
            "elapsed_seconds": elapsed,
        })
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        after_gold = result.get("gold_access_started") is True
        result.update({
            "status": "FAIL_MISTRAL_TEST_OUTCOMES",
            "error_type": type(exc).__name__,
            "diagnostic": ("DETAILS_WITHHELD_TO_PREVENT_TEST_REFERENCE_TEXT_LOGGING"
                           if after_gold else str(exc)),
            "code_locations": failure_locations(exc),
            "elapsed_seconds": time.perf_counter() - started,
        })
        if stage_output.is_dir() and not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result)
            seal(stage_output)
        print(result["status"], result["error_type"], flush=True)
        return 2


def sha256_bytes(value: bytes) -> str:
    import hashlib
    return hashlib.sha256(value).hexdigest()


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
