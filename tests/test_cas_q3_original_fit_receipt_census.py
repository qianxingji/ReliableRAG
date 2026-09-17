"""Tests for the bounded original-fit receipt census."""

from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_original_fit_receipt_census import candidate_payload_matches, scan


class OriginalFitReceiptCensusTests(unittest.TestCase):
    def test_candidate_requires_receipt_marker_and_model_identity(self):
        specs = {"model_a": (3, hashlib.sha256(b"abc").hexdigest())}
        self.assertTrue(candidate_payload_matches(b"model_a matrix_sha256=123", specs))
        self.assertFalse(candidate_payload_matches(b"model_a ordinary summary", specs))
        self.assertFalse(candidate_payload_matches(b"matrix_sha256=123 unrelated", specs))

    def test_scan_finds_exact_copy_and_candidate_archive_member(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "model.bin"
            model.write_bytes(b"abc")
            archive = root / "history.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("fit_receipt.json", '{"model":"model_a","keys_sha256":"123"}')
            specs = {"model_a": (3, hashlib.sha256(b"abc").hexdigest())}
            result = scan([("fixture", root)], top_level_archive_root=None, specs=specs)
            self.assertEqual(result["decision"], "REVIEW_REQUIRED_CANDIDATE_ORIGINAL_FIT_RECEIPT_FOUND")
            self.assertEqual(result["counts"]["exact_original_model_hash_copies"], 1)
            self.assertEqual(result["counts"]["candidate_archive_members_with_receipt_markers_and_model_identity"], 1)
            self.assertFalse(result["interpretation"]["p0_1_authenticity_gap_closed"])

    def test_empty_scan_passes_only_as_bounded_no_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = scan([("fixture", Path(temporary))], top_level_archive_root=None, specs={})
            self.assertEqual(result["decision"], "PASS_BOUNDED_ACCESSIBLE_HISTORICAL_RECEIPT_CENSUS_NO_RECOVERY")
            self.assertFalse(result["interpretation"]["absence_outside_scanned_roots_proved"])


if __name__ == "__main__":
    unittest.main()
