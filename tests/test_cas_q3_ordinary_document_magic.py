from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_ordinary_document_magic import audit


class OrdinaryDocumentMagicTests(unittest.TestCase):
    def test_strict_headers_pass_and_source_literal_is_not_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.pdf").write_bytes(b"%PDF-1.7\nsynthetic")
            (root / "source.js").write_bytes(b"const value = '%PDF-1.7';")
            with zipfile.ZipFile(root / "archive.zip", "w") as archive:
                archive.writestr("notes.txt", "ordinary")

            result = audit([root])

            self.assertEqual(result["decision"], "PASS_BOUNDED_ORDINARY_DOCUMENT_MAGIC_MATCHES_EXTENSIONS")
            self.assertEqual(result["strict_magic_counts"], {"pdf": 1, "zip": 1})
            self.assertEqual(result["loose_pdf_marker_non_header_count"], 1)
            self.assertEqual(result["document_magic_suffix_mismatch_count"], 0)

    def test_disguised_pdf_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.bin").write_bytes(b"%PDF-1.7\nsynthetic")

            result = audit([root])

            self.assertEqual(result["document_magic_suffix_mismatch_count"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_ooxml_word_stored_as_zip_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / "document.zip", "w") as archive:
                archive.writestr("[Content_Types].xml", "<Types/>")
                archive.writestr("word/document.xml", "<document/>")

            result = audit([root])

            self.assertEqual(result["zip_document_family_counts"]["ooxml_word"], 1)
            self.assertEqual(result["document_magic_suffix_mismatch_count"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_ole_container_with_unknown_suffix_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "legacy.bin").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 64)

            result = audit([root])

            self.assertEqual(result["strict_magic_counts"], {"ole_compound": 1})
            self.assertEqual(result["document_magic_suffix_mismatch_count"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))


if __name__ == "__main__":
    unittest.main()
