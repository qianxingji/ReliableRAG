"""Independently reread test Gold and verify numeric-only Mistral outcomes."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_outcome_independent import metrics
from scripts.empirical_outcome_native import authenticate, native
from scripts.empirical_pool_io import checked
from scripts.mistral_development_acquisition_common import read_jsonl, sha256
from scripts.verify_roa_artifacts import relative_path, safe_file


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_QUESTIONS = 6_000
EXPECTED_DATASET_QUESTIONS = 2_000
EXPECTED_METRIC_VALUES = 72_000
OUTCOME_FIELDS = frozenset({
    "dataset", "retriever", "sample_id",
    "a0_em", "a1_em", "a0_f1", "a1_f1",
})


def require(value, message):
    if not value:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def object_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_manifest(namespace: Path) -> set[Path]:
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
    paths = members | {manifest_path.resolve()}
    require(actual == paths, "MANIFEST_COVERAGE")
    return paths


def validate_predecessors(root: Path):
    action = root / "action_seal"
    action_validation = root / "action_seal_validation/VALIDATION.json"
    a0 = root / "a0_query"
    a0_validation = root / "a0_query_validation/VALIDATION.json"
    a1 = root / "a1_likelihood"
    a1_validation = root / "a1_likelihood_validation/VALIDATION.json"
    action_paths = validate_manifest(action)
    a0_paths = validate_manifest(a0)
    a1_paths = validate_manifest(a1)
    require(all(path.is_file() for path in
                (action_validation, a0_validation, a1_validation)),
            "PREDECESSOR_VALIDATIONS")
    action_receipt = json.loads((action / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    action_acceptance = json.loads(action_validation.read_text(encoding="utf-8"))
    require(action_receipt.get("status")
            == "PASS_MISTRAL_TEST_ACTION_SEAL_PENDING_INDEPENDENT"
            and action_receipt.get("N_all") == EXPECTED_TRACES
            and action_receipt.get("test_gold_values_read") == 0
            and action_receipt.get("test_outcome_values_read") == 0
            and action_receipt.get("action_budget_tuned") is False,
            "ACTION_RECEIPT")
    require(action_acceptance.get("status")
            == "PASS_INDEPENDENT_MISTRAL_TEST_ACTION_SEAL"
            and action_acceptance.get("producer_manifest_sha256")
            == sha256(action / "SHA256_MANIFEST.json")
            and action_acceptance.get("producer_receipt_sha256")
            == sha256(action / "STAGE_RECEIPT.json")
            and action_acceptance.get("action_rows_sha256")
            == sha256(action / "ACTION_ROWS.jsonl")
            and action_acceptance.get("validated_rows") == EXPECTED_TRACES
            and action_acceptance.get("test_gold_values_read") == 0
            and action_acceptance.get("test_outcome_values_read") == 0,
            "ACTION_ACCEPTANCE")
    source_contracts = (
        (a0, a0_validation,
         "PASS_MISTRAL_TEST_A0_QUERY_PENDING_INDEPENDENT",
         "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY",
         36_000, "GENERATION_RECEIPTS.jsonl", "generation_receipts_sha256",
         "project_gold_values_read"),
        (a1, a1_validation,
         "PASS_MISTRAL_TEST_A1_LIKELIHOOD_PENDING_INDEPENDENT",
         "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_A1_LIKELIHOOD",
         90_000, "MODEL_RECEIPTS.jsonl", "model_receipts_sha256",
         "gold_values_read"),
    )
    for (namespace, validation, producer_status, validator_status, operations,
         row_file, hash_field, producer_gold_field) in source_contracts:
        receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
            encoding="utf-8"
        ))
        acceptance = json.loads(validation.read_text(encoding="utf-8"))
        require(receipt.get("status") == producer_status
                and receipt.get("completed_traces") == EXPECTED_TRACES
                and receipt.get("logical_operations") == operations
                and receipt.get(producer_gold_field) == 0
                and receipt.get("scientific_fits") == 0,
                "ANSWER_SOURCE_RECEIPT")
        require(acceptance.get("status") == validator_status
                and acceptance.get("producer_receipt_sha256")
                == sha256(namespace / "STAGE_RECEIPT.json")
                and acceptance.get(hash_field) == sha256(namespace / row_file)
                and acceptance.get("gold_values_read") == 0
                and acceptance.get("scientific_fits") == 0,
                "ANSWER_SOURCE_ACCEPTANCE")
    return (action, action_validation, a0, a0_validation, a1, a1_validation,
            action_paths, a0_paths, a1_paths)


def action_groups(rows: list[dict]) -> set[tuple[str, str]]:
    require(len(rows) == EXPECTED_TRACES, "TEST_ACTION_COUNT")
    identities = set()
    cells = collections.Counter()
    groups = collections.Counter()
    schema = {"dataset", "retriever", "sample_id", "eligible", "scores",
              "actions", "forced_keep_reason"}
    for row in rows:
        require(type(row) is dict and set(row) == schema, "TEST_ACTION_SCHEMA")
        identity = (row["dataset"], row["retriever"], row["sample_id"])
        require(identity not in identities, "UNIQUE_TEST_ACTION_IDENTITY")
        identities.add(identity)
        cells[(identity[0], identity[1])] += 1
        groups[(identity[0], identity[2])] += 1
    datasets = ("hotpotqa", "2wikimultihopqa", "musique")
    retrievers = ("bm25", "dense", "hybrid")
    require(all(cells[(dataset, retriever)] == EXPECTED_DATASET_QUESTIONS
                for dataset in datasets for retriever in retrievers),
            "BALANCED_TEST_ACTION_CELLS")
    require(len(groups) == EXPECTED_QUESTIONS
            and all(value == 3 for value in groups.values()),
            "TEST_ACTION_SIBLINGS")
    return set(groups)


def selected_references(root: Path, spec: dict, selected: set[tuple[str, str]],
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
            require(source["format"] in {"json", "jsonl"}, "REFERENCE_FORMAT")
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
                and set(values) == wanted, "REFERENCE_COVERAGE")
        checked(path, source["sha256"], source["size_bytes"])
        references.update({(dataset, sample_id): values[sample_id]
                           for sample_id in values})
        counters[dataset] = receipt
    require(set(references) == selected and len(references) == EXPECTED_QUESTIONS,
            "EXACT_REFERENCE_SET")
    return references, counters


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original, root = args.project_root.resolve(), args.test_root.resolve()
    output = (args.output.resolve() if args.output else
              (root / "test_outcomes_validation/VALIDATION.json").resolve())
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve()
            and output
            == (root / "test_outcomes_validation/VALIDATION.json").resolve()
            and not output.exists(), "FIXED_ROOTS_OR_OUTPUT")
    (action, action_validation, a0, a0_validation, a1, a1_validation,
     action_paths, a0_paths, a1_paths) = validate_predecessors(root)
    namespace = root / "test_outcomes"
    validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    require(receipt.get("status")
            == "PASS_MISTRAL_TEST_OUTCOMES_PENDING_INDEPENDENT"
            and receipt.get("completed_traces") == EXPECTED_TRACES
            and receipt.get("test_questions") == EXPECTED_QUESTIONS
            and receipt.get("test_gold_metric_values_read")
            == EXPECTED_METRIC_VALUES
            and receipt.get("metric_values_emitted") == EXPECTED_METRIC_VALUES
            and receipt.get("raw_reference_strings_written") == 0
            and receipt.get("scientific_fits") == 0
            and receipt.get("neural_model_loads") == 0
            and receipt.get("model_forwards") == 0
            and receipt.get("action_budget_tuned") is False,
            "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(
        encoding="utf-8"
    ))
    require(freeze.get("source_commit") == receipt.get("source_commit")
            and freeze.get("status")
            == "FROZEN_BEFORE_MISTRAL_TEST_GOLD_ACCESS"
            and freeze.get("expected_traces") == EXPECTED_TRACES
            and freeze.get("expected_questions") == EXPECTED_QUESTIONS
            and freeze.get("expected_metric_values") == EXPECTED_METRIC_VALUES
            and freeze.get("metric_fields")
            == ["a0_em", "a1_em", "a0_f1", "a1_f1"]
            and set(freeze.get("output_fields", [])) == OUTCOME_FIELDS
            and freeze.get("python") == str(Path(sys.executable).resolve())
            and freeze.get("python_version") == sys.version
            and freeze.get("raw_reference_output") == "FORBIDDEN"
            and freeze.get("parameter_tuning") == "FORBIDDEN",
            "EXECUTABLE_FREEZE")
    expected_bindings = {
        "action_manifest_sha256": sha256(action / "SHA256_MANIFEST.json"),
        "action_receipt_sha256": sha256(action / "STAGE_RECEIPT.json"),
        "action_rows_sha256": sha256(action / "ACTION_ROWS.jsonl"),
    }
    require(all(freeze.get(name) == value
                for name, value in expected_bindings.items())
            and freeze.get("answer_receipts") == {
                "a0": sha256(a0 / "GENERATION_RECEIPTS.jsonl"),
                "a1": sha256(a1 / "MODEL_RECEIPTS.jsonl"),
            }, "FROZEN_SOURCE_BINDINGS")
    frozen_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(len(frozen_paths) == len(freeze["inputs"]), "UNIQUE_FROZEN_INPUTS")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_INPUT")

    spec, pre_gold, authenticated_paths, arrow_files = authenticate(original)
    require(sys.version == pre_gold["environment"]["python"]
            and freeze.get("numpy_version") == pre_gold["environment"]["numpy"],
            "FROZEN_PYTHON_NUMPY_IDENTITY")
    required_inputs = {
        *action_paths, action_validation.resolve(),
        *a0_paths, a0_validation.resolve(),
        *a1_paths, a1_validation.resolve(),
        (REPO / "scripts/run_mistral_test_outcomes.py").resolve(),
        Path(__file__).resolve(),
        (REPO / "scripts/empirical_outcome_native.py").resolve(),
        (REPO / "scripts/empirical_outcome_independent.py").resolve(),
        (REPO / "scripts/empirical_pool_io.py").resolve(),
        (REPO / "scripts/mistral_development_acquisition_common.py").resolve(),
        (REPO / "scripts/verify_roa_artifacts.py").resolve(),
        (REPO / "src/arbitration/mistral_reader_runtime.py").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_OUTCOMES_INPUT_GRAPH_AMENDMENT_2026-09-17.md").resolve(),
        Path(sys.executable).resolve(),
        *{Path(path).resolve() for path in authenticated_paths},
    }
    require(required_inputs == frozen_paths, "NONEXACT_FROZEN_INPUT_GRAPH")

    action_rows = list(read_jsonl(action / "ACTION_ROWS.jsonl"))
    selected = action_groups(action_rows)
    marker = json.loads((namespace / "GOLD_ACCESS_STARTED.json").read_text(
        encoding="utf-8"
    ))
    require(marker.get("status")
            == "TEST_GOLD_ACCESS_STARTED_AFTER_ACCEPTED_ACTION_SEAL"
            and all(marker.get(name) == value
                    for name, value in expected_bindings.items())
            and marker.get("selected_question_count") == EXPECTED_QUESTIONS
            and marker.get("selected_ids_sha256") == object_sha(sorted(selected))
            and marker.get("raw_references_may_not_be_written") is True,
            "GOLD_ACCESS_MARKER")

    require(sys.version == pre_gold["environment"]["python"], "PYTHON_IDENTITY")
    import numpy as np
    require(np.__version__ == pre_gold["environment"]["numpy"], "NUMPY_IDENTITY")
    _metric, cursor_type, readers, definitions = native(original, spec)
    require(freeze.get("native_definition_hashes") == definitions
            and freeze.get("authenticated_arrow_package_files") == arrow_files,
            "NATIVE_DEFINITION_BINDING")
    package = original / "tmp/daa_v2_hotpot_full_column_reader"
    sys.path.insert(0, str(package))
    import pyarrow
    import pyarrow.parquet as pq
    require(Path(pyarrow.__file__).resolve() == package / "pyarrow/__init__.py"
            and pyarrow.__version__ == pre_gold["environment"]["pyarrow"]
            == "20.0.0", "PYARROW_IDENTITY")
    references, source_receipts = selected_references(
        original, spec, selected, cursor_type, readers, pq,
    )
    reference_strings = sum(len(values) for values in references.values())
    a0_map, a1_map = answer_maps(
        a0 / "GENERATION_RECEIPTS.jsonl", a1 / "MODEL_RECEIPTS.jsonl"
    )
    outcomes = list(read_jsonl(namespace / "TEST_OUTCOMES.jsonl"))
    require(len(outcomes) == EXPECTED_TRACES, "OUTCOME_ROW_COUNT")
    transitions = collections.Counter()
    maximum_f1_error = 0.0
    checks = 0
    for position, (action_row, outcome) in enumerate(zip(
            action_rows, outcomes, strict=True)):
        require(type(outcome) is dict and set(outcome) == OUTCOME_FIELDS,
                "NUMERIC_ONLY_OUTCOME_SCHEMA")
        a0_payload, a1_payload = a0_map[position], a1_map[position]
        identity = {name: action_row[name]
                    for name in ("dataset", "retriever", "sample_id")}
        require(all(outcome[name] == value for name, value in identity.items())
                and all(a0_payload[name] == value
                        for name, value in identity.items())
                and all(a1_payload[name] == value
                        for name, value in identity.items())
                and a0_payload["position"] == a1_payload["position"] == position
                and a0_payload["role"] == a1_payload["role"] == "test",
                "OUTCOME_SOURCE_IDENTITY")
        refs = references[(identity["dataset"], identity["sample_id"])]
        expected0 = metrics(a0_payload["parsed_text"], refs)
        expected1 = metrics(a1_payload["parsed_text"], refs)
        require(type(outcome["a0_em"]) is int
                and type(outcome["a1_em"]) is int
                and outcome["a0_em"] == expected0[0]
                and outcome["a1_em"] == expected1[0], "INDEPENDENT_EM")
        errors = (abs(outcome["a0_f1"] - expected0[1]),
                  abs(outcome["a1_f1"] - expected1[1]))
        maximum_f1_error = max(maximum_f1_error, *errors)
        require(all(type(outcome[name]) in (int, float)
                    and math.isfinite(outcome[name])
                    and 0.0 <= outcome[name] <= 1.0
                    for name in ("a0_f1", "a1_f1"))
                and max(errors) <= 1e-15, "INDEPENDENT_F1")
        transitions[f"{outcome['a0_em']}{outcome['a1_em']}"] += 1
        checks += 25
    outcome_path = namespace / "TEST_OUTCOMES.jsonl"
    require(receipt.get("test_outcomes") == {
        "path": str(outcome_path.resolve()),
        "size_bytes": outcome_path.stat().st_size,
        "sha256": sha256(outcome_path),
    } and receipt.get("source_reader_receipts") == source_receipts
        and receipt.get("gold_question_labels_materialized") == EXPECTED_QUESTIONS
        and receipt.get("gold_reference_strings_materialized") == reference_strings
        and receipt.get("unselected_reference_python_values_materialized") == 0
        and receipt.get("em_transition_counts") == dict(transitions),
        "RECEIPT_RECONCILIATION")
    require(all(name not in sys.modules for name in
                ("torch", "transformers", "sklearn")),
            "MODEL_RUNTIME_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_MISTRAL_TEST_OUTCOMES",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_manifest_sha256": sha256(namespace / "SHA256_MANIFEST.json"),
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "test_outcomes_sha256": sha256(outcome_path),
        "validated_traces": EXPECTED_TRACES,
        "test_questions": EXPECTED_QUESTIONS,
        "test_gold_metric_values_read": EXPECTED_METRIC_VALUES,
        "metric_values_checked": EXPECTED_METRIC_VALUES,
        "maximum_f1_error": maximum_f1_error,
        "gold_question_labels_materialized": EXPECTED_QUESTIONS,
        "gold_reference_strings_materialized": reference_strings,
        "source_reader_receipts": source_receipts,
        "unselected_reference_python_values_materialized": 0,
        "raw_reference_strings_written": 0,
        "scientific_fits": 0, "neural_model_loads": 0,
        "model_forwards": 0, "action_budget_tuned": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2,
                                  allow_nan=False).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
