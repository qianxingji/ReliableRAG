"""Integrity fixtures only: these tests do not fit or replay a scientific model."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import verify_roa_artifacts as checker


class ArtifactVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.namespace = self.root / "outputs/stage"
        self.namespace.mkdir(parents=True)
        self.payload = self.namespace / "fixture.txt"
        self.payload.write_bytes(b"synthetic integrity fixture\n")
        self.manifest_path = self.namespace / "SHA256_MANIFEST.json"
        self.manifest = {
            "status": "PASS", "hard_stop": True,
            "exact_recursive_coverage": True,
            "excludes_only": "SHA256_MANIFEST.json", "payload_file_count": 1,
            "files": [{"path": "outputs/stage/fixture.txt",
                       "sha256": checker.digest(self.payload),
                       "size_bytes": self.payload.stat().st_size}],
        }
        self.spec = {"schema_version": 1, "namespace": "outputs/stage",
                     "manifest_path": "outputs/stage/SHA256_MANIFEST.json",
                     "payload_file_count": 1,
                     "payload_size_bytes": self.payload.stat().st_size}
        self.seal_fixture()

    def seal_fixture(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.spec["manifest_sha256"] = checker.digest(self.manifest_path)

    def verify(self, manifest_path=None):
        return checker.verify(self.root, manifest_path or self.manifest_path, self.spec)

    def assert_failure(self, result, kind):
        self.assertEqual(result["integrity_status"], "FAIL")
        self.assertIn(kind, [issue["kind"] for issue in result["issues"]])
        self.assertEqual(result["numeric_replay_status"], "NOT_RUN")
        self.assertEqual(result["cas_q2_status"], "NOT READY")

    def test_pass_is_read_only_and_does_not_promote_scientific_status(self):
        before = {p: p.read_bytes() for p in self.namespace.iterdir()}
        result = self.verify()
        self.assertEqual(result["integrity_status"], "PASS")
        self.assertEqual(result["verified_files"], 1)
        self.assertEqual(result["scientific_fit_calls"], 0)
        self.assertEqual(result["retrieval_generation_calls"], 0)
        self.assertEqual(result["numeric_replay_status"], "NOT_RUN")
        self.assertEqual(result["controls_status"], "NOT_RUN")
        self.assertEqual(result["upstream_dependencies_status"], "NOT_CHECKED")
        self.assertEqual(result["cas_q2_status"], "NOT READY")
        self.assertEqual(before, {p: p.read_bytes() for p in self.namespace.iterdir()})

    def test_missing_or_same_size_changed_payload_fails(self):
        self.payload.write_bytes(b"X" * self.payload.stat().st_size)
        self.assert_failure(self.verify(), "PAYLOAD_ERROR")
        self.payload.unlink()
        self.assert_failure(self.verify(), "PAYLOAD_ERROR")

    def test_manifest_cannot_self_authorize_new_hashes(self):
        self.payload.write_bytes(b"changed")
        self.manifest["files"][0]["sha256"] = checker.digest(self.payload)
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.assert_failure(self.verify(), "MANIFEST_ERROR")

    def test_unlisted_file_including_case_alias_fails(self):
        extra = self.namespace / "unexpected.txt"
        extra.write_text("extra", encoding="utf-8")
        self.assert_failure(self.verify(), "UNLISTED_FILE")
        extra.unlink()
        alias = self.namespace / "FIXTURE.txt"
        if alias.exists():
            self.skipTest("case-insensitive filesystem cannot create a distinct case alias")
        alias.write_bytes(self.payload.read_bytes())
        self.assert_failure(self.verify(), "UNLISTED_FILE")

    def test_traversal_and_duplicate_manifest_entries_fail(self):
        for bad in ("../fixture.txt", "/etc/passwd", "outputs/stage/../fixture.txt",
                    "outputs\\stage\\fixture.txt", "outputs//stage/fixture.txt",
                    "outputs/elsewhere/fixture.txt"):
            with self.subTest(path=bad):
                self.manifest["files"][0]["path"] = bad
                self.seal_fixture()
                self.assert_failure(self.verify(), "MANIFEST_ERROR")
        self.manifest["files"][0]["path"] = "outputs/stage/fixture.txt"
        self.manifest["files"].append(dict(self.manifest["files"][0]))
        self.manifest["payload_file_count"] = self.spec["payload_file_count"] = 2
        self.spec["payload_size_bytes"] *= 2
        self.seal_fixture()
        self.assert_failure(self.verify(), "MANIFEST_ERROR")

    def test_unsealed_or_wrong_count_manifest_fails(self):
        for key, value in (("hard_stop", False), ("exact_recursive_coverage", False),
                           ("payload_file_count", 2), ("files", [])):
            old = self.manifest[key]
            with self.subTest(field=key):
                self.manifest[key] = value
                self.seal_fixture()
                self.assert_failure(self.verify(), "MANIFEST_ERROR")
            self.manifest[key] = old

    def test_symlink_payload_is_rejected(self):
        outside = self.root / "external.txt"
        self.payload.rename(outside)
        try:
            self.payload.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        self.assert_failure(self.verify(), "PAYLOAD_ERROR")

    def test_external_manifest_cannot_hide_changed_original(self):
        copy = self.root / "manifest-copy.json"
        copy.write_bytes(self.manifest_path.read_bytes())
        self.manifest_path.write_text("changed", encoding="utf-8")
        self.assert_failure(self.verify(copy), "ORIGINAL_MANIFEST_ERROR")

    def run_cli(self, *extra):
        spec_path = self.root / "test-spec.json"
        spec_path.write_text(json.dumps(self.spec), encoding="utf-8")
        out = io.StringIO()
        with patch.object(checker, "SPEC_PATH", spec_path), patch(
            "sys.argv", ["verify", "--project-root", str(self.root), *map(str, extra)]
        ), contextlib.redirect_stdout(out):
            status = checker.main()
        return status, json.loads(out.getvalue())

    def test_cli_writes_new_report_and_refuses_overwrite(self):
        report = self.root / "report.json"
        status, result = self.run_cli("--output", report)
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(report.read_text()), result)
        original = report.read_bytes()
        self.assertEqual(self.run_cli("--output", report)[0], 2)
        self.assertEqual(report.read_bytes(), original)

    def test_cli_refuses_report_inside_sealed_namespace(self):
        report = self.namespace / "new-report.json"
        self.assertEqual(self.run_cli("--output", report)[0], 2)
        self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
