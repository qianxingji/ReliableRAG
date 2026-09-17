"""Run the frozen four-endpoint Mistral test analysis once."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_analysis_storage import BootstrapWriter
from scripts.mistral_development_acquisition_common import (
    read_jsonl,
    record,
    sha256,
    write_json_durable,
)
from scripts.mistral_test_analysis_math import (
    DRAWS,
    SEED,
    Panel,
    draw_record,
    intervals,
    point_estimates,
    question_weights,
)


REPO = Path(__file__).resolve().parents[1]
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_QUESTIONS = 6_000
EXPECTED_OUTCOME_VALUES = 72_000
ACTION_CAP = 900
MAX_STAGE_SECONDS = 6 * 60 * 60


def require(value, message):
    if not value:
        raise RuntimeError(message)


def validate_manifest(namespace: Path):
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
    paths = members | {manifest_path.resolve()}
    require(actual == paths, "PREDECESSOR_MANIFEST_COVERAGE")
    return paths


def validate_predecessors(root: Path):
    action = root / "action_seal"
    action_validation = root / "action_seal_validation/VALIDATION.json"
    outcomes = root / "test_outcomes"
    outcomes_validation = root / "test_outcomes_validation/VALIDATION.json"
    action_paths = validate_manifest(action)
    outcome_paths = validate_manifest(outcomes)
    require(action_validation.is_file() and outcomes_validation.is_file(),
            "INDEPENDENT_ACCEPTANCE_REQUIRED")
    action_receipt = json.loads(
        (action / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    action_acceptance = json.loads(action_validation.read_text(encoding="utf-8"))
    require(action_receipt.get("status")
            == "PASS_MISTRAL_TEST_ACTION_SEAL_PENDING_INDEPENDENT"
            and action_receipt.get("N_all") == EXPECTED_TRACES
            and action_receipt.get("action_cap") == ACTION_CAP
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
            and action_acceptance.get("action_cap") == ACTION_CAP
            and action_acceptance.get("test_gold_values_read") == 0
            and action_acceptance.get("test_outcome_values_read") == 0
            and action_acceptance.get("action_budget_tuned") is False,
            "ACTION_ACCEPTANCE")
    outcome_receipt = json.loads(
        (outcomes / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    outcome_acceptance = json.loads(outcomes_validation.read_text(encoding="utf-8"))
    require(outcome_receipt.get("status")
            == "PASS_MISTRAL_TEST_OUTCOMES_PENDING_INDEPENDENT"
            and outcome_receipt.get("completed_traces") == EXPECTED_TRACES
            and outcome_receipt.get("test_gold_metric_values_read")
            == EXPECTED_OUTCOME_VALUES
            and outcome_receipt.get("raw_reference_strings_written") == 0,
            "OUTCOME_RECEIPT")
    require(outcome_acceptance.get("status")
            == "PASS_INDEPENDENT_MISTRAL_TEST_OUTCOMES"
            and outcome_acceptance.get("producer_manifest_sha256")
            == sha256(outcomes / "SHA256_MANIFEST.json")
            and outcome_acceptance.get("producer_receipt_sha256")
            == sha256(outcomes / "STAGE_RECEIPT.json")
            and outcome_acceptance.get("test_outcomes_sha256")
            == sha256(outcomes / "TEST_OUTCOMES.jsonl")
            and outcome_acceptance.get("validated_traces") == EXPECTED_TRACES
            and outcome_acceptance.get("test_gold_metric_values_read")
            == EXPECTED_OUTCOME_VALUES
            and outcome_acceptance.get("raw_reference_strings_written") == 0,
            "OUTCOME_ACCEPTANCE")
    return (action, action_validation, outcomes, outcomes_validation,
            action_paths, outcome_paths)


def seal(stage_output: Path):
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path)
            item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS",
        "files": files,
        "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    args = parser.parse_args()
    root = args.test_root.resolve()
    require(root == TEST_ROOT.resolve(), "FIXED_TEST_ROOT")
    stage_output = root / "analysis"
    require(not stage_output.exists(), "SINGLE_USE_ANALYSIS_NAMESPACE")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    ).strip(), "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    (action, action_validation, outcomes, outcomes_validation,
     action_paths, outcome_paths) = validate_predecessors(root)
    stage_output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    writer = None
    result = {
        "status": "FAIL",
        "cas_q3_status": "NOT READY",
        "source_commit": commit,
        "stage": "analysis",
        "test_action_rows_read": 0,
        "test_numeric_outcome_rows_read": 0,
        "test_numeric_outcome_values_read": 0,
        "raw_reference_strings_read": 0,
        "scientific_fits": 0,
        "neural_model_loads": 0,
        "model_forwards": 0,
        "action_budget_tuned": False,
    }
    try:
        require(all(name not in sys.modules for name in
                    ("torch", "transformers", "sklearn")),
                "MODEL_RUNTIME_ALREADY_LOADED")
        input_paths = sorted({
            *action_paths,
            action_validation,
            *outcome_paths,
            outcomes_validation,
            Path(__file__),
            REPO / "scripts/validate_mistral_test_analysis.py",
            REPO / "scripts/mistral_test_analysis_math.py",
            REPO / "scripts/mistral_test_analysis_independent.py",
            REPO / "scripts/empirical_analysis_storage.py",
            REPO / "scripts/empirical_runtime_contract.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "src/evaluation/batch_allocation.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_TEST_ANALYSIS_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            Path(sys.executable),
        }, key=lambda path: str(Path(path).resolve()))
        inputs = [record(path) for path in input_paths]
        require(len({item["path"] for item in inputs}) == len(inputs),
                "UNIQUE_ANALYSIS_INPUTS")
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_TEST_ANALYSIS",
            "source_commit": commit,
            "stage": "analysis",
            "expected_traces": EXPECTED_TRACES,
            "expected_question_groups": EXPECTED_QUESTIONS,
            "action_cap": ACTION_CAP,
            "bootstrap_seed": SEED,
            "bootstrap_draws": DRAWS,
            "adjusted_quantiles": [0.00625, 0.99375],
            "primary_family_size": 4,
            "test_parameter_tuning": "FORBIDDEN",
            "inputs": inputs,
            "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "python_version": sys.version,
            "packages": {"numpy": importlib.metadata.version("numpy")},
        }
        write_json_durable(stage_output / "EXECUTABLE_FREEZE.json", freeze)

        actions = list(read_jsonl(action / "ACTION_ROWS.jsonl"))
        numeric_outcomes = list(read_jsonl(outcomes / "TEST_OUTCOMES.jsonl"))
        panel = Panel(actions, numeric_outcomes)
        result.update({
            "test_action_rows_read": EXPECTED_TRACES,
            "test_numeric_outcome_rows_read": EXPECTED_TRACES,
            "test_numeric_outcome_values_read": EXPECTED_OUTCOME_VALUES,
        })
        points = point_estimates(panel)
        write_json_durable(stage_output / "POINT_ESTIMATES.json", points)
        writer = BootstrapWriter(
            stage_output,
            groups=EXPECTED_QUESTIONS,
            draws=DRAWS,
            questions_per_dataset=2_000,
        )
        records = []
        for draw, weights in enumerate(question_weights(panel)):
            row = draw_record(panel, weights, draw)
            writer.append(weights, row)
            records.append(row)
            if (draw + 1) % 100 == 0:
                print(json.dumps({"completed_draws": draw + 1,
                                  "expected_draws": DRAWS}), flush=True)
        writer.close()
        interval_report = intervals(panel, records)
        write_json_durable(stage_output / "INTERVALS.json", interval_report)
        write_json_durable(stage_output / "BOOTSTRAP_STORAGE.json", writer.summary())
        for item in inputs:
            require(record(item["path"]) == item, "ANALYSIS_INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "ANALYSIS_WALL_LIMIT")
        result.update({
            "status": "PASS_MISTRAL_TEST_ANALYSIS_PENDING_INDEPENDENT",
            "N_all": panel.n,
            "question_groups": len(panel.groups),
            "N_eligible": panel.eligible_count,
            "action_cap": panel.cap,
            "completed_draws": len(records),
            "bootstrap_seed": SEED,
            "primary_interval_family_size": 4,
            "point_estimates": record(stage_output / "POINT_ESTIMATES.json"),
            "intervals": record(stage_output / "INTERVALS.json"),
            "bootstrap_weights": record(
                stage_output / "BOOTSTRAP_QUESTION_WEIGHTS.u16le"
            ),
            "bootstrap_draws": record(stage_output / "BOOTSTRAP_DRAWS.jsonl"),
            "bootstrap_storage": record(stage_output / "BOOTSTRAP_STORAGE.json"),
            "raw_reference_strings_read": 0,
            "scientific_fits": 0,
            "neural_model_loads": 0,
            "model_forwards": 0,
            "action_budget_tuned": False,
            "elapsed_seconds": elapsed,
        })
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        if writer is not None:
            writer.close()
            result["completed_draws"] = writer.completed
        result.update({
            "status": "FAIL_MISTRAL_TEST_ANALYSIS",
            "error_type": type(exc).__name__,
            "diagnostic": str(exc),
            "traceback": traceback.format_exc(),
            "elapsed_seconds": time.perf_counter() - started,
        })
        if not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result)
            seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
