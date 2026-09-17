#!/usr/bin/env python3
"""Cross-check the four private P0-G/H/I inputs without echoing their values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.verify_cas_q3_institutional_cas_record import (
        LOCAL_INPUT as CAS_INPUT,
        TEMPLATE as CAS_TEMPLATE,
        validate as validate_cas,
    )
    from scripts.verify_cas_q3_institutional_release_record import (
        LOCAL_INPUT as RELEASE_INPUT,
        TEMPLATE as RELEASE_TEMPLATE,
        validate as validate_release,
    )
    from scripts.verify_cas_q3_institutional_manuscript_approval_record import (
        LOCAL_INPUT as MANUSCRIPT_APPROVAL_INPUT,
        TEMPLATE as MANUSCRIPT_APPROVAL_TEMPLATE,
        validate as validate_manuscript_approval,
    )
    from scripts.verify_cas_q3_owner_inputs import (
        TEMPLATE as OWNER_TEMPLATE,
        validate as validate_owner,
    )
except ModuleNotFoundError:  # Direct execution places scripts/ on sys.path.
    from verify_cas_q3_institutional_cas_record import (
        LOCAL_INPUT as CAS_INPUT,
        TEMPLATE as CAS_TEMPLATE,
        validate as validate_cas,
    )
    from verify_cas_q3_institutional_release_record import (
        LOCAL_INPUT as RELEASE_INPUT,
        TEMPLATE as RELEASE_TEMPLATE,
        validate as validate_release,
    )
    from verify_cas_q3_institutional_manuscript_approval_record import (
        LOCAL_INPUT as MANUSCRIPT_APPROVAL_INPUT,
        TEMPLATE as MANUSCRIPT_APPROVAL_TEMPLATE,
        validate as validate_manuscript_approval,
    )
    from verify_cas_q3_owner_inputs import (
        TEMPLATE as OWNER_TEMPLATE,
        validate as validate_owner,
    )


ROOT = Path(__file__).resolve().parents[1]
OWNER_INPUT = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"
TEMPLATE_RECEIPT = ROOT / "docs" / "cas_q3" / "P0_GHI_EXTERNAL_CLOSURE_PREFLIGHT_VERIFICATION.json"


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "complete": result["complete"],
        "missing_field_count": len(result.get("missing_field_paths", [])),
        "validation_error_count": len(result.get("validation_error_paths", [])),
        "evidence_bytes_read": result.get("evidence_bytes_read", 0),
        "manuscript_bytes_read": result.get("manuscript_bytes_read", 0),
    }


def _missing(decision: str) -> dict[str, Any]:
    return {
        "decision": decision,
        "complete": False,
        "missing_field_paths": ["local_private_input"],
        "validation_error_paths": [],
    }


def _read(path: Path) -> tuple[Any | None, str | None]:
    if not path.is_file():
        return None, "MISSING"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError):
        return None, "UNREADABLE"


def evaluate(
    owner_data: Any | None,
    cas_data: Any | None,
    release_data: Any | None,
    manuscript_approval_data: Any | None,
    *,
    cas_evidence_override: Path | None = None,
    release_evidence_override: Path | None = None,
    manuscript_approval_evidence_override: Path | None = None,
    approved_manuscript_override: Path | None = None,
) -> dict[str, Any]:
    owner_result = (
        validate_owner(owner_data)
        if owner_data is not None
        else _missing("FAIL_CLOSED_OWNER_INPUT_FILE_MISSING")
    )
    cas_result = (
        validate_cas(cas_data, evidence_path_override=cas_evidence_override)
        if cas_data is not None
        else _missing("FAIL_CLOSED_INSTITUTIONAL_CAS_RECORD_INPUT_MISSING")
    )
    release_result = (
        validate_release(release_data, evidence_path_override=release_evidence_override)
        if release_data is not None
        else _missing("FAIL_CLOSED_INSTITUTIONAL_RELEASE_RECORD_INPUT_MISSING")
    )
    manuscript_approval_result = (
        validate_manuscript_approval(
            manuscript_approval_data,
            evidence_path_override=manuscript_approval_evidence_override,
            manuscript_path_override=approved_manuscript_override,
        )
        if manuscript_approval_data is not None
        else _missing("FAIL_CLOSED_INSTITUTIONAL_MANUSCRIPT_APPROVAL_INPUT_MISSING")
    )

    cross_errors: list[str] = []
    if owner_result["complete"] and cas_result["complete"]:
        journal = owner_data["target_journal"]
        facts = cas_data["recorded_facts"]
        comparisons = (
            (journal["selected_journal"], "Applied Intelligence", "owner.target_journal.selected_journal"),
            (journal["current_title"], facts["journal_title"], "owner/cas.current_title"),
            (journal["print_issn"], facts["print_issn"], "owner/cas.print_issn"),
            (journal["online_issn"], facts["electronic_issn"], "owner/cas.electronic_issn"),
            (journal["institution_recognized_cas_edition_year"], str(facts["cas_edition_year"]), "owner/cas.edition_year"),
            (journal["category_basis"], facts["category_basis"], "owner/cas.category_basis"),
            (journal["category_name"], facts["category_name"], "owner/cas.category_name"),
            (journal["verified_tier"], facts["tier"], "owner/cas.tier"),
            (journal["title_issn_change_treatment"], facts["title_issn_change_treatment"], "owner/cas.title_issn_change_treatment"),
            (journal["recognition_date_rule"], facts["recognition_date_rule"], "owner/cas.recognition_date_rule"),
        )
        cross_errors.extend(label for left, right, label in comparisons if left != right)

    if owner_result["complete"] and release_result["complete"]:
        owner_license = owner_data["project_license"]
        release_license = release_data["license_decision"]
        comparisons = (
            (owner_license["selected_option"], release_license["project_code_license"], "owner/release.project_code_license"),
            (owner_license["legal_copyright_holder"], release_license["legal_copyright_holder"], "owner/release.legal_copyright_holder"),
            (owner_license["copyright_year_or_range"], release_license["copyright_year_or_range"], "owner/release.copyright_year_or_range"),
            (owner_license["holder_may_license_project_authored_material"], release_license["holder_may_license_project_authored_material"], "owner/release.holder_license_authority"),
            (owner_license["institutional_release_review_required"], release_license["institutional_release_review_required"], "owner/release.review_required"),
            (owner_license["release_review_status"], release_license["institutional_release_review_status"], "owner/release.review_status"),
        )
        cross_errors.extend(label for left, right, label in comparisons if left != right)

    if owner_result["complete"] and manuscript_approval_result["complete"]:
        owner_declarations = owner_data["declarations"]
        owner_journal = owner_data["target_journal"]
        approval = manuscript_approval_data["approval_decision"]
        comparisons = (
            (
                owner_declarations["institutional_manuscript_approval_required"],
                approval["institutional_manuscript_approval_required"],
                "owner/manuscript_approval.required",
            ),
            (
                owner_declarations["institutional_manuscript_approval_status"],
                approval["institutional_manuscript_approval_status"],
                "owner/manuscript_approval.status",
            ),
            (
                owner_journal["selected_journal"],
                approval["target_journal"],
                "owner/manuscript_approval.target_journal",
            ),
        )
        cross_errors.extend(label for left, right, label in comparisons if left != right)

    all_structurally_complete = all(
        result["complete"]
        for result in (owner_result, cas_result, release_result, manuscript_approval_result)
    )
    cross_errors = sorted(set(cross_errors))
    complete = all_structurally_complete and not cross_errors
    return {
        "schema_version": 1,
        "decision": (
            "PASS_PRIVATE_EXTERNAL_CLOSURE_INPUTS_STRUCTURALLY_COMPLETE_PENDING_CLIENT_CONTENT_ARTIFACT_AND_ASTRA_AUDITS"
            if complete
            else "FAIL_CLOSED_PRIVATE_EXTERNAL_CLOSURE_INPUTS_INCOMPLETE_INVALID_OR_INCONSISTENT"
        ),
        "complete": complete,
        "component_status": {
            "owner_inputs": _summary(owner_result),
            "institutional_cas_record": _summary(cas_result),
            "institutional_release_record": _summary(release_result),
            "institutional_manuscript_approval_record": _summary(manuscript_approval_result),
        },
        "cross_consistency_error_paths": cross_errors,
        "cross_consistency_error_count": len(cross_errors),
        "private_values_emitted": False,
        "client_content_audits_required": True,
        "author_populated_artifact_build_required": True,
        "final_astra_xhigh_audit_required": True,
        "p0_g_closed": False,
        "p0_h_closed": False,
        "p0_i_closed": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }


def template_check() -> dict[str, Any]:
    owner = validate_owner(json.loads(OWNER_TEMPLATE.read_text(encoding="utf-8")), template_mode=True)
    cas = validate_cas(json.loads(CAS_TEMPLATE.read_text(encoding="utf-8")), check_template=True)
    release = validate_release(json.loads(RELEASE_TEMPLATE.read_text(encoding="utf-8")), check_template=True)
    manuscript_approval = validate_manuscript_approval(
        json.loads(MANUSCRIPT_APPROVAL_TEMPLATE.read_text(encoding="utf-8")),
        check_template=True,
    )
    passed = all(
        not item["validation_error_paths"]
        for item in (owner, cas, release, manuscript_approval)
    )
    return {
        "schema_version": 1,
        "decision": (
            "PASS_EXTERNAL_CLOSURE_TEMPLATES_AND_PRIVACY_BOUNDARY"
            if passed
            else "FAIL_EXTERNAL_CLOSURE_TEMPLATE_OR_PRIVACY_BOUNDARY"
        ),
        "templates": 4,
        "complete": False,
        "private_values_emitted": False,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-input", type=Path, default=OWNER_INPUT)
    parser.add_argument("--cas-input", type=Path, default=CAS_INPUT)
    parser.add_argument("--release-input", type=Path, default=RELEASE_INPUT)
    parser.add_argument("--manuscript-approval-input", type=Path, default=MANUSCRIPT_APPROVAL_INPUT)
    parser.add_argument("--check-templates", action="store_true")
    args = parser.parse_args()
    if args.check_templates:
        result = template_check()
        TEMPLATE_RECEIPT.write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(json.dumps(result, indent=2))
        return 0 if result["decision"].startswith("PASS_") else 2

    paths = [args.owner_input, args.cas_input, args.release_input, args.manuscript_approval_input]
    paths = [path if path.is_absolute() else ROOT / path for path in paths]
    values = [_read(path) for path in paths]
    result = evaluate(*(value for value, _ in values))
    result["input_file_states"] = {
        key: (state or "READ")
        for key, (_, state) in zip(
            (
                "owner_inputs",
                "institutional_cas_record",
                "institutional_release_record",
                "institutional_manuscript_approval_record",
            ),
            values,
        )
    }
    print(json.dumps(result, indent=2))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
