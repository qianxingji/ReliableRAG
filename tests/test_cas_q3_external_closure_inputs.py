"""Tests for the combined private P0-G/H/I closure preflight."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.verify_cas_q3_external_closure_inputs import evaluate, template_check
from scripts.verify_cas_q3_institutional_cas_record import TEMPLATE as CAS_TEMPLATE
from scripts.verify_cas_q3_institutional_release_record import (
    AGGREGATE_V2_SHA256,
    TEMPLATE as RELEASE_TEMPLATE,
)
from scripts.verify_cas_q3_owner_inputs import TEMPLATE as OWNER_TEMPLATE


def complete_owner() -> dict:
    value = copy.deepcopy(json.loads(OWNER_TEMPLATE.read_text(encoding="utf-8")))
    value["project_license"] = {
        "selected_option": "Apache-2.0",
        "legal_copyright_holder": "Synthetic Holder",
        "copyright_year_or_range": "2026",
        "holder_may_license_project_authored_material": True,
        "institutional_release_review_required": False,
        "release_review_status": "NOT_REQUIRED",
        "notice_or_review_evidence": "Synthetic retained evidence",
    }
    value["target_journal"] = {
        "selected_journal": "Applied Intelligence",
        "current_title": "Applied Intelligence",
        "print_issn": "0924-669X",
        "online_issn": "1573-7497",
        "institution_recognized_cas_edition_year": "2025",
        "category_basis": "MAJOR",
        "category_name": "Computer Science",
        "verified_tier": "Q3",
        "title_issn_change_treatment": "Current title and ISSNs control",
        "recognition_date_rule": "Formal publication date",
        "retained_authority_path_or_url": "private/institution-record.pdf",
        "institutional_verifier_or_office": "Synthetic Research Office",
        "verification_date": "2026-09-14",
        "publication_charge_route": "NO_MANDATORY_APC",
        "publication_charge_evidence_or_acknowledgement": "Subscription route reviewed",
        "data_code_policy_summary": "Restricted aggregate evidence route",
        "data_code_policy_source_url": "https://example.org/policy",
    }
    value["authorship"]["authors_in_order"] = [
        {"name": "Synthetic Author", "affiliation_ids": ["aff1"], "orcid": None}
    ]
    value["authorship"]["affiliations"] = [
        {
            "id": "aff1",
            "institution": "Synthetic University",
            "department": "Synthetic Department",
            "city": "Synthetic City",
            "postal_code": "000000",
            "country": "Synthetic Country",
        }
    ]
    value["authorship"]["corresponding_author_name"] = "Synthetic Author"
    value["authorship"]["corresponding_author_email"] = "synthetic@example.org"
    value["authorship"]["credit_role_mapping"]["Conceptualization"] = ["Synthetic Author"]
    value["declarations"].update(
        {
            "funding_statement": "Synthetic funding statement",
            "competing_interests_statement": "Synthetic interests statement",
            "ethics_statement_or_approval": "Synthetic ethics statement",
            "ai_assistance_statement_approved": True,
            "ai_tool_version_and_use_dates": "Synthetic tool record",
            "originality_confirmed": True,
            "exclusive_submission_confirmed": True,
            "all_authors_approved_final_manuscript_and_order": True,
            "overlapping_work_or_preprint_disclosure": "Synthetic disclosure",
            "institutional_manuscript_approval_required": False,
            "institutional_manuscript_approval_status": "NOT_REQUIRED",
            "institutional_manuscript_approval_evidence": "Synthetic retained evidence",
        }
    )
    return value


def complete_cas(evidence_path: Path) -> dict:
    content = b"synthetic institutional CAS record\n"
    evidence_path.write_bytes(content)
    return {
        "schema_version": 1,
        "evidence": {
            "file": "evidence/private/institutional_cas_record/example.pdf",
            "sha256": hashlib.sha256(content).hexdigest(),
            "kind": "AUTHENTICATED_CAS_PLATFORM_EXPORT",
            "issuing_office": "Synthetic Research Office",
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
            "tier": "Q3",
            "recognition_date_rule": "Formal publication date",
            "title_issn_change_treatment": "Current title and ISSNs control",
            "applies_to_hbut_first_affiliation_output": True,
        },
        "manual_review": {
            "reviewer_role": "Synthetic responsible author",
            "review_date": "2026-09-14",
            "record_visually_inspected": True,
            "metadata_matches_record": True,
            "jcr_result_not_substituted": True,
        },
    }


def complete_release(evidence_path: Path) -> dict:
    content = b"synthetic institutional release record\n"
    evidence_path.write_bytes(content)
    return {
        "schema_version": 1,
        "evidence": {
            "file": "evidence/private/institutional_release_record/example.pdf",
            "sha256": hashlib.sha256(content).hexdigest(),
            "kind": "OWNER_INSTITUTION_EVIDENCE_BUNDLE",
            "issuing_office_or_evidence_bundle_owner": "Synthetic Research Office",
            "obtained_date": "2026-09-14",
            "authenticated_or_formally_retained": True,
        },
        "license_decision": {
            "project_code_license": "Apache-2.0",
            "legal_copyright_holder": "Synthetic Holder",
            "copyright_year_or_range": "2026",
            "holder_may_license_project_authored_material": True,
            "institutional_release_review_required": False,
            "institutional_release_review_status": "NOT_REQUIRED",
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
            "reviewer_role": "Synthetic responsible author",
            "review_date": "2026-09-14",
            "record_visually_inspected": True,
            "metadata_matches_record": True,
            "legal_advice_not_claimed_unless_issued_by_counsel": True,
        },
    }


class ExternalClosureInputsTests(unittest.TestCase):
    def test_all_templates_remain_public_placeholders(self):
        result = template_check()
        self.assertEqual(result["decision"], "PASS_EXTERNAL_CLOSURE_TEMPLATES_AND_PRIVACY_BOUNDARY")
        self.assertEqual(result["templates"], 3)
        self.assertFalse(result["complete"])
        self.assertFalse(result["private_values_emitted"])

    def test_missing_inputs_fail_closed_without_private_values(self):
        result = evaluate(None, None, None)
        self.assertFalse(result["complete"])
        self.assertEqual(
            result["decision"],
            "FAIL_CLOSED_PRIVATE_EXTERNAL_CLOSURE_INPUTS_INCOMPLETE_INVALID_OR_INCONSISTENT",
        )
        self.assertFalse(result["private_values_emitted"])

    def test_consistent_synthetic_inputs_only_pass_structural_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cas_path = root / "cas.pdf"
            release_path = root / "release.pdf"
            result = evaluate(
                complete_owner(),
                complete_cas(cas_path),
                complete_release(release_path),
                cas_evidence_override=cas_path,
                release_evidence_override=release_path,
            )
        self.assertTrue(result["complete"])
        self.assertEqual(
            result["decision"],
            "PASS_PRIVATE_EXTERNAL_CLOSURE_INPUTS_STRUCTURALLY_COMPLETE_PENDING_CLIENT_CONTENT_ARTIFACT_AND_ASTRA_AUDITS",
        )
        self.assertEqual(result["cross_consistency_error_count"], 0)
        self.assertTrue(result["client_content_audits_required"])
        self.assertTrue(result["final_astra_xhigh_audit_required"])
        self.assertFalse(result["p0_g_closed"])
        self.assertFalse(result["p0_h_closed"])
        self.assertFalse(result["p0_i_closed"])
        self.assertFalse(result["submission_authorized"])
        serialized = json.dumps(result)
        for private_value in ("Synthetic Author", "synthetic@example.org", "Synthetic Holder"):
            self.assertNotIn(private_value, serialized)

    def test_qualifying_but_inconsistent_tiers_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owner = complete_owner()
            owner["target_journal"]["verified_tier"] = "Q2"
            cas_path = root / "cas.pdf"
            release_path = root / "release.pdf"
            result = evaluate(
                owner,
                complete_cas(cas_path),
                complete_release(release_path),
                cas_evidence_override=cas_path,
                release_evidence_override=release_path,
            )
        self.assertFalse(result["complete"])
        self.assertIn("owner/cas.tier", result["cross_consistency_error_paths"])

    def test_legal_holder_mismatch_is_rejected_without_echoing_holders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = complete_release(root / "release.pdf")
            release["license_decision"]["legal_copyright_holder"] = "Different Synthetic Holder"
            result = evaluate(
                complete_owner(),
                complete_cas(root / "cas.pdf"),
                release,
                cas_evidence_override=root / "cas.pdf",
                release_evidence_override=root / "release.pdf",
            )
        self.assertFalse(result["complete"])
        self.assertIn("owner/release.legal_copyright_holder", result["cross_consistency_error_paths"])
        serialized = json.dumps(result)
        self.assertNotIn("Different Synthetic Holder", serialized)


if __name__ == "__main__":
    unittest.main()
