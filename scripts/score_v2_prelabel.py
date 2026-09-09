#!/usr/bin/env python3
"""Create and seal DAA-V2 actions before fresh evaluation labels are opened.

V2 and GbV share the same strict canonical branch ledger and the same answer-pair
eligibility rule. This script consumes only label-free selector scores plus the canonical
branch ledger; no evaluation outcome file is accepted.
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
    ordered_keys = sorted(branch_by_key)
    scorable_keys: list[tuple[str, str, str]] = []
    feature_rows: list[list[float]] = []
    forced_keep_reasons: dict[tuple[str, str, str], str] = {}
    for row_key in ordered_keys:
        branch = branch_by_key[row_key]
        eligibility = assess_pair_eligibility(branch["a0"], branch["a1"])
        if not eligibility.eligible:
            forced_keep_reasons[row_key] = eligibility.reason or "ineligible"
            continue
        scores = score_by_key[row_key].get("scores", {})
        values = [scores.get(name) for name in bundle.feature_names]
        if any(value is None for value in values):
            forced_keep_reasons[row_key] = "missing_v2_feature"
            continue
        numeric = [float(value) for value in values]
        if not all(math.isfinite(value) for value in numeric):
            forced_keep_reasons[row_key] = "nonfinite_v2_feature"
            continue
        scorable_keys.append(row_key)
        feature_rows.append(numeric)

    budget = action_budget(len(branches), bundle.action_rate)
    if len(scorable_keys) < budget:
        raise RuntimeError(
            f"only {len(scorable_keys)} eligible/scorable rows for action budget {budget}"
        )

    fused = score_unseen(bundle, np.asarray(feature_rows, dtype=float))
    ranked_local = sorted(
        range(len(scorable_keys)),
        key=lambda index: (-float(fused[index]), scorable_keys[index]),
    )
    replace_keys = {scorable_keys[index] for index in ranked_local[:budget]}
    score_by_trace = {
        scorable_keys[index]: float(fused[index]) for index in range(len(scorable_keys))
    }

    args.actions_output.parent.mkdir(parents=True, exist_ok=True)
    with args.actions_output.open("w", encoding="utf-8") as handle:
        for row_key in ordered_keys:
            record = {
                "dataset": row_key[0],
                "retriever": row_key[1],
                "sample_id": row_key[2],
                "v2_score": score_by_trace.get(row_key),
                "action": "REPLACE" if row_key in replace_keys else "KEEP",
                "eligible_and_scorable": row_key in score_by_trace,
                "forced_keep_reason": forced_keep_reasons.get(row_key),
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    stratum_counts = Counter((row_key[0], row_key[1]) for row_key in replace_keys)
    reason_counts = Counter(forced_keep_reasons.values())
    seal = {
        "status": "V2_PRELABEL_ACTION_SEAL",
        "saved_utc": datetime.now(timezone.utc).isoformat(),
        "trace_count": len(branches),
        "eligible_scorable_count": len(scorable_keys),
        "forced_keep_counts": dict(sorted(reason_counts.items())),
        "action_rate": bundle.action_rate,
        "replace_count": len(replace_keys),
        "model_sha256": sha256(args.model),
        "branches_sha256": sha256(args.branches),
        "score_ledger_sha256": sha256(args.score_ledger),
        "actions_sha256": sha256(args.actions_output),
        "stratum_replace_counts": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(stratum_counts.items())
        },
        "shared_eligibility_rule": "HotpotQA-style normalization; equal/empty pairs forced KEEP",
        "gold_or_outcome_input": False,
        "tie_break": "descending fused score; then dataset, retriever, sample_id lexical order",
    }
    args.seal_output.parent.mkdir(parents=True, exist_ok=True)
    args.seal_output.write_text(
        json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
