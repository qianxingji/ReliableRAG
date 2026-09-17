"""Independently reconstruct the label-blind Mistral test action seal."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import read_jsonl, sha256
from scripts.mistral_test_prediction_independent import (
    PRIMARY_POLICIES,
    _independent_score_and_allocate,
    compare_seals,
)
from src.arbitration.mistral_reader_runtime import canonical


REPO = Path(__file__).resolve().parents[1]
EXPECTED_DEVELOPMENT_ROOT = REPO / "outputs/cas_q3/mistral_development_acquisition_v1"
EXPECTED_TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
ACTION_CAP = 900


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
    paths = members | {manifest_path.resolve()}
    require(actual == paths, "MANIFEST_COVERAGE")
    return paths


def predecessor_paths(development_root: Path, test_root: Path):
    tuning = development_root / "tuning"
    tuning_validation = development_root / "tuning_validation/VALIDATION.json"
    prelabel = test_root / "prelabel"
    prelabel_validation = test_root / "prelabel_validation/VALIDATION.json"
    tuning_paths = validate_manifest(tuning)
    prelabel_paths = validate_manifest(prelabel)
    require(tuning_validation.is_file() and prelabel_validation.is_file(),
            "PREDECESSOR_VALIDATIONS")
    tuning_receipt = json.loads(
        (tuning / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    tuning_acceptance = json.loads(tuning_validation.read_text(encoding="utf-8"))
    prelabel_receipt = json.loads(
        (prelabel / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    prelabel_acceptance = json.loads(prelabel_validation.read_text(encoding="utf-8"))
    require(tuning_receipt.get("status")
            == "PASS_MISTRAL_DEVELOPMENT_TUNING_PENDING_INDEPENDENT"
            and tuning_receipt.get("scientific_fit_attempts") == 84
            and tuning_receipt.get("test_rows_read") == 0
            and tuning_receipt.get("test_gold_values_read") == 0
            and tuning_receipt.get("action_budget_tuned") is False,
            "TUNING_RECEIPT")
    require(tuning_acceptance.get("status")
            == "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_TUNING"
            and tuning_acceptance.get("producer_manifest_sha256")
            == sha256(tuning / "SHA256_MANIFEST.json")
            and tuning_acceptance.get("producer_receipt_sha256")
            == sha256(tuning / "STAGE_RECEIPT.json")
            and tuning_acceptance.get("tuning_results_sha256")
            == sha256(tuning / "TUNING_RESULTS.json")
            and tuning_acceptance.get("scientific_fit_attempts_verified") == 84
            and tuning_acceptance.get("independent_audit_refit_attempts") == 84
            and tuning_acceptance.get("test_rows_read") == 0
            and tuning_acceptance.get("test_gold_values_read") == 0
            and tuning_acceptance.get("action_budget_tuned") is False,
            "TUNING_ACCEPTANCE")
    require(prelabel_receipt.get("status")
            == "PASS_MISTRAL_TEST_PRELABEL_PENDING_INDEPENDENT"
            and prelabel_receipt.get("completed_traces") == EXPECTED_TRACES
            and prelabel_receipt.get("test_gold_values_read") == 0
            and prelabel_receipt.get("test_outcome_values_read") == 0
            and prelabel_receipt.get("scientific_fits") == 0,
            "PRELABEL_RECEIPT")
    require(prelabel_acceptance.get("status")
            == "PASS_INDEPENDENT_MISTRAL_TEST_PRELABEL_FREEZE"
            and prelabel_acceptance.get("producer_manifest_sha256")
            == sha256(prelabel / "SHA256_MANIFEST.json")
            and prelabel_acceptance.get("producer_receipt_sha256")
            == sha256(prelabel / "STAGE_RECEIPT.json")
            and prelabel_acceptance.get("prelabel_rows_sha256")
            == sha256(prelabel / "PRELABEL_ROWS.jsonl")
            and prelabel_acceptance.get("test_gold_values_read") == 0
            and prelabel_acceptance.get("test_outcome_values_read") == 0
            and prelabel_acceptance.get("scientific_fits") == 0,
            "PRELABEL_ACCEPTANCE")
    return (tuning, tuning_validation, prelabel, prelabel_validation,
            tuning_paths, prelabel_paths)


def read_canonical_rows(path: Path):
    rows = []
    with path.open("rb") as handle:
        for raw in handle:
            require(raw.endswith(b"\n"), "PARTIAL_ACTION_ROW")
            row = json.loads(raw)
            require(raw == canonical(row) + b"\n", "NONCANONICAL_ACTION_ROW")
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-root", type=Path,
                        default=EXPECTED_DEVELOPMENT_ROOT)
    parser.add_argument("--test-root", type=Path, default=EXPECTED_TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    development_root = args.development_root.resolve()
    test_root = args.test_root.resolve()
    output = (args.output.resolve() if args.output else
              test_root / "action_seal_validation/VALIDATION.json")
    require(development_root == EXPECTED_DEVELOPMENT_ROOT.resolve()
            and test_root == EXPECTED_TEST_ROOT.resolve()
            and output == (test_root / "action_seal_validation/VALIDATION.json").resolve()
            and not output.exists(), "FIXED_ROOTS_OR_OUTPUT")

    (tuning, tuning_validation, prelabel, prelabel_validation,
     tuning_paths, prelabel_paths) = predecessor_paths(development_root, test_root)
    namespace = test_root / "action_seal"
    validate_manifest(namespace)
    receipt = json.loads(
        (namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    require(receipt.get("status")
            == "PASS_MISTRAL_TEST_ACTION_SEAL_PENDING_INDEPENDENT"
            and receipt.get("test_feature_rows_read") == EXPECTED_TRACES
            and receipt.get("test_gold_values_read") == 0
            and receipt.get("test_outcome_values_read") == 0
            and receipt.get("scientific_fits") == 0
            and receipt.get("neural_model_loads") == 0
            and receipt.get("model_forwards") == 0
            and receipt.get("action_budget_tuned") is False,
            "ACTION_RECEIPT")
    freeze = json.loads(
        (namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8")
    )
    require(freeze.get("source_commit") == receipt.get("source_commit")
            and freeze.get("status") == "FROZEN_BEFORE_MISTRAL_TEST_ACTION_SEAL"
            and freeze.get("methods") == list(PRIMARY_POLICIES)
            and freeze.get("expected_traces") == EXPECTED_TRACES
            and freeze.get("action_cap") == ACTION_CAP
            and freeze.get("selected_recipe_role") == "PRIMARY"
            and freeze.get("fixed_c1_recipe_role")
            == "DESCRIPTIVE_OUTSIDE_CONFIRMATORY_FAMILY"
            and freeze.get("python") == str(Path(sys.executable).resolve())
            and freeze.get("python_version") == sys.version
            and freeze.get("packages")
            == {"numpy": importlib.metadata.version("numpy")}
            and freeze.get("test_outcome_access") == "FORBIDDEN"
            and freeze.get("action_budget_tuning") == "FORBIDDEN",
            "ACTION_EXECUTABLE_FREEZE")
    for item in freeze.get("inputs", []):
        path = Path(item["path"])
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_ACTION_INPUT")
    input_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(len(input_paths) == len(freeze["inputs"]), "UNIQUE_FROZEN_INPUTS")
    required_inputs = {
        *tuning_paths, tuning_validation.resolve(),
        *prelabel_paths, prelabel_validation.resolve(),
        (REPO / "scripts/run_mistral_test_action_seal.py").resolve(),
        Path(__file__).resolve(),
        (REPO / "scripts/mistral_test_prediction_independent.py").resolve(),
        (REPO / "scripts/mistral_development_acquisition_common.py").resolve(),
        (REPO / "src/arbitration/mistral_reader_runtime.py").resolve(),
        (REPO / "src/arbitration/reader_test_prediction.py").resolve(),
        (REPO / "src/arbitration/empirical_contract.py").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_ACTION_SEAL_INPUT_GRAPH_AMENDMENT_2026-09-17.md").resolve(),
        Path(sys.executable).resolve(),
    }
    require(required_inputs == input_paths, "NONEXACT_FROZEN_INPUT_GRAPH")

    prelabel_rows = list(read_jsonl(prelabel / "PRELABEL_ROWS.jsonl"))
    tuning_results = json.loads(
        (tuning / "TUNING_RESULTS.json").read_text(encoding="utf-8")
    )
    expected = _independent_score_and_allocate(
        prelabel_rows, tuning_results,
        expected_traces=EXPECTED_TRACES,
        questions_per_dataset=2_000,
        action_cap=ACTION_CAP,
    )
    action_path = namespace / "ACTION_ROWS.jsonl"
    rows = read_canonical_rows(action_path)
    actual = {
        "schema_version": 1,
        "role": "LABEL_BLIND_MISTRAL_TEST_ACTION_SEAL",
        "N_all": receipt["N_all"],
        "N_eligible": receipt["N_eligible"],
        "action_cap": receipt["action_cap"],
        "replacement_counts": receipt["replacement_counts"],
        "model_bindings": receipt["model_bindings"],
        "test_labels_read": False,
        "test_outcomes_read": False,
        "action_budget_tuned": receipt["action_budget_tuned"],
        "rows": rows,
    }
    compare_seals(actual, expected, tolerance=1e-12)
    require(receipt.get("action_rows") == {
        "path": str(action_path.resolve()),
        "size_bytes": action_path.stat().st_size,
        "sha256": sha256(action_path),
    }, "ACTION_FILE_BINDING")
    require(all(name not in sys.modules for name in
                ("torch", "transformers", "sklearn")),
            "MODEL_RUNTIME_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_MISTRAL_TEST_ACTION_SEAL",
        "cas_q3_status": "NOT READY",
        "producer_manifest_sha256": sha256(namespace / "SHA256_MANIFEST.json"),
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "action_rows_sha256": sha256(action_path),
        "validated_rows": EXPECTED_TRACES,
        "N_eligible": expected["N_eligible"],
        "action_cap": ACTION_CAP,
        "replacement_counts": expected["replacement_counts"],
        "model_bindings": expected["model_bindings"],
        "probability_tolerance": 1e-12,
        "test_feature_rows_read": EXPECTED_TRACES,
        "test_gold_values_read": 0,
        "test_outcome_values_read": 0,
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
