#!/usr/bin/env python3
"""Fail-closed CAS Q3 submission-readiness gate over public audit metadata."""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ignore-local-owner-inputs",
        action="store_true",
        help="Produce the deterministic public-checkout receipt without reading the git-ignored owner file.",
    )
    args = parser.parse_args()
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

    manifest_recovery = json.loads(
        (ROOT / evidence["p0_e_historical_manifest_archive_recovery_receipt"]).read_text(encoding="utf-8")
    )
    require(
        manifest_recovery["decision"]
        == "PARTIAL_PASS_LOCALLY_PRESERVED_MARS_MANIFEST_BYTE_COPY_RECOVERED_NO_INDEPENDENT_TIMESTAMP_OR_FIT_RECEIPTS",
        "historical manifest recovery keeps its bounded partial-pass decision",
        checks,
    )
    require(
        manifest_recovery["current_manifest"]["byte_identical_to_embedded_manifest"] is True,
        "locally preserved dated/named package manifest is byte-identical to the current copy",
        checks,
    )
    require(
        manifest_recovery["evidence_interpretation"]["independent_pre_roa_timestamp_proved"] is False,
        "historical manifest recovery does not claim an independent timestamp",
        checks,
    )
    require(
        manifest_recovery["evidence_interpretation"]["independent_original_fit_witness_recovered"] is False,
        "historical manifest recovery does not claim an original-fit witness",
        checks,
    )
    manifest_verification = json.loads(
        (ROOT / evidence["p0_e_historical_manifest_archive_recovery_verification"]).read_text(encoding="utf-8")
    )
    require(
        manifest_verification["decision"] == "PASS_BOUNDED_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_VERIFICATION",
        "historical manifest recovery verifier passes",
        checks,
    )
    require(manifest_verification["checks"] == 30, "historical manifest recovery verifier runs 30 checks", checks)
    require(
        manifest_recovery["evidence_interpretation"]["seven_per_estimator_fit_time_id_receipts_recovered"] is False
        and manifest_recovery["evidence_interpretation"]["seven_per_estimator_fit_time_matrix_receipts_recovered"] is False,
        "historical fit receipts remain missing",
        checks,
    )
    require(
        manifest_verification["full_historical_content_search_reperformed"] is False,
        "bounded verifier does not claim an exhaustive historical-content search",
        checks,
    )
    require(manifest_verification["scientific_payloads_read"] is False, "historical manifest verification reads no scientific payload", checks)

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
        "historical Discover policy mapping retains its pre-license state",
        checks,
    )
    require(
        data_code["current_project_evidence"]["persistent_archive_doi_or_unique_identifier_exists"] is False,
        "policy mapping retains the missing persistent-archive gate",
        checks,
    )
    third_party = json.loads((ROOT / evidence["p0_g_third_party_terms_recheck_receipt"]).read_text(encoding="utf-8"))
    require(
        third_party["decision"]
        == "PASS_THIRD_PARTY_TERMS_RECHECK_RELEASE_SOURCE_CORRECTED_CURRENT_ARCHIVE_WITHHELD",
        "third-party terms recheck is bound",
        checks,
    )
    require(third_party["distribution_authorized"] is False, "third-party recheck preserves distribution block", checks)
    require(third_party["current_archive"]["release_ready"] is False, "current aggregate archive remains non-release-ready", checks)
    require(third_party["source_correction"]["future_archive_rebuild_required"] is True, "corrected notice requires a future archive", checks)

    target = json.loads(
        (ROOT / evidence["p0_h_applied_intelligence_target_selection_receipt"]).read_text(encoding="utf-8")
    )
    require(
        target["decision"]
        == "PARTIAL_PASS_OWNER_SELECTED_APPLIED_INTELLIGENCE_OFFICIAL_PROFILE_VERIFIED_CAS_DOCUMENT_AND_TARGET_PACKAGE_OPEN",
        "owner-selected Applied Intelligence profile is bound",
        checks,
    )
    require(target["owner_selected_target"] is True, "Applied Intelligence is the working target", checks)
    require(target["journal"]["print_issn"] == "0924-669X", "Applied Intelligence print ISSN", checks)
    require(target["journal"]["electronic_issn"] == "1573-7497", "Applied Intelligence electronic ISSN", checks)
    require(
        target["owner_cas_rule"]["category_basis"] == "MAJOR"
        and target["owner_cas_rule"]["category_name"] == "Computer Science",
        "owner-selected major-category CAS rule",
        checks,
    )
    require(
        target["owner_cas_rule"]["independent_institutional_record_retained"] is False,
        "institutional CAS record remains open",
        checks,
    )
    require(
        target["publication_route"]["owner_selected"] == "SUBSCRIPTION_NON_OPEN_ACCESS"
        and target["publication_route"]["mandatory_apc_under_selected_route"] is False,
        "owner-selected no-mandatory-APC subscription route",
        checks,
    )
    require(target["submission_authorized"] is False, "target selection does not authorize submission", checks)

    applied_policy = json.loads(
        (ROOT / evidence["p0_g_applied_intelligence_data_code_policy_receipt"]).read_text(encoding="utf-8")
    )
    require(
        applied_policy["decision"]
        == "PASS_OFFICIAL_APPLIED_INTELLIGENCE_POLICY_MAPPED_RELEASE_AND_REVIEW_ACCESS_GATES_OPEN",
        "Applied Intelligence data/code policy is mapped",
        checks,
    )
    require(applied_policy["current_project"]["top_level_license"] == "Apache-2.0", "owner-selected Apache license", checks)
    require(
        applied_policy["current_project"]["existing_aggregate_archive_release_ready"] is False,
        "pre-license aggregate archive remains withheld",
        checks,
    )
    require(applied_policy["current_project"]["new_corrected_candidate_built"] is True, "corrected V2 candidate is built", checks)
    require(
        applied_policy["current_project"]["new_corrected_candidate_deterministic_rebuild_equal"] is True,
        "corrected V2 candidate rebuild is deterministic",
        checks,
    )
    require(
        applied_policy["current_project"]["new_corrected_candidate_independently_validated"] is True,
        "corrected V2 candidate is independently validated",
        checks,
    )
    require(
        applied_policy["current_project"]["new_corrected_candidate_distribution_authorized"] is False,
        "corrected V2 candidate remains withheld",
        checks,
    )
    require(applied_policy["distribution_authorized"] is False, "Applied policy audit does not authorize distribution", checks)

    licensed_release = json.loads((ROOT / evidence["p0_g_licensed_release_v2_receipt"]).read_text(encoding="utf-8"))
    require(
        licensed_release["decision"]
        == "PARTIAL_PASS_APACHE2_AWARE_CORRECTED_AGGREGATE_V2_BUILT_AND_VALIDATED_DISTRIBUTION_WITHHELD",
        "Apache-aware V2 release candidate has a bounded partial pass",
        checks,
    )
    require(licensed_release["v2"]["deterministic_rebuild_equal"] is True, "V2 release rebuilds byte-identically", checks)
    require(licensed_release["v2"]["both_archives_independently_validated"] is True, "both V2 builds validate", checks)
    require(licensed_release["v2"]["validator_checks_each"] == 125, "V2 archive validator runs 125 checks", checks)
    require(licensed_release["v2"]["roundtrip_verifier_checks"] == 129, "V2 extracted reporting verifier runs 129 checks", checks)
    require(licensed_release["license"]["project_code_license"] == "Apache-2.0", "V2 carries Apache-2.0 for project code", checks)
    require(licensed_release["license"]["non_code_members_relicensed"] is False, "V2 does not relicense non-code members", checks)
    require(licensed_release["distribution_authorized"] is False, "V2 release remains distribution-withheld", checks)

    modern_preflight = json.loads(
        (ROOT / evidence["p0_i_applied_intelligence_modern_preflight"]).read_text(encoding="utf-8")
    )
    require(
        modern_preflight["decision"]
        == "PARTIAL_PASS_APPLIED_INTELLIGENCE_MODERN_SN_JNL_PREFLIGHT_SMALLCONDENSED_EQUIVALENCE_OPEN",
        "modern Applied Intelligence preflight is bound",
        checks,
    )
    require(modern_preflight["artifacts"]["pdf_pages"] == 12, "modern Applied Intelligence PDF is complete", checks)
    require(modern_preflight["profile"]["abstract_words"] == 155, "target preflight abstract count", checks)
    require(modern_preflight["profile"]["keywords"] == 5, "target preflight keyword count", checks)
    require(modern_preflight["profile"]["smallcondensed_profile_used"] is False, "smallcondensed remains unresolved", checks)
    require(
        modern_preflight["profile"]["sn_jnl_equivalent_to_journal_smallcondensed_proved"] is False,
        "sn-jnl equivalence is not overclaimed",
        checks,
    )
    require(modern_preflight["submission_authorized"] is False, "modern preflight does not authorize submission", checks)
    modern_verification = json.loads(
        (ROOT / evidence["p0_i_applied_intelligence_modern_preflight_verification"]).read_text(encoding="utf-8")
    )
    require(
        modern_verification["decision"]
        == "PASS_COMMITTED_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_WITH_TEMPLATE_EQUIVALENCE_OPEN",
        "committed modern target preflight verifies",
        checks,
    )
    target_transport = json.loads(
        (ROOT / evidence["p0_i_applied_intelligence_template_transport_results"]).read_text(encoding="utf-8")
    )
    require(
        target_transport["decision"]
        == "PARTIAL_PASS_OFFICIAL_SN_JNL_ALLOWED_COMPLETE_PRIVATE_TRANSPORT_VALIDATED_SMALLCONDENSED_LEGACY_CONFLICT_RETAINED",
        "private complete-source target transport has a bounded partial pass",
        checks,
    )
    transport = target_transport["private_complete_source_transport"]
    require(transport["deterministic_rebuild_equal"] is True, "target transport rebuilds byte-identically", checks)
    require(transport["both_builds_independently_validated"] is True, "both target transport builds validate", checks)
    require(transport["validator_checks_each"] == 56, "target transport validator runs 56 checks", checks)
    require(transport["clean_compile_pages"] == 12, "target transport clean-compiles to 12 pages", checks)
    require(
        transport["clean_compile_pdf_sha256"] == modern_preflight["artifacts"]["pdf_sha256"],
        "target transport clean compile matches the visually accepted PDF bytes",
        checks,
    )
    require(
        target_transport["official_source_findings"][
            "journal_specific_equivalence_from_sn_jnl_to_smallcondensed_proved"
        ]
        is False,
        "journal-specific legacy-template equivalence remains open",
        checks,
    )
    require(target_transport["submission_authorized"] is False, "target transport does not authorize submission", checks)
    require(target_transport["distribution_authorized"] is False, "target transport remains distribution-withheld", checks)

    target_packet = (ROOT / evidence["p0_h_target_journal_decision_packet"]).read_text(encoding="utf-8")
    require(
        "PARTIAL_PASS_OWNER_SELECTED_APPLIED_INTELLIGENCE_INSTITUTIONAL_CAS_RECORD_PENDING" in target_packet,
        "current target packet binds the owner-selected Applied Intelligence route",
        checks,
    )
    require("current print ISSN: `0924-669X`" in target_packet, "current target packet binds print ISSN", checks)
    require(
        "current electronic ISSN: `1573-7497`" in target_packet,
        "current target packet binds electronic ISSN",
        checks,
    )
    require(
        "DISCOVER COMPUTING REMAINS THE CONDITIONAL EDITORIAL-FIT LEAD" not in target_packet,
        "stale provisional target is excluded from the current packet",
        checks,
    )

    hbut_affiliation = json.loads(
        (ROOT / evidence["p0_i_hbut_affiliation_address_verification"]).read_text(encoding="utf-8")
    )
    require(
        hbut_affiliation["decision"]
        == "PASS_OFFICIAL_HBUT_INSTITUTION_CITY_POSTCODE_VERIFIED_DEPARTMENT_PENDING",
        "official HBUT affiliation-address verification is bound",
        checks,
    )
    require(hbut_affiliation["institution"] == "Hubei University of Technology", "HBUT institution name", checks)
    require(hbut_affiliation["verified_affiliation_fields"]["city"] == "Wuhan", "HBUT city", checks)
    require(hbut_affiliation["verified_affiliation_fields"]["postal_code"] == "430068", "HBUT postal code", checks)
    require(hbut_affiliation["department_verified"] is False, "author department remains uninferred", checks)
    require(hbut_affiliation["personal_values_emitted"] is False, "affiliation audit emits no personal values", checks)

    private_builder = json.loads(
        (ROOT / evidence["p0_i_applied_intelligence_private_submission_builder_results"]).read_text(
            encoding="utf-8"
        )
    )
    require(
        private_builder["decision"]
        == "PASS_SYNTHETIC_COMPLETE_INPUT_TO_PRIVATE_APPLIED_INTELLIGENCE_PACKAGE_PIPELINE_FINAL_FACTS_AND_AUDITS_OPEN",
        "private target-builder synthetic acceptance is bound",
        checks,
    )
    require(private_builder["input_scope"]["synthetic_complete_fixture_used"] is True, "synthetic builder input", checks)
    require(private_builder["input_scope"]["real_owner_input_used"] is False, "real owner input was not used", checks)
    require(private_builder["input_scope"]["real_owner_input_missing_fields"] == 30, "real owner input remains incomplete", checks)
    require(private_builder["synthetic_private_build"]["source_members"] == 10, "synthetic target source members", checks)
    require(private_builder["synthetic_private_build"]["compiled_pages"] == 13, "synthetic target PDF pages", checks)
    require(private_builder["synthetic_private_build"]["visual_defects"] == 0, "synthetic target visual review", checks)
    require(
        private_builder["fail_closed_properties"]["incomplete_input_rejected_before_transport_read"] is True,
        "private builder rejects incomplete input before private transport access",
        checks,
    )
    require(private_builder["final_astra_xhigh_audit_complete"] is False, "final Astra audit remains open", checks)
    require(private_builder["submission_authorized"] is False, "synthetic builder does not authorize submission", checks)

    require(len(evidence["completed_p0"]) == 6, "exactly P0-A through P0-F are fully closed", checks)
    require(len(evidence["completed_p1"]) == 5, "P1-A through P1-E are closed", checks)

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
                "exact legal copyright holder and year/range",
                "institutional NOTICE or release-review decision",
                "license-bearing latest code link and immutable archive DOI or unique identifier",
                "journal-approved review access for restricted evidence",
                "owner/institutional review of Qwen research-license compatibility for the intended release",
                "owner/institutional review of the non-c DeBERTa training-data terms for the intended release",
                "final authorization of the validated V2 archive or a required successor",
            ],
        },
        {
            "gate": "P0-H",
            "status": "OPEN",
            "missing": [
                "institution-recognized CAS edition/year",
                "retained institutional record for current Applied Intelligence title and ISSNs under the Computer Science major-category rule",
                "institutional title/ISSN-change treatment",
            ],
        },
        {
            "gate": "P0-I",
            "status": "OPEN",
            "missing": [
                "complete author publishing names, department/address and corresponding-author fields",
                "CRediT, funding, interests, ethics, acknowledgements and AI-assistance declarations",
                "originality, exclusive-submission and all-author approval",
                "author-populated final target package",
                "retained publisher or Editorial Manager acceptance of the modern sn-jnl route, or a working journal-specific legacy package",
                "final GPT-6 Astra xhigh fairness, claim, reviewer and Submission Ready audit",
            ],
        },
    ]
    require(evidence["p0_g_distribution_authorized"] is False, "P0-G distribution remains withheld", checks)
    require(evidence["p0_g_project_license"] == "Apache-2.0", "owner-selected project license is recorded", checks)
    require(
        evidence["p0_h_decision"]
        == "PARTIAL_PASS_OWNER_SELECTED_APPLIED_INTELLIGENCE_OFFICIAL_PROFILE_VERIFIED_CAS_DOCUMENT_AND_TARGET_PACKAGE_OPEN",
        "P0-H target is selected but institutional certification remains open",
        checks,
    )
    require(
        evidence["p0_i_author_inputs_status"] == "PARTIAL_OWNER_INPUTS_LOCAL_30_MISSING_ZERO_VALIDATION_ERRORS",
        "P0-I records partial owner facts without treating them as complete",
        checks,
    )
    intake = (
        {
            "decision": "FAIL_CLOSED_OWNER_INPUT_FILE_MISSING",
            "complete": False,
            "missing_field_count": 1,
            "validation_error_count": 0,
        }
        if args.ignore_local_owner_inputs
        else owner_input_state()
    )
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
            "P0_G_release_authorization_and_persistent_archive",
            "P0_H_independent_institutional_cas_record_for_applied_intelligence",
            "P0_I_complete_author_declarations_and_applied_intelligence_package",
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
        "closed_p1": ["P1-A", "P1-B", "P1-C", "P1-D", "P1-E"],
        "p2_status": "FROZEN_NO_NEW_EXPERIMENTS_OR_METHOD_SEARCH",
        "blockers": blockers,
        "owner_input_intake": intake,
        "owner_input_intake_scope": (
            "PUBLIC_CHECKOUT_LOCAL_FILE_INTENTIONALLY_EXCLUDED"
            if args.ignore_local_owner_inputs
            else "LOCAL_GIT_IGNORED_FILE_IF_PRESENT"
        ),
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
