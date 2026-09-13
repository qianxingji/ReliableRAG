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
    checks.equal(static_receipt["check_count"], 126, "static manuscript checks")
    checks.equal(static_receipt["abstract_word_count"], 142, "cross-profile abstract words")
    checks.equal(static_receipt["bibliography_entries"], 22, "bibliography entries")
    length_receipt = json.loads(
        (ROOT / "docs" / "cas_q3" / "P0_I_MANUSCRIPT_LENGTH_VERIFICATION.json").read_text(encoding="utf-8")
    )
    checks.equal(length_receipt["pdf_tokens_before_references"], 3898, "pre-reference PDF token proxy")
    checks.equal(length_receipt["pdf_tokens_full_document"], 4596, "full PDF token proxy")
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
