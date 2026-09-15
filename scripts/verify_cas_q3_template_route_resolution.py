#!/usr/bin/env python3
"""Verify the bounded Applied Intelligence current-template route resolution."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOLUTION = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_TEMPLATE_ROUTE_RESOLUTION.json"
TRANSPORT = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_TEMPLATE_TRANSPORT_RESULTS.json"
PREFLIGHT = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT.json"
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_TEMPLATE_ROUTE_RESOLUTION_VERIFICATION.json"


def main() -> int:
    result = json.loads(RESOLUTION.read_text(encoding="utf-8"))
    transport = json.loads(TRANSPORT.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    checks = 0

    def require(condition: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(label)

    require(
        result["decision"]
        == "PASS_OFFICIAL_PUBLISHER_ACCEPTS_CURRENT_SN_JNL_SUBMISSION_ROUTE_SMALLCONDENSED_STYLE_EQUIVALENCE_UNPROVED",
        "bounded decision",
    )
    require(result["cas_q3_status"] == "NOT_READY", "CAS status")
    require(result["target_journal"] == "Applied Intelligence", "target journal")
    require(all(result["official_sources"].values()), "official source URLs")
    require(all(result["official_findings"].values()), "official findings")
    route = result["authenticated_current_route"]
    require(route["template"] == "sn-jnl", "current template")
    require(route["template_version"] == "Version 3.1 December 2024", "template version")
    require(route["template_zip_sha256"] == preflight["template_dependency"]["official_download_sha256"], "template ZIP pin")
    require(route["class_sha256"] == preflight["template_dependency"]["sn_jnl_class_sha256"], "class pin")
    require(route["bibliography_style_sha256"] == preflight["template_dependency"]["sn_basic_bst_sha256"], "BST pin")
    private = transport["private_complete_source_transport"]
    require(route["flat_transport_members"] == private["archive_members"], "flat member count")
    require(route["independent_transport_validations"] == 2, "independent transport count")
    require(route["validator_checks_each"] == private["validator_checks_each"], "transport check count")
    require(route["clean_compile_pages"] == private["clean_compile_pages"], "compiled pages")
    require(route["clean_compile_pdf_sha256"] == private["clean_compile_pdf_sha256"], "compiled PDF pin")
    resolution = result["resolution"]
    require(resolution["publisher_acceptance_of_current_sn_jnl_submission_route_proved"] is True, "publisher route acceptance")
    require(resolution["journal_specific_smallcondensed_style_equivalence_proved"] is False, "style equivalence not claimed")
    require(resolution["working_legacy_smallcondensed_package_recovered"] is False, "legacy package not claimed")
    require(resolution["pre_submission_template_route_gate_closed"] is True, "pre-submission route gate")
    require(resolution["submission_system_compile_observed"] is False, "submission-system compile not claimed")
    require(resolution["author_populated_package_built"] is False, "author package not claimed")
    require(result["scientific_payloads_read"] is False, "no scientific payload reads")
    require(result["model_forwards"] == 0, "no model forwards")
    require(result["scientific_fits"] == 0, "no scientific fits")
    require(result["submission_authorized"] is False, "submission remains unauthorized")
    require(result["distribution_authorized"] is False, "distribution remains unauthorized")

    receipt = {
        "schema_version": 1,
        "decision": "PASS_BOUNDED_APPLIED_INTELLIGENCE_TEMPLATE_ROUTE_RESOLUTION_VERIFICATION",
        "checks": checks,
        "publisher_route_accepted": True,
        "smallcondensed_equivalence_proved": False,
        "cas_q3_status": "NOT_READY",
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
