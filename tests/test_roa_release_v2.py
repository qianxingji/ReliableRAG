"""Regression for the actual omitted direct dependency, without original data."""
import unittest
from scripts.package_roa_replay_release_v2 import parent_coverage


class DirectClosureTests(unittest.TestCase):
    def test_omitted_or_different_direct_input_rejects(self):
        earlier = dict(path="score.jsonl", size_bytes=1, sha256="1" * 64)
        direct = dict(path="decisions/v2_actions.jsonl", size_bytes=2, sha256="2" * 64)
        accepted = [earlier, direct]
        for provided in ([earlier], [earlier, dict(direct, sha256="3" * 64)]):
            with self.assertRaisesRegex(ValueError, "ACCEPTED_PARENT_MISSING_OR_DIFFERENT"):
                parent_coverage(provided, accepted)
        self.assertEqual(parent_coverage([earlier, direct], accepted), 2)

    def test_duplicate_reference_receipt_does_not_inflate_coverage(self):
        row = dict(path="one", size_bytes=0, sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ACCEPTED_PARENT"):
            parent_coverage([row], [row, row])


if __name__ == "__main__":
    unittest.main()
