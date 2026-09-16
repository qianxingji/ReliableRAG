"""Independently replay all Mistral test point and bootstrap arithmetic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import read_jsonl, sha256
from scripts.mistral_test_analysis_independent import (
    IndependentPanel,
    compare_report,
    independent_intervals,
    validate_draw_files,
)


REPO = Path(__file__).resolve().parents[1]
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_QUESTIONS = 6_000
EXPECTED_OUTCOME_VALUES = 72_000
ACTION_CAP = 900
DRAWS = 20_000
SEED = 20260930


def require(value, message):
    if not value:
        raise RuntimeError(message)


def validate_manifest(namespace: Path):
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
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_predecessors(root: Path):
    action = root / "action_seal"
    action_validation = root / "action_seal_validation/VALIDATION.json"
    outcomes = root / "test_outcomes"
    outcomes_validation = root / "test_outcomes_validation/VALIDATION.json"
    validate_manifest(action)
    validate_manifest(outcomes)
    require(action_validation.is_file() and outcomes_validation.is_file(),
            "PREDECESSOR_VALIDATIONS")
    action_receipt = json.loads(
        (action / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    action_acceptance = json.loads(action_validation.read_text(encoding="utf-8"))
    outcome_receipt = json.loads(
        (outcomes / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    outcome_acceptance = json.loads(outcomes_validation.read_text(encoding="utf-8"))
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
            and action_acceptance.get("test_outcome_values_read") == 0,
            "ACTION_ACCEPTANCE")
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
    return action, action_validation, outcomes, outcomes_validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.test_root.resolve()
    output = (args.output.resolve() if args.output else
              (root / "analysis_validation/VALIDATION.json").resolve())
    require(root == TEST_ROOT.resolve()
            and output == (root / "analysis_validation/VALIDATION.json").resolve()
            and not output.exists(), "FIXED_ROOT_OR_OUTPUT")
    action, action_validation, outcomes, outcomes_validation = validate_predecessors(root)
    namespace = root / "analysis"
    validate_manifest(namespace)
    receipt = json.loads(
        (namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    require(receipt.get("status")
            == "PASS_MISTRAL_TEST_ANALYSIS_PENDING_INDEPENDENT"
            and receipt.get("N_all") == EXPECTED_TRACES
            and receipt.get("question_groups") == EXPECTED_QUESTIONS
            and receipt.get("action_cap") == ACTION_CAP
            and receipt.get("completed_draws") == DRAWS
            and receipt.get("bootstrap_seed") == SEED
            and receipt.get("primary_interval_family_size") == 4
            and receipt.get("test_action_rows_read") == EXPECTED_TRACES
            and receipt.get("test_numeric_outcome_rows_read") == EXPECTED_TRACES
            and receipt.get("test_numeric_outcome_values_read")
            == EXPECTED_OUTCOME_VALUES
            and receipt.get("raw_reference_strings_read") == 0
            and receipt.get("scientific_fits") == 0
            and receipt.get("action_budget_tuned") is False,
            "ANALYSIS_RECEIPT")
    freeze = json.loads(
        (namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8")
    )
    require(freeze.get("source_commit") == receipt.get("source_commit")
            and freeze.get("status") == "FROZEN_BEFORE_MISTRAL_TEST_ANALYSIS"
            and freeze.get("expected_traces") == EXPECTED_TRACES
            and freeze.get("expected_question_groups") == EXPECTED_QUESTIONS
            and freeze.get("action_cap") == ACTION_CAP
            and freeze.get("bootstrap_seed") == SEED
            and freeze.get("bootstrap_draws") == DRAWS
            and freeze.get("adjusted_quantiles") == [0.00625, 0.99375]
            and freeze.get("primary_family_size") == 4
            and freeze.get("test_parameter_tuning") == "FORBIDDEN",
            "ANALYSIS_FREEZE")
    for item in freeze.get("inputs", []):
        path = Path(item["path"])
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_ANALYSIS_INPUT")
    input_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(action_validation.resolve() in input_paths
            and outcomes_validation.resolve() in input_paths,
            "FROZEN_ACCEPTANCE_INPUTS")

    actions = list(read_jsonl(action / "ACTION_ROWS.jsonl"))
    numeric_outcomes = list(read_jsonl(outcomes / "TEST_OUTCOMES.jsonl"))
    panel = IndependentPanel(actions, numeric_outcomes)
    saved_points = json.loads(
        (namespace / "POINT_ESTIMATES.json").read_text(encoding="utf-8")
    )
    compare_report(saved_points, panel.point())
    accepted_draws = validate_draw_files(
        panel,
        namespace / "BOOTSTRAP_QUESTION_WEIGHTS.u16le",
        namespace / "BOOTSTRAP_DRAWS.jsonl",
        draws=DRAWS,
        seed=SEED,
        progress=lambda count: print(json.dumps({
            "validated_draws": count,
            "expected_draws": DRAWS,
        }), flush=True) if count % 100 == 0 else None,
    )
    expected_intervals = independent_intervals(panel, accepted_draws)
    saved_intervals = json.loads(
        (namespace / "INTERVALS.json").read_text(encoding="utf-8")
    )
    compare_report(saved_intervals, expected_intervals)
    storage = json.loads(
        (namespace / "BOOTSTRAP_STORAGE.json").read_text(encoding="utf-8")
    )
    require(storage == {
        "dtype": "little-endian uint16",
        "shape": [DRAWS, EXPECTED_QUESTIONS],
        "completed_draws": DRAWS,
        "completed_weight_bytes": DRAWS * EXPECTED_QUESTIONS * 2,
        "expected_complete_weight_bytes": DRAWS * EXPECTED_QUESTIONS * 2,
        "maximum_count": 2_000,
        "arithmetic_dtype": "int64",
        "no_header": True,
    }, "BOOTSTRAP_STORAGE")
    for name, filename in (
        ("point_estimates", "POINT_ESTIMATES.json"),
        ("intervals", "INTERVALS.json"),
        ("bootstrap_weights", "BOOTSTRAP_QUESTION_WEIGHTS.u16le"),
        ("bootstrap_draws", "BOOTSTRAP_DRAWS.jsonl"),
        ("bootstrap_storage", "BOOTSTRAP_STORAGE.json"),
    ):
        path = namespace / filename
        require(receipt.get(name) == {
            "path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }, "ANALYSIS_FILE_BINDING")
    require(all(name not in sys.modules for name in
                ("torch", "transformers", "sklearn")),
            "MODEL_RUNTIME_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_MISTRAL_TEST_ANALYSIS",
        "cas_q3_status": "NOT READY",
        "producer_manifest_sha256": sha256(namespace / "SHA256_MANIFEST.json"),
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "point_estimates_sha256": sha256(namespace / "POINT_ESTIMATES.json"),
        "intervals_sha256": sha256(namespace / "INTERVALS.json"),
        "bootstrap_weights_sha256": sha256(
            namespace / "BOOTSTRAP_QUESTION_WEIGHTS.u16le"
        ),
        "bootstrap_draws_sha256": sha256(namespace / "BOOTSTRAP_DRAWS.jsonl"),
        "validated_rows": EXPECTED_TRACES,
        "validated_question_groups": EXPECTED_QUESTIONS,
        "validated_draws": DRAWS,
        "bootstrap_seed": SEED,
        "action_cap": ACTION_CAP,
        "primary_interval_family_size": 4,
        "test_numeric_outcome_values_read": EXPECTED_OUTCOME_VALUES,
        "raw_reference_strings_read": 0,
        "scientific_fits": 0,
        "neural_model_loads": 0,
        "model_forwards": 0,
        "action_budget_tuned": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2,
                                  allow_nan=False).encode("utf-8") + b"\n")
    print(result["status"], flush=True)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
