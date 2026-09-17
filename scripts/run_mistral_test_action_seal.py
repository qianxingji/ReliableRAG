"""Seal Mistral test actions from accepted label-blind features and dev models."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    read_jsonl,
    record,
    sha256,
    write_json_durable,
)
from src.arbitration.mistral_reader_runtime import canonical
from src.arbitration.reader_test_prediction import (
    ACTION_CAP,
    EXPECTED_TRACES,
    PRIMARY_POLICIES,
    score_and_allocate,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_DEVELOPMENT_ROOT = REPO / "outputs/cas_q3/mistral_development_acquisition_v1"
EXPECTED_TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
MAX_STAGE_SECONDS = 60 * 60


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


def validate_predecessors(development_root: Path, test_root: Path):
    tuning = development_root / "tuning"
    tuning_validation = development_root / "tuning_validation/VALIDATION.json"
    prelabel = test_root / "prelabel"
    prelabel_validation = test_root / "prelabel_validation/VALIDATION.json"
    tuning_paths = validate_manifest(tuning)
    prelabel_paths = validate_manifest(prelabel)
    require(tuning_validation.is_file() and prelabel_validation.is_file(),
            "INDEPENDENT_ACCEPTANCE_REQUIRED")

    tuning_receipt = json.loads(
        (tuning / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    tuning_acceptance = json.loads(tuning_validation.read_text(encoding="utf-8"))
    require(tuning_receipt.get("status")
            == "PASS_MISTRAL_DEVELOPMENT_TUNING_PENDING_INDEPENDENT"
            and tuning_receipt.get("scientific_fit_attempts") == 84
            and tuning_receipt.get("test_rows_read") == 0
            and tuning_receipt.get("test_gold_values_read") == 0
            and tuning_receipt.get("action_budget_tuned") is False,
            "DEVELOPMENT_TUNING_RECEIPT")
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
            "DEVELOPMENT_TUNING_ACCEPTANCE")

    prelabel_receipt = json.loads(
        (prelabel / "STAGE_RECEIPT.json").read_text(encoding="utf-8")
    )
    prelabel_acceptance = json.loads(prelabel_validation.read_text(encoding="utf-8"))
    require(prelabel_receipt.get("status")
            == "PASS_MISTRAL_TEST_PRELABEL_PENDING_INDEPENDENT"
            and prelabel_receipt.get("completed_traces") == EXPECTED_TRACES
            and prelabel_receipt.get("test_gold_values_read") == 0
            and prelabel_receipt.get("test_outcome_values_read") == 0
            and prelabel_receipt.get("scientific_fits") == 0,
            "TEST_PRELABEL_RECEIPT")
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
            "TEST_PRELABEL_ACCEPTANCE")
    return (tuning, tuning_validation, prelabel, prelabel_validation,
            tuning_paths, prelabel_paths)


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
    parser.add_argument("--development-root", type=Path,
                        default=EXPECTED_DEVELOPMENT_ROOT)
    parser.add_argument("--test-root", type=Path, default=EXPECTED_TEST_ROOT)
    args = parser.parse_args()
    development_root = args.development_root.resolve()
    test_root = args.test_root.resolve()
    require(development_root == EXPECTED_DEVELOPMENT_ROOT.resolve()
            and test_root == EXPECTED_TEST_ROOT.resolve(), "FIXED_STAGE_ROOTS")
    stage_output = test_root / "action_seal"
    require(not stage_output.exists(), "SINGLE_USE_ACTION_SEAL_NAMESPACE")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    ).strip(), "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    (tuning, tuning_validation, prelabel, prelabel_validation,
     tuning_paths, prelabel_paths) = validate_predecessors(development_root, test_root)
    stage_output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    result = {
        "status": "FAIL",
        "cas_q3_status": "NOT READY",
        "source_commit": commit,
        "stage": "action_seal",
        "test_feature_rows_read": 0,
        "test_gold_values_read": 0,
        "test_outcome_values_read": 0,
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
            *prelabel_paths,
            prelabel_validation,
            *tuning_paths,
            tuning_validation,
            Path(__file__),
            REPO / "scripts/validate_mistral_test_action_seal.py",
            REPO / "scripts/mistral_test_prediction_independent.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "src/arbitration/reader_test_prediction.py",
            REPO / "src/arbitration/empirical_contract.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_TEST_ACTION_SEAL_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            Path(sys.executable),
        }, key=lambda path: str(Path(path).resolve()))
        inputs = [record(path) for path in input_paths]
        require(len({item["path"] for item in inputs}) == len(inputs),
                "UNIQUE_ACTION_SEAL_INPUTS")
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_TEST_ACTION_SEAL",
            "source_commit": commit,
            "stage": "action_seal",
            "methods": list(PRIMARY_POLICIES),
            "expected_traces": EXPECTED_TRACES,
            "action_cap": ACTION_CAP,
            "selected_recipe_role": "PRIMARY",
            "fixed_c1_recipe_role": "DESCRIPTIVE_OUTSIDE_CONFIRMATORY_FAMILY",
            "score_order": "descending_probability_then_dataset_retriever_sample_id",
            "test_outcome_access": "FORBIDDEN",
            "action_budget_tuning": "FORBIDDEN",
            "inputs": inputs,
            "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "python_version": sys.version,
            "packages": {"numpy": importlib.metadata.version("numpy")},
        }
        write_json_durable(stage_output / "EXECUTABLE_FREEZE.json", freeze)

        prelabel_rows = list(read_jsonl(prelabel / "PRELABEL_ROWS.jsonl"))
        tuning_results = json.loads(
            (tuning / "TUNING_RESULTS.json").read_text(encoding="utf-8")
        )
        sealed = score_and_allocate(prelabel_rows, tuning_results)
        result["test_feature_rows_read"] = EXPECTED_TRACES
        raw = b"".join(canonical(row) + b"\n" for row in sealed["rows"])
        action_path = stage_output / "ACTION_ROWS.jsonl"
        with action_path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        for item in inputs:
            require(record(item["path"]) == item, "ACTION_SEAL_INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "ACTION_SEAL_WALL_LIMIT")
        result.update({
            "status": "PASS_MISTRAL_TEST_ACTION_SEAL_PENDING_INDEPENDENT",
            "N_all": sealed["N_all"],
            "N_eligible": sealed["N_eligible"],
            "action_cap": sealed["action_cap"],
            "replacement_counts": sealed["replacement_counts"],
            "model_bindings": sealed["model_bindings"],
            "action_rows": record(action_path),
            "test_gold_values_read": 0,
            "test_outcome_values_read": 0,
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
        result.update({
            "status": "FAIL_MISTRAL_TEST_ACTION_SEAL",
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
