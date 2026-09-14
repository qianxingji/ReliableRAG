#!/usr/bin/env python3
"""Verify bounded HBUT secondary evidence about the CAS report-year rule."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "cas_q3" / "P0_H_HBUT_CAS_EDITION_RULE_SECONDARY_EVIDENCE.json"
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_H_HBUT_CAS_EDITION_RULE_SECONDARY_EVIDENCE_VERIFICATION.json"


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    checks = 0

    def require(condition: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(label)

    require(
        data["decision"]
        == "PARTIAL_PASS_OFFICIAL_HBUT_COLLEGE_PREVIOUS_YEAR_CAS_RULE_FOUND_UNIVERSITY_WIDE_CONFIRMATION_PENDING",
        "bounded decision",
    )
    require(data["cas_q3_status"] == "NOT_READY", "CAS status")
    require(data["official_source"]["url"].startswith("https://lxy.hbut.edu.cn/"), "official HBUT source")
    require("上一年度" in data["official_source"]["verified_observation"], "previous-year observation")
    scope = data["evidence_scope"]
    require(scope["official_hbut_subdomain"] is True, "official subdomain")
    require(scope["college_training_plan"] is True, "college-plan scope")
    require(scope["central_research_administration_policy"] is False, "not central policy")
    require(scope["previous_publication_year_rule_observed"] is True, "previous-year rule observed")
    require(scope["rule_proved_university_wide_for_faculty_research_recognition"] is False, "university-wide rule not claimed")
    require(scope["applied_intelligence_record_present"] is False, "journal record absent")
    require(scope["applied_intelligence_tier_proved"] is False, "journal tier not claimed")
    candidate = data["candidate_interpretation_requiring_confirmation"]
    require(candidate["if_formal_publication_year_is_2026_candidate_cas_report_year"] == 2025, "candidate report year")
    require(candidate["confirmed_by_hbut_research_administration"] is False, "central confirmation pending")
    require(candidate["safe_to_use_as_final_p0_h_evidence"] is False, "not final evidence")
    attachment = data["central_policy_attachment_access"]
    require(attachment["captcha_required"] is True, "CAPTCHA boundary")
    require(attachment["contents_inspected"] is False, "attachment not inspected")
    require(attachment["contents_inferred"] is False, "attachment not inferred")
    require(data["p0_h_closed"] is False, "P0-H remains open")
    require(data["submission_authorized"] is False, "submission remains unauthorized")

    receipt = {
        "schema_version": 1,
        "decision": "PASS_BOUNDED_HBUT_CAS_EDITION_SECONDARY_EVIDENCE_VERIFICATION",
        "checks": checks,
        "candidate_2026_publication_report_year": 2025,
        "university_wide_confirmation_received": False,
        "applied_intelligence_tier_proved": False,
        "cas_q3_status": "NOT_READY",
        "submission_authorized": False
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
