"""Tests for the private owner-input structure and fail-closed semantics."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.verify_cas_q3_owner_inputs import TEMPLATE, validate


class OwnerInputsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_tracked_template_has_no_identity_and_is_structurally_valid(self):
        result = validate(self.template, template_mode=True)
        self.assertEqual(result["decision"], "PASS_OWNER_INPUTS_TEMPLATE_STRUCTURE_AND_PRIVACY_BOUNDARY")
        self.assertFalse(result["complete"])
        self.assertFalse(result["personal_values_emitted"])

    def test_unfilled_template_fails_closed_without_echoing_values(self):
        result = validate(self.template)
        self.assertEqual(result["decision"], "FAIL_CLOSED_OWNER_INPUTS_INCOMPLETE_OR_INVALID")
        self.assertFalse(result["complete"])
        self.assertIn("project_license.selected_option", result["missing_field_paths"])
        self.assertIn("target_journal.verified_tier=Q3", result["missing_field_paths"])
        self.assertFalse(result["personal_values_emitted"])

    def test_complete_synthetic_input_passes_only_to_independent_gates(self):
        value = copy.deepcopy(self.template)
        value["project_license"] = {
            "selected_option": "Apache-2.0",
            "legal_copyright_holder": "Example Holder",
            "copyright_year_or_range": "2026",
            "holder_may_license_project_authored_material": True,
            "institutional_release_review_required": False,
            "release_review_status": "NOT_REQUIRED",
            "notice_or_review_evidence": "Owner attestation retained privately",
        }
        value["target_journal"] = {
            "selected_journal": "Example Journal",
            "current_title": "Example Journal",
            "print_issn": "1234-5678",
            "online_issn": "8765-4321",
            "institution_recognized_cas_edition_year": "2026",
            "category_basis": "MAJOR",
            "category_name": "Computer Science",
            "verified_tier": "Q3",
            "title_issn_change_treatment": "Current title accepted",
            "recognition_date_rule": "Submission date",
            "retained_authority_path_or_url": "private/authority.pdf",
            "institutional_verifier_or_office": "Research Office",
            "verification_date": "2026-09-13",
            "publication_charge_route": "ACCEPTED",
            "publication_charge_evidence_or_acknowledgement": "Current official charge reviewed and payer retained privately",
            "data_code_policy_summary": "Aggregate package permitted",
            "data_code_policy_source_url": "https://example.org/policy",
        }
        value["authorship"]["authors_in_order"] = [
            {"name": "Example Author", "affiliation_ids": ["aff1"], "orcid": "NONE_NOT_SUPPLIED"}
        ]
        value["authorship"]["affiliations"] = [
            {
                "id": "aff1",
                "institution": "Example University",
                "department": "Department",
                "city": "City",
                "postal_code": "000000",
                "country": "Country",
            }
        ]
        value["authorship"]["corresponding_author_name"] = "Example Author"
        value["authorship"]["corresponding_author_email"] = "author@example.org"
        value["authorship"]["corresponding_author_postal_address"] = "Example address"
        for role in value["authorship"]["credit_role_mapping"]:
            if role in {
                "Conceptualization",
                "Methodology",
                "Software",
                "Validation",
                "Formal analysis",
                "Writing - original draft",
                "Writing - review and editing",
                "Supervision",
                "Project administration",
            }:
                value["authorship"]["credit_role_mapping"][role] = ["Example Author"]
        value["declarations"].update(
            {
                "funding_statement": "No external funding",
                "competing_interests_statement": "None declared",
                "ethics_statement_or_approval": "Not applicable under institutional policy",
                "acknowledgements": "NONE",
                "ai_assistance_statement_approved": True,
                "ai_tool_version_and_use_dates": "OpenAI ChatGPT/Codex, 2026",
                "originality_confirmed": True,
                "exclusive_submission_confirmed": True,
                "all_authors_approved_final_manuscript_and_order": True,
                "overlapping_work_or_preprint_disclosure": "NONE_DISCLOSED",
                "institutional_manuscript_approval_required": False,
                "institutional_manuscript_approval_status": "NOT_REQUIRED",
                "institutional_manuscript_approval_evidence": "Responsible-author attestation retained privately",
            }
        )
        result = validate(value)
        self.assertEqual(result["decision"], "PASS_OWNER_INPUTS_COMPLETE_PENDING_INDEPENDENT_EVIDENCE_AND_ARTIFACT_GATES")
        self.assertTrue(result["complete"])
        self.assertFalse(result["independent_cas_authority_verified"])
        self.assertFalse(result["distribution_authorized"])
        self.assertFalse(result["submission_authorized"])

    def test_charge_route_without_evidence_or_acknowledgement_cannot_pass(self):
        value = copy.deepcopy(self.template)
        value["target_journal"]["publication_charge_route"] = "ACCEPTED"
        result = validate(value)
        self.assertIn(
            "target_journal.publication_charge_evidence_or_acknowledgement",
            result["missing_field_paths"],
        )

    def test_false_author_approval_cannot_pass(self):
        value = copy.deepcopy(self.template)
        value["declarations"]["all_authors_approved_final_manuscript_and_order"] = False
        result = validate(value)
        self.assertIn(
            "declarations.all_authors_approved_final_manuscript_and_order=true",
            result["missing_field_paths"],
        )

    def test_optional_orcid_postal_address_and_acknowledgements_do_not_block(self):
        value = copy.deepcopy(self.template)
        value["authorship"]["authors_in_order"] = [
            {"name": "Example Author", "affiliation_ids": ["aff1"], "orcid": None}
        ]
        value["authorship"]["affiliations"] = [
            {"id": "aff1", "institution": "U", "department": "D", "city": "C", "postal_code": "0", "country": "X"}
        ]
        value["authorship"]["credit_role_mapping"]["Conceptualization"] = ["Example Author"]
        result = validate(value)
        self.assertNotIn("authorship.authors_in_order[0].orcid", result["missing_field_paths"])
        self.assertNotIn("authorship.corresponding_author_postal_address", result["missing_field_paths"])
        self.assertNotIn("declarations.acknowledgements", result["missing_field_paths"])
        self.assertNotIn("authorship.authors_in_order[0].credit_role_assignment", result["missing_field_paths"])

    def test_every_author_needs_at_least_one_truthful_credit_role(self):
        value = copy.deepcopy(self.template)
        value["authorship"]["authors_in_order"] = [
            {"name": "Example Author", "affiliation_ids": ["aff1"], "orcid": None}
        ]
        value["authorship"]["affiliations"] = [
            {"id": "aff1", "institution": "U", "department": "D", "city": "C", "postal_code": "0", "country": "X"}
        ]
        result = validate(value)
        self.assertIn("authorship.authors_in_order[0].credit_role_assignment", result["missing_field_paths"])


if __name__ == "__main__":
    unittest.main()
