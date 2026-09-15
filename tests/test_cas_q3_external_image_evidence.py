from pathlib import Path
import io
import tempfile
import unittest
import zipfile

from scripts.audit_cas_q3_external_image_evidence import (
    _is_within_declared_roots,
    audit,
)


PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic"
JPEG = b"\xff\xd8\xff\xe0" + b"synthetic"


class ExternalImageEvidenceTests(unittest.TestCase):
    def test_declared_root_boundary_helper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            inside = root / "inside.png"
            outside = root.parent / "outside.png"

            self.assertTrue(_is_within_declared_roots(inside, [root]))
            self.assertFalse(_is_within_declared_roots(outside, [root]))

    def test_valid_images_are_deduplicated_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "figure.png").write_bytes(PNG)
            (root / "copy.png").write_bytes(PNG)
            (root / "photo.jpeg").write_bytes(JPEG)

            result = audit([root])

            self.assertEqual(
                result["decision"],
                "PASS_BOUNDED_COMMON_RASTER_IMAGE_INVENTORY_NO_EXTENSION_MISMATCH",
            )
            self.assertEqual(result["image_occurrences"], 3)
            self.assertEqual(result["unique_image_hashes"], 2)
            self.assertEqual(result["strict_image_magic_counts"], {"png": 2, "jpeg": 1})
            self.assertEqual(result["image_magic_suffix_mismatch_count"], 0)

    def test_direct_and_nested_zip_images_are_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested_bytes = io.BytesIO()
            with zipfile.ZipFile(nested_bytes, "w") as nested:
                nested.writestr("inside/photo.jpg", JPEG)
            with zipfile.ZipFile(root / "archive.zip", "w") as archive:
                archive.writestr("figure.png", PNG)
                archive.writestr("nested.zip", nested_bytes.getvalue())

            result = audit([root])

            self.assertEqual(
                result["decision"],
                "PASS_BOUNDED_COMMON_RASTER_IMAGE_INVENTORY_NO_EXTENSION_MISMATCH",
            )
            self.assertEqual(result["zip_archives_scanned"], 1)
            self.assertEqual(result["nested_zip_archives_scanned"], 1)
            self.assertEqual(result["direct_zip_image_members"], 1)
            self.assertEqual(result["nested_zip_image_members"], 1)
            self.assertEqual(result["unique_image_hashes"], 2)

    def test_image_magic_with_wrong_suffix_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "hidden.bin").write_bytes(PNG)

            result = audit([root])

            self.assertEqual(result["image_occurrences"], 1)
            self.assertEqual(result["image_magic_suffix_mismatch_count"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_image_suffix_without_image_magic_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fake.png").write_text("not an image", encoding="utf-8")

            result = audit([root])

            self.assertEqual(result["extension_labeled_image_files"], 1)
            self.assertEqual(result["image_occurrences"], 0)
            self.assertEqual(result["image_magic_suffix_mismatch_count"], 1)
            self.assertTrue(result["decision"].startswith("REVIEW_"))

    def test_exclusion_case_matches_the_prior_census_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lower" / "tmp").mkdir(parents=True)
            (root / "lower" / "tmp" / "excluded.png").write_bytes(PNG)
            (root / "upper" / "TMP").mkdir(parents=True)
            (root / "upper" / "TMP" / "included.png").write_bytes(PNG)

            result = audit([root])

            self.assertEqual(result["ordinary_files_seen"], 1)
            self.assertEqual(result["ordinary_image_occurrences"], 1)


if __name__ == "__main__":
    unittest.main()
