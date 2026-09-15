"""Tests for streaming oversized external-closure evidence census."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_oversized_external_closure_evidence import audit


class OversizedExternalClosureEvidenceTests(unittest.TestCase):
    def test_large_clean_text_is_stream_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.txt").write_bytes(b"x" * 32)
            result = audit((root,), min_stream_bytes=10, max_stream_bytes=100)
        self.assertEqual(result["decision"], "PASS_BOUNDED_OVERSIZED_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES")
        self.assertEqual(result["ordinary_large_text_files_stream_scanned"], 1)
        self.assertEqual(result["ordinary_large_text_bytes_scanned"], 32)

    def test_marker_crossing_stream_chunk_boundary_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = b"x" * (1_048_576 - 8)
            (root / "large.txt").write_bytes(prefix + b"Applied Intelligence" + b"y" * 16)
            result = audit((root,), min_stream_bytes=10, max_stream_bytes=2_000_000)
        self.assertEqual(result["candidate_match_count"], 1)
        self.assertIsNone(result["bounded_interpretation"]["institutional_record_recovered"])

    def test_large_zip_member_is_streamed_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "bundle.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("nested/record.md", b"x" * 32)
            result = audit((archive,), min_stream_bytes=10, max_stream_bytes=100)
        self.assertEqual(result["zip_large_text_members_stream_scanned"], 1)
        self.assertEqual(result["zip_large_text_member_bytes_scanned"], 32)
        self.assertFalse(result["archives_extracted"])

    def test_stream_cap_and_excluded_descendant_remain_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "too_large.txt").write_bytes(b"x" * 101)
            excluded = root / ".git"
            excluded.mkdir()
            (excluded / "record.txt").write_bytes(b"Applied Intelligence" * 3)
            result = audit((root,), min_stream_bytes=10, max_stream_bytes=100)
        self.assertEqual(result["ordinary_too_large_text_files_skipped"], 1)
        self.assertEqual(result["candidate_match_count"], 0)
        self.assertFalse(result["bounded_interpretation"]["absence_outside_scanned_roots_proved"])


if __name__ == "__main__":
    unittest.main()
