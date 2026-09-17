#!/usr/bin/env python3
"""Verify the public license state without reading scientific payloads."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_G_LICENSE_STATE_VERIFICATION.json"
EXPECTED_LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
DECISION = "PARTIAL_PASS_OWNER_SELECTED_APACHE2_ROOT_LICENSE_AND_SCOPE_BOUND_THIRD_PARTY_AND_INSTITUTIONAL_GATES_OPEN"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> dict[str, object]:
    checks = 0

    def require(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    license_path = ROOT / "LICENSE"
    scope_path = ROOT / "LICENSE_SCOPE.md"
    decision_path = ROOT / "docs" / "cas_q3" / "P0_G_PROJECT_LICENSE_DECISION_PACKET.md"
    record_path = ROOT / "docs" / "cas_q3" / "P0_G_LICENSE_STATE_CORRIGENDUM.json"
    notice_path = ROOT / "NOTICE"
    require(license_path.is_file(), "root LICENSE missing")
    require(sha(license_path) == EXPECTED_LICENSE_SHA256, "root LICENSE hash changed")
    license_text = license_path.read_text(encoding="utf-8")
    require("Apache License" in license_text and "Version 2.0, January 2004" in license_text, "Apache markers missing")
    require(scope_path.is_file(), "LICENSE_SCOPE.md missing")
    scope = scope_path.read_text(encoding="utf-8")
    for marker in (
        "source code authored by the project",
        "does not grant rights to third-party datasets",
        "Public distribution of the candidate remains withheld",
    ):
        require(marker in scope, f"license scope marker missing: {marker}")
    decision_text = decision_path.read_text(encoding="utf-8")
    require("OWNER SELECTED APACHE-2.0" in decision_text, "current decision is not recorded")
    require("OWNER DECISION REQUIRED" not in decision_text, "stale owner-decision status remains")
    require("It does not add a license" not in decision_text, "stale no-license claim remains")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    require(record["decision"] == DECISION, "corrigendum decision mismatch")
    current = record["current_state"]
    require(current["owner_selected_project_code_license"] == "Apache-2.0", "owner-selected license mismatch")
    require(current["root_license_sha256"] == EXPECTED_LICENSE_SHA256, "recorded license hash mismatch")
    require(current["project_specific_notice_present"] is False, "NOTICE state mismatch")
    require(not notice_path.exists(), "unreviewed root NOTICE appeared")
    require(current["legal_copyright_holder_confirmed"] is False, "holder must remain open")
    require(current["copyright_year_or_range_confirmed"] is False, "year must remain open")
    require(current["institutional_release_review_resolved"] is False, "institutional review must remain open")
    boundary = record["third_party_boundary"]
    require(boundary["qwen_non_commercial_grant"] is True, "Qwen research-license boundary missing")
    require(boundary["qwen_weights_in_release_candidate"] is False, "Qwen weights cannot be in release")
    require(boundary["deberta_non_c_training_data_includes_non_commercial_terms"] is True, "DeBERTa caveat missing")
    require(boundary["deberta_weights_in_release_candidate"] is False, "DeBERTa weights cannot be in release")
    require(boundary["institutional_review_complete"] is False, "third-party institutional review must remain open")
    require(record["p0_g_closed"] is False, "P0-G cannot be closed")
    require(record["distribution_authorized"] is False, "distribution cannot be authorized")
    require(record["submission_authorized"] is False, "submission cannot be authorized")
    return {
        "schema_version": 1,
        "decision": "PASS_CURRENT_LICENSE_STATE_CONSISTENCY_WITH_EXTERNAL_GATES_OPEN",
        "checks": checks,
        "root_license_sha256": EXPECTED_LICENSE_SHA256,
        "project_code_license": "Apache-2.0",
        "legal_holder_confirmed": False,
        "copyright_year_confirmed": False,
        "institutional_release_review_complete": False,
        "third_party_institutional_review_complete": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    result = verify()
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
