"""Independent saved-head replay and whole-ledger actions; no executor import."""
import math
from collections import Counter

import numpy as np

from scripts.empirical_feature_independent import pair_eligibility, feature_pair, check_numeric_tree
from scripts.empirical_scoring_fixtures import direct_base, direct_v2, scalar_panel

POLICIES = ("Keep", "HGB", "GbV", "ROA-FULL", "ROA-NOGBV", "HGB_GBV_R", "HGB_ONLY_R", "GBV_ONLY_R", "V2")
NUMERIC = ("state_symmetric_hgb", "state_symmetric_logistic", "no_cross_state", "no_B", "no_evidence_change",
    "no_answer_form", "ordinary_compact_logistic", "B_rule", "higher_own_likelihood", "likelihood_margin")


def key(row):
    return row["dataset"], row["retriever"], row["sample_id"]


def require(value, message):
    if not value:
        raise ValueError(message)


def validate_policies(traces, base_records, gbv_records, allocation, models, ordinary_names, bundle, panel):
    """Checks all raw base features/scores, frozen heads, shared masks and actions.

    Neural witness validation is a separate required gate. HGB saved estimator
    predict_proba remains shared; this function is not independent tree traversal.
    """
    keys = [key(t) for t in traces]
    require(len(keys) == len(set(keys)) and len(keys) == len(base_records) == len(gbv_records), "Independent complete trace universe")
    require(set(panel) == set(POLICIES[3:8]), "Independent fixed five heads")
    require([key(t) for t in base_records] == [key(t) for t in gbv_records] == keys, "Independent source alignment")
    result = dict(numeric_checks=0, max_numeric_error=0., trace_count=len(keys))
    def compare(actual, expected):
        count, maximum = check_numeric_tree(actual, expected)
        result["numeric_checks"] += count
        result["max_numeric_error"] = max(result["max_numeric_error"], maximum)
    expected_scores = {name: {} for name in POLICIES[1:]}
    common, reasons, pairs, pairs_indices = [], {}, [], []
    for i, (trace, base, gbv) in enumerate(zip(traces, base_records, gbv_records, strict=True)):
        k = keys[i]
        native_eligible, native_reason = pair_eligibility(trace["a0"], trace["a1"])
        require(type(base["eligible"]) is bool and base["eligible"] == native_eligible and
            base["forced_keep_reason"] == native_reason, "Independent native eligibility")
        require(set(base["scores"]) == set(NUMERIC) and type(gbv["eligible"]) is bool, "Independent input schema")
        if native_eligible:
            expected_pair = feature_pair(trace, base["cells"])
            compare(base["pair"], expected_pair)
            pairs.append(expected_pair)
            pairs_indices.append(i)
        else:
            require(all(v is None for v in base["scores"].values()) and not gbv["eligible"] and
                gbv["forced_keep_reason"] == native_reason and all(gbv[f] is None for f in ("F0", "F1", "gbv_margin")), "Independent native null row")
        if native_eligible and gbv["eligible"]:
            require(gbv["forced_keep_reason"] is None and all(type(gbv[f]) in (int, float) and math.isfinite(gbv[f]) for f in ("F0", "F1", "gbv_margin")), "Independent finite GbV scores")
            require(0 <= gbv["F0"] <= 1 and 0 <= gbv["F1"] <= 1, "Independent GbV probability interval")
            # Margin is an exact subtraction of the observed FP32 branch maxima.
            require(gbv["gbv_margin"] == gbv["F1"] - gbv["F0"], "Independent exact GbV subtraction")
            common.append(i)
            reasons[k] = None
        else:
            reasons[k] = native_reason if not native_eligible else gbv["forced_keep_reason"]
            if native_eligible:
                reason = reasons[k]
                prefix = "nli_unscorable:"
                require(type(reason) is str and reason.startswith(prefix), "Independent documented NLI exclusion")
                message = reason[len(prefix):]
                words = message.split()
                hypothesis = message == "hypothesis does not fit the NLI context window"
                single_word = (len(words) == 12 and words[:4] == ["single-word", "premise", "at", "position"] and
                    words[4].isascii() and words[4].isdigit() and words[5:] == ["does", "not", "fit", "the", "NLI", "context", "window"])
                require(hypothesis or single_word, "Independent deterministic NLI reason")
            for name in expected_scores:
                expected_scores[name][k] = None
    if pairs:
        independently_scored = direct_base(models, pairs, ordinary_names)
        for j, i in enumerate(pairs_indices):
            compare(base_records[i]["scores"], {name: float(independently_scored[name][j]) for name in NUMERIC})
    detail_rows = allocation["policy_details"]
    require([key(row) for row in detail_rows] == [keys[i] for i in common], "Independent policy-detail coverage/order")
    if common:
        numeric = np.asarray([[base_records[i]["scores"][n] for n in NUMERIC] + [gbv_records[i]["gbv_margin"]] for i in common])
        v2_scores = direct_v2(bundle, numeric[:, :10])
        for j, i in enumerate(common):
            k, detail = keys[i], detail_rows[j]
            require(detail["numeric"] == numeric[j].tolist(), "Independent eleven-input binding")
            expected_scores["HGB"][k], expected_scores["GbV"][k] = float(numeric[j, 0]), float(numeric[j, 10])
            expected_scores["V2"][k] = float(v2_scores[j])
            compare(detail["V2"], float(v2_scores[j]))
            require(set(detail["panel"]) == set(panel), "Independent complete head detail")
            for name, model in panel.items():
                logit, probability = scalar_panel(model, k[1], numeric[j])
                compare(detail["panel"][name], dict(logit_R=logit, pR=probability))
                expected_scores[name][k] = probability
    ledger = allocation["ledger"]
    require([key(row) for row in ledger] == sorted(keys), "Independent all-row canonical action ledger")
    eligible_keys = {keys[i] for i in common}
    actual_scores = {name: {} for name in expected_scores}
    for row in ledger:
        k = key(row)
        require(type(row["eligible"]) is bool and row["eligible"] == (k in eligible_keys) and
            row["forced_keep_reason"] == reasons[k], "Independent common mask/reason")
        require(set(row["scores"]) == set(expected_scores) and set(row["actions"]) == set(POLICIES), "Independent exact policy names")
        compare(row["scores"], {p: expected_scores[p][k] for p in expected_scores})
        for name, value in row["scores"].items():
            actual_scores[name][k] = value
    # Actions must be exact on the actual frozen scores. Tiny valid replay errors
    # must not create a different expected tie break by perturbing those scores.
    cap = int(round(len(keys) / 20))
    memberships = {"Keep": set()}
    for name in expected_scores:
        ranked = sorted(eligible_keys)
        ranked.sort(key=lambda k: actual_scores[name][k], reverse=True)
        memberships[name] = set(ranked[:cap])
    for row in ledger:
        for name in POLICIES:
            require(row["actions"][name] == ("REPLACE" if key(row) in memberships[name] else "KEEP"), "Independent exact budget/action membership")
    counts = {name: len(values) for name, values in memberships.items()}
    require(allocation["N_all"] == len(keys) and allocation["N_eligible"] == len(common) and allocation["cap"] == cap,
        "Independent all-row budget denominator")
    require(allocation["replacement_counts"] == counts and allocation["selected"] == memberships, "Independent replacement accounting")
    forced = dict(Counter(value for value in reasons.values() if value is not None))
    require(allocation["forced_keep_counts"] == forced, "Independent complete reason counts")
    result.update(status="PASS_INDEPENDENT_DOWNSTREAM_POLICY_ARITHMETIC", eligible_count=len(common), cap=cap,
        replacement_counts=counts, limitation="Neural witness validation required separately; HGB estimator probabilities remain a shared dependency.")
    return result
