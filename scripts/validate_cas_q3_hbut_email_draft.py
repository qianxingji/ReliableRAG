#!/usr/bin/env python3
"""Validate a sender-free HBUT email draft without sending or extracting it."""

from __future__ import annotations

import argparse
from email import policy
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re

try:
    from scripts.build_cas_q3_hbut_email_draft import (
        ATTACHMENT_NAME,
        BOUNDARY,
        RECIPIENT,
        SUBJECT,
        body_text,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from build_cas_q3_hbut_email_draft import (
        ATTACHMENT_NAME,
        BOUNDARY,
        RECIPIENT,
        SUBJECT,
        body_text,
    )


FORBIDDEN_HEADERS = {"from", "sender", "date", "message-id", "cc", "bcc", "reply-to", "received"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact_hex(value: str, length: int, label: str) -> str:
    if re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None:
        raise ValueError(f"{label} must be lowercase hexadecimal with length {length}")
    return value


def validate_draft(
    draft: Path,
    expected_draft_sha256: str,
    expected_packet_sha256: str,
    expected_packet_acceptance_commit: str,
) -> dict[str, object]:
    expected_draft_sha256 = _exact_hex(expected_draft_sha256, 64, "expected draft SHA-256")
    expected_packet_sha256 = _exact_hex(expected_packet_sha256, 64, "expected packet SHA-256")
    expected_packet_acceptance_commit = _exact_hex(
        expected_packet_acceptance_commit, 40, "expected packet acceptance commit"
    )
    if not draft.is_file() or draft.is_symlink():
        raise ValueError("email draft is missing or unsafe")
    draft_bytes = draft.read_bytes()
    if digest(draft_bytes) != expected_draft_sha256:
        raise ValueError("email draft SHA-256 mismatch")

    message = BytesParser(policy=policy.default).parsebytes(draft_bytes)
    checks = 2
    expected_headers = {
        "To": RECIPIENT,
        "Subject": SUBJECT,
        "X-ReliableRAG-Draft-Status": "NOT-SENT",
        "X-ReliableRAG-Packet-Commit": expected_packet_acceptance_commit,
        "X-ReliableRAG-Attachment-SHA256-1": expected_packet_sha256[:32],
        "X-ReliableRAG-Attachment-SHA256-2": expected_packet_sha256[32:],
    }
    for name, expected in expected_headers.items():
        if message.get(name) != expected or len(message.get_all(name, [])) != 1:
            raise ValueError(f"email header mismatch: {name}")
        checks += 2
    present = {name.lower() for name in message.keys()}
    forbidden_present = sorted(present & FORBIDDEN_HEADERS)
    if forbidden_present:
        raise ValueError("sender or transport header present: " + ", ".join(forbidden_present))
    checks += len(FORBIDDEN_HEADERS)
    if not message.is_multipart() or message.get_content_subtype() != "mixed" or message.get_boundary() != BOUNDARY:
        raise ValueError("email multipart boundary mismatch")
    checks += 3

    leaves = [part for part in message.walk() if not part.is_multipart()]
    bodies = [part for part in leaves if part.get_content_disposition() != "attachment"]
    attachments = [part for part in leaves if part.get_content_disposition() == "attachment"]
    if len(bodies) != 1 or len(attachments) != 1:
        raise ValueError("email must contain exactly one plain body and one attachment")
    checks += 2
    body = bodies[0]
    if body.get_content_type() != "text/plain" or body.get_content_charset() != "utf-8":
        raise ValueError("email body type mismatch")
    actual_body = body.get_content()
    expected_body = body_text(expected_packet_sha256, expected_packet_acceptance_commit)
    if actual_body.replace("\r\n", "\n") != expected_body.replace("\r\n", "\n"):
        raise ValueError("email body content mismatch")
    checks += 3
    for marker in (
        "Applied Intelligence",
        "0924-669X",
        "1573-7497",
        "计算机科学大类三区及以上",
        "Apache License 2.0",
        "Qwen2.5-3B-Instruct",
        expected_packet_sha256,
        "不代表学校已确认分区",
        "补充姓名、学院、联系方式",
    ):
        if marker not in actual_body:
            raise ValueError(f"email body marker missing: {marker}")
        checks += 1

    attachment = attachments[0]
    if attachment.get_filename() != ATTACHMENT_NAME or attachment.get_content_type() != "application/zip":
        raise ValueError("email attachment metadata mismatch")
    attachment_bytes = attachment.get_payload(decode=True)
    if not isinstance(attachment_bytes, bytes) or digest(attachment_bytes) != expected_packet_sha256:
        raise ValueError("email attachment SHA-256 mismatch")
    checks += 4

    return {
        "schema_version": 1,
        "decision": "PASS_READY_TO_REVIEW_HBUT_EMAIL_DRAFT_NOT_SENT",
        "draft": str(draft),
        "draft_sha256": expected_draft_sha256,
        "packet_sha256": expected_packet_sha256,
        "packet_acceptance_commit": expected_packet_acceptance_commit,
        "recipient": RECIPIENT,
        "subject": SUBJECT,
        "checks": checks,
        "sender_identity_present": False,
        "transport_headers_present": False,
        "attachment_extracted": False,
        "email_sent": False,
        "institutional_response_received": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--draft-sha256", required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--packet-acceptance-commit", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            validate_draft(
                args.draft,
                args.draft_sha256,
                args.packet_sha256,
                args.packet_acceptance_commit,
            ),
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
