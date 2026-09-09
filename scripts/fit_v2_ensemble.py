#!/usr/bin/env python3
"""Fit the fixed-parameter DAA-V2 cross-fitted ensemble on development data.

The resulting joblib bundle contains only lightweight classifiers and numeric score
reference distributions. It contains no benchmark question, passage, answer, or gold
string. This script is for development/freeze preparation; a fresh confirmatory label
file must never be supplied here.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import sys

import joblib
import numpy as np
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.arbitration.v2_ensemble import (  # noqa: E402
    V2_ACTION_RATE,
    V2_GROUP_FOLDS,
    V2_GROUP_SEED,
    V2_LAMBDA_DAMAGE,
    V2_META_ALPHA,
    V2_SCORE_FEATURES,
    action_budget,
    fit_crossfitted_ensemble,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def row_key(row: dict) -> tuple[str, str, str]:
    return (row["sample_id"], row["dataset"], row["retriever"])


def transition_label(outcome: dict) -> str:
    if int(outcome["a0_em"]) == 0 and int(outcome["a1_em"]) == 1:
        return "recovery"
    if int(outcome["a0_em"]) == 1 and int(outcome["a1_em"]) == 0:
        return "damage"
    return "neutral"


def stable_order(scores: np.ndarray, keys: list[tuple[str, str, str]]) -> list[int]:
    return sorted(range(len(scores)), key=lambda i: (-float(scores[i]), keys[i]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--model-output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    args = parser.parse_args()

    outcomes = {row_key(row): row for row in read_jsonl(args.outcomes)}
    decisions = []
    for row in read_jsonl(args.decisions):
        if row.get("scores", {}).get("state_symmetric_hgb") is not None:
            decisions.append(row)

    x = np.asarray(
        [[float(row["scores"][name]) for name in V2_SCORE_FEATURES] for row in decisions],
        dtype=float,
    )
    labels = np.asarray([transition_label(outcomes[row_key(row)]) for row in decisions])
    groups = np.asarray([f'{row["dataset"]}:{row["sample_id"]}' for row in decisions])
    hgb_scores = x[:, V2_SCORE_FEATURES.index("state_symmetric_hgb")]
    keys = [(row["dataset"], row["retriever"], row["sample_id"]) for row in decisions]

    bundle, oof_fused = fit_crossfitted_ensemble(
        x,
        labels,
        groups,
        hgb_scores=hgb_scores,
        n_splits=V2_GROUP_FOLDS,
        seed=V2_GROUP_SEED,
        lambda_damage=V2_LAMBDA_DAMAGE,
        meta_alpha=V2_META_ALPHA,
        action_rate=V2_ACTION_RATE,
    )

    budget = action_budget(9000, V2_ACTION_RATE)
    selected = stable_order(oof_fused, keys)[:budget]
    selected_labels = labels[np.asarray(selected, dtype=int)]
    recovery = int(np.sum(selected_labels == "recovery"))
    damage = int(np.sum(selected_labels == "damage"))

    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.model_output)

    manifest = {
        "status": "V2_DEVELOPMENT_CANDIDATE_NOT_FRESH_CONFIRMATORY",
        "source_hashes": {
            "decisions_sha256": sha256(args.decisions),
            "outcomes_sha256": sha256(args.outcomes),
        },
        "model_sha256": sha256(args.model_output),
        "scorable_records": len(decisions),
        "label_counts": dict(Counter(labels.tolist())),
        "feature_names": list(V2_SCORE_FEATURES),
        "lambda_damage": V2_LAMBDA_DAMAGE,
        "meta_alpha": V2_META_ALPHA,
        "action_rate": V2_ACTION_RATE,
        "reference_trace_count": 9000,
        "reference_action_budget": budget,
        "group_folds": V2_GROUP_FOLDS,
        "group_seed": V2_GROUP_SEED,
        "oof_development_diagnostic": {
            "actions": budget,
            "recovery": recovery,
            "damage": damage,
            "net": recovery - damage,
        },
        "runtime_gold_free": true,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "interpretation": (
            "The bundle is trained only for the prospective V2 design after the historical "
            "9,000-trace cohort was reclassified as development evidence. Its OOF metric is "
            "development evidence and must not be reported as fresh-test superiority."
        ),
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
