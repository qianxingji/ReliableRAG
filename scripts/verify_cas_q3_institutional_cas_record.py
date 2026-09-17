#!/usr/bin/env python3
"""Preflight a private institution-recognized CAS journal record.

The verifier fixes the private evidence bytes and validates a redaction-safe
metadata description. It deliberately does not parse or certify the record's
content. A separate client content audit remains mandatory before P0-H closes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "cas_q3" / "INSTITUTIONAL_CAS_RECORD_TEMPLATE.json"
LOCAL_INPUT = ROOT / "docs" / "cas_q3" / "INSTITUTIONAL_CAS_RECORD.local.json"
PRIVATE_EVIDENCE_ROOT = ROOT / "evidence" / "private" / "institutional_cas_record"
EVIDENCE_KINDS = {
    "AUTHENTICATED_CAS_PLATFORM_SCREENSHOT",
    "AUTHENTICATED_CAS_PLATFORM_EXPORT",
    "INSTITUTIONAL_EMAIL",
    "INSTITUTIONAL_LETTER",
    "INSTITUTIONAL_RESEARCH_SYSTEM_RECORD",
}
SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".eml", ".msg", ".html", ".htm"}
QUALIFYING_TIERS = {"Q1", "Q2", "Q3"}


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
                "PASS_INSTITUTIONAL_CAS_RECORD_TEMPLATE_AND_PRIVACY_BOUNDARY"
                if not errors
                else "FAIL_INSTITUTIONAL_CAS_RECORD_TEMPLATE"
            ),
            "complete": False,
            "template_mode": True,
            "missing_field_paths": [],
            "validation_error_paths": sorted(set(errors)),
            "private_values_emitted": False,
            "evidence_bytes_read": 0,
            "content_independently_certified": False,
            "p0_h_closed": False,
            "cas_q3_status": "NOT_READY",
        }

    evidence = _object(root.get("evidence"), "evidence", errors)
    facts = _object(root.get("recorded_facts"), "recorded_facts", errors)
    review = _object(root.get("manual_review"), "manual_review", errors)

    for key in ("file", "sha256", "kind", "issuing_office", "obtained_date"):
        if not _nonempty(evidence.get(key)):
            missing.append(f"evidence.{key}")
    if evidence.get("kind") not in EVIDENCE_KINDS:
        missing.append("evidence.kind=SUPPORTED_INSTITUTIONAL_RECORD_KIND")
    if evidence.get("authenticated_or_institution_issued") is not True:
        missing.append("evidence.authenticated_or_institution_issued=true")
    sha256 = evidence.get("sha256")
    if _nonempty(sha256) and not re.fullmatch(r"[0-9a-f]{64}", sha256):
        errors.append("evidence.sha256: must be a lowercase SHA-256 digest")
    obtained_date = evidence.get("obtained_date")
    if _nonempty(obtained_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", obtained_date):
        errors.append("evidence.obtained_date: must use YYYY-MM-DD")

    expected_facts = {
        "category_basis": "MAJOR",
        "category_name": "Computer Science",
        "journal_title": "Applied Intelligence",
        "print_issn": "0924-669X",
        "electronic_issn": "1573-7497",
    }
    for key, expected in expected_facts.items():
        value = facts.get(key)
        if not _nonempty(value):
            missing.append(f"recorded_facts.{key}")
        elif value != expected:
            errors.append(f"recorded_facts.{key}: must equal {expected}")
    year = facts.get("cas_edition_year")
    if not isinstance(year, int):
        missing.append("recorded_facts.cas_edition_year")
    elif year < 2020 or year > 2100:
        errors.append("recorded_facts.cas_edition_year: implausible year")
    tier = facts.get("tier")
    if tier not in QUALIFYING_TIERS:
        missing.append("recorded_facts.tier=Q1_Q2_or_Q3")
    for key in ("recognition_date_rule", "title_issn_change_treatment"):
        if not _nonempty(facts.get(key)):
            missing.append(f"recorded_facts.{key}")
    if facts.get("applies_to_hbut_first_affiliation_output") is not True:
        missing.append("recorded_facts.applies_to_hbut_first_affiliation_output=true")

    for key in ("reviewer_role", "review_date"):
        if not _nonempty(review.get(key)):
            missing.append(f"manual_review.{key}")
    review_date = review.get("review_date")
    if _nonempty(review_date) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_date):
        errors.append("manual_review.review_date: must use YYYY-MM-DD")
    for key in ("record_visually_inspected", "metadata_matches_record", "jcr_result_not_substituted"):
        if review.get(key) is not True:
            missing.append(f"manual_review.{key}=true")

    path = evidence_path_override or _safe_relative_evidence_path(evidence.get("file"))
    evidence_bytes_read = 0
    evidence_digest_matches = False
    if path is None:
        if _nonempty(evidence.get("file")):
            errors.append("evidence.file: must stay under evidence/private/institutional_cas_record")
    elif path.suffix.lower() not in SUPPORTED_SUFFIXES:
        errors.append("evidence.file: unsupported file extension")
    elif not path.is_file():
        missing.append("evidence.file: local evidence file is missing")
    elif path.is_symlink():
        errors.append("evidence.file: symbolic links are not accepted")
    else:
        evidence_bytes_read = path.stat().st_size
        actual = _digest(path)
        evidence_digest_matches = actual == sha256
        if not evidence_digest_matches:
            errors.append("evidence.sha256: does not match local evidence bytes")

    missing = sorted(set(missing))
    errors = sorted(set(errors))
    complete = not missing and not errors and evidence_digest_matches
    return {
        "schema_version": 1,
        "decision": (
            "PASS_PRIVATE_INSTITUTIONAL_CAS_RECORD_INTEGRITY_PREFLIGHT_PENDING_CLIENT_CONTENT_AUDIT"
            if complete
            else "FAIL_CLOSED_INSTITUTIONAL_CAS_RECORD_INCOMPLETE_OR_INVALID"
        ),
        "complete": complete,
        "template_mode": False,
        "missing_field_paths": missing,
        "validation_error_paths": errors,
        "private_values_emitted": False,
        "evidence_bytes_read": evidence_bytes_read,
        "evidence_sha256_matches": evidence_digest_matches,
        "target_tier_or_better_structurally_recorded": tier in QUALIFYING_TIERS,
        "content_independently_certified": False,
        "independent_client_content_audit_required": True,
        "p0_h_closed": False,
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
            "decision": "FAIL_CLOSED_INSTITUTIONAL_CAS_RECORD_INPUT_MISSING",
            "complete": False,
            "template_mode": False,
            "missing_field_paths": ["docs/cas_q3/INSTITUTIONAL_CAS_RECORD.local.json"],
            "validation_error_paths": [],
            "private_values_emitted": False,
            "evidence_bytes_read": 0,
            "content_independently_certified": False,
            "p0_h_closed": False,
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
            "decision": "FAIL_CLOSED_INSTITUTIONAL_CAS_RECORD_JSON_UNREADABLE",
            "complete": False,
            "template_mode": bool(args.check_template),
            "missing_field_paths": [],
            "validation_error_paths": [type(exc).__name__],
            "private_values_emitted": False,
            "evidence_bytes_read": 0,
            "content_independently_certified": False,
            "p0_h_closed": False,
            "submission_authorized": False,
            "cas_q3_status": "NOT_READY",
        }
        print(json.dumps(result, indent=2))
        return 2
    result = validate(data, check_template=args.check_template)
    print(json.dumps(result, indent=2))
    return 0 if args.check_template and not result["validation_error_paths"] or result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
