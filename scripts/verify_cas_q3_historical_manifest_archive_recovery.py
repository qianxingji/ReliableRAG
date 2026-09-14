#!/usr/bin/env python3
"""Verify the bounded historical mars_full manifest archive recovery."""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/cas_q3/P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.json"
RECEIPT = ROOT / "docs/cas_q3/P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_VERIFICATION.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def main() -> int:
    evidence = json.loads(AUDIT.read_text(encoding="utf-8"))
    checks: list[str] = []
    require(
        evidence["decision"]
        == "PARTIAL_PASS_LOCALLY_PRESERVED_MARS_MANIFEST_BYTE_COPY_RECOVERED_NO_INDEPENDENT_TIMESTAMP_OR_FIT_RECEIPTS",
        "bounded recovery decision is retained",
        checks,
    )
    require(evidence["cas_q3_status"] == "NOT_READY", "CAS Q3 remains fail-closed", checks)

    archive = Path(evidence["source_archive"]["path"])
    current = Path(evidence["current_manifest"]["path"])
    require(archive.is_file(), "preserved source archive exists", checks)
    require(current.is_file(), "current preserved mars_full manifest exists", checks)
    require(archive.stat().st_size == evidence["source_archive"]["bytes"], "archive size matches", checks)
    require(sha(archive) == evidence["source_archive"]["sha256"], "archive SHA-256 matches", checks)

    manifest_member = evidence["embedded_manifest"]["member"]
    pin_member = evidence["internal_archive_pin"]["member"]
    with zipfile.ZipFile(archive) as bundle:
        require(len(bundle.infolist()) == evidence["source_archive"]["members"], "archive member count matches", checks)
        embedded = bundle.read(manifest_member)
        pin = bundle.read(pin_member)
        info = bundle.getinfo(manifest_member)
        historical_json_members = sorted(
            name for name in bundle.namelist()
            if "/evidence/mars_full/" in name and name.endswith(".json")
        )

    require(len(embedded) == evidence["embedded_manifest"]["bytes"], "embedded manifest size matches", checks)
    require(hashlib.sha256(embedded).hexdigest() == evidence["embedded_manifest"]["sha256"], "embedded manifest SHA-256 matches", checks)
    require(embedded == current.read_bytes(), "embedded and current manifests are byte-identical", checks)
    require(sha(current) == evidence["current_manifest"]["sha256"], "current manifest SHA-256 matches", checks)
    manifest = json.loads(embedded)
    require(manifest["phase"] == evidence["embedded_manifest"]["phase"], "manifest phase matches", checks)
    require(manifest["code_version"] == evidence["embedded_manifest"]["code_version"], "manifest code version matches", checks)
    require(manifest["file_count"] == 363 == len(manifest["files"]), "manifest closes over 363 file records", checks)
    require(info.date_time == (2026, 8, 30, 2, 12, 24), "ZIP member timestamp matches recorded observation", checks)
    require(hashlib.sha256(pin).hexdigest() == evidence["internal_archive_pin"]["sha256"], "internal checksum-list SHA-256 matches", checks)
    expected_pin_line = b"evidence/mars_full/manifest.json\t77147\t5924851c30b18785cb1e2bf6893c74cdc819d3549748760bd44b4ebf7ab4e753"
    require(expected_pin_line in pin.splitlines(), "internal checksum list pins embedded manifest", checks)
    require(len(historical_json_members) == 7, "seven packaged mars_full JSON records are present", checks)
    require(
        not any("fit" in Path(name).name.lower() and "receipt" in Path(name).name.lower() for name in historical_json_members),
        "packaged mars_full JSON filenames contain no fit receipt",
        checks,
    )

    original_root = archive.parent
    zip_paths = [
        path for path in original_root.rglob("*.zip")
        if not any(part.lower() in {".venv", "site-packages", "pip-cache", "node_modules"} for part in path.parts)
    ]
    hits: list[str] = []
    for path in zip_paths:
        with zipfile.ZipFile(path) as bundle:
            if any(name.endswith("evidence/mars_full/manifest.json") for name in bundle.namelist()):
                hits.append(str(path.resolve()))
    require(len(zip_paths) == evidence["search_evidence"]["relevant_zip_archives_scanned"], "relevant ZIP scan count matches", checks)
    require(hits == [str(archive.resolve())], "exactly the recorded archive contains a mars_full manifest", checks)

    fsck = subprocess.run(
        ["git", "fsck", "--full", "--no-reflogs", "--unreachable"],
        cwd=original_root,
        check=True,
        text=True,
        capture_output=True,
    )
    kinds = Counter(line.split()[1] for line in fsck.stdout.splitlines() if line.startswith("unreachable "))
    expected = evidence["search_evidence"]["unreachable_git_objects"]
    require(sum(kinds.values()) == expected["total"], "unreachable Git object total matches", checks)
    require(kinds == Counter({"blob": expected["blobs"], "commit": expected["commits"], "tree": expected["trees"]}), "unreachable Git object kinds match", checks)

    interpretation = evidence["evidence_interpretation"]
    require(
        interpretation["locally_preserved_dated_named_package_byte_copy_recovered"] is True,
        "locally preserved dated/named package byte copy is recorded",
        checks,
    )
    require(interpretation["independent_pre_roa_timestamp_proved"] is False, "independent timestamp is not claimed", checks)
    require(interpretation["original_training_event_authenticated_by_this_archive"] is False, "original training event is not claimed", checks)
    require(interpretation["seven_per_estimator_fit_time_id_receipts_recovered"] is False, "ID receipts remain missing", checks)
    require(interpretation["seven_per_estimator_fit_time_matrix_receipts_recovered"] is False, "matrix receipts remain missing", checks)
    require(interpretation["independent_original_fit_witness_recovered"] is False, "independent fit witness remains missing", checks)
    require(evidence["operations"] == {
        "scientific_payloads_decoded": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "gold_or_answer_text_read": False,
        "sealed_source_files_modified": 0,
    }, "read-only operation boundary is retained", checks)

    result = {
        "schema_version": 1,
        "decision": "PASS_BOUNDED_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_VERIFICATION",
        "checks": len(checks),
        "archive_sha256": sha(archive),
        "manifest_sha256": hashlib.sha256(embedded).hexdigest(),
        "manifest_byte_identical": True,
        "independent_timestamp_certified": False,
        "fit_receipt_filenames_in_packaged_mars_json_members_found": False,
        "full_historical_content_search_reperformed": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "gold_or_answer_text_read": False,
        "cas_q3_status": "NOT_READY"
    }
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
