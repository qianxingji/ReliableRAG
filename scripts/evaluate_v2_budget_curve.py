#!/usr/bin/env python3
"""Evaluate the predeclared same-budget V2/HGB/GbV operating-point grid.

This script is post-seal only. The ranking scores are fixed before labels are opened and
the budget grid is read from a precommitted JSON specification. It cannot search for or
promote a new primary operating point.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.arbitration.v2_ensemble import action_budget  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def key(row: dict) -> tuple[str, str, str]:
    return (str(row["dataset"]), str(row["retriever"]), str(row["sample_id"]))


def finite_score(value):
    if value is None:
        return None
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def select_top(score_map: dict, budget: int) -> dict:
    ranked = [(k, score) for k, score in score_map.items() if score is not None]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    if len(ranked) < budget:
        raise RuntimeError(
            f"only {len(ranked)} scorable rows available for requested budget {budget}"
        )
    selected = {k for k, _ in ranked[:budget]}
    return {k: ("REPLACE" if k in selected else "KEEP") for k in score_map}


def metrics(actions: dict, outcomes: dict) -> dict:
    recovery = damage = replace = 0
    baseline_em = selected_em = 0.0
    baseline_f1 = selected_f1 = 0.0
    initially_correct = 0
    for k, outcome in outcomes.items():
        use_repair = actions[k] == "REPLACE"
        a0_em, a1_em = int(outcome["a0_em"]), int(outcome["a1_em"])
        a0_f1, a1_f1 = float(outcome["a0_f1"]), float(outcome["a1_f1"])
        initially_correct += a0_em
        replace += int(use_repair)
        recovery += int(use_repair and a0_em == 0 and a1_em == 1)
        damage += int(use_repair and a0_em == 1 and a1_em == 0)
        baseline_em += a0_em
        baseline_f1 += a0_f1
        selected_em += a1_em if use_repair else a0_em
        selected_f1 += a1_f1 if use_repair else a0_f1
    n = len(outcomes)
    return {
        "actions": replace,
        "recovery": recovery,
        "damage": damage,
        "net": recovery - damage,
        "delta_em_pp": 100.0 * (selected_em - baseline_em) / n,
        "delta_f1_pp": 100.0 * (selected_f1 - baseline_f1) / n,
        "system_damage_percent": 100.0 * damage / initially_correct if initially_correct else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--combined-gate", type=Path, required=True)
    parser.add_argument("--v2-actions", type=Path, required=True)
    parser.add_argument("--gbv-scores", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument(
        "--grid",
        type=Path,
        default=Path("docs/V2_SECONDARY_BUDGET_GRID.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    gate = json.loads(args.combined_gate.read_text(encoding="utf-8"))
    if gate.get("status") != "PASS" or gate.get("stage") != "DAA_V2_GBV_COMBINED_PRELABEL_GATE":
        raise RuntimeError("combined pre-label gate is not PASS")
    if gate.get("fresh_label_access_authorized") is not False:
        raise RuntimeError("combined gate must have been created before label access")
    if gate.get("hashes", {}).get("v2_actions_sha256") != sha256(args.v2_actions):
        raise RuntimeError("V2 score/action ledger differs from the pre-label gate")
    if gate.get("hashes", {}).get("gbv_scores_sha256") != sha256(args.gbv_scores):
        raise RuntimeError("GbV score ledger differs from the pre-label gate")

    v2_rows = read_jsonl(args.v2_actions)
    gbv_rows = read_jsonl(args.gbv_scores)
    outcome_rows = read_jsonl(args.outcomes)
    v2_by_key = {key(row): row for row in v2_rows}
    gbv_by_key = {key(row): row for row in gbv_rows}
    outcomes = {key(row): row for row in outcome_rows}
    if len(v2_by_key) != len(v2_rows) or len(gbv_by_key) != len(gbv_rows) or len(outcomes) != len(outcome_rows):
        raise RuntimeError("duplicate keys in curve inputs")
    if set(v2_by_key) != set(gbv_by_key) or set(v2_by_key) != set(outcomes):
        raise RuntimeError("curve inputs must contain identical trace keys")

    v2_scores = {k: finite_score(row.get("v2_score")) for k, row in v2_by_key.items()}
    hgb_scores = {k: finite_score(row.get("hgb_score")) for k, row in v2_by_key.items()}
    gbv_scores = {
        k: (
            finite_score(row.get("gbv_margin"))
            if row.get("eligible") is not False
            else None
        )
        for k, row in gbv_by_key.items()
    }

    specification = json.loads(args.grid.read_text(encoding="utf-8"))
    rates = [float(rate) for rate in specification["secondary_action_rates"]]
    if float(specification["primary_action_rate"]) not in rates:
        raise RuntimeError("primary action rate must appear in the frozen secondary grid")

    rows = []
    favorable_v2_vs_gbv = 0
    for rate in rates:
        budget = action_budget(len(outcomes), rate)
        v2 = metrics(select_top(v2_scores, budget), outcomes)
        hgb = metrics(select_top(hgb_scores, budget), outcomes)
        gbv = metrics(select_top(gbv_scores, budget), outcomes)
        favorable = v2["net"] > gbv["net"] and v2["damage"] <= gbv["damage"]
        favorable_v2_vs_gbv += int(favorable)
        rows.append(
            {
                "action_rate": rate,
                "action_budget": budget,
                "daa_v2": v2,
                "raw_hgb": hgb,
                "gbv": gbv,
                "v2_higher_net_and_no_more_damage_than_gbv": favorable,
                "v2_higher_net_and_no_more_damage_than_hgb": (
                    v2["net"] > hgb["net"] and v2["damage"] <= hgb["damage"]
                ),
            }
        )

    result = {
        "status": "POST_SEAL_SECONDARY_BUDGET_GRID",
        "grid_sha256": sha256(args.grid),
        "combined_gate_sha256": sha256(args.combined_gate),
        "outcomes_sha256": sha256(args.outcomes),
        "rates": rates,
        "operating_points": rows,
        "engineering_frontier_summary": {
            "favorable_v2_vs_gbv_rate_count": favorable_v2_vs_gbv,
            "total_rate_count": len(rates),
            "target_at_least_4_of_5": favorable_v2_vs_gbv >= 4 if len(rates) == 5 else None,
        },
        "interpretation_guardrail": (
            "The entire grid was frozen before fresh-label access. These operating-point results are "
            "secondary descriptive evidence and cannot replace the primary 5.0% matched-budget result."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
