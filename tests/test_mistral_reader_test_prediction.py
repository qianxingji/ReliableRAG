"""Invented-only tests for label-blind Mistral test prediction and actions."""
import copy
from pathlib import Path
import unittest

from scripts.mistral_test_prediction_independent import (
    _independent_score_and_allocate,
    compare_seals,
)
from src.arbitration.reader_test_prediction import (
    ACTION_CAP,
    EXPECTED_TRACES,
    FIXED_POLICIES,
    METHOD_WIDTHS,
    PRIMARY_POLICIES,
    SCORED_POLICIES,
    TestPredictionContractError,
    _score_and_allocate,
    score_and_allocate,
    sigmoid,
)


DATASETS = ("2wikimultihopqa", "hotpotqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")


def model(width, *, shift, fixed=False):
    design_width = 2 * width + 3
    return {
        "preprocessing": {
            "median": [0.25 + index * 0.1 for index in range(width)],
            "mean": [0.1 + index * 0.05 for index in range(width)],
            "std": [0.5 + index * 0.2 for index in range(width)],
        },
        "coef": [((index % 3) - 1) * 0.2 + shift
                 for index in range(design_width)],
        "intercept": -0.15 + shift,
        "platt_slope": 0.8 + (0.05 if fixed else 0.0),
        "platt_intercept": 0.03 - shift,
        "fit_keys_sha256": "a" * 64,
        "cal_keys_sha256": "b" * 64,
    }


def tuning_results():
    output = {}
    for index, (method, width) in enumerate(METHOD_WIDTHS.items()):
        selected = model(width, shift=0.01 * (index + 1))
        fixed = model(width, shift=0.03 * (index + 1), fixed=True)
        fixed["preprocessing"] = copy.deepcopy(selected["preprocessing"])
        output[method] = {
            "role": "DEVELOPMENT_ONLY_READER_HEAD_TUNING",
            "variant": method,
            "fit_attempts": 28,
            "test_labels_read": False,
            "test_predictions_emitted": False,
            "action_budget_tuned": False,
            "final_model": selected,
            "fixed_reference_model": fixed,
        }
    return output


def prelabel_rows(*, questions_per_dataset=4, eligible_count=None):
    rows = []
    position = 0
    for dataset in DATASETS:
        for index in range(questions_per_dataset):
            for retriever in RETRIEVERS:
                eligible = (position % 5 != 0 if eligible_count is None
                            else position < eligible_count)
                hgb = (None if not eligible else
                       0.05 + ((position * 7) % 80) / 100.0)
                margin = (None if not eligible else
                          -0.4 + ((position * 11) % 70) / 100.0)
                rows.append({
                    "dataset": dataset,
                    "retriever": retriever,
                    "sample_id": f"invented-{index:03d}",
                    "position": position,
                    "role": "test",
                    "pair_eligible": eligible,
                    "eligible": eligible,
                    "forced_keep_reason": (None if eligible
                                           else "invented_common_exclusion"),
                    "hgb_score": hgb,
                    "gbv_F0": None if not eligible else 0.4,
                    "gbv_F1": None if not eligible else 0.4 + margin,
                    "gbv_margin": margin,
                    "feature_vectors": {
                        "HGB_GBV_R": [hgb, margin],
                        "HGB_ONLY_R": [hgb],
                        "GBV_ONLY_R": [margin],
                    },
                    "source_bindings": {
                        "hgb_signal_row_sha256": "c" * 64,
                        "gbv_row_sha256": "d" * 64,
                    },
                })
                position += 1
    return rows


def seals(*, eligible_count=None):
    rows = prelabel_rows(eligible_count=eligible_count)
    tuning = tuning_results()
    parameters = {
        "expected_traces": 36,
        "questions_per_dataset": 4,
        "action_cap": 2,
    }
    return (
        _score_and_allocate(rows, tuning, **parameters),
        _independent_score_and_allocate(rows, tuning, **parameters),
    )


class ReaderTestPredictionTests(unittest.TestCase):
    def test_selected_and_fixed_probabilities_and_actions_match_independent_path(self):
        actual, expected = seals()
        compare_seals(actual, expected)
        self.assertEqual(actual["N_all"], 36)
        self.assertEqual(actual["action_cap"], 2)
        self.assertFalse(actual["test_labels_read"])
        self.assertFalse(actual["test_outcomes_read"])
        self.assertFalse(actual["action_budget_tuned"])
        for policy in PRIMARY_POLICIES + FIXED_POLICIES:
            self.assertEqual(actual["replacement_counts"][policy], 2)
        self.assertTrue(all(
            set(row["scores"]) == set(SCORED_POLICIES) for row in actual["rows"]
        ))

    def test_zero_or_one_unique_eligible_rows_keep_full_denominator_and_fixed_cap(self):
        for eligible_count in (0, 1):
            with self.subTest(eligible_count=eligible_count):
                actual, expected = seals(eligible_count=eligible_count)
                compare_seals(actual, expected)
                self.assertEqual(actual["N_all"], 36)
                self.assertEqual(actual["N_eligible"], eligible_count)
                self.assertEqual(actual["action_cap"], 2)
                wanted = min(2, eligible_count)
                self.assertTrue(all(
                    actual["replacement_counts"][policy] == wanted
                    for policy in SCORED_POLICIES
                ))

    def test_canonical_ties_use_dataset_retriever_sample_identity(self):
        tuning = tuning_results()
        for method in PRIMARY_POLICIES:
            for field in ("final_model", "fixed_reference_model"):
                record = tuning[method][field]
                record["coef"] = [0.0] * len(record["coef"])
                record["intercept"] = 0.0
                record["platt_slope"] = 1.0
                record["platt_intercept"] = 0.0
        rows = prelabel_rows(eligible_count=36)
        actual = _score_and_allocate(
            rows, tuning, expected_traces=36, questions_per_dataset=4,
            action_cap=2,
        )
        selected = [
            (row["dataset"], row["retriever"], row["sample_id"])
            for row in actual["rows"]
            if row["actions"]["HGB_GBV_R"] == "REPLACE"
        ]
        expected = sorted(
            (row["dataset"], row["retriever"], row["sample_id"]) for row in rows
        )[:2]
        self.assertEqual(selected, expected)

    def test_extreme_logits_are_stable_and_independent_probability_tolerance_is_strict(self):
        self.assertEqual(sigmoid(1_000.0), 1.0)
        self.assertEqual(sigmoid(-1_000.0), 0.0)
        actual, expected = seals()
        changed = copy.deepcopy(actual)
        row = next(row for row in changed["rows"] if row["eligible"])
        row["scores"]["HGB_GBV_R"] += 2e-12
        with self.assertRaises(ValueError):
            compare_seals(changed, expected)

    def test_outcome_fields_roles_model_mutation_and_vector_drift_fail_closed(self):
        rows = prelabel_rows()
        tuning = tuning_results()
        cases = ("gold", "role", "model", "flags", "vector", "binding", "source")
        for mode in cases:
            altered_rows = copy.deepcopy(rows)
            altered_tuning = copy.deepcopy(tuning)
            parameters = {
                "expected_traces": 36,
                "questions_per_dataset": 4,
                "action_cap": 2,
            }
            if mode == "gold":
                altered_rows[0]["a0_em"] = 1
            elif mode == "role":
                altered_rows[0]["role"] = "fit"
            elif mode == "model":
                altered_tuning["HGB_GBV_R"]["fixed_reference_model"] \
                    ["preprocessing"]["mean"][0] += 0.1
            elif mode == "flags":
                altered_tuning["HGB_ONLY_R"]["test_predictions_emitted"] = True
            elif mode == "vector":
                altered_rows[1]["feature_vectors"]["HGB_GBV_R"].append(0.0)
            elif mode == "binding":
                altered_rows[1]["feature_vectors"]["HGB_ONLY_R"][0] += 0.01
            else:
                altered_rows[1]["source_bindings"]["extra"] = "e" * 64
            with self.subTest(mode=mode), self.assertRaises(
                (TestPredictionContractError, ValueError)
            ):
                _score_and_allocate(altered_rows, altered_tuning, **parameters)
        self.assertEqual(EXPECTED_TRACES, 18_000)
        self.assertEqual(ACTION_CAP, 900)
        with self.assertRaises(TestPredictionContractError):
            score_and_allocate(rows, tuning)

    def test_independent_module_imports_neither_producer_nor_allocation_kernel(self):
        source = (Path(__file__).resolve().parents[1] / "scripts"
                  / "mistral_test_prediction_independent.py").read_text(
                      encoding="utf-8"
                  )
        self.assertNotIn("from src.arbitration.reader_test_prediction", source)
        self.assertNotIn("import src.arbitration.reader_test_prediction", source)
        self.assertNotIn("from src.evaluation.batch_allocation", source)
        self.assertNotIn("import src.evaluation.batch_allocation", source)


if __name__ == "__main__":
    unittest.main()
