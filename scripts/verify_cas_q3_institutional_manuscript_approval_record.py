#!/usr/bin/env python3
"""Preflight a private institutional manuscript-approval record.

The verifier binds retained approval evidence to exact evidence and manuscript
bytes. It does not interpret institutional policy, certify the record's
substance, or authorize submission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "cas_q3" / "INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD_TEMPLATE.json"
LOCAL_INPUT = ROOT / "docs" / "cas_q3" / "INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD.local.json"
PRIVATE_EVIDENCE_ROOT = ROOT / "evidence" / "private" / "institutional_manuscript_approval"
EVIDENCE_KINDS = {
    "INSTITUTIONAL_EMAIL",
    "INSTITUTIONAL_LETTER",
    "INSTITUTIONAL_RESEARCH_SYSTEM_RECORD",
    "SUPERVISOR_AND_SCHOOL_APPROVAL_BUNDLE",
}
SUPPORTED_EVIDENCE_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".eml", ".msg", ".html", ".htm", ".zip"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: must be an object")
        return {}
    return value


def _safe_private_evidence_path(value: Any) -> Path | None:
    if not _nonempty(value):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return None
    resolved = (ROOT / candidate).resolve()
    if not resolved.is_relative_to(PRIVATE_EVIDENCE_ROOT.resolve()):
        return None
    return resolved


def _safe_manuscript_path(value: Any) -> Path | None:
    if not _nonempty(value):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return None
    resolved = (ROOT / candidate).resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
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
    manuscript_path_override: Path | None = None,
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
            "decision": "PASS_INSTITUTIONAL_MANUSCRIPT_APPROVAL_TEMPLATE_AND_PRIVACY_BOUNDARY" if not errors else "FAIL_INSTITUTIONAL_MANUSCRIPT_APPROVAL_TEMPLATE",
            "complete": False,
            "template_mode": True,
            "missing_field_paths": [],
            "validation_error_paths": sorted(set(errors)),
            "private_values_emitted": False,
            "evidence_bytes_read": 0,
            "manuscript_bytes_read": 0,
            "content_independently_certified": False,
            "p0_i_closed": False,
            "submission_authorized": False,
            "cas_q3_status": "NOT_READY",
        }

    evidence = _object(root.get("evidence"), "evidence", errors)
    decision = _object(root.get("approval_decision"), "approval_decision", errors)
    review = _object(root.get("manual_review"), "manual_review", errors)

    for key in ("file", "sha256", "kind", "issuing_office", "obtained_date"):
        if not _nonempty(evidence.get(key)):
            missing.append(f"evidence.{key}")
    if evidence.get("kind") not in EVIDENCE_KINDS:
        missing.append("evidence.kind=SUPPORTED_INSTITUTIONAL_APPROVAL_RECORD_KIND")
    if evidence.get("authenticated_or_institution_issued") is not True:
        missing.append("evidence.authenticated_or_institution_issued=true")
    evidence_sha = evidence.get("sha256")
    if _nonempty(evidence_sha) and not re.fullmatch(r"[0-9a-f]{64}", evidence_sha):
        errors.append("evidence.sha256: must be a lowercase SHA-256 digest")
    obtained_date = evidence.get("obtained_date")
    if _nonempty(obtained_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", obtained_date):
        errors.append("evidence.obtained_date: must use YYYY-MM-DD")

    if decision.get("institutional_manuscript_approval_required") is not True:
        errors.append("approval_decision.institutional_manuscript_approval_required: must be true")
    if decision.get("institutional_manuscript_approval_status") != "APPROVED":
        errors.append("approval_decision.institutional_manuscript_approval_status: must be APPROVED")
    for key in ("approved_manuscript_file", "approved_manuscript_sha256", "target_journal", "approval_date", "conditions_or_none"):
        if not _nonempty(decision.get(key)):
            missing.append(f"approval_decision.{key}")
    manuscript_sha = decision.get("approved_manuscript_sha256")
    if _nonempty(manuscript_sha) and not re.fullmatch(r"[0-9a-f]{64}", manuscript_sha):
        errors.append("approval_decision.approved_manuscript_sha256: must be a lowercase SHA-256 digest")
    approval_date = decision.get("approval_date")
    if _nonempty(approval_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", approval_date):
        errors.append("approval_decision.approval_date: must use YYYY-MM-DD")
    if _nonempty(decision.get("target_journal")) and decision.get("target_journal") != "Applied Intelligence":
        errors.append("approval_decision.target_journal: must equal Applied Intelligence")

    for key in ("reviewer_role", "review_date"):
        if not _nonempty(review.get(key)):
            missing.append(f"manual_review.{key}")
    review_date = review.get("review_date")
    if _nonempty(review_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_date):
        errors.append("manual_review.review_date: must use YYYY-MM-DD")
    for key in ("record_visually_inspected", "metadata_matches_record", "approved_manuscript_digest_recomputed"):
        if review.get(key) is not True:
            missing.append(f"manual_review.{key}=true")

    evidence_path = evidence_path_override or _safe_private_evidence_path(evidence.get("file"))
    evidence_bytes_read = 0
    evidence_digest_matches = False
    if evidence_path is None:
        if _nonempty(evidence.get("file")):
            errors.append("evidence.file: must stay under evidence/private/institutional_manuscript_approval")
    elif evidence_path.suffix.lower() not in SUPPORTED_EVIDENCE_SUFFIXES:
        errors.append("evidence.file: unsupported file extension")
    elif not evidence_path.is_file():
        missing.append("evidence.file: local evidence file is missing")
    elif evidence_path.is_symlink():
        errors.append("evidence.file: symbolic links are not accepted")
    else:
        evidence_bytes_read = evidence_path.stat().st_size
        evidence_digest_matches = _digest(evidence_path) == evidence_sha
        if not evidence_digest_matches:
            errors.append("evidence.sha256: does not match local evidence bytes")

    manuscript_path = manuscript_path_override or _safe_manuscript_path(decision.get("approved_manuscript_file"))
    manuscript_bytes_read = 0
    manuscript_digest_matches = False
    if manuscript_path is None:
        if _nonempty(decision.get("approved_manuscript_file")):
            errors.append("approval_decision.approved_manuscript_file: must be a repository-relative path")
    elif manuscript_path.suffix.lower() not in {".pdf", ".tex", ".docx"}:
        errors.append("approval_decision.approved_manuscript_file: unsupported manuscript extension")
    elif not manuscript_path.is_file():
        missing.append("approval_decision.approved_manuscript_file: local manuscript file is missing")
    elif manuscript_path.is_symlink():
        errors.append("approval_decision.approved_manuscript_file: symbolic links are not accepted")
    else:
        manuscript_bytes_read = manuscript_path.stat().st_size
        manuscript_digest_matches = _digest(manuscript_path) == manuscript_sha
        if not manuscript_digest_matches:
            errors.append("approval_decision.approved_manuscript_sha256: does not match local manuscript bytes")

    missing = sorted(set(missing))
    errors = sorted(set(errors))
    complete = not missing and not errors and evidence_digest_matches and manuscript_digest_matches
    return {
        "schema_version": 1,
        "decision": "PASS_PRIVATE_INSTITUTIONAL_MANUSCRIPT_APPROVAL_INTEGRITY_PREFLIGHT_PENDING_CLIENT_CONTENT_AND_FINAL_AUDITS" if complete else "FAIL_CLOSED_INSTITUTIONAL_MANUSCRIPT_APPROVAL_INCOMPLETE_OR_INVALID",
        "complete": complete,
        "template_mode": False,
        "missing_field_paths": missing,
        "validation_error_paths": errors,
        "private_values_emitted": False,
        "evidence_bytes_read": evidence_bytes_read,
        "manuscript_bytes_read": manuscript_bytes_read,
        "evidence_sha256_matches": evidence_digest_matches,
        "approved_manuscript_sha256_matches": manuscript_digest_matches,
        "content_independently_certified": False,
        "independent_client_content_audit_required": True,
        "final_astra_xhigh_audit_required": True,
        "p0_i_closed": False,
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
            "decision": "FAIL_CLOSED_INSTITUTIONAL_MANUSCRIPT_APPROVAL_INPUT_MISSING",
            "complete": False,
            "template_mode": False,
            "missing_field_paths": ["docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD.local.json"],
            "validation_error_paths": [],
            "private_values_emitted": False,
            "p0_i_closed": False,
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
            "decision": "FAIL_CLOSED_INSTITUTIONAL_MANUSCRIPT_APPROVAL_JSON_UNREADABLE",
            "complete": False,
            "template_mode": bool(args.check_template),
            "missing_field_paths": [],
            "validation_error_paths": [type(exc).__name__],
            "private_values_emitted": False,
            "p0_i_closed": False,
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
