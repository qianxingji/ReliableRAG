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

    receipt_census = json.loads(
        (ROOT / evidence["p0_e_original_fit_receipt_census"]).read_text(encoding="utf-8")
    )
    require(
        receipt_census["decision"] == "PASS_BOUNDED_ACCESSIBLE_HISTORICAL_RECEIPT_CENSUS_NO_RECOVERY",
        "bounded original-fit receipt census is recorded",
        checks,
    )
    require(
        receipt_census["counts"]
        == {
            "filesystem_files_scanned": 55373,
            "candidate_text_files_scanned": 1770,
            "zip_archives_scanned": 37,
            "exact_original_model_hash_copies": 14,
            "candidate_files_with_receipt_markers_and_model_identity": 0,
            "candidate_archive_members_with_receipt_markers_and_model_identity": 0,
            "scan_errors": 0,
        },
        "bounded receipt census counts are exact",
        checks,
    )
    require(
        sorted(receipt_census["exact_models_by_root"]) == ["original_workspace", "static_original"]
        and all(len(models) == 7 for models in receipt_census["exact_models_by_root"].values()),
        "only the original model set and its static-delivery copy are present",
        checks,
    )
    require(
        receipt_census["interpretation"]["third_independent_model_copy_found"] is False
        and receipt_census["interpretation"]["independent_original_fit_witness_recovered"] is False
        and receipt_census["interpretation"]["p0_1_authenticity_gap_closed"] is False,
        "receipt census does not close original-fit authenticity",
        checks,
    )
    require(
        receipt_census["interpretation"]["absence_outside_scanned_roots_proved"] is False
        and receipt_census["interpretation"]["filesystem_or_zip_timestamps_are_independent_certification"] is False,
        "receipt census preserves scope and timestamp limits",
        checks,
    )
    require(
        receipt_census["operations"]["model_deserialization"] is False
        and receipt_census["operations"]["model_forwards"] == 0
        and receipt_census["operations"]["scientific_fits"] == 0,
        "receipt census performs no model execution",
        checks,
    )

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

    hbut_cas = json.loads((ROOT / evidence["p0_h_hbut_cas_policy_verification"]).read_text(encoding="utf-8"))
    require(
        hbut_cas["decision"]
        == "PARTIAL_PASS_OFFICIAL_HBUT_UPGRADED_CAS_BASIS_AND_REVIEW_OFFICE_VERIFIED_EDITION_AND_JOURNAL_RECORD_PENDING",
        "official HBUT CAS policy boundary is bound",
        checks,
    )
    require(hbut_cas["verified_scope"]["institution_uses_cas_upgraded_basis_for_sci_ssci"] is True, "HBUT uses upgraded CAS basis", checks)
    require(hbut_cas["verified_scope"]["hbut_first_affiliation_requirement"] is True, "HBUT first affiliation is required", checks)
    require(hbut_cas["verified_scope"]["institutional_review_route_identified"] is True, "HBUT review route is identified", checks)
    require(hbut_cas["verified_scope"]["institution_recognized_cas_edition_year"] is None, "HBUT CAS edition/year remains open", checks)
    require(hbut_cas["verified_scope"]["college_plan_previous_publication_year_rule_observed"] is True, "HBUT college previous-year rule is retained", checks)
    require(hbut_cas["verified_scope"]["candidate_report_year_if_formal_publication_in_2026"] == 2025, "candidate report year for 2026 publication", checks)
    require(hbut_cas["verified_scope"]["candidate_year_rule_confirmed_university_wide"] is False, "candidate report-year rule remains centrally unconfirmed", checks)
    require(hbut_cas["verified_scope"]["applied_intelligence_current_title_issns_major_category_q3_record_retained"] is False, "Applied Intelligence institutional CAS record remains open", checks)
    require(hbut_cas["attachment_access"]["attachment_contents_inspected"] is False, "CAPTCHA-gated policy attachments were not inferred", checks)
    require(hbut_cas["p0_h_closed"] is False, "official HBUT policy evidence does not close P0-H", checks)
    require(hbut_cas["submission_authorized"] is False, "official HBUT policy evidence does not authorize submission", checks)

    hbut_request = json.loads((ROOT / evidence["p0_gh_hbut_institutional_request_receipt"]).read_text(encoding="utf-8"))
    require(hbut_request["decision"] == "PASS_CONCRETE_HBUT_INSTITUTIONAL_REQUEST_PREPARED_RESPONSE_PENDING", "HBUT institutional request is bound", checks)
    require(all(hbut_request["requested_evidence"].values()), "HBUT request covers the external evidence surface", checks)
    require(hbut_request["request_sent"] is False, "HBUT institutional request remains unsent", checks)
    require(hbut_request["institutional_response_received"] is False, "HBUT institutional response remains pending", checks)
    require(hbut_request["institutional_response_retained"] is False, "HBUT institutional response is not fabricated", checks)
    require(
        hbut_request["public_corroboration_context"]["public_2025_major_category_q3_supported"] is True
        and hbut_request["public_corroboration_context"]["public_2025_minor_category_q4_supported"] is True,
        "institutional request gives the major-Q3/minor-Q4 public context",
        checks,
    )
    require(
        hbut_request["public_corroboration_context"]["accepted_as_hbut_record"] is False,
        "institutional request does not elevate public corroboration",
        checks,
    )
    require(
        hbut_request["central_notice_attachments"]["count"] == 2
        and hbut_request["central_notice_attachments"]["download_requires_captcha"] is True,
        "institutional request retains the two-attachment CAPTCHA boundary",
        checks,
    )
    require(
        hbut_request["central_notice_attachments"]["contents_inspected"] is False
        and hbut_request["central_notice_attachments"]["contents_inferred"] is False,
        "institutional request does not infer unread attachment contents",
        checks,
    )
    require(
        hbut_request["private_response_import"]["unified_preflight_command"]
        == "python scripts/verify_cas_q3_external_closure_inputs.py",
        "institutional response is routed into the unified private preflight",
        checks,
    )
    require(
        hbut_request["private_response_import"]["client_content_audit_required_after_structural_pass"] is True,
        "institutional response still requires client content audit",
        checks,
    )
    require(hbut_request["p0_g_closed"] is False and hbut_request["p0_h_closed"] is False and hbut_request["p0_i_closed"] is False, "request does not close P0 gates", checks)
    require(hbut_request["submission_authorized"] is False, "request does not authorize submission", checks)

    hbut_secondary = json.loads(
        (ROOT / evidence["p0_h_hbut_cas_edition_secondary_evidence"]).read_text(encoding="utf-8")
    )
    require(
        hbut_secondary["decision"]
        == "PARTIAL_PASS_OFFICIAL_HBUT_COLLEGE_PREVIOUS_YEAR_CAS_RULE_FOUND_UNIVERSITY_WIDE_CONFIRMATION_PENDING",
        "HBUT secondary edition-rule evidence is bound",
        checks,
    )
    require(hbut_secondary["evidence_scope"]["previous_publication_year_rule_observed"] is True, "secondary previous-year rule is observed", checks)
    require(hbut_secondary["evidence_scope"]["central_research_administration_policy"] is False, "secondary source is not overclaimed as central policy", checks)
    require(hbut_secondary["evidence_scope"]["rule_proved_university_wide_for_faculty_research_recognition"] is False, "university-wide applicability remains open", checks)
    require(hbut_secondary["candidate_interpretation_requiring_confirmation"]["if_formal_publication_year_is_2026_candidate_cas_report_year"] == 2025, "candidate report year is retained", checks)
    require(hbut_secondary["candidate_interpretation_requiring_confirmation"]["confirmed_by_hbut_research_administration"] is False, "central year confirmation remains open", checks)
    require(hbut_secondary["authoritative_cas_platform"]["upgraded_2025_listed_as_available"] is True, "authoritative 2025 upgraded data is available", checks)
    require(hbut_secondary["authoritative_cas_platform"]["journal_search_supports_title_and_issn"] is True, "authoritative title and ISSN query is supported", checks)
    require(hbut_secondary["authoritative_cas_platform"]["journal_partition_data_requires_institutional_or_authenticated_access"] is True, "authoritative platform access remains restricted", checks)
    require(hbut_secondary["authoritative_cas_platform"]["hbut_access_verified"] is False, "HBUT authoritative-platform access is not claimed", checks)
    require(hbut_secondary["authoritative_cas_platform"]["applied_intelligence_2025_record_retrieved"] is False, "Applied Intelligence authoritative record remains missing", checks)
    require(hbut_secondary["central_policy_attachment_access"]["contents_inspected"] is False, "CAPTCHA-gated central attachments remain uninspected", checks)
    require(hbut_secondary["central_policy_attachment_access"]["contents_inferred"] is False, "CAPTCHA-gated contents are not inferred", checks)
    require(hbut_secondary["p0_h_closed"] is False, "secondary evidence does not close P0-H", checks)

    public_corroboration = json.loads(
        (ROOT / evidence["p0_h_applied_intelligence_2025_public_corroboration"]).read_text(
            encoding="utf-8"
        )
    )
    require(
        public_corroboration["decision"]
        == "PARTIAL_PASS_PUBLIC_2025_MAJOR_Q3_CORROBORATION_INSTITUTIONAL_RECORD_STILL_REQUIRED",
        "public 2025 target corroboration is bounded",
        checks,
    )
    require(
        public_corroboration["owner_rule"]["category_basis"] == "MAJOR"
        and public_corroboration["owner_rule"]["category_name"] == "Computer Science",
        "public corroboration uses the owner's major-category rule",
        checks,
    )
    require(
        public_corroboration["bounded_interpretation"]["public_sources_support_2025_major_category_q3"] is True,
        "public sources support the 2025 major-Q3 interpretation",
        checks,
    )
    require(
        public_corroboration["bounded_interpretation"]["shufe_single_q4_label_proved_to_be_minor_category"] is False,
        "ambiguous Q4 source is not overinterpreted",
        checks,
    )
    require(
        public_corroboration["bounded_interpretation"]["institution_recognized_edition_year_confirmed"] is False
        and public_corroboration["bounded_interpretation"]["hbut_current_title_issn_record_retained"] is False,
        "public corroboration leaves the HBUT authority gates open",
        checks,
    )
    require(public_corroboration["bounded_interpretation"]["p0_h_closed"] is False, "public corroboration does not close P0-H", checks)
    corroboration_receipt = json.loads(
        (ROOT / evidence["p0_h_applied_intelligence_2025_public_corroboration_verification"]).read_text(
            encoding="utf-8"
        )
    )
    require(
        corroboration_receipt["decision"]
        == "PASS_BOUNDED_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION_VERIFICATION",
        "public corroboration verifier passes",
        checks,
    )
    require(corroboration_receipt["checks"] == 39, "public corroboration verifier runs 39 checks", checks)
    require(corroboration_receipt["institution_recognized_record_retained"] is False, "public verifier retains institutional gap", checks)

    owner_cas_path_check = json.loads(
        (ROOT / evidence["p0_h_owner_2025_cas_assertion_path_check"]).read_text(encoding="utf-8")
    )
    require(
        owner_cas_path_check["decision"]
        == "PARTIAL_PASS_OWNER_2025_MAJOR_Q3_ASSERTION_RECEIVED_DECLARED_EVIDENCE_PATH_MISSING",
        "owner CAS assertion path check is bounded",
        checks,
    )
    require(
        owner_cas_path_check["owner_assertion_received"] is True
        and owner_cas_path_check["candidate_edition_year"] == 2025
        and owner_cas_path_check["category_basis"] == "MAJOR"
        and owner_cas_path_check["asserted_tier"] == "Q3",
        "owner 2025 major-Q3 assertion is recorded",
        checks,
    )
    require(
        owner_cas_path_check["declared_path_exists_in_active_worktree"] is False
        and owner_cas_path_check["declared_path_exists_in_original_workspace"] is False,
        "declared CAS evidence path is absent from both workspaces",
        checks,
    )
    require(
        owner_cas_path_check["institutional_record_received"] is False
        and owner_cas_path_check["institutional_evidence_bytes_read"] == 0
        and owner_cas_path_check["p0_h_closed"] is False,
        "owner assertion does not manufacture institutional evidence",
        checks,
    )

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
    require(private_builder["input_scope"]["real_owner_input_missing_fields"] == 30, "historical real owner input snapshot remains incomplete", checks)
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

    route_resolution = json.loads(
        (ROOT / evidence["p0_i_applied_intelligence_template_route_resolution"]).read_text(
            encoding="utf-8"
        )
    )
    require(
        route_resolution["decision"]
        == "PASS_OFFICIAL_PUBLISHER_ACCEPTS_CURRENT_SN_JNL_SUBMISSION_ROUTE_SMALLCONDENSED_STYLE_EQUIVALENCE_UNPROVED",
        "official publisher template-route resolution is bound",
        checks,
    )
    require(
        route_resolution["resolution"]["publisher_acceptance_of_current_sn_jnl_submission_route_proved"] is True,
        "publisher accepts current sn-jnl submission route",
        checks,
    )
    require(
        route_resolution["resolution"]["journal_specific_smallcondensed_style_equivalence_proved"] is False,
        "smallcondensed style equivalence is not overclaimed",
        checks,
    )
    require(route_resolution["resolution"]["pre_submission_template_route_gate_closed"] is True, "pre-submission template route is closed", checks)
    require(route_resolution["resolution"]["submission_system_compile_observed"] is False, "submission-system compile remains unobserved", checks)
    require(route_resolution["resolution"]["author_populated_package_built"] is False, "author-populated package remains open", checks)
    require(route_resolution["scientific_payloads_read"] is False, "template-route audit reads no scientific payload", checks)
    require(route_resolution["model_forwards"] == 0 and route_resolution["scientific_fits"] == 0, "template-route audit executes no model work", checks)
    require(route_resolution["submission_authorized"] is False, "template-route audit does not authorize submission", checks)

    license_state = json.loads((ROOT / evidence["p0_g_license_state_verification"]).read_text(encoding="utf-8"))
    require(license_state["decision"] == "PASS_CURRENT_LICENSE_STATE_CONSISTENCY_WITH_EXTERNAL_GATES_OPEN", "current license state is bound", checks)
    require(license_state["checks"] == 26, "license-state verifier count", checks)
    require(license_state["project_code_license"] == "Apache-2.0", "project-authored code license is Apache-2.0", checks)
    require(license_state["legal_holder_confirmed"] is False, "legal copyright holder remains open", checks)
    require(license_state["copyright_year_confirmed"] is False, "copyright year remains open", checks)
    require(license_state["institutional_release_review_complete"] is False, "institutional release review remains open", checks)
    require(license_state["third_party_institutional_review_complete"] is False, "Qwen and DeBERTa institutional review remains open", checks)
    require(license_state["distribution_authorized"] is False, "license state does not authorize distribution", checks)

    release_record_intake = json.loads(
        (ROOT / evidence["p0_g_institutional_release_record_intake"]).read_text(encoding="utf-8")
    )
    require(
        release_record_intake["decision"]
        == "PASS_PRIVATE_RELEASE_RECORD_INTAKE_PREPARED_EXTERNAL_DECISIONS_MISSING",
        "institutional release-record intake is prepared",
        checks,
    )
    require(
        release_record_intake["bound_release_candidate"]["project_code_license"] == "Apache-2.0",
        "release-record intake binds the owner-selected project license",
        checks,
    )
    require(
        release_record_intake["bound_release_candidate"]["aggregate_v2_sha256"]
        == licensed_release["v2"]["archive_sha256"],
        "release-record intake binds the exact validated V2 candidate",
        checks,
    )
    require(
        release_record_intake["bound_release_candidate"]["model_weights_in_release"] is False
        and release_record_intake["bound_release_candidate"][
            "benchmark_payloads_answers_or_per_question_records_in_release"
        ]
        is False,
        "release-record intake preserves the no-weight and no-payload release scope",
        checks,
    )
    require(
        release_record_intake["privacy_boundary"]["local_metadata_git_ignored"] is True
        and release_record_intake["privacy_boundary"]["private_evidence_directory_git_ignored"] is True,
        "institutional release evidence remains outside Git",
        checks,
    )
    require(
        release_record_intake["current_state"]["release_record_received"] is False,
        "institutional release record remains missing",
        checks,
    )
    require(
        release_record_intake["current_state"]["content_independently_certified"] is False
        and release_record_intake["current_state"]["independent_client_content_audit_required"] is True,
        "institutional release-record content audit remains open",
        checks,
    )
    require(release_record_intake["current_state"]["p0_g_closed"] is False, "release intake does not close P0-G", checks)
    require(release_record_intake["distribution_authorized"] is False, "release intake does not authorize distribution", checks)

    external_closure = json.loads(
        (ROOT / evidence["p0_ghi_external_closure_preflight"]).read_text(encoding="utf-8")
    )
    require(
        external_closure["decision"]
        == "PASS_PRIVATE_EXTERNAL_CLOSURE_PREFLIGHT_PREPARED_REAL_INPUTS_AND_AUDITS_OPEN",
        "unified private external-closure preflight is prepared",
        checks,
    )
    require(len(external_closure["component_inputs"]) == 4, "unified preflight covers all four private inputs", checks)
    require(len(external_closure["cross_checks"]) == 9, "unified preflight documents cross-record consistency", checks)
    require(
        external_closure["privacy_boundary"]["private_inputs_git_ignored"] is True
        and external_closure["privacy_boundary"]["private_values_emitted"] is False,
        "unified preflight preserves private input boundary",
        checks,
    )
    require(
        external_closure["strongest_result_closes_p0_g"] is False
        and external_closure["strongest_result_closes_p0_h"] is False
        and external_closure["strongest_result_closes_p0_i"] is False,
        "structural external-input pass cannot close P0 gates",
        checks,
    )
    require(external_closure["client_content_audits_required"] is True, "client content audits remain mandatory", checks)
    require(external_closure["author_populated_artifact_build_required"] is True, "author-populated artifact remains mandatory", checks)
    require(external_closure["final_astra_xhigh_audit_required"] is True, "final Astra xhigh audit remains mandatory", checks)
    require(external_closure["submission_authorized"] is False, "unified preflight does not authorize submission", checks)
    local_closure = external_closure["local_workspace_execution"]
    require(
        local_closure["preparation_decision"]
        == "PASS_PRIVATE_CLOSURE_WORKSPACE_PREPARED_WITHOUT_OVERWRITE",
        "private closure workspace was prepared without overwrite",
        checks,
    )
    require(local_closure["owner_input_hash_unchanged"] is True, "owner input bytes were preserved", checks)
    require(
        local_closure["placeholder_files_are_institutional_records"] is False,
        "empty institutional placeholders are not treated as received records",
        checks,
    )
    require(
        local_closure["institutional_record_received"] is False
        and local_closure["institutional_release_record_received"] is False
        and local_closure["institutional_manuscript_approval_record_received"] is False,
        "institutional CAS, release and manuscript-approval records remain pending",
        checks,
    )
    local_validation = local_closure["validation"]
    require(local_validation["exit_code"] == 2, "local unified validation remains fail-closed", checks)
    require(
        local_validation["owner_inputs"] == {"missing_field_count": 6, "validation_error_count": 0},
        "owner-input local status is fixed without exposing values",
        checks,
    )
    require(
        local_validation["institutional_cas_record"]
        == {"missing_field_count": 22, "validation_error_count": 0, "evidence_bytes_read": 0},
        "empty institutional CAS placeholder is recorded exactly",
        checks,
    )
    require(
        local_validation["institutional_release_record"]
        == {"missing_field_count": 22, "validation_error_count": 5, "evidence_bytes_read": 0},
        "empty institutional release placeholder is recorded exactly",
        checks,
    )
    require(
        local_validation["institutional_manuscript_approval_record"]
        == {
            "missing_field_count": 17,
            "validation_error_count": 2,
            "evidence_bytes_read": 0,
            "manuscript_bytes_read": 0,
        },
        "empty institutional manuscript-approval placeholder is recorded exactly",
        checks,
    )
    require(local_validation["cross_consistency_error_count"] == 0, "placeholder run reports no cross inconsistency", checks)
    require(local_closure["private_values_emitted"] is False, "workspace preparation emits no private values", checks)
    require(
        evidence["p0_ghi_private_closure_workspace_preparation_decision"]
        == "PASS_PRIVATE_CLOSURE_WORKSPACE_PREPARED_WITHOUT_OVERWRITE",
        "evidence index records the no-overwrite workspace preparation",
        checks,
    )
    require(
        evidence["p0_ghi_private_closure_workspace_owner_bytes_preserved"] is True
        and evidence["p0_ghi_private_closure_workspace_private_values_emitted"] is False,
        "workspace preparation preserves owner bytes and privacy",
        checks,
    )
    require(
        evidence["p0_ghi_external_closure_current_cas_record_input"]
        == "READ_EMPTY_TEMPLATE_PLACEHOLDER"
        and evidence["p0_ghi_external_closure_current_release_record_input"]
        == "READ_EMPTY_TEMPLATE_PLACEHOLDER"
        and evidence["p0_ghi_external_closure_current_manuscript_approval_record_input"]
        == "READ_EMPTY_TEMPLATE_PLACEHOLDER",
        "institutional local files are explicitly classified as empty placeholders",
        checks,
    )
    require(
        evidence["p0_ghi_external_closure_current_owner_missing_fields"] == 6
        and evidence["p0_ghi_external_closure_current_owner_validation_errors"] == 0,
        "indexed owner component remains incomplete without validation errors",
        checks,
    )
    require(
        evidence["p0_ghi_external_closure_current_cas_record_missing_fields"] == 22
        and evidence["p0_ghi_external_closure_current_cas_record_validation_errors"] == 0
        and evidence["p0_ghi_external_closure_current_cas_record_evidence_bytes_read"] == 0,
        "indexed CAS placeholder state is exact",
        checks,
    )
    require(
        evidence["p0_ghi_external_closure_current_release_record_missing_fields"] == 22
        and evidence["p0_ghi_external_closure_current_release_record_validation_errors"] == 5
        and evidence["p0_ghi_external_closure_current_release_record_evidence_bytes_read"] == 0,
        "indexed release placeholder state is exact",
        checks,
    )
    require(
        evidence["p0_ghi_external_closure_current_manuscript_approval_record_missing_fields"] == 17
        and evidence["p0_ghi_external_closure_current_manuscript_approval_record_validation_errors"] == 2
        and evidence["p0_ghi_external_closure_current_manuscript_approval_record_evidence_bytes_read"] == 0
        and evidence["p0_ghi_external_closure_current_manuscript_approval_record_manuscript_bytes_read"] == 0,
        "indexed manuscript-approval placeholder state is exact",
        checks,
    )
    require(
        evidence["p0_ghi_external_closure_current_cross_consistency_errors"] == 0
        and evidence["p0_ghi_external_closure_current_exit_code"] == 2,
        "indexed unified local closure remains fail-closed",
        checks,
    )
    require(
        evidence["p0_ghi_external_closure_institutional_cas_record_received"] is False
        and evidence["p0_ghi_external_closure_institutional_release_record_received"] is False
        and evidence["p0_ghi_external_closure_institutional_manuscript_approval_record_received"] is False,
        "empty placeholders do not close any institutional record gate",
        checks,
    )
    external_closure_verification = json.loads(
        (ROOT / evidence["p0_ghi_external_closure_preflight_verification"]).read_text(encoding="utf-8")
    )
    require(
        external_closure_verification["decision"]
        == "PASS_EXTERNAL_CLOSURE_TEMPLATES_AND_PRIVACY_BOUNDARY",
        "unified external-closure templates verify",
        checks,
    )
    require(external_closure_verification["templates"] == 4, "four private templates are covered", checks)
    require(external_closure_verification["submission_authorized"] is False, "template check does not authorize submission", checks)

    external_evidence_census = json.loads(
        (ROOT / evidence["p0_ghi_accessible_external_evidence_census"]).read_text(encoding="utf-8")
    )
    require(
        external_evidence_census["decision"]
        == "REVIEW_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_CANDIDATES_OR_ERRORS",
        "raw external-evidence census preserves triage requirement",
        checks,
    )
    require(
        external_evidence_census["ordinary_text_files_scanned"] == 454115
        and external_evidence_census["zip_archives_scanned"] == 39
        and external_evidence_census["zip_text_members_scanned"] == 1448,
        "external-evidence census coverage is pinned",
        checks,
    )
    require(
        external_evidence_census["candidate_match_count"] == 3
        and external_evidence_census["scan_error_count"] == 0,
        "external-evidence census retains three triaged candidates and zero errors",
        checks,
    )
    require(
        external_evidence_census["bounded_interpretation"]["institutional_record_recovered"] is False
        and external_evidence_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"] is False,
        "external-evidence census remains a bounded negative result",
        checks,
    )
    require(
        external_evidence_census["submission_authorized"] is False,
        "external-evidence census does not authorize submission",
        checks,
    )
    external_evidence_triage = (
        ROOT / evidence["p0_ghi_accessible_external_evidence_census_acceptance"]
    ).read_text(encoding="utf-8")
    require(
        "PASS_BOUNDED_ACCESSIBLE_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_RECOVERY_AFTER_TRIAGE"
        in external_evidence_triage,
        "external-evidence candidate triage is retained",
        checks,
    )

    oversized_census = json.loads(
        (ROOT / evidence["p0_ghi_oversized_external_evidence_census"]).read_text(encoding="utf-8")
    )
    require(
        oversized_census["decision"]
        == "PASS_BOUNDED_OVERSIZED_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES",
        "oversized external-evidence census passes without candidates",
        checks,
    )
    require(
        oversized_census["ordinary_large_text_files_stream_scanned"] == 26
        and oversized_census["ordinary_large_text_bytes_scanned"] == 518683752
        and oversized_census["zip_large_text_members_stream_scanned"] == 12
        and oversized_census["zip_large_text_member_bytes_scanned"] == 970485466,
        "oversized external-evidence coverage is pinned",
        checks,
    )
    require(
        oversized_census["ordinary_too_large_text_files_skipped"] == 0
        and oversized_census["zip_too_large_text_members_skipped"] == 0
        and oversized_census["candidate_match_count"] == 0
        and oversized_census["scan_error_count"] == 0,
        "oversized external-evidence census retains zero skips, candidates and errors",
        checks,
    )
    require(
        oversized_census["bounded_interpretation"]["unsupported_binary_formats_covered"] is False
        and oversized_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"] is False,
        "oversized external-evidence result remains bounded",
        checks,
    )
    require(
        oversized_census["submission_authorized"] is False,
        "oversized external-evidence census does not authorize submission",
        checks,
    )

    pdf_census = json.loads(
        (ROOT / evidence["p0_ghi_pdf_external_evidence_census"]).read_text(encoding="utf-8")
    )
    require(
        pdf_census["decision"]
        == "PASS_BOUNDED_PDF_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES",
        "PDF external-evidence census passes without candidates",
        checks,
    )
    require(
        pdf_census["ordinary_pdfs_extracted"] == 100
        and pdf_census["ordinary_pdf_bytes_processed"] == 20267890
        and pdf_census["zip_pdf_members_extracted"] == 138
        and pdf_census["zip_pdf_member_bytes_processed"] == 22448146
        and pdf_census["extracted_text_bytes_scanned"] == 3448238,
        "PDF external-evidence coverage is pinned",
        checks,
    )
    require(
        pdf_census["ordinary_pdfs_skipped"] == 0
        and pdf_census["zip_pdf_members_skipped"] == 0
        and pdf_census["candidate_match_count"] == 0
        and pdf_census["scan_error_count"] == 0,
        "PDF external-evidence census retains zero skips, candidates and errors",
        checks,
    )
    require(
        pdf_census["unique_pdf_hashes"] == 35
        and pdf_census["unique_pdfs_with_zero_extracted_text"] == 0
        and pdf_census["unique_pdfs_with_fewer_than_20_nonwhitespace_text_bytes"] == 0,
        "all unique PDFs retain usable extracted text layers",
        checks,
    )
    require(
        pdf_census["unique_pdfs_attachment_inspected"] == 35
        and pdf_census["embedded_attachment_count"] == 0
        and pdf_census["temporary_attachment_inventory_files_removed"] is True
        and pdf_census["bounded_interpretation"]["embedded_attachment_inventory_complete"] is True,
        "PDF attachment inventory is complete with no retained temporary files",
        checks,
    )
    require(
        pdf_census["bounded_interpretation"]["pdf_image_ocr_performed"] is False
        and pdf_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"] is False,
        "PDF external-evidence result remains text-layer bounded",
        checks,
    )
    require(
        pdf_census["submission_authorized"] is False,
        "PDF external-evidence census does not authorize submission",
        checks,
    )

    document_inventory = json.loads(
        (ROOT / evidence["p0_ghi_document_container_inventory"]).read_text(encoding="utf-8")
    )
    require(
        document_inventory["decision"]
        == "PASS_BOUNDED_COMMON_DOCUMENT_CONTAINER_INVENTORY_PDF_ONLY",
        "common document-container inventory passes",
        checks,
    )
    require(
        document_inventory["ordinary_file_counts"][".pdf"] == 100
        and document_inventory["zip_member_counts"][".pdf"] == 138
        and document_inventory["non_pdf_document_count"] == 0
        and document_inventory["scan_error_count"] == 0,
        "common document-container inventory coverage is pinned",
        checks,
    )
    require(
        document_inventory["file_contents_read"] is False
        and document_inventory["bounded_interpretation"]["files_with_incorrect_or_missing_extensions_covered"] is False
        and document_inventory["bounded_interpretation"]["unknown_binary_formats_covered"] is False,
        "common document-container inventory remains metadata and extension bounded",
        checks,
    )
    require(
        document_inventory["submission_authorized"] is False,
        "common document-container inventory does not authorize submission",
        checks,
    )

    recursive_archive_census = json.loads(
        (ROOT / evidence["p0_ghi_recursive_archive_closure_evidence"]).read_text(encoding="utf-8")
    )
    require(
        recursive_archive_census["decision"]
        == "PASS_BOUNDED_FIRST_LEVEL_NESTED_ARCHIVE_CENSUS_NO_RECOVERY",
        "first-level nested-archive census passes without recovery",
        checks,
    )
    require(
        recursive_archive_census["top_level_zip_archives_scanned"] == 39
        and recursive_archive_census["nested_archives_seen"] == 4
        and recursive_archive_census["nested_archives_materialized"] == 4
        and recursive_archive_census["nested_archive_bytes_materialized"] == 269975228,
        "nested-archive discovery and materialization coverage is pinned",
        checks,
    )
    require(
        recursive_archive_census["nested_archives_skipped"] == 0
        and recursive_archive_census["nested_member_count"] == 301
        and recursive_archive_census["deeper_archives_seen"] == 0,
        "all first-level nested archives are covered without deeper nesting",
        checks,
    )
    require(
        recursive_archive_census["text_members_seen"] == 234
        and recursive_archive_census["text_members_scanned"] == 234
        and recursive_archive_census["text_bytes_scanned"] == 858962287
        and recursive_archive_census["text_members_skipped"] == 0,
        "nested text coverage is pinned without skips",
        checks,
    )
    require(
        recursive_archive_census["text_candidate_match_count"] == 0
        and recursive_archive_census["strict_magic_counts"] == {"pdf": 32}
        and recursive_archive_census["strict_magic_suffix_mismatch_count"] == 0,
        "nested text and strict-header passes retain no candidate or mismatch",
        checks,
    )
    require(
        recursive_archive_census["pdf_audit"]["zip_pdf_members_extracted"] == 32
        and recursive_archive_census["pdf_audit"]["unique_pdf_hashes"] == 14
        and recursive_archive_census["pdf_audit"]["extracted_text_bytes_scanned"] == 323181
        and recursive_archive_census["pdf_audit"]["embedded_attachment_count"] == 0,
        "nested PDF text and attachment coverage is pinned",
        checks,
    )
    require(
        recursive_archive_census["candidate_match_count"] == 0
        and recursive_archive_census["scan_error_count"] == 0
        and recursive_archive_census["temporary_files_removed"] is True
        and recursive_archive_census["archive_trees_extracted"] is False,
        "nested archive audit retains zero candidates/errors and removes temporary files",
        checks,
    )
    require(
        recursive_archive_census["bounded_interpretation"]["pdf_image_ocr_performed"] is False
        and recursive_archive_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"] is False
        and recursive_archive_census["submission_authorized"] is False,
        "nested archive result remains bounded and non-authorizing",
        checks,
    )

    ordinary_magic = json.loads(
        (ROOT / evidence["p0_ghi_ordinary_document_magic"]).read_text(encoding="utf-8")
    )
    require(
        ordinary_magic["decision"] == "PASS_BOUNDED_ORDINARY_DOCUMENT_MAGIC_MATCHES_EXTENSIONS",
        "ordinary-file document-magic census passes",
        checks,
    )
    require(
        ordinary_magic["roots_scanned"] == 3
        and ordinary_magic["ordinary_files_seen"] == 465460
        and ordinary_magic["header_bytes_per_file"] == 4096
        and ordinary_magic["header_bytes_read"] == 631242643,
        "ordinary-file header coverage is pinned",
        checks,
    )
    require(
        ordinary_magic["strict_magic_counts"] == {"zip": 39, "pdf": 100}
        and ordinary_magic["strict_magic_suffix_counts"]["zip"] == {".zip": 39}
        and ordinary_magic["strict_magic_suffix_counts"]["pdf"] == {".pdf": 100}
        and sum(ordinary_magic["zip_document_family_counts"].values()) == 0,
        "ordinary strict document signatures match extensions without OOXML/ODF",
        checks,
    )
    require(
        ordinary_magic["loose_pdf_marker_non_header_count"] == 3
        and ordinary_magic["loose_pdf_marker_non_header_suffix_counts"] == {".js": 2, ".ts": 1},
        "ordinary loose PDF markers remain identified as source-code literals",
        checks,
    )
    require(
        ordinary_magic["document_magic_suffix_mismatch_count"] == 0
        and ordinary_magic["scan_error_count"] == 0,
        "ordinary document-magic census retains no mismatch or error",
        checks,
    )
    require(
        ordinary_magic["bounded_interpretation"]["common_pdf_rtf_ole_zip_document_magic_covered"] is True
        and ordinary_magic["bounded_interpretation"]["unknown_binary_formats_covered"] is False
        and ordinary_magic["bounded_interpretation"]["absence_outside_scanned_roots_proved"] is False
        and ordinary_magic["submission_authorized"] is False,
        "ordinary document-magic result remains bounded and non-authorizing",
        checks,
    )

    reply_receipt = json.loads(
        (ROOT / evidence["p0_i_owner_reply_packet_verification"]).read_text(encoding="utf-8")
    )
    require(
        reply_receipt["decision"]
        == "PASS_PRIVACY_SAFE_ONE_REPLY_PACKET_GENERATED_OWNER_CONFIRMATION_PENDING",
        "privacy-safe owner reply packet is bound",
        checks,
    )
    require(reply_receipt["missing_field_count"] == 6, "owner reply packet records 6 missing fields", checks)
    require(reply_receipt["validation_error_count"] == 0, "owner reply packet records zero validation errors", checks)
    require(
        set(reply_receipt["missing_field_paths"])
        == {
            "declarations.ai_assistance_statement_approved=true",
            "declarations.ai_tool_version_and_use_dates",
            "declarations.competing_interests_statement",
            "declarations.institutional_manuscript_approval_evidence",
            "declarations.institutional_manuscript_approval_status=APPROVED",
            "project_license.release_review_status=APPROVED",
        },
        "owner reply packet records the exact current deficit",
        checks,
    )
    for resolved_path in (
        "authorship.affiliations[0].department",
        "authorship.corresponding_author_name",
        "authorship.corresponding_author_email",
    ):
        require(
            resolved_path not in reply_receipt["missing_field_paths"],
            f"owner-supplied field no longer requested: {resolved_path}",
            checks,
        )
    require(reply_receipt["personal_values_emitted"] is False, "owner reply packet emits no personal values", checks)
    require(reply_receipt["submission_authorized"] is False, "owner reply packet does not authorize submission", checks)

    current_build_gate = json.loads(
        (ROOT / evidence["p0_i_current_private_build_gate_verification"]).read_text(encoding="utf-8")
    )
    require(
        current_build_gate["decision"]
        == "PASS_OWNER_INPUT_GATE_REJECTS_BEFORE_TRANSPORT_OR_OUTPUT",
        "current private owner input is rejected before transport or output",
        checks,
    )
    require(
        current_build_gate["input_scope"] == "LOCAL_GIT_IGNORED_OWNER_INPUT"
        and current_build_gate["input_matches_empty_template"] is False,
        "current build gate exercised the nonempty private owner input",
        checks,
    )
    require(
        current_build_gate["missing_field_count"] == 6
        and current_build_gate["validation_error_count"] == 0,
        "current build gate retains the exact owner-input deficit",
        checks,
    )
    require(
        current_build_gate["transport_access_attempted"] is False
        and current_build_gate["output_created"] is False,
        "current build gate stops before transport access and output creation",
        checks,
    )
    require(
        current_build_gate["author_populated_package_built"] is False
        and current_build_gate["private_values_emitted"] is False
        and current_build_gate["private_input_hash_emitted"] is False,
        "current build gate creates no package and emits no private material",
        checks,
    )
    require(current_build_gate["submission_authorized"] is False, "current build gate does not authorize submission", checks)
    require(
        evidence["private_submission_current_decision"]
        == "FAIL_CLOSED_OWNER_INPUTS_INCOMPLETE_OR_INVALID",
        "evidence index records the current real private-builder gate",
        checks,
    )
    require(
        evidence["p0_i_current_private_build_gate_missing_fields"] == 6
        and evidence["p0_i_current_private_build_gate_validation_errors"] == 0
        and evidence["p0_i_current_private_build_gate_input_matches_empty_template"] is False
        and evidence["p0_i_current_private_build_gate_transport_access_attempted"] is False
        and evidence["p0_i_current_private_build_gate_output_created"] is False
        and evidence["p0_i_current_private_build_gate_package_built"] is False
        and evidence["p0_i_current_private_build_gate_private_values_emitted"] is False,
        "indexed current private-builder boundary matches its receipt",
        checks,
    )

    cas_record_intake = json.loads(
        (ROOT / evidence["p0_h_institutional_cas_record_intake"]).read_text(encoding="utf-8")
    )
    require(
        cas_record_intake["decision"]
        == "PASS_PRIVATE_RECORD_INTAKE_PATH_PREPARED_AUTHORITY_CONTENT_STILL_MISSING",
        "institutional CAS record intake is prepared",
        checks,
    )
    require(
        cas_record_intake["target_identity"]["journal_title"] == "Applied Intelligence",
        "institutional record intake binds the selected journal",
        checks,
    )
    require(
        cas_record_intake["target_identity"]["print_issn"] == "0924-669X"
        and cas_record_intake["target_identity"]["electronic_issn"] == "1573-7497",
        "institutional record intake binds both current ISSNs",
        checks,
    )
    require(
        cas_record_intake["target_identity"]["category_basis"] == "MAJOR"
        and cas_record_intake["target_identity"]["category_name"] == "Computer Science",
        "institutional record intake binds the Computer Science major category",
        checks,
    )
    require(
        cas_record_intake["target_identity"]["qualifying_tiers"] == ["Q1", "Q2", "Q3"],
        "institutional record intake accepts Q3 or better",
        checks,
    )
    require(
        cas_record_intake["privacy_boundary"]["local_metadata_git_ignored"] is True
        and cas_record_intake["privacy_boundary"]["private_evidence_directory_git_ignored"] is True,
        "institutional record intake keeps local evidence outside Git",
        checks,
    )
    require(
        cas_record_intake["current_state"]["institutional_record_received"] is False,
        "institutional record remains missing",
        checks,
    )
    require(
        cas_record_intake["current_state"]["content_independently_certified"] is False
        and cas_record_intake["current_state"]["independent_client_content_audit_required"] is True,
        "institutional record content audit remains open",
        checks,
    )
    require(cas_record_intake["current_state"]["p0_h_closed"] is False, "record intake does not close P0-H", checks)
    require(cas_record_intake["submission_authorized"] is False, "record intake does not authorize submission", checks)

    correction = json.loads(
        (ROOT / evidence["p0_i_required_owner_fields_correction"]).read_text(encoding="utf-8")
    )
    require(
        correction["decision"]
        == "PASS_APPLIED_INTELLIGENCE_OWNER_GATE_CORRECTION_19_REAL_MISSING_ZERO_ERRORS",
        "official Applied Intelligence owner-gate correction is bound",
        checks,
    )
    require(correction["correction"]["prior_snapshot_missing_fields"] == 30, "owner-gate prior snapshot count", checks)
    require(correction["correction"]["current_real_missing_fields"] == 19, "owner-gate current missing count", checks)
    require(correction["correction"]["current_validation_errors"] == 0, "owner-gate current validation errors", checks)
    require(correction["correction"]["net_missing_field_reduction"] == 11, "owner-gate correction size", checks)
    require(correction["historical_private_builder_snapshot_mutated"] is False, "historical builder snapshot remains immutable", checks)
    require(correction["real_owner_values_emitted"] is False, "owner-gate correction exposes no owner values", checks)
    require(correction["real_private_package_built"] is False, "owner-gate correction builds no private package", checks)
    require(correction["submission_authorized"] is False, "owner-gate correction does not authorize submission", checks)

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
                "institutional release-review approval and retained evidence",
                "independent confirmation of legal copyright holder and year/range",
                "license-bearing latest code link and immutable archive DOI or unique identifier",
                "journal-approved review access for restricted evidence",
                "owner/institutional review of Qwen research-license compatibility for the intended release",
                "owner/institutional review of the non-c DeBERTa training-data terms for the intended release",
                "retained private institutional release record and separate client content audit",
                "final authorization of the validated V2 archive or a required successor",
            ],
        },
        {
            "gate": "P0-H",
            "status": "OPEN",
            "missing": [
                "institutional confirmation of the owner-asserted 2025 CAS edition/year",
                "retained institutional record for current Applied Intelligence title and ISSNs under the Computer Science major-category rule",
                "institutional title/ISSN-change treatment",
            ],
        },
        {
            "gate": "P0-I",
            "status": "OPEN",
            "missing": [
                "approved AI-assistance wording with a versioned and date-bounded tool record",
                "substantive competing-interests wording",
                "institutional manuscript approval and retained evidence",
                "author-populated final target package",
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
        evidence["p0_i_author_inputs_status"] == "PARTIAL_OWNER_INPUTS_LOCAL_6_MISSING_ZERO_VALIDATION_ERRORS",
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
