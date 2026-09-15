#!/usr/bin/env python3
"""Preflight private owner/institution evidence for the P0-G release boundary.

The verifier authenticates bytes and validates redaction-safe structure. It
does not interpret legal advice, authorize distribution, or close P0-G. A
separate client content audit and explicit owner release decision remain
mandatory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "cas_q3" / "INSTITUTIONAL_RELEASE_RECORD_TEMPLATE.json"
LOCAL_INPUT = ROOT / "docs" / "cas_q3" / "INSTITUTIONAL_RELEASE_RECORD.local.json"
PRIVATE_EVIDENCE_ROOT = ROOT / "evidence" / "private" / "institutional_release_record"
AGGREGATE_V2_SHA256 = "4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8"
EVIDENCE_KINDS = {
    "INSTITUTIONAL_EMAIL",
    "INSTITUTIONAL_LETTER",
    "INSTITUTIONAL_RESEARCH_SYSTEM_RECORD",
    "LEGAL_REVIEW_MEMO",
    "OWNER_INSTITUTION_EVIDENCE_BUNDLE",
}
SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".eml", ".msg", ".html", ".htm", ".zip"}
ACCEPTED_BOUNDARY_DECISIONS = {
    "ACCEPTED_FOR_PUBLICATION_AND_NO_WEIGHT_RELEASE_SCOPE",
    "NO_INSTITUTIONAL_REVIEW_REQUIRED_FOR_NO_WEIGHT_RELEASE_SCOPE",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: must be an object")
        return {}
    return value


def _safe_relative_evidence_path(value: Any) -> Path | None:
    if not _nonempty(value):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return None
    resolved = (ROOT / candidate).resolve()
    if not resolved.is_relative_to(PRIVATE_EVIDENCE_ROOT.resolve()):
        return None
    return resolved


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate(
    data: Any,
    *,
    check_template: bool = False,
    evidence_path_override: Path | None = None,
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
                "PASS_INSTITUTIONAL_RELEASE_RECORD_TEMPLATE_AND_PRIVACY_BOUNDARY"
                if not errors
                else "FAIL_INSTITUTIONAL_RELEASE_RECORD_TEMPLATE"
            ),
            "complete": False,
            "template_mode": True,
            "missing_field_paths": [],
            "validation_error_paths": sorted(set(errors)),
            "private_values_emitted": False,
            "evidence_bytes_read": 0,
            "content_independently_certified": False,
            "p0_g_closed": False,
            "distribution_authorized": False,
            "cas_q3_status": "NOT_READY",
        }

    evidence = _object(root.get("evidence"), "evidence", errors)
    license_decision = _object(root.get("license_decision"), "license_decision", errors)
    boundary = _object(root.get("third_party_scope_decision"), "third_party_scope_decision", errors)
    review = _object(root.get("manual_review"), "manual_review", errors)

    for key in ("file", "sha256", "kind", "issuing_office_or_evidence_bundle_owner", "obtained_date"):
        if not _nonempty(evidence.get(key)):
            missing.append(f"evidence.{key}")
    if evidence.get("kind") not in EVIDENCE_KINDS:
        missing.append("evidence.kind=SUPPORTED_OWNER_INSTITUTION_RECORD_KIND")
    if evidence.get("authenticated_or_formally_retained") is not True:
        missing.append("evidence.authenticated_or_formally_retained=true")
    sha256 = evidence.get("sha256")
    if _nonempty(sha256) and not re.fullmatch(r"[0-9a-f]{64}", sha256):
        errors.append("evidence.sha256: must be a lowercase SHA-256 digest")
    obtained_date = evidence.get("obtained_date")
    if _nonempty(obtained_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", obtained_date):
        errors.append("evidence.obtained_date: must use YYYY-MM-DD")

    if license_decision.get("project_code_license") != "Apache-2.0":
        missing.append("license_decision.project_code_license=Apache-2.0")
    for key in ("legal_copyright_holder", "copyright_year_or_range", "notice_decision_evidence"):
        if not _nonempty(license_decision.get(key)):
            missing.append(f"license_decision.{key}")
    year = license_decision.get("copyright_year_or_range")
    if _nonempty(year) and not re.fullmatch(r"\d{4}(?:-\d{4})?", year):
        errors.append("license_decision.copyright_year_or_range: must be YYYY or YYYY-YYYY")
    if license_decision.get("holder_may_license_project_authored_material") is not True:
        missing.append("license_decision.holder_may_license_project_authored_material=true")

    release_review_required = license_decision.get("institutional_release_review_required")
    if not isinstance(release_review_required, bool):
        missing.append("license_decision.institutional_release_review_required")
    elif release_review_required and license_decision.get("institutional_release_review_status") != "APPROVED":
        errors.append("license_decision.institutional_release_review_status: must be APPROVED")
    elif not release_review_required and license_decision.get("institutional_release_review_status") != "NOT_REQUIRED":
        errors.append("license_decision.institutional_release_review_status: must be NOT_REQUIRED")

    notice_required = license_decision.get("project_specific_notice_required")
    if not isinstance(notice_required, bool):
        missing.append("license_decision.project_specific_notice_required")
    elif notice_required and not str(license_decision.get("notice_decision_evidence", "")).startswith("APPROVED_NOTICE:"):
        errors.append("license_decision.notice_decision_evidence: required NOTICE must use APPROVED_NOTICE:<private reference>")
    elif not notice_required and license_decision.get("notice_decision_evidence") != "NOT_REQUIRED":
        errors.append("license_decision.notice_decision_evidence: must be NOT_REQUIRED")

    for key in ("qwen_boundary_decision", "deberta_boundary_decision"):
        if boundary.get(key) not in ACCEPTED_BOUNDARY_DECISIONS:
            missing.append(f"third_party_scope_decision.{key}=ACCEPTED_OR_NOT_REQUIRED_NO_WEIGHT_SCOPE")
    for key in (
        "qwen_weights_in_release",
        "deberta_weights_in_release",
        "benchmark_payloads_or_answers_in_release",
        "per_question_records_in_release",
    ):
        if boundary.get(key) is not False:
            errors.append(f"third_party_scope_decision.{key}: must be false")
    if boundary.get("aggregate_v2_candidate_sha256") != AGGREGATE_V2_SHA256:
        errors.append("third_party_scope_decision.aggregate_v2_candidate_sha256: unexpected candidate")
    if boundary.get("aggregate_v2_scope_reviewed") is not True:
        missing.append("third_party_scope_decision.aggregate_v2_scope_reviewed=true")

    for key in ("reviewer_role", "review_date"):
        if not _nonempty(review.get(key)):
            missing.append(f"manual_review.{key}")
    review_date = review.get("review_date")
    if _nonempty(review_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_date):
        errors.append("manual_review.review_date: must use YYYY-MM-DD")
    for key in ("record_visually_inspected", "metadata_matches_record", "legal_advice_not_claimed_unless_issued_by_counsel"):
        if review.get(key) is not True:
            missing.append(f"manual_review.{key}=true")

    path = evidence_path_override or _safe_relative_evidence_path(evidence.get("file"))
    evidence_bytes_read = 0
    evidence_digest_matches = False
    if path is None:
        if _nonempty(evidence.get("file")):
            errors.append("evidence.file: must stay under evidence/private/institutional_release_record")
    elif path.suffix.lower() not in SUPPORTED_SUFFIXES:
        errors.append("evidence.file: unsupported file extension")
    elif not path.is_file():
        missing.append("evidence.file: local evidence file is missing")
    elif path.is_symlink():
        errors.append("evidence.file: symbolic links are not accepted")
    else:
        evidence_bytes_read = path.stat().st_size
        evidence_digest_matches = _digest(path) == sha256
        if not evidence_digest_matches:
            errors.append("evidence.sha256: does not match local evidence bytes")

    missing = sorted(set(missing))
    errors = sorted(set(errors))
    complete = not missing and not errors and evidence_digest_matches
    return {
        "schema_version": 1,
        "decision": (
            "PASS_PRIVATE_INSTITUTIONAL_RELEASE_RECORD_INTEGRITY_PREFLIGHT_PENDING_CLIENT_AND_OWNER_DECISIONS"
            if complete
            else "FAIL_CLOSED_INSTITUTIONAL_RELEASE_RECORD_INCOMPLETE_OR_INVALID"
        ),
        "complete": complete,
        "template_mode": False,
        "missing_field_paths": missing,
        "validation_error_paths": errors,
        "private_values_emitted": False,
        "evidence_bytes_read": evidence_bytes_read,
        "evidence_sha256_matches": evidence_digest_matches,
        "release_boundary_structurally_recorded": complete,
        "content_independently_certified": False,
        "independent_client_content_audit_required": True,
        "explicit_owner_archive_authorization_required": True,
        "persistent_identifier_required_after_authorization": True,
        "p0_g_closed": False,
        "distribution_authorized": False,
        "submission_authorized": False,
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
            "decision": "FAIL_CLOSED_INSTITUTIONAL_RELEASE_RECORD_INPUT_MISSING",
            "complete": False,
            "template_mode": False,
            "missing_field_paths": ["docs/cas_q3/INSTITUTIONAL_RELEASE_RECORD.local.json"],
            "validation_error_paths": [],
            "private_values_emitted": False,
            "evidence_bytes_read": 0,
            "content_independently_certified": False,
            "p0_g_closed": False,
            "distribution_authorized": False,
            "submission_authorized": False,
            "cas_q3_status": "NOT_READY",
        }
        print(json.dumps(result, indent=2))
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "decision": "FAIL_CLOSED_INSTITUTIONAL_RELEASE_RECORD_JSON_UNREADABLE",
            "complete": False,
            "template_mode": bool(args.check_template),
            "missing_field_paths": [],
            "validation_error_paths": [type(exc).__name__],
            "private_values_emitted": False,
            "evidence_bytes_read": 0,
            "content_independently_certified": False,
            "p0_g_closed": False,
            "distribution_authorized": False,
            "submission_authorized": False,
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
