"""Tests for the private P0-G institutional release-record preflight."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.verify_cas_q3_institutional_release_record import (
    AGGREGATE_V2_SHA256,
    TEMPLATE,
    validate,
)


class InstitutionalReleaseRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def _complete(self, evidence_path: Path, *, review_required: bool = False) -> dict:
        content = b"synthetic owner and institutional release record fixture\n"
        evidence_path.write_bytes(content)
        return {
            "schema_version": 1,
            "evidence": {
                "file": "evidence/private/institutional_release_record/example.pdf",
                "sha256": hashlib.sha256(content).hexdigest(),
                "kind": "OWNER_INSTITUTION_EVIDENCE_BUNDLE",
                "issuing_office_or_evidence_bundle_owner": "Example institutional office",
                "obtained_date": "2026-09-14",
                "authenticated_or_formally_retained": True,
            },
            "license_decision": {
                "project_code_license": "Apache-2.0",
                "legal_copyright_holder": "Example Holder",
                "copyright_year_or_range": "2026",
                "holder_may_license_project_authored_material": True,
                "institutional_release_review_required": review_required,
                "institutional_release_review_status": "APPROVED" if review_required else "NOT_REQUIRED",
                "project_specific_notice_required": False,
                "notice_decision_evidence": "NOT_REQUIRED",
            },
            "third_party_scope_decision": {
                "qwen_boundary_decision": "ACCEPTED_FOR_PUBLICATION_AND_NO_WEIGHT_RELEASE_SCOPE",
                "deberta_boundary_decision": "ACCEPTED_FOR_PUBLICATION_AND_NO_WEIGHT_RELEASE_SCOPE",
                "qwen_weights_in_release": False,
                "deberta_weights_in_release": False,
                "benchmark_payloads_or_answers_in_release": False,
                "per_question_records_in_release": False,
                "aggregate_v2_candidate_sha256": AGGREGATE_V2_SHA256,
                "aggregate_v2_scope_reviewed": True,
            },
            "manual_review": {
                "reviewer_role": "Responsible author",
                "review_date": "2026-09-14",
                "record_visually_inspected": True,
                "metadata_matches_record": True,
                "legal_advice_not_claimed_unless_issued_by_counsel": True,
            },
        }

    def test_template_is_placeholder_only(self):
        result = validate(self.template, check_template=True)
        self.assertEqual(result["decision"], "PASS_INSTITUTIONAL_RELEASE_RECORD_TEMPLATE_AND_PRIVACY_BOUNDARY")
        self.assertFalse(result["complete"])
        self.assertFalse(result["distribution_authorized"])

    def test_unfilled_template_fails_closed(self):
        result = validate(self.template)
        self.assertEqual(result["decision"], "FAIL_CLOSED_INSTITUTIONAL_RELEASE_RECORD_INCOMPLETE_OR_INVALID")
        self.assertFalse(result["complete"])
        self.assertIn("license_decision.legal_copyright_holder", result["missing_field_paths"])
        self.assertFalse(result["private_values_emitted"])

    def test_complete_synthetic_record_only_passes_integrity_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            result = validate(self._complete(evidence_path), evidence_path_override=evidence_path)
        self.assertEqual(
            result["decision"],
            "PASS_PRIVATE_INSTITUTIONAL_RELEASE_RECORD_INTEGRITY_PREFLIGHT_PENDING_CLIENT_AND_OWNER_DECISIONS",
        )
        self.assertTrue(result["complete"])
        self.assertTrue(result["evidence_sha256_matches"])
        self.assertFalse(result["content_independently_certified"])
        self.assertTrue(result["explicit_owner_archive_authorization_required"])
        self.assertFalse(result["p0_g_closed"])
        self.assertFalse(result["distribution_authorized"])

    def test_required_institutional_review_must_be_approved(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path, review_required=True)
            data["license_decision"]["institutional_release_review_status"] = "PENDING"
            result = validate(data, evidence_path_override=evidence_path)
        self.assertIn(
            "license_decision.institutional_release_review_status: must be APPROVED",
            result["validation_error_paths"],
        )

    def test_candidate_hash_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path)
            data["third_party_scope_decision"]["aggregate_v2_candidate_sha256"] = "0" * 64
            result = validate(data, evidence_path_override=evidence_path)
        self.assertIn(
            "third_party_scope_decision.aggregate_v2_candidate_sha256: unexpected candidate",
            result["validation_error_paths"],
        )

    def test_any_model_weight_release_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path)
            data["third_party_scope_decision"]["qwen_weights_in_release"] = True
            result = validate(data, evidence_path_override=evidence_path)
        self.assertIn(
            "third_party_scope_decision.qwen_weights_in_release: must be false",
            result["validation_error_paths"],
        )

    def test_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "example.pdf"
            data = self._complete(evidence_path)
            data["evidence"]["sha256"] = "0" * 64
            result = validate(data, evidence_path_override=evidence_path)
        self.assertIn("evidence.sha256: does not match local evidence bytes", result["validation_error_paths"])


if __name__ == "__main__":
    unittest.main()
