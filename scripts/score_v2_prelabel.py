#!/usr/bin/env python3
"""Create and seal DAA-V2 and raw-HGB actions before fresh labels are opened.

V2 and GbV share the same strict canonical branch ledger and answer-pair eligibility
rule. This script consumes only label-free selector scores plus the canonical branch
ledger; no evaluation outcome file is accepted. Raw global HGB at the exact V2 budget
is sealed as the mandatory backbone ablation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.arbitration.v2_ensemble import action_budget, score_unseen  # noqa: E402
from src.evaluation.answer_normalization import assess_pair_eligibility  # noqa: E402
from src.evaluation.fresh_schema import read_fresh_branches, trace_key  # noqa: E402

HGB_FIELD = "state_symmetric_hgb"


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


def finite_or_none(value):
    if value is None:
        return None
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branches", type=Path, required=True)
    parser.add_argument("--score-ledger", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--actions-output", type=Path, required=True)
    parser.add_argument("--seal-output", type=Path, required=True)
    args = parser.parse_args()

    branches = read_fresh_branches(args.branches)
    branch_by_key = {trace_key(row): row for row in branches}
    score_rows = read_jsonl(args.score_ledger)
    score_by_key = {key(row): row for row in score_rows}
    if len(score_by_key) != len(score_rows):
        raise RuntimeError("duplicate dataset/retriever/sample_id keys in score ledger")
    if set(branch_by_key) != set(score_by_key):
        raise RuntimeError("canonical branch and V2 score ledgers must contain identical keys")

    bundle = joblib.load(args.model)
    if HGB_FIELD not in bundle.feature_names:
        raise RuntimeError(f"V2 bundle does not contain mandatory {HGB_FIELD} backbone field")

    ordered_keys = sorted(branch_by_key)
    v2_scorable_keys: list[tuple[str, str, str]] = []
    v2_feature_rows: list[list[float]] = []
    hgb_scorable: list[tuple[tuple[str, str, str], float]] = []
    forced_keep_reasons: dict[tuple[str, str, str], str] = {}

    for row_key in ordered_keys:
        branch = branch_by_key[row_key]
        eligibility = assess_pair_eligibility(branch["a0"], branch["a1"])
        if not eligibility.eligible:
            forced_keep_reasons[row_key] = eligibility.reason or "ineligible"
            continue

        scores = score_by_key[row_key].get("scores", {})
        hgb_score = finite_or_none(scores.get(HGB_FIELD))
        if hgb_score is not None:
            hgb_scorable.append((row_key, hgb_score))

        values = [finite_or_none(scores.get(name)) for name in bundle.feature_names]
        if any(value is None for value in values):
            forced_keep_reasons[row_key] = "missing_or_nonfinite_v2_feature"
            continue
        v2_scorable_keys.append(row_key)
        v2_feature_rows.append([float(value) for value in values])

    budget = action_budget(len(branches), bundle.action_rate)
    if len(v2_scorable_keys) < budget:
        raise RuntimeError(
            f"only {len(v2_scorable_keys)} V2-scorable rows for action budget {budget}"
        )
    if len(hgb_scorable) < budget:
        raise RuntimeError(
            f"only {len(hgb_scorable)} raw-HGB-scorable rows for action budget {budget}"
        )

    fused = score_unseen(bundle, np.asarray(v2_feature_rows, dtype=float))
    v2_ranked_local = sorted(
        range(len(v2_scorable_keys)),
        key=lambda index: (-float(fused[index]), v2_scorable_keys[index]),
    )
    v2_replace_keys = {
        v2_scorable_keys[index] for index in v2_ranked_local[:budget]
    }
    v2_score_by_trace = {
        v2_scorable_keys[index]: float(fused[index])
        for index in range(len(v2_scorable_keys))
    }

    hgb_scorable.sort(key=lambda item: (-item[1], item[0]))
    hgb_replace_keys = {row_key for row_key, _ in hgb_scorable[:budget]}
    hgb_score_by_trace = dict(hgb_scorable)

    args.actions_output.parent.mkdir(parents=True, exist_ok=True)
    with args.actions_output.open("w", encoding="utf-8") as handle:
        for row_key in ordered_keys:
            record = {
                "dataset": row_key[0],
                "retriever": row_key[1],
                "sample_id": row_key[2],
                "v2_score": v2_score_by_trace.get(row_key),
                "hgb_score": hgb_score_by_trace.get(row_key),
                "action": "REPLACE" if row_key in v2_replace_keys else "KEEP",
                "hgb_action": "REPLACE" if row_key in hgb_replace_keys else "KEEP",
                "v2_eligible_and_scorable": row_key in v2_score_by_trace,
                "hgb_eligible_and_scorable": row_key in hgb_score_by_trace,
                "forced_keep_reason": forced_keep_reasons.get(row_key),
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    v2_strata = Counter((row_key[0], row_key[1]) for row_key in v2_replace_keys)
    hgb_strata = Counter((row_key[0], row_key[1]) for row_key in hgb_replace_keys)
    reason_counts = Counter(forced_keep_reasons.values())
    seal = {
        "status": "V2_PRELABEL_ACTION_SEAL",
        "saved_utc": datetime.now(timezone.utc).isoformat(),
        "trace_count": len(branches),
        "v2_eligible_scorable_count": len(v2_scorable_keys),
        "hgb_eligible_scorable_count": len(hgb_scorable),
        "forced_keep_counts": dict(sorted(reason_counts.items())),
        "action_rate": bundle.action_rate,
        "replace_count": len(v2_replace_keys),
        "hgb_replace_count": len(hgb_replace_keys),
        "model_sha256": sha256(args.model),
        "branches_sha256": sha256(args.branches),
        "score_ledger_sha256": sha256(args.score_ledger),
        "actions_sha256": sha256(args.actions_output),
        "stratum_replace_counts": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(v2_strata.items())
        },
        "hgb_stratum_replace_counts": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(hgb_strata.items())
        },
        "shared_eligibility_rule": "HotpotQA-style normalization; equal/empty pairs forced KEEP",
        "gold_or_outcome_input": False,
        "v2_tie_break": "descending fused score; then dataset, retriever, sample_id lexical order",
        "hgb_tie_break": "descending raw state_symmetric_hgb score; then dataset, retriever, sample_id lexical order",
        "backbone_ablation_predeclared": True,
    }
    args.seal_output.parent.mkdir(parents=True, exist_ok=True)
    args.seal_output.write_text(
        json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
