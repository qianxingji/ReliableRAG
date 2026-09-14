"""Tests for the privacy-safe responsible-author one-reply packet."""

from __future__ import annotations

import copy
import json
import unittest

from scripts.build_cas_q3_owner_reply_packet import build
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
        self.assertIn("authorship.authors_in_order[0].orcid", content)
        self.assertFalse(receipt["personal_values_emitted"])
        self.assertFalse(receipt["submission_authorized"])

    def test_invalid_structure_refuses_to_generate(self):
        self.value["schema_version"] = 99
        with self.assertRaisesRegex(ValueError, "validation errors"):
            build(self.value)


if __name__ == "__main__":
    unittest.main()
