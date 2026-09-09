from __future__ import annotations

import unittest

from src.arbitration.v2_policy import (
    RankedTrace,
    four_state_utility,
    select_global_budget,
    select_stratum_budgets,
    two_head_utility,
)


class V2PolicyTests(unittest.TestCase):
    def test_global_ranking_and_tie_break_are_deterministic(self):
        rows = [
            RankedTrace("b", "hotpotqa", "bm25", 0.9),
            RankedTrace("a", "hotpotqa", "bm25", 0.9),
            RankedTrace("c", "hotpotqa", "bm25", 0.8),
        ]
        selected = select_global_budget(rows, 2)
        self.assertEqual([r.sample_id for r in selected], ["a", "b"])

    def test_stratum_budget(self):
        rows = [
            RankedTrace("a", "hotpotqa", "bm25", 0.9),
            RankedTrace("b", "hotpotqa", "bm25", 0.8),
            RankedTrace("c", "hotpotqa", "dense", 0.7),
        ]
        selected = select_stratum_budgets(
            rows,
            {("hotpotqa", "bm25"): 1, ("hotpotqa", "dense"): 1},
        )
        self.assertEqual({r.sample_id for r in selected}, {"a", "c"})

    def test_two_head_utility(self):
        self.assertAlmostEqual(two_head_utility(0.8, 0.1, 2.0), 0.6)

    def test_four_state_utility(self):
        probs = {"00": 0.2, "01": 0.5, "10": 0.1, "11": 0.2}
        self.assertAlmostEqual(four_state_utility(probs, 2.0), 0.3)


if __name__ == "__main__":
    unittest.main()
