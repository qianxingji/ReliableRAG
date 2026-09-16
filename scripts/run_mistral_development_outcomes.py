"""Map authenticated development Gold to accepted Mistral answer pairs."""

from __future__ import annotations

import argparse
import collections
import json
import math
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
    read_jsonl, record, sha256, verify_manifest, write_json_durable,
)
from scripts.mistral_development_scoring_common import write_bytes_once
from scripts.run_mistral_development_a0_query import (
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256, EXPECTED_INPUT_LEDGER_SHA256,
)
from scripts.verify_roa_artifacts import relative_path, safe_file
from src.arbitration.mistral_reader_runtime import canonical, object_sha256, require


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q3"
EXPECTED_TRACES = 13_500
EXPECTED_QUESTIONS = 4_500
EXPECTED_DATASET_QUESTIONS = 1_500
METRIC_FIELDS = ("a0_em", "a1_em", "a0_f1", "a1_f1")
MAX_STAGE_SECONDS = 2 * 60 * 60


def validate_prelabel_gate(root: Path) -> tuple[Path, Path]:
    namespace = root / "prelabel"
    validation = root / "prelabel_validation/VALIDATION.json"
    require((namespace / "SHA256_MANIFEST.json").is_file() and validation.is_file(),
            "PRELABEL_ACCEPTANCE_REQUIRED")
    manifest_sha = sha256(namespace / "SHA256_MANIFEST.json")
    verify_manifest(namespace, manifest_sha)
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_PRELABEL_FREEZE"
            and value["producer_manifest_sha256"] == manifest_sha
            and value["producer_receipt_sha256"]
            == sha256(namespace / "STAGE_RECEIPT.json")
            and value["prelabel_rows_sha256"]
            == sha256(namespace / "PRELABEL_ROWS.jsonl")
            and value["gold_values_read"] == value["scientific_fits"]
            == value["test_rows_read"] == 0,
            "PRELABEL_VALIDATION_BINDING")
    return namespace, validation


def development_group_roles(prelabel_rows: list[dict]) -> tuple[set[tuple[str, str]], dict]:
    roles: dict[tuple[str, str], str] = {}
    trace_counts = collections.Counter()
    for row in prelabel_rows:
        group = (row["dataset"], row["sample_id"])
        if group in roles:
            require(roles[group] == row["role"], "DEVELOPMENT_SIBLING_ROLE")
        else:
            roles[group] = row["role"]
        trace_counts[(row["dataset"], row["sample_id"])] += 1
    require(len(roles) == EXPECTED_QUESTIONS
            and all(value == 3 for value in trace_counts.values())
            and all(sum(dataset == name for dataset, _ in roles)
                    == EXPECTED_DATASET_QUESTIONS
                    for name in ("hotpotqa", "2wikimultihopqa", "musique")),
            "DEVELOPMENT_GROUP_SCOPE")
    question_roles = collections.Counter(roles.values())
    require(question_roles == {"fit": 3_600, "cal": 900},
            "DEVELOPMENT_QUESTION_ROLES")
    return set(roles), dict(question_roles)


def development_references(
    root: Path,
    spec: dict,
    selected: set[tuple[str, str]],
    cursor_type,
    readers,
    parquet,
) -> tuple[dict, dict]:
    references, counters = {}, {}
    for dataset in sorted(spec["sources"]):
        source = spec["sources"][dataset]
        wanted = {sample_id for name, sample_id in selected if name == dataset}
        require(len(wanted) == EXPECTED_DATASET_QUESTIONS,
                "DEVELOPMENT_DATASET_REFERENCE_SCOPE")
        path = checked(
            safe_file(root, relative_path(source["path"])),
            source["sha256"], source["size_bytes"],
        )
        if source["format"] == "parquet":
            values, receipt = readers.parquet_references(path, wanted, parquet)
        else:
            require(source["format"] in {"json", "jsonl"},
                    "REFERENCE_SERIALIZATION")
            values, receipt = readers.json_references(
                lambda: path.open("rb"), wanted,
                id_field=source["id_field"],
                json_lines=source["format"] == "jsonl",
                aliases=source["aliases"], Cursor=cursor_type,
            )
        require(receipt["source_rows"] == source["row_count"]
                and receipt["selected_question_labels"] == EXPECTED_DATASET_QUESTIONS
                and receipt["unselected_reference_python_values_materialized"] == 0
                and len(values) == EXPECTED_DATASET_QUESTIONS
                and set(values) == wanted, "DEVELOPMENT_REFERENCE_COVERAGE")
        checked(path, source["sha256"], source["size_bytes"])
        references.update({(dataset, sample_id): values[sample_id]
                           for sample_id in values})
        counters[dataset] = receipt
    require(set(references) == selected and len(references) == EXPECTED_QUESTIONS,
            "EXACT_DEVELOPMENT_REFERENCE_SET")
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


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path); item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files, "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def failure_locations(exc: BaseException) -> list[dict]:
    rows = []; current = exc.__traceback__
    while current is not None:
        rows.append({
            "file": current.tb_frame.f_code.co_filename,
            "line": current.tb_lineno,
            "function": current.tb_frame.f_code.co_name,
        })
        current = current.tb_next
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    require(args.output_name and all(part not in args.output_name
                                     for part in ("/", "\\", "..")),
            "SAFE_OUTPUT_NAME")
    original = args.project_root.resolve(); root = (OUTPUT_PARENT / args.output_name).resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve()
            and root.parent == OUTPUT_PARENT.resolve(), "FIXED_ROOTS")
    prelabel, prelabel_validation = validate_prelabel_gate(root)
    stage_output = root / "development_outcomes"
    require(not any((stage_output / name).exists() for name in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json", "SHA256_MANIFEST.json")),
            "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(["git", "status", "--porcelain"],
                                        cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     cwd=REPO, text=True).strip()
    started = time.perf_counter()
    result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "development_outcomes", "gold_access_started": False,
        "gold_values_read": 0, "gold_question_labels_materialized": 0,
        "gold_reference_strings_materialized": 0,
        "raw_reference_strings_written": 0, "test_rows_read": 0,
        "test_question_labels_materialized": 0, "scientific_fits": 0,
        "neural_model_loads": 0, "model_forwards": 0,
    }
    try:
        if not args.resume: stage_output.mkdir(parents=True, exist_ok=False)
        require(all(name not in sys.modules for name in
                    ("torch", "transformers", "sklearn")), "MODEL_RUNTIME_ALREADY_LOADED")
        spec, pre_gold, authenticated_paths, arrow_files = authenticate(original)
        require(sys.version == pre_gold["environment"]["python"],
                "OUTCOME_PYTHON_IDENTITY")
        import numpy as np
        require(np.__version__ == pre_gold["environment"]["numpy"],
                "OUTCOME_NUMPY_IDENTITY")
        metric, cursor_type, readers, definitions = native(original, spec)
        a0_namespace = root / "a0_query"; a1_namespace = root / "a1_likelihood"
        verify_manifest(a0_namespace, sha256(a0_namespace / "SHA256_MANIFEST.json"))
        verify_manifest(a1_namespace, sha256(a1_namespace / "SHA256_MANIFEST.json"))
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
                and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256,
                "INPUT_FREEZE")
        input_paths = [
            prelabel / "SHA256_MANIFEST.json", prelabel_validation,
            a0_namespace / "SHA256_MANIFEST.json",
            a1_namespace / "SHA256_MANIFEST.json",
            input_manifest, frozen_ledger,
            Path(__file__), REPO / "scripts/empirical_outcome_native.py",
            REPO / "scripts/empirical_outcome_independent.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/mistral_development_scoring_common.py",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_SCORING_AND_TUNING_PROTOCOL_2026-09-17.md",
            *authenticated_paths,
        ]
        unique_paths = sorted({path.resolve() for path in input_paths}, key=str)
        input_records = [record(path) for path in unique_paths]
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_DEVELOPMENT_GOLD_ACCESS",
            "source_commit": commit, "stage": "development_outcomes",
            "expected_traces": EXPECTED_TRACES,
            "expected_questions": EXPECTED_QUESTIONS,
            "expected_questions_per_dataset": EXPECTED_DATASET_QUESTIONS,
            "metric_fields": list(METRIC_FIELDS),
            "test_access": "FORBIDDEN",
            "inputs": input_records, "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "python_version": sys.version, "numpy_version": np.__version__,
            "native_definition_hashes": definitions,
            "authenticated_arrow_package_files": arrow_files,
            "scope": "development selected references and numeric EM/F1 only; test/model/fit forbidden",
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                    "RESUME_FREEZE_MISMATCH")
        else:
            write_json_durable(freeze_path, freeze)

        prelabel_rows = list(read_jsonl(prelabel / "PRELABEL_ROWS.jsonl"))
        require(len(prelabel_rows) == EXPECTED_TRACES
                and [row["position"] for row in prelabel_rows]
                == list(range(EXPECTED_TRACES)), "PRELABEL_ROW_ORDER")
        selected, question_role_counts = development_group_roles(prelabel_rows)
        marker = {
            "status": "DEVELOPMENT_GOLD_ACCESS_STARTED",
            "prelabel_manifest_sha256": sha256(prelabel / "SHA256_MANIFEST.json"),
            "selected_question_count": EXPECTED_QUESTIONS,
            "selected_ids_sha256": object_sha256(sorted(selected)),
            "test_access": "FORBIDDEN",
            "raw_references_may_not_be_written": True,
        }
        marker_path = stage_output / "GOLD_ACCESS_STARTED.json"
        if args.resume:
            if marker_path.exists():
                require(json.loads(marker_path.read_text(encoding="utf-8")) == marker,
                        "RESUME_GOLD_MARKER_MISMATCH")
            else:
                write_json_durable(marker_path, marker)
        else:
            write_json_durable(marker_path, marker)
        result.update(gold_access_started=True, gold_values_read=None,
                      gold_question_labels_materialized=None,
                      gold_reference_strings_materialized=None)

        package = original / "tmp/daa_v2_hotpot_full_column_reader"
        sys.path.insert(0, str(package))
        import pyarrow
        import pyarrow.parquet as pq
        require(Path(pyarrow.__file__).resolve() == package / "pyarrow/__init__.py"
                and pyarrow.__version__ == pre_gold["environment"]["pyarrow"] == "20.0.0",
                "OUTCOME_PYARROW_IDENTITY")
        references, source_receipts = development_references(
            original, spec, selected, cursor_type, readers, pq,
        )
        reference_strings = sum(len(values) for values in references.values())
        result.update(gold_values_read=reference_strings,
                      gold_question_labels_materialized=len(references),
                      gold_reference_strings_materialized=reference_strings)

        a0_rows = list(read_jsonl(a0_namespace / "GENERATION_RECEIPTS.jsonl"))
        a1_rows = list(read_jsonl(a1_namespace / "MODEL_RECEIPTS.jsonl"))
        a0_map = {row["payload"]["position"]: row["payload"]
                  for row in a0_rows if row["operation"] == "a0"}
        a1_map = {row["payload"]["position"]: row["payload"]
                  for row in a1_rows if row["operation"] == "a1"}
        require(len(a0_map) == len(a1_map) == EXPECTED_TRACES,
                "ANSWER_SOURCE_COUNTS")
        outcome_rows = []; role_trace_counts = collections.Counter()
        transitions = collections.Counter()
        for position, prelabel_row in enumerate(prelabel_rows):
            a0_payload, a1_payload = a0_map[position], a1_map[position]
            identity = {name: prelabel_row[name]
                        for name in ("dataset", "retriever", "sample_id", "position", "role")}
            require(all(a0_payload[name] == identity[name]
                        for name in ("dataset", "retriever", "sample_id", "position", "role"))
                    and all(a1_payload[name] == identity[name]
                            for name in ("dataset", "retriever", "sample_id", "position", "role")),
                    "ANSWER_PRELABEL_IDENTITY")
            values = metric_values(
                metric, a0_payload["parsed_text"], a1_payload["parsed_text"],
                references[(identity["dataset"], identity["sample_id"])],
            )
            row = {
                **identity,
                "prelabel_row_sha256": object_sha256(prelabel_row),
                "a0_receipt_sha256": object_sha256(a0_payload),
                "a1_receipt_sha256": object_sha256(a1_payload),
                **values,
            }
            outcome_rows.append(row); role_trace_counts[row["role"]] += 1
            transitions[f"{values['a0_em']}{values['a1_em']}"] += 1
        require(role_trace_counts == {"fit": 10_800, "cal": 2_700},
                "OUTCOME_ROLE_TRACE_COUNTS")
        raw = b"".join(canonical(row) + b"\n" for row in outcome_rows)
        write_bytes_once(stage_output / "DEVELOPMENT_OUTCOMES.jsonl", raw)
        for item in input_records:
            require(record(item["path"]) == item, "INPUT_CHANGED")
        require(all(name not in sys.modules for name in
                    ("torch", "transformers", "sklearn")),
                "MODEL_RUNTIME_LOADED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_DEVELOPMENT_OUTCOMES_PENDING_INDEPENDENT",
            completed_traces=EXPECTED_TRACES,
            development_questions=EXPECTED_QUESTIONS,
            question_role_counts=question_role_counts,
            trace_role_counts=dict(role_trace_counts),
            em_transition_counts=dict(transitions),
            metric_values_emitted=EXPECTED_TRACES * len(METRIC_FIELDS),
            source_reader_receipts=source_receipts,
            unselected_reference_python_values_materialized=0,
            development_outcomes=record(stage_output / "DEVELOPMENT_OUTCOMES.jsonl"),
            raw_reference_strings_written=0,
            test_rows_read=0, test_question_labels_materialized=0,
            scientific_fits=0, neural_model_loads=0, model_forwards=0,
            elapsed_seconds=elapsed,
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output); print(result["status"], flush=True); return 0
    except Exception as exc:
        result.update(
            status="FAIL_MISTRAL_DEVELOPMENT_OUTCOMES",
            error_type=type(exc).__name__,
            diagnostic="DETAILS_WITHHELD_TO_PREVENT_REFERENCE_TEXT_LOGGING",
            code_locations=failure_locations(exc),
            elapsed_seconds=time.perf_counter() - started,
        )
        if stage_output.is_dir() and not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result); seal(stage_output)
        print(result["status"], result["error_type"], flush=True); return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
