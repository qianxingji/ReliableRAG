#!/usr/bin/env python3
"""Nested grouped development study for the DAA-V2 meta selector.

The historical main evaluation is treated as development-only evidence for V2. The
script never changes historical decisions. It evaluates whether a lightweight
three-state damage-aware meta model can improve the ranking of the already-frozen
state-symmetrized HGB score.

The outer folds are evaluation-only. Lambda and the HGB/meta fusion weight are chosen
inside each outer-training split from inner out-of-fold predictions. Question/sample
IDs are the grouping unit so all retriever traces for a question stay together.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


FEATURES = [
    "state_symmetric_hgb",
    "state_symmetric_logistic",
    "no_cross_state",
    "no_B",
    "no_evidence_change",
    "no_answer_form",
    "ordinary_compact_logistic",
    "B_rule",
    "higher_own_likelihood",
    "likelihood_margin",
]
DEFAULT_LAMBDAS = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0)
DEFAULT_ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> Iterable[dict]:
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


def empirical_cdf(reference: np.ndarray, values: np.ndarray) -> np.ndarray:
    ordered = np.sort(np.asarray(reference, dtype=float))
    if len(ordered) == 0:
        raise ValueError("empirical CDF requires a non-empty reference")
    return np.searchsorted(ordered, np.asarray(values, dtype=float), side="right") / len(ordered)


def allocate_budget(sizes: list[int], total: int) -> list[int]:
    if total < 0 or total > sum(sizes):
        raise ValueError("invalid total budget")
    raw = np.asarray(sizes, dtype=float) * total / sum(sizes)
    base = np.floor(raw).astype(int)
    remaining = total - int(base.sum())
    residual = raw - base
    order = np.argsort(-residual, kind="stable")
    base[order[:remaining]] += 1
    return base.tolist()


def build_model() -> object:
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=4000,
            class_weight="balanced",
            C=1.0,
        ),
    )


def select_local(
    indices: np.ndarray,
    local_score: np.ndarray,
    budget: int,
    keys: list[tuple[str, str, str]],
) -> list[int]:
    if len(indices) != len(local_score):
        raise ValueError("indices and local_score must have the same length")
    local_order = sorted(
        range(len(indices)),
        key=lambda j: (-float(local_score[j]), keys[int(indices[j])]),
    )
    return [int(indices[j]) for j in local_order[:budget]]


def metrics(indices: list[int], y: np.ndarray) -> dict[str, int]:
    labels = y[np.asarray(indices, dtype=int)]
    recovery = int(np.sum(labels == "recovery"))
    damage = int(np.sum(labels == "damage"))
    return {
        "actions": len(indices),
        "recovery": recovery,
        "damage": damage,
        "net": recovery - damage,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=370)
    parser.add_argument("--outer-folds", type=int, default=5)
    parser.add_argument("--inner-folds", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260909)
    args = parser.parse_args()

    outcomes = {row_key(row): row for row in read_jsonl(args.outcomes)}
    records = []
    for decision in read_jsonl(args.decisions):
        score = decision.get("scores", {}).get("state_symmetric_hgb")
        if score is None:
            continue
        outcome = outcomes[row_key(decision)]
        records.append((decision, outcome, transition_label(outcome)))

    x = np.asarray(
        [[float(decision["scores"][name]) for name in FEATURES] for decision, _, _ in records],
        dtype=float,
    )
    hgb = x[:, 0]
    y = np.asarray([label for _, _, label in records])
    groups = np.asarray([decision["sample_id"] for decision, _, _ in records])
    keys = [
        (decision["dataset"], decision["retriever"], decision["sample_id"])
        for decision, _, _ in records
    ]

    outer = GroupKFold(n_splits=args.outer_folds, shuffle=True, random_state=args.seed)
    outer_splits = list(outer.split(x, y, groups))
    outer_budgets = allocate_budget([len(valid) for _, valid in outer_splits], args.budget)
    target_rate = args.budget / len(records)

    v2_selected: list[int] = []
    hgb_selected: list[int] = []
    fold_records = []

    for fold_index, ((train, valid), valid_budget) in enumerate(zip(outer_splits, outer_budgets)):
        inner = GroupKFold(
            n_splits=args.inner_folds,
            shuffle=True,
            random_state=args.seed + 1000 + fold_index,
        )
        inner_splits = list(inner.split(x[train], y[train], groups[train]))

        p_recovery = np.zeros(len(train), dtype=float)
        p_damage = np.zeros(len(train), dtype=float)
        for inner_train, inner_valid in inner_splits:
            model = build_model()
            model.fit(x[train][inner_train], y[train][inner_train])
            proba = model.predict_proba(x[train][inner_valid])
            classes = list(model[-1].classes_)
            p_recovery[inner_valid] = proba[:, classes.index("recovery")]
            p_damage[inner_valid] = proba[:, classes.index("damage")]

        hgb_quantile_train = empirical_cdf(hgb[train], hgb[train])
        inner_budget = round(target_rate * len(train))
        best = None
        for lambda_damage in DEFAULT_LAMBDAS:
            utility = p_recovery - lambda_damage * p_damage
            utility_quantile = empirical_cdf(utility, utility)
            for alpha in DEFAULT_ALPHAS:
                fused = hgb_quantile_train + alpha * utility_quantile
                local_order = sorted(
                    range(len(train)),
                    key=lambda j: (-float(fused[j]), keys[train[j]]),
                )[:inner_budget]
                selected_train = train[np.asarray(local_order, dtype=int)]
                summary = metrics(selected_train.tolist(), y)
                objective = (
                    summary["net"],
                    -summary["damage"],
                    summary["recovery"],
                    -alpha,
                    -abs(lambda_damage - 2.0),
                )
                if best is None or objective > best[0]:
                    best = (objective, lambda_damage, alpha, summary)

        assert best is not None
        _, lambda_damage, alpha, inner_summary = best

        model = build_model()
        model.fit(x[train], y[train])
        valid_proba = model.predict_proba(x[valid])
        classes = list(model[-1].classes_)
        valid_utility = (
            valid_proba[:, classes.index("recovery")]
            - lambda_damage * valid_proba[:, classes.index("damage")]
        )
        training_oof_utility = p_recovery - lambda_damage * p_damage

        valid_hgb_quantile = empirical_cdf(hgb[train], hgb[valid])
        valid_utility_quantile = empirical_cdf(training_oof_utility, valid_utility)
        valid_fused = valid_hgb_quantile + alpha * valid_utility_quantile

        v2_fold = select_local(valid, valid_fused, valid_budget, keys)
        hgb_fold = select_local(valid, hgb[valid], valid_budget, keys)
        v2_selected.extend(v2_fold)
        hgb_selected.extend(hgb_fold)

        fold_records.append(
            {
                "fold": fold_index,
                "train_scorable": len(train),
                "valid_scorable": len(valid),
                "valid_budget": valid_budget,
                "selected_lambda_damage": lambda_damage,
                "selected_alpha": alpha,
                "inner_selection_metrics": inner_summary,
                "outer_v2_metrics": metrics(v2_fold, y),
                "outer_raw_hgb_metrics": metrics(hgb_fold, y),
            }
        )

    result = {
        "status": "NESTED_DEVELOPMENT_VALIDATION_ONLY",
        "source_hashes": {
            "decisions_sha256": sha256(args.decisions),
            "outcomes_sha256": sha256(args.outcomes),
        },
        "feature_names": FEATURES,
        "label_space": ["recovery", "damage", "neutral"],
        "label_counts": dict(Counter(y.tolist())),
        "scorable_records": len(records),
        "budget": args.budget,
        "outer_folds": args.outer_folds,
        "inner_folds": args.inner_folds,
        "seed": args.seed,
        "selection_grid": {
            "lambda_damage": list(DEFAULT_LAMBDAS),
            "alpha": list(DEFAULT_ALPHAS),
        },
        "v2_nested_metrics": metrics(v2_selected, y),
        "raw_hgb_same_outer_budgets": metrics(hgb_selected, y),
        "folds": fold_records,
        "interpretation": (
            "This is nested development validation after reclassifying the historical main cohort as "
            "V2 development evidence. It is not a fresh confirmatory superiority result. The V2 score "
            "uses only label-free frozen selector scores at runtime; gold-derived transition labels are "
            "used only inside development fitting/selection and evaluation."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
