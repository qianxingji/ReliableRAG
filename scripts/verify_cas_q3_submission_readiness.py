#!/usr/bin/env python3
"""Fail-closed CAS Q3 submission-readiness gate over public audit metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from verify_cas_q3_owner_inputs import validate as validate_owner_inputs


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "cas_q3" / "EVIDENCE_INDEX.json"
RECEIPT = ROOT / "docs" / "cas_q3" / "SUBMISSION_READINESS_VERIFICATION.json"
OWNER_INPUTS_LOCAL = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def owner_input_state() -> dict[str, object]:
    """Return only non-sensitive intake status; never echo supplied values."""
    if not OWNER_INPUTS_LOCAL.is_file():
        return {
            "decision": "FAIL_CLOSED_OWNER_INPUT_FILE_MISSING",
            "complete": False,
            "missing_field_count": 1,
            "validation_error_count": 0,
        }
    try:
        data = json.loads(OWNER_INPUTS_LOCAL.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "decision": "FAIL_CLOSED_OWNER_INPUT_JSON_UNREADABLE",
            "complete": False,
            "missing_field_count": 0,
            "validation_error_count": 1,
        }
    result = validate_owner_inputs(data)
    return {
        "decision": result["decision"],
        "complete": result["complete"],
        "missing_field_count": len(result["missing_field_paths"]),
        "validation_error_count": len(result["validation_error_paths"]),
    }


def main() -> int:
    evidence = json.loads(INDEX.read_text(encoding="utf-8"))
    checks: list[str] = []

    require(evidence["schema_version"] == 1, "evidence-index schema is supported", checks)
    require(evidence["cas_q3_status"] == "NOT READY", "current CAS Q3 status remains fail-closed", checks)
    require(
        evidence["route_decision"] == "PROCEED_Q3_QWEN_ONLY_EVIDENCE_AND_JOURNAL_FIT_GATE_NO_NEW_EXPERIMENTS",
        "frozen Qwen-only Q3 route is retained",
        checks,
    )
    require(evidence["accepted_reader_conditions"] == ["QWEN"], "only Qwen is accepted", checks)
    require(evidence["primary_policy"] == "HGB_GBV_R", "focal empirical policy remains HGB_GBV_R", checks)
    require(evidence["current_candidate"] is None, "no novel top-level candidate is claimed", checks)
    require(
        evidence["primary_findings"] == {
            "HGB_GBV_R_minus_GBV_ONLY_R_joint_em_damage": "PASS",
            "HGB_GBV_R_minus_HGB_ONLY_R_joint_em_damage": "NOT_PASS",
            "ROA_FULL_minus_HGB_GBV_R_advancement": "REJECTED",
            "novel_top_level_method_cleared": False,
        },
        "complete positive and negative primary findings are retained",
        checks,
    )
    require(evidence["scientific_execution_authorized"] is False, "new scientific execution remains unauthorized", checks)
    require(evidence["terminal_exclusions"]["phi"]["scientific_effect_use"] is False, "failed Phi route remains excluded", checks)
    require(evidence["terminal_exclusions"]["mistral"]["model_execution_occurred"] is False, "stopped Mistral route remains unexecuted", checks)

    expected_p0 = {
        "p0_a_decision": "PASS_BOUNDED_EMPIRICAL_POSITIONING_METHOD_NOVELTY_REJECTED",
        "p0_b_decision": "PASS_COMPLETE_FROZEN_QWEN_RESULT_CLAIM_MAP",
        "p0_c_decision": "PASS_REVIEWER_READABLE_METHOD_AND_FAIRNESS_ACCOUNT",
        "p0_d_decision": "PASS_CAS_Q3_STATISTICAL_STATEMENT_VERIFICATION",
        "p0_e_decision": "PASS_FROZEN_Q3_DISCLOSURE_BOUNDARY",
        "p0_f_decision": "PASS_SHARED_STUDY_COST_WITH_EXPLICIT_MISSING_DEPLOYMENT_MEASUREMENTS",
    }
    for key, value in expected_p0.items():
        require(evidence.get(key) == value, f"{key} is closed with its exact bounded decision", checks)

    discover = json.loads(
        (ROOT / evidence["p0_i_discover_computing_preflight"]).read_text(encoding="utf-8")
    )
    require(
        discover["decision"]
        == "PASS_DISCOVER_COMPUTING_PROVISIONAL_TECHNICAL_PREFLIGHT_EXTERNAL_GATES_OPEN",
        "provisional Discover Computing technical preflight passes in bounded scope",
        checks,
    )
    require(discover["final_target_selected"] is False, "Discover Computing is not final-selected", checks)
    require(discover["submission_authorized"] is False, "provisional target profile is not submission-authorized", checks)
    require(
        discover["source_protection"]["scientific_prose_or_numbers_changed"] is False,
        "provisional target conversion preserves scientific content",
        checks,
    )
    apc = json.loads((ROOT / evidence["p0_h_discover_computing_apc_audit_receipt"]).read_text(encoding="utf-8"))
    require(
        apc["decision"] == "PASS_OFFICIAL_DISCOVER_COMPUTING_APC_FACTS_OWNER_ACCEPTANCE_PENDING",
        "official Discover Computing current APC facts are recorded",
        checks,
    )
    require(apc["owner_publication_charge_route_selected"] is False, "owner publication-charge route remains open", checks)
    require(apc["submission_authorized"] is False, "APC audit does not authorize submission", checks)
    data_code = json.loads((ROOT / evidence["p0_g_discover_data_code_policy_audit_receipt"]).read_text(encoding="utf-8"))
    require(
        data_code["decision"] == "PASS_OFFICIAL_DISCOVER_DATA_CODE_POLICY_MAPPED_IMPLEMENTATION_GATES_OPEN",
        "official Discover data/code policy is mapped",
        checks,
    )
    require(
        data_code["current_project_evidence"]["top_level_project_license_present"] is False,
        "policy mapping retains the missing project-license gate",
        checks,
    )
    require(
        data_code["current_project_evidence"]["persistent_archive_doi_or_unique_identifier_exists"] is False,
        "policy mapping retains the missing persistent-archive gate",
        checks,
    )

    require(len(evidence["completed_p0"]) == 6, "exactly P0-A through P0-F are fully closed", checks)
    require(len(evidence["completed_p1"]) == 4, "P1-A through P1-D are closed", checks)

    # Verify every repository path that has an adjacent SHA-256 field. External
    # receipt hashes without a repository path are deliberately outside scope.
    verified_hashes: list[str] = []
    for key, expected_hash in sorted(evidence.items()):
        if not key.endswith("_sha256") or not isinstance(expected_hash, str):
            continue
        path_key = key.removesuffix("_sha256")
        relative = evidence.get(path_key)
        if not isinstance(relative, str):
            continue
        path = ROOT / relative
        require(path.is_file(), f"pinned file exists: {relative}", checks)
        require(sha(path) == expected_hash, f"pinned hash matches: {relative}", checks)
        verified_hashes.append(relative)

    blockers = [
        {
            "gate": "P0-G",
            "status": "OPEN",
            "missing": [
                "owner-selected project license",
                "exact legal copyright holder and year/range",
                "institutional NOTICE or release-review decision",
                "selected journal data/code release policy",
                "license-bearing latest code link and immutable archive DOI or unique identifier",
                "journal-approved review access for restricted evidence",
                "new licensed release archive and independent validation",
            ],
        },
        {
            "gate": "P0-H",
            "status": "OPEN",
            "missing": [
                "institution-recognized CAS edition/year and category rule",
                "verified current journal title and ISSNs under that rule",
                "title/ISSN-change and recognition-date treatment",
                "final target journal and owner-confirmed payer, agreement, waiver or no-mandatory-APC route",
            ],
        },
        {
            "gate": "P0-I",
            "status": "OPEN",
            "missing": [
                "real authorship, affiliations and corresponding-author fields",
                "CRediT, funding, interests, ethics, acknowledgements and AI-assistance declarations",
                "originality, exclusive-submission and all-author approval",
                "target-specific source/PDF/package conversion and verification",
                "final GPT-6 Astra xhigh fairness, claim, reviewer and Submission Ready audit",
            ],
        },
    ]
    require(evidence["p0_g_distribution_authorized"] is False, "P0-G distribution remains withheld", checks)
    require(evidence["p0_g_project_license"] == "PENDING_OWNER_SELECTION", "P0-G license remains pending", checks)
    require(evidence["p0_h_decision"] == "PENDING_OWNER_AND_INSTITUTION_NO_JOURNAL_CERTIFIED", "P0-H remains uncertified", checks)
    require(evidence["p0_i_author_inputs_status"] == "PENDING_RESPONSIBLE_AUTHOR_NO_FACTS_GUESSED", "P0-I author facts remain pending", checks)
    intake = owner_input_state()
    require(
        intake["decision"] in {
            "FAIL_CLOSED_OWNER_INPUT_FILE_MISSING",
            "FAIL_CLOSED_OWNER_INPUT_JSON_UNREADABLE",
            "FAIL_CLOSED_OWNER_INPUTS_INCOMPLETE_OR_INVALID",
            "PASS_OWNER_INPUTS_COMPLETE_PENDING_INDEPENDENT_EVIDENCE_AND_ARTIFACT_GATES",
        },
        "local owner-input state is recognized without exposing supplied values",
        checks,
    )
    require(
        evidence["missing_p0"] == [
            "P0_G_owner_selected_project_license_and_target_journal_release_policy",
            "P0_H_verified_target_journal_and_applicable_cas_q3_rule",
            "P0_I_author_identity_declarations_and_target_specific_submission_package",
        ],
        "machine-readable missing-P0 list is complete",
        checks,
    )

    result = {
        "schema_version": 1,
        "decision": "FAIL_CLOSED_CAS_Q3_NOT_READY_EXTERNAL_OWNER_INSTITUTION_AUTHOR_GATES",
        "cas_q3_status": "NOT_READY",
        "submission_ready": False,
        "closed_p0": ["P0-A", "P0-B", "P0-C", "P0-D", "P0-E", "P0-F"],
        "open_p0": ["P0-G", "P0-H", "P0-I"],
        "closed_p1": ["P1-A", "P1-B", "P1-C", "P1-D"],
        "p2_status": "FROZEN_NO_NEW_EXPERIMENTS_OR_METHOD_SEARCH",
        "blockers": blockers,
        "owner_input_intake": intake,
        "verified_repository_hashes": len(verified_hashes),
        "checks": len(checks),
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
    }
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
