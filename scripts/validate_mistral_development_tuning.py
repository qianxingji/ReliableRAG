"""Independently refit and verify the frozen Mistral development head search."""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import warnings

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_info, threadpool_limits

from scripts.validate_mistral_development_a0_query import read_rows, require, sha256
from src.arbitration.empirical_contract import DATASETS, RETRIEVERS


REPO = Path(__file__).resolve().parents[1]
METHODS = ("HGB_GBV_R", "HGB_ONLY_R", "GBV_ONLY_R")
WIDTHS = {"HGB_GBV_R": 2, "HGB_ONLY_R": 1, "GBV_ONLY_R": 1}
FOLD_PREFIX = "cas-q3-reader-tuning-fold-v1|20260917"
C_VALUES = (0.01, 0.1, 1.0, 10.0)
C_TIE_ORDER = (1.0, 0.1, 10.0, 0.01)
BASE = {
    "solver": "lbfgs", "max_iter": 5000, "penalty": "l2", "tol": 1e-4,
    "fit_intercept": True, "random_state": None,
}
PLATT = {**BASE, "C": 1e6, "class_weight": None, "max_iter": 2000}
EXPECTED_TRACES = 13_500
IDENTITY_FIELDS = ("dataset", "retriever", "sample_id", "position", "role")
PRELABEL_FIELDS = frozenset({
    *IDENTITY_FIELDS, "pair_eligible", "eligible", "forced_keep_reason",
    "hgb_score", "gbv_F0", "gbv_F1", "gbv_margin", "feature_vectors",
    "source_bindings",
})
OUTCOME_FIELDS = frozenset({
    *IDENTITY_FIELDS, "prelabel_row_sha256", "a0_receipt_sha256",
    "a1_receipt_sha256", "a0_em", "a1_em", "a0_f1", "a1_f1",
})


class IndependentTuningError(RuntimeError):
    pass


def needed(condition: bool, message: str) -> None:
    if not condition:
        raise IndependentTuningError(message)


def object_sha(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def key_hash(keys) -> str:
    payload = "".join(
        json.dumps(list(key), ensure_ascii=False, separators=(",", ":")) + "\n"
        for key in sorted(keys)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def grid() -> tuple[dict, ...]:
    return tuple({**BASE, "C": value, "class_weight": weight}
                 for value in C_VALUES for weight in (None, "balanced"))


def candidate_id(parameters: dict) -> str:
    weight = "none" if parameters["class_weight"] is None else "balanced"
    return f"C={parameters['C']:g}|class_weight={weight}"


def tie_rank(parameters: dict) -> tuple[int, int]:
    return (0 if parameters["class_weight"] is None else 1,
            C_TIE_ORDER.index(float(parameters["C"])))


def independent_folds(fit_keys) -> tuple[dict, ...]:
    keys = set(fit_keys); groups = {(key[0], key[2]) for key in keys}
    needed(len(keys) == 10_800 and len(groups) == 3_600, "INDEPENDENT_FIT_SCOPE")
    needed({key[0] for key in keys} == set(DATASETS), "INDEPENDENT_DATASETS")
    for dataset, sample_id in groups:
        needed({(dataset, retriever, sample_id) for retriever in RETRIEVERS} <= keys,
               "INDEPENDENT_FIT_SIBLINGS")
    buckets = [set(), set(), set()]
    for dataset in DATASETS:
        values = sorted(
            (group for group in groups if group[0] == dataset),
            key=lambda group: (
                hashlib.sha256(
                    f"{FOLD_PREFIX}|{group[0]}|{group[1]}".encode("utf-8")
                ).hexdigest(),
                group[1],
            ),
        )
        needed(len(values) == 1_200, "INDEPENDENT_DATASET_FIT_SCOPE")
        for index, group in enumerate(values):
            buckets[index % 3].add(group)
    folds = []
    for index, validation_groups in enumerate(buckets):
        validation = {key for key in keys if (key[0], key[2]) in validation_groups}
        training = keys - validation
        needed(len(validation) == 3_600 and len(training) == 7_200,
               "INDEPENDENT_FOLD_SIZE")
        needed(all(sum(group[0] == dataset for group in validation_groups) == 400
                   for dataset in DATASETS), "INDEPENDENT_FOLD_BALANCE")
        folds.append({"fold_index": index, "train": training,
                      "validation": validation})
    needed(set.union(*(fold["validation"] for fold in folds)) == keys,
           "INDEPENDENT_FOLD_COVERAGE")
    return tuple(folds)


def assemble_inputs(prelabel_rows: list[dict], outcome_rows: list[dict]):
    needed(len(prelabel_rows) == len(outcome_rows) == EXPECTED_TRACES,
           "INDEPENDENT_SOURCE_COUNTS")
    features = {method: {} for method in METHODS}
    outcomes = {}; parts = {"fit": set(), "cal": set()}
    for position, (prelabel, outcome) in enumerate(zip(
            prelabel_rows, outcome_rows, strict=True)):
        needed(set(prelabel) == PRELABEL_FIELDS and set(outcome) == OUTCOME_FIELDS,
               "INDEPENDENT_SOURCE_SCHEMA")
        identity = {name: prelabel[name] for name in IDENTITY_FIELDS}
        needed(identity["position"] == position
               and all(outcome[name] == value for name, value in identity.items())
               and outcome["prelabel_row_sha256"] == object_sha(prelabel),
               "INDEPENDENT_SOURCE_BINDING")
        key = (identity["dataset"], identity["retriever"], identity["sample_id"])
        needed(key not in outcomes and identity["role"] in parts,
               "INDEPENDENT_UNIQUE_KEY")
        outcomes[key] = outcome; parts[identity["role"]].add(key)
        needed(set(prelabel["feature_vectors"]) == set(METHODS),
               "INDEPENDENT_METHODS")
        for method in METHODS:
            numeric = prelabel["feature_vectors"][method]
            needed(type(numeric) is list and len(numeric) == WIDTHS[method],
                   "INDEPENDENT_FEATURE_WIDTH")
            features[method][key] = {
                "eligible": prelabel["eligible"], "numeric": numeric,
            }
    needed(len(parts["fit"]) == 10_800 and len(parts["cal"]) == 2_700
           and parts["fit"].isdisjoint(parts["cal"]),
           "INDEPENDENT_DEVELOPMENT_PARTS")
    groups = collections.defaultdict(set); group_roles = {}
    for role, keys in parts.items():
        for dataset, retriever, sample_id in keys:
            group = (dataset, sample_id); groups[group].add(retriever)
            needed(group not in group_roles or group_roles[group] == role,
                   "INDEPENDENT_SIBLING_ROLE")
            group_roles[group] = role
    needed(len(groups) == 4_500
           and all(value == set(RETRIEVERS) for value in groups.values())
           and all(sum(dataset == name for dataset, _ in groups) == 1_500
                   for name in DATASETS)
           and collections.Counter(group_roles.values()) == {"fit": 3_600, "cal": 900},
           "INDEPENDENT_QUESTION_GROUPS")
    return features, outcomes, parts


def numeric(rows: dict, keys: list[tuple], width: int) -> np.ndarray:
    return np.asarray([
        [np.nan if value is None else value for value in rows[key]["numeric"]]
        for key in keys
    ], dtype=np.float64).reshape(len(keys), width)


def transform(rows: dict, train_keys: list[tuple], apply_keys: list[tuple], width: int):
    train = numeric(rows, train_keys, width); apply = numeric(rows, apply_keys, width)
    needed(np.isfinite(train).any(axis=0).all(), "INDEPENDENT_ALL_MISSING_COLUMN")
    median = np.nanmedian(np.where(np.isfinite(train), train, np.nan), axis=0)
    filled = np.where(np.isfinite(train), train, median)
    mean = filled.mean(axis=0); std = filled.std(axis=0, ddof=0)
    std = np.where(std == 0, 1, std)

    def apply_transform(values, keys):
        missing = ~np.isfinite(values)
        scaled = (np.where(missing, median, values) - mean) / std
        retrievers = np.asarray([
            [float(key[1] == retriever) for retriever in RETRIEVERS] for key in keys
        ], dtype=np.float64)
        design = np.concatenate((scaled, missing.astype(np.float64), retrievers), axis=1)
        needed(np.isfinite(design).all(), "INDEPENDENT_NONFINITE_DESIGN")
        return design

    return (apply_transform(train, train_keys), apply_transform(apply, apply_keys),
            {"median": median.tolist(), "mean": mean.tolist(), "std": std.tolist()})


def target(outcome: dict) -> int:
    needed(outcome["a0_em"] in (0, 1) and outcome["a1_em"] in (0, 1),
           "INDEPENDENT_NONBINARY_EM")
    return int(outcome["a0_em"] == 0 and outcome["a1_em"] == 1)


def fit(values: np.ndarray, labels: np.ndarray, parameters: dict):
    needed(set(labels.tolist()) == {0, 1}, "INDEPENDENT_MISSING_CLASS")
    model = LogisticRegression(**parameters)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always"); model.fit(values, labels)
    needed(not any(issubclass(item.category, ConvergenceWarning) for item in captured),
           "INDEPENDENT_NONCONVERGENCE")
    needed(np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all(),
           "INDEPENDENT_NONFINITE_MODEL")
    return model


def replay_variant(rows: dict, outcomes: dict, parts: dict, variant: str) -> dict:
    width = WIDTHS[variant]; folds = independent_folds(parts["fit"])
    candidates = []; fit_attempts = successes = 0
    for parameters in grid():
        item = {"candidate_id": candidate_id(parameters),
                "parameters": parameters, "valid": True, "folds": []}
        loss_sum = 0.0; pooled = 0
        for fold in folds:
            train_keys = sorted(key for key in fold["train"] if rows[key]["eligible"])
            validation_keys = sorted(key for key in fold["validation"]
                                     if rows[key]["eligible"])
            record = {
                "fold_index": fold["fold_index"],
                "train_keys_sha256": key_hash(train_keys),
                "validation_keys_sha256": key_hash(validation_keys),
                "train_rows": len(train_keys), "validation_rows": len(validation_keys),
            }
            fit_attempts += 1
            try:
                needed(bool(train_keys) and bool(validation_keys), "INDEPENDENT_EMPTY_FOLD")
                x_train, x_validation, preprocessing = transform(
                    rows, train_keys, validation_keys, width,
                )
                y_train = np.asarray([target(outcomes[key]) for key in train_keys],
                                     dtype=np.int64)
                y_validation = np.asarray([target(outcomes[key]) for key in validation_keys],
                                          dtype=np.int64)
                model = fit(x_train, y_train, parameters); successes += 1
                logits = x_validation @ model.coef_[0] + model.intercept_[0]
                losses = np.logaddexp(0.0, logits) - y_validation * logits
                needed(np.isfinite(losses).all(), "INDEPENDENT_NONFINITE_LOSS")
                fold_sum = math.fsum(float(value) for value in losses)
                record.update({
                    "status": "PASS",
                    "train_class_counts": np.bincount(y_train, minlength=2).tolist(),
                    "validation_class_counts": np.bincount(
                        y_validation, minlength=2).tolist(),
                    "validation_log_loss_sum": fold_sum,
                    "validation_log_loss": fold_sum / len(y_validation),
                    "preprocessing": preprocessing,
                    "coef": model.coef_[0].tolist(),
                    "intercept": float(model.intercept_[0]),
                    "iterations": model.n_iter_.tolist(),
                })
                loss_sum += fold_sum; pooled += len(y_validation)
            except (IndependentTuningError, ValueError, FloatingPointError) as exc:
                record.update({"status": "FAIL",
                               "error_type": type(exc).__name__, "error": str(exc)})
                item["valid"] = False
            item["folds"].append(record)
        if item["valid"]:
            needed(pooled > 0, "INDEPENDENT_EMPTY_POOLED")
            item.update({"pooled_validation_rows": pooled,
                         "pooled_log_loss_sum": loss_sum,
                         "pooled_log_loss": loss_sum / pooled})
        candidates.append(item)
    valid = [item for item in candidates if item["valid"]]
    needed(bool(valid), "INDEPENDENT_ALL_CANDIDATES_INVALID")
    selected = min(valid, key=lambda item: (item["pooled_log_loss"],
                                            tie_rank(item["parameters"])))
    fit_keys = sorted(key for key in parts["fit"] if rows[key]["eligible"])
    cal_keys = sorted(key for key in parts["cal"] if rows[key]["eligible"])
    x_fit, x_cal, preprocessing = transform(rows, fit_keys, cal_keys, width)
    y_fit = np.asarray([target(outcomes[key]) for key in fit_keys], dtype=np.int64)
    y_cal = np.asarray([target(outcomes[key]) for key in cal_keys], dtype=np.int64)
    fit_attempts += 1; base = fit(x_fit, y_fit, selected["parameters"]); successes += 1
    calibration_logits = x_cal @ base.coef_[0] + base.intercept_[0]
    fit_attempts += 1
    platt = fit(calibration_logits.reshape(-1, 1), y_cal, PLATT); successes += 1
    fixed_parameters = {**BASE, "C": 1.0, "class_weight": None}
    fixed_identifier = candidate_id(fixed_parameters)
    fit_attempts += 1; fixed_base = fit(x_fit, y_fit, fixed_parameters); successes += 1
    fixed_logits = x_cal @ fixed_base.coef_[0] + fixed_base.intercept_[0]
    fit_attempts += 1
    fixed_platt = fit(fixed_logits.reshape(-1, 1), y_cal, PLATT); successes += 1
    return {
        "schema_version": 1, "role": "DEVELOPMENT_ONLY_READER_HEAD_TUNING",
        "variant": variant, "fold_prefix": FOLD_PREFIX,
        "folds": [{
            "fold_index": fold["fold_index"],
            "train_keys_sha256": key_hash(fold["train"]),
            "validation_keys_sha256": key_hash(fold["validation"]),
            "train_traces": len(fold["train"]),
            "validation_traces": len(fold["validation"]),
        } for fold in folds],
        "candidates": candidates,
        "selected_candidate_id": selected["candidate_id"],
        "selected_parameters": selected["parameters"],
        "selection_metric": "pooled_eligible_validation_binary_log_loss",
        "selection_value": selected["pooled_log_loss"],
        "fit_attempts": fit_attempts, "successful_fits": successes,
        "final_model": {
            "fit_keys_sha256": key_hash(fit_keys), "cal_keys_sha256": key_hash(cal_keys),
            "fit_rows": len(fit_keys), "cal_rows": len(cal_keys),
            "fit_class_counts": np.bincount(y_fit, minlength=2).tolist(),
            "cal_class_counts": np.bincount(y_cal, minlength=2).tolist(),
            "preprocessing": preprocessing, "coef": base.coef_[0].tolist(),
            "intercept": float(base.intercept_[0]),
            "base_iterations": base.n_iter_.tolist(), "platt_parameters": PLATT,
            "platt_slope": float(platt.coef_[0, 0]),
            "platt_intercept": float(platt.intercept_[0]),
            "platt_iterations": platt.n_iter_.tolist(),
        },
        "fixed_reference_model": {
            "candidate_id": fixed_identifier,
            "parameters": fixed_parameters,
            "fit_keys_sha256": key_hash(fit_keys),
            "cal_keys_sha256": key_hash(cal_keys),
            "fit_rows": len(fit_keys), "cal_rows": len(cal_keys),
            "fit_class_counts": np.bincount(y_fit, minlength=2).tolist(),
            "cal_class_counts": np.bincount(y_cal, minlength=2).tolist(),
            "preprocessing": preprocessing,
            "coef": fixed_base.coef_[0].tolist(),
            "intercept": float(fixed_base.intercept_[0]),
            "base_iterations": fixed_base.n_iter_.tolist(),
            "platt_parameters": PLATT,
            "platt_slope": float(fixed_platt.coef_[0, 0]),
            "platt_intercept": float(fixed_platt.intercept_[0]),
            "platt_iterations": fixed_platt.n_iter_.tolist(),
        },
        "test_labels_read": False, "test_predictions_emitted": False,
        "action_budget_tuned": False,
    }


def comparable(value):
    if isinstance(value, dict):
        return {key: comparable(item) for key, item in value.items()
                if key not in {"error", "error_type"}}
    if isinstance(value, list):
        return [comparable(item) for item in value]
    return value


def compare(actual, expected, state: dict) -> None:
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected),
                "RESULT_DICTIONARY_SCHEMA")
        for key in expected:
            compare(actual[key], expected[key], state)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected),
                "RESULT_LIST_SCHEMA")
        for left, right in zip(actual, expected, strict=True):
            compare(left, right, state)
    elif (type(expected) is float or type(actual) is float):
        require(type(actual) in (int, float) and math.isfinite(actual)
                and math.isfinite(expected), "RESULT_FINITE_NUMERIC")
        error = abs(float(actual) - float(expected))
        state["maximum_numeric_error"] = max(state["maximum_numeric_error"], error)
        require(error <= 1e-10, "RESULT_NUMERIC_TOLERANCE")
        state["numeric_checks"] += 1
    else:
        require(actual == expected, "RESULT_EXACT_VALUE")
        state["exact_checks"] += 1


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


def read_canonical_events(path: Path) -> list[dict]:
    rows = []
    with path.open("rb") as handle:
        for raw in handle:
            require(raw.endswith(b"\n"), "PARTIAL_EVENT_ROW")
            row = json.loads(raw)
            expected = json.dumps(row, ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
            require(raw == expected and row["sequence"] == len(rows),
                    "CANONICAL_EVENT_SEQUENCE")
            rows.append(row)
    return rows


def validate_events(events: list[dict], results: dict, state: dict) -> None:
    require(len(events) == 168, "EVENT_ROW_COUNT")
    counts = collections.Counter((event["variant"], event["event"]) for event in events)
    for method in METHODS:
        require(counts[(method, "cv_fit_started")] == 24
                and counts[(method, "cv_fit_completed")]
                + counts[(method, "cv_fit_failed")] == 24
                and counts[(method, "selected_base_fit_started")] == 1
                and counts[(method, "selected_base_fit_completed")] == 1
                and counts[(method, "platt_fit_started")] == 1
                and counts[(method, "platt_fit_completed")] == 1
                and counts[(method, "fixed_base_fit_started")] == 1
                and counts[(method, "fixed_base_fit_completed")] == 1
                and counts[(method, "fixed_platt_fit_started")] == 1
                and counts[(method, "fixed_platt_fit_completed")] == 1,
                "EVENT_METHOD_COUNTS")
        selected = results[method]["selected_candidate_id"]
        require(next(event for event in events
                     if event["variant"] == method
                     and event["event"] == "selected_base_fit_started")["candidate_id"]
                == selected, "EVENT_SELECTED_BINDING")
    expected = []; sequence = 0
    for method in METHODS:
        result = results[method]
        for candidate in result["candidates"]:
            for fold in candidate["folds"]:
                base = {key: fold[key] for key in (
                    "fold_index", "train_keys_sha256", "validation_keys_sha256",
                    "train_rows", "validation_rows",
                )}
                expected.append({
                    "sequence": sequence, "event": "cv_fit_started",
                    "variant": method, "candidate_id": candidate["candidate_id"],
                    **base, "parameters": candidate["parameters"],
                }); sequence += 1
                terminal = "cv_fit_completed" if fold["status"] == "PASS" else "cv_fit_failed"
                expected.append({
                    "sequence": sequence, "event": terminal,
                    "variant": method, "candidate_id": candidate["candidate_id"], **fold,
                }); sequence += 1
        expected.append({"sequence": sequence, "event": "selected_base_fit_started",
                         "variant": method,
                         "candidate_id": result["selected_candidate_id"]}); sequence += 1
        expected.append({"sequence": sequence, "event": "selected_base_fit_completed",
                         "variant": method,
                         "candidate_id": result["selected_candidate_id"]}); sequence += 1
        expected.append({"sequence": sequence, "event": "platt_fit_started",
                         "variant": method}); sequence += 1
        expected.append({"sequence": sequence, "event": "platt_fit_completed",
                         "variant": method}); sequence += 1
        fixed = result["fixed_reference_model"]["candidate_id"]
        expected.append({"sequence": sequence, "event": "fixed_base_fit_started",
                         "variant": method, "candidate_id": fixed}); sequence += 1
        expected.append({"sequence": sequence, "event": "fixed_base_fit_completed",
                         "variant": method, "candidate_id": fixed}); sequence += 1
        expected.append({"sequence": sequence, "event": "fixed_platt_fit_started",
                         "variant": method, "candidate_id": fixed}); sequence += 1
        expected.append({"sequence": sequence, "event": "fixed_platt_fit_completed",
                         "variant": method, "candidate_id": fixed}); sequence += 1
    compare(comparable(events), comparable(expected), state)


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
    namespace = root / "tuning"; validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "PASS_MISTRAL_DEVELOPMENT_TUNING_PENDING_INDEPENDENT"
            and receipt["scientific_fit_attempts"] == 84
            and receipt["development_rows_read"] == EXPECTED_TRACES
            and receipt["development_gold_metric_values_read"] == EXPECTED_TRACES * 4
            and receipt["test_rows_read"] == receipt["test_gold_values_read"]
            == receipt["neural_model_loads"] == receipt["model_forwards"] == 0
            and receipt["action_budget_tuned"] is False,
            "PRODUCER_RECEIPT")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"]
            and freeze["methods"] == list(METHODS)
            and freeze["variant_widths"] == WIDTHS
            and freeze["fold_prefix"] == FOLD_PREFIX
            and freeze["candidate_grid"] == list(grid())
            and freeze["base_fixed"] == BASE and freeze["platt_fixed"] == PLATT
            and freeze["expected_search_fit_attempts"] == 78
            and freeze["expected_fixed_reference_fit_attempts"] == 6
            and freeze["expected_fit_attempts"] == 84
            and freeze["test_access"] == "FORBIDDEN"
            and freeze["action_budget_tuning"] == "FORBIDDEN",
            "EXECUTABLE_FREEZE")
    require(Path(sys.executable).resolve() == Path(freeze["python"]).resolve()
            and sys.version == freeze["python_version"]
            and freeze["packages"] == {
                name: importlib.metadata.version(name) for name in
                ("numpy", "scipy", "scikit-learn", "threadpoolctl")
            }
            and freeze["threadpool_preflight"] == threadpool_info()
            and freeze["thread_limit"] == 1,
            "VALIDATION_ENVIRONMENT_IDENTITY")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_INPUT")
    prelabel = root / "prelabel"; outcomes_path = root / "development_outcomes"
    prelabel_validation = root / "prelabel_validation/VALIDATION.json"
    outcomes_validation = root / "development_outcomes_validation/VALIDATION.json"
    input_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(prelabel_validation.resolve() in input_paths
            and outcomes_validation.resolve() in input_paths,
            "FROZEN_ACCEPTANCE_INPUTS")
    validate_manifest(prelabel); validate_manifest(outcomes_path)
    prelabel_acceptance = json.loads(prelabel_validation.read_text(encoding="utf-8"))
    outcome_acceptance = json.loads(outcomes_validation.read_text(encoding="utf-8"))
    require(prelabel_acceptance["status"]
            == "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_PRELABEL_FREEZE"
            and prelabel_acceptance["producer_manifest_sha256"]
            == sha256(prelabel / "SHA256_MANIFEST.json")
            and prelabel_acceptance["producer_receipt_sha256"]
            == sha256(prelabel / "STAGE_RECEIPT.json")
            and prelabel_acceptance["prelabel_rows_sha256"]
            == sha256(prelabel / "PRELABEL_ROWS.jsonl")
            and outcome_acceptance["status"]
            == "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_OUTCOMES"
            and outcome_acceptance["producer_manifest_sha256"]
            == sha256(outcomes_path / "SHA256_MANIFEST.json")
            and outcome_acceptance["producer_receipt_sha256"]
            == sha256(outcomes_path / "STAGE_RECEIPT.json")
            and outcome_acceptance["development_outcomes_sha256"]
            == sha256(outcomes_path / "DEVELOPMENT_OUTCOMES.jsonl"),
            "PREDECESSOR_ACCEPTANCE")
    features, outcomes, parts = assemble_inputs(
        read_rows(prelabel / "PRELABEL_ROWS.jsonl"),
        read_rows(outcomes_path / "DEVELOPMENT_OUTCOMES.jsonl"),
    )
    saved = json.loads((namespace / "TUNING_RESULTS.json").read_text(encoding="utf-8"))
    require(set(saved) == set(METHODS), "TUNING_RESULT_METHODS")
    replayed = {}
    with threadpool_limits(limits=1):
        for method in METHODS:
            replayed[method] = replay_variant(features[method], outcomes, parts, method)
    state = {"maximum_numeric_error": 0.0, "numeric_checks": 0, "exact_checks": 0}
    compare(comparable(saved), comparable(replayed), state)
    events = read_canonical_events(namespace / "FIT_EVENTS.jsonl")
    validate_events(events, replayed, state)
    require(receipt["scientific_fit_completions"]
            == sum(saved[method]["successful_fits"] for method in METHODS)
            and receipt["fit_event_rows"] == len(events)
            and receipt["selected_candidates"]
            == {method: saved[method]["selected_candidate_id"] for method in METHODS},
            "RECEIPT_RESULT_COUNTS")
    for name, path in (("tuning_results", namespace / "TUNING_RESULTS.json"),
                       ("fit_events", namespace / "FIT_EVENTS.jsonl")):
        require(receipt[name] == {"path": str(path.resolve()),
                                  "size_bytes": path.stat().st_size,
                                  "sha256": sha256(path)},
                "RECEIPT_FILE_BINDING")
    require(all(name not in sys.modules for name in ("torch", "transformers")),
            "NEURAL_RUNTIME_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_TUNING",
        "cas_q3_status": "NOT READY",
        "producer_manifest_sha256": sha256(namespace / "SHA256_MANIFEST.json"),
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "tuning_results_sha256": sha256(namespace / "TUNING_RESULTS.json"),
        "fit_events_sha256": sha256(namespace / "FIT_EVENTS.jsonl"),
        "methods": list(METHODS), "scientific_fit_attempts_verified": 84,
        "scientific_fit_completions_verified": receipt["scientific_fit_completions"],
        "independent_audit_refit_attempts": sum(
            replayed[method]["fit_attempts"] for method in METHODS
        ),
        "independent_audit_refit_completions": sum(
            replayed[method]["successful_fits"] for method in METHODS
        ),
        "combined_producer_and_validator_fit_attempts": 168,
        "selected_candidates": receipt["selected_candidates"],
        "maximum_numeric_error": state["maximum_numeric_error"],
        "numeric_checks": state["numeric_checks"],
        "exact_checks": state["exact_checks"],
        "development_rows_read": EXPECTED_TRACES,
        "development_gold_metric_values_read": EXPECTED_TRACES * 4,
        "test_rows_read": 0, "test_gold_values_read": 0,
        "neural_model_loads": 0, "model_forwards": 0,
        "action_budget_tuned": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2,
                                  allow_nan=False).encode("utf-8") + b"\n")
    print(result["status"], state["maximum_numeric_error"], flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
