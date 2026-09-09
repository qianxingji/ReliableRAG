#!/usr/bin/env python3
"""Post-seal evaluation of DAA-V2, raw HGB, and Generate-but-Verify.

Run only after the combined pre-label gate has passed and a separate responsible-human
authorization has permitted numeric outcome mapping. No model/threshold/budget
selection occurs here.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

BOOTSTRAP_SEED = 20260920
BOOTSTRAP_DRAWS = 10000
HIGH_STANDARD_EM_POINT_PP = 0.60
HIGH_STANDARD_EM_LCB_PP = 0.30
HIGH_STANDARD_F1_POINT_PP = 0.50
STRETCH_DAMAGE_RATIO = 0.75


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


def selected_metrics(actions: dict, outcomes: dict) -> dict[str, float | int]:
    recovery = damage = replace = 0
    selected_em = selected_f1 = baseline_em = baseline_f1 = 0.0
    initially_correct = 0
    for k, outcome in outcomes.items():
        use_repair = actions[k] == "REPLACE"
        a0_em = int(outcome["a0_em"])
        a1_em = int(outcome["a1_em"])
        a0_f1 = float(outcome["a0_f1"])
        a1_f1 = float(outcome["a1_f1"])
        initially_correct += a0_em
        recovery += int(use_repair and a0_em == 0 and a1_em == 1)
        damage += int(use_repair and a0_em == 1 and a1_em == 0)
        replace += int(use_repair)
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
        "system_damage_percent": 100.0 * damage / initially_correct if initially_correct else 0.0,
        "action_recovery_percent": 100.0 * recovery / replace if replace else 0.0,
        "action_damage_percent": 100.0 * damage / replace if replace else 0.0,
    }


def policy_values(actions: dict, outcomes: dict):
    em, f1, damage = {}, {}, {}
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


def cluster_bootstrap(left_actions: dict, right_actions: dict, outcomes: dict) -> dict:
    left_em, left_f1, left_damage = policy_values(left_actions, outcomes)
    right_em, right_f1, right_damage = policy_values(right_actions, outcomes)

    cluster_rows: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    for k in outcomes:
        cluster_rows[(k[0], k[2])].append(k)
    clusters = sorted(cluster_rows)
    if not clusters:
        raise RuntimeError("no clusters available")

    per_cluster = []
    for cluster in clusters:
        rows = cluster_rows[cluster]
        per_cluster.append(
            (
                len(rows),
                sum(left_em[k] - right_em[k] for k in rows),
                sum(left_f1[k] - right_f1[k] for k in rows),
                sum(left_damage[k] - right_damage[k] for k in rows),
                sum(int(outcomes[k]["a0_em"]) for k in rows),
            )
        )

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
        initially_correct = selected[:, 4].sum()
        damage_samples[i] = (
            100.0 * selected[:, 3].sum() / initially_correct
            if initially_correct > 0
            else np.nan
        )

    def interval(samples: np.ndarray) -> list[float]:
        return [float(np.nanquantile(samples, 0.025)), float(np.nanquantile(samples, 0.975))]

    n = len(outcomes)
    initially_correct = sum(int(outcomes[k]["a0_em"]) for k in outcomes)
    return {
        "cluster_count": len(clusters),
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "resampling_unit": "dataset:sample_id cluster; all retriever rows retained",
        "left_minus_right_em_pp": {
            "point": 100.0 * sum(left_em[k] - right_em[k] for k in outcomes) / n,
            "ci95": interval(em_samples),
        },
        "left_minus_right_f1_pp": {
            "point": 100.0 * sum(left_f1[k] - right_f1[k] for k in outcomes) / n,
            "ci95": interval(f1_samples),
        },
        "left_minus_right_damage_pp": {
            "point": (
                100.0 * sum(left_damage[k] - right_damage[k] for k in outcomes) / initially_correct
                if initially_correct else float("nan")
            ),
            "ci95": interval(damage_samples),
        },
    }


def stratum_action_counts(actions: dict) -> Counter:
    return Counter((k[0], k[1]) for k, action in actions.items() if action == "REPLACE")


def subgroup_metrics(actions: dict, outcomes: dict, *, field: int) -> dict[str, dict]:
    result = {}
    for name in sorted({k[field] for k in outcomes}):
        subset = {k: outcome for k, outcome in outcomes.items() if k[field] == name}
        result[name] = selected_metrics({k: actions[k] for k in subset}, subset)
    return result


def subgroup_em_differences(left_actions: dict, right_actions: dict, outcomes: dict, *, field: int) -> dict[str, float]:
    points = {}
    for name in sorted({k[field] for k in outcomes}):
        subset = {k: outcome for k, outcome in outcomes.items() if k[field] == name}
        left_em, _, _ = policy_values({k: left_actions[k] for k in subset}, subset)
        right_em, _, _ = policy_values({k: right_actions[k] for k in subset}, subset)
        points[name] = 100.0 * sum(left_em[k] - right_em[k] for k in subset) / len(subset)
    return points


def compare(
    left_name: str,
    left_actions: dict,
    right_name: str,
    right_actions: dict,
    outcomes: dict,
) -> dict:
    left_metrics = selected_metrics(left_actions, outcomes)
    right_metrics = selected_metrics(right_actions, outcomes)
    bootstrap = cluster_bootstrap(left_actions, right_actions, outcomes)
    return {
        "left_method": left_name,
        "right_method": right_name,
        "left": left_metrics,
        "right": right_metrics,
        "paired_cluster_bootstrap": bootstrap,
        "left_minus_right_em_pp_by_dataset": subgroup_em_differences(left_actions, right_actions, outcomes, field=0),
        "left_minus_right_em_pp_by_retriever": subgroup_em_differences(left_actions, right_actions, outcomes, field=1),
        "left_metrics_by_retriever": subgroup_metrics(left_actions, outcomes, field=1),
        "right_metrics_by_retriever": subgroup_metrics(right_actions, outcomes, field=1),
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
    if len(v2_by_key) != len(v2_rows) or len(gbv_by_key) != len(gbv_rows) or len(outcomes) != len(outcome_rows):
        raise RuntimeError("duplicate keys in V2, GbV, or outcome ledger")
    if set(v2_by_key) != set(gbv_by_key) or set(v2_by_key) != set(outcomes):
        raise RuntimeError("V2, GbV, and outcome ledgers must contain identical keys")

    v2_actions = {k: row["action"] for k, row in v2_by_key.items()}
    hgb_actions = {k: row["hgb_action"] for k, row in v2_by_key.items()}
    v2_replace_count = sum(action == "REPLACE" for action in v2_actions.values())
    hgb_replace_count = sum(action == "REPLACE" for action in hgb_actions.values())
    if hgb_replace_count != v2_replace_count:
        raise RuntimeError("raw HGB ablation must exactly match V2 total action budget")
    v2_strata = stratum_action_counts(v2_actions)

    gbv_global = {k: row["gbv_global_matched"] for k, row in gbv_by_key.items()}
    gbv_stratum = {k: row["gbv_stratum_matched"] for k, row in gbv_by_key.items()}
    gbv_dev = {k: row["gbv_dev_selected"] for k, row in gbv_by_key.items()}

    if sum(value == "REPLACE" for value in gbv_global.values()) != v2_replace_count:
        raise RuntimeError("GbV global comparator does not match V2 total budget")
    if sum(value == "REPLACE" for value in gbv_stratum.values()) != v2_replace_count:
        raise RuntimeError("GbV stratum comparator does not match V2 total budget")
    if stratum_action_counts(gbv_stratum) != v2_strata:
        raise RuntimeError("GbV stratum comparator does not exactly match V2 strata")

    primary = compare("DAA-V2", v2_actions, "GbV-global-budget-matched", gbv_global, outcomes)
    primary_boot = primary["paired_cluster_bootstrap"]
    em_result = primary_boot["left_minus_right_em_pp"]
    f1_result = primary_boot["left_minus_right_f1_pp"]
    dataset_points = primary["left_minus_right_em_pp_by_dataset"]
    v2_retriever_metrics = primary["left_metrics_by_retriever"]
    v2_metrics = primary["left"]
    gbv_metrics = primary["right"]
    damage_ratio = (
        v2_metrics["damage"] / gbv_metrics["damage"]
        if gbv_metrics["damage"] > 0
        else (0.0 if v2_metrics["damage"] == 0 else float("inf"))
    )

    formal_primary = {
        "paired_em_superiority_ci_lower_gt_zero": em_result["ci95"][0] > 0.0
    }
    high_standard = {
        "em_point_at_least_plus_0_60_pp": em_result["point"] >= HIGH_STANDARD_EM_POINT_PP,
        "em_ci_lower_at_least_plus_0_30_pp": em_result["ci95"][0] >= HIGH_STANDARD_EM_LCB_PP,
        "f1_point_at_least_plus_0_50_pp": f1_result["point"] >= HIGH_STANDARD_F1_POINT_PP,
        "f1_ci_lower_gt_zero": f1_result["ci95"][0] > 0.0,
        "damage_count_not_higher": v2_metrics["damage"] <= gbv_metrics["damage"],
        "all_dataset_em_point_estimates_positive": all(value > 0.0 for value in dataset_points.values()),
        "all_v2_retrievers_positive_net": all(metrics["net"] > 0 for metrics in v2_retriever_metrics.values()),
    }
    stretch = {
        "damage_at_least_25_percent_lower": damage_ratio <= STRETCH_DAMAGE_RATIO,
        "all_retriever_v2_minus_gbv_em_points_positive": all(
            value > 0.0 for value in primary["left_minus_right_em_pp_by_retriever"].values()
        ),
    }
    primary.update(
        {
            "damage_count_ratio_v2_over_gbv": damage_ratio,
            "formal_primary_superiority": formal_primary,
            "high_standard_engineering_targets": high_standard,
            "high_standard_all_met": all(high_standard.values()),
            "stretch_targets": stretch,
            "stretch_all_met": all(stretch.values()),
        }
    )

    stratum_comparison = compare(
        "DAA-V2", v2_actions, "GbV-exact-stratum-budget-matched", gbv_stratum, outcomes
    )
    dev_comparison = compare(
        "DAA-V2", v2_actions, "GbV-historical-dev-selected", gbv_dev, outcomes
    )
    hgb_comparison = compare(
        "DAA-V2", v2_actions, "Raw-global-HGB-same-budget", hgb_actions, outcomes
    )

    dev_boot = dev_comparison["paired_cluster_bootstrap"]["left_minus_right_em_pp"]
    dev_comparison["stronger_published_operating_point_target"] = {
        "v2_em_point_higher": dev_boot["point"] > 0.0,
        "v2_em_ci_lower_gt_zero": dev_boot["ci95"][0] > 0.0,
        "v2_damage_not_higher": dev_comparison["left"]["damage"] <= dev_comparison["right"]["damage"],
        "v2_uses_no_more_actions": dev_comparison["left"]["replace"] <= dev_comparison["right"]["replace"],
    }
    dev_comparison["stronger_target_all_met"] = all(
        dev_comparison["stronger_published_operating_point_target"].values()
    )

    hgb_boot = hgb_comparison["paired_cluster_bootstrap"]["left_minus_right_em_pp"]
    hgb_comparison["backbone_increment_target"] = {
        "v2_em_point_higher": hgb_boot["point"] > 0.0,
        "v2_em_ci_lower_gt_zero": hgb_boot["ci95"][0] > 0.0,
        "v2_damage_not_higher": hgb_comparison["left"]["damage"] <= hgb_comparison["right"]["damage"],
    }

    result = {
        "status": "POST_SEAL_FRESH_EVALUATION",
        "input_hashes": {
            "v2_actions_sha256": sha256(args.v2_actions),
            "gbv_actions_sha256": sha256(args.gbv_actions),
            "outcomes_sha256": sha256(args.outcomes),
        },
        "bootstrap": {"draws": BOOTSTRAP_DRAWS, "seed": BOOTSTRAP_SEED},
        "predeclared_high_standard_thresholds": {
            "em_point_pp": HIGH_STANDARD_EM_POINT_PP,
            "em_ci_lower_pp": HIGH_STANDARD_EM_LCB_PP,
            "f1_point_pp": HIGH_STANDARD_F1_POINT_PP,
            "stretch_damage_ratio": STRETCH_DAMAGE_RATIO,
        },
        "primary_same_total_budget": primary,
        "secondary_exact_stratum_budget": stratum_comparison,
        "secondary_gbv_historical_dev_selected": dev_comparison,
        "key_ablation_v2_vs_raw_hgb": hgb_comparison,
        "interpretation_guardrail": (
            "The same-total-budget GbV comparison is the formal primary published-method contrast. "
            "The exact-stratum, historical-dev-selected GbV, and raw-HGB comparisons are predeclared "
            "secondary/key-ablation evidence. Stronger multi-condition targets are engineering goals, "
            "not familywise-controlled tests. Negative, tied, or inconclusive results must be retained."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
