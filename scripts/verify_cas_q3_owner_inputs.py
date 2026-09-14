#!/usr/bin/env python3
"""Validate local P0-G/H/I owner inputs without printing personal values."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS_TEMPLATE.json"
LICENSE_OPTIONS = {"Apache-2.0", "MIT", "NO_PUBLIC_CODE_LICENSE_YET"}
PUBLICATION_CHARGE_ROUTES = {"ACCEPTED", "WAIVER_CONFIRMED", "NO_MANDATORY_APC"}
ALL_CREDIT_ROLES = {
    "Conceptualization",
    "Methodology",
    "Software",
    "Validation",
    "Formal analysis",
    "Investigation",
    "Data curation",
    "Writing - original draft",
    "Writing - review and editing",
    "Visualization",
    "Supervision",
    "Project administration",
    "Funding acquisition",
}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def unresolved_text(value: Any) -> bool:
    """Treat explicit pending placeholders as unanswered owner facts."""
    if not nonempty(value):
        return True
    return bool(
        re.search(r"\bpending(?:[_\s-]|$)|\bpendin\b", value, flags=re.IGNORECASE)
        or re.search(r"待定|待核实|待确认", value)
    )


def require_object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: must be an object")
        return {}
    return value


def require_text(container: dict[str, Any], key: str, prefix: str, missing: list[str]) -> None:
    if not nonempty(container.get(key)):
        missing.append(f"{prefix}.{key}")


def validate(data: Any, *, template_mode: bool = False) -> dict[str, Any]:
    missing: list[str] = []
    errors: list[str] = []
    root = require_object(data, "$", errors)
    if root.get("schema_version") != 1:
        errors.append("schema_version: must equal 1")

    license_data = require_object(root.get("project_license"), "project_license", errors)
    journal = require_object(root.get("target_journal"), "target_journal", errors)
    authorship = require_object(root.get("authorship"), "authorship", errors)
    declarations = require_object(root.get("declarations"), "declarations", errors)

    if template_mode:
        expected = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        if root != expected:
            errors.append("template: tracked template differs from the canonical placeholder structure")
        owner_fields = [
            license_data.get("selected_option"),
            journal.get("selected_journal"),
            authorship.get("corresponding_author_name"),
            declarations.get("funding_statement"),
        ]
        if any(value is not None for value in owner_fields):
            errors.append("template: owner-supplied sentinel fields must remain null")
        if authorship.get("authors_in_order") != [] or authorship.get("affiliations") != []:
            errors.append("template: identity arrays must remain empty")
        return {
            "schema_version": 1,
            "decision": "PASS_OWNER_INPUTS_TEMPLATE_STRUCTURE_AND_PRIVACY_BOUNDARY" if not errors else "FAIL_OWNER_INPUTS_TEMPLATE",
            "complete": False,
            "template_mode": True,
            "missing_field_paths": [],
            "validation_error_paths": sorted(errors),
            "personal_values_emitted": False,
            "cas_q3_status": "NOT_READY",
        }

    selected_license = license_data.get("selected_option")
    if selected_license is None:
        missing.append("project_license.selected_option")
    elif selected_license not in LICENSE_OPTIONS:
        errors.append("project_license.selected_option: unsupported option")
    for key in ("legal_copyright_holder", "copyright_year_or_range", "notice_or_review_evidence"):
        require_text(license_data, key, "project_license", missing)
    if unresolved_text(license_data.get("legal_copyright_holder")):
        missing.append("project_license.legal_copyright_holder")
    if license_data.get("holder_may_license_project_authored_material") is not True:
        missing.append("project_license.holder_may_license_project_authored_material=true")
    review_required = license_data.get("institutional_release_review_required")
    if not isinstance(review_required, bool):
        missing.append("project_license.institutional_release_review_required")
    elif review_required is True:
        review_status = license_data.get("release_review_status")
        if review_status in {None, "PENDING", "PENDING_VERIFICATION"}:
            missing.append("project_license.release_review_status=APPROVED")
        elif review_status != "APPROVED":
            errors.append("project_license.release_review_status: must be APPROVED")
    elif license_data.get("release_review_status") != "NOT_REQUIRED":
        errors.append("project_license.release_review_status: must be NOT_REQUIRED")

    for key in (
        "selected_journal",
        "current_title",
        "institution_recognized_cas_edition_year",
        "category_name",
        "title_issn_change_treatment",
        "recognition_date_rule",
        "retained_authority_path_or_url",
        "institutional_verifier_or_office",
        "verification_date",
        "publication_charge_evidence_or_acknowledgement",
        "data_code_policy_summary",
        "data_code_policy_source_url",
    ):
        require_text(journal, key, "target_journal", missing)
    if unresolved_text(journal.get("institution_recognized_cas_edition_year")):
        missing.append("target_journal.institution_recognized_cas_edition_year")
    if not (nonempty(journal.get("print_issn")) or nonempty(journal.get("online_issn"))):
        missing.append("target_journal.print_issn_or_online_issn")
    if journal.get("category_basis") not in {"MAJOR", "MINOR"}:
        missing.append("target_journal.category_basis=MAJOR_or_MINOR")
    if journal.get("verified_tier") not in {"Q1", "Q2", "Q3"}:
        missing.append("target_journal.verified_tier=Q1_Q2_or_Q3")
    if journal.get("publication_charge_route") not in PUBLICATION_CHARGE_ROUTES:
        missing.append("target_journal.publication_charge_route")

    authors = authorship.get("authors_in_order")
    affiliations = authorship.get("affiliations")
    if not isinstance(authors, list) or not authors:
        missing.append("authorship.authors_in_order")
        authors = []
    if not isinstance(affiliations, list) or not affiliations:
        missing.append("authorship.affiliations")
        affiliations = []

    affiliation_ids: set[str] = set()
    for index, affiliation in enumerate(affiliations):
        item = require_object(affiliation, f"authorship.affiliations[{index}]", errors)
        for key in ("id", "institution", "department", "city", "postal_code", "country"):
            if not nonempty(item.get(key)):
                missing.append(f"authorship.affiliations[{index}].{key}")
        if nonempty(item.get("id")):
            if item["id"] in affiliation_ids:
                errors.append(f"authorship.affiliations[{index}].id: duplicate")
            affiliation_ids.add(item["id"])

    author_names: list[str] = []
    for index, author in enumerate(authors):
        item = require_object(author, f"authorship.authors_in_order[{index}]", errors)
        name = item.get("name")
        if not nonempty(name):
            missing.append(f"authorship.authors_in_order[{index}].name")
        else:
            author_names.append(name)
        ids = item.get("affiliation_ids")
        if not isinstance(ids, list) or not ids:
            missing.append(f"authorship.authors_in_order[{index}].affiliation_ids")
        elif any(not nonempty(value) or value not in affiliation_ids for value in ids):
            errors.append(f"authorship.authors_in_order[{index}].affiliation_ids: unknown id")
        orcid = item.get("orcid")
        if nonempty(orcid) and orcid != "NONE_NOT_SUPPLIED" and not re.fullmatch(r"\d{4}-\d{4}-\d{4}-[\dX]{4}", orcid):
            errors.append(f"authorship.authors_in_order[{index}].orcid: invalid format")
    if len(set(author_names)) != len(author_names):
        errors.append("authorship.authors_in_order: duplicate publishing name")

    for key in ("corresponding_author_name", "corresponding_author_email"):
        require_text(authorship, key, "authorship", missing)
    corresponding = authorship.get("corresponding_author_name")
    if nonempty(corresponding) and corresponding not in author_names:
        errors.append("authorship.corresponding_author_name: must name a listed author")
    email = authorship.get("corresponding_author_email")
    if nonempty(email) and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("authorship.corresponding_author_email: invalid format")

    credit = require_object(authorship.get("credit_role_mapping"), "authorship.credit_role_mapping", errors)
    if set(credit) != ALL_CREDIT_ROLES:
        errors.append("authorship.credit_role_mapping: role set must match template")
    credited_authors: set[str] = set()
    for role in sorted(ALL_CREDIT_ROLES):
        names = credit.get(role)
        if not isinstance(names, list):
            errors.append(f"authorship.credit_role_mapping.{role}: must be an array")
        else:
            if any(name not in author_names for name in names):
                errors.append(f"authorship.credit_role_mapping.{role}: contributor is not a listed author")
            credited_authors.update(name for name in names if name in author_names)
    for index, name in enumerate(author_names):
        if name not in credited_authors:
            missing.append(f"authorship.authors_in_order[{index}].credit_role_assignment")

    for key in (
        "funding_statement",
        "competing_interests_statement",
        "ethics_statement_or_approval",
        "ai_assistance_statement",
        "ai_tool_version_and_use_dates",
        "overlapping_work_or_preprint_disclosure",
    ):
        require_text(declarations, key, "declarations", missing)
    competing = declarations.get("competing_interests_statement")
    if nonempty(competing) and re.fullmatch(
        r"competing\s+interests\s+statement[.。:]?",
        competing.strip(),
        flags=re.IGNORECASE,
    ):
        missing.append("declarations.competing_interests_statement")
    ai_tools = declarations.get("ai_tool_version_and_use_dates")
    if nonempty(ai_tools):
        date_tokens = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", ai_tools)
        if unresolved_text(ai_tools) or len(date_tokens) < 2:
            missing.append("declarations.ai_tool_version_and_use_dates")
        else:
            try:
                start_date, end_date = (date.fromisoformat(value) for value in date_tokens[:2])
            except ValueError:
                errors.append("declarations.ai_tool_version_and_use_dates: dates must be valid YYYY-MM-DD values")
            else:
                if start_date > end_date:
                    errors.append("declarations.ai_tool_version_and_use_dates: start date must not be after end date")
    for key in (
        "ai_assistance_statement_approved",
        "originality_confirmed",
        "exclusive_submission_confirmed",
        "all_authors_approved_final_manuscript_and_order",
    ):
        if declarations.get(key) is not True:
            missing.append(f"declarations.{key}=true")
    manuscript_approval_required = declarations.get("institutional_manuscript_approval_required")
    if not isinstance(manuscript_approval_required, bool):
        missing.append("declarations.institutional_manuscript_approval_required")
    elif manuscript_approval_required is True:
        manuscript_status = declarations.get("institutional_manuscript_approval_status")
        if manuscript_status in {None, "PENDING", "PENDING_VERIFICATION"}:
            missing.append("declarations.institutional_manuscript_approval_status=APPROVED")
        elif manuscript_status != "APPROVED":
            errors.append("declarations.institutional_manuscript_approval_status: must be APPROVED")
    elif declarations.get("institutional_manuscript_approval_status") != "NOT_REQUIRED":
        errors.append("declarations.institutional_manuscript_approval_status: must be NOT_REQUIRED")
    require_text(declarations, "institutional_manuscript_approval_evidence", "declarations", missing)
    if unresolved_text(declarations.get("institutional_manuscript_approval_evidence")):
        missing.append("declarations.institutional_manuscript_approval_evidence")

    missing = sorted(set(missing))
    errors = sorted(set(errors))
    complete = not missing and not errors
    return {
        "schema_version": 1,
        "decision": (
            "PASS_OWNER_INPUTS_COMPLETE_PENDING_INDEPENDENT_EVIDENCE_AND_ARTIFACT_GATES"
            if complete
            else "FAIL_CLOSED_OWNER_INPUTS_INCOMPLETE_OR_INVALID"
        ),
        "complete": complete,
        "template_mode": False,
        "missing_field_paths": missing,
        "validation_error_paths": errors,
        "personal_values_emitted": False,
        "independent_cas_authority_verified": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json")
    parser.add_argument("--check-template", action="store_true")
    args = parser.parse_args()
    path = args.input if args.input.is_absolute() else ROOT / args.input
    if args.check_template:
        path = TEMPLATE
    if not path.is_file():
        result = {
            "schema_version": 1,
            "decision": "FAIL_CLOSED_OWNER_INPUT_FILE_MISSING",
            "complete": False,
            "template_mode": False,
            "missing_field_paths": [str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else "external_input_file"],
            "validation_error_paths": [],
            "personal_values_emitted": False,
            "cas_q3_status": "NOT_READY",
        }
        print(json.dumps(result, indent=2))
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "decision": "FAIL_CLOSED_OWNER_INPUT_JSON_UNREADABLE",
            "complete": False,
            "template_mode": bool(args.check_template),
            "missing_field_paths": [],
            "validation_error_paths": [type(exc).__name__],
            "personal_values_emitted": False,
            "cas_q3_status": "NOT_READY",
        }
        print(json.dumps(result, indent=2))
        return 2
    result = validate(data, template_mode=args.check_template)
    print(json.dumps(result, indent=2))
    return 0 if (result["complete"] or args.check_template and not result["validation_error_paths"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
