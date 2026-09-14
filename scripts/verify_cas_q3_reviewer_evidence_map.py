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
    checks.equal(static_receipt["check_count"], 139, "static manuscript checks")
    checks.equal(static_receipt["abstract_word_count"], 155, "Applied Intelligence abstract words")
    checks.equal(static_receipt["bibliography_entries"], 22, "bibliography entries")
    length_receipt = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_MANUSCRIPT_LENGTH_VERIFICATION.json").read_text(encoding="utf-8")
    )
    checks.equal(length_receipt["decision"], "PASS_REPRODUCIBLE_LENGTH_PROXY_WITH_APPLIED_INTELLIGENCE_ABSTRACT_RANGE", "length audit decision")
    checks.equal(length_receipt["pdf_tokens_before_references"], 3994, "pre-reference PDF token proxy")
    checks.equal(length_receipt["pdf_tokens_full_document"], 4691, "full PDF token proxy")
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
        applied_preflight["artifacts"]["pdf_sha256"],
        "target transport recompiles to accepted preflight PDF bytes",
    )
    checks.equal(
        applied_transport["official_source_findings"]["journal_specific_equivalence_from_sn_jnl_to_smallcondensed_proved"],
        False,
        "legacy smallcondensed discrepancy retained",
    )
    checks.equal(applied_transport["submission_authorized"], False, "target transport does not authorize submission")
    checks.equal(applied_transport["distribution_authorized"], False, "target transport remains private")

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
    checks.equal(hbut_request["p0_g_closed"], False, "request does not close P0-G")
    checks.equal(hbut_request["p0_h_closed"], False, "request does not close P0-H")
    checks.equal(hbut_request["p0_i_closed"], False, "request does not close P0-I")
    checks.equal(hbut_request["submission_authorized"], False, "request does not authorize submission")

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
    checks.equal(reply_receipt["missing_field_count"], 19, "reply packet missing-field count")
    checks.equal(reply_receipt["validation_error_count"], 0, "reply packet validation errors")
    checks.equal(reply_receipt["personal_values_emitted"], False, "reply packet privacy boundary")
    checks.equal(reply_receipt["submission_authorized"], False, "reply packet does not authorize submission")
    reply_packet = (ROOT / reply_receipt["packet_path"]).read_text(encoding="utf-8")
    checks.equal(hashlib.sha256(reply_packet.encode("utf-8")).hexdigest(), reply_receipt["packet_sha256"], "reply packet hash")
    checks.true("@" not in reply_packet, "tracked reply packet contains no email value")

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
        "python scripts/verify_cas_q3_license_state.py",
        "tests.test_cas_q3_applied_intelligence_preflight",
        "tests.test_cas_q3_applied_intelligence_transport",
        "tests.test_cas_q3_applied_intelligence_private_submission",
        "tests.test_cas_q3_private_submission_packet",
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
        transport_result["archive_sha256"],
        "target transport result and external map archive pin",
    )
    checks.equal(
        target_transport["clean_compile_pdf_sha256"],
        transport_result["clean_compile_pdf_sha256"],
        "target transport result and external map compiled PDF pin",
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
    for key in ("source_archive_sha256", "compiled_pdf_sha256", "cover_letter_sha256"):
        checks.equal(
            synthetic[key],
            private_builder["synthetic_private_build"][key],
            f"synthetic private result and map pin: {key}",
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
