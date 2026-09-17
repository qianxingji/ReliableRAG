#!/usr/bin/env python3
"""Verify that the JIIS R5 PDF and public numeric reproduction are aligned."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "output/pdf/JIIS_Manuscript_R5_Reproducible.pdf"
R3 = ROOT / "paper/source_reference/JIIS_Manuscript_R3.pdf"
RECEIPT = ROOT / "paper/JIIS_R5_REPRODUCIBILITY_VERIFICATION.json"
PUBLIC = Path(os.environ.get("RELIABLERAG_PUBLIC_REPO", ROOT.parent / "ReliableRAG-Code"))

R3_SHA256 = "b01683e3431cd01c62739c66cd6045395f30362234c04f3315458602eebf6c2e"
PUBLIC_COMMIT = "44d22c66c2adbdce8ebc2289844a8b26e6929bd5"
PUBLIC_URL = "https://github.com/qianxingji/ReliableRAG-Code"
EXPECTED_BLOBS = {
    "src/arbitration/empirical_panel.py": "f27090ee94a04c4fc693dd9d0a61380660db13e9",
    "src/arbitration/empirical_contract.py": "60bdaa96ef27072e856f30a1f163b3c768f240d1",
    "src/verification/gbv_nli.py": "8be2e0b54e6ff0fce61aba361b4fa4785904b724",
    "scripts/reproduce_paper_statistics.py": "19322ba6dcb3bf818e4bcda123041bb6ee2c2ace",
    "outputs/reproduction_v1/TRACE_NUMERIC.jsonl.gz": "fb355935d1e0cb2cf5e771e8f618daa1abdb5cb4",
    "outputs/reproduction_v1/MANIFEST.json": "095f38032382d4a1ec0a27bb490934a6890c4eb6",
}
HGB_PATH = "src/mars/state_symmetric.py"
HGB_SHA256 = "3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717"
NUMERIC_BUNDLE_SHA256 = "a930286d62bddf9f4837cb1beb4b863f0f94c1bc697b2311977a9b0eb18f09f7"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def close(actual: float, expected: float, tolerance: float = 5e-12) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> int:
    checks: list[str] = []
    require(R3.is_file(), "author-designated R3 source is retained", checks)
    require(sha256(R3) == R3_SHA256, "R3 source SHA-256 matches", checks)
    require(PDF.is_file(), "reproducibility-aligned R5 PDF exists", checks)
    require(PUBLIC.is_dir(), "local public repository checkout exists", checks)
    require(run("git", "rev-parse", "HEAD", cwd=PUBLIC) == PUBLIC_COMMIT, "public repository HEAD matches manuscript commit", checks)

    for path, expected in EXPECTED_BLOBS.items():
        actual = run("git", "rev-parse", f"HEAD:{path}", cwd=PUBLIC)
        require(actual == expected, f"public Git blob matches for {path}", checks)
    require(sha256(PUBLIC / HGB_PATH) == HGB_SHA256, "public HGB source SHA-256 matches manuscript", checks)

    manifest = json.loads((PUBLIC / "MANIFEST.json").read_text(encoding="utf-8"))
    require(manifest["status"] == "PUBLIC_NUMERIC_REPRODUCTION_RELEASE", "public manifest records numeric-reproduction release status", checks)
    entries = {entry["path"]: entry for entry in manifest["files"]}
    for path in (*EXPECTED_BLOBS, HGB_PATH):
        require(path in entries, f"public manifest lists {path}", checks)
        require(sha256(PUBLIC / path) == entries[path]["sha256"], f"public manifest SHA-256 matches for {path}", checks)
    require(sha256(PUBLIC / "outputs/reproduction_v1/TRACE_NUMERIC.jsonl.gz") == NUMERIC_BUNDLE_SHA256, "public numeric bundle SHA-256 matches manuscript", checks)

    document = fitz.open(PDF)
    require(len(document) == 21, "R5 PDF has 21 pages", checks)
    require(all(abs(page.rect.width - 595.276) < 0.02 and abs(page.rect.height - 841.89) < 0.02 for page in document), "all R5 pages use A4 dimensions", checks)
    require(document.metadata.get("author") == "qianxingji", "R5 PDF author metadata matches", checks)
    require("reproducibility-aligned R5" in document.metadata.get("subject", ""), "R5 PDF subject records reproducibility alignment", checks)
    raw_text = "\n".join(page.get_text() for page in document)
    text = re.sub(r"\s+", " ", raw_text.replace("\u00ad", "-"))
    links = [link for page in document for link in page.get_links() if link.get("uri") == PUBLIC_URL]
    require(len(links) == 3, "R5 PDF contains three clickable public-repository links", checks)
    document.close()

    required_markers = [
        PUBLIC_URL,
        PUBLIC_COMMIT,
        "src/arbitration/empirical_panel.py",
        "src/arbitration/empirical_contract.py",
        "src/verification/gbv_nli.py",
        HGB_PATH,
        HGB_SHA256,
        NUMERIC_BUNDLE_SHA256,
        "scripts/reproduce_paper_statistics.py",
        "scripts/reproduce_all.py",
        "exactly rebuilds all nine-policy point estimates",
        "not independent authentication of the original training event",
        "does not regenerate the neural acquisition or refit the paper heads",
    ]
    for marker in required_markers:
        require(marker in text, f"R5 text contains: {marker}", checks)
    stale_markers = [
        "fd5c6f11fd4308c9442218b02e39428110bbd36d",
        "a6da7d80aca082301824b320ec4698c0dfac7b12",
        "candidate is reported as rebuilt and checked",
        "project development repository",
        "HGB source paths are not necessarily present on a public branch",
        "cannot reconstruct the per-question top-K bootstrap",
    ]
    for marker in stale_markers:
        require(marker not in text, f"R5 omits stale release statement: {marker}", checks)

    estimates_dir = PUBLIC / "outputs/cas_q2/empirical_analysis_v1"
    point = json.loads((estimates_dir / "POINT_ESTIMATES.json").read_text(encoding="utf-8"))
    intervals = json.loads((estimates_dir / "INTERVALS.json").read_text(encoding="utf-8"))
    require(point["N_all"] == 18000, "public aggregate N is 18,000", checks)
    require(point["question_groups"] == 6000, "public aggregate question count is 6,000", checks)
    require(point["N_eligible"] == 4267, "public aggregate eligible count is 4,267", checks)
    require(point["primary_global_cap"] == 900, "public aggregate action cap is 900", checks)

    keep = point["policies"]["Keep"]
    combo = point["policies"]["HGB_GBV_R"]
    require(close(100 * keep["em_rate"], 17.988888888888887), "Keep EM agrees with the public aggregate", checks)
    require(close(100 * keep["token_f1"], 22.720665118734132), "Keep F1 agrees with the public aggregate", checks)
    require((combo["recovery"], combo["damage"], combo["neutral"], combo["net"]) == (352, 11, 537, 341), "HGB+GbV_R event counts agree with the public aggregate", checks)
    require(close(100 * combo["em_rate"], 19.883333333333333), "HGB+GbV_R EM agrees with the public aggregate", checks)
    require(close(100 * combo["token_f1"], 25.278046128247494), "HGB+GbV_R F1 agrees with the public aggregate", checks)
    require(close(combo["damage_rate_pp"], 0.06111111111111111), "HGB+GbV_R Damage agrees with the public aggregate", checks)

    require("Keep obtains 17.9889% EM and 22.7207% token F1" in text, "R5 reports the public Keep EM/F1 values", checks)
    require("352 Recoveries and 11 Damage events, giving Net = 341, EM = 19.8833%, and F1 = 25.2780%" in text, "R5 reports the public HGB+GbV_R counts and rates", checks)
    require("0.0611" in text, "R5 reports the public HGB+GbV_R Damage rate", checks)

    expected_primary = [
        ("ROA-FULL", "HGB_GBV_R", 0.044444444444444446, [-0.13333333333333333, 0.2037268518518532], 0.06111111111111111, [0.0, 0.1277777777777778], False),
        ("HGB_GBV_R", "HGB_ONLY_R", 0.05555555555555555, [-0.15555555555555556, 0.31666666666666665], -0.08333333333333333, [-0.18333333333333335, -0.005555555555555556], False),
        ("HGB_GBV_R", "GBV_ONLY_R", 0.23333333333333334, [0.07222222222222223, 0.43333333333333335], -0.07222222222222222, [-0.14444444444444446, -0.02777777777777778], True),
    ]
    comparisons = intervals["reallocated"]["comparisons"]
    require(len(comparisons) == 3, "public primary interval family has three comparisons", checks)
    for actual, expected in zip(comparisons, expected_primary):
        left, right, em_point, em_range, damage_point, damage_range, joint = expected
        require((actual["left"], actual["right"]) == (left, right), f"primary comparison order matches for {left} minus {right}", checks)
        em = actual["endpoints"]["em_difference_pp"]
        damage = actual["endpoints"]["damage_rate_difference_pp"]
        require(close(em["point_pp"], em_point) and all(close(a, b) for a, b in zip(em["adjusted_percentile_range_pp"], em_range)), f"primary EM point/range matches for {left} minus {right}", checks)
        require(close(damage["point_pp"], damage_point) and all(close(a, b) for a, b in zip(damage["adjusted_percentile_range_pp"], damage_range)), f"primary Damage point/range matches for {left} minus {right}", checks)
        require(actual["joint_em_improvement_and_damage_reduction"] is joint, f"primary joint decision matches for {left} minus {right}", checks)

    table_markers = [
        "+0.0444 [−0.1333, +0.2037]",
        "+0.0611 [+0.0000, +0.1278]",
        "+0.0556 [−0.1556, +0.3167]",
        "−0.0833 [−0.1833, −0.0056]",
        "+0.2333 [+0.0722, +0.4333]",
        "−0.0722 [−0.1444, −0.0278]",
    ]
    compact = re.sub(r"\s+", " ", text)
    for marker in table_markers:
        require(marker in compact, f"R5 primary table contains {marker}", checks)

    font_rows = run("pdffonts", str(PDF)).splitlines()[2:]
    require(bool(font_rows), "R5 PDF contains font records", checks)
    require(all(row.split()[-5] == "yes" for row in font_rows), "all R5 fonts are embedded", checks)
    require(all("Type 3" not in row for row in font_rows), "R5 PDF contains no Type 3 fonts", checks)
    info = run("pdfinfo", str(PDF))
    require("Encrypted:       no" in info, "R5 PDF is not encrypted", checks)
    require("Form:            none" in info, "R5 PDF contains no form", checks)
    require("JavaScript:      no" in info, "R5 PDF contains no JavaScript", checks)

    result = {
        "schema_version": 1,
        "decision": "PASS_JIIS_R5_PUBLIC_STATISTICAL_REPRODUCIBILITY",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "r3_source": {"path": str(R3.relative_to(ROOT)), "sha256": R3_SHA256},
        "r5_pdf": {"path": str(PDF.relative_to(ROOT)), "sha256": sha256(PDF), "pages": 21, "page_size": "A4"},
        "public_repository": {
            "url": PUBLIC_URL,
            "commit": PUBLIC_COMMIT,
            "github_actions_run": "https://github.com/qianxingji/ReliableRAG-Code/actions/runs/35054121085",
            "github_actions_conclusion": "success",
            "full_statistical_reproduction": "PASS_EXACT_18000_TRACES_20000_DRAWS",
            "aggregate_reporting_checks": 129,
            "repository_checks": 194,
            "unit_tests": 8,
        },
        "scientific_results_changed": False,
        "replacement_scope": ["page 12 data and code availability", "page 17 Appendix D.3 code versions", "page 19 HGB implementation provenance", "page 21 replication-materials scope"],
        "known_boundary": "Public artifacts exactly reproduce point estimates and the full selected top-K bootstrap from opaque numeric traces; excluded text, model, fitted-development, and execution assets prevent neural regeneration and paper-head refitting.",
        "check_count": len(checks),
        "checks": checks,
    }
    RECEIPT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
