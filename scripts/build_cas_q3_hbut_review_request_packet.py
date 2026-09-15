#!/usr/bin/env python3
"""Build a deterministic, non-public HBUT institutional review request packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "hbut_institutional_review_request_candidate.zip"


@dataclass(frozen=True)
class Member:
    source: str
    destination: str
    role: str


MEMBERS = (
    Member(
        "docs/cas_q3/P0_GH_HBUT_INSTITUTIONAL_VERIFICATION_REQUEST_ZH.md",
        "REQUEST_ZH.md",
        "institutional_questions_and_retention_requirements",
    ),
    Member("output/pdf/manuscript.pdf", "MANUSCRIPT_DRAFT.pdf", "anonymous_manuscript_draft"),
    Member("output/pdf/supplement.pdf", "SUPPLEMENT_DRAFT.pdf", "anonymous_supplement_draft"),
    Member("LICENSE", "LICENSE", "proposed_project_code_license_text"),
    Member("LICENSE_SCOPE.md", "LICENSE_SCOPE.md", "project_code_license_scope"),
    Member(
        "release/cas_q3_aggregate_v2/THIRD_PARTY_NOTICES.md",
        "THIRD_PARTY_NOTICES.md",
        "third_party_terms_review_input",
    ),
    Member(
        "release/cas_q3_aggregate_v2/DATA_AND_CODE_AVAILABILITY.md",
        "DATA_AND_CODE_AVAILABILITY.md",
        "proposed_availability_boundary",
    ),
    Member(
        "docs/cas_q3/P0_G_PROJECT_LICENSE_DECISION_PACKET.md",
        "PROJECT_LICENSE_DECISION_PACKET.md",
        "release_questions_and_current_open_gates",
    ),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def safe_name(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value or not value:
        raise ValueError(f"unsafe archive member: {value!r}")
    return path.as_posix()


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def _source_commit(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError("source commit must be a lowercase 40-character Git SHA")
    return value


def build(project_root: Path, output_dir: Path, source_commit: str) -> dict[str, object]:
    project_root = project_root.resolve()
    output_dir = output_dir.resolve()
    source_commit = _source_commit(source_commit)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / ARCHIVE_NAME
    if archive.exists():
        raise FileExistsError(f"refusing to overwrite existing packet: {archive}")

    prepared: list[tuple[str, bytes, str, str]] = []
    destinations: set[str] = set()
    for member in MEMBERS:
        source = (project_root / member.source).resolve()
        if not source.is_relative_to(project_root):
            raise ValueError(f"source escapes project root: {member.source}")
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"missing or unsafe source: {member.source}")
        destination = safe_name(member.destination)
        if destination in destinations:
            raise ValueError(f"duplicate destination: {destination}")
        data = source.read_bytes()
        prepared.append((destination, data, member.role, member.source))
        destinations.add(destination)

    boundary = (
        "# HBUT institutional review request packet boundary\n\n"
        "**CAS Q3 STATUS: NOT READY.**\n\n"
        "This is a draft request package assembled for institutional review. It has not been sent, "
        "does not contain an institutional response, and does not prove journal tier, manuscript approval, "
        "copyright ownership, code-release approval, distribution authorization or Submission Ready status.\n\n"
        f"The included tracked inputs are bound to Git commit `{source_commit}`. The manuscript and supplement "
        "are anonymous draft artifacts; any later approval must be rebound to the exact final author-populated "
        "submission artifact and its SHA-256.\n"
    ).encode("utf-8")
    commit_record = (source_commit + "\n").encode("ascii")
    prepared.extend(
        [
            ("PACKET_BOUNDARY.md", boundary, "fail_closed_scope_and_rebind_notice", "GENERATED"),
            ("SOURCE_COMMIT.txt", commit_record, "tracked_input_revision", "GENERATED"),
        ]
    )

    records = [
        {
            "path": destination,
            "size_bytes": len(data),
            "sha256": digest(data),
            "role": role,
            "source": source,
        }
        for destination, data, role, source in sorted(prepared)
    ]
    manifest = {
        "schema_version": 1,
        "decision": "DRAFT_HBUT_INSTITUTIONAL_REVIEW_REQUEST_PACKET_NOT_SENT",
        "cas_q3_status": "NOT_READY",
        "source_commit": source_commit,
        "scope": "institutional_policy_and_pre_submission_review_request",
        "members": records,
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
    manifest_bytes = canonical_json(manifest)

    with tempfile.NamedTemporaryFile(
        dir=output_dir, prefix=ARCHIVE_NAME + ".", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for destination, data, _, _ in sorted(prepared):
                bundle.writestr(zip_info(destination), data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            bundle.writestr(zip_info("PACKET_MANIFEST.json"), manifest_bytes, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        temporary.replace(archive)
    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "schema_version": 1,
        "decision": "BUILT_DETERMINISTIC_HBUT_INSTITUTIONAL_REVIEW_REQUEST_CANDIDATE_NOT_SENT",
        "archive": str(archive),
        "archive_sha256": digest(archive.read_bytes()),
        "manifest_sha256": digest(manifest_bytes),
        "source_commit": source_commit,
        "payload_members": len(records),
        "archive_members": len(records) + 1,
        "private_values_emitted": False,
        "request_sent": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.project_root, args.output_dir, args.source_commit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
