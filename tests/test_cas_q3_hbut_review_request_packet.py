"""Integrity tests for the HBUT institutional review request packet."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from scripts.build_cas_q3_hbut_review_request_packet import ARCHIVE_NAME, ROOT, build
from scripts.validate_cas_q3_hbut_review_request_packet import validate_archive


COMMIT = "a" * 40


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HbutReviewRequestPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.result = build(ROOT, self.root / "a", COMMIT)
        self.archive = self.root / "a" / ARCHIVE_NAME

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate(self, path: Path | None = None):
        target = path or self.archive
        return validate_archive(target, sha(target), self.result["manifest_sha256"], COMMIT)

    def rewrite(self, name: str, transform) -> Path:
        target = self.root / name
        with zipfile.ZipFile(self.archive) as source, zipfile.ZipFile(target, "w") as output:
            for info in source.infolist():
                data = source.read(info.filename)
                for new_info, new_data in transform(info, data):
                    output.writestr(new_info, new_data)
        return target

    def test_deterministic_build_and_roundtrip(self):
        second = build(ROOT, self.root / "b", COMMIT)
        self.assertEqual(self.result["archive_sha256"], second["archive_sha256"])
        result = self.validate()
        self.assertEqual(result["decision"], "PASS_HBUT_INSTITUTIONAL_REVIEW_REQUEST_PACKET_INTEGRITY_NOT_SENT")
        self.assertFalse(result["request_sent"])
        self.assertFalse(result["submission_authorized"])

    def test_packet_contains_only_fixed_review_materials(self):
        with zipfile.ZipFile(self.archive) as bundle:
            names = set(bundle.namelist())
            self.assertIn("REQUEST_ZH.md", names)
            self.assertIn("MANUSCRIPT_DRAFT.pdf", names)
            self.assertIn("PACKET_BOUNDARY.md", names)
            self.assertNotIn("OWNER_INPUTS.local.json", names)
            self.assertNotIn("INSTITUTIONAL_CAS_RECORD.local.json", names)

    def test_changed_member_is_rejected(self):
        changed = self.rewrite(
            "changed.zip",
            lambda info, data: [(info, data + b"changed")]
            if info.filename == "LICENSE_SCOPE.md"
            else [(info, data)],
        )
        with self.assertRaisesRegex(ValueError, "member integrity mismatch"):
            self.validate(changed)

    def test_extra_member_is_rejected(self):
        def transform(info, data):
            rows = [(info, data)]
            if info.filename == "PACKET_MANIFEST.json":
                rows.append((zipfile.ZipInfo("extra.txt"), b"extra"))
            return rows

        extra = self.rewrite("extra.zip", transform)
        with self.assertRaisesRegex(ValueError, "exact unique allowlisted membership"):
            self.validate(extra)

    def test_traversal_member_is_rejected(self):
        def transform(info, data):
            rows = [(info, data)]
            if info.filename == "PACKET_MANIFEST.json":
                rows.append((zipfile.ZipInfo("../escape.txt"), b"escape"))
            return rows

        traversal = self.rewrite("traversal.zip", transform)
        with self.assertRaisesRegex(ValueError, "exact unique allowlisted membership|unsafe archive member"):
            self.validate(traversal)

    def test_wrong_source_commit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source_commit|source commit|boundary mismatch"):
            validate_archive(
                self.archive,
                self.result["archive_sha256"],
                self.result["manifest_sha256"],
                "b" * 40,
            )

    def test_existing_packet_is_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            build(ROOT, self.root / "a", COMMIT)

    def test_validator_direct_cli_entrypoint(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_cas_q3_hbut_review_request_packet.py"),
                "--archive",
                str(self.archive),
                "--archive-sha256",
                self.result["archive_sha256"],
                "--manifest-sha256",
                self.result["manifest_sha256"],
                "--source-commit",
                COMMIT,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS_HBUT_INSTITUTIONAL_REVIEW_REQUEST_PACKET_INTEGRITY_NOT_SENT", result.stdout)


if __name__ == "__main__":
    unittest.main()
