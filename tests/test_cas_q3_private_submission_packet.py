"""Privacy and fail-closed tests for the local identity/declaration builder."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts.build_cas_q3_private_submission_packet import build, tex
from scripts.verify_cas_q3_author_intake import executable
from scripts.verify_cas_q3_owner_inputs import TEMPLATE


def complete_fixture() -> dict:
    value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    value["project_license"] = {
        "selected_option": "Apache-2.0",
        "legal_copyright_holder": "Example Holder",
        "copyright_year_or_range": "2026",
        "holder_may_license_project_authored_material": True,
        "institutional_release_review_required": False,
        "release_review_status": "NOT_REQUIRED",
        "notice_or_review_evidence": "Private attestation",
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
        {"name": "A_uthor & Co", "affiliation_ids": ["aff1"], "orcid": "NONE_NOT_SUPPLIED"}
    ]
    value["authorship"]["affiliations"] = [
        {"id": "aff1", "institution": "U%", "department": "D#", "city": "C", "postal_code": "0", "country": "X"}
    ]
    value["authorship"]["corresponding_author_name"] = "A_uthor & Co"
    value["authorship"]["corresponding_author_email"] = "private@example.org"
    value["authorship"]["corresponding_author_postal_address"] = "Private address"
    required = {
        "Conceptualization", "Methodology", "Software", "Validation", "Formal analysis",
        "Writing - original draft", "Writing - review and editing", "Supervision", "Project administration",
    }
    for role in value["authorship"]["credit_role_mapping"]:
        if role in required:
            value["authorship"]["credit_role_mapping"][role] = ["A_uthor & Co"]
    value["declarations"].update(
        {
            "funding_statement": "No external funding",
            "competing_interests_statement": "None declared",
            "ethics_statement_or_approval": "Not applicable",
            "acknowledgements": "NONE",
            "ai_assistance_statement_approved": True,
            "ai_tool_version_and_use_dates": "OpenAI ChatGPT/Codex, 2026",
            "originality_confirmed": True,
            "exclusive_submission_confirmed": True,
            "all_authors_approved_final_manuscript_and_order": True,
            "overlapping_work_or_preprint_disclosure": "NONE_DISCLOSED",
            "institutional_manuscript_approval_required": False,
            "institutional_manuscript_approval_status": "NOT_REQUIRED",
            "institutional_manuscript_approval_evidence": "Private attestation",
        }
    )
    return value


class PrivateSubmissionPacketTests(unittest.TestCase):
    def test_executable_lookup_is_portable_without_windows_localappdata(self):
        with mock.patch("scripts.verify_cas_q3_author_intake.shutil.which", return_value=None):
            with mock.patch.dict("scripts.verify_cas_q3_author_intake.os.environ", {}, clear=True):
                with self.assertRaisesRegex(RuntimeError, "missing executable: pdflatex"):
                    executable("pdflatex")

    def test_tex_escapes_identity_metacharacters(self):
        self.assertEqual(
            tex("A_#%&$~^{}" + chr(92)),
            r"A\_\#\%\&\$\textasciitilde{}\textasciicircum{}\{\}\textbackslash{}",
        )

    def test_incomplete_input_fails_before_output_creation(self):
        value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            with self.assertRaisesRegex(ValueError, "incomplete or invalid"):
                build(value, output)
            self.assertFalse(output.exists())

    def test_private_packet_is_built_but_never_authorized(self):
        value = complete_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            receipt = build(value, output)
            self.assertEqual(set(receipt["files"]), {"cover_letter.md", "declarations.tex", "title_page.tex"})
            self.assertFalse(receipt["submission_authorized"])
            self.assertFalse(receipt["distribution_authorized"])
            self.assertFalse(receipt["independent_cas_authority_verified"])
            title = (output / "title_page.tex").read_text(encoding="utf-8")
            self.assertIn(r"A\_uthor \& Co", title)
            self.assertIn(r"U\%", title)
            receipt_text = (output / "PRIVATE_BUILD_RECEIPT.json").read_text(encoding="utf-8")
            for private_value in ("A_uthor", "private@example.org", "Private address", "Example Journal"):
                self.assertNotIn(private_value, receipt_text)

    def test_existing_output_is_not_overwritten(self):
        value = complete_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            output.mkdir()
            marker = output / "marker.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                build(copy.deepcopy(value), output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_optional_identity_and_acknowledgement_fields_are_omitted_cleanly(self):
        value = complete_fixture()
        value["authorship"]["authors_in_order"][0]["orcid"] = None
        value["authorship"]["corresponding_author_postal_address"] = None
        value["declarations"]["acknowledgements"] = None
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            build(value, output)
            title = (output / "title_page.tex").read_text(encoding="utf-8")
            declarations = (output / "declarations.tex").read_text(encoding="utf-8")
            self.assertNotIn("ORCID", title)
            self.assertNotIn("Acknowledgements", declarations)
            self.assertNotIn("None", title)

    def test_synthetic_title_page_compiles_when_latex_is_available(self):
        try:
            pdflatex = executable("pdflatex")
        except RuntimeError:
            self.skipTest("pdflatex is not installed in this engineering environment")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            build(complete_fixture(), output)
            process = subprocess.run(
                [
                    pdflatex,
                    "--enable-installer",
                    "--interaction=nonstopmode",
                    "--halt-on-error",
                    f"-output-directory={output}",
                    str(output / "title_page.tex"),
                ],
                cwd=output,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=120,
            )
            self.assertEqual(process.returncode, 0, process.stdout[-3000:] + process.stderr[-3000:])
            self.assertTrue((output / "title_page.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
