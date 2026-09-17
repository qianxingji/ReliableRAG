#!/usr/bin/env python3
"""Verify the JIIS R6 major revision and its public refit evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "output/pdf/JIIS_Manuscript_R6_Major_Revision.pdf"
RECEIPT = ROOT / "paper/JIIS_R6_MAJOR_REVISION_VERIFICATION.json"
PUBLIC = Path(os.environ.get("RELIABLERAG_PUBLIC_REPO", ROOT.parent / "ReliableRAG-Code"))
COMMIT = "038d769e96d092a2eec3bbc5df9f45f3c2a17ff0"
EXPECTED_SHA = {
    "outputs/reproduction_v1/DEVELOPMENT_NUMERIC.jsonl.gz": "8867daa8c8d827d5aa928627d8de068656e35760b47f784c38d328a369afe7f0",
    "outputs/reproduction_v1/CURRENT_HEADS.json": "a519b80b08ece87c59d296a3b590a1cda31de16122c68a1e0efe5a2c27f1e5ea",
    "outputs/reproduction_v1/TRACE_NUMERIC.jsonl.gz": "a930286d62bddf9f4837cb1beb4b863f0f94c1bc697b2311977a9b0eb18f09f7",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def main() -> int:
    checks = []
    def require(value: bool, message: str) -> None:
        if not value:
            raise AssertionError(message)
        checks.append(message)

    require(PDF.is_file(), "R6 PDF exists")
    require(run("git", "rev-parse", "HEAD", cwd=PUBLIC).strip() == COMMIT, "public repository commit matches R6")
    for name, expected in EXPECTED_SHA.items():
        require(sha256(PUBLIC / name) == expected, f"public SHA-256 matches for {name}")
    refit = json.loads(run(os.sys.executable, "scripts/reproduce_current_heads.py", cwd=PUBLIC))
    require(refit["status"] == "PASS_EXACT_CURRENT_HEAD_REFIT", "public exact current-head refit passes")
    require((refit["fit_eligible"], refit["fit_positive"]) == (2572, 557), "fit sample and positive counts match")
    require((refit["calibration_eligible"], refit["calibration_positive"]) == (630, 132), "calibration sample and positive counts match")
    require(refit["scientific_fit_calls"] == 10, "public refit executes ten model fits")

    document = fitz.open(PDF)
    require(len(document) == 21, "R6 PDF has 21 pages")
    require(all(abs(page.rect.width - 595.276) < 0.02 and abs(page.rect.height - 841.89) < 0.02 for page in document), "all R6 pages are A4")
    text = re.sub(r"\s+", " ", "\n".join(page.get_text() for page in document).replace("\u00ad", "-"))
    links = [link for page in document for link in page.get_links() if link.get("uri") == "https://github.com/qianxingji/ReliableRAG-Code"]
    document.close()
    require(len(links) == 3, "R6 contains three public-repository links")
    for marker in (
        COMMIT, "2,572 eligible traces", "557 Recovery positives", "630 eligible traces", "132 positives",
        "28, 26, 10, 8, and 8 learned scalar parameters", "scripts/reproduce_current_heads.py",
        "adding HGB to GbV-only passes the joint rule", "stronger HGB-only head does not",
        "not end-to-end regeneration of retrieval", "not independent authentication of the original training event",
    ):
        require(marker in text, "R6 contains: " + marker)
    for marker in (
        "44d22c66c2adbdce8ebc2289844a8b26e6929bd5",
        "public materials do not report the eligible fitting/calibration row totals",
        "does not regenerate the neural acquisition or refit the paper heads",
        "not sufficient to reconstruct selection within the question-cluster bootstrap",
    ):
        require(marker not in text, "R6 omits stale statement: " + marker)
    font_rows = run("pdffonts", str(PDF)).splitlines()[2:]
    require(bool(font_rows), "R6 has font records")
    require(all(row.split()[-5] == "yes" for row in font_rows), "all R6 fonts are embedded")
    require(all("Type 3" not in row for row in font_rows), "R6 has no Type 3 fonts")
    info = run("pdfinfo", str(PDF))
    require("Encrypted:       no" in info, "R6 is not encrypted")
    require("JavaScript:      no" in info, "R6 has no JavaScript")

    result = {
        "schema_version": 1,
        "decision": "PASS_JIIS_R6_MAJOR_REVISION",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "pdf": {"path": str(PDF.relative_to(ROOT)), "sha256": sha256(PDF), "pages": 21},
        "public_repository": {
            "url": "https://github.com/qianxingji/ReliableRAG-Code",
            "commit": COMMIT,
            "github_actions_run": "https://github.com/qianxingji/ReliableRAG-Code/actions/runs/35057594179",
            "github_actions_conclusion": "success",
            "exact_current_head_refit": refit,
            "development_bundle_sha256": EXPECTED_SHA["outputs/reproduction_v1/DEVELOPMENT_NUMERIC.jsonl.gz"],
            "current_heads_sha256": EXPECTED_SHA["outputs/reproduction_v1/CURRENT_HEADS.json"],
            "evaluation_bundle_sha256": EXPECTED_SHA["outputs/reproduction_v1/TRACE_NUMERIC.jsonl.gz"],
        },
        "scientific_results_changed": False,
        "revision_scope": [
            "clarify empirical contribution against prior two-answer prediction",
            "report effective fit/calibration sample and positive counts",
            "report learned scalar parameter counts",
            "release exact current-head refit inputs and parameter records",
            "unify manuscript data/code availability boundaries",
        ],
        "check_count": len(checks),
        "checks": checks,
    }
    RECEIPT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
