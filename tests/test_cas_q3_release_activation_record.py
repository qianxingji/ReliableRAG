"""Tests for the fail-closed P0-G release-activation intake."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.verify_cas_q3_release_activation_record import (
    AGGREGATE_V2_SHA256,
    AUTHORIZATION_DECISION,
    REPOSITORY_URL,
    TEMPLATE,
    validate,
)


class ReleaseActivationRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def _complete(self, archive_path: Path, *, requested: bool = False) -> dict:
        archive_path.write_bytes(b"synthetic aggregate V2 archive fixture\n")
        archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        commit_sha = "a" * 40
        data = copy.deepcopy(self.template)
        data["release_authorization"] = {
            "institutional_release_record_sha256": "b" * 64,
            "institutional_release_record_decision": AUTHORIZATION_DECISION,
            "owner_distribution_authorized": True,
            "authorization_date": "2026-09-15",
        }
        data["repository_revision"] = {
            "repository_url": REPOSITORY_URL,
            "commit_sha": commit_sha,
            "immutable_commit_url": f"{REPOSITORY_URL}/commit/{commit_sha}",
            "final_submission_revision_frozen": True,
            "release_reference_kind": "GITHUB_RELEASE",
            "release_tag_or_not_applicable": "submission-v1",
            "release_url_or_not_applicable": f"{REPOSITORY_URL}/releases/tag/submission-v1",
            "release_reference_matches_commit": True,
        }
        data["archive"] = {
            "kind": "AUTHORIZED_SUCCESSOR",
            "file": "evidence/private/release_activation/archive.zip",
            "sha256": archive_sha,
            "manifest_sha256": "c" * 64,
            "source_aggregate_v2_sha256": AGGREGATE_V2_SHA256,
            "successor_reason_or_not_applicable": "Synthetic fixture differs from the frozen V2 bytes.",
            "model_weights_in_archive": False,
            "benchmark_payloads_answers_or_per_question_records_in_archive": False,
        }
        data["persistent_record"] = {
            "identifier_kind": "DOI",
            "identifier": "10.0000/synthetic.fixture",
            "landing_url": "https://doi.org/10.0000/synthetic.fixture",
            "resolution_status": "VERIFIED_RESOLVING",
            "landing_record_binds_exact_archive_sha256": True,
        }
        data["restricted_review_access"] = {
            "editor_request_status": "REQUESTED" if requested else "NOT_REQUESTED",
            "channel_status": "EDITOR_DESIGNATED_OR_ACCEPTED" if requested else "NOT_APPLICABLE",
            "delivery_evidence_reference_or_not_applicable": "private receipt" if requested else "NOT_APPLICABLE",
            "access_terms_or_not_applicable": "review-only access" if requested else "NOT_APPLICABLE",
            "recipient_role_or_not_applicable": "handling editor recipient" if requested else "NOT_APPLICABLE",
            "delivery_date_or_not_applicable": "2026-09-15" if requested else "NOT_APPLICABLE",
            "no_unrequested_private_distribution": True,
        }
        data["manual_review"] = {
            "reviewer_role": "Responsible author",
            "review_date": "2026-09-15",
            "authorization_record_compared_to_activation_record": True,
            "commit_url_compared_to_commit_sha": True,
            "archive_hash_compared_to_retained_bytes": True,
            "persistent_landing_record_visually_inspected": True,
            "legal_advice_not_claimed_unless_issued_by_counsel": True,
        }
        return data

    def test_template_is_placeholder_and_never_authorizes(self):
        result = validate(self.template, check_template=True)
        self.assertEqual(
            result["decision"],
            "PASS_RELEASE_ACTIVATION_RECORD_TEMPLATE_AND_FAIL_CLOSED_BOUNDARY",
        )
        self.assertFalse(result["complete"])
        self.assertFalse(result["distribution_authorized_by_verifier"])

    def test_unfilled_template_fails_closed(self):
        result = validate(self.template)
        self.assertEqual(result["decision"], "FAIL_CLOSED_RELEASE_ACTIVATION_RECORD_INCOMPLETE_OR_INVALID")
        self.assertFalse(result["complete"])
        self.assertFalse(result["private_values_emitted"])

    def test_complete_synthetic_record_is_only_structurally_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.zip"
            result = validate(self._complete(path), archive_path_override=path)
        self.assertEqual(
            result["decision"],
            "PASS_RELEASE_ACTIVATION_RECORD_STRUCTURALLY_COMPLETE_PENDING_CLIENT_CONTENT_FINAL_ARTIFACT_AND_ASTRA_AUDITS",
        )
        self.assertTrue(result["complete"])
        self.assertTrue(result["archive_sha256_matches"])
        self.assertTrue(result["record_asserts_owner_authorization"])
        self.assertTrue(result["astra_xhigh_final_audit_required"])
        self.assertFalse(result["distribution_authorized_by_verifier"])
        self.assertFalse(result["p0_g_closed"])

    def test_commit_url_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.zip"
            data = self._complete(path)
            data["repository_revision"]["immutable_commit_url"] = REPOSITORY_URL + "/commit/" + "d" * 40
            result = validate(data, archive_path_override=path)
        self.assertIn(
            "repository_revision.immutable_commit_url: must bind the exact commit SHA",
            result["validation_error_paths"],
        )

    def test_v2_kind_rejects_substituted_archive_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.zip"
            data = self._complete(path)
            data["archive"]["kind"] = "CAS_Q3_AGGREGATE_V2"
            data["archive"]["successor_reason_or_not_applicable"] = "NOT_APPLICABLE"
            result = validate(data, archive_path_override=path)
        self.assertIn(
            "archive.sha256: exact aggregate V2 hash required for this kind",
            result["validation_error_paths"],
        )

    def test_archive_byte_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.zip"
            data = self._complete(path)
            data["archive"]["sha256"] = "e" * 64
            result = validate(data, archive_path_override=path)
        self.assertIn("archive.sha256: does not match retained archive bytes", result["validation_error_paths"])

    def test_unrequested_access_requires_not_applicable_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.zip"
            data = self._complete(path)
            data["restricted_review_access"]["channel_status"] = "EDITOR_DESIGNATED_OR_ACCEPTED"
            result = validate(data, archive_path_override=path)
        self.assertIn(
            "restricted_review_access.channel_status: must be NOT_APPLICABLE",
            result["validation_error_paths"],
        )

    def test_requested_access_requires_editor_channel(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.zip"
            data = self._complete(path, requested=True)
            data["restricted_review_access"]["channel_status"] = "AUTHOR_SELECTED_CHANNEL"
            result = validate(data, archive_path_override=path)
        self.assertIn(
            "restricted_review_access.channel_status: must be EDITOR_DESIGNATED_OR_ACCEPTED",
            result["validation_error_paths"],
        )


if __name__ == "__main__":
    unittest.main()
