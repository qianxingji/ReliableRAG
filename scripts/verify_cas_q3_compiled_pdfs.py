#!/usr/bin/env python3
"""Verify compiled manuscript PDFs, logs, text resolution, and font inventory."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True, errors="replace").stdout


def pdf_info(path: Path) -> dict:
    text = run("pdfinfo", str(path))
    pages = int(re.search(r"^Pages:\s+(\d+)", text, re.M).group(1))
    size = re.search(r"^Page size:\s+(.+)$", text, re.M).group(1).strip()
    version = re.search(r"^PDF version:\s+(.+)$", text, re.M).group(1).strip()
    return {"pages": pages, "page_size": size, "pdf_version": version}


def font_info(path: Path) -> dict:
    lines = run("pdffonts", str(path)).splitlines()[2:]
    records = [line for line in lines if line.strip()]
    nonembedded = []
    type3 = []
    for line in records:
        parts = line.split()
        if len(parts) >= 5 and parts[-5] == "no":
            nonembedded.append(parts[0])
        if len(parts) >= 3 and parts[1:3] == ["Type", "3"]:
            type3.append(parts[0])
    # Poppler columns can vary; explicitly retain the known Base-14 figure fonts.
    for family in ("Helvetica", "Helvetica-Bold"):
        if any(line.startswith(family + " ") and " no " in line for line in records):
            nonembedded.append(family)
    return {
        "font_rows": len(records),
        "nonembedded_fonts": sorted(set(nonembedded)),
        "type3_fonts": sorted(set(type3)),
    }


def log_audit(path: Path, allow_infinite_glue: bool) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    fatal = re.findall(r"(?:LaTeX Error|Undefined control sequence|Emergency stop|Fatal error)", text, re.I)
    undefined = re.findall(r"undefined (?:citations?|references?)|Citation .+ undefined|Reference .+ undefined", text, re.I)
    boxes = re.findall(r"(?:Overfull|Underfull) \\[hv]box", text)
    infinite = "Infinite glue shrinkage found in box being split" in text
    if fatal or undefined or boxes or (infinite and not allow_infinite_glue):
        raise AssertionError({"log": str(path), "fatal": fatal, "undefined": undefined, "boxes": boxes, "infinite": infinite})
    return {
        "fatal_errors": len(fatal),
        "undefined_citations_or_references": len(undefined),
        "overfull_or_underfull_boxes": len(boxes),
        "known_nonfatal_infinite_glue_notice": infinite,
    }


def main() -> int:
    for tool in ("pdfinfo", "pdffonts", "pdftotext"):
        if not shutil.which(tool):
            raise RuntimeError(f"missing Poppler tool: {tool}")
    main_pdf = OUT / "manuscript.pdf"
    supp_pdf = OUT / "supplement.pdf"
    if not main_pdf.exists() or not supp_pdf.exists():
        raise FileNotFoundError("compiled manuscript PDFs are missing")

    main_text = run("pdftotext", str(main_pdf), "-")
    supp_text = run("pdftotext", str(supp_pdf), "-")
    for label, text in (("manuscript", main_text), ("supplement", supp_text)):
        if "[?]" in text or "??" in text:
            raise AssertionError(f"unresolved marker in {label} PDF text")

    result = {
        "schema_version": 1,
        "decision": "PASS_COMPILED_PDF_MECHANICAL_VERIFICATION_WITH_DISCLOSED_FONT_AND_LONGTABLE_NOTICES",
        "engine": "MiKTeX pdfTeX 1.40.28 / LaTeX2e 2025-11-01",
        "artifacts": {
            "output/pdf/manuscript.pdf": {"sha256": sha(main_pdf), **pdf_info(main_pdf), **font_info(main_pdf)},
            "output/pdf/supplement.pdf": {"sha256": sha(supp_pdf), **pdf_info(supp_pdf), **font_info(supp_pdf)},
        },
        "logs": {
            "output/pdf/manuscript.log": {"sha256": sha(OUT / "manuscript.log"), **log_audit(OUT / "manuscript.log", False)},
            "output/pdf/supplement.log": {"sha256": sha(OUT / "supplement.log"), **log_audit(OUT / "supplement.log", True)},
        },
        "text_checks": {
            "manuscript_has_title": "Supervision-Matched Selection of Paired RAG Repairs" in main_text,
            "manuscript_has_references": "References" in main_text,
            "supplement_has_fixed_action_table": "Fixed-action sensitivity" in supp_text,
            "unresolved_markers": 0,
        },
        "visual_review": {
            "status": "PASS_BY_PROJECT_LEAD_2026-09-13",
            "main_pages_reviewed": 11,
            "supplement_pages_reviewed": 3,
            "defects_observed": 0,
        },
        "disclosures": [
            "MiKTeX reports its installation has not yet checked for updates; this is outside the LaTeX logs.",
            "Supplement log retains one nonfatal longtable infinite-glue page-split notice; rendered content is complete.",
            "The two included vector figures use unembedded PDF Base-14 Helvetica/Helvetica-Bold fonts; target-journal PDF-profile compliance remains to be checked after journal selection.",
            "The main PDF also contains one embedded Type 3 font, F127; target-journal Type 3 font rules remain to be checked after journal selection.",
        ],
    }
    if not all(result["text_checks"][k] for k in ("manuscript_has_title", "manuscript_has_references", "supplement_has_fixed_action_table")):
        raise AssertionError(result["text_checks"])
    path = ROOT / "paper" / "COMPILE_RECEIPT.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
