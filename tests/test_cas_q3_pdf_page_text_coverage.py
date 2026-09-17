from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_pdf_page_text_coverage import audit


PDF = b"%PDF-1.7\nsynthetic unique bytes"


def accepted_inspector(_: Path) -> dict:
    return {
        "pages": 2,
        "nonwhitespace_text_bytes_by_page": [40, 50],
        "raster_image_pages": [2],
    }


class PdfPageTextCoverageTests(unittest.TestCase):
    def test_direct_and_zip_occurrences_are_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ordinary.pdf").write_bytes(PDF)
            with zipfile.ZipFile(root / "outer.zip", "w") as archive:
                archive.writestr("copy.pdf", PDF)

            result = audit([root], inspector=accepted_inspector)

            self.assertEqual(result["decision"], "PASS_BOUNDED_UNIQUE_PDF_PAGE_TEXT_COVERAGE_NO_LOW_TEXT_PAGES")
            self.assertEqual(result["total_pdf_occurrences"], 2)
            self.assertEqual(result["unique_pdf_hashes"], 1)
            self.assertEqual(result["total_unique_pdf_pages"], 2)
            self.assertEqual(result["pages_with_raster_images"], 1)

    def test_first_level_nested_pdf_is_included_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inner_path = root / "inner.zip"
            with zipfile.ZipFile(inner_path, "w") as inner:
                inner.writestr("copy.pdf", PDF)
            inner_bytes = inner_path.read_bytes()
            inner_path.unlink()
            with zipfile.ZipFile(root / "outer.zip", "w") as outer:
                outer.writestr("inner.zip", inner_bytes)

            result = audit([root], inspector=accepted_inspector)

            self.assertEqual(result["nested_archives_seen"], 1)
            self.assertEqual(result["nested_zip_pdf_occurrences"], 1)
            self.assertEqual(result["unique_pdf_hashes"], 1)

    def test_low_text_page_fails_closed(self) -> None:
        def low_text(_: Path) -> dict:
            return {"pages": 2, "nonwhitespace_text_bytes_by_page": [40, 0], "raster_image_pages": [2]}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ordinary.pdf").write_bytes(PDF)

            result = audit([root], inspector=low_text)

            self.assertEqual(result["zero_text_page_count"], 1)
            self.assertTrue(result["bounded_interpretation"]["wholly_textless_raster_pages_detected"])
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_oversized_pdf_is_not_claimed_covered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ordinary.pdf").write_bytes(PDF)

            result = audit([root], max_pdf_bytes=len(PDF) - 1, inspector=accepted_inspector)

            self.assertEqual(result["skipped_pdf_occurrences"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))


if __name__ == "__main__":
    unittest.main()
