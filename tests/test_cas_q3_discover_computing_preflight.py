"""Tests for the provisional Discover Computing technical preflight."""

from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from scripts.build_cas_q3_discover_computing_preflight import ROOT, SOURCE, build, transformed_source


class DiscoverComputingPreflightTests(unittest.TestCase):
    def test_transform_is_limited_to_size_and_flat_paths(self):
        source = SOURCE.read_text(encoding="utf-8")
        converted, changes = transformed_source(source)
        self.assertIn(r"\documentclass[12pt]{article}", converted)
        self.assertNotIn(r"\documentclass[11pt]{article}", converted)
        self.assertNotIn("figures/", converted)
        self.assertNotIn("tables/", converted)
        self.assertEqual(len(changes), 6)
        restored = converted
        for change in reversed(changes):
            restored = restored.replace(change["to"], change["from"])
        self.assertEqual(restored, source)

    def test_build_is_fail_closed_and_preserves_source(self):
        before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        result = build()
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), before)
        self.assertFalse(result["submission_authorized"])
        self.assertFalse(result["final_target_selected"])
        self.assertFalse(result["institutional_cas_q3_qualification_verified"])
        self.assertFalse(result["profile"]["springer_nature_template_applied"])
        self.assertEqual(result["artifacts"]["source_zip_nested_members"], [])
        self.assertEqual(result["artifacts"]["pdf_nonembedded_font_rows"], [])
        self.assertEqual(result["artifacts"]["pdf_type3_font_rows"], [])
        self.assertTrue((ROOT / result["artifacts"]["pdf"]).is_file())
        self.assertTrue((ROOT / result["artifacts"]["source_zip"]).is_file())


if __name__ == "__main__":
    unittest.main()
