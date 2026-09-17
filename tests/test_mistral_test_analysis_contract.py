"""Invented-only tests for the frozen Mistral test analysis contract."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from scripts.empirical_analysis_storage import BootstrapWriter
from scripts.mistral_test_analysis_independent import (
    IndependentPanel,
    compare_report,
    independent_intervals,
    validate_draw_files,
)
from scripts.mistral_test_analysis_math import (
    ADJUSTED_QUANTILES,
    FIXED_POLICIES,
    POLICIES,
    PRIMARY_POLICIES,
    SCORED_POLICIES,
    SEED,
    Panel,
    draw_record,
    intervals,
    point_estimates,
    question_weights,
)


def fixture(*, eligible_count=None):
    keys = sorted(
        (dataset, retriever, "invented-" + str(index))
        for dataset in ("2wikimultihopqa", "hotpotqa", "musique")
        for index in range(4)
        for retriever in ("bm25", "dense", "hybrid")
    )
    eligible = (set(key for index, key in enumerate(keys) if index % 5)
                if eligible_count is None else set(keys[:eligible_count]))
    score_maps = {
        policy: {
            key: (((index * (policy_index + 3)) % 19) / 7.0 - 1.0
                  if key in eligible else None)
            for index, key in enumerate(keys)
        }
        for policy_index, policy in enumerate(SCORED_POLICIES)
    }
    cap = round(0.05 * len(keys))
    selected = {
        policy: set(sorted(eligible, key=lambda key: (-score_maps[policy][key], key))[:cap])
        for policy in SCORED_POLICIES
    }
    actions = []
    outcomes = []
    for index, (dataset, retriever, sample_id) in enumerate(keys):
        actions.append({
            "dataset": dataset,
            "retriever": retriever,
            "sample_id": sample_id,
            "eligible": (dataset, retriever, sample_id) in eligible,
            "scores": {
                policy: score_maps[policy][(dataset, retriever, sample_id)]
                for policy in SCORED_POLICIES
            },
            "actions": {
                policy: ("KEEP" if policy == "Keep" else
                         "REPLACE" if (dataset, retriever, sample_id) in selected[policy]
                         else "KEEP")
                for policy in POLICIES
            },
            "forced_keep_reason": (None if (dataset, retriever, sample_id) in eligible
                                   else "invented_common_exclusion"),
        })
        before = int(index % 3 == 0)
        after = int(index % 4 == 0)
        outcomes.append({
            "dataset": dataset,
            "retriever": retriever,
            "sample_id": sample_id,
            "a0_em": before,
            "a1_em": after,
            "a0_f1": 1.0 if before else (index % 4) / 4.0,
            "a1_f1": 1.0 if after else ((index + 1) % 4) / 4.0,
        })
    return actions, outcomes


class MistralTestAnalysisContractTests(unittest.TestCase):
    def panels(self, **kwargs):
        actions, outcomes = fixture(**kwargs)
        return (
            Panel(actions, outcomes, questions_per_dataset=4),
            IndependentPanel(actions, outcomes, questions_per_dataset=4),
        )

    def test_point_counts_overlaps_and_fixed_recipe_are_independently_reproduced(self):
        panel, independent = self.panels()
        actual = point_estimates(panel)
        compare_report(actual, independent.point())
        self.assertEqual(actual["N_all"], 36)
        self.assertEqual(actual["question_groups"], 12)
        self.assertEqual(actual["primary_global_cap"], 2)
        self.assertEqual(actual["policies"]["Keep"]["replacements"], 0)
        for policy in PRIMARY_POLICIES + FIXED_POLICIES:
            row = actual["policies"][policy]
            self.assertEqual(row["replacements"], 2)
            self.assertEqual(row["net"], row["recovery"] - row["damage"])
            self.assertEqual(row["replacements"],
                             row["recovery"] + row["damage"] + row["neutral"])
        for comparison in actual["primary_action_overlaps"]:
            self.assertEqual(sum(
                value["rows"] for value in comparison["overall"].values()
            ), 36)
            self.assertEqual(len(comparison["dataset_x_retriever"]), 9)

    def test_every_draw_matches_independent_rng_and_explicit_copy_allocation(self):
        panel, independent = self.panels()
        records = []
        for index, (weights, other) in enumerate(zip(
            question_weights(panel, draws=40), independent.counts(draws=40), strict=True
        )):
            np.testing.assert_array_equal(weights, other)
            actual = draw_record(panel, weights, index)
            expected = independent.draw(other, index)
            compare_report(actual, expected)
            self.assertEqual(actual["N_all"], 36)
            self.assertEqual(actual["cap"], 2)
            self.assertTrue(all(
                actual["reallocated"]["policy_totals"][policy]["replacements"] == 2
                for policy in SCORED_POLICIES
            ))
            records.append(actual)
        compare_report(intervals(panel, records),
                       independent_intervals(independent, records))

    def test_four_endpoint_adjustment_and_fixed_recipe_remain_separate(self):
        panel, independent = self.panels()
        records = [draw_record(panel, weights, index)
                   for index, weights in enumerate(question_weights(panel, draws=20))]
        for row in records:
            for mode in ("reallocated", "fixed_action"):
                row[mode]["primary_event_differences"] = [[1, -1], [0, 0]]
                row[mode]["fixed_recipe_event_differences"] = [[5, -5], [5, -5]]
        actual = intervals(panel, records)
        compare_report(actual, independent_intervals(independent, records))
        self.assertEqual(actual["primary_interval_family_size"], 4)
        self.assertEqual(actual["adjusted_quantiles"], list(ADJUSTED_QUANTILES))
        first, second = actual["reallocated"]["primary_comparisons"]
        self.assertTrue(first["joint_em_improvement_and_damage_reduction"])
        self.assertFalse(second["joint_em_improvement_and_damage_reduction"])
        self.assertNotIn(
            "joint_em_improvement_and_damage_reduction",
            actual["reallocated"]["fixed_recipe_comparisons"][0],
        )
        self.assertEqual(
            actual["reallocated"]["fixed_recipe_role"],
            "descriptive_outside_confirmatory_family",
        )

    def test_ineligible_rows_stay_in_denominator_and_cap_is_not_rescaled(self):
        for eligible_count in (0, 1):
            with self.subTest(eligible_count=eligible_count):
                panel, independent = self.panels(eligible_count=eligible_count)
                compare_report(point_estimates(panel), independent.point())
                for index, weights in enumerate(question_weights(panel, draws=5)):
                    actual = draw_record(panel, weights, index)
                    compare_report(actual, independent.draw(weights, index))
                    self.assertEqual(actual["N_all"], 36)
                    self.assertEqual(actual["cap"], 2)
                    replacements = (
                        actual["reallocated"]["policy_totals"]["HGB_GBV_R"]
                        ["replacements"]
                    )
                    self.assertLessEqual(replacements, actual["cap"])
                    if eligible_count == 0:
                        self.assertEqual(replacements, 0)

    def test_corrupted_schema_action_mask_and_outcomes_fail_closed(self):
        actions, outcomes = fixture()
        cases = ("missing", "action", "mask", "nan", "bool_em", "gold", "policy")
        for mode in cases:
            altered_actions = copy.deepcopy(actions)
            altered_outcomes = copy.deepcopy(outcomes)
            if mode == "missing":
                altered_outcomes.pop()
            elif mode == "action":
                altered_actions[0]["actions"]["Keep"] = "REPLACE"
            elif mode == "mask":
                altered_actions[0]["scores"]["HGB_GBV_R"] = 0.0
            elif mode == "nan":
                altered_outcomes[0]["a0_f1"] = float("nan")
            elif mode == "bool_em":
                altered_outcomes[0]["a0_em"] = True
            elif mode == "gold":
                altered_outcomes[0]["answer"] = "forbidden reference text"
            else:
                del altered_actions[0]["scores"]["HGB_ONLY_R_FIXED_C1"]
            for constructor in (Panel, IndependentPanel):
                with self.subTest(mode=mode, constructor=constructor.__name__), \
                        self.assertRaises(ValueError):
                    constructor(altered_actions, altered_outcomes,
                                questions_per_dataset=4)

    def test_durable_draws_are_reconstructed_without_producer_kernel(self):
        panel, independent = self.panels()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            writer = BootstrapWriter(
                output, groups=len(panel.groups), draws=12, questions_per_dataset=4
            )
            expected = []
            try:
                for index, weights in enumerate(question_weights(panel, draws=12)):
                    row = draw_record(panel, weights, index)
                    writer.append(weights, row)
                    expected.append(row)
            finally:
                writer.close()
            accepted = validate_draw_files(
                independent,
                output / "BOOTSTRAP_QUESTION_WEIGHTS.u16le",
                output / "BOOTSTRAP_DRAWS.jsonl",
                draws=12,
            )
            self.assertEqual(accepted, json.loads(json.dumps(expected)))
            compare_report(intervals(panel, expected),
                           independent_intervals(independent, accepted))

    def test_independent_module_has_no_producer_or_weighted_kernel_import(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts" / "mistral_test_analysis_independent.py").read_text(
                      encoding="utf-8"
                  )
        self.assertNotIn("mistral_test_analysis_math", source)
        self.assertNotIn("batch_allocation", source)
        self.assertNotIn("weighted_top_k", source)
        self.assertEqual(SEED, 20260930)

    def test_formal_analysis_wrappers_freeze_family_draws_and_independent_path(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts" / "run_mistral_test_analysis.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts" / "validate_mistral_test_analysis.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("PASS_MISTRAL_TEST_ANALYSIS_PENDING_INDEPENDENT", producer)
        self.assertIn("PASS_INDEPENDENT_MISTRAL_TEST_ANALYSIS", validator)
        self.assertIn('"bootstrap_draws": DRAWS', producer)
        self.assertIn('"primary_family_size": 4', producer)
        self.assertIn('"adjusted_quantiles": [0.00625, 0.99375]', producer)
        self.assertIn("validate_draw_files", validator)
        self.assertNotIn("from scripts.run_mistral_test_analysis", validator)
        self.assertNotIn("from scripts.mistral_test_analysis_math", validator)
        self.assertNotIn("from src.evaluation.batch_allocation", validator)

    def test_formal_analysis_manifest_checks_reject_mutation_and_extra_files(self):
        from scripts.run_mistral_test_analysis import validate_manifest as producer_check
        from scripts.validate_mistral_test_analysis import validate_manifest as audit_check

        with tempfile.TemporaryDirectory() as directory:
            namespace = Path(directory)
            member = namespace / "invented.json"
            member.write_bytes(b"{}\n")
            manifest = {
                "status": "PASS",
                "files": [{
                    "path": member.name,
                    "size_bytes": member.stat().st_size,
                    "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                }],
                "excludes_only": "SHA256_MANIFEST.json",
                "exact_recursive_coverage": True,
            }
            (namespace / "SHA256_MANIFEST.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            expected = {
                (namespace / "SHA256_MANIFEST.json").resolve(), member.resolve(),
            }
            self.assertEqual(producer_check(namespace), expected)
            self.assertEqual(audit_check(namespace), expected)
            extra = namespace / "extra.txt"
            extra.write_text("unsealed", encoding="utf-8")
            for check in (producer_check, audit_check):
                with self.assertRaises(RuntimeError):
                    check(namespace)

    def test_analysis_freeze_requires_exact_recursive_input_graph(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_test_analysis.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_test_analysis.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MISTRAL_TEST_ANALYSIS_INPUT_GRAPH_AMENDMENT", producer)
        self.assertIn("NONEXACT_FROZEN_INPUT_GRAPH", validator)
        self.assertIn('"packages": {"numpy":', producer)


if __name__ == "__main__":
    unittest.main()
