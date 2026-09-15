"""Tests for the bounded external-closure evidence census."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_external_closure_evidence_census import audit


class ExternalClosureEvidenceCensusTests(unittest.TestCase):
    def test_clean_root_reports_bounded_no_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.txt").write_text("ordinary project note", encoding="utf-8")
            result = audit((root,))
        self.assertEqual(result["decision"], "PASS_BOUNDED_ACCESSIBLE_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_RECOVERY")
        self.assertEqual(result["candidate_match_count"], 0)
        self.assertFalse(result["bounded_interpretation"]["absence_outside_scanned_roots_proved"])
        self.assertFalse(result["submission_authorized"])

    def test_ordinary_text_candidate_is_hash_reported_without_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = "institutional manuscript approval for Applied Intelligence"
            (root / "record.txt").write_text(marker, encoding="utf-8")
            result = audit((root,))
        self.assertEqual(result["candidate_match_count"], 1)
        self.assertNotIn(marker, str(result))
        self.assertEqual(result["candidate_matches"][0]["scope"], "ordinary_text")

    def test_zip_member_candidate_is_detected_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "bundle.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("nested/record.md", "2025 CAS Journal Partition")
            result = audit((archive,))
        self.assertEqual(result["zip_archives_scanned"], 1)
        self.assertEqual(result["zip_text_members_scanned"], 1)
        self.assertEqual(result["candidate_match_count"], 1)
        self.assertFalse(result["archives_extracted"])

    def test_large_text_and_excluded_directory_are_not_claimed_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.txt").write_bytes(b"x" * 11)
            excluded = root / ".git"
            excluded.mkdir()
            (excluded / "record.txt").write_text("Applied Intelligence", encoding="utf-8")
            result = audit((root,), max_text_bytes=10)
        self.assertEqual(result["ordinary_large_text_files_skipped"], 1)
        self.assertEqual(result["candidate_match_count"], 0)
        self.assertFalse(result["bounded_interpretation"]["large_skipped_files_proved_irrelevant"])


if __name__ == "__main__":
    unittest.main()
