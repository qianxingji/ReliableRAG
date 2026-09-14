import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_recursive_archive_closure_evidence import _strict_magic, audit


def nested_zip_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()


class RecursiveArchiveClosureEvidenceTests(unittest.TestCase):
    def test_first_level_nested_text_is_scanned_without_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / "outer.zip", "w") as archive:
                archive.writestr("inner.zip", nested_zip_bytes({"notes.txt": b"ordinary notes"}))

            result = audit([root])

            self.assertEqual(result["decision"], "PASS_BOUNDED_FIRST_LEVEL_NESTED_ARCHIVE_CENSUS_NO_RECOVERY")
            self.assertEqual(result["nested_archives_seen"], 1)
            self.assertEqual(result["text_members_scanned"], 1)
            self.assertEqual(result["candidate_match_count"], 0)
            self.assertTrue(result["temporary_files_removed"])

    def test_nested_text_marker_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / "outer.zip", "w") as archive:
                archive.writestr(
                    "inner.zip",
                    nested_zip_bytes({"approval.txt": b"institutional manuscript approval"}),
                )

            result = audit([root])

            self.assertEqual(result["candidate_match_count"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_deeper_archive_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            level_two = nested_zip_bytes({"plain.txt": b"ordinary"})
            level_one = nested_zip_bytes({"deeper.zip": level_two})
            with zipfile.ZipFile(root / "outer.zip", "w") as archive:
                archive.writestr("inner.zip", level_one)

            result = audit([root])

            self.assertEqual(result["deeper_archives_seen"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_oversized_nested_archive_is_not_claimed_covered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = nested_zip_bytes({"plain.txt": b"ordinary"})
            with zipfile.ZipFile(root / "outer.zip", "w") as archive:
                archive.writestr("inner.zip", payload)

            result = audit([root], max_nested_archive_bytes=len(payload) - 1)

            self.assertEqual(result["nested_archives_skipped"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_disguised_pdf_member_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inner = nested_zip_bytes({"document.bin": b"%PDF-1.7\nsynthetic"})
            with zipfile.ZipFile(root / "outer.zip", "w") as archive:
                archive.writestr("inner.zip", inner)

            result = audit([root])

            self.assertEqual(result["strict_magic_suffix_mismatch_count"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_pdf_marker_inside_source_text_is_not_a_pdf_header(self) -> None:
        self.assertIsNone(_strict_magic(b"const header = '%PDF-1.7';"))


if __name__ == "__main__":
    unittest.main()
