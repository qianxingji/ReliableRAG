"""Tests for bounded PDF external-closure evidence census."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_pdf_external_closure_evidence import audit


def clean_extractor(source: Path | bytes) -> tuple[int, bytes, bytes]:
    return 0, b"ordinary extracted text", b""


def no_attachments(source: Path | bytes) -> tuple[int, bytes, bytes]:
    return 0, b"0 embedded files\n", b""


class PdfExternalClosureEvidenceTests(unittest.TestCase):
    def test_ordinary_pdf_is_extracted_without_path_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "document.pdf").write_bytes(b"synthetic pdf")
            result = audit((root,), extractor=clean_extractor, attachment_inspector=no_attachments)
        self.assertEqual(result["ordinary_pdfs_extracted"], 1)
        self.assertEqual(result["candidate_match_count"], 0)
        self.assertNotIn("document.pdf", str(result))

    def test_marker_candidate_reports_hash_without_text(self):
        marker = b"institutional manuscript approval"

        def extractor(source: Path | bytes) -> tuple[int, bytes, bytes]:
            return 0, marker, b""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "record.pdf").write_bytes(b"synthetic pdf")
            result = audit((root,), extractor=extractor, attachment_inspector=no_attachments)
        self.assertEqual(result["candidate_match_count"], 1)
        self.assertNotIn(marker.decode(), str(result))
        self.assertIsNone(result["bounded_interpretation"]["institutional_record_recovered"])

    def test_zip_pdf_member_is_read_without_archive_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "bundle.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("nested/document.pdf", b"synthetic pdf")
            result = audit((archive,), extractor=clean_extractor, attachment_inspector=no_attachments)
        self.assertEqual(result["zip_pdf_members_extracted"], 1)
        self.assertFalse(result["archives_extracted"])
        self.assertEqual(result["zip_pdf_members_temporarily_materialized_for_attachment_inventory"], 1)

    def test_attachment_inventory_is_counted_without_names(self):
        def attachments(source: Path | bytes) -> tuple[int, bytes, bytes]:
            return 0, b"2 embedded files\n1: secret.txt\n2: record.pdf\n", b""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "document.pdf").write_bytes(b"synthetic pdf")
            result = audit((root,), extractor=clean_extractor, attachment_inspector=attachments)
        self.assertEqual(result["embedded_attachment_count"], 2)
        self.assertNotIn("secret.txt", str(result))
        self.assertTrue(result["bounded_interpretation"]["embedded_attachments_present"])
        self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_size_cap_error_and_ocr_limits_remain_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.pdf").write_bytes(b"x" * 11)
            result = audit(
                (root,),
                max_pdf_bytes=10,
                extractor=clean_extractor,
                attachment_inspector=no_attachments,
            )
        self.assertEqual(result["ordinary_pdfs_skipped"], 1)
        self.assertTrue(result["decision"].startswith("REVIEW_"))
        self.assertFalse(result["bounded_interpretation"]["pdf_image_ocr_performed"])
        self.assertFalse(result["bounded_interpretation"]["absence_outside_scanned_roots_proved"])


if __name__ == "__main__":
    unittest.main()
