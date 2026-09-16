"""Independently reread development Gold and verify Mistral EM/F1 rows."""

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
from scripts.validate_mistral_development_a0_query import read_rows, require, sha256
from scripts.verify_roa_artifacts import relative_path, safe_file


REPO = Path(__file__).resolve().parents[1]
EXPECTED_TRACES = 13_500
EXPECTED_QUESTIONS = 4_500
EXPECTED_DATASET_QUESTIONS = 1_500
OUTCOME_FIELDS = frozenset({
    "dataset", "retriever", "sample_id", "position", "role",
    "prelabel_row_sha256", "a0_receipt_sha256", "a1_receipt_sha256",
    "a0_em", "a1_em", "a0_f1", "a1_f1",
})


def object_sha(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    require(manifest["status"] == "PASS" and manifest["exact_recursive_coverage"] is True,
            "MANIFEST_STATUS")
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members,
                "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_prelabel(root: Path) -> tuple[Path, Path]:
    namespace = root / "prelabel"
    validation = root / "prelabel_validation/VALIDATION.json"
    require(validation.is_file(), "PRELABEL_VALIDATION_REQUIRED")
    validate_manifest(namespace)
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_PRELABEL_FREEZE"
            and value["producer_manifest_sha256"]
            == sha256(namespace / "SHA256_MANIFEST.json")
            and value["producer_receipt_sha256"]
            == sha256(namespace / "STAGE_RECEIPT.json")
            and value["prelabel_rows_sha256"]
            == sha256(namespace / "PRELABEL_ROWS.jsonl")
            and value["gold_values_read"] == value["scientific_fits"]
            == value["test_rows_read"] == 0, "PRELABEL_ACCEPTANCE")
    return namespace, validation


def development_groups(prelabel_rows: list[dict]) -> tuple[set[tuple[str, str]], dict]:
    roles = {}; sibling_counts = collections.Counter()
    for row in prelabel_rows:
        group = (row["dataset"], row["sample_id"])
        if group in roles:
            require(roles[group] == row["role"], "SIBLING_ROLE")
        else:
            roles[group] = row["role"]
        sibling_counts[group] += 1
    require(len(roles) == EXPECTED_QUESTIONS
            and all(value == 3 for value in sibling_counts.values())
            and all(sum(dataset == name for dataset, _ in roles)
                    == EXPECTED_DATASET_QUESTIONS
                    for name in ("hotpotqa", "2wikimultihopqa", "musique")),
            "DEVELOPMENT_GROUP_SCOPE")
    counts = collections.Counter(roles.values())
    require(counts == {"fit": 3_600, "cal": 900}, "QUESTION_ROLE_COUNTS")
    return set(roles), dict(counts)


def selected_references(root: Path, spec: dict, selected: set[tuple[str, str]],
                        cursor_type, readers, parquet) -> tuple[dict, dict]:
    references, counters = {}, {}
    for dataset in sorted(spec["sources"]):
        source = spec["sources"][dataset]
        wanted = {sample_id for name, sample_id in selected if name == dataset}
        require(len(wanted) == EXPECTED_DATASET_QUESTIONS, "DATASET_REFERENCE_SCOPE")
        path = checked(safe_file(root, relative_path(source["path"])),
                       source["sha256"], source["size_bytes"])
        if source["format"] == "parquet":
            values, receipt = readers.parquet_references(path, wanted, parquet)
        else:
            require(source["format"] in {"json", "jsonl"}, "REFERENCE_FORMAT")
            values, receipt = readers.json_references(
                lambda: path.open("rb"), wanted, id_field=source["id_field"],
                json_lines=source["format"] == "jsonl", aliases=source["aliases"],
                Cursor=cursor_type,
            )
        require(receipt["source_rows"] == source["row_count"]
                and receipt["selected_question_labels"] == EXPECTED_DATASET_QUESTIONS
                and receipt["unselected_reference_python_values_materialized"] == 0
                and set(values) == wanted, "REFERENCE_COVERAGE")
        checked(path, source["sha256"], source["size_bytes"])
        references.update({(dataset, sample_id): values[sample_id]
                           for sample_id in values})
        counters[dataset] = receipt
    require(set(references) == selected and len(references) == EXPECTED_QUESTIONS,
            "EXACT_REFERENCE_SET")
    return references, counters


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
    prelabel, prelabel_validation = validate_prelabel(root)
    namespace = root / "development_outcomes"; validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"]
            == "PASS_MISTRAL_DEVELOPMENT_OUTCOMES_PENDING_INDEPENDENT"
            and receipt["completed_traces"] == EXPECTED_TRACES
            and receipt["development_questions"] == EXPECTED_QUESTIONS
            and receipt["raw_reference_strings_written"] == 0
            and receipt["test_rows_read"] == receipt["test_question_labels_materialized"]
            == receipt["scientific_fits"] == receipt["neural_model_loads"]
            == receipt["model_forwards"] == 0, "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"]
            and freeze["stage"] == "development_outcomes"
            and freeze["expected_traces"] == EXPECTED_TRACES
            and freeze["expected_questions"] == EXPECTED_QUESTIONS
            and freeze["test_access"] == "FORBIDDEN"
            and freeze["metric_fields"] == ["a0_em", "a1_em", "a0_f1", "a1_f1"],
            "EXECUTABLE_FREEZE")
    frozen_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(len(frozen_paths) == len(freeze["inputs"])
            and prelabel_validation.resolve() in frozen_paths,
            "FROZEN_PRELABEL_VALIDATION")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_INPUT")
    marker = json.loads((namespace / "GOLD_ACCESS_STARTED.json").read_text(encoding="utf-8"))
    require(marker["status"] == "DEVELOPMENT_GOLD_ACCESS_STARTED"
            and marker["prelabel_manifest_sha256"]
            == sha256(prelabel / "SHA256_MANIFEST.json")
            and marker["selected_question_count"] == EXPECTED_QUESTIONS
            and marker["test_access"] == "FORBIDDEN"
            and marker["raw_references_may_not_be_written"] is True,
            "GOLD_ACCESS_MARKER")

    spec, pre_gold, _paths, arrow_files = authenticate(original)
    require(sys.version == pre_gold["environment"]["python"], "PYTHON_IDENTITY")
    import numpy as np
    require(np.__version__ == pre_gold["environment"]["numpy"], "NUMPY_IDENTITY")
    _original_metric, cursor_type, readers, definitions = native(original, spec)
    require(freeze["native_definition_hashes"] == definitions
            and freeze["authenticated_arrow_package_files"] == arrow_files,
            "NATIVE_DEFINITION_BINDING")
    package = original / "tmp/daa_v2_hotpot_full_column_reader"
    sys.path.insert(0, str(package))
    import pyarrow
    import pyarrow.parquet as pq
    require(Path(pyarrow.__file__).resolve() == package / "pyarrow/__init__.py"
            and pyarrow.__version__ == pre_gold["environment"]["pyarrow"] == "20.0.0",
            "PYARROW_IDENTITY")

    prelabel_rows = read_rows(prelabel / "PRELABEL_ROWS.jsonl")
    selected, question_role_counts = development_groups(prelabel_rows)
    require(marker["selected_ids_sha256"] == object_sha(sorted(selected)),
            "SELECTED_ID_BINDING")
    references, source_receipts = selected_references(
        original, spec, selected, cursor_type, readers, pq,
    )
    reference_strings = sum(len(values) for values in references.values())
    a0_rows = read_rows(root / "a0_query/GENERATION_RECEIPTS.jsonl")
    a1_rows = read_rows(root / "a1_likelihood/MODEL_RECEIPTS.jsonl")
    a0_map = {row["payload"]["position"]: row["payload"]
              for row in a0_rows if row["operation"] == "a0"}
    a1_map = {row["payload"]["position"]: row["payload"]
              for row in a1_rows if row["operation"] == "a1"}
    outcomes = read_rows(namespace / "DEVELOPMENT_OUTCOMES.jsonl")
    require(len(prelabel_rows) == len(a0_map) == len(a1_map) == len(outcomes)
            == EXPECTED_TRACES, "SOURCE_COUNTS")
    role_traces = collections.Counter(); transitions = collections.Counter()
    maximum_f1_error = 0.0; checks = 0
    for position, (prelabel_row, outcome) in enumerate(zip(
            prelabel_rows, outcomes, strict=True)):
        require(set(outcome) == OUTCOME_FIELDS, "OUTCOME_SCHEMA")
        a0_payload, a1_payload = a0_map[position], a1_map[position]
        identity = {name: prelabel_row[name]
                    for name in ("dataset", "retriever", "sample_id", "position", "role")}
        require(all(outcome[name] == value for name, value in identity.items())
                and all(a0_payload[name] == value for name, value in identity.items())
                and all(a1_payload[name] == value for name, value in identity.items()),
                "OUTCOME_IDENTITY")
        expected0 = metrics(
            a0_payload["parsed_text"],
            references[(identity["dataset"], identity["sample_id"])],
        )
        expected1 = metrics(
            a1_payload["parsed_text"],
            references[(identity["dataset"], identity["sample_id"])],
        )
        require(type(outcome["a0_em"]) is int and type(outcome["a1_em"]) is int
                and outcome["a0_em"] == expected0[0]
                and outcome["a1_em"] == expected1[0], "INDEPENDENT_EM")
        errors = (abs(outcome["a0_f1"] - expected0[1]),
                  abs(outcome["a1_f1"] - expected1[1]))
        maximum_f1_error = max(maximum_f1_error, *errors)
        require(all(type(outcome[name]) in (int, float)
                    and math.isfinite(outcome[name]) and 0.0 <= outcome[name] <= 1.0
                    for name in ("a0_f1", "a1_f1"))
                and max(errors) <= 1e-15, "INDEPENDENT_F1")
        require(outcome["prelabel_row_sha256"] == object_sha(prelabel_row)
                and outcome["a0_receipt_sha256"] == object_sha(a0_payload)
                and outcome["a1_receipt_sha256"] == object_sha(a1_payload),
                "OUTCOME_SOURCE_BINDINGS")
        role_traces[outcome["role"]] += 1
        transitions[f"{outcome['a0_em']}{outcome['a1_em']}"] += 1
        checks += 34
    require(question_role_counts == receipt["question_role_counts"]
            and question_role_counts == {"fit": 3_600, "cal": 900}
            and role_traces == receipt["trace_role_counts"]
            and role_traces == {"fit": 10_800, "cal": 2_700}
            and dict(transitions) == receipt["em_transition_counts"]
            and receipt["source_reader_receipts"] == source_receipts
            and receipt["gold_values_read"] == reference_strings
            and receipt["gold_reference_strings_materialized"] == reference_strings
            and receipt["gold_question_labels_materialized"] == EXPECTED_QUESTIONS
            and receipt["metric_values_emitted"] == EXPECTED_TRACES * 4
            and receipt["unselected_reference_python_values_materialized"] == 0,
            "RECEIPT_RECONCILIATION")
    outcome_path = namespace / "DEVELOPMENT_OUTCOMES.jsonl"
    expected_record = {"path": str(outcome_path.resolve()),
                       "size_bytes": outcome_path.stat().st_size,
                       "sha256": sha256(outcome_path)}
    require(receipt["development_outcomes"] == expected_record,
            "OUTCOME_FILE_BINDING")
    require(all(name not in sys.modules for name in ("torch", "transformers", "sklearn")),
            "MODEL_RUNTIME_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_OUTCOMES",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_manifest_sha256": sha256(namespace / "SHA256_MANIFEST.json"),
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "development_outcomes_sha256": sha256(outcome_path),
        "traces_validated": EXPECTED_TRACES,
        "development_questions": EXPECTED_QUESTIONS,
        "gold_question_labels_materialized": EXPECTED_QUESTIONS,
        "gold_reference_strings_materialized": reference_strings,
        "gold_values_read": reference_strings,
        "metric_values_checked": EXPECTED_TRACES * 4,
        "maximum_f1_error": maximum_f1_error,
        "source_reader_receipts": source_receipts,
        "unselected_reference_python_values_materialized": 0,
        "raw_reference_strings_written": 0,
        "test_rows_read": 0, "test_question_labels_materialized": 0,
        "scientific_fits": 0, "neural_model_loads": 0, "model_forwards": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
