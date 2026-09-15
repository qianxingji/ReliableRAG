#!/usr/bin/env python3
"""Verify the bounded public corroboration record without making network calls."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs" / "cas_q3" / "P0_H_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION.json"
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_H_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION_VERIFICATION.json"


def main() -> int:
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    checks: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)
        checks.append(message)

    require(data["schema_version"] == 1, "supported schema")
    require(
        data["decision"]
        == "PARTIAL_PASS_PUBLIC_2025_MAJOR_Q3_CORROBORATION_INSTITUTIONAL_RECORD_STILL_REQUIRED",
        "bounded decision",
    )
    require(data["cas_q3_status"] == "NOT_READY", "fail-closed project status")
    target = data["target_identity"]
    require(target["journal_title"] == "Applied Intelligence", "current title")
    require(target["print_issn"] == "0924-669X", "print ISSN")
    require(target["electronic_issn"] == "1573-7497", "electronic ISSN")
    rule = data["owner_rule"]
    require(rule["category_basis"] == "MAJOR", "owner major-category basis")
    require(rule["category_name"] == "Computer Science", "owner category")
    require(rule["qualifying_tiers"] == ["Q1", "Q2", "Q3"], "Q3-or-better tiers")
    sources = data["sources"]
    cas = sources["official_cas_landing"]
    require(cas["observed_2025_upgraded_edition_listed"] is True, "official 2025 availability")
    require(cas["journal_record_publicly_retrieved"] is False, "official journal record remains missing")
    require(cas["detailed_record_requires_authenticated_or_institutional_access"] is True, "official access boundary")
    xhu = sources["xihua_university_faculty_page"]
    require(xhu["direct_fetch_status"] == 412, "direct-fetch failure retained")
    require(xhu["excerpt_binds_print_issn"] is True, "secondary excerpt binds print ISSN")
    require(xhu["excerpt_labels_2025_applied_intelligence_item_major_q3"] is True, "secondary major-Q3 label")
    require(xhu["edition_year_explicitly_authenticated"] is False, "secondary edition not overclaimed")
    require(xhu["accepted_as_hbut_institutional_record"] is False, "secondary page is not HBUT authority")
    shufe = sources["shufe_library_navigation"]
    require(shufe["single_cas_label"] == "Q4", "condensed Q4 label retained")
    require(shufe["major_minor_category_context_explicit"] is False, "Q4 category ambiguity retained")
    require(shufe["treated_as_unresolved_category_ambiguity"] is True, "no unsupported conflict resolution")
    details = sources["public_detail_pages"]
    require(len(details) == 2, "two public detail sources")
    for index, source in enumerate(details, start=1):
        require(source["source_role"] == "NONAUTHORITATIVE_PUBLIC_CORROBORATION", f"source {index} authority boundary")
        require(source["edition"] == "2025 March upgraded edition", f"source {index} edition")
        require(source["major_category"] == "Computer Science", f"source {index} major category")
        require(source["major_tier"] == "Q3", f"source {index} major tier")
        require(source["minor_tier"] == "Q4", f"source {index} minor tier")
    bounded = data["bounded_interpretation"]
    require(bounded["public_sources_support_2025_major_category_q3"] is True, "public major-Q3 support")
    require(bounded["public_sources_support_2025_minor_category_q4"] is True, "public minor-Q4 support")
    require(bounded["shufe_single_q4_label_proved_to_be_minor_category"] is False, "ambiguous Q4 not reclassified")
    require(bounded["institution_recognized_edition_year_confirmed"] is False, "institutional edition remains open")
    require(bounded["hbut_current_title_issn_record_retained"] is False, "HBUT record remains open")
    require(bounded["p0_h_closed"] is False, "P0-H remains open")
    require(len(data["required_closure_evidence"]) == 5, "closure evidence list")
    require(data["submission_authorized"] is False, "submission remains unauthorized")

    result = {
        "schema_version": 1,
        "decision": "PASS_BOUNDED_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION_VERIFICATION",
        "checks": len(checks),
        "public_major_category_q3_supported": True,
        "institution_recognized_record_retained": False,
        "p0_h_closed": False,
        "submission_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
