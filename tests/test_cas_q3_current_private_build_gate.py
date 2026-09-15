"""Tests for the current private owner-input pre-transport gate verifier."""

from __future__ import annotations

import copy
import json
import unittest

from scripts.verify_cas_q3_current_private_build_gate import TEMPLATE, evaluate, validate


class CurrentPrivateBuildGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_empty_template_is_rejected_before_transport_or_output(self):
        missing = len(validate(self.template)["missing_field_paths"])
        result = evaluate(
            self.template,
            expected_missing=missing,
            input_matches_empty_template=True,
        )
        self.assertEqual(result["decision"], "PASS_OWNER_INPUT_GATE_REJECTS_BEFORE_TRANSPORT_OR_OUTPUT")
        self.assertFalse(result["transport_access_attempted"])
        self.assertFalse(result["output_created"])
        self.assertFalse(result["author_populated_package_built"])

    def test_partial_private_values_are_not_emitted(self):
        value = copy.deepcopy(self.template)
        secret = "PRIVATE_SENTINEL_8Q4J"
        value["authorship"]["corresponding_author_name"] = secret
        missing = len(validate(value)["missing_field_paths"])
        result = evaluate(
            value,
            expected_missing=missing,
            input_matches_empty_template=False,
        )
        self.assertNotIn(secret, json.dumps(result))
        self.assertFalse(result["private_values_emitted"])
        self.assertFalse(result["private_input_hash_emitted"])

    def test_wrong_expected_missing_count_fails(self):
        missing = len(validate(self.template)["missing_field_paths"])
        result = evaluate(
            self.template,
            expected_missing=missing + 1,
            input_matches_empty_template=True,
        )
        self.assertEqual(
            result["decision"],
            "FAIL_OWNER_INPUT_GATE_DID_NOT_PRESERVE_PRE_TRANSPORT_BOUNDARY",
        )


if __name__ == "__main__":
    unittest.main()
