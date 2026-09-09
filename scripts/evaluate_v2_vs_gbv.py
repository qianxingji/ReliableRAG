#!/usr/bin/env python3
"""Post-seal evaluation of DAA-V2 versus matched Generate-but-Verify actions.

Run this script only after both action ledgers have been sealed without labels. It joins
numeric evaluation outcomes, computes policy metrics, and performs one predeclared
question-cluster bootstrap for paired V2-minus-GbV differences.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

BOOTSTRAP_SEED = 20260920
BOOTSTRAP_DRAWS = 10000


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


def selected_metrics(actions: dict, outcomes: dict) -> dict[str, float | int]:
    recovery = damage = replace = 0
    selected_em = selected_f1 = baseline_em = baseline_f1 = 0.0
    initially_correct = 0
    for k, outcome in outcomes.items():
        use_repair = actions[k] == "REPLACE"
        replace += int(use_repair)
        a0_em = int(outcome["a0_em"])
        a1_em = int(outcome["a1_em"])
        a0_f1 = float(outcome["a0_f1"])
        a1_f1 = float(outcome["a1_f1"])
        initially_correct += a0_em
        recovery += int(use_repair and a0_em == 0 and a1_em == 1)
        damage += int(use_repair and a0_em == 1 and a1_em == 0)
        baseline_em += a0_em
        baseline_f1 += a0_f1
        selected_em += a1_em if use_repair else a0_em
        selected_f1 += a1_f1 if use_repair else a0_f1
    n = len(outcomes)
    return {
        "trace_count": n,
        "replace": replace,
        "recovery": recovery,
        "damage": damage,
        "net": recovery - damage,
        "em": 100.0 * selected_em / n,
        "f1": 100.0 * selected_f1 / n,
        "delta_em_pp": 100.0 * (selected_em - baseline_em) / n,
        "delta_f1_pp": 100.0 * (selected_f1 - baseline_f1) / n,
        "system_damage_percent": 100.0 * damage / initially_correct,
        "action_recovery_percent": 100.0 * recovery / replace if replace else 0.0,
        "action_damage_percent": 100.0 * damage / replace if replace else 0.0,
    }


def policy_values(actions: dict, outcomes: dict):
    em = {}
    f1 = {}
    damage = {}
    for k, outcome in outcomes.items():
        use_repair = actions[k] == "REPLACE"
        a0_em = int(outcome["a0_em"])
        a1_em = int(outcome["a1_em"])
        a0_f1 = float(outcome["a0_f1"])
        a1_f1 = float(outcome["a1_f1"])
        em[k] = a1_em if use_repair else a0_em
        f1[k] = a1_f1 if use_repair else a0_f1
        damage[k] = int(use_repair and a0_em == 1 and a1_em == 0)
    return em, f1, damage


def cluster_bootstrap(v2_actions: dict, gbv_actions: dict, outcomes: dict) -> dict:
    v2_em, v2_f1, v2_damage = policy_values(v2_actions, outcomes)
    gbv_em, gbv_f1, gbv_damage = policy_values(gbv_actions, outcomes)

    cluster_rows: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    for k in outcomes:
        cluster_rows[(k[0], k[2])].append(k)
    clusters = sorted(cluster_rows)
    if not clusters:
        raise RuntimeError("no clusters available")

    per_cluster = []
    for cluster in clusters:
        rows = cluster_rows[cluster]
        em_diff = sum(v2_em[k] - gbv_em[k] for k in rows)
        f1_diff = sum(v2_f1[k] - gbv_f1[k] for k in rows)
        damage_diff = sum(v2_damage[k] - gbv_damage[k] for k in rows)
        initial_correct = sum(int(outcomes[k]["a0_em"]) for k in rows)
        per_cluster.append((len(rows), em_diff, f1_diff, damage_diff, initial_correct))

    matrix = np.asarray(per_cluster, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = rng.integers(0, len(clusters), size=(BOOTSTRAP_DRAWS, len(clusters)))

    em_samples = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    f1_samples = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    damage_samples = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for i, sampled in enumerate(draws):
        selected = matrix[sampled]
        n_rows = selected[:, 0].sum()
        em_samples[i] = 100.0 * selected[:, 1].sum() / n_rows
        f1_samples[i] = 100.0 * selected[:, 2].sum() / n_rows
        initial_correct = selected[:, 4].sum()
        damage_samples[i] = (
            100.0 * selected[:, 3].sum() / initial_correct
            if initial_correct > 0
            else np.nan
        )

    def interval(samples: np.ndarray) -> list[float]:
        return [
            float(np.nanquantile(samples, 0.025)),
            float(np.nanquantile(samples, 0.975)),
        ]

    point_em = 100.0 * sum(v2_em[k] - gbv_em[k] for k in outcomes) / len(outcomes)
    point_f1 = 100.0 * sum(v2_f1[k] - gbv_f1[k] for k in outcomes) / len(outcomes)
    initial_correct = sum(int(outcomes[k]["a0_em"]) for k in outcomes)
    point_damage = 100.0 * sum(v2_damage[k] - gbv_damage[k] for k in outcomes) / initial_correct

    return {
        "cluster_count": len(clusters),
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "v2_minus_gbv_em_pp": {"point": point_em, "ci95": interval(em_samples)},
        "v2_minus_gbv_f1_pp": {"point": point_f1, "ci95": interval(f1_samples)},
        "v2_minus_gbv_damage_pp": {
            "point": point_damage,
            "ci95": interval(damage_samples),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2-actions", type=Path, required=True)
    parser.add_argument("--gbv-actions", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    v2_rows = read_jsonl(args.v2_actions)
    gbv_rows = read_jsonl(args.gbv_actions)
    outcome_rows = read_jsonl(args.outcomes)
    v2_by_key = {key(row): row for row in v2_rows}
    gbv_by_key = {key(row): row for row in gbv_rows}
    outcomes = {key(row): row for row in outcome_rows}
    if set(v2_by_key) != set(gbv_by_key) or set(v2_by_key) != set(outcomes):
        raise RuntimeError("V2, GbV, and outcome ledgers must contain identical keys")

    v2_actions = {k: row["action"] for k, row in v2_by_key.items()}
    comparisons = {}
    for field in ("gbv_global_matched", "gbv_stratum_matched"):
        gbv_actions = {k: row[field] for k, row in gbv_by_key.items()}
        v2_metrics = selected_metrics(v2_actions, outcomes)
        gbv_metrics = selected_metrics(gbv_actions, outcomes)
        bootstrap = cluster_bootstrap(v2_actions, gbv_actions, outcomes)
        comparisons[field] = {
            "v2": v2_metrics,
            "gbv": gbv_metrics,
            "paired_cluster_bootstrap": bootstrap,
            "high_standard_targets": {
                "em_point_at_least_plus_0_60_pp": bootstrap["v2_minus_gbv_em_pp"]["point"] >= 0.60,
                "em_ci_lower_at_least_plus_0_30_pp": bootstrap["v2_minus_gbv_em_pp"]["ci95"][0] >= 0.30,
                "damage_count_not_higher": v2_metrics["damage"] <= gbv_metrics["damage"],
            },
        }

    dataset_points = {}
    for dataset in sorted({k[0] for k in outcomes}):
        subset = {k: v for k, v in outcomes.items() if k[0] == dataset}
        v2_subset = {k: v2_actions[k] for k in subset}
        gbv_subset = {
            k: gbv_by_key[k]["gbv_global_matched"] for k in subset
        }
        v2_em, _, _ = policy_values(v2_subset, subset)
        gbv_em, _, _ = policy_values(gbv_subset, subset)
        dataset_points[dataset] = 100.0 * sum(
            v2_em[k] - gbv_em[k] for k in subset
        ) / len(subset)

    result = {
        "status": "POST_SEAL_FRESH_EVALUATION",
        "input_hashes": {
            "v2_actions_sha256": sha256(args.v2_actions),
            "gbv_actions_sha256": sha256(args.gbv_actions),
            "outcomes_sha256": sha256(args.outcomes),
        },
        "comparisons": comparisons,
        "v2_minus_gbv_global_em_pp_by_dataset": dataset_points,
        "all_dataset_point_estimates_positive": all(
            value > 0 for value in dataset_points.values()
        ),
        "interpretation_guardrail": (
            "Superiority may be claimed only for a comparison whose predeclared paired interval "
            "and other success criteria are satisfied. Negative, tied, or inconclusive results "
            "must be retained."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
