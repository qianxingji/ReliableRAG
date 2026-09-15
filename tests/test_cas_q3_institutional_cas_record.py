"""Tests for the private institution-recognized CAS record preflight."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.verify_cas_q3_institutional_cas_record import TEMPLATE, validate


class InstitutionalCasRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def _complete(self, evidence_path: Path, *, tier: str = "Q3") -> dict:
        content = b"synthetic institutional record fixture\n"
        evidence_path.write_bytes(content)
        return {
            "schema_version": 1,
            "evidence": {
                "file": "evidence/private/institutional_cas_record/example.pdf",
                "sha256": hashlib.sha256(content).hexdigest(),
                "kind": "AUTHENTICATED_CAS_PLATFORM_EXPORT",
                "issuing_office": "Example institutional office",
                "obtained_date": "2026-09-14",
                "authenticated_or_institution_issued": True,
            },
            "recorded_facts": {
                "cas_edition_year": 2025,
                "category_basis": "MAJOR",
                "category_name": "Computer Science",
                "journal_title": "Applied Intelligence",
                "print_issn": "0924-669X",
                "electronic_issn": "1573-7497",
                "tier": tier,
                "recognition_date_rule": "Formal publication date",
                "title_issn_change_treatment": "Current title and ISSNs control",
                "applies_to_hbut_first_affiliation_output": True,
            },
            "manual_review": {
                "reviewer_role": "Responsible author",
                "review_date": "2026-09-14",
                "record_visually_inspected": True,
                "metadata_matches_record": True,
                "jcr_result_not_substituted": True,
            },
        }

    def test_template_is_placeholder_only(self):
        result = validate(self.template, check_template=True)
        self.assertEqual(result["decision"], "PASS_INSTITUTIONAL_CAS_RECORD_TEMPLATE_AND_PRIVACY_BOUNDARY")
        self.assertFalse(result["complete"])
        self.assertFalse(result["private_values_emitted"])

    def test_unfilled_template_fails_closed_without_echoing_values(self):
        result = validate(self.template)
        self.assertEqual(result["decision"], "FAIL_CLOSED_INSTITUTIONAL_CAS_RECORD_INCOMPLETE_OR_INVALID")
        self.assertFalse(result["complete"])
        self.assertIn("recorded_facts.tier=Q1_Q2_or_Q3", result["missing_field_paths"])
        self.assertFalse(result["private_values_emitted"])

    def test_complete_synthetic_record_only_passes_integrity_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path)
            result = validate(data, evidence_path_override=evidence_path)
        self.assertEqual(
            result["decision"],
            "PASS_PRIVATE_INSTITUTIONAL_CAS_RECORD_INTEGRITY_PREFLIGHT_PENDING_CLIENT_CONTENT_AUDIT",
        )
        self.assertTrue(result["complete"])
        self.assertTrue(result["evidence_sha256_matches"])
        self.assertFalse(result["content_independently_certified"])
        self.assertTrue(result["independent_client_content_audit_required"])
        self.assertFalse(result["p0_h_closed"])

    def test_q1_and_q2_also_meet_q3_or_better_structural_target(self):
        for tier in ("Q1", "Q2"):
            with self.subTest(tier=tier), tempfile.TemporaryDirectory() as directory:
                evidence_path = Path(directory) / "example.pdf"
                data = self._complete(evidence_path, tier=tier)
                result = validate(data, evidence_path_override=evidence_path)
                self.assertTrue(result["target_tier_or_better_structurally_recorded"])

    def test_q4_fails_target_tier_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path, tier="Q4")
            result = validate(data, evidence_path_override=evidence_path)
        self.assertFalse(result["complete"])
        self.assertIn("recorded_facts.tier=Q1_Q2_or_Q3", result["missing_field_paths"])

    def test_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path)
            data["evidence"]["sha256"] = "0" * 64
            result = validate(data, evidence_path_override=evidence_path)
        self.assertFalse(result["complete"])
        self.assertIn("evidence.sha256: does not match local evidence bytes", result["validation_error_paths"])

    def test_wrong_journal_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path)
            data["recorded_facts"]["journal_title"] = "Different Journal"
            result = validate(data, evidence_path_override=evidence_path)
        self.assertFalse(result["complete"])
        self.assertIn(
            "recorded_facts.journal_title: must equal Applied Intelligence",
            result["validation_error_paths"],
        )


if __name__ == "__main__":
    unittest.main()
