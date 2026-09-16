"""Label-blind reader-head prediction and fixed global action allocation.

The public entry point is fixed to the 18,000-row Mistral test population and
K=900. It consumes only accepted prelabel features and frozen development model
records; no outcome or reference field is accepted.
"""
from collections import Counter
import hashlib
import json
import math

import numpy as np

from src.arbitration.empirical_contract import DATASETS, RETRIEVERS


METHOD_WIDTHS = {"HGB_GBV_R": 2, "HGB_ONLY_R": 1, "GBV_ONLY_R": 1}
PRIMARY_POLICIES = tuple(METHOD_WIDTHS)
FIXED_POLICIES = tuple(method + "_FIXED_C1" for method in PRIMARY_POLICIES)
SCORED_POLICIES = PRIMARY_POLICIES + FIXED_POLICIES
POLICIES = ("Keep",) + SCORED_POLICIES
EXPECTED_TRACES = 18_000
EXPECTED_QUESTIONS_PER_DATASET = 2_000
ACTION_CAP = 900
PRELABEL_FIELDS = frozenset({
    "dataset", "retriever", "sample_id", "position", "role",
    "pair_eligible", "eligible", "forced_keep_reason", "hgb_score",
    "gbv_F0", "gbv_F1", "gbv_margin", "feature_vectors", "source_bindings",
})


class TestPredictionContractError(RuntimeError):
    """Raised when a label-blind test prediction contract is violated."""


def require(condition, message):
    if not condition:
        raise TestPredictionContractError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def object_sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sigmoid(value):
    require(finite(value), "NONFINITE_LOGIT")
    if value >= 0:
        probability = 1.0 / (1.0 + math.exp(-value))
    else:
        exponential = math.exp(value)
        probability = exponential / (1.0 + exponential)
    require(math.isfinite(probability) and 0.0 <= probability <= 1.0,
            "INVALID_PROBABILITY")
    return probability


def _validated_model(tuning, method, field):
    width = METHOD_WIDTHS[method]
    require(type(tuning) is dict and tuning.get("role")
            == "DEVELOPMENT_ONLY_READER_HEAD_TUNING"
            and tuning.get("variant") == method
            and tuning.get("fit_attempts") == 28
            and tuning.get("test_labels_read") is False
            and tuning.get("test_predictions_emitted") is False
            and tuning.get("action_budget_tuned") is False,
            "DEVELOPMENT_TUNING_BINDING")
    model = tuning.get(field)
    require(type(model) is dict, "MODEL_RECORD")
    preprocessing = model.get("preprocessing")
    require(type(preprocessing) is dict and set(preprocessing)
            == {"median", "mean", "std"}, "PREPROCESSING_SCHEMA")
    median = np.asarray(preprocessing["median"], dtype=np.float64)
    mean = np.asarray(preprocessing["mean"], dtype=np.float64)
    std = np.asarray(preprocessing["std"], dtype=np.float64)
    require(median.shape == mean.shape == std.shape == (width,)
            and np.isfinite(median).all() and np.isfinite(mean).all()
            and np.isfinite(std).all() and np.all(std > 0),
            "PREPROCESSING_VALUES")
    coefficient = np.asarray(model.get("coef"), dtype=np.float64)
    require(coefficient.shape == (2 * width + len(RETRIEVERS),)
            and np.isfinite(coefficient).all(), "COEFFICIENT_VALUES")
    for name in ("intercept", "platt_slope", "platt_intercept"):
        require(finite(model.get(name)), "MODEL_SCALAR")
    require(type(model.get("fit_keys_sha256")) is str
            and len(model["fit_keys_sha256"]) == 64
            and type(model.get("cal_keys_sha256")) is str
            and len(model["cal_keys_sha256"]) == 64,
            "MODEL_ROLE_HASHES")
    return {
        "preprocessing": {
            "median": median,
            "mean": mean,
            "std": std,
        },
        "coef": coefficient,
        "intercept": float(model["intercept"]),
        "platt_slope": float(model["platt_slope"]),
        "platt_intercept": float(model["platt_intercept"]),
        "record_sha256": object_sha(model),
        "fit_keys_sha256": model["fit_keys_sha256"],
        "cal_keys_sha256": model["cal_keys_sha256"],
    }


def _design(vector, retriever, model, width):
    require(type(vector) is list and len(vector) == width,
            "FEATURE_VECTOR_WIDTH")
    numeric = np.asarray([
        np.nan if value is None else value for value in vector
    ], dtype=np.float64)
    require(np.logical_or(np.isfinite(numeric), np.isnan(numeric)).all(),
            "INVALID_FEATURE_VALUE")
    missing = ~np.isfinite(numeric)
    preprocessing = model["preprocessing"]
    filled = np.where(missing, preprocessing["median"], numeric)
    scaled = (filled - preprocessing["mean"]) / preprocessing["std"]
    retrievers = np.asarray([
        float(retriever == name) for name in RETRIEVERS
    ], dtype=np.float64)
    design = np.concatenate((scaled, missing.astype(np.float64), retrievers))
    require(np.isfinite(design).all(), "NONFINITE_TEST_DESIGN")
    return design


def _probability(vector, retriever, model, width):
    design = _design(vector, retriever, model, width)
    raw = float(design @ model["coef"] + model["intercept"])
    calibrated = model["platt_slope"] * raw + model["platt_intercept"]
    return sigmoid(calibrated)


def _score_and_allocate(prelabel_rows, tuning_results, *, expected_traces,
                        questions_per_dataset, action_cap):
    require(type(expected_traces) is int and expected_traces == 9 * questions_per_dataset
            and type(action_cap) is int and 0 <= action_cap <= expected_traces,
            "FIXED_POPULATION_AND_CAP")
    require(type(tuning_results) is dict
            and set(tuning_results) == set(PRIMARY_POLICIES),
            "EXACT_TUNING_METHODS")
    models = {}
    bindings = {}
    for method in PRIMARY_POLICIES:
        selected = _validated_model(tuning_results[method], method, "final_model")
        fixed = _validated_model(
            tuning_results[method], method, "fixed_reference_model"
        )
        require(all(np.array_equal(
            selected["preprocessing"][name], fixed["preprocessing"][name]
        ) for name in ("median", "mean", "std"))
                and selected["fit_keys_sha256"] == fixed["fit_keys_sha256"]
                and selected["cal_keys_sha256"] == fixed["cal_keys_sha256"],
                "SELECTED_FIXED_ROLE_AND_PREPROCESSING_MATCH")
        models[method] = selected
        models[method + "_FIXED_C1"] = fixed
        bindings[method] = {
            "selected_model_sha256": selected["record_sha256"],
            "fixed_reference_model_sha256": fixed["record_sha256"],
            "fit_keys_sha256": selected["fit_keys_sha256"],
            "cal_keys_sha256": selected["cal_keys_sha256"],
        }

    rows = list(prelabel_rows)
    require(len(rows) == expected_traces, "TEST_TRACE_COUNT")
    prepared = []
    identities = set()
    counts = Counter()
    groups = Counter()
    for position, row in enumerate(rows):
        require(type(row) is dict and set(row) == PRELABEL_FIELDS,
                "PRELABEL_SCHEMA")
        require(row["position"] == position and row["role"] == "test"
                and row["dataset"] in DATASETS and row["retriever"] in RETRIEVERS
                and type(row["sample_id"]) is str and row["sample_id"],
                "TEST_IDENTITY")
        identity = (row["dataset"], row["retriever"], row["sample_id"])
        require(identity not in identities, "UNIQUE_TEST_IDENTITY")
        identities.add(identity)
        counts[(row["dataset"], row["retriever"])] += 1
        groups[(row["dataset"], row["sample_id"])] += 1
        require(type(row["pair_eligible"]) is bool
                and type(row["eligible"]) is bool
                and (not row["eligible"] or row["pair_eligible"]),
                "COMMON_ELIGIBILITY")
        reason = row["forced_keep_reason"]
        require(reason is None if row["eligible"] else
                type(reason) is str and bool(reason), "FORCED_KEEP_REASON")
        require(type(row["feature_vectors"]) is dict
                and set(row["feature_vectors"]) == set(PRIMARY_POLICIES),
                "FEATURE_METHODS")
        expected_vectors = {
            "HGB_GBV_R": [row["hgb_score"], row["gbv_margin"]],
            "HGB_ONLY_R": [row["hgb_score"]],
            "GBV_ONLY_R": [row["gbv_margin"]],
        }
        require(row["feature_vectors"] == expected_vectors,
                "FEATURE_SIGNAL_BINDING")
        require(type(row["source_bindings"]) is dict
                and set(row["source_bindings"])
                == {"hgb_signal_row_sha256", "gbv_row_sha256"}
                and all(type(value) is str and len(value) == 64
                        for value in row["source_bindings"].values()),
                "PRELABEL_SOURCE_BINDINGS")
        scores = {}
        for policy in SCORED_POLICIES:
            method = policy.removesuffix("_FIXED_C1")
            vector = row["feature_vectors"][method]
            require(type(vector) is list and len(vector) == METHOD_WIDTHS[method]
                    and all(value is None or finite(value) for value in vector),
                    "FEATURE_VECTOR_VALUES")
            if row["eligible"]:
                require(all(finite(value) for value in vector),
                        "ELIGIBLE_COMPLETE_FEATURE_VECTOR")
                scores[policy] = _probability(
                    vector, row["retriever"], models[policy], METHOD_WIDTHS[method]
                )
            else:
                scores[policy] = None
        prepared.append({
            "dataset": row["dataset"],
            "retriever": row["retriever"],
            "sample_id": row["sample_id"],
            "eligible": row["eligible"],
            "scores": scores,
            "actions": {policy: "KEEP" for policy in POLICIES},
            "forced_keep_reason": reason,
        })
    require(all(counts[(dataset, retriever)] == questions_per_dataset
                for dataset in DATASETS for retriever in RETRIEVERS),
            "BALANCED_TEST_CELLS")
    require(len(groups) == 3 * questions_per_dataset
            and all(value == 3 for value in groups.values()),
            "TEST_QUESTION_SIBLINGS")

    eligible_indices = [index for index, row in enumerate(prepared)
                        if row["eligible"]]
    selected_indices = {}
    for policy in SCORED_POLICIES:
        order = sorted(eligible_indices, key=lambda index: (
            -prepared[index]["scores"][policy],
            prepared[index]["dataset"],
            prepared[index]["retriever"],
            prepared[index]["sample_id"],
        ))
        chosen = order[:action_cap]
        selected_indices[policy] = chosen
        for index in chosen:
            prepared[index]["actions"][policy] = "REPLACE"
    return {
        "schema_version": 1,
        "role": "LABEL_BLIND_MISTRAL_TEST_ACTION_SEAL",
        "N_all": expected_traces,
        "N_eligible": len(eligible_indices),
        "action_cap": action_cap,
        "replacement_counts": {
            "Keep": 0,
            **{policy: len(selected_indices[policy]) for policy in SCORED_POLICIES},
        },
        "model_bindings": bindings,
        "test_labels_read": False,
        "test_outcomes_read": False,
        "action_budget_tuned": False,
        "rows": prepared,
    }


def score_and_allocate(prelabel_rows, tuning_results):
    """Score the exact frozen Mistral test population and allocate K=900."""
    return _score_and_allocate(
        prelabel_rows,
        tuning_results,
        expected_traces=EXPECTED_TRACES,
        questions_per_dataset=EXPECTED_QUESTIONS_PER_DATASET,
        action_cap=ACTION_CAP,
    )
