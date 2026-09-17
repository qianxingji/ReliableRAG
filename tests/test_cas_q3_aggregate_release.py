"""Integrity tests for the anonymous aggregate release candidate."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.package_cas_q3_aggregate_release import ARCHIVE_NAME, ROOT, build, scan_text as build_scan_text
from scripts.validate_cas_q3_aggregate_release import validate_archive, scan_text as validate_scan_text


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AggregateReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.built = build(ROOT, self.root)
        self.archive = self.root / ARCHIVE_NAME

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate(self, archive: Path, manifest_sha256: str | None = None):
        return validate_archive(
            archive,
            sha256(archive),
            manifest_sha256 or self.built["manifest_sha256"],
        )

    def rewrite(self, name: str, transform) -> Path:
        target = self.root / name
        with zipfile.ZipFile(self.archive) as source, zipfile.ZipFile(target, "w") as output:
            for info in source.infolist():
                data = source.read(info.filename)
                for new_info, new_data in transform(info, data):
                    output.writestr(new_info, new_data)
        return target

    def test_valid_candidate_is_deterministic_and_roundtrips(self):
        other = self.root / "other"
        rebuilt = build(ROOT, other)
        self.assertEqual(self.built["archive_sha256"], rebuilt["archive_sha256"])
        result = self.validate(self.archive)
        self.assertEqual(result["status"], "PASS_CAS_Q3_ANONYMOUS_AGGREGATE_RELEASE_ROUNDTRIP")
        self.assertFalse(result["distribution_authorized"])

    def test_changed_member_is_rejected(self):
        def transform(info, data):
            if info.filename == "README.md":
                data += b"changed\n"
            return [(info, data)]
        changed = self.rewrite("changed.zip", transform)
        with self.assertRaisesRegex(ValueError, "size README.md"):
            self.validate(changed)

    def test_extra_undeclared_member_is_rejected(self):
        def transform(info, data):
            rows = [(info, data)]
            if info.filename == "MANIFEST.json":
                extra = zipfile.ZipInfo("extra.txt", date_time=(1980, 1, 1, 0, 0, 0))
                extra.external_attr = 0o100644 << 16
                rows.append((extra, b"extra"))
            return rows
        extra = self.rewrite("extra.zip", transform)
        with self.assertRaisesRegex(ValueError, "exact declared membership"):
            self.validate(extra)

    def test_traversal_member_is_rejected_before_extraction(self):
        def transform(info, data):
            rows = [(info, data)]
            if info.filename == "MANIFEST.json":
                traversal = zipfile.ZipInfo("../escape.txt", date_time=(1980, 1, 1, 0, 0, 0))
                traversal.external_attr = 0o100644 << 16
                rows.append((traversal, b"escape"))
            return rows
        traversal = self.rewrite("traversal.zip", transform)
        with self.assertRaisesRegex(ValueError, "unsafe archive member"):
            self.validate(traversal)

    def test_symlink_member_is_rejected(self):
        def transform(info, data):
            if info.filename == "README.md":
                info.external_attr = 0o120777 << 16
            return [(info, data)]
        symlink = self.rewrite("symlink.zip", transform)
        with self.assertRaisesRegex(ValueError, "no symlink entries"):
            self.validate(symlink)

    def test_identity_scanners_allow_urls_but_reject_local_identity_paths(self):
        for scanner in (build_scan_text, validate_scan_text):
            scanner(b"https://example.org/project/LICENSE", "url")
            for value in (b"E:/private/file", b"C:\\Users\\person\\file", b"/home/person/file", b"owner=qianx"):
                with self.subTest(scanner=scanner.__module__, value=value), self.assertRaises(ValueError):
                    scanner(value, "forbidden")


if __name__ == "__main__":
    unittest.main()
