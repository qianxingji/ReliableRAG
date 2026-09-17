#!/usr/bin/env python3
"""Validate the deterministic HBUT review-request packet without extracting it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

try:
    from scripts.build_cas_q3_hbut_review_request_packet import ARCHIVE_NAME
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from build_cas_q3_hbut_review_request_packet import ARCHIVE_NAME


EXPECTED_PAYLOAD = {
    "REQUEST_ZH.md",
    "MANUSCRIPT_DRAFT.pdf",
    "SUPPLEMENT_DRAFT.pdf",
    "LICENSE",
    "LICENSE_SCOPE.md",
    "THIRD_PARTY_NOTICES.md",
    "DATA_AND_CODE_AVAILABILITY.md",
    "PROJECT_LICENSE_DECISION_PACKET.md",
    "PACKET_BOUNDARY.md",
    "SOURCE_COMMIT.txt",
}
EXPECTED_ALL = EXPECTED_PAYLOAD | {"PACKET_MANIFEST.json"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and "\\" not in name and ":" not in name


def validate_archive(
    archive: Path,
    expected_archive_sha256: str,
    expected_manifest_sha256: str,
    expected_source_commit: str,
) -> dict[str, object]:
    if re.fullmatch(r"[0-9a-f]{40}", expected_source_commit) is None:
        raise ValueError("expected source commit must be lowercase 40-character Git SHA")
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("packet archive is missing or unsafe")
    archive_bytes = archive.read_bytes()
    if digest(archive_bytes) != expected_archive_sha256:
        raise ValueError("archive SHA-256 mismatch")

    checks = 2
    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)) or set(names) != EXPECTED_ALL:
            raise ValueError("archive must have exact unique allowlisted membership")
        checks += 2
        for info in infos:
            if not _safe(info.filename):
                raise ValueError(f"unsafe archive member: {info.filename}")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"symlink archive member: {info.filename}")
            checks += 2

        manifest_bytes = bundle.read("PACKET_MANIFEST.json")
        if digest(manifest_bytes) != expected_manifest_sha256:
            raise ValueError("manifest SHA-256 mismatch")
        manifest = json.loads(manifest_bytes)
        checks += 2
        expected_boundary = {
            "schema_version": 1,
            "decision": "DRAFT_HBUT_INSTITUTIONAL_REVIEW_REQUEST_PACKET_NOT_SENT",
            "cas_q3_status": "NOT_READY",
            "source_commit": expected_source_commit,
            "request_sent": False,
            "institutional_response_received": False,
            "institutional_cas_tier_verified": False,
            "manuscript_approved": False,
            "code_release_approved": False,
            "distribution_authorized": False,
            "submission_authorized": False,
            "contains_raw_benchmark_text_answers_or_per_question_results": False,
            "contains_model_weights_or_private_reproduction_archives": False,
            "contains_author_identity_or_corresponding_author_email": False,
            "final_author_artifact_rebind_required": True,
        }
        for key, expected in expected_boundary.items():
            if manifest.get(key) != expected:
                raise ValueError(f"manifest boundary mismatch: {key}")
            checks += 1
        if manifest.get("scope") != "institutional_policy_and_pre_submission_review_request":
            raise ValueError("manifest scope mismatch")
        checks += 1

        records = manifest.get("members")
        if not isinstance(records, list) or {item.get("path") for item in records} != EXPECTED_PAYLOAD:
            raise ValueError("manifest payload membership mismatch")
        checks += 2
        for record in records:
            name = record["path"]
            data = bundle.read(name)
            if record.get("size_bytes") != len(data) or record.get("sha256") != digest(data):
                raise ValueError(f"member integrity mismatch: {name}")
            if not isinstance(record.get("role"), str) or not record["role"]:
                raise ValueError(f"member role missing: {name}")
            if not isinstance(record.get("source"), str) or not record["source"]:
                raise ValueError(f"member source missing: {name}")
            checks += 4

        if bundle.read("SOURCE_COMMIT.txt") != (expected_source_commit + "\n").encode("ascii"):
            raise ValueError("source commit member mismatch")
        if not bundle.read("MANUSCRIPT_DRAFT.pdf").startswith(b"%PDF-"):
            raise ValueError("manuscript is not a PDF")
        if not bundle.read("SUPPLEMENT_DRAFT.pdf").startswith(b"%PDF-"):
            raise ValueError("supplement is not a PDF")
        request = bundle.read("REQUEST_ZH.md").decode("utf-8")
        boundary = bundle.read("PACKET_BOUNDARY.md").decode("utf-8")
        for marker in (
            "Applied Intelligence",
            "0924-669X",
            "1573-7497",
            "计算机科学",
            "Apache License 2.0",
            "Qwen2.5-3B-Instruct",
            "不得因此稿而关闭",
        ):
            if marker not in request:
                raise ValueError(f"request marker missing: {marker}")
            checks += 1
        for marker in ("CAS Q3 STATUS: NOT READY", "has not been sent", "final author-populated"):
            if marker not in boundary:
                raise ValueError(f"boundary marker missing: {marker}")
            checks += 1
        checks += 3

    return {
        "schema_version": 1,
        "decision": "PASS_HBUT_INSTITUTIONAL_REVIEW_REQUEST_PACKET_INTEGRITY_NOT_SENT",
        "archive": str(archive),
        "archive_sha256": expected_archive_sha256,
        "manifest_sha256": expected_manifest_sha256,
        "source_commit": expected_source_commit,
        "archive_members": len(EXPECTED_ALL),
        "checks": checks,
        "archive_extracted": False,
        "request_sent": False,
        "institutional_response_received": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            validate_archive(
                args.archive,
                args.archive_sha256,
                args.manifest_sha256,
                args.source_commit,
            ),
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
