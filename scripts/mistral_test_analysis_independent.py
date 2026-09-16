"""Independent explicit-copy audit for the frozen Mistral test analysis.

This module intentionally imports neither the producer arithmetic nor the
weighted top-K kernel.
"""
from collections import Counter
import json
import math

import numpy as np


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
SEED = 20260930
ADJUSTED_QUANTILES = (0.00625, 0.99375)
UNADJUSTED_QUANTILES = (0.025, 0.975)


def require(value, message):
    if not value:
        raise ValueError("Independent Mistral test analysis: " + message)


def identity(row):
    value = tuple(row.get(field) for field in ("dataset", "retriever", "sample_id"))
    require(all(type(item) is str and item for item in value), "nonempty identity")
    require(value[0] in DATASETS and value[1] in RETRIEVERS, "fixed stratum")
    return value


class IndependentPanel:
    def __init__(self, actions, outcomes, *, questions_per_dataset=2_000):
        require(type(questions_per_dataset) is int and questions_per_dataset > 0,
                "positive question count")
        actions = list(actions)
        outcomes = list(outcomes)
        action_schema = {
            "dataset", "retriever", "sample_id", "eligible", "scores",
            "actions", "forced_keep_reason",
        }
        outcome_schema = {
            "dataset", "retriever", "sample_id", "a0_em", "a1_em",
            "a0_f1", "a1_f1",
        }
        by_key = {}
        numeric = {}
        for row in actions:
            require(type(row) is dict and set(row) == action_schema,
                    "exact independent action schema")
            key = identity(row)
            require(key not in by_key, "unique independent action identity")
            require(type(row["eligible"]) is bool, "boolean eligibility")
            require(set(row["scores"]) == set(SCORED_POLICIES)
                    and set(row["actions"]) == set(POLICIES), "fixed policy schema")
            reason = row["forced_keep_reason"]
            require(reason is None if row["eligible"] else
                    type(reason) is str and bool(reason), "forced-Keep reason")
            for value in row["scores"].values():
                require((type(value) in (int, float) and math.isfinite(value))
                        if row["eligible"] else value is None,
                        "finite eligible and null ineligible scores")
            require(all(type(value) is str and value in {"KEEP", "REPLACE"}
                        for value in row["actions"].values()), "exact actions")
            by_key[key] = row
        for row in outcomes:
            require(type(row) is dict and set(row) == outcome_schema,
                    "exact independent numeric schema")
            key = identity(row)
            require(key not in numeric, "unique independent outcome identity")
            require(all(type(row[field]) is int and row[field] in (0, 1)
                        for field in ("a0_em", "a1_em")), "binary integer EM")
            require(all(type(row[field]) in (int, float)
                        and math.isfinite(row[field]) and 0 <= row[field] <= 1
                        for field in ("a0_f1", "a1_f1")), "bounded numeric F1")
            numeric[key] = row
        require(set(by_key) == set(numeric), "complete identity equality")

        self.keys = sorted(by_key)
        self.n = len(self.keys)
        self.q = questions_per_dataset
        require(self.n == 9 * self.q, "balanced independent trace population")
        self.groups = sorted({(dataset, sample_id)
                              for dataset, _, sample_id in self.keys})
        require(Counter(dataset for dataset, _ in self.groups)
                == Counter({dataset: self.q for dataset in DATASETS}),
                "balanced independent question strata")
        require(all(all((dataset, retriever, sample_id) in by_key
                        for retriever in RETRIEVERS)
                    for dataset, sample_id in self.groups),
                "complete independent retriever siblings")
        group_index = {group: index for index, group in enumerate(self.groups)}
        self.siblings = np.asarray(
            [group_index[(dataset, sample_id)]
             for dataset, _, sample_id in self.keys], dtype=np.int64
        )
        self.strata = [
            np.asarray([index for index, group in enumerate(self.groups)
                        if group[0] == dataset], dtype=np.int64)
            for dataset in DATASETS
        ]
        self.raw = [numeric[key] for key in self.keys]
        self.em0 = np.asarray([row["a0_em"] for row in self.raw], dtype=np.int64)
        self.em1 = np.asarray([row["a1_em"] for row in self.raw], dtype=np.int64)
        self.gain = self.em1 - self.em0
        self.damage = ((self.em0 == 1) & (self.em1 == 0)).astype(np.int64)
        self.recovery = ((self.em0 == 0) & (self.em1 == 1)).astype(np.int64)
        self.eligible = np.asarray([by_key[key]["eligible"] for key in self.keys],
                                   dtype=bool)
        self.scores = {
            policy: np.asarray([
                by_key[key]["scores"][policy] if by_key[key]["eligible"] else 0.0
                for key in self.keys
            ], dtype=np.float64)
            for policy in SCORED_POLICIES
        }
        self.actions = {
            policy: np.asarray([
                by_key[key]["actions"][policy] == "REPLACE" for key in self.keys
            ], dtype=bool)
            for policy in POLICIES
        }
        unit = np.ones(self.n, dtype=np.int64)
        for policy in POLICIES:
            copies = self.select_copies(policy, unit, fixed=False)
            observed = np.bincount(copies, minlength=self.n).astype(bool)
            require(np.array_equal(observed, self.actions[policy]),
                    "independent explicit-copy point actions")

    def select_copies(self, policy, weights, *, fixed):
        weights = np.asarray(weights)
        require(weights.dtype.kind in "iu" and weights.shape == (self.n,)
                and np.all(weights >= 0), "nonnegative row copy counts")
        copies = np.repeat(np.arange(self.n, dtype=np.int64), weights)
        if fixed:
            return copies[self.actions[policy][copies]]
        if policy == "Keep":
            return np.asarray([], dtype=np.int64)
        eligible = copies[self.eligible[copies]]
        positions = np.lexsort((eligible, -self.scores[policy][eligible]))
        cap = round(0.05 * len(copies))
        return eligible[positions[:cap]]

    def counts(self, *, draws=20_000, seed=SEED):
        require(type(draws) is int and draws > 0 and type(seed) is int,
                "fixed draw count and seed")
        generator = np.random.default_rng(seed)
        for _ in range(draws):
            counts = np.zeros(len(self.groups), dtype=np.int64)
            for stratum in self.strata:
                sample = generator.choice(stratum, size=self.q, replace=True)
                unique, multiplicity = np.unique(sample, return_counts=True)
                counts[unique] = multiplicity
            yield counts

    def draw(self, counts, draw):
        counts = np.asarray(counts)
        require(type(draw) is int and draw >= 0 and counts.dtype.kind in "iu"
                and counts.shape == (len(self.groups),) and np.all(counts >= 0)
                and np.all(counts <= self.q), "canonical question multiplicities")
        require([int(counts[stratum].sum()) for stratum in self.strata]
                == [self.q] * 3, "independent dataset draw sizes")
        weights = counts.astype(np.int64, copy=False)[self.siblings]
        count = int(weights.sum())
        result = {"draw": draw, "N_all": count, "cap": round(0.05 * count)}
        for mode in ("reallocated", "fixed_action"):
            totals = {}
            for policy in POLICIES:
                selected = self.select_copies(
                    policy, weights, fixed=mode == "fixed_action"
                )
                recovery = int(self.recovery[selected].sum())
                damage = int(self.damage[selected].sum())
                totals[policy] = {
                    "net": recovery - damage,
                    "damage": damage,
                    "replacements": len(selected),
                }
            result[mode] = {
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
        return result

    def point_cell(self, indices):
        require(bool(indices), "nonempty independent point cell")
        n = len(indices)
        baseline_em = sum(int(self.em0[index]) for index in indices)
        baseline_f1 = math.fsum(self.raw[index]["a0_f1"] for index in indices)
        output = {}
        for policy in POLICIES:
            changed = [index for index in indices if self.actions[policy][index]]
            recovery = sum(int(self.recovery[index]) for index in changed)
            damage = sum(int(self.damage[index]) for index in changed)
            final_em = [int(self.em1[index] if self.actions[policy][index]
                            else self.em0[index]) for index in indices]
            f1 = math.fsum(
                self.raw[index]["a1_f1" if self.actions[policy][index] else "a0_f1"]
                for index in indices
            )
            transitions = Counter(
                str(int(self.em0[index])) + str(value)
                for index, value in zip(indices, final_em)
            )
            output[policy] = {
                "N_all": n,
                "replacements": len(changed),
                "recovery": recovery,
                "damage": damage,
                "neutral": len(changed) - recovery - damage,
                "net": recovery - damage,
                "em_correct": sum(final_em),
                "em_rate": sum(final_em) / n,
                "token_f1": f1 / n,
                "delta_em_pp": 100.0 * (sum(final_em) - baseline_em) / n,
                "delta_f1_pp": 100.0 * (f1 - baseline_f1) / n,
                "damage_rate_pp": 100.0 * damage / n,
                "realized_em_transition_counts": {
                    item: transitions[item] for item in ("00", "01", "10", "11")
                },
            }
        return output

    @staticmethod
    def comparisons(rows, pairs):
        output = []
        for left, right in pairs:
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

    def overlap(self, indices, left, right):
        predicates = {
            "both": lambda l, r: l and r,
            "left_only": lambda l, r: l and not r,
            "right_only": lambda l, r: r and not l,
            "neither": lambda l, r: not l and not r,
        }
        output = {}
        for name, predicate in predicates.items():
            members = [index for index in indices
                       if predicate(bool(self.actions[left][index]),
                                    bool(self.actions[right][index]))]
            recovery = sum(int(self.recovery[index]) for index in members)
            damage = sum(int(self.damage[index]) for index in members)
            output[name] = {
                "rows": len(members),
                "potential_recovery": recovery,
                "potential_damage": damage,
                "potential_neutral": len(members) - recovery - damage,
            }
        return output

    def point(self):
        all_indices = list(range(self.n))
        overall = self.point_cell(all_indices)
        breakdown = {}
        for kind, labels in (
            ("dataset", DATASETS),
            ("retriever", RETRIEVERS),
            ("dataset_x_retriever", [(dataset, retriever)
                                     for dataset in DATASETS
                                     for retriever in RETRIEVERS]),
        ):
            cells = []
            for label in labels:
                indices = [index for index, key in enumerate(self.keys)
                           if (key[0] if kind == "dataset" else
                               key[1] if kind == "retriever" else key[:2])
                           == label]
                cells.append({"cell": label, "policies": self.point_cell(indices)})
            breakdown[kind] = cells
        overlaps = []
        for left, right in PRIMARY_COMPARISONS:
            cells = []
            for dataset in DATASETS:
                for retriever in RETRIEVERS:
                    indices = [index for index, key in enumerate(self.keys)
                               if key[:2] == (dataset, retriever)]
                    cells.append({
                        "cell": [dataset, retriever],
                        "categories": self.overlap(indices, left, right),
                    })
            overlaps.append({
                "left": left,
                "right": right,
                "overall": self.overlap(all_indices, left, right),
                "dataset_x_retriever": cells,
            })
        return {
            "N_all": self.n,
            "question_groups": len(self.groups),
            "N_eligible": int(self.eligible.sum()),
            "primary_global_cap": round(0.05 * self.n),
            "policies": overall,
            "primary_comparisons": self.comparisons(overall, PRIMARY_COMPARISONS),
            "fixed_recipe_comparisons": self.comparisons(overall, FIXED_COMPARISONS),
            "fixed_global_action_breakdowns": breakdown,
            "primary_action_overlaps": overlaps,
        }


def compare_report(actual, expected, *, field=None):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected),
                "complete report mapping schema")
        for name in expected:
            compare_report(actual[name], expected[name], field=name)
    elif isinstance(expected, (list, tuple)):
        require(isinstance(actual, (list, tuple)) and len(actual) == len(expected),
                "complete report sequence")
        for left, right in zip(actual, expected):
            compare_report(left, right, field=field)
    elif field in {"token_f1", "delta_f1_pp"}:
        require(type(actual) in (int, float) and math.isfinite(actual)
                and abs(actual - expected) <= 1e-15, "bounded F1 tolerance")
    else:
        require(type(actual) is type(expected) and actual == expected,
                "exact non-F1 report value")


def _reports(values, points, pairs, *, adjusted):
    ordinary = np.quantile(values, UNADJUSTED_QUANTILES, axis=0, method="linear")
    family = (np.quantile(values, ADJUSTED_QUANTILES, axis=0, method="linear")
              if adjusted else None)
    reports = []
    for i, (left, right) in enumerate(pairs):
        endpoints = {}
        for j, endpoint in enumerate(ENDPOINTS):
            row = {
                "point_pp": points[i][endpoint],
                "unadjusted_95_range_pp": ordinary[:, i, j].tolist(),
            }
            if adjusted:
                lower, upper = map(float, family[:, i, j])
                row["adjusted_percentile_range_pp"] = [lower, upper]
                row["adjusted_direction"] = (
                    "positive" if lower > 0 else
                    "negative" if upper < 0 else "inconclusive"
                )
            endpoints[endpoint] = row
        report = {"left": left, "right": right, "endpoints": endpoints}
        if adjusted:
            report["joint_em_improvement_and_damage_reduction"] = (
                endpoints[ENDPOINTS[0]]["adjusted_direction"] == "positive"
                and endpoints[ENDPOINTS[1]]["adjusted_direction"] == "negative"
            )
        reports.append(report)
    return reports


def independent_intervals(panel, records):
    records = list(records)
    require(bool(records) and all(row["draw"] == index
            and row["N_all"] == panel.n and row["cap"] == round(0.05 * panel.n)
            for index, row in enumerate(records)), "complete ordered draw records")
    points = panel.point()
    output = {
        "draws": len(records),
        "primary_interval_family_size": 4,
        "adjusted_quantiles": list(ADJUSTED_QUANTILES),
        "unadjusted_quantiles": list(UNADJUSTED_QUANTILES),
        "quantile_method": "linear",
        "denominator": panel.n,
        "bootstrap_seed": SEED,
    }
    for mode in ("reallocated", "fixed_action"):
        primary = np.asarray(
            [row[mode]["primary_event_differences"] for row in records],
            dtype=np.int64,
        ) * (100.0 / panel.n)
        fixed = np.asarray(
            [row[mode]["fixed_recipe_event_differences"] for row in records],
            dtype=np.int64,
        ) * (100.0 / panel.n)
        require(primary.shape == (len(records), 2, 2)
                and fixed.shape == (len(records), 2, 2), "exact draw arrays")
        output[mode] = {
            "primary_comparisons": _reports(
                primary, points["primary_comparisons"], PRIMARY_COMPARISONS,
                adjusted=True,
            ),
            "fixed_recipe_comparisons": _reports(
                fixed, points["fixed_recipe_comparisons"], FIXED_COMPARISONS,
                adjusted=False,
            ),
            "interval_role": ("primary_confirmatory" if mode == "reallocated"
                              else "secondary_fixed_action_sensitivity"),
            "fixed_recipe_role": "descriptive_outside_confirmatory_family",
        }
    return output


def validate_draw_files(panel, weights_path, receipts_path, *, draws=20_000,
                        seed=SEED, progress=None):
    width = len(panel.groups) * 2
    require(weights_path.stat().st_size == draws * width,
            "complete binary multiplicity file length")
    accepted = []
    with weights_path.open("rb") as weights, receipts_path.open(encoding="utf-8") as receipts:
        for index, expected_counts in enumerate(panel.counts(draws=draws, seed=seed)):
            raw = weights.read(width)
            require(len(raw) == width, "complete binary draw row")
            actual_counts = np.frombuffer(raw, dtype="<u2").astype(np.int64)
            require(np.array_equal(actual_counts, expected_counts),
                    "stored multiplicities match independent RNG")
            line = receipts.readline()
            require(bool(line.strip()) and line.endswith("\n"),
                    "complete newline-terminated receipt")
            observed = json.loads(line)
            expected = panel.draw(expected_counts, index)
            compare_report(observed, expected)
            accepted.append(observed)
            if progress is not None:
                progress(index + 1)
        require(weights.read(1) == b"", "no trailing multiplicity bytes")
        require(receipts.read() == "", "no trailing draw receipts")
    return accepted
