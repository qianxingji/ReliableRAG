"""Fail-closed tests for the private Applied Intelligence target builder."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.build_cas_q3_applied_intelligence_private_submission import (
    ANONYMOUS_FRONT_MATTER,
    DECLARATION_PLACEHOLDER,
    build,
    render_target_source,
)
from tests.test_cas_q3_private_submission_packet import complete_fixture


class AppliedIntelligencePrivateSubmissionTests(unittest.TestCase):
    def test_render_replaces_only_private_anchors_and_retains_claim_boundaries(self):
        source = (
            ANONYMOUS_FRONT_MATTER
            + "\nThe same joint rule does not pass against the HGB-only policy.\n"
            + "This is not a new selector architecture.\nPublic distribution remains withheld.\n"
            + DECLARATION_PLACEHOLDER
        )
        data = complete_fixture()
        data["target_journal"]["selected_journal"] = "Applied Intelligence"
        rendered = render_target_source(source, data)
        self.assertNotIn("Anonymous affiliation retained", rendered)
        self.assertNotIn("must be completed by the responsible authors", rendered)
        self.assertIn(r"\author*[1]{A\_uthor \& Co}", rendered)
        self.assertIn(r"\orgdiv{D\#}", rendered)
        self.assertIn("Private address", rendered)
        self.assertIn("private@example.org", rendered)
        self.assertIn("does not pass against the HGB-only policy", rendered)
        self.assertIn("not a new selector architecture", rendered)
        self.assertIn("Public distribution remains withheld", rendered)
        self.assertIn("Generative AI and AI-assisted technologies", rendered)

    def test_render_rejects_missing_or_duplicate_anchors(self):
        data = complete_fixture()
        for source in ("missing", ANONYMOUS_FRONT_MATTER * 2 + DECLARATION_PLACEHOLDER):
            with self.assertRaises(AssertionError):
                render_target_source(source, data)

    def test_incomplete_real_shape_fails_before_reading_transport_or_creating_output(self):
        data = complete_fixture()
        data["authorship"]["corresponding_author_email"] = None
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "private"
            with self.assertRaisesRegex(ValueError, "incomplete or invalid"):
                build(data, Path(temporary) / "missing.zip", "0" * 64, output)
            self.assertFalse(output.exists())

    def test_wrong_target_fails_before_reading_transport_or_creating_output(self):
        data = complete_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "private"
            with self.assertRaisesRegex(ValueError, "requires Applied Intelligence"):
                build(data, Path(temporary) / "missing.zip", "0" * 64, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
