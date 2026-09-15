#!/usr/bin/env python3
"""Validate a private P0-G release-activation record without authorizing release.

The strongest result is structural.  URL resolution, authorization content,
the final artifact rebind and the required Astra audit remain separate human
gates.  The verifier never publishes, uploads or fetches external URLs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "cas_q3" / "RELEASE_ACTIVATION_RECORD_TEMPLATE.json"
LOCAL_INPUT = ROOT / "docs" / "cas_q3" / "RELEASE_ACTIVATION_RECORD.local.json"
PRIVATE_ARCHIVE_ROOT = ROOT / "evidence" / "private" / "release_activation"
REPOSITORY_URL = "https://github.com/qianxingji/ReliableRAG"
AGGREGATE_V2_SHA256 = "4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8"
AUTHORIZATION_DECISION = "PASS_CLIENT_AUDITED_RELEASE_RECORD_AND_OWNER_ARCHIVE_AUTHORIZATION"
ARCHIVE_KINDS = {"CAS_Q3_AGGREGATE_V2", "AUTHORIZED_SUCCESSOR"}
IDENTIFIER_KINDS = {"DOI", "OTHER_PERSISTENT_IDENTIFIER"}
RELEASE_REFERENCE_KINDS = {"GITHUB_RELEASE", "IMMUTABLE_COMMIT_ONLY"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: must be an object")
        return {}
    return value


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _safe_archive_path(value: Any) -> Path | None:
    if not _nonempty(value):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return None
    resolved = (ROOT / candidate).resolve()
    if not resolved.is_relative_to(PRIVATE_ARCHIVE_ROOT.resolve()):
        return None
    return resolved


def _valid_digest(value: Any) -> bool:
    return _nonempty(value) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _valid_date(value: Any) -> bool:
    return _nonempty(value) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None


def validate(
    data: Any,
    *,
    check_template: bool = False,
    archive_path_override: Path | None = None,
) -> dict[str, Any]:
    missing: list[str] = []
    errors: list[str] = []
    root = _object(data, "$", errors)
    if root.get("schema_version") != 1:
        errors.append("schema_version: must equal 1")

    if check_template:
        expected = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        if root != expected:
            errors.append("template: differs from the canonical placeholder structure")
        return {
            "schema_version": 1,
            "decision": (
                "PASS_RELEASE_ACTIVATION_RECORD_TEMPLATE_AND_FAIL_CLOSED_BOUNDARY"
                if not errors
                else "FAIL_RELEASE_ACTIVATION_RECORD_TEMPLATE"
            ),
            "complete": False,
            "template_mode": True,
            "missing_field_paths": [],
            "validation_error_paths": sorted(set(errors)),
            "private_values_emitted": False,
            "archive_bytes_read": 0,
            "external_urls_fetched": False,
            "distribution_authorized_by_verifier": False,
            "submission_authorized": False,
            "p0_g_closed": False,
            "cas_q3_status": "NOT_READY",
        }

    authorization = _object(root.get("release_authorization"), "release_authorization", errors)
    revision = _object(root.get("repository_revision"), "repository_revision", errors)
    archive = _object(root.get("archive"), "archive", errors)
    persistent = _object(root.get("persistent_record"), "persistent_record", errors)
    restricted = _object(root.get("restricted_review_access"), "restricted_review_access", errors)
    review = _object(root.get("manual_review"), "manual_review", errors)

    auth_sha = authorization.get("institutional_release_record_sha256")
    if not _valid_digest(auth_sha):
        missing.append("release_authorization.institutional_release_record_sha256")
    if authorization.get("institutional_release_record_decision") != AUTHORIZATION_DECISION:
        missing.append(
            "release_authorization.institutional_release_record_decision=" + AUTHORIZATION_DECISION
        )
    if authorization.get("owner_distribution_authorized") is not True:
        missing.append("release_authorization.owner_distribution_authorized=true")
    if not _valid_date(authorization.get("authorization_date")):
        missing.append("release_authorization.authorization_date=YYYY-MM-DD")

    if revision.get("repository_url") != REPOSITORY_URL:
        errors.append("repository_revision.repository_url: unexpected repository")
    commit_sha = revision.get("commit_sha")
    if not (_nonempty(commit_sha) and re.fullmatch(r"[0-9a-f]{40}", commit_sha)):
        missing.append("repository_revision.commit_sha=LOWERCASE_40_HEX")
    elif revision.get("immutable_commit_url") != f"{REPOSITORY_URL}/commit/{commit_sha}":
        errors.append("repository_revision.immutable_commit_url: must bind the exact commit SHA")
    if revision.get("final_submission_revision_frozen") is not True:
        missing.append("repository_revision.final_submission_revision_frozen=true")
    reference_kind = revision.get("release_reference_kind")
    if reference_kind not in RELEASE_REFERENCE_KINDS:
        missing.append("repository_revision.release_reference_kind=SUPPORTED_KIND")
    elif reference_kind == "GITHUB_RELEASE":
        if not _nonempty(revision.get("release_tag_or_not_applicable")):
            missing.append("repository_revision.release_tag_or_not_applicable")
        release_url = revision.get("release_url_or_not_applicable")
        if not (_nonempty(release_url) and release_url.startswith(REPOSITORY_URL + "/releases/tag/")):
            errors.append("repository_revision.release_url_or_not_applicable: invalid GitHub release URL")
    else:
        for key in ("release_tag_or_not_applicable", "release_url_or_not_applicable"):
            if revision.get(key) != "NOT_APPLICABLE":
                errors.append(f"repository_revision.{key}: must be NOT_APPLICABLE")
    if revision.get("release_reference_matches_commit") is not True:
        missing.append("repository_revision.release_reference_matches_commit=true")

    archive_kind = archive.get("kind")
    if archive_kind not in ARCHIVE_KINDS:
        missing.append("archive.kind=CAS_Q3_AGGREGATE_V2_OR_AUTHORIZED_SUCCESSOR")
    for key in ("file", "sha256", "manifest_sha256", "source_aggregate_v2_sha256"):
        if not _nonempty(archive.get(key)):
            missing.append(f"archive.{key}")
    for key in ("sha256", "manifest_sha256", "source_aggregate_v2_sha256"):
        value = archive.get(key)
        if _nonempty(value) and not _valid_digest(value):
            errors.append(f"archive.{key}: must be a lowercase SHA-256 digest")
    if archive.get("source_aggregate_v2_sha256") != AGGREGATE_V2_SHA256:
        errors.append("archive.source_aggregate_v2_sha256: unexpected source candidate")
    if archive_kind == "CAS_Q3_AGGREGATE_V2":
        if archive.get("sha256") != AGGREGATE_V2_SHA256:
            errors.append("archive.sha256: exact aggregate V2 hash required for this kind")
        if archive.get("successor_reason_or_not_applicable") != "NOT_APPLICABLE":
            errors.append("archive.successor_reason_or_not_applicable: must be NOT_APPLICABLE")
    elif archive_kind == "AUTHORIZED_SUCCESSOR" and not _nonempty(
        archive.get("successor_reason_or_not_applicable")
    ):
        missing.append("archive.successor_reason_or_not_applicable")
    for key in (
        "model_weights_in_archive",
        "benchmark_payloads_answers_or_per_question_records_in_archive",
    ):
        if archive.get(key) is not False:
            errors.append(f"archive.{key}: must be false")

    if persistent.get("identifier_kind") not in IDENTIFIER_KINDS:
        missing.append("persistent_record.identifier_kind=SUPPORTED_KIND")
    for key in ("identifier", "landing_url"):
        if not _nonempty(persistent.get(key)):
            missing.append(f"persistent_record.{key}")
    if _nonempty(persistent.get("landing_url")) and not persistent["landing_url"].startswith("https://"):
        errors.append("persistent_record.landing_url: must use HTTPS")
    if persistent.get("resolution_status") != "VERIFIED_RESOLVING":
        missing.append("persistent_record.resolution_status=VERIFIED_RESOLVING")
    if persistent.get("landing_record_binds_exact_archive_sha256") is not True:
        missing.append("persistent_record.landing_record_binds_exact_archive_sha256=true")

    request_status = restricted.get("editor_request_status")
    if request_status not in {"NOT_REQUESTED", "REQUESTED"}:
        missing.append("restricted_review_access.editor_request_status=NOT_REQUESTED_OR_REQUESTED")
    elif request_status == "NOT_REQUESTED":
        for key in (
            "channel_status",
            "delivery_evidence_reference_or_not_applicable",
            "access_terms_or_not_applicable",
            "recipient_role_or_not_applicable",
            "delivery_date_or_not_applicable",
        ):
            if restricted.get(key) != "NOT_APPLICABLE":
                errors.append(f"restricted_review_access.{key}: must be NOT_APPLICABLE")
    else:
        if restricted.get("channel_status") != "EDITOR_DESIGNATED_OR_ACCEPTED":
            errors.append(
                "restricted_review_access.channel_status: must be EDITOR_DESIGNATED_OR_ACCEPTED"
            )
        for key in (
            "delivery_evidence_reference_or_not_applicable",
            "access_terms_or_not_applicable",
            "recipient_role_or_not_applicable",
        ):
            if not _nonempty(restricted.get(key)):
                missing.append(f"restricted_review_access.{key}")
        if not _valid_date(restricted.get("delivery_date_or_not_applicable")):
            missing.append("restricted_review_access.delivery_date_or_not_applicable=YYYY-MM-DD")
    if restricted.get("no_unrequested_private_distribution") is not True:
        missing.append("restricted_review_access.no_unrequested_private_distribution=true")

    for key in ("reviewer_role",):
        if not _nonempty(review.get(key)):
            missing.append(f"manual_review.{key}")
    if not _valid_date(review.get("review_date")):
        missing.append("manual_review.review_date=YYYY-MM-DD")
    for key in (
        "authorization_record_compared_to_activation_record",
        "commit_url_compared_to_commit_sha",
        "archive_hash_compared_to_retained_bytes",
        "persistent_landing_record_visually_inspected",
        "legal_advice_not_claimed_unless_issued_by_counsel",
    ):
        if review.get(key) is not True:
            missing.append(f"manual_review.{key}=true")

    path = archive_path_override or _safe_archive_path(archive.get("file"))
    archive_bytes_read = 0
    archive_digest_matches = False
    if path is None:
        if _nonempty(archive.get("file")):
            errors.append("archive.file: must stay under evidence/private/release_activation")
    elif not path.is_file():
        missing.append("archive.file: retained archive is missing")
    elif path.is_symlink():
        errors.append("archive.file: symbolic links are not accepted")
    else:
        archive_bytes_read = path.stat().st_size
        archive_digest_matches = _sha256(path) == archive.get("sha256")
        if not archive_digest_matches:
            errors.append("archive.sha256: does not match retained archive bytes")

    missing = sorted(set(missing))
    errors = sorted(set(errors))
    complete = not missing and not errors and archive_digest_matches
    return {
        "schema_version": 1,
        "decision": (
            "PASS_RELEASE_ACTIVATION_RECORD_STRUCTURALLY_COMPLETE_PENDING_CLIENT_CONTENT_FINAL_ARTIFACT_AND_ASTRA_AUDITS"
            if complete
            else "FAIL_CLOSED_RELEASE_ACTIVATION_RECORD_INCOMPLETE_OR_INVALID"
        ),
        "complete": complete,
        "template_mode": False,
        "missing_field_paths": missing,
        "validation_error_paths": errors,
        "private_values_emitted": False,
        "archive_bytes_read": archive_bytes_read,
        "archive_sha256_matches": archive_digest_matches,
        "record_asserts_owner_authorization": authorization.get("owner_distribution_authorized") is True,
        "external_urls_fetched": False,
        "client_content_audit_required": True,
        "final_artifact_rebind_required": True,
        "astra_xhigh_final_audit_required": True,
        "distribution_authorized_by_verifier": False,
        "submission_authorized": False,
        "p0_g_closed": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=LOCAL_INPUT)
    parser.add_argument("--check-template", action="store_true")
    args = parser.parse_args()
    path = TEMPLATE if args.check_template else args.input
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        result = {
            "schema_version": 1,
            "decision": "FAIL_CLOSED_RELEASE_ACTIVATION_RECORD_INPUT_MISSING",
            "complete": False,
            "template_mode": False,
            "missing_field_paths": ["docs/cas_q3/RELEASE_ACTIVATION_RECORD.local.json"],
            "validation_error_paths": [],
            "private_values_emitted": False,
            "archive_bytes_read": 0,
            "external_urls_fetched": False,
            "distribution_authorized_by_verifier": False,
            "submission_authorized": False,
            "p0_g_closed": False,
            "cas_q3_status": "NOT_READY",
        }
        print(json.dumps(result, indent=2))
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "decision": "FAIL_CLOSED_RELEASE_ACTIVATION_RECORD_JSON_UNREADABLE",
            "complete": False,
            "template_mode": bool(args.check_template),
            "missing_field_paths": [],
            "validation_error_paths": [type(exc).__name__],
            "private_values_emitted": False,
            "archive_bytes_read": 0,
            "external_urls_fetched": False,
            "distribution_authorized_by_verifier": False,
            "submission_authorized": False,
            "p0_g_closed": False,
            "cas_q3_status": "NOT_READY",
        }
        print(json.dumps(result, indent=2))
        return 2
    result = validate(data, check_template=args.check_template)
    print(json.dumps(result, indent=2))
    passed_template = args.check_template and not result["validation_error_paths"]
    return 0 if passed_template or result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
