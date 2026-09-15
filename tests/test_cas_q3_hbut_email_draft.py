"""Integrity tests for the deterministic sender-free HBUT email draft."""

from __future__ import annotations

from email import policy
from email.parser import BytesParser
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.build_cas_q3_hbut_email_draft import DRAFT_NAME, build
from scripts.build_cas_q3_hbut_review_request_packet import ARCHIVE_NAME, ROOT, build as build_packet
from scripts.validate_cas_q3_hbut_email_draft import validate_draft


COMMIT = "a" * 40


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HbutEmailDraftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.packet_result = build_packet(ROOT, self.root / "packet", COMMIT)
        self.packet = self.root / "packet" / ARCHIVE_NAME
        self.result = build(
            self.packet,
            self.packet_result["archive_sha256"],
            self.root / "draft-a",
            COMMIT,
        )
        self.draft = self.root / "draft-a" / DRAFT_NAME

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate(self, path: Path | None = None):
        target = path or self.draft
        return validate_draft(
            target,
            sha(target),
            self.packet_result["archive_sha256"],
            COMMIT,
        )

    def test_deterministic_build_and_roundtrip(self):
        second = build(
            self.packet,
            self.packet_result["archive_sha256"],
            self.root / "draft-b",
            COMMIT,
        )
        self.assertEqual(self.result["draft_sha256"], second["draft_sha256"])
        result = self.validate()
        self.assertEqual(result["decision"], "PASS_READY_TO_REVIEW_HBUT_EMAIL_DRAFT_NOT_SENT")
        self.assertFalse(result["email_sent"])
        self.assertFalse(result["submission_authorized"])

    def test_no_sender_or_transport_headers_and_exact_attachment(self):
        message = BytesParser(policy=policy.default).parsebytes(self.draft.read_bytes())
        headers = {name.lower() for name in message.keys()}
        self.assertFalse(headers & {"from", "sender", "date", "message-id", "cc", "bcc", "reply-to", "received"})
        attachments = list(message.iter_attachments())
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].get_filename(), ARCHIVE_NAME)
        self.assertEqual(hashlib.sha256(attachments[0].get_payload(decode=True)).hexdigest(), sha(self.packet))

    def test_wrong_packet_hash_is_rejected_before_output(self):
        output = self.root / "wrong"
        with self.assertRaisesRegex(ValueError, "packet SHA-256 mismatch"):
            build(self.packet, "b" * 64, output, COMMIT)
        self.assertFalse((output / DRAFT_NAME).exists())

    def test_existing_draft_is_never_overwritten(self):
        before = self.draft.read_bytes()
        with self.assertRaises(FileExistsError):
            build(
                self.packet,
                self.packet_result["archive_sha256"],
                self.root / "draft-a",
                COMMIT,
            )
        self.assertEqual(self.draft.read_bytes(), before)

    def test_tampered_email_is_rejected(self):
        tampered = self.root / "tampered.eml"
        tampered.write_bytes(self.draft.read_bytes().replace(b"NOT-SENT", b"SENT----", 1))
        with self.assertRaisesRegex(ValueError, "email header mismatch"):
            validate_draft(
                tampered,
                sha(tampered),
                self.packet_result["archive_sha256"],
                COMMIT,
            )

    def test_validator_direct_cli_entrypoint(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_cas_q3_hbut_email_draft.py"),
                "--draft",
                str(self.draft),
                "--draft-sha256",
                self.result["draft_sha256"],
                "--packet-sha256",
                self.packet_result["archive_sha256"],
                "--packet-acceptance-commit",
                COMMIT,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS_READY_TO_REVIEW_HBUT_EMAIL_DRAFT_NOT_SENT", result.stdout)


if __name__ == "__main__":
    unittest.main()
