#!/usr/bin/env python3
"""Verify committed Applied Intelligence modern-template preflight artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT.json"
VERIFICATION = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_VERIFICATION.json"
EXPECTED_MEMBERS = [
    "Fig1.pdf",
    "Fig2.pdf",
    "manuscript.bbl",
    "manuscript.tex",
    "references.bib",
    "table_main_results.tex",
    "table_primary_comparisons.tex",
    "table_study_design.tex",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64"
    candidate = local / f"{name}.exe"
    if candidate.is_file():
        return str(candidate)
    raise RuntimeError(f"{name} is required")


def command_text(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True, errors="replace")
    return completed.stdout


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def main() -> int:
    checks: list[str] = []
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    require(
        receipt["decision"]
        == "PARTIAL_PASS_APPLIED_INTELLIGENCE_MODERN_SN_JNL_PREFLIGHT_SMALLCONDENSED_EQUIVALENCE_OPEN",
        "bounded modern-template decision",
        checks,
    )
    require(receipt["cas_q3_status"] == "NOT_READY", "CAS Q3 remains not ready", checks)
    require(receipt["target_selected"] is True, "Applied Intelligence remains selected", checks)
    require(receipt["submission_authorized"] is False, "preflight does not authorize submission", checks)
    require(receipt["distribution_authorized"] is False, "preflight does not authorize distribution", checks)
    require(receipt["profile"]["class"] == "sn-jnl", "modern sn-jnl class recorded", checks)
    require(receipt["profile"]["class_options"] == ["pdflatex", "sn-basic", "Numbered"], "numeric profile", checks)
    require(receipt["profile"]["abstract_words"] == 155, "abstract count", checks)
    require(receipt["profile"]["keywords"] == 5, "keyword count", checks)
    require(receipt["profile"]["smallcondensed_profile_used"] is False, "smallcondensed is not overclaimed", checks)
    require(
        receipt["profile"]["sn_jnl_equivalent_to_journal_smallcondensed_proved"] is False,
        "template equivalence remains open",
        checks,
    )
    require(receipt["source_protection"]["scientific_prose_or_numbers_changed"] is False, "scientific source preserved", checks)
    require(receipt["source_protection"]["allowed_transformation_count"] == 11, "bounded transformation count", checks)
    require(receipt["compile_checks"]["fatal_errors"] == 0, "no fatal compile errors", checks)
    require(receipt["compile_checks"]["undefined_citations_or_references"] == 0, "no unresolved citations", checks)
    require(receipt["compile_checks"]["overfull_boxes"] == 0, "no overfull boxes", checks)
    require(receipt["compile_checks"]["underfull_boxes"] == 14, "class-driven underfull count recorded", checks)
    require(receipt["compile_checks"]["unresolved_markers"] == 0, "no visible unresolved markers", checks)

    neutral = ROOT / "paper" / "manuscript.tex"
    require(
        sha256(neutral) == receipt["source_protection"]["journal_neutral_source_sha256_before_and_after"],
        "journal-neutral source hash",
        checks,
    )
    pdf = ROOT / receipt["artifacts"]["pdf"]
    source_zip = ROOT / receipt["artifacts"]["authored_source_zip"]
    require(pdf.is_file(), "preflight PDF exists", checks)
    require(source_zip.is_file(), "authored-source ZIP exists", checks)
    require(sha256(pdf) == receipt["artifacts"]["pdf_sha256"], "preflight PDF hash", checks)
    require(sha256(source_zip) == receipt["artifacts"]["authored_source_zip_sha256"], "authored-source ZIP hash", checks)

    pdfinfo = command_text([executable("pdfinfo"), str(pdf)])
    pages = int(next(line for line in pdfinfo.splitlines() if line.startswith("Pages:")).split(":", 1)[1])
    require(pages == receipt["artifacts"]["pdf_pages"] == 12, "preflight PDF pages", checks)
    font_rows = [row for row in command_text([executable("pdffonts"), str(pdf)]).splitlines()[2:] if row.strip()]
    nonembedded = [row for row in font_rows if len(row.split()) >= 5 and row.split()[-5] == "no"]
    type3 = [row for row in font_rows if row.split()[1:3] == ["Type", "3"]]
    require(not nonembedded, "all preflight fonts embedded", checks)
    require(not type3, "no Type 3 preflight fonts", checks)
    visible = command_text([executable("pdftotext"), str(pdf), "-"])
    visible_flat = re.sub(r"\s+", " ", visible)
    for marker in (
        "Supervision-Matched Selection of Paired RAG",
        "The same joint rule does not pass against the HGB-only policy",
        "Data and code availability",
        "References",
    ):
        require(marker in visible_flat, f"visible PDF marker: {marker}", checks)

    with zipfile.ZipFile(source_zip) as bundle:
        members = bundle.namelist()
        require(members == EXPECTED_MEMBERS, "authored-source member allowlist", checks)
        require(not any("/" in name or "\\" in name for name in members), "authored source is flat", checks)
        require("sn-jnl.cls" not in members and "sn-basic.bst" not in members, "template files are not redistributed", checks)
        manuscript = bundle.read("manuscript.tex").decode("utf-8")
    require(r"\documentclass[pdflatex,sn-basic,Numbered]{sn-jnl}" in manuscript, "authored source targets sn-jnl", checks)
    require("The same joint rule does not pass against the HGB-only policy" in manuscript, "negative Claim retained", checks)
    require("not a new selector architecture" in manuscript, "novelty boundary retained", checks)
    require(
        receipt["template_dependency"]["files_redistributed_in_repository_or_authored_source_zip"] is False,
        "external template dependency boundary",
        checks,
    )

    result = {
        "schema_version": 1,
        "decision": "PASS_COMMITTED_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_WITH_TEMPLATE_EQUIVALENCE_OPEN",
        "checks": len(checks),
        "pdf_pages": pages,
        "source_members": len(EXPECTED_MEMBERS),
        "visual_review": "SEPARATE_VERSIONED_PROJECT_LEAD_ACCEPTANCE",
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }
    VERIFICATION.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
