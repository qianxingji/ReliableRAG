"""Tests for the privacy-safe responsible-author one-reply packet."""

from __future__ import annotations

import copy
import json
import unittest

from scripts.build_cas_q3_owner_reply_packet import (
    AI_ASSISTANCE_CANDIDATE,
    NO_COMPETING_INTERESTS_CANDIDATE,
    build,
)
from scripts.verify_cas_q3_owner_inputs import TEMPLATE


class OwnerReplyPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = copy.deepcopy(json.loads(TEMPLATE.read_text(encoding="utf-8")))

    def test_packet_lists_only_missing_paths_and_never_echoes_existing_private_values(self):
        self.value["authorship"]["authors_in_order"] = [
            {"name": "Sensitive Name 7QX", "affiliation_ids": ["aff1"], "orcid": None}
        ]
        self.value["authorship"]["affiliations"] = [
            {
                "id": "aff1",
                "institution": "Sensitive University 7QX",
                "department": None,
                "city": "Sensitive City 7QX",
                "postal_code": "700007",
                "country": "Sensitive Country 7QX",
            }
        ]
        self.value["authorship"]["corresponding_author_email"] = "private-7qx@example.org"
        self.value["declarations"]["funding_statement"] = "Sensitive funding text 7QX"
        content, receipt = build(self.value)
        for secret in (
            "Sensitive Name 7QX",
            "Sensitive University 7QX",
            "Sensitive City 7QX",
            "Sensitive Country 7QX",
            "700007",
            "private-7qx@example.org",
            "Sensitive funding text 7QX",
        ):
            self.assertNotIn(secret, content)
            self.assertNotIn(secret, json.dumps(receipt))
        self.assertIn("authorship.affiliations[0].department", content)
        self.assertNotIn("authorship.authors_in_order[0].orcid", content)
        self.assertIn("authorship.authors_in_order[0].credit_role_assignment", content)
        self.assertNotIn("院系/部门的正式中英文署名", content)
        self.assertNotIn("通讯作者正式署名", content)
        self.assertNotIn("通讯作者有效邮箱", content)
        self.assertFalse(receipt["personal_values_emitted"])
        self.assertFalse(receipt["submission_authorized"])

    def test_packet_exposes_reviewable_static_declaration_candidates(self):
        content, _ = build(self.value)
        self.assertIn(AI_ASSISTANCE_CANDIDATE, content)
        self.assertIn(NO_COMPETING_INTERESTS_CANDIDATE, content)
        self.assertIn("YYYY-MM-DD to YYYY-MM-DD", content)
        self.assertIn("P0_I_AI_TOOL_DATE_EVIDENCE.md", content)
        self.assertIn("这不是实际最早使用日", content)
        self.assertIn("最终起止日期仍须作者依据真实记录确认", content)
        self.assertIn("P0_I_AI_TOOL_SESSION_METADATA.md", content)
        self.assertIn("2026-09-10 to YYYY-MM-DD", content)
        self.assertIn("不能把它写成最终结束日", content)
        self.assertIn("evidence/private/institutional_manuscript_approval/", content)
        self.assertIn("evidence/private/institutional_release_record/", content)

    def test_invalid_structure_refuses_to_generate(self):
        self.value["schema_version"] = 99
        with self.assertRaisesRegex(ValueError, "validation errors"):
            build(self.value)


if __name__ == "__main__":
    unittest.main()
