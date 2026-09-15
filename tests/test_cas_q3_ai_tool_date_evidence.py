"""Tests for the bounded AI-tool use-date evidence derivation."""

from __future__ import annotations

import copy
import unittest

from scripts.audit_cas_q3_ai_tool_date_evidence import EVIDENCE, derive


class AiToolDateEvidenceTests(unittest.TestCase):
    def records(self):
        records = [copy.deepcopy(record) for record in EVIDENCE]
        for record in records:
            record["verified"] = True
            record["required_markers"] = list(record["required_markers"])
        return records

    def test_routing_date_is_not_promoted_to_use_date(self):
        result = derive(self.records())
        self.assertEqual(
            result["decision"],
            "PASS_EVIDENCE_BOUNDED_AI_TOOL_USE_CONFIRMED_BY_DATE_EXACT_RANGE_PENDING",
        )
        self.assertEqual(result["routing_record"]["recorded_date"], "2026-09-11")
        self.assertFalse(result["routing_record"]["proves_actual_use_on_that_date"])
        self.assertEqual(
            result["joint_evidence_boundary"]["both_model_families_have_retained_use_evidence_by"],
            "2026-09-12",
        )
        self.assertFalse(result["joint_evidence_boundary"]["is_actual_first_use_date"])

    def test_exact_use_range_remains_unresolved_and_fail_closed(self):
        result = derive(self.records())
        fields = result["declaration_fields"]
        self.assertIsNone(fields["actual_first_use_date"])
        self.assertIsNone(fields["actual_last_use_date"])
        self.assertFalse(fields["exact_version_and_date_bounded_record_complete"])
        self.assertTrue(fields["author_confirmation_required"])
        self.assertFalse(result["p0_i_closed"])
        self.assertFalse(result["submission_authorized"])

    def test_integrity_failure_fails_closed(self):
        records = self.records()
        records[1]["verified"] = False
        result = derive(records)
        self.assertEqual(result["decision"], "FAIL_AI_TOOL_DATE_EVIDENCE_INTEGRITY")


if __name__ == "__main__":
    unittest.main()
