"""Independent explicit-copy D analysis; no executor or weighted-kernel import."""
import math
from collections import Counter
import json

import numpy as np

from scripts.empirical_neural_checks import Checks

DATASETS = ("2wikimultihopqa", "hotpotqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
POLICIES = ("Keep", "HGB", "GbV", "ROA-FULL", "ROA-NOGBV", "HGB_GBV_R", "HGB_ONLY_R", "GBV_ONLY_R", "V2")
PAIRS = (("ROA-FULL", "HGB_GBV_R"), ("HGB_GBV_R", "HGB_ONLY_R"), ("HGB_GBV_R", "GBV_ONLY_R"))
ENDPOINTS = ("em_difference_pp", "damage_rate_difference_pp")


def key(row):
    return row["dataset"], row["retriever"], row["sample_id"]


class IndependentPanel:
    def __init__(self, actions, outcomes, *, questions_per_dataset=2000):
        self.audit = Checks()
        a = self.audit
        actions, outcomes = list(actions), list(outcomes)
        keys = sorted(key(r) for r in actions)
        a.require(len(set(keys)) == len(keys) == 9 * questions_per_dataset, "independent unique balanced action population")
        a.exact(sorted(key(r) for r in outcomes), keys, "independent complete numeric population")
        a.require(all(all(type(v) is str and v for v in k) and k[0] in DATASETS and k[1] in RETRIEVERS for k in keys), "independent canonical identities")
        bykey, numeric = {key(r): r for r in actions}, {key(r): r for r in outcomes}
        self.keys, self.n, self.q = keys, len(keys), questions_per_dataset
        self.groups = sorted({(ds, sid) for ds, _, sid in keys})
        a.exact(sorted(Counter(ds for ds, _ in self.groups).items()), [(d, questions_per_dataset) for d in DATASETS], "independent question strata")
        for ds, sid in self.groups:
            a.require(all((ds, r, sid) in bykey for r in RETRIEVERS), "independent complete sibling set")
        group_index = {k: i for i, k in enumerate(self.groups)}
        self.siblings = np.array([group_index[(ds, sid)] for ds, _, sid in keys], dtype=np.int64)
        self.strata = [np.array([i for i, g in enumerate(self.groups) if g[0] == ds], dtype=np.int64) for ds in DATASETS]
        self.raw = [numeric[k] for k in keys]
        for row in self.raw:
            a.schema(row, {"dataset", "retriever", "sample_id", "a0_em", "a1_em", "a0_f1", "a1_f1"}, "independent numeric schema")
            for field in ("a0_em", "a1_em"):
                a.require(type(row[field]) is int and row[field] in (0, 1), "independent exact binary outcome")
            for field in ("a0_f1", "a1_f1"):
                a.finite(row[field], "independent finite F1")
                a.require(0 <= row[field] <= 1, "independent F1 domain")
        self.em0 = np.array([r["a0_em"] for r in self.raw], dtype=np.int64)
        self.em1 = np.array([r["a1_em"] for r in self.raw], dtype=np.int64)
        self.eligible = np.array([bykey[k]["eligible"] for k in keys])
        a.require(self.eligible.dtype == np.bool_, "independent boolean common mask")
        self.scores, self.actions = {}, {}
        for row in actions:
            a.schema(row, {"dataset", "retriever", "sample_id", "eligible", "scores", "actions", "forced_keep_reason"}, "independent prelabel schema")
            a.schema(row["scores"], POLICIES[1:], "independent fixed score names")
            a.schema(row["actions"], POLICIES, "independent fixed action names")
            a.require((row["forced_keep_reason"] is None) if row["eligible"] else
                (type(row["forced_keep_reason"]) is str and bool(row["forced_keep_reason"])), "independent mask reason")
            for value in row["actions"].values():
                a.require(type(value) is str and value in {"KEEP", "REPLACE"}, "independent exact action string")
            for value in row["scores"].values():
                if row["eligible"]:
                    a.finite(value, "independent finite eligible score")
                else:
                    a.exact(value, None, "independent common null score")
        for policy in POLICIES:
            self.actions[policy] = np.array([bykey[k]["actions"][policy] == "REPLACE" for k in keys])
            if policy != "Keep":
                self.scores[policy] = np.array([bykey[k]["scores"][policy] if bykey[k]["eligible"] else 0. for k in keys], dtype=np.float64)
        unit = np.ones(self.n, dtype=np.int64)
        for policy in POLICIES:
            copies = self.select_copies(policy, unit, fixed=False)
            a.exact(np.bincount(copies, minlength=self.n).tolist(), self.actions[policy].astype(int).tolist(), "independent exact sealed point actions")

    def select_copies(self, policy, weights, *, fixed):
        """Expand the actual row copies, independently sort, then take the cap."""
        self.audit.require(weights.dtype.kind in "iu" and weights.shape == (self.n,) and np.all(weights >= 0), "independent nonnegative copy counts")
        copies = np.repeat(np.arange(self.n, dtype=np.int64), weights)
        if fixed:
            return copies[self.actions[policy][copies]]
        if policy == "Keep":
            return np.array([], dtype=np.int64)
        eligible = copies[self.eligible[copies]]
        # Stable lexsort preserves identical copy order. Canonical key order is
        # represented by the independently sorted original row index.
        positions = np.lexsort((eligible, -self.scores[policy][eligible]))
        cap = round(.05 * len(copies))
        return eligible[positions[:cap]]

    def draw(self, counts, draw):
        counts = np.asarray(counts)
        a = self.audit
        a.require(counts.shape == (len(self.groups),) and counts.dtype.kind in "iu" and np.all(counts >= 0) and np.all(counts <= self.q), "independent group multiplicities")
        a.exact([int(counts[s].sum()) for s in self.strata], [self.q] * 3, "independent stratified draw size")
        weights = counts.astype(np.int64, copy=False)[self.siblings]
        result = dict(draw=draw, N_all=int(weights.sum()), cap=round(.05 * int(weights.sum())))
        for mode in ("reallocated", "fixed_action"):
            totals = {}
            for policy in POLICIES:
                selected = self.select_copies(policy, weights, fixed=mode == "fixed_action")
                before, after = self.em0[selected], self.em1[selected]
                recovery = int(np.count_nonzero((before == 0) & (after == 1)))
                damage = int(np.count_nonzero((before == 1) & (after == 0)))
                totals[policy] = dict(net=recovery-damage, damage=damage, replacements=len(selected))
            result[mode] = dict(policy_totals=totals, paired_event_differences=[[totals[left][f] - totals[right][f]
                for f in ("net", "damage")] for left, right in PAIRS])
        return result

    def counts(self, *, draws=20000, seed=20260926):
        generator = np.random.default_rng(seed)
        for _ in range(draws):
            counts = np.zeros(len(self.groups), dtype=np.int64)
            for indices in self.strata:
                sample = generator.choice(indices, size=self.q, replace=True)
                unique, multiplicity = np.unique(sample, return_counts=True)
                counts[unique] = multiplicity
            yield counts

    def point_cell(self, indices):
        a = self.audit
        a.require(bool(indices), "independent nonempty fixed cell")
        n = len(indices)
        baseline = sum(self.raw[i]["a0_em"] for i in indices)
        baseline_f1 = math.fsum(self.raw[i]["a0_f1"] for i in indices)
        summaries = {}
        for policy in POLICIES:
            changes = [i for i in indices if self.actions[policy][i]]
            r = sum(self.raw[i]["a0_em"] == 0 and self.raw[i]["a1_em"] == 1 for i in changes)
            d = sum(self.raw[i]["a0_em"] == 1 and self.raw[i]["a1_em"] == 0 for i in changes)
            final_em = [self.raw[i]["a1_em" if self.actions[policy][i] else "a0_em"] for i in indices]
            f1_sum = math.fsum(self.raw[i]["a1_f1" if self.actions[policy][i] else "a0_f1"] for i in indices)
            transitions = Counter(str(self.raw[i]["a0_em"]) + str(em) for i, em in zip(indices, final_em))
            summaries[policy] = dict(N_all=n, replacements=len(changes), recovery=r, damage=d, neutral=len(changes)-r-d,
                net=r-d, em_correct=sum(final_em), em_rate=sum(final_em)/n, token_f1=f1_sum/n,
                delta_em_pp=100.*(sum(final_em)-baseline)/n, delta_f1_pp=100.*(f1_sum-baseline_f1)/n,
                damage_rate_pp=100.*d/n, realized_em_transition_counts={x: transitions[x] for x in ("00", "01", "10", "11")})
        return summaries

    def point(self):
        overall = self.point_cell(list(range(self.n)))
        cells = {}
        for kind in ("dataset", "retriever", "dataset_x_retriever"):
            labels = DATASETS if kind == "dataset" else RETRIEVERS if kind == "retriever" else [(d, r) for d in DATASETS for r in RETRIEVERS]
            reports = []
            for label in labels:
                members = [i for i, k in enumerate(self.keys) if (k[0] if kind == "dataset" else k[1] if kind == "retriever" else k[:2]) == label]
                reports.append(dict(cell=label, policies=self.point_cell(members)))
            cells[kind] = reports
        comparisons = []
        for left, right in PAIRS:
            differences = [overall[left][f]-overall[right][f] for f in ("net", "damage")]
            comparisons.append(dict(left=left, right=right, event_differences=differences,
                **{name: 100.*value/self.n for name, value in zip(ENDPOINTS, differences)}))
        return dict(N_all=self.n, question_groups=len(self.groups), N_eligible=int(self.eligible.sum()), primary_global_cap=round(.05*self.n),
            policies=overall, comparisons=comparisons, fixed_global_action_breakdowns=cells)


def compare_report(actual, expected, audit, field=None):
    """Only F1 aggregates use tolerance; actions, integers and other floats exact."""
    if isinstance(expected, dict):
        audit.schema(actual, expected, "independent complete report schema")
        for name in expected:
            compare_report(actual[name], expected[name], audit, name)
    elif isinstance(expected, (list, tuple)):
        audit.require(isinstance(actual, (list, tuple)) and len(actual) == len(expected), "independent complete report sequence")
        for x, y in zip(actual, expected):
            compare_report(x, y, audit, field)
    elif field in {"token_f1", "delta_f1_pp"}:
        audit.finite(actual, "independent finite F1 summary")
        audit.require(abs(actual-expected) <= 1e-15, "independent F1 aggregate bound")
    else:
        audit.exact(actual, expected, "independent exact integer/action/EM/report value")


def independent_intervals(panel, draws):
    """Quantiles from independently checked integer event receipts."""
    point = panel.point()["comparisons"]
    result = dict(draws=len(draws), interval_family_size=6, adjusted_quantiles=[.05/12,1-.05/12],
        unadjusted_quantiles=[.025,.975], quantile_method="linear", denominator=panel.n)
    for mode in ("reallocated", "fixed_action"):
        comparisons = []
        for i, (left, right) in enumerate(PAIRS):
            endpoints = {}
            for j, endpoint in enumerate(ENDPOINTS):
                values = np.asarray([r[mode]["paired_event_differences"][i][j] for r in draws], dtype=np.int64) * (100./panel.n)
                bounds = np.quantile(values, [.05/12,1-.05/12], method="linear").tolist()
                ordinary = np.quantile(values, [.025,.975], method="linear").tolist()
                label = "inconclusive"
                if min(bounds) > 0: label = "positive"
                if max(bounds) < 0: label = "negative"
                endpoints[endpoint] = dict(point_pp=point[i][endpoint], adjusted_percentile_range_pp=bounds,
                    secondary_unadjusted_95_range_pp=ordinary, adjusted_direction=label)
            joint = endpoints[ENDPOINTS[0]]["adjusted_percentile_range_pp"][0] > 0 and endpoints[ENDPOINTS[1]]["adjusted_percentile_range_pp"][1] < 0
            comparisons.append(dict(left=left, right=right, endpoints=endpoints, joint_em_improvement_and_damage_reduction=joint))
        result[mode] = dict(comparisons=comparisons, interval_role="primary" if mode == "reallocated" else "secondary_sensitivity_same_draws")
    return result


def validate_draw_files(panel, weights_path, receipts_path, *, draws=20000, seed=20260926, progress=None):
    """Recreate every RNG draw and explicitly rank every policy's replicated rows."""
    a = panel.audit
    width = len(panel.groups) * 2
    a.exact(weights_path.stat().st_size, draws * width, "complete binary bootstrap file length")
    accepted = []
    with weights_path.open("rb") as weights, receipts_path.open(encoding="utf-8") as receipts:
        for index, expected_counts in enumerate(panel.counts(draws=draws, seed=seed)):
            raw = weights.read(width)
            a.exact(len(raw), width, "complete binary question-weight row")
            actual_counts = np.frombuffer(raw, dtype="<u2").astype(np.int64)
            a.require(np.array_equal(actual_counts, expected_counts), "every stored group multiplicity matches fixed RNG")
            line = receipts.readline()
            a.require(bool(line.strip()) and line.endswith("\n"), "complete nonblank draw receipt")
            observed = json.loads(line)
            expected = panel.draw(expected_counts, index)
            compare_report(observed, expected, a)
            accepted.append(observed)
            if progress is not None:
                progress(index + 1)
        a.require(weights.read(1) == b"", "no extra bootstrap multiplicity bytes")
        a.exact(receipts.read(), "", "no extra bootstrap draw receipts")
    return accepted
