#!/usr/bin/env python3
"""Create and seal DAA-V2 actions before fresh evaluation labels are opened.

Input rows contain identifiers and label-free selector scores only. The script loads a
frozen V2 ensemble, assigns a fused score to scorable rows, spends exactly the fixed
action-rate budget globally, and writes KEEP/REPLACE actions. It has no label input.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.arbitration.v2_ensemble import action_budget, score_unseen  # noqa: E402


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
    return (row["dataset"], row["retriever"], row["sample_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-ledger", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--actions-output", type=Path, required=True)
    parser.add_argument("--seal-output", type=Path, required=True)
    args = parser.parse_args()

    rows = read_jsonl(args.score_ledger)
    if len({key(row) for row in rows}) != len(rows):
        raise RuntimeError("duplicate dataset/retriever/sample_id keys in score ledger")

    bundle = joblib.load(args.model)
    scorable_indices: list[int] = []
    feature_rows: list[list[float]] = []
    for index, row in enumerate(rows):
        scores = row.get("scores", {})
        values = [scores.get(name) for name in bundle.feature_names]
        if any(value is None for value in values):
            continue
        scorable_indices.append(index)
        feature_rows.append([float(value) for value in values])

    budget = action_budget(len(rows), bundle.action_rate)
    if len(scorable_indices) < budget:
        raise RuntimeError(
            f"only {len(scorable_indices)} rows are scorable for action budget {budget}"
        )

    fused = score_unseen(bundle, np.asarray(feature_rows, dtype=float))
    ranked_local = sorted(
        range(len(scorable_indices)),
        key=lambda j: (-float(fused[j]), key(rows[scorable_indices[j]])),
    )
    replace_indices = {scorable_indices[j] for j in ranked_local[:budget]}
    score_by_index = {
        scorable_indices[j]: float(fused[j]) for j in range(len(scorable_indices))
    }

    args.actions_output.parent.mkdir(parents=True, exist_ok=True)
    with args.actions_output.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(rows):
            record = {
                "dataset": row["dataset"],
                "retriever": row["retriever"],
                "sample_id": row["sample_id"],
                "v2_score": score_by_index.get(index),
                "action": "REPLACE" if index in replace_indices else "KEEP",
                "scorable": index in score_by_index,
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    stratum_counts = Counter(
        (rows[index]["dataset"], rows[index]["retriever"])
        for index in replace_indices
    )
    seal = {
        "status": "V2_PRELABEL_ACTION_SEAL",
        "saved_utc": datetime.now(timezone.utc).isoformat(),
        "trace_count": len(rows),
        "scorable_count": len(scorable_indices),
        "action_rate": bundle.action_rate,
        "replace_count": len(replace_indices),
        "model_sha256": sha256(args.model),
        "score_ledger_sha256": sha256(args.score_ledger),
        "actions_sha256": sha256(args.actions_output),
        "stratum_replace_counts": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(stratum_counts.items())
        },
        "gold_or_outcome_input": False,
        "tie_break": "descending fused score; then dataset, retriever, sample_id lexical order",
    }
    args.seal_output.parent.mkdir(parents=True, exist_ok=True)
    args.seal_output.write_text(json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
