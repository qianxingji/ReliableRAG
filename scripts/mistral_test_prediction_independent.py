"""Independent pure-Python audit of Mistral test prediction and allocation.

This implementation imports neither ``reader_test_prediction`` nor a top-K
allocation helper. It is intended to validate a future sealed action ledger.
"""
from collections import Counter
import hashlib
import json
import math


DATASETS = ("2wikimultihopqa", "hotpotqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
METHOD_WIDTHS = {"HGB_GBV_R": 2, "HGB_ONLY_R": 1, "GBV_ONLY_R": 1}
PRIMARY_POLICIES = tuple(METHOD_WIDTHS)
FIXED_POLICIES = tuple(method + "_FIXED_C1" for method in PRIMARY_POLICIES)
SCORED_POLICIES = PRIMARY_POLICIES + FIXED_POLICIES
POLICIES = ("Keep",) + SCORED_POLICIES
PRELABEL_FIELDS = {
    "dataset", "retriever", "sample_id", "position", "role",
    "pair_eligible", "eligible", "forced_keep_reason", "hgb_score",
    "gbv_F0", "gbv_F1", "gbv_margin", "feature_vectors", "source_bindings",
}


def require(value, message):
    if not value:
        raise ValueError("Independent test prediction: " + message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def object_sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def logistic(value):
    require(finite(value), "finite logistic input")
    if value < 0:
        exponential = math.exp(value)
        result = exponential / (1.0 + exponential)
    else:
        result = 1.0 / (1.0 + math.exp(-value))
    require(math.isfinite(result) and 0 <= result <= 1, "bounded probability")
    return result


def model_record(tuning, method, field):
    require(type(tuning) is dict
            and tuning.get("role") == "DEVELOPMENT_ONLY_READER_HEAD_TUNING"
            and tuning.get("variant") == method
            and tuning.get("fit_attempts") == 28
            and tuning.get("test_labels_read") is False
            and tuning.get("test_predictions_emitted") is False
            and tuning.get("action_budget_tuned") is False,
            "development-only tuning record")
    record = tuning.get(field)
    width = METHOD_WIDTHS[method]
    require(type(record) is dict and type(record.get("preprocessing")) is dict
            and set(record["preprocessing"]) == {"median", "mean", "std"},
            "model and preprocessing record")
    preprocessing = {
        name: [float(value) for value in record["preprocessing"][name]]
        for name in ("median", "mean", "std")
    }
    require(all(len(preprocessing[name]) == width for name in preprocessing)
            and all(math.isfinite(value) for values in preprocessing.values()
                    for value in values)
            and all(value > 0 for value in preprocessing["std"]),
            "preprocessing dimensions and values")
    coefficients = [float(value) for value in record.get("coef", [])]
    require(len(coefficients) == 2 * width + len(RETRIEVERS)
            and all(math.isfinite(value) for value in coefficients),
            "coefficient dimensions and values")
    require(all(finite(record.get(name)) for name in
                ("intercept", "platt_slope", "platt_intercept")),
            "finite model scalars")
    require(type(record.get("fit_keys_sha256")) is str
            and len(record["fit_keys_sha256"]) == 64
            and type(record.get("cal_keys_sha256")) is str
            and len(record["cal_keys_sha256"]) == 64,
            "development role hashes")
    return {
        "preprocessing": preprocessing,
        "coef": coefficients,
        "intercept": float(record["intercept"]),
        "platt_slope": float(record["platt_slope"]),
        "platt_intercept": float(record["platt_intercept"]),
        "record_sha256": object_sha(record),
        "fit_keys_sha256": record["fit_keys_sha256"],
        "cal_keys_sha256": record["cal_keys_sha256"],
    }


def probability(vector, retriever, model, width):
    require(type(vector) is list and len(vector) == width,
            "exact feature vector width")
    values = []
    missing = []
    for index, value in enumerate(vector):
        require(value is None or finite(value), "finite or missing feature")
        is_missing = value is None
        missing.append(float(is_missing))
        numeric = model["preprocessing"]["median"][index] if is_missing else value
        values.append(
            (numeric - model["preprocessing"]["mean"][index])
            / model["preprocessing"]["std"][index]
        )
    design = values + missing + [float(retriever == name) for name in RETRIEVERS]
    require(all(math.isfinite(value) for value in design), "finite design")
    raw = math.fsum(value * coefficient
                    for value, coefficient in zip(design, model["coef"]))
    raw += model["intercept"]
    return logistic(model["platt_slope"] * raw + model["platt_intercept"])


def _independent_score_and_allocate(prelabel_rows, tuning_results, *,
                                    expected_traces, questions_per_dataset,
                                    action_cap):
    require(type(expected_traces) is int and expected_traces == 9 * questions_per_dataset
            and type(action_cap) is int and 0 <= action_cap <= expected_traces,
            "fixed population and cap")
    require(type(tuning_results) is dict
            and set(tuning_results) == set(PRIMARY_POLICIES),
            "exact three tuning methods")
    models = {}
    bindings = {}
    for method in PRIMARY_POLICIES:
        selected = model_record(tuning_results[method], method, "final_model")
        fixed = model_record(tuning_results[method], method,
                             "fixed_reference_model")
        require(selected["preprocessing"] == fixed["preprocessing"]
                and selected["fit_keys_sha256"] == fixed["fit_keys_sha256"]
                and selected["cal_keys_sha256"] == fixed["cal_keys_sha256"],
                "selected and fixed role/preprocessing equality")
        models[method] = selected
        models[method + "_FIXED_C1"] = fixed
        bindings[method] = {
            "selected_model_sha256": selected["record_sha256"],
            "fixed_reference_model_sha256": fixed["record_sha256"],
            "fit_keys_sha256": selected["fit_keys_sha256"],
            "cal_keys_sha256": selected["cal_keys_sha256"],
        }

    source = list(prelabel_rows)
    require(len(source) == expected_traces, "exact trace count")
    rows = []
    identities = set()
    cells = Counter()
    groups = Counter()
    for position, row in enumerate(source):
        require(type(row) is dict and set(row) == PRELABEL_FIELDS,
                "exact prelabel schema")
        require(row["position"] == position and row["role"] == "test"
                and row["dataset"] in DATASETS and row["retriever"] in RETRIEVERS
                and type(row["sample_id"]) is str and row["sample_id"],
                "canonical test identity")
        key = (row["dataset"], row["retriever"], row["sample_id"])
        require(key not in identities, "unique test identity")
        identities.add(key)
        cells[key[:2]] += 1
        groups[(key[0], key[2])] += 1
        require(type(row["pair_eligible"]) is bool
                and type(row["eligible"]) is bool
                and (not row["eligible"] or row["pair_eligible"]),
                "common eligibility")
        reason = row["forced_keep_reason"]
        require(reason is None if row["eligible"] else
                type(reason) is str and bool(reason), "forced-Keep reason")
        require(type(row["feature_vectors"]) is dict
                and set(row["feature_vectors"]) == set(PRIMARY_POLICIES),
                "feature vector methods")
        expected_vectors = {
            "HGB_GBV_R": [row["hgb_score"], row["gbv_margin"]],
            "HGB_ONLY_R": [row["hgb_score"]],
            "GBV_ONLY_R": [row["gbv_margin"]],
        }
        require(row["feature_vectors"] == expected_vectors,
                "feature and signal binding")
        require(type(row["source_bindings"]) is dict
                and set(row["source_bindings"])
                == {"hgb_signal_row_sha256", "gbv_row_sha256"}
                and all(type(value) is str and len(value) == 64
                        for value in row["source_bindings"].values()),
                "prelabel source bindings")
        scores = {}
        for policy in SCORED_POLICIES:
            method = policy[:-9] if policy.endswith("_FIXED_C1") else policy
            vector = row["feature_vectors"][method]
            require(type(vector) is list and len(vector) == METHOD_WIDTHS[method]
                    and all(value is None or finite(value) for value in vector),
                    "feature vector values")
            if row["eligible"]:
                require(all(finite(value) for value in vector),
                        "eligible complete feature vector")
            scores[policy] = (
                probability(vector, row["retriever"],
                            models[policy], METHOD_WIDTHS[method])
                if row["eligible"] else None
            )
        rows.append({
            "dataset": key[0],
            "retriever": key[1],
            "sample_id": key[2],
            "eligible": row["eligible"],
            "scores": scores,
            "actions": {policy: "KEEP" for policy in POLICIES},
            "forced_keep_reason": reason,
        })
    require(all(cells[(dataset, retriever)] == questions_per_dataset
                for dataset in DATASETS for retriever in RETRIEVERS),
            "balanced cells")
    require(len(groups) == 3 * questions_per_dataset
            and all(value == 3 for value in groups.values()),
            "three siblings per question")

    eligible = [index for index, row in enumerate(rows) if row["eligible"]]
    replacement_counts = {"Keep": 0}
    for policy in SCORED_POLICIES:
        ordered = sorted(eligible, key=lambda index: (
            -rows[index]["scores"][policy],
            rows[index]["dataset"], rows[index]["retriever"],
            rows[index]["sample_id"],
        ))
        chosen = ordered[:action_cap]
        replacement_counts[policy] = len(chosen)
        for index in chosen:
            rows[index]["actions"][policy] = "REPLACE"
    return {
        "schema_version": 1,
        "role": "LABEL_BLIND_MISTRAL_TEST_ACTION_SEAL",
        "N_all": expected_traces,
        "N_eligible": len(eligible),
        "action_cap": action_cap,
        "replacement_counts": replacement_counts,
        "model_bindings": bindings,
        "test_labels_read": False,
        "test_outcomes_read": False,
        "action_budget_tuned": False,
        "rows": rows,
    }


def independent_score_and_allocate(prelabel_rows, tuning_results):
    return _independent_score_and_allocate(
        prelabel_rows, tuning_results,
        expected_traces=18_000,
        questions_per_dataset=2_000,
        action_cap=900,
    )


def compare_seals(actual, expected, *, tolerance=1e-12):
    """Compare producer and independent seals; only probabilities use tolerance."""
    require(type(actual) is dict and set(actual) == set(expected),
            "complete seal schema")
    for name in expected:
        left = actual[name]
        right = expected[name]
        if name == "rows":
            require(len(left) == len(right), "row count")
            for producer, independent in zip(left, right):
                require(set(producer) == set(independent), "row schema")
                for field in independent:
                    if field == "scores":
                        require(set(producer[field]) == set(independent[field]),
                                "score policy schema")
                        for policy, value in independent[field].items():
                            observed = producer[field][policy]
                            if value is None:
                                require(observed is None, "null ineligible score")
                            else:
                                require(finite(observed)
                                        and abs(observed - value) <= tolerance,
                                        "independent probability tolerance")
                    else:
                        require(producer[field] == independent[field],
                                "exact row field")
        else:
            require(left == right, "exact seal metadata")
