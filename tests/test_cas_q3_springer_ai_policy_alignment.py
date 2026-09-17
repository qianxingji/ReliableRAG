"""Tests for the current Springer Nature AI policy mapping."""

from __future__ import annotations

import unittest

from scripts.audit_cas_q3_springer_ai_policy_alignment import (
    PREVIOUS_CANDIDATE,
    REVISED_CANDIDATE,
    SOURCES,
    build,
    render,
)
from scripts.build_cas_q3_applied_intelligence_private_submission import AI_METHOD_ANCHOR


class SpringerAiPolicyAlignmentTests(unittest.TestCase):
    def test_policy_mapping_is_official_bounded_and_non_authorizing(self):
        result = build()
        self.assertEqual(
            result["decision"],
            "PARTIAL_PASS_CURRENT_SPRINGER_NATURE_AI_POLICY_MAPPED_AUTHOR_APPROVAL_FINAL_DATE_AND_ARTIFACT_OPEN",
        )
        self.assertEqual(result["cas_q3_status"], "NOT_READY")
        self.assertEqual(len(result["sources"]), 5)
        self.assertEqual(
            {source["url"].split("/")[2] for source in SOURCES},
            {"link.springer.com", "www.springernature.com", "group.springernature.com"},
        )
        self.assertFalse(result["policy_application"]["copy_editing_only_exception_applies"])
        self.assertTrue(result["policy_application"]["journal_specific_methods_documentation_required"])
        self.assertTrue(result["policy_application"]["prompt_scope_required"])
        self.assertEqual(result["project_use_classification"]["red_or_not_permitted_claimed"], [])
        self.assertFalse(result["candidate_revision"]["responsible_author_approval"])
        self.assertIsNone(result["candidate_revision"]["final_use_end_date"])
        self.assertEqual(result["synthetic_target_validation"]["compiled_pages"], 13)
        self.assertTrue(result["synthetic_target_validation"]["all_pages_visually_reviewed"])
        self.assertEqual(result["synthetic_target_validation"]["visual_defects_found"], 0)
        self.assertFalse(result["synthetic_target_validation"]["real_owner_package_built"])
        self.assertFalse(result["p0_i_closed"])
        self.assertFalse(result["submission_authorized"])
        self.assertEqual(result["target_artifact_rule"]["private_builder_path"], "scripts/build_cas_q3_applied_intelligence_private_submission.py")
        self.assertEqual(AI_METHOD_ANCHOR, r"\section{Results}")

    def test_revised_candidate_expands_truthful_scope_without_claiming_full_transcript(self):
        self.assertNotEqual(PREVIOUS_CANDIDATE, REVISED_CANDIDATE)
        for phrase in (
            "research-design and methodological option review",
            "statistical, and numerical-result checking",
            "Prompts instructed the tools",
            "did not fabricate or autonomously select data",
            "made all final research and submission decisions",
        ):
            self.assertIn(phrase, REVISED_CANDIDATE)
        result = build()
        self.assertTrue(result["candidate_revision"]["revised_candidate_covers_prompt_categories"])
        self.assertFalse(result["candidate_revision"]["revised_candidate_claims_verbatim_complete_prompt_transcript"])

    def test_acceptance_keeps_author_and_final_artifact_gates_open(self):
        text_value = render(build())
        self.assertIn("CAS Q3 STATUS: NOT READY", text_value)
        self.assertIn(REVISED_CANDIDATE, text_value)
        self.assertIn("不能作为当前政策下的完整声明", text_value)
        self.assertIn("不批准声明，不关闭 P0-I，不授权发布或投稿", text_value)


if __name__ == "__main__":
    unittest.main()
