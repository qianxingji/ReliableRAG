"""Fail-closed behavior for the CAS Q3 submission-readiness gate."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_cas_q3_submission_readiness.py"
RECEIPT = ROOT / "docs" / "cas_q3" / "SUBMISSION_READINESS_VERIFICATION.json"


class SubmissionReadinessGateTests(unittest.TestCase):
    def test_current_external_gates_fail_closed_without_scientific_execution(self):
        process = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 2, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(
            result["decision"],
            "FAIL_CLOSED_CAS_Q3_NOT_READY_EXTERNAL_OWNER_INSTITUTION_AUTHOR_GATES",
        )
        self.assertFalse(result["submission_ready"])
        self.assertEqual(result["open_p0"], ["P0-G", "P0-H", "P0-I"])
        self.assertEqual(
            result["owner_input_intake"],
            {
                "decision": "FAIL_CLOSED_OWNER_INPUT_FILE_MISSING",
                "complete": False,
                "missing_field_count": 1,
                "validation_error_count": 0,
            },
        )
        self.assertFalse(result["scientific_payloads_read"])
        self.assertEqual(result["model_forwards"], 0)
        self.assertEqual(result["scientific_fits"], 0)
        self.assertEqual(result, json.loads(RECEIPT.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
