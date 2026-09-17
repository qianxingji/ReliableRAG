"""Test local transfer integrity and preservation with synthetic byte fixtures."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts import package_roa_review_bundle as bundler
from scripts.verify_roa_artifacts import digest, verify


class ReviewBundleTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.namespace = self.root / "outputs/stage"
        self.namespace.mkdir(parents=True)
        self.payload = self.namespace / "fixture.txt"
        self.payload.write_bytes(b"synthetic integrity fixture\n")
        self.manifest = self.namespace / "SHA256_MANIFEST.json"
        self.manifest.write_text(json.dumps({
            "status": "PASS", "hard_stop": True, "exact_recursive_coverage": True,
            "excludes_only": "SHA256_MANIFEST.json", "payload_file_count": 1,
            "files": [{"path": "outputs/stage/fixture.txt", "sha256": digest(self.payload),
                       "size_bytes": self.payload.stat().st_size}]}))
        self.spec = {"schema_version": 1, "namespace": "outputs/stage",
                     "manifest_path": "outputs/stage/SHA256_MANIFEST.json",
                     "manifest_sha256": digest(self.manifest), "payload_file_count": 1,
                     "payload_size_bytes": self.payload.stat().st_size}
        self.output = self.root / "review.zip"

    def test_bundle_round_trip_preserves_all_bytes_and_status_boundaries(self):
        before = {p.name: p.read_bytes() for p in self.namespace.iterdir()}
        result = bundler.package(self.root, self.output, self.spec)
        self.assertEqual(result["bundle_status"], "PASS")
        self.assertEqual(result["numeric_replay_status"], "NOT_RUN")
        self.assertEqual(result["cas_q2_status"], "NOT READY")
        self.assertFalse(result["uploaded"])
        self.assertEqual(result["bundle_sha256"], digest(self.output))
        unpacked = self.root / "unpacked"
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(len(archive.namelist()), 2)
            archive.extractall(unpacked)  # Trusted synthetic archive, known names.
        check = verify(unpacked, unpacked / self.spec["manifest_path"], self.spec)
        self.assertEqual(check["integrity_status"], "PASS")
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.namespace.iterdir()})

    def test_missing_or_changed_source_does_not_create_archive(self):
        self.payload.unlink()
        with self.assertRaises(ValueError):
            bundler.package(self.root, self.output, self.spec)
        self.assertFalse(self.output.exists())

    def test_existing_destination_is_preserved(self):
        self.output.write_bytes(b"existing file")
        with self.assertRaises(ValueError):
            bundler.package(self.root, self.output, self.spec)
        self.assertEqual(self.output.read_bytes(), b"existing file")

    def test_output_inside_original_namespace_is_rejected(self):
        output = self.namespace / "review.zip"
        with self.assertRaises(ValueError):
            bundler.package(self.root, output, self.spec)
        self.assertFalse(output.exists())

    def test_source_changed_after_initial_check_removes_partial_archive(self):
        def verify_then_change(*args):
            result = verify(*args)
            self.payload.write_bytes(b"changed after verification")
            return result

        with patch.object(bundler, "verify", verify_then_change):
            with self.assertRaisesRegex(ValueError, "changed during packaging"):
                bundler.package(self.root, self.output, self.spec)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
