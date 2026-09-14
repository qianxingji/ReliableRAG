"""Safety tests for the private Applied Intelligence transport packager."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.package_cas_q3_applied_intelligence_transport import deterministic_zip, safe_flat_member


class AppliedIntelligenceTransportTests(unittest.TestCase):
    def test_flat_member_policy(self):
        self.assertTrue(safe_flat_member("manuscript.tex"))
        for name in ("../x", "a/b", r"a\b", "/x", "", ".", ".."):
            self.assertFalse(safe_flat_member(name), name)

    def test_deterministic_zip_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            root = Path(tmp_name)
            members = {"b.txt": b"two\n", "a.txt": b"one\n"}
            deterministic_zip(root / "a.zip", members)
            deterministic_zip(root / "b.zip", members)
            self.assertEqual((root / "a.zip").read_bytes(), (root / "b.zip").read_bytes())
            with zipfile.ZipFile(root / "a.zip") as bundle:
                self.assertEqual(bundle.namelist(), ["a.txt", "b.txt"])

    def test_packager_rejects_nested_member(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            with self.assertRaisesRegex(AssertionError, "unsafe or nested"):
                deterministic_zip(Path(tmp_name) / "bad.zip", {"nested/file": b"x"})


if __name__ == "__main__":
    unittest.main()
