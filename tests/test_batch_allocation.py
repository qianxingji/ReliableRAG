"""Compare the future inference kernel with explicitly replicated toy batches."""
import unittest

import numpy as np

from src.evaluation.batch_allocation import weighted_top_k


class BatchAllocationTests(unittest.TestCase):
    def test_matches_explicit_replicated_batches_with_question_siblings(self):
        rng = np.random.default_rng(20260910)
        # Four question groups, three siblings each; two rows are ineligible.
        order = np.array([9, 3, 11, 2, 8, 7, 0, 10, 4, 5])
        for _ in range(100):
            question_weights = rng.multinomial(4, np.full(4, 0.25))
            weights = np.repeat(question_weights, 3)
            cap = int(rng.integers(0, 15))
            explicit_rows = np.repeat(order, weights[order])[:cap]
            expected = np.bincount(explicit_rows, minlength=12)
            actual = weighted_top_k(order, weights, cap)
            np.testing.assert_array_equal(actual, expected)
            self.assertEqual(int(actual.sum()), min(cap, int(weights[order].sum())))
            self.assertTrue(np.all(actual <= weights))

    def test_reallocation_differs_from_copying_old_actions(self):
        # Originally row 0 wins; the sampled batch contains no copy of it.
        order, weights = np.array([0, 1, 2]), np.array([0, 1, 2])
        selected = weighted_top_k(order, weights, 1)
        np.testing.assert_array_equal(selected, [0, 1, 0])
        frozen_actions = np.array([1, 0, 0]) * weights
        self.assertEqual(int(frozen_actions.sum()), 0)

    def test_empty_eligible_set_and_partial_duplicate_selection(self):
        np.testing.assert_array_equal(weighted_top_k(np.array([], dtype=int), np.array([2, 1]), 1), [0, 0])
        np.testing.assert_array_equal(weighted_top_k(np.array([1, 0]), np.array([3, 4]), 5), [1, 4])

    def test_invalid_counts_order_or_cap_are_rejected(self):
        cases = [([0], [-1], 1), ([0, 0], [1], 1), ([2], [1], 1),
                 ([0], [1.5], 1), ([0], [1], -1), ([0], [1], True)]
        for order, weights, cap in cases:
            with self.subTest(order=order, weights=weights, cap=cap):
                with self.assertRaises(ValueError):
                    weighted_top_k(np.asarray(order), np.asarray(weights), cap)


if __name__ == "__main__":
    unittest.main()
