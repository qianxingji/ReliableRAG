"""Describe saved Qwen action disagreement; no fitting or new significance test.

This is explicitly post-hoc accounting of the public numeric release. It must
not be used to select new features, thresholds, questions, or reader outcomes.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = "a930286d62bddf9f4837cb1beb4b863f0f94c1bc697b2311977a9b0eb18f09f7"
FUSION = "HGB_GBV_R"
CONTROL = "HGB_ONLY_R"


def describe(source: Path) -> dict:
    """Reconcile the four action-membership strata with accepted event totals."""
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError("Input is not the bound public Qwen numeric release")
    strata = defaultdict(Counter)
    cells = defaultdict(lambda: defaultdict(Counter))
    group_rows = defaultdict(set)
    seen = set()
    actions = Counter()
    policy_events = defaultdict(Counter)
    for line in gzip.open(source, "rt", encoding="utf-8"):
        row = json.loads(line)
        identity = (row["dataset"], row["group_id"], row["retriever"])
        if identity in seen:
            raise ValueError("Duplicate trace")
        seen.add(identity)
        group_rows[identity[:2]].add(row["retriever"])
        a0, a1 = row["a0_em"], row["a1_em"]
        if a0 not in (0, 1) or a1 not in (0, 1):
            raise ValueError("EM must be binary")
        event = "recovery" if a1 > a0 else "damage" if a1 < a0 else "neutral"
        selected = {}
        for policy in (FUSION, CONTROL):
            action = row["actions"][policy]
            if action not in ("KEEP", "REPLACE"):
                raise ValueError(f"Unknown action: {action}")
            selected[policy] = action == "REPLACE"
            if selected[policy]:
                if not row["eligible"]:
                    raise ValueError("Ineligible trace selected")
                actions[policy] += 1
                policy_events[policy][event] += 1
        fusion, control = selected[FUSION], selected[CONTROL]
        key = (
            "both" if fusion and control else "fusion_only" if fusion
            else "hgb_only" if control else "neither"
        )
        strata[key][event] += 1
        cells[(row["dataset"], row["retriever"])][key][event] += 1
    if len(seen) != 18000 or len(group_rows) != 6000:
        raise ValueError("Unexpected population size")
    if any(len(retrievers) != 3 for retrievers in group_rows.values()):
        raise ValueError("Each question must retain its three retrieval siblings")
    expected = {
        FUSION: {"recovery": 352, "damage": 11, "neutral": 537},
        CONTROL: {"recovery": 357, "damage": 26, "neutral": 517},
    }
    if dict(actions) != {FUSION: 900, CONTROL: 900}:
        raise ValueError("Action counts disagree with the frozen 5% allocation")
    if {p: dict(v) for p, v in policy_events.items()} != expected:
        raise ValueError("Events disagree with the accepted result/Claim map")

    def serialize(values: dict) -> dict:
        return {
            name: {"traces": sum(values[name].values()), **{
                event: values[name][event]
                for event in ("recovery", "damage", "neutral")
            }} for name in ("both", "fusion_only", "hgb_only", "neither")
        }

    delta_r = policy_events[FUSION]["recovery"] - policy_events[CONTROL]["recovery"]
    delta_d = policy_events[FUSION]["damage"] - policy_events[CONTROL]["damage"]
    return {
        "schema_version": 1,
        "analysis_role": "POST_HOC_DESCRIPTIVE_ACTION_ACCOUNTING",
        "source_sha256": digest,
        "source": str(source.resolve()),
        "source_repository_commit": "038d769e96d092a2eec3bbc5df9f45f3c2a17ff0",
        "question_groups": len(group_rows),
        "traces": len(seen),
        "actions_per_policy": dict(actions),
        "strata": serialize(strata),
        "policy_events": expected,
        "fusion_minus_hgb": {
            "recovery": delta_r, "damage": delta_d, "net_correct": delta_r - delta_d,
            "em_pp": 100 * (delta_r - delta_d) / len(seen),
            "damage_pp": 100 * delta_d / len(seen),
        },
        "dataset_retriever_descriptive_cells": [
            {"dataset": dataset, "retriever": retriever, "strata": serialize(value)}
            for (dataset, retriever), value in sorted(cells.items())
        ],
        "interpretation_limits": [
            "These are frozen action memberships; there is no reallocation or new inference.",
            "Counts for neither are potential paired outcomes, not executed recoveries or damage.",
            "Neutral means unchanged normalized EM, not necessarily unchanged F1.",
            "Disagreement strata depend on the policies and are descriptive, not causal subgroups.",
            "Reader extension hypotheses are informed by the already observed Qwen results.",
            "No reader transfer, equivalence, noninferiority, or algorithm novelty is established.",
        ],
        "new_fits": 0,
        "neural_forwards": 0,
        "new_bootstrap_runs": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = describe(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"output": str(args.output), "strata": report["strata"],
                      "delta": report["fusion_minus_hgb"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
