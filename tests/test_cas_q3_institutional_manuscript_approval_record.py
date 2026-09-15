"""Tests for the private P0-I institutional manuscript-approval preflight."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.verify_cas_q3_institutional_manuscript_approval_record import TEMPLATE, validate


class InstitutionalManuscriptApprovalRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def _complete(self, evidence_path: Path, manuscript_path: Path) -> dict:
        evidence = b"synthetic institutional manuscript approval fixture\n"
        manuscript = b"synthetic approved manuscript fixture\n"
        evidence_path.write_bytes(evidence)
        manuscript_path.write_bytes(manuscript)
        return {
            "schema_version": 1,
            "evidence": {
                "file": "evidence/private/institutional_manuscript_approval/example.pdf",
                "sha256": hashlib.sha256(evidence).hexdigest(),
                "kind": "SUPERVISOR_AND_SCHOOL_APPROVAL_BUNDLE",
                "issuing_office": "Synthetic institutional office",
                "obtained_date": "2026-09-14",
                "authenticated_or_institution_issued": True,
            },
            "approval_decision": {
                "institutional_manuscript_approval_required": True,
                "institutional_manuscript_approval_status": "APPROVED",
                "approved_manuscript_file": "output/private_submission/manuscript.pdf",
                "approved_manuscript_sha256": hashlib.sha256(manuscript).hexdigest(),
                "target_journal": "Applied Intelligence",
                "approval_date": "2026-09-14",
                "conditions_or_none": "NONE",
            },
            "manual_review": {
                "reviewer_role": "Responsible author",
                "review_date": "2026-09-14",
                "record_visually_inspected": True,
                "metadata_matches_record": True,
                "approved_manuscript_digest_recomputed": True,
            },
        }

    def test_template_is_placeholder_only(self):
        result = validate(self.template, check_template=True)
        self.assertEqual(result["decision"], "PASS_INSTITUTIONAL_MANUSCRIPT_APPROVAL_TEMPLATE_AND_PRIVACY_BOUNDARY")
        self.assertFalse(result["complete"])
        self.assertFalse(result["submission_authorized"])

    def test_unfilled_template_fails_closed(self):
        result = validate(self.template)
        self.assertEqual(result["decision"], "FAIL_CLOSED_INSTITUTIONAL_MANUSCRIPT_APPROVAL_INCOMPLETE_OR_INVALID")
        self.assertFalse(result["complete"])
        self.assertFalse(result["private_values_emitted"])

    def test_complete_synthetic_record_only_passes_integrity_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence_path = root / "approval.pdf"
            manuscript_path = root / "manuscript.pdf"
            result = validate(
                self._complete(evidence_path, manuscript_path),
                evidence_path_override=evidence_path,
                manuscript_path_override=manuscript_path,
            )
        self.assertEqual(result["decision"], "PASS_PRIVATE_INSTITUTIONAL_MANUSCRIPT_APPROVAL_INTEGRITY_PREFLIGHT_PENDING_CLIENT_CONTENT_AND_FINAL_AUDITS")
        self.assertTrue(result["complete"])
        self.assertTrue(result["evidence_sha256_matches"])
        self.assertTrue(result["approved_manuscript_sha256_matches"])
        self.assertFalse(result["content_independently_certified"])
        self.assertFalse(result["p0_i_closed"])
        self.assertFalse(result["submission_authorized"])

    def test_pending_approval_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = self._complete(root / "approval.pdf", root / "manuscript.pdf")
            data["approval_decision"]["institutional_manuscript_approval_status"] = "PENDING"
            result = validate(data, evidence_path_override=root / "approval.pdf", manuscript_path_override=root / "manuscript.pdf")
        self.assertIn("approval_decision.institutional_manuscript_approval_status: must be APPROVED", result["validation_error_paths"])

    def test_manuscript_hash_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = self._complete(root / "approval.pdf", root / "manuscript.pdf")
            data["approval_decision"]["approved_manuscript_sha256"] = "0" * 64
            result = validate(data, evidence_path_override=root / "approval.pdf", manuscript_path_override=root / "manuscript.pdf")
        self.assertIn("approval_decision.approved_manuscript_sha256: does not match local manuscript bytes", result["validation_error_paths"])

    def test_non_applied_intelligence_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = self._complete(root / "approval.pdf", root / "manuscript.pdf")
            data["approval_decision"]["target_journal"] = "Different Journal"
            result = validate(data, evidence_path_override=root / "approval.pdf", manuscript_path_override=root / "manuscript.pdf")
        self.assertIn("approval_decision.target_journal: must equal Applied Intelligence", result["validation_error_paths"])


if __name__ == "__main__":
    unittest.main()
