#!/usr/bin/env python3
"""Authenticate the CAS Q3 reviewer evidence map without scientific payload reads."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "cas_q3" / "REVIEWER_EVIDENCE_MAP.json"
RECEIPT_PATH = ROOT / "docs" / "cas_q3" / "REVIEWER_EVIDENCE_MAP_VERIFICATION.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Checks:
    def __init__(self) -> None:
        self.count = 0

    def equal(self, actual: object, expected: object, label: str) -> None:
        self.count += 1
        if actual != expected:
            raise AssertionError(f"{label}: {actual!r} != {expected!r}")

    def true(self, value: bool, label: str) -> None:
        self.count += 1
        if not value:
            raise AssertionError(label)


def main() -> int:
    checks = Checks()
    evidence = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    checks.equal(evidence["schema_version"], 1, "schema")
    checks.equal(evidence["cas_q3_status"], "NOT_READY", "submission status")
    checks.equal(evidence["distribution_authorized"], False, "distribution gate")
    checks.equal(
        evidence["decision"],
        "PASS_REVIEWER_EVIDENCE_MAP_WITH_EXTERNAL_RELEASE_GATES",
        "map decision",
    )

    for record in evidence["repository_evidence"]:
        path = (ROOT / record["path"]).resolve()
        checks.true(path.is_relative_to(ROOT), f"repository path contained: {record['path']}")
        checks.true(path.is_file(), f"repository evidence exists: {record['path']}")
        checks.equal(digest(path), record["sha256"], f"repository hash: {record['path']}")
        if marker := record.get("required_marker"):
            text = path.read_text(encoding="utf-8", errors="strict")
            checks.true(marker in text, f"decision marker: {record['path']}")

    compile_receipt = json.loads((ROOT / "paper" / "COMPILE_RECEIPT.json").read_text(encoding="utf-8"))
    checks.equal(compile_receipt["artifacts"]["output/pdf/manuscript.pdf"]["pages"], 11, "main pages")
    checks.equal(compile_receipt["artifacts"]["output/pdf/supplement.pdf"]["pages"], 3, "supplement pages")
    checks.equal(compile_receipt["text_checks"]["unresolved_markers"], 0, "compiled unresolved markers")
    checks.equal(
        compile_receipt["visual_review"]["status"],
        "NOT_PERFORMED_BY_MECHANICAL_VERIFIER_SEE_VERSIONED_ACCEPTANCE_RECORD",
        "mechanical verifier does not self-certify visual review",
    )
    static_receipt = json.loads((ROOT / "paper" / "MANUSCRIPT_VERIFICATION.json").read_text(encoding="utf-8"))
    checks.equal(static_receipt["check_count"], 141, "static manuscript checks")
    checks.equal(static_receipt["abstract_word_count"], 155, "Applied Intelligence abstract words")
    checks.equal(static_receipt["bibliography_entries"], 22, "bibliography entries")
    length_receipt = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_MANUSCRIPT_LENGTH_VERIFICATION.json").read_text(encoding="utf-8")
    )
    checks.equal(length_receipt["decision"], "PASS_REPRODUCIBLE_LENGTH_PROXY_WITH_APPLIED_INTELLIGENCE_ABSTRACT_RANGE", "length audit decision")
    checks.equal(length_receipt["pdf_tokens_before_references"], 4048, "pre-reference PDF token proxy")
    checks.equal(length_receipt["pdf_tokens_full_document"], 4745, "full PDF token proxy")
    checks.equal(length_receipt["applied_intelligence_abstract_requirement_met"], True, "Applied Intelligence abstract range")
    checks.equal(length_receipt["publisher_word_count_claimed"], False, "proxy is not a publisher word count")
    discover = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_DISCOVER_COMPUTING_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    checks.equal(
        discover["decision"],
        "PASS_DISCOVER_COMPUTING_PROVISIONAL_TECHNICAL_PREFLIGHT_EXTERNAL_GATES_OPEN",
        "Discover technical preflight decision",
    )
    checks.equal(discover["cas_q3_status"], "NOT_READY", "Discover preflight retains CAS Q3 status")
    checks.equal(discover["submission_authorized"], False, "Discover preflight is not submittable")
    checks.equal(discover["final_target_selected"], False, "Discover is not final-selected")
    checks.equal(discover["profile"]["main_text_pt"], 12, "Discover preflight text size")
    checks.equal(discover["artifacts"]["pdf_pages"], 12, "Discover preflight pages")
    checks.equal(discover["artifacts"]["source_zip_nested_members"], [], "Discover source archive is flat")
    checks.equal(discover["artifacts"]["pdf_nonembedded_font_rows"], [], "Discover fonts are embedded")
    checks.equal(discover["source_protection"]["scientific_prose_or_numbers_changed"], False, "Discover conversion preserves scientific content")
    apc = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_DISCOVER_COMPUTING_APC_AUDIT.json").read_text(encoding="utf-8")
    )
    checks.equal(
        apc["decision"],
        "PASS_OFFICIAL_DISCOVER_COMPUTING_APC_FACTS_OWNER_ACCEPTANCE_PENDING",
        "Discover APC audit decision",
    )
    checks.equal(
        apc["current_prices"],
        [
            {"amount": 1040.0, "currency": "GBP"},
            {"amount": 1520.0, "currency": "USD"},
            {"amount": 1140.0, "currency": "EUR"},
        ],
        "Discover current APC alternatives",
    )
    checks.equal(apc["price_determined_at"], "ARTICLE_ACCEPTANCE_DATE", "Discover APC date rule")
    checks.equal(apc["vat_or_local_taxes_may_apply"], True, "Discover APC tax boundary")
    checks.equal(apc["owner_publication_charge_route_selected"], False, "Discover payer route remains open")
    checks.equal(apc["waiver_confirmed"], False, "Discover waiver remains unconfirmed")
    checks.equal(apc["submission_authorized"], False, "APC audit does not authorize submission")
    data_code = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_G_DISCOVER_DATA_CODE_POLICY_AUDIT.json").read_text(encoding="utf-8")
    )
    checks.equal(
        data_code["decision"],
        "PASS_OFFICIAL_DISCOVER_DATA_CODE_POLICY_MAPPED_IMPLEMENTATION_GATES_OPEN",
        "Discover data/code policy decision",
    )
    checks.equal(data_code["final_target_selected"], False, "Discover policy mapping is provisional")
    checks.equal(data_code["official_policy"]["data_availability_statement_required"], True, "Discover data statement requirement")
    checks.equal(data_code["official_policy"]["new_custom_code_available_for_editor_reviewer_testing"], True, "Discover code testing requirement")
    checks.equal(data_code["official_policy"]["archive_doi_or_unique_identifier_expected"], True, "Discover persistent archive expectation")
    checks.equal(data_code["current_project_evidence"]["top_level_project_license_present"], False, "historical Discover audit retains pre-license state")
    checks.equal(data_code["current_project_evidence"]["persistent_archive_doi_or_unique_identifier_exists"], False, "persistent code archive gap remains")
    checks.equal(data_code["distribution_authorized"], False, "policy audit does not authorize distribution")
    third_party = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_G_THIRD_PARTY_TERMS_RECHECK.json").read_text(encoding="utf-8")
    )
    checks.equal(
        third_party["decision"],
        "PASS_THIRD_PARTY_TERMS_RECHECK_RELEASE_SOURCE_CORRECTED_CURRENT_ARCHIVE_WITHHELD",
        "third-party terms recheck decision",
    )
    checks.equal(third_party["legal_advice_claimed"], False, "terms recheck is not legal advice")
    checks.equal(third_party["distribution_authorized"], False, "terms recheck does not authorize distribution")
    checks.equal(third_party["current_archive"]["release_ready"], False, "current archive is not release ready")
    checks.equal(third_party["current_archive"]["preserved"], True, "current arithmetic witness remains preserved")
    checks.equal(third_party["source_correction"]["future_archive_rebuild_required"], True, "corrected notice requires a future rebuild")
    notices_path = ROOT / third_party["source_correction"]["path"]
    checks.equal(digest(notices_path), third_party["source_correction"]["corrected_source_sha256"], "corrected notice hash")
    notices = notices_path.read_text(encoding="utf-8")
    checks.true("including non-commercial licenses" in notices, "DeBERTa training-data caveat retained")
    checks.true("Do not reduce the training-data caveat" in notices, "unconditional MIT summary is prohibited")

    target = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_APPLIED_INTELLIGENCE_TARGET_SELECTION.json").read_text(encoding="utf-8")
    )
    checks.equal(
        target["decision"],
        "PARTIAL_PASS_OWNER_SELECTED_APPLIED_INTELLIGENCE_OFFICIAL_PROFILE_VERIFIED_CAS_DOCUMENT_AND_TARGET_PACKAGE_OPEN",
        "Applied Intelligence target selection decision",
    )
    checks.equal(target["owner_selected_target"], True, "Applied Intelligence owner selection")
    checks.equal(target["journal"]["print_issn"], "0924-669X", "Applied Intelligence print ISSN")
    checks.equal(target["journal"]["electronic_issn"], "1573-7497", "Applied Intelligence electronic ISSN")
    checks.equal(target["publication_route"]["owner_selected"], "SUBSCRIPTION_NON_OPEN_ACCESS", "subscription route")
    checks.equal(target["publication_route"]["mandatory_apc_under_selected_route"], False, "subscription route has no mandatory APC")
    checks.equal(target["current_package"]["journal_neutral_abstract_words"], 155, "target profile abstract count")
    checks.equal(target["current_package"]["abstract_requirement_met"], True, "target profile abstract requirement")
    checks.equal(target["current_package"]["journal_neutral_keyword_count"], 5, "target profile keyword count")
    checks.equal(target["current_package"]["keyword_requirement_met"], True, "target profile keyword requirement")
    checks.equal(target["current_package"]["modern_sn_jnl_preflight_built"], True, "modern target preflight built")
    checks.equal(target["current_package"]["modern_sn_jnl_preflight_verified"], True, "modern target preflight verified")
    checks.equal(target["current_package"]["publisher_current_sn_jnl_route_accepted"], True, "publisher accepts current template route")
    checks.equal(target["current_package"]["pre_submission_template_route_gate_closed"], True, "pre-submission template route gate closed")
    checks.equal(target["current_package"]["applied_intelligence_template_built"], True, "current target template built")
    checks.equal(target["current_package"]["target_specific_pdf_verified"], True, "current target PDF verified")
    checks.equal(target["current_package"]["smallcondensed_equivalence_proved"], False, "template equivalence remains open")
    checks.equal(target["owner_cas_rule"]["independent_institutional_record_retained"], False, "institutional CAS record remains open")
    checks.equal(target["submission_authorized"], False, "target audit does not authorize submission")
    applied_policy = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_G_APPLIED_INTELLIGENCE_DATA_CODE_POLICY_AUDIT.json").read_text(encoding="utf-8")
    )
    checks.equal(
        applied_policy["decision"],
        "PASS_OFFICIAL_APPLIED_INTELLIGENCE_POLICY_MAPPED_RELEASE_AND_REVIEW_ACCESS_GATES_OPEN",
        "Applied Intelligence data/code policy decision",
    )
    checks.equal(applied_policy["current_project"]["top_level_license"], "Apache-2.0", "Apache-2.0 project-code license")
    checks.equal(applied_policy["current_project"]["existing_aggregate_archive_release_ready"], False, "old archive remains withheld")
    checks.equal(applied_policy["current_project"]["new_corrected_candidate_built"], True, "corrected V2 candidate built")
    checks.equal(applied_policy["current_project"]["new_corrected_candidate_deterministic_rebuild_equal"], True, "corrected V2 deterministic rebuild")
    checks.equal(applied_policy["current_project"]["new_corrected_candidate_independently_validated"], True, "corrected V2 independent validation")
    checks.equal(applied_policy["current_project"]["new_corrected_candidate_distribution_authorized"], False, "corrected V2 remains withheld")
    checks.equal(applied_policy["policy"]["relevant_new_code_free_availability_implied_by_submission"], True, "current Springer code-sharing obligation")
    checks.equal(applied_policy["policy"]["code_availability_section_required_under_company_policy"], True, "current Code Availability section requirement")
    checks.equal(applied_policy["policy"]["reasonable_third_party_license_data_restrictions_permitted"], True, "licensed-data restrictions are policy-compatible")
    checks.equal(applied_policy["policy"]["editors_or_reviewers_may_request_nonpublic_data_or_code"], True, "editor/reviewer access right retained")
    checks.equal(applied_policy["policy"]["particular_private_delivery_channel_preapproved"], False, "private delivery channel is not overclaimed")
    checks.equal(applied_policy["current_project"]["public_github_repository_exists"], True, "public code location exists")
    checks.equal(applied_policy["current_project"]["final_submission_code_revision_frozen"], False, "final code revision remains open")
    checks.equal(applied_policy["current_project"]["restricted_evidence_policy_compatible_in_principle"], True, "restricted evidence is policy-compatible in principle")
    checks.equal(applied_policy["current_project"]["restricted_evidence_operational_delivery_confirmed"], False, "restricted-evidence delivery remains open")
    checks.equal(applied_policy["distribution_authorized"], False, "Applied policy does not authorize distribution")

    licensed_release = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_G_LICENSED_RELEASE_V2_RESULTS.json").read_text(encoding="utf-8")
    )
    checks.equal(
        licensed_release["decision"],
        "PARTIAL_PASS_APACHE2_AWARE_CORRECTED_AGGREGATE_V2_BUILT_AND_VALIDATED_DISTRIBUTION_WITHHELD",
        "licensed V2 bounded decision",
    )
    checks.equal(licensed_release["v2"]["deterministic_rebuild_equal"], True, "licensed V2 rebuild equality")
    checks.equal(licensed_release["v2"]["both_archives_independently_validated"], True, "licensed V2 archives validated")
    checks.equal(licensed_release["v2"]["validator_checks_each"], 125, "licensed V2 validator checks")
    checks.equal(licensed_release["v2"]["roundtrip_verifier_checks"], 129, "licensed V2 roundtrip checks")
    checks.equal(licensed_release["license"]["project_code_license"], "Apache-2.0", "licensed V2 project-code license")
    checks.equal(licensed_release["license"]["non_code_members_relicensed"], False, "licensed V2 does not relicense non-code members")
    checks.equal(licensed_release["distribution_authorized"], False, "licensed V2 distribution withheld")

    release_record_intake = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_G_INSTITUTIONAL_RELEASE_RECORD_INTAKE.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        release_record_intake["decision"],
        "PASS_PRIVATE_RELEASE_RECORD_INTAKE_PREPARED_EXTERNAL_DECISIONS_MISSING",
        "institutional release-record intake decision",
    )
    checks.equal(
        release_record_intake["bound_release_candidate"]["project_code_license"],
        "Apache-2.0",
        "release intake binds Apache-2.0",
    )
    checks.equal(
        release_record_intake["bound_release_candidate"]["aggregate_v2_sha256"],
        licensed_release["v2"]["archive_sha256"],
        "release intake binds exact validated V2 archive",
    )
    checks.equal(
        release_record_intake["bound_release_candidate"]["model_weights_in_release"],
        False,
        "release intake excludes model weights",
    )
    checks.equal(
        release_record_intake["bound_release_candidate"]["benchmark_payloads_answers_or_per_question_records_in_release"],
        False,
        "release intake excludes benchmark payloads and per-question records",
    )
    checks.equal(
        release_record_intake["privacy_boundary"]["local_metadata_git_ignored"]
        and release_record_intake["privacy_boundary"]["private_evidence_directory_git_ignored"],
        True,
        "release record and evidence remain outside Git",
    )
    checks.equal(release_record_intake["current_state"]["release_record_received"], False, "release record remains missing")
    checks.equal(release_record_intake["current_state"]["p0_g_closed"], False, "release intake does not close P0-G")
    checks.equal(release_record_intake["distribution_authorized"], False, "release intake does not authorize distribution")

    external_closure = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_EXTERNAL_CLOSURE_PREFLIGHT.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        external_closure["decision"],
        "PASS_PRIVATE_EXTERNAL_CLOSURE_PREFLIGHT_PREPARED_REAL_INPUTS_AND_AUDITS_OPEN",
        "unified external-closure preflight decision",
    )
    checks.equal(len(external_closure["component_inputs"]), 4, "four private closure inputs")
    checks.equal(len(external_closure["cross_checks"]), 9, "external cross-record checks documented")
    checks.equal(external_closure["privacy_boundary"]["private_inputs_git_ignored"], True, "private closure inputs ignored")
    checks.equal(external_closure["privacy_boundary"]["private_values_emitted"], False, "external closure emits no private values")
    checks.equal(external_closure["strongest_result_closes_p0_g"], False, "structural pass does not close P0-G")
    checks.equal(external_closure["strongest_result_closes_p0_h"], False, "structural pass does not close P0-H")
    checks.equal(external_closure["strongest_result_closes_p0_i"], False, "structural pass does not close P0-I")
    checks.equal(external_closure["submission_authorized"], False, "unified preflight does not authorize submission")
    local_closure = external_closure["local_workspace_execution"]
    checks.equal(
        local_closure["preparation_decision"],
        "PASS_PRIVATE_CLOSURE_WORKSPACE_PREPARED_WITHOUT_OVERWRITE",
        "private closure workspace prepared without overwrite",
    )
    checks.equal(local_closure["owner_input_hash_unchanged"], True, "owner input bytes preserved")
    checks.equal(local_closure["placeholder_files_are_institutional_records"], False, "placeholders are not records")
    checks.equal(local_closure["institutional_record_received"], False, "institutional CAS record remains pending")
    checks.equal(
        local_closure["institutional_release_record_received"],
        False,
        "institutional release record remains pending",
    )
    checks.equal(
        local_closure["institutional_manuscript_approval_record_received"],
        False,
        "institutional manuscript-approval record remains pending",
    )
    local_validation = local_closure["validation"]
    checks.equal(local_validation["exit_code"], 2, "current local closure remains fail-closed")
    checks.equal(local_validation["owner_inputs"]["missing_field_count"], 6, "current owner missing fields")
    checks.equal(local_validation["institutional_cas_record"]["missing_field_count"], 22, "CAS placeholder missing fields")
    checks.equal(local_validation["institutional_release_record"]["missing_field_count"], 22, "release placeholder missing fields")
    checks.equal(local_validation["institutional_release_record"]["validation_error_count"], 5, "release placeholder conflicts")
    checks.equal(local_validation["institutional_manuscript_approval_record"]["missing_field_count"], 17, "manuscript-approval placeholder missing fields")
    checks.equal(local_validation["institutional_manuscript_approval_record"]["validation_error_count"], 2, "manuscript-approval placeholder conflicts")
    checks.equal(local_validation["institutional_manuscript_approval_record"]["manuscript_bytes_read"], 0, "no approved manuscript bytes read")
    checks.equal(local_validation["cross_consistency_error_count"], 0, "no cross-record inconsistency inferred from placeholders")
    checks.equal(local_closure["private_values_emitted"], False, "workspace preparation emits no private values")
    external_closure_verification = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_EXTERNAL_CLOSURE_PREFLIGHT_VERIFICATION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        external_closure_verification["decision"],
        "PASS_EXTERNAL_CLOSURE_TEMPLATES_AND_PRIVACY_BOUNDARY",
        "unified closure template verification",
    )
    checks.equal(external_closure_verification["templates"], 4, "four closure templates verified")
    checks.equal(external_closure_verification["submission_authorized"], False, "template verification does not authorize submission")

    external_evidence_census = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_ACCESSIBLE_EXTERNAL_EVIDENCE_CENSUS.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(external_evidence_census["decision"], "REVIEW_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_CANDIDATES_OR_ERRORS", "raw external-evidence census retains candidate review state")
    checks.equal(external_evidence_census["ordinary_text_files_scanned"], 454115, "bounded ordinary text files scanned")
    checks.equal(external_evidence_census["zip_archives_scanned"], 39, "bounded ZIP archives scanned")
    checks.equal(external_evidence_census["zip_text_members_scanned"], 1448, "bounded ZIP text members scanned")
    checks.equal(external_evidence_census["candidate_match_count"], 3, "three broad-marker candidates retained")
    checks.equal(external_evidence_census["scan_error_count"], 0, "external-evidence census read errors")
    checks.equal(external_evidence_census["bounded_interpretation"]["institutional_record_recovered"], False, "census recovers no institutional record")
    checks.equal(external_evidence_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"], False, "census does not claim global absence")
    checks.equal(external_evidence_census["archives_extracted"], False, "census extracts no archives")
    checks.equal(external_evidence_census["submission_authorized"], False, "census does not authorize submission")
    external_evidence_triage = (ROOT / "docs" / "cas_q3" / "P0_GHI_ACCESSIBLE_EXTERNAL_EVIDENCE_CENSUS.md").read_text(encoding="utf-8")
    checks.true("PASS_BOUNDED_ACCESSIBLE_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_RECOVERY_AFTER_TRIAGE" in external_evidence_triage, "external-evidence candidate triage decision")
    checks.true("experimental data, fit/calibration/test" in external_evidence_triage, "external-evidence false-positive boundary")

    oversized_census = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_OVERSIZED_EXTERNAL_EVIDENCE_CENSUS.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(oversized_census["decision"], "PASS_BOUNDED_OVERSIZED_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES", "oversized external-evidence census decision")
    checks.equal(oversized_census["ordinary_large_text_files_stream_scanned"], 26, "oversized ordinary text files streamed")
    checks.equal(oversized_census["ordinary_large_text_bytes_scanned"], 518683752, "oversized ordinary bytes streamed")
    checks.equal(oversized_census["zip_large_text_members_stream_scanned"], 12, "oversized ZIP text members streamed")
    checks.equal(oversized_census["zip_large_text_member_bytes_scanned"], 970485466, "oversized ZIP member bytes streamed")
    checks.equal(oversized_census["ordinary_too_large_text_files_skipped"], 0, "oversized ordinary cap skips")
    checks.equal(oversized_census["zip_too_large_text_members_skipped"], 0, "oversized ZIP cap skips")
    checks.equal(oversized_census["candidate_match_count"], 0, "oversized external-evidence candidates")
    checks.equal(oversized_census["scan_error_count"], 0, "oversized external-evidence scan errors")
    checks.equal(oversized_census["bounded_interpretation"]["unsupported_binary_formats_covered"], False, "oversized census excludes unsupported binary formats")
    checks.equal(oversized_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"], False, "oversized census does not claim global absence")
    checks.equal(oversized_census["submission_authorized"], False, "oversized census does not authorize submission")

    pdf_census = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_PDF_EXTERNAL_EVIDENCE_CENSUS.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(pdf_census["decision"], "PASS_BOUNDED_PDF_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES", "PDF external-evidence census decision")
    checks.equal(pdf_census["ordinary_pdfs_extracted"], 100, "ordinary PDFs text-extracted")
    checks.equal(pdf_census["ordinary_pdf_bytes_processed"], 20267890, "ordinary PDF bytes processed")
    checks.equal(pdf_census["zip_pdf_members_extracted"], 138, "ZIP PDF members text-extracted")
    checks.equal(pdf_census["zip_pdf_member_bytes_processed"], 22448146, "ZIP PDF member bytes processed")
    checks.equal(pdf_census["extracted_text_bytes_scanned"], 3448238, "PDF extracted text bytes searched")
    checks.equal(pdf_census["ordinary_pdfs_skipped"], 0, "ordinary PDF skips")
    checks.equal(pdf_census["zip_pdf_members_skipped"], 0, "ZIP PDF member skips")
    checks.equal(pdf_census["candidate_match_count"], 0, "PDF external-evidence candidates")
    checks.equal(pdf_census["scan_error_count"], 0, "PDF external-evidence scan errors")
    checks.equal(pdf_census["unique_pdf_hashes"], 35, "unique PDF hashes inspected")
    checks.equal(pdf_census["unique_pdfs_with_zero_extracted_text"], 0, "unique PDFs without extracted text")
    checks.equal(pdf_census["unique_pdfs_with_fewer_than_20_nonwhitespace_text_bytes"], 0, "unique PDFs with low extracted text")
    checks.equal(pdf_census["unique_pdfs_attachment_inspected"], 35, "unique PDFs with attachment inventory")
    checks.equal(pdf_census["embedded_attachment_count"], 0, "embedded PDF attachments")
    checks.equal(pdf_census["zip_pdf_members_temporarily_materialized_for_attachment_inventory"], 30, "temporary ZIP PDF materializations")
    checks.equal(pdf_census["temporary_attachment_inventory_files_removed"], True, "temporary PDF inventory files removed")
    checks.equal(pdf_census["bounded_interpretation"]["embedded_attachment_inventory_complete"], True, "PDF attachment inventory complete")
    checks.equal(pdf_census["bounded_interpretation"]["pdf_image_ocr_performed"], False, "PDF census does not claim image OCR")
    checks.equal(pdf_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"], False, "PDF census does not claim global absence")
    checks.equal(pdf_census["submission_authorized"], False, "PDF census does not authorize submission")

    document_inventory = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_DOCUMENT_CONTAINER_INVENTORY.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(document_inventory["decision"], "PASS_BOUNDED_COMMON_DOCUMENT_CONTAINER_INVENTORY_PDF_ONLY", "common document-container inventory decision")
    checks.equal(document_inventory["zip_archives_scanned"], 39, "document-container ZIP archives scanned")
    checks.equal(document_inventory["ordinary_file_counts"][".pdf"], 100, "ordinary PDF inventory count")
    checks.equal(document_inventory["zip_member_counts"][".pdf"], 138, "ZIP PDF inventory count")
    checks.equal(document_inventory["non_pdf_document_count"], 0, "non-PDF common document containers")
    checks.equal(document_inventory["scan_error_count"], 0, "document-container inventory errors")
    checks.equal(document_inventory["file_contents_read"], False, "document-container inventory reads metadata only")
    checks.equal(document_inventory["bounded_interpretation"]["files_with_incorrect_or_missing_extensions_covered"], False, "document inventory does not claim disguised formats")
    checks.equal(document_inventory["bounded_interpretation"]["unknown_binary_formats_covered"], False, "document inventory does not claim unknown formats")
    checks.equal(document_inventory["submission_authorized"], False, "document inventory does not authorize submission")

    recursive_archive_census = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_RECURSIVE_ARCHIVE_CLOSURE_EVIDENCE.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        recursive_archive_census["decision"],
        "PASS_BOUNDED_FIRST_LEVEL_NESTED_ARCHIVE_CENSUS_NO_RECOVERY",
        "first-level nested-archive census decision",
    )
    checks.equal(recursive_archive_census["top_level_zip_archives_scanned"], 39, "top-level ZIPs checked for nested archives")
    checks.equal(recursive_archive_census["nested_archives_seen"], 4, "nested ZIP archives seen")
    checks.equal(recursive_archive_census["nested_archives_materialized"], 4, "nested ZIP archives materialized")
    checks.equal(recursive_archive_census["nested_archive_bytes_materialized"], 269975228, "nested ZIP bytes materialized")
    checks.equal(recursive_archive_census["nested_archives_skipped"], 0, "nested ZIP skips")
    checks.equal(recursive_archive_census["nested_member_count"], 301, "nested archive member count")
    checks.equal(recursive_archive_census["deeper_archives_seen"], 0, "deeper ZIP archives")
    checks.equal(recursive_archive_census["text_members_seen"], 234, "nested text members seen")
    checks.equal(recursive_archive_census["text_members_scanned"], 234, "nested text members scanned")
    checks.equal(recursive_archive_census["text_bytes_scanned"], 858962287, "nested text bytes scanned")
    checks.equal(recursive_archive_census["text_members_skipped"], 0, "nested text skips")
    checks.equal(recursive_archive_census["text_candidate_match_count"], 0, "nested text candidates")
    checks.equal(recursive_archive_census["strict_magic_counts"], {"pdf": 32}, "nested strict file-header counts")
    checks.equal(recursive_archive_census["strict_magic_suffix_mismatch_count"], 0, "nested file-header extension mismatches")
    checks.equal(recursive_archive_census["pdf_audit"]["zip_pdf_members_extracted"], 32, "nested PDFs extracted")
    checks.equal(recursive_archive_census["pdf_audit"]["unique_pdf_hashes"], 14, "nested unique PDF hashes")
    checks.equal(recursive_archive_census["pdf_audit"]["extracted_text_bytes_scanned"], 323181, "nested PDF text bytes searched")
    checks.equal(recursive_archive_census["pdf_audit"]["embedded_attachment_count"], 0, "nested PDF attachments")
    checks.equal(recursive_archive_census["candidate_match_count"], 0, "nested archive candidates")
    checks.equal(recursive_archive_census["scan_error_count"], 0, "nested archive errors")
    checks.equal(recursive_archive_census["temporary_files_removed"], True, "nested archive temporary files removed")
    checks.equal(recursive_archive_census["archive_trees_extracted"], False, "nested archive trees not extracted")
    checks.equal(recursive_archive_census["bounded_interpretation"]["pdf_image_ocr_performed"], False, "nested PDF census does not claim OCR")
    checks.equal(recursive_archive_census["bounded_interpretation"]["absence_outside_scanned_roots_proved"], False, "nested archive census does not claim global absence")
    checks.equal(recursive_archive_census["submission_authorized"], False, "nested archive census does not authorize submission")

    ordinary_magic = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_ORDINARY_DOCUMENT_MAGIC.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        ordinary_magic["decision"],
        "PASS_BOUNDED_ORDINARY_DOCUMENT_MAGIC_MATCHES_EXTENSIONS",
        "ordinary-file document-magic census decision",
    )
    checks.equal(ordinary_magic["roots_scanned"], 3, "ordinary document-magic roots")
    checks.equal(ordinary_magic["ordinary_files_seen"], 465460, "ordinary files with headers inspected")
    checks.equal(ordinary_magic["header_bytes_per_file"], 4096, "ordinary document-magic header cap")
    checks.equal(ordinary_magic["header_bytes_read"], 631242643, "ordinary document-magic bytes read")
    checks.equal(ordinary_magic["strict_magic_counts"], {"zip": 39, "pdf": 100}, "ordinary strict document-magic counts")
    checks.equal(ordinary_magic["strict_magic_suffix_counts"]["zip"], {".zip": 39}, "ordinary ZIP suffix matches")
    checks.equal(ordinary_magic["strict_magic_suffix_counts"]["pdf"], {".pdf": 100}, "ordinary PDF suffix matches")
    checks.equal(sum(ordinary_magic["zip_document_family_counts"].values()), 0, "ordinary OOXML/ODF packages")
    checks.equal(ordinary_magic["loose_pdf_marker_non_header_count"], 3, "loose non-header PDF markers retained")
    checks.equal(ordinary_magic["loose_pdf_marker_non_header_suffix_counts"], {".js": 2, ".ts": 1}, "loose PDF-marker source suffixes")
    checks.equal(ordinary_magic["document_magic_suffix_mismatch_count"], 0, "ordinary document-magic suffix mismatches")
    checks.equal(ordinary_magic["scan_error_count"], 0, "ordinary document-magic errors")
    checks.equal(ordinary_magic["bounded_interpretation"]["common_pdf_rtf_ole_zip_document_magic_covered"], True, "common ordinary document magic covered")
    checks.equal(ordinary_magic["bounded_interpretation"]["unknown_binary_formats_covered"], False, "ordinary magic audit does not claim unknown formats")
    checks.equal(ordinary_magic["bounded_interpretation"]["absence_outside_scanned_roots_proved"], False, "ordinary magic audit does not claim global absence")
    checks.equal(ordinary_magic["submission_authorized"], False, "ordinary magic audit does not authorize submission")

    pdf_page_coverage = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_PDF_PAGE_TEXT_COVERAGE.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        pdf_page_coverage["decision"],
        "PASS_BOUNDED_UNIQUE_PDF_PAGE_TEXT_COVERAGE_NO_LOW_TEXT_PAGES",
        "unique-PDF page-text coverage decision",
    )
    checks.equal(pdf_page_coverage["ordinary_pdf_occurrences"], 100, "page-audit ordinary PDF occurrences")
    checks.equal(pdf_page_coverage["direct_zip_pdf_occurrences"], 138, "page-audit direct ZIP PDF occurrences")
    checks.equal(pdf_page_coverage["nested_zip_pdf_occurrences"], 32, "page-audit nested ZIP PDF occurrences")
    checks.equal(pdf_page_coverage["total_pdf_occurrences"], 270, "page-audit total PDF occurrences")
    checks.equal(pdf_page_coverage["unique_pdf_hashes"], 35, "page-audit unique PDF hashes")
    checks.equal(pdf_page_coverage["nested_archives_materialized"], 4, "page-audit nested archives")
    checks.equal(pdf_page_coverage["total_unique_pdf_pages"], 446, "unique PDF pages inspected")
    checks.equal(pdf_page_coverage["pages_with_raster_images"], 15, "PDF pages with raster images")
    checks.equal(pdf_page_coverage["zero_text_page_count"], 0, "zero-text PDF pages")
    checks.equal(pdf_page_coverage["fewer_than_20_nonwhitespace_text_page_count"], 0, "low-text PDF pages")
    checks.equal(pdf_page_coverage["skipped_pdf_occurrences"], 0, "page-audit PDF skips")
    checks.equal(pdf_page_coverage["skipped_nested_archives"], 0, "page-audit nested archive skips")
    checks.equal(pdf_page_coverage["scan_error_count"], 0, "page-audit parser errors")
    checks.equal(pdf_page_coverage["bounded_interpretation"]["text_inside_raster_images_ocr_performed"], False, "page audit does not claim image OCR")
    checks.equal(pdf_page_coverage["bounded_interpretation"]["text_inside_images_on_text_bearing_pages_excluded"], True, "image-internal text exclusion retained")
    checks.equal(pdf_page_coverage["submission_authorized"], False, "page audit does not authorize submission")

    image_evidence = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GHI_EXTERNAL_IMAGE_EVIDENCE.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        image_evidence["decision"],
        "PASS_BOUNDED_COMMON_RASTER_IMAGE_INVENTORY_NO_EXTENSION_MISMATCH",
        "external raster-image inventory decision",
    )
    checks.equal(image_evidence["roots_scanned"], 3, "external image logical roots")
    checks.equal(image_evidence["ordinary_files_seen"], 465460, "external image ordinary logical paths")
    checks.equal(image_evidence["resolved_outside_declared_roots_files"], 7796, "junction outside-resolved files disclosed")
    checks.equal(image_evidence["zip_archives_scanned"], 39, "external image direct ZIPs")
    checks.equal(image_evidence["nested_zip_archives_scanned"], 4, "external image nested ZIPs")
    checks.equal(image_evidence["direct_zip_members_seen"], 2389, "external image direct ZIP members")
    checks.equal(image_evidence["nested_zip_members_seen"], 301, "external image nested ZIP members")
    checks.equal(image_evidence["ordinary_image_occurrences"], 83, "ordinary image occurrences")
    checks.equal(image_evidence["direct_zip_image_members"], 21, "direct ZIP image occurrences")
    checks.equal(image_evidence["nested_zip_image_members"], 0, "nested ZIP image occurrences")
    checks.equal(image_evidence["image_occurrences"], 104, "total image occurrences")
    checks.equal(image_evidence["unique_image_hashes"], 43, "unique image hashes")
    checks.equal(image_evidence["resolved_outside_declared_roots_image_occurrences"], 34, "junction image occurrences")
    checks.equal(image_evidence["resolved_outside_declared_roots_unique_image_hashes"], 29, "junction unique image hashes")
    checks.equal(image_evidence["image_magic_suffix_mismatch_count"], 0, "image suffix mismatches")
    checks.equal(image_evidence["scan_error_count"], 0, "external image scan errors")
    checks.equal(image_evidence["bounded_interpretation"]["image_pixel_text_ocr_performed"], False, "image audit does not claim OCR")
    checks.equal(image_evidence["bounded_interpretation"]["logical_root_reparse_targets_disclosed"], True, "junction scope disclosed")
    checks.equal(image_evidence["bounded_interpretation"]["absence_outside_scanned_roots_proved"], False, "image audit does not claim global absence")
    checks.equal(image_evidence["submission_authorized"], False, "image audit does not authorize submission")

    applied_preflight = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    checks.equal(
        applied_preflight["decision"],
        "PARTIAL_PASS_APPLIED_INTELLIGENCE_MODERN_SN_JNL_PREFLIGHT_SMALLCONDENSED_EQUIVALENCE_OPEN",
        "Applied Intelligence modern preflight decision",
    )
    checks.equal(applied_preflight["artifacts"]["pdf_pages"], 12, "Applied Intelligence preflight pages")
    checks.equal(applied_preflight["artifacts"]["pdf_nonembedded_font_rows"], [], "Applied Intelligence embedded fonts")
    checks.equal(applied_preflight["artifacts"]["pdf_type3_font_rows"], [], "Applied Intelligence no Type 3 fonts")
    checks.equal(applied_preflight["profile"]["smallcondensed_profile_used"], False, "smallcondensed not claimed")
    checks.equal(
        applied_preflight["source_protection"]["scientific_prose_or_numbers_changed"],
        False,
        "Applied Intelligence preflight preserves scientific content",
    )
    checks.equal(applied_preflight["submission_authorized"], False, "Applied Intelligence preflight not submittable")
    applied_verification = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_VERIFICATION.json").read_text(encoding="utf-8")
    )
    checks.equal(
        applied_verification["decision"],
        "PASS_COMMITTED_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_WITH_TEMPLATE_EQUIVALENCE_OPEN",
        "committed Applied Intelligence preflight verification",
    )
    checks.equal(applied_verification["checks"], 38, "Applied Intelligence preflight verification checks")

    applied_transport = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_TEMPLATE_TRANSPORT_RESULTS.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        applied_transport["decision"],
        "PARTIAL_PASS_OFFICIAL_SN_JNL_ALLOWED_COMPLETE_PRIVATE_TRANSPORT_VALIDATED_SMALLCONDENSED_LEGACY_CONFLICT_RETAINED",
        "Applied Intelligence complete-source transport bounded decision",
    )
    transport_result = applied_transport["private_complete_source_transport"]
    checks.equal(transport_result["deterministic_rebuild_equal"], True, "target transport rebuild equality")
    checks.equal(transport_result["both_builds_independently_validated"], True, "both target transports validated")
    checks.equal(transport_result["validator_checks_each"], 56, "target transport validator checks")
    checks.equal(transport_result["clean_compile_pages"], 12, "target transport compiled pages")
    checks.equal(
        transport_result["clean_compile_pdf_sha256"],
        "f423cdeb634d66e4315d56a8f4c3dda8807ef0b4fe79235e13b698c20d185ea4",
        "historical target transport compiled PDF remains pinned",
    )
    checks.equal(
        applied_transport["official_source_findings"]["journal_specific_equivalence_from_sn_jnl_to_smallcondensed_proved"],
        False,
        "legacy smallcondensed discrepancy retained",
    )
    checks.equal(applied_transport["submission_authorized"], False, "target transport does not authorize submission")
    checks.equal(applied_transport["distribution_authorized"], False, "target transport remains private")

    policy_refresh = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_DATA_CODE_POLICY_REFRESH_ACCEPTANCE.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        policy_refresh["decision"],
        "PASS_DATA_CODE_POLICY_REFRESH_BASE_TARGET_TRANSPORT_AND_SYNTHETIC_BUILD_ACCEPTED_EXTERNAL_GATES_OPEN",
        "data/code policy refresh bounded decision",
    )
    checks.equal(policy_refresh["cas_q3_status"], "NOT_READY", "policy refresh retains CAS Q3 status")
    checks.equal(policy_refresh["base_artifacts"]["static_checks"], 141, "policy refresh static checks")
    checks.equal(policy_refresh["base_artifacts"]["pdf_tokens_before_references"], 4048, "policy refresh pre-reference tokens")
    checks.equal(policy_refresh["base_artifacts"]["pdf_tokens_full_document"], 4745, "policy refresh full tokens")
    checks.equal(policy_refresh["base_artifacts"]["pages_visually_inspected"], 14, "policy refresh base visual pages")
    checks.equal(policy_refresh["base_artifacts"]["visual_defects"], 0, "policy refresh base visual defects")
    checks.equal(
        policy_refresh["target_preflight"]["pdf_sha256"],
        applied_preflight["artifacts"]["pdf_sha256"],
        "policy refresh target PDF pin",
    )
    checks.equal(policy_refresh["target_preflight"]["pages_visually_inspected"], 12, "policy refresh target visual pages")
    checks.equal(policy_refresh["target_preflight"]["visual_defects"], 0, "policy refresh target visual defects")
    current_transport_result = policy_refresh["current_private_transport"]
    checks.equal(current_transport_result["deterministic_rebuild_equal"], True, "refreshed transport rebuild equality")
    checks.equal(current_transport_result["both_builds_independently_validated"], True, "refreshed transports validated")
    checks.equal(current_transport_result["validator_checks_each"], 56, "refreshed transport checks")
    checks.equal(current_transport_result["clean_compile_pages"], 12, "refreshed transport pages")
    checks.equal(
        current_transport_result["clean_compile_pdf_sha256"],
        applied_preflight["artifacts"]["pdf_sha256"],
        "refreshed transport compiles to current preflight PDF",
    )
    checks.equal(
        policy_refresh["preserved_historical_artifacts"]["prior_transport_archive_sha256"],
        transport_result["archive_sha256"],
        "prior transport remains bound as history",
    )
    checks.equal(policy_refresh["preserved_historical_artifacts"]["prior_transport_record_mutated"], False, "historical transport record not mutated")
    checks.equal(policy_refresh["scope"]["real_author_package_built"], False, "refresh builds no real author package")
    checks.equal(policy_refresh["scope"]["distribution_authorized"], False, "refresh does not authorize distribution")
    checks.equal(policy_refresh["scope"]["submission_authorized"], False, "refresh does not authorize submission")

    target_packet = (ROOT / "docs" / "cas_q3" / "P0_H_TARGET_JOURNAL_DECISION_PACKET.md").read_text(
        encoding="utf-8"
    )
    normalized_target_packet = " ".join(target_packet.split())
    for phrase in (
        "PARTIAL_PASS_OWNER_SELECTED_APPLIED_INTELLIGENCE_INSTITUTIONAL_CAS_RECORD_PENDING",
        "current print ISSN: `0924-669X`",
        "current electronic ISSN: `1573-7497`",
        "JCR quartiles and third-party partition sites are not substitutes",
    ):
        checks.true(phrase in normalized_target_packet, f"current target qualification packet: {phrase}")
    checks.true(
        "DISCOVER COMPUTING REMAINS THE CONDITIONAL EDITORIAL-FIT LEAD" not in target_packet,
        "stale Discover Computing lead removed from current packet",
    )

    hbut_affiliation = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_HBUT_AFFILIATION_ADDRESS_VERIFICATION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        hbut_affiliation["decision"],
        "PASS_OFFICIAL_HBUT_INSTITUTION_CITY_POSTCODE_VERIFIED_DEPARTMENT_PENDING",
        "HBUT affiliation-address bounded decision",
    )
    checks.equal(hbut_affiliation["institution"], "Hubei University of Technology", "HBUT institution")
    checks.equal(hbut_affiliation["verified_affiliation_fields"]["city"], "Wuhan", "HBUT city")
    checks.equal(hbut_affiliation["verified_affiliation_fields"]["postal_code"], "430068", "HBUT postal code")
    checks.equal(hbut_affiliation["department_verified"], False, "HBUT department remains pending")
    checks.equal(hbut_affiliation["personal_values_emitted"], False, "HBUT audit personal-value boundary")

    hbut_cas = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_HBUT_CAS_POLICY_VERIFICATION.json").read_text(encoding="utf-8")
    )
    checks.equal(
        hbut_cas["decision"],
        "PARTIAL_PASS_OFFICIAL_HBUT_UPGRADED_CAS_BASIS_AND_REVIEW_OFFICE_VERIFIED_EDITION_AND_JOURNAL_RECORD_PENDING",
        "HBUT CAS policy decision",
    )
    checks.equal(hbut_cas["verified_scope"]["institution_uses_cas_upgraded_basis_for_sci_ssci"], True, "HBUT upgraded CAS basis")
    checks.equal(hbut_cas["verified_scope"]["hbut_first_affiliation_requirement"], True, "HBUT first-affiliation requirement")
    checks.equal(hbut_cas["verified_scope"]["institutional_review_route_identified"], True, "HBUT review route")
    checks.equal(hbut_cas["verified_scope"]["institution_recognized_cas_edition_year"], None, "HBUT CAS edition remains open")
    checks.equal(hbut_cas["verified_scope"]["college_plan_previous_publication_year_rule_observed"], True, "HBUT college previous-year rule observed")
    checks.equal(hbut_cas["verified_scope"]["candidate_report_year_if_formal_publication_in_2026"], 2025, "candidate 2026-publication report year")
    checks.equal(hbut_cas["verified_scope"]["candidate_year_rule_confirmed_university_wide"], False, "candidate year rule remains centrally unconfirmed")
    checks.equal(hbut_cas["verified_scope"]["applied_intelligence_current_title_issns_major_category_q3_record_retained"], False, "Applied Intelligence institutional record remains open")
    checks.equal(hbut_cas["attachment_access"]["attachment_contents_inspected"], False, "CAPTCHA-gated attachments not inferred")
    checks.equal(hbut_cas["p0_h_closed"], False, "P0-H remains open")
    checks.equal(hbut_cas["submission_authorized"], False, "HBUT policy evidence does not authorize submission")

    hbut_request = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_GH_HBUT_INSTITUTIONAL_VERIFICATION_REQUEST.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(hbut_request["decision"], "PASS_CONCRETE_HBUT_INSTITUTIONAL_REQUEST_PREPARED_RESPONSE_PENDING", "HBUT verification request decision")
    checks.equal(all(hbut_request["requested_evidence"].values()), True, "HBUT request covers every external evidence field")
    checks.equal(hbut_request["request_sent"], False, "HBUT request remains unsent")
    checks.equal(hbut_request["institutional_response_received"], False, "HBUT response remains pending")
    checks.equal(hbut_request["institutional_response_retained"], False, "HBUT response is not fabricated")
    checks.equal(hbut_request["public_corroboration_context"]["public_2025_major_category_q3_supported"], True, "request supplies public major-Q3 context")
    checks.equal(hbut_request["public_corroboration_context"]["public_2025_minor_category_q4_supported"], True, "request distinguishes public minor-Q4 context")
    checks.equal(hbut_request["public_corroboration_context"]["accepted_as_hbut_record"], False, "public context is not HBUT authority")
    checks.equal(hbut_request["central_notice_attachments"]["count"], 2, "two central-notice attachments")
    checks.equal(hbut_request["central_notice_attachments"]["download_requires_captcha"], True, "attachment CAPTCHA boundary retained")
    checks.equal(hbut_request["central_notice_attachments"]["contents_inspected"], False, "CAPTCHA attachments remain uninspected")
    checks.equal(hbut_request["central_notice_attachments"]["contents_inferred"], False, "CAPTCHA attachment contents not inferred")
    official_contact = hbut_request["official_contact_route"]
    checks.equal(official_contact["general_email"], "kyc@mail.hbut.edu.cn", "request uses official general email")
    checks.equal(official_contact["natural_science_results_office_phone"], "027-59750136", "request uses natural-science results office phone")
    checks.equal(official_contact["temporary_or_unrelated_notice_email_used"], False, "request excludes temporary notice addresses")
    checks.equal(len(hbut_request["private_response_import"]) == 6, True, "request binds private import workflow")
    checks.equal(
        hbut_request["private_response_import"]["manuscript_approval_record_input"],
        "docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD.local.json",
        "request binds manuscript-approval private input",
    )
    checks.equal(hbut_request["private_response_import"]["unified_preflight_command"], "python scripts/verify_cas_q3_external_closure_inputs.py", "request binds unified preflight command")
    checks.equal(hbut_request["private_response_import"]["client_content_audit_required_after_structural_pass"], True, "request retains client content audit")
    checks.equal(hbut_request["p0_g_closed"], False, "request does not close P0-G")
    checks.equal(hbut_request["p0_h_closed"], False, "request does not close P0-H")
    checks.equal(hbut_request["p0_i_closed"], False, "request does not close P0-I")
    checks.equal(hbut_request["submission_authorized"], False, "request does not authorize submission")
    request_text = (ROOT / hbut_request["request_path"]).read_text(encoding="utf-8")
    checks.true("计算机科学大类3区、人工智能小类4区" in request_text, "request states public major/minor context")
    checks.true("kyc@mail.hbut.edu.cn" in request_text, "request contains official general email")
    checks.true("python scripts/verify_cas_q3_external_closure_inputs.py" in request_text, "request contains private import command")
    checks.true("本稿不依据未读取的" in request_text, "request retains CAPTCHA non-inference boundary")

    hbut_secondary = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_HBUT_CAS_EDITION_RULE_SECONDARY_EVIDENCE.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        hbut_secondary["decision"],
        "PARTIAL_PASS_OFFICIAL_HBUT_COLLEGE_PREVIOUS_YEAR_CAS_RULE_FOUND_UNIVERSITY_WIDE_CONFIRMATION_PENDING",
        "HBUT secondary edition-rule decision",
    )
    checks.equal(hbut_secondary["evidence_scope"]["previous_publication_year_rule_observed"], True, "secondary previous-year rule")
    checks.equal(hbut_secondary["evidence_scope"]["central_research_administration_policy"], False, "secondary evidence is not central policy")
    checks.equal(hbut_secondary["evidence_scope"]["rule_proved_university_wide_for_faculty_research_recognition"], False, "university-wide applicability remains open")
    checks.equal(hbut_secondary["candidate_interpretation_requiring_confirmation"]["if_formal_publication_year_is_2026_candidate_cas_report_year"], 2025, "secondary candidate report year")
    checks.equal(hbut_secondary["candidate_interpretation_requiring_confirmation"]["confirmed_by_hbut_research_administration"], False, "central confirmation remains open")
    checks.equal(hbut_secondary["authoritative_cas_platform"]["upgraded_2025_listed_as_available"], True, "authoritative 2025 upgraded data available")
    checks.equal(hbut_secondary["authoritative_cas_platform"]["journal_search_supports_title_and_issn"], True, "authoritative title and ISSN search")
    checks.equal(hbut_secondary["authoritative_cas_platform"]["journal_partition_data_requires_institutional_or_authenticated_access"], True, "authoritative platform access boundary")
    checks.equal(hbut_secondary["authoritative_cas_platform"]["hbut_access_verified"], False, "HBUT platform access not claimed")
    checks.equal(hbut_secondary["authoritative_cas_platform"]["applied_intelligence_2025_record_retrieved"], False, "target platform record remains missing")
    checks.equal(hbut_secondary["central_policy_attachment_access"]["contents_inspected"], False, "CAPTCHA-gated contents not inspected")
    checks.equal(hbut_secondary["central_policy_attachment_access"]["contents_inferred"], False, "CAPTCHA-gated contents not inferred")
    checks.equal(hbut_secondary["p0_h_closed"], False, "secondary evidence does not close P0-H")
    checks.equal(hbut_secondary["submission_authorized"], False, "secondary evidence does not authorize submission")

    public_corroboration = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        public_corroboration["decision"],
        "PARTIAL_PASS_PUBLIC_2025_MAJOR_Q3_CORROBORATION_INSTITUTIONAL_RECORD_STILL_REQUIRED",
        "public target corroboration bounded decision",
    )
    checks.equal(
        public_corroboration["bounded_interpretation"]["public_sources_support_2025_major_category_q3"],
        True,
        "public evidence supports 2025 major Q3",
    )
    checks.equal(
        public_corroboration["bounded_interpretation"]["public_sources_support_2025_minor_category_q4"],
        True,
        "public evidence distinguishes minor Q4",
    )
    checks.equal(
        public_corroboration["bounded_interpretation"]["shufe_single_q4_label_proved_to_be_minor_category"],
        False,
        "ambiguous condensed Q4 label is not reclassified",
    )
    checks.equal(
        public_corroboration["bounded_interpretation"]["hbut_current_title_issn_record_retained"],
        False,
        "public corroboration does not replace HBUT record",
    )
    checks.equal(public_corroboration["bounded_interpretation"]["p0_h_closed"], False, "public corroboration does not close P0-H")

    hbut_public_recheck = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_HBUT_PUBLIC_TARGET_RECORD_RECHECK.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        hbut_public_recheck["decision"],
        "PASS_BOUNDED_HBUT_PUBLIC_TARGET_RECORD_RECHECK_NO_QUALIFYING_2025_INSTITUTIONAL_RECORD_FOUND",
        "HBUT public target-record recheck decision",
    )
    checks.equal(hbut_public_recheck["cas_q3_status"], "NOT_READY", "HBUT public recheck retains CAS Q3 status")
    checks.equal(len(hbut_public_recheck["candidate_pages"]), 4, "HBUT public recheck candidate pages")
    checks.equal(all(not item["qualifies_for_current_gate"] for item in hbut_public_recheck["candidate_pages"]), True, "HBUT public candidates do not qualify")
    checks.equal(hbut_public_recheck["search_scope"]["search_engine_completeness_claimed"], False, "HBUT web search completeness not overclaimed")
    checks.equal(hbut_public_recheck["search_scope"]["authenticated_or_internal_pages_searched"], False, "HBUT internal pages outside scope")
    checks.equal(hbut_public_recheck["search_scope"]["captcha_protected_attachments_inspected"], False, "HBUT CAPTCHA attachments outside recheck")
    checks.equal(hbut_public_recheck["result"]["qualifying_public_hbut_record_found"], False, "no qualifying public HBUT record found")
    checks.equal(hbut_public_recheck["result"]["absence_of_any_institutional_record_proved"], False, "institutional record absence not claimed")
    checks.equal(hbut_public_recheck["result"]["p0_h_closed"], False, "HBUT public recheck does not close P0-H")
    checks.equal(hbut_public_recheck["submission_authorized"], False, "HBUT public recheck does not authorize submission")

    owner_cas_path_check = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_OWNER_2025_CAS_ASSERTION_PATH_CHECK.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        owner_cas_path_check["decision"],
        "PARTIAL_PASS_OWNER_2025_MAJOR_Q3_ASSERTION_RECEIVED_DECLARED_EVIDENCE_PATH_MISSING",
        "owner CAS assertion path-check decision",
    )
    checks.equal(owner_cas_path_check["owner_assertion_received"], True, "owner CAS assertion received")
    checks.equal(owner_cas_path_check["candidate_edition_year"], 2025, "owner candidate CAS edition")
    checks.equal(owner_cas_path_check["category_basis"], "MAJOR", "owner asserted major category")
    checks.equal(owner_cas_path_check["asserted_tier"], "Q3", "owner asserted tier")
    checks.equal(owner_cas_path_check["declared_path_exists_in_active_worktree"], False, "declared CAS path absent in worktree")
    checks.equal(owner_cas_path_check["declared_path_exists_in_original_workspace"], False, "declared CAS path absent in original workspace")
    checks.equal(owner_cas_path_check["institutional_record_received"], False, "owner assertion is not institutional record")
    checks.equal(owner_cas_path_check["institutional_evidence_bytes_read"], 0, "owner path check read no evidence bytes")
    checks.equal(owner_cas_path_check["p0_h_closed"], False, "owner assertion path check does not close P0-H")
    corroboration_receipt = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION_VERIFICATION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        corroboration_receipt["decision"],
        "PASS_BOUNDED_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION_VERIFICATION",
        "public corroboration verifier decision",
    )
    checks.equal(corroboration_receipt["checks"], 39, "public corroboration verifier checks")
    checks.equal(corroboration_receipt["institution_recognized_record_retained"], False, "institutional record remains open")

    cas_record_intake = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_H_INSTITUTIONAL_CAS_RECORD_INTAKE.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        cas_record_intake["decision"],
        "PASS_PRIVATE_RECORD_INTAKE_PATH_PREPARED_AUTHORITY_CONTENT_STILL_MISSING",
        "institutional CAS record intake decision",
    )
    checks.equal(cas_record_intake["target_identity"]["journal_title"], "Applied Intelligence", "record intake journal")
    checks.equal(cas_record_intake["target_identity"]["print_issn"], "0924-669X", "record intake print ISSN")
    checks.equal(cas_record_intake["target_identity"]["electronic_issn"], "1573-7497", "record intake electronic ISSN")
    checks.equal(cas_record_intake["target_identity"]["category_basis"], "MAJOR", "record intake major category")
    checks.equal(cas_record_intake["target_identity"]["qualifying_tiers"], ["Q1", "Q2", "Q3"], "record intake Q3-or-better tiers")
    checks.equal(cas_record_intake["privacy_boundary"]["local_metadata_git_ignored"], True, "record metadata ignored")
    checks.equal(cas_record_intake["privacy_boundary"]["private_evidence_directory_git_ignored"], True, "record bytes ignored")
    checks.equal(cas_record_intake["current_state"]["institutional_record_received"], False, "record remains missing")
    checks.equal(cas_record_intake["current_state"]["content_independently_certified"], False, "record content is not self-certified")
    checks.equal(cas_record_intake["current_state"]["independent_client_content_audit_required"], True, "record client audit remains required")
    checks.equal(cas_record_intake["current_state"]["p0_h_closed"], False, "record intake does not close P0-H")
    checks.equal(cas_record_intake["submission_authorized"], False, "record intake does not authorize submission")

    private_builder = json.loads(
        (
            ROOT
            / "docs"
            / "cas_q3"
            / "P0_I_APPLIED_INTELLIGENCE_PRIVATE_SUBMISSION_BUILDER_RESULTS.json"
        ).read_text(encoding="utf-8")
    )
    checks.equal(
        private_builder["decision"],
        "PASS_SYNTHETIC_COMPLETE_INPUT_TO_PRIVATE_APPLIED_INTELLIGENCE_PACKAGE_PIPELINE_FINAL_FACTS_AND_AUDITS_OPEN",
        "private target-builder bounded decision",
    )
    checks.equal(private_builder["input_scope"]["synthetic_complete_fixture_used"], True, "synthetic input scope")
    checks.equal(private_builder["input_scope"]["real_owner_input_used"], False, "real owner input excluded")
    checks.equal(private_builder["input_scope"]["real_owner_input_missing_fields"], 30, "historical real owner missing fields")
    checks.equal(
        private_builder["authenticated_anonymous_transport"]["archive_sha256"],
        transport_result["archive_sha256"],
        "private builder authenticates accepted anonymous transport",
    )
    checks.equal(private_builder["synthetic_private_build"]["source_members"], 10, "synthetic private source members")
    checks.equal(private_builder["synthetic_private_build"]["compiled_pages"], 13, "synthetic private compiled pages")
    checks.equal(private_builder["synthetic_private_build"]["visual_defects"], 0, "synthetic private visual defects")
    checks.equal(private_builder["submission_authorized"], False, "synthetic build does not authorize submission")

    route_resolution = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_TEMPLATE_ROUTE_RESOLUTION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        route_resolution["decision"],
        "PASS_OFFICIAL_PUBLISHER_ACCEPTS_CURRENT_SN_JNL_SUBMISSION_ROUTE_SMALLCONDENSED_STYLE_EQUIVALENCE_UNPROVED",
        "template-route resolution decision",
    )
    checks.equal(
        route_resolution["resolution"]["publisher_acceptance_of_current_sn_jnl_submission_route_proved"],
        True,
        "publisher accepts current template route",
    )
    checks.equal(
        route_resolution["resolution"]["journal_specific_smallcondensed_style_equivalence_proved"],
        False,
        "smallcondensed equivalence remains unproved",
    )
    checks.equal(route_resolution["resolution"]["pre_submission_template_route_gate_closed"], True, "template route gate closed")
    checks.equal(route_resolution["resolution"]["submission_system_compile_observed"], False, "Editorial Manager compile not claimed")
    checks.equal(route_resolution["resolution"]["author_populated_package_built"], False, "real author package not claimed")
    checks.equal(route_resolution["authenticated_current_route"]["validator_checks_each"], 56, "route transport checks")
    checks.equal(route_resolution["authenticated_current_route"]["clean_compile_pages"], 12, "route compiled pages")
    checks.equal(route_resolution["scientific_payloads_read"], False, "route audit reads no scientific payload")
    checks.equal(route_resolution["model_forwards"], 0, "route audit model forwards")
    checks.equal(route_resolution["scientific_fits"], 0, "route audit scientific fits")
    checks.equal(route_resolution["submission_authorized"], False, "route audit does not authorize submission")

    license_state = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_G_LICENSE_STATE_VERIFICATION.json").read_text(encoding="utf-8")
    )
    checks.equal(license_state["decision"], "PASS_CURRENT_LICENSE_STATE_CONSISTENCY_WITH_EXTERNAL_GATES_OPEN", "current license state")
    checks.equal(license_state["checks"], 26, "license-state verification checks")
    checks.equal(license_state["project_code_license"], "Apache-2.0", "project-code license")
    checks.equal(license_state["legal_holder_confirmed"], False, "legal holder remains open")
    checks.equal(license_state["copyright_year_confirmed"], False, "copyright year remains open")
    checks.equal(license_state["institutional_release_review_complete"], False, "institutional release review remains open")
    checks.equal(license_state["third_party_institutional_review_complete"], False, "third-party review remains open")
    checks.equal(license_state["distribution_authorized"], False, "license state does not authorize distribution")

    reply_receipt = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_RESPONSIBLE_AUTHOR_ONE_REPLY_PACKET_VERIFICATION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        reply_receipt["decision"],
        "PASS_PRIVACY_SAFE_ONE_REPLY_PACKET_GENERATED_OWNER_CONFIRMATION_PENDING",
        "responsible-author reply packet decision",
    )
    checks.equal(reply_receipt["missing_field_count"], 6, "reply packet missing-field count")
    checks.equal(reply_receipt["validation_error_count"], 0, "reply packet validation errors")
    checks.equal(
        set(reply_receipt["missing_field_paths"]),
        {
            "declarations.ai_assistance_statement_approved=true",
            "declarations.ai_tool_version_and_use_dates",
            "declarations.competing_interests_statement",
            "declarations.institutional_manuscript_approval_evidence",
            "declarations.institutional_manuscript_approval_status=APPROVED",
            "project_license.release_review_status=APPROVED",
        },
        "exact current owner-input deficit",
    )
    for resolved_path in (
        "authorship.affiliations[0].department",
        "authorship.corresponding_author_name",
        "authorship.corresponding_author_email",
    ):
        checks.equal(resolved_path in reply_receipt["missing_field_paths"], False, f"owner-supplied field resolved: {resolved_path}")
    checks.equal(reply_receipt["personal_values_emitted"], False, "reply packet privacy boundary")
    checks.equal(reply_receipt["submission_authorized"], False, "reply packet does not authorize submission")
    reply_packet = (ROOT / reply_receipt["packet_path"]).read_text(encoding="utf-8")
    checks.equal(hashlib.sha256(reply_packet.encode("utf-8")).hexdigest(), reply_receipt["packet_sha256"], "reply packet hash")
    checks.true("@" not in reply_packet, "tracked reply packet contains no email value")

    ai_dates = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_AI_TOOL_DATE_EVIDENCE.json").read_text(encoding="utf-8")
    )
    checks.equal(
        ai_dates["decision"],
        "PASS_EVIDENCE_BOUNDED_AI_TOOL_USE_CONFIRMED_BY_DATE_EXACT_RANGE_PENDING",
        "AI-tool date evidence decision",
    )
    checks.equal(ai_dates["routing_record"]["recorded_date"], "2026-09-11", "routing record date")
    checks.equal(
        ai_dates["routing_record"]["proves_actual_use_on_that_date"],
        False,
        "routing date is not promoted to an actual use date",
    )
    checks.equal(
        ai_dates["joint_evidence_boundary"]["both_model_families_have_retained_use_evidence_by"],
        "2026-09-12",
        "both retained model-use records exist by date",
    )
    checks.equal(ai_dates["joint_evidence_boundary"]["is_actual_first_use_date"], False, "first use remains unknown")
    checks.equal(ai_dates["joint_evidence_boundary"]["is_complete_use_range"], False, "complete use range remains unknown")
    checks.equal(ai_dates["declaration_fields"]["actual_first_use_date"], None, "actual first-use date not guessed")
    checks.equal(ai_dates["declaration_fields"]["actual_last_use_date"], None, "actual last-use date not guessed")
    checks.equal(ai_dates["declaration_fields"]["author_confirmation_required"], True, "author date confirmation retained")
    checks.equal(ai_dates["p0_i_closed"], False, "bounded date evidence does not close P0-I")
    checks.equal(ai_dates["submission_authorized"], False, "bounded date evidence does not authorize submission")

    session_metadata = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_AI_TOOL_SESSION_METADATA.json").read_text(encoding="utf-8")
    )
    checks.equal(
        session_metadata["decision"],
        "PASS_LOCAL_CODEX_TURN_CONTEXT_METADATA_START_BOUND_END_DATE_PENDING",
        "local Codex session-metadata decision",
    )
    checks.equal(session_metadata["snapshot_cutoff_utc"], "2026-09-15T03:32:41.264Z", "session metadata cutoff")
    scope = session_metadata["selection_scope"]
    checks.equal(scope["session_files_scanned"], 115, "pre-cutoff local session files scanned")
    checks.equal(scope["selected_session_files"], 6, "ReliableRAG project-task sessions selected")
    checks.equal(scope["selected_session_identifiers_emitted"], False, "session identifiers not emitted")
    checks.equal(scope["absolute_paths_emitted"], False, "absolute session paths not emitted")
    checks.equal(scope["message_response_or_tool_content_inspected"], False, "message and tool content not inspected")
    checks.equal(session_metadata["target_turn_context_count"], 379, "target model turn-context count")
    astra_metadata = session_metadata["models"]["gpt-6-astra"]
    sol_metadata = session_metadata["models"]["gpt-5.6-sol"]
    checks.equal(astra_metadata["turn_context_count"], 62, "Astra turn-context count")
    checks.equal(astra_metadata["reasoning_effort_counts"], {"high": 3, "xhigh": 59}, "Astra reasoning levels")
    checks.equal(astra_metadata["first_observed_asia_shanghai_date"], "2026-09-10", "Astra first observed date")
    checks.equal(sol_metadata["turn_context_count"], 317, "Sol turn-context count")
    checks.equal(sol_metadata["reasoning_effort_counts"], {"high": 317}, "Sol reasoning level")
    checks.equal(sol_metadata["first_observed_asia_shanghai_date"], "2026-09-11", "Sol first observed date")
    observation = session_metadata["project_task_observation"]
    checks.equal(observation["first_observed_asia_shanghai_date"], "2026-09-10", "project-task AI start date")
    checks.equal(observation["last_observed_asia_shanghai_date"], "2026-09-15", "project-task last observed date")
    checks.equal(observation["last_observed_date_is_final_use_date"], False, "last observation is not final use")
    declaration = session_metadata["declaration_boundary"]
    checks.equal(declaration["final_use_end_date"], None, "final AI use date remains unset")
    checks.equal(declaration["date_bounded_declaration_complete"], False, "AI date declaration remains incomplete")
    checks.equal(declaration["author_approval_still_required"], True, "AI statement still needs author approval")
    checks.equal(session_metadata["p0_i_closed"], False, "session metadata does not close P0-I")
    checks.equal(session_metadata["submission_authorized"], False, "session metadata does not authorize submission")

    ai_policy = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_SPRINGER_NATURE_AI_POLICY_ALIGNMENT.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        ai_policy["decision"],
        "PARTIAL_PASS_CURRENT_SPRINGER_NATURE_AI_POLICY_MAPPED_AUTHOR_APPROVAL_FINAL_DATE_AND_ARTIFACT_OPEN",
        "current Springer Nature AI policy mapping decision",
    )
    checks.equal(ai_policy["accessed_date"], "2026-09-15", "AI policy access date")
    checks.equal(len(ai_policy["sources"]), 5, "AI policy source count")
    checks.equal(ai_policy["policy_application"]["copy_editing_only_exception_applies"], False, "copy-editing exception rejected")
    checks.equal(ai_policy["policy_application"]["journal_specific_methods_documentation_required"], True, "Methods disclosure required")
    checks.equal(ai_policy["policy_application"]["prompt_scope_required"], True, "prompt scope disclosure required")
    checks.equal(ai_policy["candidate_revision"]["previous_candidate_is_complete_for_current_policy"], False, "old AI candidate incomplete")
    checks.equal(ai_policy["candidate_revision"]["revised_candidate_covers_prompt_categories"], True, "new candidate covers prompt categories")
    checks.equal(ai_policy["candidate_revision"]["revised_candidate_claims_verbatim_complete_prompt_transcript"], False, "no verbatim-transcript overclaim")
    checks.equal(ai_policy["candidate_revision"]["responsible_author_approval"], False, "AI candidate unapproved")
    checks.equal(ai_policy["candidate_revision"]["final_use_end_date"], None, "final AI end date unset")
    checks.equal(ai_policy["synthetic_target_validation"]["compiled_pages"], 13, "policy-aligned synthetic pages")
    checks.equal(ai_policy["synthetic_target_validation"]["all_pages_visually_reviewed"], True, "policy-aligned synthetic visual review")
    checks.equal(ai_policy["synthetic_target_validation"]["visual_defects_found"], 0, "policy-aligned synthetic visual defects")
    checks.equal(ai_policy["synthetic_target_validation"]["real_owner_package_built"], False, "policy test builds no real owner package")
    checks.equal(ai_policy["p0_i_closed"], False, "AI policy alignment does not close P0-I")
    checks.equal(ai_policy["submission_authorized"], False, "AI policy alignment does not authorize submission")

    prompt_record = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_AI_PROMPT_RECORD.json").read_text(encoding="utf-8")
    )
    checks.equal(
        prompt_record["decision"],
        "PASS_PRIVATE_REDACTED_ROOT_USER_PROMPT_LEDGER_SNAPSHOT_FINAL_RANGE_AND_AUTHOR_RELEASE_OPEN",
        "private prompt-record snapshot decision",
    )
    checks.equal(prompt_record["snapshot_cutoff_utc"], "2026-09-15T04:18:53.028Z", "prompt snapshot cutoff")
    prompt_scope = prompt_record["selection_scope"]
    checks.equal(prompt_scope["root_user_sessions_selected"], 1, "one root user session selected")
    checks.equal(prompt_scope["subagent_sessions_excluded"], True, "subagent sessions excluded from prompt record")
    checks.equal(prompt_scope["retained_user_prompt_chunks"], 47, "retained user prompt chunks")
    checks.equal(prompt_scope["unique_exact_user_prompt_hashes"], 37, "unique user prompt hashes")
    checks.equal(prompt_scope["raw_prompt_characters"], 9785, "raw user prompt characters")
    checks.equal(
        prompt_scope["automatic_context_chunk_counts"],
        {"<codex_internal_context": 269, "<recommended_plugins>": 7, "<environment_context>": 17},
        "automatic context chunks excluded",
    )
    prompt_privacy = prompt_record["privacy_and_integrity"]
    checks.equal(prompt_privacy["private_ledger_contains_complete_unredacted_prompt_set"], False, "no complete raw prompt copy")
    checks.equal(prompt_privacy["unaffected_prompt_chunks_may_remain_verbatim"], True, "verbatim private chunks disclosed")
    checks.equal(prompt_privacy["private_ledger_is_anonymous"], False, "private ledger is not called anonymous")
    checks.equal(prompt_privacy["redaction_is_identity_minimization_not_anonymization"], True, "redaction scope is bounded")
    checks.equal(prompt_privacy["public_receipt_contains_prompt_text"], False, "public receipt emits no prompt text")
    prompt_boundary = prompt_record["disclosure_boundary"]
    checks.equal(prompt_boundary["snapshot_is_final_project_use_range"], False, "prompt snapshot is not final range")
    checks.equal(prompt_boundary["responsible_author_content_review_complete"], False, "prompt record awaits author review")
    checks.equal(prompt_boundary["responsible_author_release_approval"], False, "prompt release awaits author approval")
    checks.equal(prompt_boundary["editor_requested_or_approved_access_route"], False, "prompt editor route open")
    checks.equal(prompt_record["p0_i_closed"], False, "prompt record does not close P0-I")
    checks.equal(prompt_record["submission_authorized"], False, "prompt record does not authorize submission")

    current_build_gate = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_CURRENT_PRIVATE_BUILD_GATE_VERIFICATION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        current_build_gate["decision"],
        "PASS_OWNER_INPUT_GATE_REJECTS_BEFORE_TRANSPORT_OR_OUTPUT",
        "current private owner input fails before transport or output",
    )
    checks.equal(current_build_gate["input_scope"], "LOCAL_GIT_IGNORED_OWNER_INPUT", "current private gate input scope")
    checks.equal(current_build_gate["input_matches_empty_template"], False, "current owner input is not empty template")
    checks.equal(current_build_gate["missing_field_count"], 6, "current private gate missing fields")
    checks.equal(current_build_gate["validation_error_count"], 0, "current private gate validation errors")
    checks.equal(current_build_gate["transport_access_attempted"], False, "current private gate does not access transport")
    checks.equal(current_build_gate["output_created"], False, "current private gate creates no output")
    checks.equal(current_build_gate["author_populated_package_built"], False, "current private gate builds no package")
    checks.equal(current_build_gate["private_values_emitted"], False, "current private gate emits no values")
    checks.equal(current_build_gate["private_input_hash_emitted"], False, "current private gate emits no input hash")
    checks.equal(current_build_gate["submission_authorized"], False, "current private gate does not authorize submission")

    correction = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_REQUIRED_OWNER_FIELDS_CORRECTION.json").read_text(
            encoding="utf-8"
        )
    )
    checks.equal(
        correction["decision"],
        "PASS_APPLIED_INTELLIGENCE_OWNER_GATE_CORRECTION_19_REAL_MISSING_ZERO_ERRORS",
        "official requirement correction decision",
    )
    checks.equal(correction["correction"]["prior_snapshot_missing_fields"], 30, "prior snapshot count")
    checks.equal(correction["correction"]["current_real_missing_fields"], 19, "current real missing count")
    checks.equal(correction["correction"]["current_validation_errors"], 0, "current validation error count")
    checks.equal(correction["correction"]["net_missing_field_reduction"], 11, "missing-field correction size")
    checks.equal(correction["historical_private_builder_snapshot_mutated"], False, "historical snapshot preserved")
    checks.equal(correction["real_owner_values_emitted"], False, "correction emits no owner values")
    checks.equal(correction["real_private_package_built"], False, "correction does not build private package")
    checks.equal(correction["submission_authorized"], False, "correction does not authorize submission")

    workflow = (ROOT / ".github" / "workflows" / "public-reporting-audit.yml").read_text(encoding="utf-8")
    for phrase in (
        "permissions:\n  contents: read",
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
        "python scripts/verify_cas_q3_public_reporting_surface.py",
        "python scripts/verify_cas_q3_applied_intelligence_preflight.py",
        "python scripts/verify_cas_q3_template_route_resolution.py",
        "python scripts/verify_cas_q3_hbut_cas_edition_secondary_evidence.py",
        "python scripts/verify_cas_q3_applied_intelligence_public_corroboration.py",
        "python scripts/verify_cas_q3_institutional_cas_record.py --check-template",
        "python scripts/verify_cas_q3_institutional_release_record.py --check-template",
        "python scripts/verify_cas_q3_external_closure_inputs.py --check-templates",
        "python scripts/verify_cas_q3_current_private_build_gate.py --check-template",
        "python scripts/verify_cas_q3_license_state.py",
        "tests.test_cas_q3_institutional_cas_record",
        "tests.test_cas_q3_institutional_release_record",
        "tests.test_cas_q3_external_closure_inputs",
        "tests.test_cas_q3_private_closure_workspace",
        "tests.test_cas_q3_current_private_build_gate",
        "tests.test_cas_q3_original_fit_receipt_census",
        "tests.test_cas_q3_external_closure_evidence_census",
        "tests.test_cas_q3_oversized_external_closure_evidence",
        "tests.test_cas_q3_pdf_external_closure_evidence",
        "tests.test_cas_q3_document_container_inventory",
        "tests.test_cas_q3_applied_intelligence_preflight",
        "tests.test_cas_q3_applied_intelligence_transport",
        "tests.test_cas_q3_applied_intelligence_private_submission",
        "tests.test_cas_q3_private_submission_packet",
        "tests.test_cas_q3_ai_tool_date_evidence",
        "tests.test_cas_q3_codex_session_metadata",
        "tests.test_cas_q3_springer_ai_policy_alignment",
        "tests.test_cas_q3_ai_prompt_record",
        "tests.test_cas_q3_owner_reply_packet",
        "python scripts/verify_cas_q3_submission_readiness.py --ignore-local-owner-inputs",
        "git diff --exit-code",
    ):
        checks.true(phrase in workflow, f"public CI boundary: {phrase}")
    for forbidden in (
        "python scripts/verify_cas_q3_claim_statistics.py",
        "python scripts/verify_cas_q3_historical_manifest_archive_recovery.py",
        "tests.test_cas_q3_aggregate_release",
        "tests.test_cas_q3_licensed_release",
    ):
        checks.true(forbidden not in workflow, f"private-input command excluded from public CI: {forbidden}")
    ci_acceptance = (ROOT / "docs" / "cas_q3" / "P1_E_PUBLIC_REPORTING_CI.md").read_text(encoding="utf-8")
    for run_id in (
        "34929458917",
        "34929463056",
        "34929268521",
        "34929271440",
        "34928736267",
        "34928739266",
        "34927816944",
        "34927820531",
        "34820858483",
        "34820862475",
        "34817939287",
        "34817942528",
        "34814508417",
        "34814511106",
        "34814218658",
        "34814221769",
        "34813538336",
        "34813542720",
        "34812422447",
        "34812424983",
        "34812220477",
        "34812222762",
        "34807538106",
        "34807539860",
        "34806236165",
        "34806238427",
        "34806104442",
        "34806106663",
        "34804142574",
        "34804144674",
        "34801833707",
        "34801836852",
        "34801428340",
        "34801428452",
    ):
        checks.true(run_id in ci_acceptance, f"public CI run retained: {run_id}")

    manifest_recovery = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.json").read_text(encoding="utf-8")
    )
    checks.equal(
        manifest_recovery["decision"],
        "PARTIAL_PASS_LOCALLY_PRESERVED_MARS_MANIFEST_BYTE_COPY_RECOVERED_NO_INDEPENDENT_TIMESTAMP_OR_FIT_RECEIPTS",
        "historical manifest recovery decision",
    )
    checks.equal(manifest_recovery["current_manifest"]["byte_identical_to_embedded_manifest"], True, "historical manifest byte identity")
    checks.equal(manifest_recovery["evidence_interpretation"]["independent_pre_roa_timestamp_proved"], False, "historical timestamp is not overclaimed")
    checks.equal(manifest_recovery["evidence_interpretation"]["independent_original_fit_witness_recovered"], False, "independent original-fit witness remains missing")
    manifest_verification = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_VERIFICATION.json").read_text(encoding="utf-8")
    )
    checks.equal(manifest_verification["decision"], "PASS_BOUNDED_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_VERIFICATION", "historical manifest verifier passes")
    checks.equal(manifest_verification["checks"], 30, "historical manifest verifier check count")
    checks.equal(
        manifest_verification["full_historical_content_search_reperformed"],
        False,
        "bounded verifier does not claim an exhaustive historical-content search",
    )
    receipt_census = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_E_ORIGINAL_FIT_RECEIPT_CENSUS.json").read_text(encoding="utf-8")
    )
    checks.equal(
        receipt_census["decision"],
        "PASS_BOUNDED_ACCESSIBLE_HISTORICAL_RECEIPT_CENSUS_NO_RECOVERY",
        "bounded original-fit receipt census decision",
    )
    checks.equal(receipt_census["counts"]["filesystem_files_scanned"], 55373, "receipt census file count")
    checks.equal(receipt_census["counts"]["candidate_text_files_scanned"], 1770, "receipt census metadata count")
    checks.equal(receipt_census["counts"]["zip_archives_scanned"], 37, "receipt census ZIP count")
    checks.equal(receipt_census["counts"]["exact_original_model_hash_copies"], 14, "receipt census exact model copies")
    checks.equal(receipt_census["counts"]["candidate_files_with_receipt_markers_and_model_identity"], 0, "no filesystem receipt candidate")
    checks.equal(receipt_census["counts"]["candidate_archive_members_with_receipt_markers_and_model_identity"], 0, "no archive receipt candidate")
    checks.equal(receipt_census["counts"]["scan_errors"], 0, "receipt census scan errors")
    checks.equal(sorted(receipt_census["exact_models_by_root"]), ["original_workspace", "static_original"], "only original and static-copy model sets found")
    checks.equal(receipt_census["interpretation"]["third_independent_model_copy_found"], False, "no third independent model copy")
    checks.equal(receipt_census["interpretation"]["independent_original_fit_witness_recovered"], False, "receipt census recovers no independent fit witness")
    checks.equal(receipt_census["interpretation"]["absence_outside_scanned_roots_proved"], False, "receipt census remains bounded")
    checks.equal(receipt_census["operations"]["scientific_fits"], 0, "receipt census performs no fit")

    release = evidence["aggregate_release_candidate"]
    archive = Path(release["local_archive"])
    checks.true(archive.is_file(), "withheld aggregate archive exists locally")
    checks.equal(digest(archive), release["archive_sha256"], "aggregate archive external pin")
    with zipfile.ZipFile(archive) as bundle:
        checks.equal(len(bundle.infolist()), release["archive_members"], "aggregate archive members")
        manifest = bundle.read("MANIFEST.json")
        checks.equal(hashlib.sha256(manifest).hexdigest(), release["manifest_sha256"], "aggregate manifest pin")
        manifest_json = json.loads(manifest)
        checks.equal(manifest_json["distribution_authorized"], False, "archive distribution gate")
        checks.equal(manifest_json["project_license"], "PENDING_OWNER_SELECTION", "archive license gate")

    licensed = evidence["licensed_aggregate_release_candidate_v2"]
    licensed_archive = Path(licensed["local_archive"])
    checks.true(licensed_archive.is_file(), "licensed V2 aggregate archive exists locally")
    checks.equal(digest(licensed_archive), licensed["archive_sha256"], "licensed V2 archive external pin")
    with zipfile.ZipFile(licensed_archive) as bundle:
        checks.equal(len(bundle.infolist()), licensed["archive_members"], "licensed V2 archive members")
        manifest = bundle.read("MANIFEST.json")
        checks.equal(hashlib.sha256(manifest).hexdigest(), licensed["manifest_sha256"], "licensed V2 manifest pin")
        manifest_json = json.loads(manifest)
        checks.equal(manifest_json["distribution_authorized"], False, "licensed V2 distribution gate")
        checks.equal(manifest_json["project_license"], "Apache-2.0", "licensed V2 license")
        checks.equal(
            manifest_json["project_license_scope"],
            ["scripts/verify_cas_q3_claim_statistics.py", "scripts/empirical_analysis_math.py"],
            "licensed V2 exact code scope",
        )
        checks.equal(manifest_json["non_code_members_not_relicensed_by_project_code_license"], True, "licensed V2 documentation boundary")

    target_transport = evidence["applied_intelligence_private_transport_candidate"]
    checks.equal(
        target_transport["archive_sha256"],
        current_transport_result["archive_sha256"],
        "refreshed target transport and external map archive pin",
    )
    checks.equal(
        target_transport["clean_compile_pdf_sha256"],
        current_transport_result["clean_compile_pdf_sha256"],
        "refreshed target transport and external map compiled PDF pin",
    )
    checks.equal(
        target_transport["historical_archive_sha256"],
        transport_result["archive_sha256"],
        "external map preserves historical transport pin",
    )
    checks.equal(
        target_transport["smallcondensed_equivalence_proved"],
        False,
        "external target transport does not overclaim legacy equivalence",
    )
    target_archives = [Path(target_transport["first_build"]), Path(target_transport["second_build"])]
    target_bytes = []
    for index, target_archive in enumerate(target_archives, start=1):
        checks.true(target_archive.is_file(), f"target transport build {index} exists locally")
        checks.equal(digest(target_archive), target_transport["archive_sha256"], f"target transport build {index} hash")
        target_bytes.append(target_archive.read_bytes())
        with zipfile.ZipFile(target_archive) as bundle:
            checks.equal(bundle.namelist(), target_transport["archive_members"], f"target transport build {index} members")
            checks.equal(
                hashlib.sha256(bundle.read("sn-jnl.cls")).hexdigest(),
                target_transport["sn_jnl_class_sha256"],
                f"target transport build {index} class pin",
            )
            checks.equal(
                hashlib.sha256(bundle.read("sn-basic.bst")).hexdigest(),
                target_transport["sn_basic_bst_sha256"],
                f"target transport build {index} bibliography-style pin",
            )
    checks.equal(target_bytes[0], target_bytes[1], "two target transport builds are byte-identical")
    checks.equal(target_transport["submission_authorized"], False, "external target transport submission gate")
    checks.equal(target_transport["distribution_authorized"], False, "external target transport distribution gate")

    synthetic = evidence["applied_intelligence_private_submission_synthetic_candidate"]
    current_synthetic = policy_refresh["current_synthetic_private_build"]
    for key in ("source_archive_sha256", "compiled_pdf_sha256", "cover_letter_sha256"):
        checks.equal(
            synthetic[key],
            current_synthetic[key],
            f"refreshed synthetic private result and map pin: {key}",
        )
    synthetic_root = Path(synthetic["directory"])
    checks.true(synthetic_root.is_dir(), "synthetic private target directory exists")
    for name_key, hash_key in (
        ("source_archive", "source_archive_sha256"),
        ("compiled_pdf", "compiled_pdf_sha256"),
        ("cover_letter", "cover_letter_sha256"),
    ):
        artifact = synthetic_root / synthetic[name_key]
        checks.true(artifact.is_file(), f"synthetic private artifact exists: {name_key}")
        checks.equal(digest(artifact), synthetic[hash_key], f"synthetic private artifact pin: {name_key}")
    private_receipt_path = synthetic_root / synthetic["receipt"]
    checks.true(private_receipt_path.is_file(), "synthetic private receipt exists")
    private_receipt = json.loads(private_receipt_path.read_text(encoding="utf-8"))
    checks.equal(
        private_receipt["decision"],
        "PASS_PRIVATE_APPLIED_INTELLIGENCE_AUTHOR_POPULATED_CANDIDATE_FINAL_AUDITS_OPEN",
        "synthetic private receipt decision",
    )
    checks.equal(private_receipt["personal_values_in_receipt"], False, "synthetic private receipt privacy")
    checks.equal(private_receipt["submission_authorized"], False, "synthetic private receipt submission gate")
    checks.equal(synthetic["compiled_pages"], 13, "refreshed synthetic page count")
    checks.equal(synthetic["visual_review"], "PASS_PROJECT_LEAD_ALL_13_PAGES_110_DPI", "refreshed synthetic visual review")
    checks.equal(current_synthetic["pages_visually_inspected"], 13, "refreshed synthetic inspected pages")
    checks.equal(current_synthetic["visual_defects"], 0, "refreshed synthetic visual defects")
    checks.equal(current_synthetic["synthetic_values_only"], True, "refreshed synthetic-only boundary")
    checks.equal(current_synthetic["real_owner_package_built"], False, "refreshed synthetic is not real package")

    ai_synthetic = evidence["applied_intelligence_ai_policy_synthetic_candidate"]
    checks.equal(
        ai_synthetic["compiled_pdf_sha256"],
        ai_policy["synthetic_target_validation"]["compiled_pdf_sha256"],
        "AI-policy synthetic map and audit PDF pin",
    )
    ai_synthetic_root = Path(ai_synthetic["directory"])
    checks.true(ai_synthetic_root.is_dir(), "AI-policy synthetic target directory exists")
    for name, expected_hash in (
        ("applied_intelligence_author_populated_source.zip", ai_synthetic["source_archive_sha256"]),
        ("manuscript.pdf", ai_synthetic["compiled_pdf_sha256"]),
        ("cover_letter.md", ai_synthetic["cover_letter_sha256"]),
    ):
        path = ai_synthetic_root / name
        checks.true(path.is_file(), f"AI-policy synthetic artifact exists: {name}")
        checks.equal(digest(path), expected_hash, f"AI-policy synthetic artifact pin: {name}")
    checks.equal(ai_synthetic["compiled_pages"], 13, "AI-policy synthetic page count")
    checks.equal(ai_synthetic["nonembedded_fonts"], 0, "AI-policy synthetic embedded fonts")
    checks.equal(ai_synthetic["type3_fonts"], 0, "AI-policy synthetic Type 3 fonts")
    checks.equal(ai_synthetic["all_pages_visually_reviewed"], True, "AI-policy synthetic complete visual review")
    checks.equal(ai_synthetic["visual_defects_found"], 0, "AI-policy synthetic visual defects")
    checks.equal(ai_synthetic["synthetic_identity_only"], True, "AI-policy synthetic identity boundary")
    checks.equal(ai_synthetic["real_owner_package_built"], False, "AI-policy synthetic is not real owner package")
    checks.equal(ai_synthetic["submission_authorized"], False, "AI-policy synthetic submission gate")

    static_delivery = json.loads((ROOT / evidence["private_transport"]["static_delivery_receipt"]).read_text(encoding="utf-8"))
    checks.equal(static_delivery["status"], "PASS_DECLARED_STATIC_TRANSPORT_AND_RESTORATION_ONLY", "static delivery scope")
    checks.equal(static_delivery["complete_pipeline_delivered"], False, "static delivery is not full pipeline")
    checks.equal(static_delivery["archive"]["sha256"], evidence["private_transport"]["static_archive_sha256"], "static archive recorded pin")
    checks.equal(static_delivery["external_archive"]["sha256"], evidence["private_transport"]["pretrained_archive_sha256"], "pretrained archive recorded pin")
    replay = json.loads((ROOT / evidence["private_transport"]["roa_replay_receipt"]).read_text(encoding="utf-8"))
    checks.equal(replay["release_status"], "PASS_SAME_HOST_SOURCE_AND_DATA_RELOCATION", "saved-parameter relocation scope")
    checks.equal(replay["other_host_or_OS_tested"], False, "no another-host claim")
    checks.equal(replay["private_review_archive"]["sha256"], evidence["private_transport"]["roa_archive_sha256"], "ROA archive recorded pin")

    manuscript = (ROOT / "docs" / "cas_q3" / "REVIEWER_EVIDENCE_MAP.md").read_text(encoding="utf-8")
    normalized_manuscript = " ".join(manuscript.split())
    for phrase in (
        "does not pass against `HGB_ONLY_R`",
        "does not establish advancement",
        "does not authorize distribution",
        "The V1 archive preserves the historical arithmetic witness",
        "Neither archive has a DOI or distribution authorization",
        "An independently certified timestamp, original-fit authentication",
        "Six evidence lanes",
        "CAS Q3 STATUS: NOT READY",
    ):
        checks.true(phrase in normalized_manuscript, f"map boundary phrase: {phrase}")

    cost_failure = (ROOT / "docs" / "cas_q3" / "REVIEWER_COST_FAILURE_REGISTER.md").read_text(encoding="utf-8")
    for phrase in (
        "51,901,556 prompt tokens",
        "8,534 NLI forwards over 42,946",
        "not 5% of retrieval, generation, scoring",
        "Standalone HGB-only, GbV-only and fusion deployment timing",
        "FAIL_P0_1_PHI_DEVELOPMENT_AUTHENTICITY",
        "STOP_MISTRAL_EXTENSION_BEFORE_ENGINEERING",
        "C3 validation V1/V2",
        "Aggregate release candidate V1",
    ):
        checks.true(phrase in cost_failure, f"cost/failure boundary phrase: {phrase}")

    result = {
        "schema_version": 1,
        "decision": "PASS_REVIEWER_EVIDENCE_MAP_WITH_EXTERNAL_RELEASE_GATES",
        "checks": checks.count,
        "repository_records": len(evidence["repository_evidence"]),
        "aggregate_archive_sha256": release["archive_sha256"],
        "licensed_aggregate_v2_archive_sha256": licensed["archive_sha256"],
        "applied_intelligence_transport_archive_sha256": target_transport["archive_sha256"],
        "aggregate_distribution_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }
    RECEIPT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
