"""Contract tests for prospective reader tuning; synthetic development data only."""

from __future__ import annotations

import unittest

from src.arbitration.empirical_contract import DATASETS, RETRIEVERS
from src.arbitration.reader_development_tuning import (
    BASE_FIXED,
    C_SEARCH_VALUES,
    candidate_grid,
    candidate_tie_rank,
    development_folds,
    tune_recovery_head,
)


def development_keys() -> tuple[set[tuple[str, str, str]], set[tuple[str, str, str]]]:
    fit = {
        (dataset, retriever, f"fit-{index:04d}")
        for dataset in DATASETS
        for index in range(1200)
        for retriever in RETRIEVERS
    }
    cal = {
        (dataset, retriever, f"cal-{index:04d}")
        for dataset in DATASETS
        for index in range(300)
        for retriever in RETRIEVERS
    }
    return fit, cal


class ReaderDevelopmentTuningTests(unittest.TestCase):
    def test_grid_and_tie_rule_are_exact(self):
        grid = candidate_grid()
        self.assertEqual(len(grid), 8)
        self.assertEqual({item["C"] for item in grid}, set(C_SEARCH_VALUES))
        self.assertEqual({item["class_weight"] for item in grid}, {None, "balanced"})
        self.assertTrue(all(
            all(item[key] == value for key, value in BASE_FIXED.items())
            for item in grid
        ))
        tied = sorted(grid, key=candidate_tie_rank)
        self.assertEqual(
            [(item["class_weight"], item["C"]) for item in tied],
            [(None, 1.0), (None, 0.1), (None, 10.0), (None, 0.01),
             ("balanced", 1.0), ("balanced", 0.1),
             ("balanced", 10.0), ("balanced", 0.01)],
        )

    def test_folds_are_exact_deterministic_and_keep_siblings_together(self):
        fit, _ = development_keys()
        folds = development_folds(fit)
        reverse = development_folds(reversed(sorted(fit)))
        self.assertEqual(folds, reverse)
        self.assertEqual(len(folds), 3)
        all_validation = set()
        for fold in folds:
            self.assertEqual(len(fold["train"]), 7200)
            self.assertEqual(len(fold["validation"]), 3600)
            self.assertFalse(fold["train"] & fold["validation"])
            groups = {(key[0], key[2]) for key in fold["validation"]}
            self.assertEqual(len(groups), 1200)
            for dataset in DATASETS:
                self.assertEqual(sum(group[0] == dataset for group in groups), 400)
            for dataset, sample_id in groups:
                self.assertTrue(
                    {(dataset, retriever, sample_id) for retriever in RETRIEVERS}
                    <= fold["validation"]
                )
            self.assertFalse(all_validation & fold["validation"])
            all_validation |= fold["validation"]
        self.assertEqual(all_validation, fit)

    def test_tuner_has_development_only_surface_and_finite_budget(self):
        fit, cal = development_keys()
        keys = fit | cal
        rows = {}
        outcomes = {}
        retriever_value = {"bm25": -0.3, "dense": 0.0, "hybrid": 0.3}
        for dataset, retriever, sample_id in keys:
            index = int(sample_id.rsplit("-", 1)[1])
            dataset_index = DATASETS.index(dataset)
            signal = ((index + dataset_index) % 11 - 5) / 5 + retriever_value[retriever]
            rows[(dataset, retriever, sample_id)] = {
                "eligible": (index + dataset_index) % 17 != 0,
                "numeric": [signal],
            }
            recovery = int((index + 2 * dataset_index + RETRIEVERS.index(retriever)) % 13 == 0)
            outcomes[(dataset, retriever, sample_id)] = {
                "a0_em": 0,
                "a1_em": recovery,
            }
        events = []
        result = tune_recovery_head(
            rows,
            outcomes,
            {"fit": fit, "cal": cal},
            "HGB_ONLY_R",
            events.append,
        )
        self.assertEqual(result["fit_attempts"], 26)
        self.assertEqual(result["successful_fits"], 26)
        self.assertEqual(len(result["candidates"]), 8)
        self.assertTrue(all(item["valid"] for item in result["candidates"]))
        self.assertEqual(sum(e["event"] == "cv_fit_started" for e in events), 24)
        self.assertEqual(sum(e["event"] == "cv_fit_completed" for e in events), 24)
        self.assertFalse(result["test_labels_read"])
        self.assertFalse(result["test_predictions_emitted"])
        self.assertFalse(result["action_budget_tuned"])
        self.assertIn(result["selected_parameters"], candidate_grid())

    def test_rejects_extra_role_and_outcome_scope(self):
        fit, cal = development_keys()
        with self.assertRaisesRegex(RuntimeError, "DEVELOPMENT_ROLES_ONLY"):
            tune_recovery_head({}, {}, {"fit": fit, "cal": cal, "test": set()}, "HGB_ONLY_R")
        with self.assertRaisesRegex(RuntimeError, "OUTCOME_SCOPE"):
            tune_recovery_head(
                {key: {"eligible": True, "numeric": [0.0]} for key in fit | cal},
                {},
                {"fit": fit, "cal": cal},
                "HGB_ONLY_R",
            )


if __name__ == "__main__":
    unittest.main()
