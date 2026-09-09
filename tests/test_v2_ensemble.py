from __future__ import annotations

import unittest

import numpy as np

from src.arbitration.v2_ensemble import (
    V2_ACTION_RATE,
    action_budget,
    empirical_cdf,
    transition_utility,
)


class V2EnsembleTests(unittest.TestCase):
    def test_action_budget_is_five_percent_by_default(self):
        self.assertEqual(action_budget(9000), 450)
        self.assertEqual(V2_ACTION_RATE, 0.05)

    def test_empirical_cdf_is_monotone(self):
        ref = np.asarray([0.1, 0.3, 0.2, 0.4])
        values = np.asarray([0.05, 0.2, 0.35, 0.5])
        got = empirical_cdf(ref, values)
        self.assertTrue(np.all(np.diff(got) >= 0))
        np.testing.assert_allclose(got, [0.0, 0.5, 0.75, 1.0])

    def test_transition_utility_penalizes_damage(self):
        probabilities = np.asarray(
            [
                [0.8, 0.1, 0.1],
                [0.2, 0.6, 0.2],
            ]
        )
        utility = transition_utility(
            probabilities,
            classes=("recovery", "damage", "neutral"),
            lambda_damage=1.0,
        )
        np.testing.assert_allclose(utility, [0.7, -0.4])


if __name__ == "__main__":
    unittest.main()
