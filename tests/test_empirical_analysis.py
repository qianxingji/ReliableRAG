"""Frozen D tests on invented numeric outcomes; no benchmark or model loading."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from scripts.empirical_analysis_math import Panel, point_estimates, question_weights, draw_record, intervals
from scripts.empirical_analysis_independent import IndependentPanel, independent_intervals, compare_report, validate_draw_files
from scripts.empirical_analysis_storage import BootstrapWriter
from scripts.empirical_policy_actions import allocate, POLICIES
from scripts.empirical_neural_checks import Checks


def fixture(*, eligible_count=None):
    keys = sorted((ds, r, 'invented-' + str(i)) for ds in ("2wikimultihopqa", "hotpotqa", "musique")
        for i in range(4) for r in ("bm25", "dense", "hybrid"))
    eligible = [k for i, k in enumerate(keys) if i % 5] if eligible_count is None else keys[:eligible_count]
    scores = {p: {k: ((i*(j+3)) % 17)/7 - 1. if k in eligible else None for i, k in enumerate(keys)}
        for j, p in enumerate(POLICIES[1:])}
    allocation = allocate(keys, eligible, scores)
    for row in allocation['ledger']:
        row['forced_keep_reason'] = None if row['eligible'] else 'invented_common_exclusion'
    outcomes = []
    for i, (ds, r, sid) in enumerate(keys):
        before, after = int(i % 3 == 0), int(i % 4 == 0)
        outcomes.append(dict(dataset=ds, retriever=r, sample_id=sid, a0_em=before, a1_em=after,
            a0_f1=1. if before else (i % 4)/4, a1_f1=1. if after else ((i+1) % 4)/4))
    return allocation['ledger'], outcomes


class AnalysisTests(unittest.TestCase):
    def panels(self, **kwargs):
        actions, outcomes = fixture(**kwargs)
        return Panel(actions, outcomes, questions_per_dataset=4), IndependentPanel(actions, outcomes, questions_per_dataset=4)

    def test_exact_point_counts_f1_and_global_action_cells(self):
        panel, independent = self.panels()
        actual = json.loads(json.dumps(point_estimates(panel)))
        compare_report(actual, independent.point(), Checks())
        self.assertEqual(actual['policies']['Keep']['replacements'], 0)
        self.assertTrue(all(actual['policies'][p]['replacements'] == 2 for p in POLICIES[1:]))
        for policy in POLICIES:
            row = actual['policies'][policy]
            self.assertEqual(row['net'], row['recovery']-row['damage'])
            self.assertEqual(row['replacements'], row['recovery']+row['damage']+row['neutral'])
            self.assertEqual(sum(row['realized_em_transition_counts'].values()), 36)
            for kind, cells in actual['fixed_global_action_breakdowns'].items():
                self.assertEqual(sum(c['policies'][policy]['replacements'] for c in cells), row['replacements'], kind)

    def test_full_draws_match_independent_explicit_copies_and_same_rng(self):
        panel, independent = self.panels()
        records = []
        differs = False
        for i, (weights, other) in enumerate(zip(question_weights(panel, draws=40), independent.counts(draws=40), strict=True)):
            np.testing.assert_array_equal(weights, other)
            row = draw_record(panel, weights, i)
            expected = independent.draw(other, i)
            compare_report(json.loads(json.dumps(row)), expected, Checks())
            self.assertEqual(row['N_all'], 36)
            self.assertTrue(all(row['reallocated']['policy_totals'][p]['replacements'] == 2 for p in POLICIES[1:]))
            differs |= row['reallocated'] != row['fixed_action']
            records.append(row)
        self.assertTrue(differs)
        compare_report(intervals(panel, records), independent_intervals(independent, records), Checks())
        self.assertEqual(intervals(panel, records)['interval_family_size'], 6)

    def test_zero_and_insufficient_eligible_copies_remain_in_denominator(self):
        for eligible in (0, 1):
            with self.subTest(eligible=eligible):
                panel, independent = self.panels(eligible_count=eligible)
                compare_report(point_estimates(panel), independent.point(), Checks())
                for i, weights in enumerate(question_weights(panel, draws=10)):
                    row = draw_record(panel, weights, i)
                    compare_report(row, independent.draw(weights, i), Checks())
                    self.assertEqual(row['N_all'], 36)
                    self.assertLessEqual(row['reallocated']['policy_totals']['HGB']['replacements'], 2)

    def test_question_group_order_and_rng_state_do_not_depend_on_input_order(self):
        actions, outcomes = fixture()
        first = Panel(actions, outcomes, questions_per_dataset=4)
        second = Panel(list(reversed(actions)), list(reversed(outcomes)), questions_per_dataset=4)
        self.assertEqual(first.groups, second.groups)
        self.assertEqual([g[0] for g in first.groups], ['2wikimultihopqa']*4 + ['hotpotqa']*4 + ['musique']*4)
        one, two = list(question_weights(first, draws=5)), list(question_weights(second, draws=5))
        for left, right in zip(one, two): np.testing.assert_array_equal(left, right)
        weights = one[0]
        for group_index in range(len(first.groups)):
            self.assertEqual(len(first.siblings[first.siblings == group_index]), 3)
        self.assertTrue(all(int(weights[s].sum()) == 4 for s in first.strata))

    def test_missing_sibling_changed_action_bad_mask_and_non_numeric_outcomes_rejected(self):
        actions, outcomes = fixture()
        for mode in ('missing', 'duplicate', 'action', 'mask', 'nan', 'bool_em', 'gold'):
            a, y = copy.deepcopy(actions), copy.deepcopy(outcomes)
            if mode == 'missing': y.pop()
            elif mode == 'duplicate': y[-1] = copy.deepcopy(y[0])
            elif mode == 'action': a[0]['actions']['Keep'] = 'REPLACE'
            elif mode == 'mask': a[0]['scores']['HGB'] = 0.
            elif mode == 'nan': y[0]['a0_f1'] = float('nan')
            elif mode == 'bool_em': y[0]['a0_em'] = True
            else: y[0]['answer'] = 'forbidden text'
            for constructor in (Panel, IndependentPanel):
                with self.subTest(mode=mode, constructor=constructor.__name__), self.assertRaises(ValueError):
                    constructor(a, y, questions_per_dataset=4)

    def test_wrong_stratum_weights_invalid_dtype_and_changed_draw_fail(self):
        panel, independent = self.panels()
        good = next(question_weights(panel))
        wrong_sum = good.copy(); wrong_sum[0] += 1
        negative = good.copy(); negative[0] = -1
        for weights in (good.astype(float), wrong_sum, negative, good[:-1]):
            with self.assertRaises(ValueError): draw_record(panel, weights, 0)
            with self.assertRaises(ValueError): independent.draw(weights, 0)
        row = draw_record(panel, good, 0)
        row['reallocated']['policy_totals']['HGB']['net'] += 1
        with self.assertRaises(ValueError): compare_report(row, independent.draw(good, 0), Checks())

    def test_fixed_family_signs_zero_touching_and_secondary_sensitivity_labels(self):
        panel, independent = self.panels()
        # Invented endpoint receipts exercise the interval rule only, not full
        # draw acceptance. Full draw equality is checked in the preceding tests.
        records = [draw_record(panel, w, i) for i, w in enumerate(question_weights(panel, draws=20))]
        for row in records:
            for mode in ('reallocated', 'fixed_action'):
                row[mode]['paired_event_differences'] = [[-1, 1], [0, 0], [1, -1]]
        actual = intervals(panel, records)
        compare_report(actual, independent_intervals(independent, records), Checks())
        first, second, third = actual['reallocated']['comparisons']
        self.assertEqual(first['endpoints']['em_difference_pp']['adjusted_direction'], 'negative')
        self.assertEqual(second['endpoints']['em_difference_pp']['adjusted_direction'], 'inconclusive')
        self.assertFalse(first['joint_em_improvement_and_damage_reduction'])
        self.assertFalse(second['joint_em_improvement_and_damage_reduction'])
        self.assertTrue(third['joint_em_improvement_and_damage_reduction'])
        self.assertEqual(actual['fixed_action']['interval_role'], 'secondary_sensitivity_same_draws')
        self.assertEqual(actual['adjusted_quantiles'], [.05/12, 1-.05/12])

    def test_independent_f1_tolerance_does_not_relax_counts_or_em(self):
        compare_report({'token_f1': .5 + 1e-16}, {'token_f1': .5}, Checks())
        for actual, expected in (({'token_f1': .5 + 1e-12}, {'token_f1': .5}),
            ({'em_rate': .5 + 1e-16}, {'em_rate': .5}), ({'replacements': True}, {'replacements': 1})):
            with self.assertRaises(ValueError): compare_report(actual, expected, Checks())

    def test_durable_binary_roundtrip_and_all_draw_independent_validation(self):
        panel, independent = self.panels()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            writer = BootstrapWriter(out, groups=len(panel.groups), draws=12, questions_per_dataset=4)
            records = []
            try:
                for i, weights in enumerate(question_weights(panel, draws=12)):
                    row = draw_record(panel, weights, i)
                    writer.append(weights, row)
                    records.append(row)
                self.assertEqual(writer.summary()['completed_weight_bytes'], 12*12*2)
            finally:
                writer.close()
            accepted = validate_draw_files(independent, out/'BOOTSTRAP_QUESTION_WEIGHTS.u16le', out/'BOOTSTRAP_DRAWS.jsonl', draws=12)
            self.assertEqual(accepted, records)
            compare_report(intervals(panel, records), independent_intervals(independent, accepted), Checks())
            with self.assertRaises(FileExistsError):
                BootstrapWriter(out, groups=12, draws=12, questions_per_dataset=4)

    def test_truncated_extra_or_corrupted_binary_draws_and_receipts_are_rejected(self):
        panel, independent = self.panels()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            writer = BootstrapWriter(out, groups=12, draws=2, questions_per_dataset=4)
            try:
                for i, w in enumerate(question_weights(panel, draws=2)):
                    writer.append(w, draw_record(panel, w, i))
            finally:
                writer.close()
            wp, rp = out/'BOOTSTRAP_QUESTION_WEIGHTS.u16le', out/'BOOTSTRAP_DRAWS.jsonl'
            original_weights, original_receipts = wp.read_bytes(), rp.read_bytes()
            changed = bytearray(original_weights); changed[0] ^= 1
            for weights, receipts in ((original_weights[:-1], original_receipts), (original_weights+b'\0', original_receipts),
                (changed, original_receipts), (original_weights, original_receipts[:-1]), (original_weights, original_receipts+b'{}\n')):
                wp.write_bytes(weights); rp.write_bytes(receipts)
                with self.assertRaises(ValueError): validate_draw_files(independent, wp, rp, draws=2)

    def test_invalid_unsigned_conversion_or_failed_receipt_preserves_prior_draw(self):
        panel, _ = self.panels()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            writer = BootstrapWriter(out, groups=12, draws=2, questions_per_dataset=4)
            w = next(question_weights(panel))
            try:
                writer.append(w, draw_record(panel, w, 0))
                before = (out/'BOOTSTRAP_QUESTION_WEIGHTS.u16le').stat().st_size
                bad = w.copy(); bad[0] = 65536
                with self.assertRaises(ValueError): writer.append(bad, {'draw': 1})
                with self.assertRaises(ValueError): writer.append(w, {'draw': True})
                with self.assertRaises(ValueError): writer.append(w, {'draw': 1, 'bad': float('nan')})
                self.assertEqual(writer.completed, 1)
                self.assertEqual((out/'BOOTSTRAP_QUESTION_WEIGHTS.u16le').stat().st_size, before)
            finally:
                writer.close()


if __name__ == '__main__':
    unittest.main()
