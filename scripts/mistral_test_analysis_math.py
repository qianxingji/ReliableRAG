"""Frozen Mistral test arithmetic on numeric rows and sealed actions only.

This module opens no files, fits no model and grants no outcome access. Callers
must authenticate and independently accept the action and numeric-outcome rows.
"""
from collections import Counter
import math

import numpy as np

from src.evaluation.batch_allocation import weighted_top_k


DATASETS = ("2wikimultihopqa", "hotpotqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
PRIMARY_POLICIES = ("HGB_GBV_R", "HGB_ONLY_R", "GBV_ONLY_R")
FIXED_POLICIES = tuple(name + "_FIXED_C1" for name in PRIMARY_POLICIES)
SCORED_POLICIES = PRIMARY_POLICIES + FIXED_POLICIES
POLICIES = ("Keep",) + SCORED_POLICIES
PRIMARY_COMPARISONS = (
    ("HGB_GBV_R", "HGB_ONLY_R"),
    ("HGB_GBV_R", "GBV_ONLY_R"),
)
FIXED_COMPARISONS = (
    ("HGB_GBV_R_FIXED_C1", "HGB_ONLY_R_FIXED_C1"),
    ("HGB_GBV_R_FIXED_C1", "GBV_ONLY_R_FIXED_C1"),
)
ENDPOINTS = ("em_difference_pp", "damage_rate_difference_pp")
KEY_FIELDS = ("dataset", "retriever", "sample_id")
SEED = 20260930
DRAWS = 20_000
ADJUSTED_QUANTILES = (0.00625, 0.99375)
UNADJUSTED_QUANTILES = (0.025, 0.975)


def require(value, message):
    if not value:
        raise ValueError("Frozen Mistral test analysis: " + message)


def key(row):
    require(all(type(row.get(field)) is str and row[field] for field in KEY_FIELDS),
            "nonempty exact identity strings")
    value = tuple(row[field] for field in KEY_FIELDS)
    require(value[0] in DATASETS and value[1] in RETRIEVERS,
            "fixed dataset/retriever strata")
    return value


class Panel:
    """Validate complete sealed numeric rows; small populations are toy tests."""

    def __init__(self, actions, outcomes, *, questions_per_dataset=2_000):
        require(type(questions_per_dataset) is int and questions_per_dataset > 0,
                "positive fixed question count")
        action_rows = {}
        outcome_rows = {}
        action_schema = set(KEY_FIELDS) | {
            "eligible", "scores", "actions", "forced_keep_reason"
        }
        outcome_schema = set(KEY_FIELDS) | {"a0_em", "a1_em", "a0_f1", "a1_f1"}
        for row in actions:
            require(type(row) is dict and set(row) == action_schema,
                    "exact sealed-action row schema")
            identity = key(row)
            require(identity not in action_rows, "unique action identity")
            require(type(row["eligible"]) is bool, "boolean common eligibility")
            require(set(row["scores"]) == set(SCORED_POLICIES)
                    and set(row["actions"]) == set(POLICIES),
                    "fixed selected/fixed policy schema")
            reason = row["forced_keep_reason"]
            require(reason is None if row["eligible"] else
                    type(reason) is str and bool(reason),
                    "complete common forced-Keep reason")
            for value in row["scores"].values():
                valid = (type(value) in (int, float) and math.isfinite(value))
                require(valid if row["eligible"] else value is None,
                        "finite eligible score and null ineligible score")
            require(all(type(value) is str and value in {"KEEP", "REPLACE"}
                        for value in row["actions"].values()),
                    "exact action values")
            action_rows[identity] = row
        for row in outcomes:
            require(type(row) is dict and set(row) == outcome_schema,
                    "numeric-only outcome schema")
            identity = key(row)
            require(identity not in outcome_rows, "unique outcome identity")
            for field in ("a0_em", "a1_em"):
                require(type(row[field]) is int and row[field] in (0, 1),
                        "binary integer EM")
            for field in ("a0_f1", "a1_f1"):
                require(type(row[field]) in (int, float)
                        and math.isfinite(row[field]) and 0 <= row[field] <= 1,
                        "finite bounded token F1")
            outcome_rows[identity] = row
        require(set(action_rows) == set(outcome_rows),
                "complete action/outcome identity equality")

        self.keys = sorted(action_rows)
        self.n = len(self.keys)
        self.questions_per_dataset = questions_per_dataset
        require(self.n == 9 * questions_per_dataset,
                "complete balanced test trace population")
        self.groups = sorted({(identity[0], identity[2]) for identity in self.keys})
        require(Counter(ds for ds, _ in self.groups)
                == Counter({dataset: questions_per_dataset for dataset in DATASETS}),
                "balanced dataset question groups")
        require(Counter((identity[0], identity[2]) for identity in self.keys)
                == Counter({group: 3 for group in self.groups}),
                "three retriever siblings per question")
        group_index = {group: index for index, group in enumerate(self.groups)}
        self.siblings = np.asarray(
            [group_index[(identity[0], identity[2])] for identity in self.keys],
            dtype=np.int64,
        )
        self.strata = [
            np.asarray([i for i, group in enumerate(self.groups)
                        if group[0] == dataset], dtype=np.int64)
            for dataset in DATASETS
        ]
        self.outcomes = [outcome_rows[identity] for identity in self.keys]
        self.em = np.asarray(
            [[row["a0_em"], row["a1_em"]] for row in self.outcomes],
            dtype=np.int64,
        )
        self.gain = self.em[:, 1] - self.em[:, 0]
        self.damage = ((self.em[:, 0] == 1) & (self.em[:, 1] == 0)).astype(np.int64)
        self.recovery = ((self.em[:, 0] == 0) & (self.em[:, 1] == 1)).astype(np.int64)
        self.cap = round(0.05 * self.n)
        self.eligible = np.asarray(
            [action_rows[identity]["eligible"] for identity in self.keys], dtype=bool
        )
        self.eligible_count = int(self.eligible.sum())
        eligible_indices = np.flatnonzero(self.eligible)
        unit_weights = np.ones(self.n, dtype=np.int64)
        self.actions = {"Keep": np.zeros(self.n, dtype=np.int64)}
        self.orders = {"Keep": np.asarray([], dtype=np.int64)}
        for policy in SCORED_POLICIES:
            actual = np.asarray(
                [int(action_rows[identity]["actions"][policy] == "REPLACE")
                 for identity in self.keys], dtype=np.int64
            )
            order = np.asarray(sorted(
                eligible_indices,
                key=lambda index: (
                    -action_rows[self.keys[index]]["scores"][policy],
                    self.keys[index],
                ),
            ), dtype=np.int64)
            expected = weighted_top_k(order, unit_weights, self.cap)
            require(np.array_equal(actual, expected),
                    "sealed actions match global score/canonical allocation")
            self.actions[policy] = actual
            self.orders[policy] = order
        require(not np.any([
            action_rows[identity]["actions"]["Keep"] != "KEEP"
            for identity in self.keys
        ]), "Keep policy never replaces")


def _point(panel, indices):
    require(bool(indices), "nonempty analysis cell")
    n = len(indices)
    before_em = sum(int(panel.em[index, 0]) for index in indices)
    before_f1 = math.fsum(panel.outcomes[index]["a0_f1"] for index in indices)
    result = {}
    for policy in POLICIES:
        selected = panel.actions[policy]
        changed = [index for index in indices if selected[index]]
        recovery = sum(int(panel.recovery[index]) for index in changed)
        damage = sum(int(panel.damage[index]) for index in changed)
        after_em = sum(int(panel.em[index, int(selected[index])]) for index in indices)
        after_f1 = math.fsum(
            panel.outcomes[index]["a1_f1" if selected[index] else "a0_f1"]
            for index in indices
        )
        transitions = {
            before + after: sum(
                int(panel.em[index, 0]) == int(before)
                and int(panel.em[index, int(selected[index])]) == int(after)
                for index in indices
            )
            for before in "01" for after in "01"
        }
        result[policy] = {
            "N_all": n,
            "replacements": len(changed),
            "recovery": int(recovery),
            "damage": int(damage),
            "neutral": int(len(changed) - recovery - damage),
            "net": int(recovery - damage),
            "em_correct": int(after_em),
            "em_rate": after_em / n,
            "token_f1": after_f1 / n,
            "delta_em_pp": 100.0 * (after_em - before_em) / n,
            "delta_f1_pp": 100.0 * (after_f1 - before_f1) / n,
            "damage_rate_pp": 100.0 * damage / n,
            "realized_em_transition_counts": transitions,
        }
    return result


def _comparisons(rows, comparisons):
    output = []
    for left, right in comparisons:
        net = rows[left]["net"] - rows[right]["net"]
        damage = rows[left]["damage"] - rows[right]["damage"]
        output.append({
            "left": left,
            "right": right,
            "event_differences": [net, damage],
            "em_difference_pp": 100.0 * net / rows[left]["N_all"],
            "damage_rate_difference_pp": 100.0 * damage / rows[left]["N_all"],
        })
    return output


def _overlap(panel, indices, left, right):
    categories = {
        "both": lambda l, r: l and r,
        "left_only": lambda l, r: l and not r,
        "right_only": lambda l, r: r and not l,
        "neither": lambda l, r: not l and not r,
    }
    output = {}
    for name, predicate in categories.items():
        members = [index for index in indices
                   if predicate(bool(panel.actions[left][index]),
                                bool(panel.actions[right][index]))]
        recovery = sum(int(panel.recovery[index]) for index in members)
        damage = sum(int(panel.damage[index]) for index in members)
        output[name] = {
            "rows": len(members),
            "potential_recovery": recovery,
            "potential_damage": damage,
            "potential_neutral": len(members) - recovery - damage,
        }
    return output


def point_estimates(panel):
    overall = _point(panel, list(range(panel.n)))
    breakdown = {}
    for kind, labels in (
        ("dataset", DATASETS),
        ("retriever", RETRIEVERS),
        ("dataset_x_retriever", [(dataset, retriever)
                                 for dataset in DATASETS for retriever in RETRIEVERS]),
    ):
        cells = []
        for label in labels:
            indices = [index for index, identity in enumerate(panel.keys)
                       if (identity[0] if kind == "dataset" else
                           identity[1] if kind == "retriever" else identity[:2])
                       == label]
            cells.append({"cell": label, "policies": _point(panel, indices)})
        breakdown[kind] = cells
    overlaps = []
    for left, right in PRIMARY_COMPARISONS:
        cells = []
        for dataset in DATASETS:
            for retriever in RETRIEVERS:
                indices = [index for index, identity in enumerate(panel.keys)
                           if identity[:2] == (dataset, retriever)]
                cells.append({
                    "cell": [dataset, retriever],
                    "categories": _overlap(panel, indices, left, right),
                })
        overlaps.append({
            "left": left,
            "right": right,
            "overall": _overlap(panel, list(range(panel.n)), left, right),
            "dataset_x_retriever": cells,
        })
    return {
        "N_all": panel.n,
        "question_groups": len(panel.groups),
        "N_eligible": panel.eligible_count,
        "primary_global_cap": panel.cap,
        "policies": overall,
        "primary_comparisons": _comparisons(overall, PRIMARY_COMPARISONS),
        "fixed_recipe_comparisons": _comparisons(overall, FIXED_COMPARISONS),
        "fixed_global_action_breakdowns": breakdown,
        "primary_action_overlaps": overlaps,
    }


def question_weights(panel, *, draws=DRAWS, seed=SEED):
    require(type(draws) is int and draws > 0 and type(seed) is int,
            "fixed positive draw count and integer seed")
    generator = np.random.default_rng(seed)
    for _ in range(draws):
        weights = np.zeros(len(panel.groups), dtype=np.int64)
        for stratum in panel.strata:
            sampled = generator.choice(
                stratum, size=panel.questions_per_dataset, replace=True
            )
            weights += np.bincount(sampled, minlength=len(panel.groups))
        yield weights


def draw_record(panel, weights, draw):
    weights = np.asarray(weights)
    require(type(draw) is int and draw >= 0 and weights.ndim == 1
            and weights.dtype.kind in "iu" and len(weights) == len(panel.groups)
            and np.all(weights >= 0)
            and np.all(weights <= panel.questions_per_dataset),
            "canonical nonnegative integer question multiplicities")
    require(all(int(weights[stratum].sum()) == panel.questions_per_dataset
                for stratum in panel.strata),
            "every draw preserves each dataset question count")
    row_weights = weights.astype(np.int64, copy=False)[panel.siblings]
    count = int(row_weights.sum())
    require(count == panel.n, "all siblings and forced-Keep rows stay in denominator")
    cap = round(0.05 * count)
    analyses = {}
    for mode in ("reallocated", "fixed_action"):
        totals = {}
        for policy in POLICIES:
            chosen = (weighted_top_k(panel.orders[policy], row_weights, cap)
                      if mode == "reallocated"
                      else panel.actions[policy] * row_weights)
            totals[policy] = {
                "net": int(chosen @ panel.gain),
                "damage": int(chosen @ panel.damage),
                "replacements": int(chosen.sum()),
            }
        analyses[mode] = {
            "policy_totals": totals,
            "primary_event_differences": [
                [totals[left][field] - totals[right][field]
                 for field in ("net", "damage")]
                for left, right in PRIMARY_COMPARISONS
            ],
            "fixed_recipe_event_differences": [
                [totals[left][field] - totals[right][field]
                 for field in ("net", "damage")]
                for left, right in FIXED_COMPARISONS
            ],
        }
    return {"draw": draw, "N_all": count, "cap": cap, **analyses}


def _endpoint_reports(values, point, *, adjusted):
    ordinary = np.quantile(values, UNADJUSTED_QUANTILES, axis=0, method="linear")
    reports = []
    adjusted_values = (np.quantile(values, ADJUSTED_QUANTILES, axis=0,
                                   method="linear") if adjusted else None)
    for comparison_index, (left, right) in enumerate(
        PRIMARY_COMPARISONS if adjusted else FIXED_COMPARISONS
    ):
        endpoints = {}
        for endpoint_index, endpoint in enumerate(ENDPOINTS):
            row = {
                "point_pp": point[comparison_index][endpoint],
                "unadjusted_95_range_pp": ordinary[:, comparison_index,
                                                    endpoint_index].tolist(),
            }
            if adjusted:
                lower, upper = map(float, adjusted_values[:, comparison_index,
                                                         endpoint_index])
                direction = ("positive" if lower > 0 else
                             "negative" if upper < 0 else "inconclusive")
                row.update({
                    "adjusted_percentile_range_pp": [lower, upper],
                    "adjusted_direction": direction,
                })
            endpoints[endpoint] = row
        report = {"left": left, "right": right, "endpoints": endpoints}
        if adjusted:
            em = endpoints[ENDPOINTS[0]]["adjusted_direction"]
            damage = endpoints[ENDPOINTS[1]]["adjusted_direction"]
            report["joint_em_improvement_and_damage_reduction"] = (
                em == "positive" and damage == "negative"
            )
        reports.append(report)
    return reports


def intervals(panel, records):
    records = list(records)
    require(bool(records) and all(
        row["draw"] == index and row["N_all"] == panel.n
        and row["cap"] == panel.cap for index, row in enumerate(records)
    ), "complete ordered draw records")
    points = point_estimates(panel)
    result = {
        "draws": len(records),
        "primary_interval_family_size": 4,
        "adjusted_quantiles": list(ADJUSTED_QUANTILES),
        "unadjusted_quantiles": list(UNADJUSTED_QUANTILES),
        "quantile_method": "linear",
        "denominator": panel.n,
        "bootstrap_seed": SEED,
    }
    for mode in ("reallocated", "fixed_action"):
        primary_counts = np.asarray(
            [row[mode]["primary_event_differences"] for row in records],
            dtype=np.int64,
        )
        fixed_counts = np.asarray(
            [row[mode]["fixed_recipe_event_differences"] for row in records],
            dtype=np.int64,
        )
        require(primary_counts.shape == (len(records), 2, 2)
                and fixed_counts.shape == (len(records), 2, 2),
                "exact two-comparison by two-endpoint draw arrays")
        scale = 100.0 / panel.n
        result[mode] = {
            "primary_comparisons": _endpoint_reports(
                primary_counts * scale,
                points["primary_comparisons"],
                adjusted=True,
            ),
            "fixed_recipe_comparisons": _endpoint_reports(
                fixed_counts * scale,
                points["fixed_recipe_comparisons"],
                adjusted=False,
            ),
            "interval_role": ("primary_confirmatory" if mode == "reallocated"
                              else "secondary_fixed_action_sensitivity"),
            "fixed_recipe_role": "descriptive_outside_confirmatory_family",
        }
    return result
