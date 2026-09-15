"""Tests for the common document-container inventory."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_document_container_inventory import audit


class DocumentContainerInventoryTests(unittest.TestCase):
    def test_pdf_only_root_passes_without_content_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.pdf").write_bytes(b"not parsed")
            result = audit((root,))
        self.assertEqual(result["decision"], "PASS_BOUNDED_COMMON_DOCUMENT_CONTAINER_INVENTORY_PDF_ONLY")
        self.assertEqual(result["ordinary_file_counts"][".pdf"], 1)
        self.assertFalse(result["file_contents_read"])

    def test_non_pdf_document_requires_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "record.docx").write_bytes(b"not parsed")
            result = audit((root,))
        self.assertEqual(result["non_pdf_document_count"], 1)
        self.assertTrue(result["decision"].startswith("REVIEW_"))
        self.assertFalse(result["bounded_interpretation"]["unknown_binary_formats_covered"])

    def test_zip_members_are_counted_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "bundle.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("nested/paper.pdf", b"not parsed")
                handle.writestr("nested/sheet.xlsx", b"not parsed")
            result = audit((archive,))
        self.assertEqual(result["zip_member_counts"][".pdf"], 1)
        self.assertEqual(result["zip_member_counts"][".xlsx"], 1)
        self.assertFalse(result["archives_extracted"])


if __name__ == "__main__":
    unittest.main()
