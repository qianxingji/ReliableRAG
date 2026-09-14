"""Tests for the bounded Applied Intelligence modern-template preflight."""

from __future__ import annotations

from pathlib import Path
import unittest

from scripts.build_cas_q3_applied_intelligence_preflight import SOURCE, transformed_source


class AppliedIntelligencePreflightTests(unittest.TestCase):
    def test_transform_uses_modern_numbered_profile_and_preserves_scientific_text(self):
        source = SOURCE.read_text(encoding="utf-8")
        converted, changes = transformed_source(source)
        self.assertIn(r"\documentclass[pdflatex,sn-basic,Numbered]{sn-jnl}", converted)
        self.assertIn(r"\abstract{Retrieval repair can recover", converted)
        self.assertIn(r"\keywords{retrieval-augmented generation, answer verification", converted)
        self.assertNotIn(r"\bibliographystyle{plainnat}", converted)
        self.assertNotIn("figures/", converted)
        self.assertNotIn("tables/", converted)
        self.assertIn("The same joint rule does not pass against the HGB-only policy", converted)
        self.assertIn("not a new selector architecture", converted)
        self.assertEqual(len(changes), 11)

    def test_transform_rejects_noncanonical_source(self):
        source = SOURCE.read_text(encoding="utf-8").replace(
            r"\documentclass[11pt]{article}", r"\documentclass[12pt]{article}", 1
        )
        with self.assertRaisesRegex(AssertionError, "journal-neutral preamble"):
            transformed_source(source)


if __name__ == "__main__":
    unittest.main()
