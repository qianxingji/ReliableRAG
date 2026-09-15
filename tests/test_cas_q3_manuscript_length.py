"""Tests for the explicitly bounded manuscript-length proxy."""

from __future__ import annotations

import unittest

from scripts.audit_cas_q3_manuscript_length import audit, text_before_references, token_count


class ManuscriptLengthTests(unittest.TestCase):
    def test_tokenization_is_fixed_for_hyphens_apostrophes_and_decimals(self):
        self.assertEqual(token_count("post-generation author's 0.2333"), 3)

    def test_reference_split_requires_a_standalone_heading(self):
        self.assertEqual(text_before_references("Body\nReferences\nEntry"), "Body\n")
        with self.assertRaisesRegex(AssertionError, "References heading"):
            text_before_references("Body with References inline")

    def test_current_pdf_counts_are_bound_but_not_called_publisher_counts(self):
        result = audit()
        self.assertEqual(result["pdf_tokens_before_references"], 4048)
        self.assertEqual(result["pdf_tokens_full_document"], 4745)
        self.assertEqual(result["static_abstract_word_count"], 155)
        self.assertTrue(result["applied_intelligence_abstract_requirement_met"])
        self.assertFalse(result["publisher_word_count_claimed"])
        self.assertEqual(result["cas_q3_status"], "NOT_READY")


if __name__ == "__main__":
    unittest.main()
