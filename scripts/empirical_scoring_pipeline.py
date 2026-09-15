"""Original fixed scoring calls and explicit shared eligibility reconciliation."""
from dataclasses import asdict
import math
import re

import numpy as np

from scripts.empirical_policy_actions import SCORED_POLICIES, allocate
from scripts.empirical_scoring_io import FIELDS, panel_scores
from scripts.empirical_runtime_contract import trace_key

CELLS = ("L00", "L01", "L10", "L11")
BASE_FEATURES = ("state_symmetric_hgb", "state_symmetric_logistic", "no_cross_state", "no_B",
    "no_evidence_change", "no_answer_form", "ordinary_compact_logistic", "B_rule",
    "higher_own_likelihood", "likelihood_margin")


def require(value, message):
    if not value:
        raise RuntimeError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def identity(trace):
    return {k: trace[k] for k in ("dataset", "retriever", "sample_id")}


def score_likelihood_trace(wrapper, native, models, eligibility, trace, witness):
    """No fallback, retry, altered native feature body or suppressed exception."""
    require(finite(trace.get("answer_semantic_agreement")), "Semantic acquisition precedes eligibility")
    decision = eligibility.assess_pair_eligibility(trace["a0"], trace["a1"])
    record = dict(**identity(trace), eligible=decision.eligible, forced_keep_reason=decision.reason,
        scores={name: None for name in BASE_FEATURES}, cells=None, pair=None, requests=[], forward_witnesses=[])
    if not decision.eligible:
        return record
    results, requests, forwards = witness.score(native.ordinary._score_items(trace))
    require(len(results) == len(requests) == 4, "Four native likelihood cells per eligible pair")
    cells = {name: asdict(result) for name, result in zip(CELLS, results, strict=True)}
    pair = native.symmetric.build_pair_record(trace, cells, schema_version="mars-state-symmetric-v1")
    scores = wrapper.base_scores(native, models, pair)
    require(set(scores) == set(BASE_FEATURES) and all(finite(v) for v in scores.values()), "Finite original ten-score record")
    record.update(scores=scores, cells=cells, pair=pair, requests=requests, forward_witnesses=forwards)
    return record


def deterministic_nli_error(message):
    return message == "hypothesis does not fit the NLI context window" or bool(re.fullmatch(
        r"single-word premise at position [0-9]+ does not fit the NLI context window", message))


def score_gbv_trace(eligibility, trace, witness):
    """Original branch order, including retained work before deterministic failure."""
    decision = eligibility.assess_pair_eligibility(trace["a0"], trace["a1"])
    record = dict(**identity(trace), eligible=decision.eligible, forced_keep_reason=decision.reason,
        F0=None, F1=None, gbv_margin=None, completed_branches=[], failed_branch=None,
        attempted_branches=0, forward_calls=0)
    if not decision.eligible:
        return record
    before = witness.forward_count
    for state, answer, evidence in (("F0", "a0", "E0"), ("F1", "a1", "E1")):
        branch_before = witness.forward_count
        record["attempted_branches"] += 1
        try:
            result, observed = witness.score_branch(trace["question"], trace[answer], [r["text"] for r in trace[evidence]])
        except ValueError as exc:
            if not deterministic_nli_error(str(exc)) or witness.forward_count != branch_before:
                raise
            record.update(eligible=False, forced_keep_reason="nli_unscorable:" + str(exc), failed_branch=state,
                forward_calls=witness.forward_count - before)
            return record
        require(finite(result.score) and 0 <= result.score <= 1, "Finite native GbV branch probability")
        record["completed_branches"].append(dict(state=state, result=asdict(result), witness=observed))
        record[state] = result.score
    record.update(gbv_margin=record["F1"] - record["F0"], forward_calls=witness.forward_count - before)
    return record


def common_policy_ledger(traces, base_records, gbv_records, eligibility, v2, bundle, panel):
    """Caller seals original records separately; this function never edits them."""
    require(len(traces) == len(base_records) == len(gbv_records), "Complete aligned policy inputs")
    keys = [trace_key(t) for t in traces]
    require(len(keys) == len(set(keys)), "Unique common-policy trace universe")
    require(tuple(v2.V2_SCORE_FEATURES) == BASE_FEATURES and set(panel) == set(FIELDS), "Frozen model panel/schema")
    masks, reasons, numeric = [], {}, []
    for key, trace, base, gbv in zip(keys, traces, base_records, gbv_records, strict=True):
        require(trace_key(base) == trace_key(gbv) == key, "Exact policy ledger order")
        decision = eligibility.assess_pair_eligibility(trace["a0"], trace["a1"])
        require(type(base["eligible"]) is bool and base["eligible"] is decision.eligible and
            base["forced_keep_reason"] == decision.reason, "Original likelihood eligibility and reason")
        require(type(gbv["eligible"]) is bool, "Explicit GbV eligibility")
        require(set(base["scores"]) == set(BASE_FEATURES), "Complete base score schema")
        if not decision.eligible:
            require(not gbv["eligible"] and gbv["forced_keep_reason"] == decision.reason and
                all(v is None for v in base["scores"].values()) and
                all(gbv[k] is None for k in ("F0", "F1", "gbv_margin")) and
                gbv["attempted_branches"] == gbv["forward_calls"] == 0 and not gbv["completed_branches"], "Shared native forced-keep row")
            require(base["cells"] is None and base["pair"] is None and not base["requests"] and
                not base["forward_witnesses"], "No likelihood requests for native ineligible pair")
            eligible, reason = False, decision.reason
        else:
            require(all(finite(v) for v in base["scores"].values()), "No missing eligible base score")
            require(type(base["cells"]) is dict and set(base["cells"]) == set(CELLS) and
                type(base["pair"]) is dict and len(base["requests"]) == 4, "Complete eligible likelihood record")
            if gbv["eligible"]:
                require(gbv["forced_keep_reason"] is None and gbv["failed_branch"] is None and
                    gbv["attempted_branches"] == 2 and len(gbv["completed_branches"]) == 2 and
                    all(finite(gbv[k]) for k in ("F0", "F1", "gbv_margin")) and
                    0 <= gbv["F0"] <= 1 and 0 <= gbv["F1"] <= 1 and
                    gbv["gbv_margin"] == gbv["F1"] - gbv["F0"], "Complete finite native GbV margin")
                eligible, reason = True, None
            else:
                reason = gbv["forced_keep_reason"]
                require(type(reason) is str and reason.startswith("nli_unscorable:") and
                    deterministic_nli_error(reason.removeprefix("nli_unscorable:")) and
                    gbv["gbv_margin"] is None and gbv["failed_branch"] in ("F0", "F1"), "Only deterministic NLI failure can extend common mask")
                finished = 0 if gbv["failed_branch"] == "F0" else 1
                require(gbv["attempted_branches"] == finished + 1 and len(gbv["completed_branches"]) == finished and
                    gbv["F1"] is None and ((gbv["F0"] is None) if finished == 0 else finite(gbv["F0"])), "Retain prior branch on deterministic NLI failure")
                eligible = False
        masks.append(eligible)
        reasons[key] = reason
        if eligible:
            numeric.append([base["scores"][name] for name in BASE_FEATURES] + [gbv["gbv_margin"]])
    selected_keys = [k for k, good in zip(keys, masks) if good]
    scores = {name: {key: None for key in keys} for name in SCORED_POLICIES}
    details = []
    if selected_keys:
        x = np.asarray(numeric, dtype=np.float64)
        panel_values = panel_scores(panel, selected_keys, x)
        v2_values = v2.score_unseen(bundle, x[:, :10])
        require(v2_values.shape == (len(selected_keys),) and np.isfinite(v2_values).all(), "Finite original V2 scores")
        for i, key in enumerate(selected_keys):
            values = dict(HGB=float(x[i, 0]), GbV=float(x[i, 10]), V2=float(v2_values[i]))
            values.update({name: float(panel_values[name]["pR"][i]) for name in FIELDS})
            for name, value in values.items():
                scores[name][key] = value
            details.append(dict(dataset=key[0], retriever=key[1], sample_id=key[2], numeric=x[i].tolist(),
                panel={name: {field: float(value[i]) for field, value in item.items()} for name, item in panel_values.items()},
                V2=float(v2_values[i])))
    result = allocate(keys, selected_keys, scores)
    for row in result["ledger"]:
        row["forced_keep_reason"] = reasons[trace_key(row)]
    result["policy_details"] = details
    result["forced_keep_counts"] = {reason: sum(value == reason for value in reasons.values())
        for reason in sorted({v for v in reasons.values() if v is not None})}
    return result
