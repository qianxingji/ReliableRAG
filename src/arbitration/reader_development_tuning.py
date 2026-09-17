"""Prospective, development-only tuning for the additional reader condition.

The module accepts the existing fit/calibration roles only. It cannot score a
test partition and does not select an action budget. Three policies must invoke
the same grid through the future bound execution controller.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import hashlib
import json
import math
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from src.arbitration.empirical_contract import DATASETS, RETRIEVERS


Key = tuple[str, str, str]
FOLD_PREFIX = "cas-q3-reader-tuning-fold-v1|20260917"
VARIANT_WIDTHS = {"HGB_GBV_R": 2, "HGB_ONLY_R": 1, "GBV_ONLY_R": 1}
C_TIE_ORDER = (1.0, 0.1, 10.0, 0.01)
C_SEARCH_VALUES = (0.01, 0.1, 1.0, 10.0)
BASE_FIXED = {
    "solver": "lbfgs",
    "max_iter": 5000,
    "penalty": "l2",
    "tol": 1e-4,
    "fit_intercept": True,
    "random_state": None,
}
PLATT_FIXED = {
    **BASE_FIXED,
    "C": 1e6,
    "class_weight": None,
    "max_iter": 2000,
}


class TuningContractError(RuntimeError):
    """Raised when the development-only tuning contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TuningContractError(message)


def key_hash(keys: Iterable[Key]) -> str:
    payload = "".join(
        json.dumps(list(key), ensure_ascii=False, separators=(",", ":")) + "\n"
        for key in sorted(keys)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def candidate_grid() -> tuple[dict, ...]:
    """Return the fixed eight candidates; order is not the tie-break order."""
    return tuple(
        {**BASE_FIXED, "C": c_value, "class_weight": class_weight}
        for c_value in C_SEARCH_VALUES
        for class_weight in (None, "balanced")
    )


def candidate_id(parameters: Mapping) -> str:
    weight = "none" if parameters["class_weight"] is None else "balanced"
    return f"C={parameters['C']:g}|class_weight={weight}"


def candidate_tie_rank(parameters: Mapping) -> tuple[int, int]:
    """Prefer no class weighting, then the prospectively fixed C order."""
    return (
        0 if parameters["class_weight"] is None else 1,
        C_TIE_ORDER.index(float(parameters["C"])),
    )


def development_folds(fit_keys: Iterable[Key]) -> tuple[dict[str, set[Key]], ...]:
    """Create three exact, deterministic, dataset-stratified group folds."""
    keys = set(fit_keys)
    groups = {(dataset, sample_id) for dataset, _, sample_id in keys}
    _require(len(keys) == 10800, "FIT_TRACE_COUNT")
    _require(len(groups) == 3600, "FIT_QUESTION_COUNT")
    _require({key[0] for key in keys} == set(DATASETS), "FIT_DATASET_IDENTITIES")
    for dataset, sample_id in groups:
        siblings = {(dataset, retriever, sample_id) for retriever in RETRIEVERS}
        _require(siblings <= keys, "FIT_RETRIEVAL_SIBLINGS")
    fold_groups: list[set[tuple[str, str]]] = [set(), set(), set()]
    for dataset in DATASETS:
        dataset_groups = sorted(
            (group for group in groups if group[0] == dataset),
            key=lambda group: (
                hashlib.sha256(
                    f"{FOLD_PREFIX}|{group[0]}|{group[1]}".encode("utf-8")
                ).hexdigest(),
                group[1],
            ),
        )
        _require(len(dataset_groups) == 1200, "FIT_DATASET_QUESTION_COUNT")
        for index, group in enumerate(dataset_groups):
            fold_groups[index % 3].add(group)
    folds = []
    for fold_index, validation_groups in enumerate(fold_groups):
        validation = {
            key for key in keys if (key[0], key[2]) in validation_groups
        }
        training = keys - validation
        _require(len(validation) == 3600, "VALIDATION_TRACE_COUNT")
        _require(len(training) == 7200, "TRAINING_TRACE_COUNT")
        _require(
            len({(key[0], key[2]) for key in validation}) == 1200,
            "VALIDATION_QUESTION_COUNT",
        )
        for dataset in DATASETS:
            _require(
                sum(group[0] == dataset for group in validation_groups) == 400,
                "VALIDATION_DATASET_BALANCE",
            )
        folds.append(
            {
                "fold_index": fold_index,
                "train": training,
                "validation": validation,
            }
        )
    _require(set.union(*(fold["validation"] for fold in folds)) == keys, "FOLD_COVERAGE")
    _require(
        sum(len(folds[i]["validation"] & folds[j]["validation"])
            for i in range(3) for j in range(i)) == 0,
        "FOLD_OVERLAP",
    )
    return tuple(folds)


def _target(outcome: Mapping) -> int:
    a0_em, a1_em = outcome["a0_em"], outcome["a1_em"]
    _require(a0_em in (0, 1) and a1_em in (0, 1), "NONBINARY_EM")
    return int(a0_em == 0 and a1_em == 1)


def _numeric(rows: Mapping[Key, Mapping], keys: list[Key], width: int) -> np.ndarray:
    values = []
    for key in keys:
        numeric = rows[key]["numeric"]
        _require(len(numeric) == width, "FEATURE_WIDTH")
        values.append([np.nan if value is None else value for value in numeric])
    return np.asarray(values, dtype=np.float64)


def _fit_transform(
    rows: Mapping[Key, Mapping],
    train_keys: list[Key],
    apply_keys: list[Key],
    width: int,
) -> tuple[np.ndarray, np.ndarray, dict]:
    train = _numeric(rows, train_keys, width)
    apply = _numeric(rows, apply_keys, width)
    _require(np.isfinite(train).any(axis=0).all(), "ALL_MISSING_TRAIN_COLUMN")
    median = np.nanmedian(np.where(np.isfinite(train), train, np.nan), axis=0)
    filled = np.where(np.isfinite(train), train, median)
    mean = filled.mean(axis=0)
    std = filled.std(axis=0, ddof=0)
    std = np.where(std == 0, 1, std)

    def transform(values: np.ndarray, keys: list[Key]) -> np.ndarray:
        missing = ~np.isfinite(values)
        scaled = (np.where(missing, median, values) - mean) / std
        retrievers = np.asarray(
            [[float(key[1] == retriever) for retriever in RETRIEVERS] for key in keys],
            dtype=np.float64,
        )
        result = np.concatenate((scaled, missing.astype(np.float64), retrievers), axis=1)
        _require(np.isfinite(result).all(), "NONFINITE_DESIGN")
        return result

    preprocessing = {
        "median": median.tolist(),
        "mean": mean.tolist(),
        "std": std.tolist(),
    }
    return transform(train, train_keys), transform(apply, apply_keys), preprocessing


def _fit_logistic(
    values: np.ndarray,
    labels: np.ndarray,
    parameters: Mapping,
) -> LogisticRegression:
    _require(set(labels.tolist()) == {0, 1}, "MISSING_TRAIN_CLASS")
    model = LogisticRegression(**dict(parameters))
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        model.fit(values, labels)
    _require(
        not any(issubclass(item.category, ConvergenceWarning) for item in captured),
        "FIT_NONCONVERGENCE",
    )
    _require(
        np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all(),
        "NONFINITE_COEFFICIENTS",
    )
    return model


def _pooled_log_loss(raw_logits: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    losses = np.logaddexp(0.0, raw_logits) - labels * raw_logits
    _require(np.isfinite(losses).all(), "NONFINITE_LOG_LOSS")
    total = math.fsum(float(value) for value in losses)
    return total, total / len(losses)


def tune_recovery_head(
    rows: Mapping[Key, Mapping],
    development_outcomes: Mapping[Key, Mapping],
    parts: Mapping[str, set[Key]],
    variant: str,
    event: Callable[[dict], None] | None = None,
) -> dict:
    """Tune one recovery head, then refit and calibrate without test access."""
    _require(variant in VARIANT_WIDTHS, "UNAUTHORIZED_VARIANT")
    _require(set(parts) == {"fit", "cal"}, "DEVELOPMENT_ROLES_ONLY")
    fit_keys, cal_keys = set(parts["fit"]), set(parts["cal"])
    _require(fit_keys.isdisjoint(cal_keys), "FIT_CAL_OVERLAP")
    _require(len(fit_keys) == 10800 and len(cal_keys) == 2700, "DEVELOPMENT_ROLE_SIZE")
    _require(set(development_outcomes) == fit_keys | cal_keys, "OUTCOME_SCOPE")
    _require(set(rows) == fit_keys | cal_keys, "FEATURE_SCOPE")
    width = VARIANT_WIDTHS[variant]
    _require(all(len(row["numeric"]) == width for row in rows.values()), "FEATURE_WIDTH")
    folds = development_folds(fit_keys)
    emitted = event if event is not None else lambda _: None
    results = []
    fit_attempts = 0
    successful_fits = 0

    for parameters in candidate_grid():
        identifier = candidate_id(parameters)
        record = {
            "candidate_id": identifier,
            "parameters": dict(parameters),
            "valid": True,
            "folds": [],
        }
        pooled_loss_sum = 0.0
        pooled_rows = 0
        for fold in folds:
            train_keys = sorted(key for key in fold["train"] if rows[key]["eligible"])
            validation_keys = sorted(
                key for key in fold["validation"] if rows[key]["eligible"]
            )
            fold_record = {
                "fold_index": fold["fold_index"],
                "train_keys_sha256": key_hash(train_keys),
                "validation_keys_sha256": key_hash(validation_keys),
                "train_rows": len(train_keys),
                "validation_rows": len(validation_keys),
            }
            fit_attempts += 1
            emitted({
                "event": "cv_fit_started",
                "variant": variant,
                "candidate_id": identifier,
                **fold_record,
                "parameters": dict(parameters),
            })
            try:
                _require(train_keys and validation_keys, "EMPTY_ELIGIBLE_FOLD")
                x_train, x_validation, preprocessing = _fit_transform(
                    rows, train_keys, validation_keys, width
                )
                y_train = np.asarray(
                    [_target(development_outcomes[key]) for key in train_keys], dtype=np.int64
                )
                y_validation = np.asarray(
                    [_target(development_outcomes[key]) for key in validation_keys],
                    dtype=np.int64,
                )
                model = _fit_logistic(x_train, y_train, parameters)
                raw = x_validation @ model.coef_[0] + model.intercept_[0]
                loss_sum, loss_mean = _pooled_log_loss(raw, y_validation)
                successful_fits += 1
                fold_record.update({
                    "status": "PASS",
                    "train_class_counts": np.bincount(y_train, minlength=2).tolist(),
                    "validation_class_counts": np.bincount(
                        y_validation, minlength=2
                    ).tolist(),
                    "validation_log_loss_sum": loss_sum,
                    "validation_log_loss": loss_mean,
                    "preprocessing": preprocessing,
                    "coef": model.coef_[0].tolist(),
                    "intercept": float(model.intercept_[0]),
                    "iterations": model.n_iter_.tolist(),
                })
                pooled_loss_sum += loss_sum
                pooled_rows += len(y_validation)
                emitted({"event": "cv_fit_completed", "variant": variant,
                         "candidate_id": identifier, **fold_record})
            except (TuningContractError, ValueError, FloatingPointError) as exc:
                fold_record.update({
                    "status": "FAIL",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
                record["valid"] = False
                emitted({"event": "cv_fit_failed", "variant": variant,
                         "candidate_id": identifier, **fold_record})
            record["folds"].append(fold_record)
        if record["valid"]:
            _require(pooled_rows > 0, "EMPTY_POOLED_VALIDATION")
            record.update({
                "pooled_validation_rows": pooled_rows,
                "pooled_log_loss_sum": pooled_loss_sum,
                "pooled_log_loss": pooled_loss_sum / pooled_rows,
            })
        results.append(record)

    valid = [record for record in results if record["valid"]]
    _require(valid, "ALL_CANDIDATES_INVALID")
    selected = min(
        valid,
        key=lambda record: (
            record["pooled_log_loss"],
            candidate_tie_rank(record["parameters"]),
        ),
    )

    eligible_fit = sorted(key for key in fit_keys if rows[key]["eligible"])
    eligible_cal = sorted(key for key in cal_keys if rows[key]["eligible"])
    _require(eligible_fit and eligible_cal, "EMPTY_FINAL_ROLE")
    x_fit, x_cal, preprocessing = _fit_transform(
        rows, eligible_fit, eligible_cal, width
    )
    y_fit = np.asarray(
        [_target(development_outcomes[key]) for key in eligible_fit], dtype=np.int64
    )
    y_cal = np.asarray(
        [_target(development_outcomes[key]) for key in eligible_cal], dtype=np.int64
    )
    emitted({"event": "selected_base_fit_started", "variant": variant,
             "candidate_id": selected["candidate_id"]})
    fit_attempts += 1
    base = _fit_logistic(x_fit, y_fit, selected["parameters"])
    successful_fits += 1
    emitted({"event": "selected_base_fit_completed", "variant": variant,
             "candidate_id": selected["candidate_id"]})
    calibration_logits = x_cal @ base.coef_[0] + base.intercept_[0]
    emitted({"event": "platt_fit_started", "variant": variant})
    fit_attempts += 1
    platt = _fit_logistic(calibration_logits.reshape(-1, 1), y_cal, PLATT_FIXED)
    successful_fits += 1
    emitted({"event": "platt_fit_completed", "variant": variant})

    fixed_parameters = {**BASE_FIXED, "C": 1.0, "class_weight": None}
    fixed_identifier = candidate_id(fixed_parameters)
    emitted({"event": "fixed_base_fit_started", "variant": variant,
             "candidate_id": fixed_identifier})
    fit_attempts += 1
    fixed_base = _fit_logistic(x_fit, y_fit, fixed_parameters)
    successful_fits += 1
    emitted({"event": "fixed_base_fit_completed", "variant": variant,
             "candidate_id": fixed_identifier})
    fixed_calibration_logits = x_cal @ fixed_base.coef_[0] + fixed_base.intercept_[0]
    emitted({"event": "fixed_platt_fit_started", "variant": variant,
             "candidate_id": fixed_identifier})
    fit_attempts += 1
    fixed_platt = _fit_logistic(
        fixed_calibration_logits.reshape(-1, 1), y_cal, PLATT_FIXED
    )
    successful_fits += 1
    emitted({"event": "fixed_platt_fit_completed", "variant": variant,
             "candidate_id": fixed_identifier})

    return {
        "schema_version": 1,
        "role": "DEVELOPMENT_ONLY_READER_HEAD_TUNING",
        "variant": variant,
        "fold_prefix": FOLD_PREFIX,
        "folds": [
            {
                "fold_index": fold["fold_index"],
                "train_keys_sha256": key_hash(fold["train"]),
                "validation_keys_sha256": key_hash(fold["validation"]),
                "train_traces": len(fold["train"]),
                "validation_traces": len(fold["validation"]),
            }
            for fold in folds
        ],
        "candidates": results,
        "selected_candidate_id": selected["candidate_id"],
        "selected_parameters": selected["parameters"],
        "selection_metric": "pooled_eligible_validation_binary_log_loss",
        "selection_value": selected["pooled_log_loss"],
        "fit_attempts": fit_attempts,
        "successful_fits": successful_fits,
        "final_model": {
            "fit_keys_sha256": key_hash(eligible_fit),
            "cal_keys_sha256": key_hash(eligible_cal),
            "fit_rows": len(eligible_fit),
            "cal_rows": len(eligible_cal),
            "fit_class_counts": np.bincount(y_fit, minlength=2).tolist(),
            "cal_class_counts": np.bincount(y_cal, minlength=2).tolist(),
            "preprocessing": preprocessing,
            "coef": base.coef_[0].tolist(),
            "intercept": float(base.intercept_[0]),
            "base_iterations": base.n_iter_.tolist(),
            "platt_parameters": PLATT_FIXED,
            "platt_slope": float(platt.coef_[0, 0]),
            "platt_intercept": float(platt.intercept_[0]),
            "platt_iterations": platt.n_iter_.tolist(),
        },
        "fixed_reference_model": {
            "candidate_id": fixed_identifier,
            "parameters": fixed_parameters,
            "fit_keys_sha256": key_hash(eligible_fit),
            "cal_keys_sha256": key_hash(eligible_cal),
            "fit_rows": len(eligible_fit),
            "cal_rows": len(eligible_cal),
            "fit_class_counts": np.bincount(y_fit, minlength=2).tolist(),
            "cal_class_counts": np.bincount(y_cal, minlength=2).tolist(),
            "preprocessing": preprocessing,
            "coef": fixed_base.coef_[0].tolist(),
            "intercept": float(fixed_base.intercept_[0]),
            "base_iterations": fixed_base.n_iter_.tolist(),
            "platt_parameters": PLATT_FIXED,
            "platt_slope": float(fixed_platt.coef_[0, 0]),
            "platt_intercept": float(fixed_platt.intercept_[0]),
            "platt_iterations": fixed_platt.n_iter_.tolist(),
        },
        "test_labels_read": False,
        "test_predictions_emitted": False,
        "action_budget_tuned": False,
    }
