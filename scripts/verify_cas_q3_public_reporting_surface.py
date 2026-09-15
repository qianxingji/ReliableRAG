#!/usr/bin/env python3
"""Verify only committed, public reporting artifacts.

This check is intentionally independent of ignored scientific outputs. It does
not authenticate the private aggregate inputs or recompute any scientific
result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
RELEASE = ROOT / "release" / "cas_q3_aggregate"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def main() -> int:
    checks: list[str] = []
    manuscript = (PAPER / "manuscript.tex").read_text(encoding="utf-8")
    supplement = (PAPER / "supplement.tex").read_text(encoding="utf-8")
    bibliography = (PAPER / "references.bib").read_text(encoding="utf-8")
    summary = (RELEASE / "CLAIM_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")
    summary_flat = re.sub(r"\s+", " ", summary)
    readme = (RELEASE / "README.md").read_text(encoding="utf-8")
    availability = (RELEASE / "DATA_AND_CODE_AVAILABILITY.md").read_text(encoding="utf-8")
    receipt = json.loads((PAPER / "ASSET_RECEIPT.json").read_text(encoding="utf-8"))

    require(receipt["decision"] == "PASS_AGGREGATE_ONLY_MANUSCRIPT_ASSET_BUILD", "asset receipt decision", checks)
    require(receipt["scientific_fits"] == 0, "asset receipt records zero fits", checks)
    require(receipt["model_forwards"] == 0, "asset receipt records zero model forwards", checks)
    require(receipt["gold_or_answer_text_read"] is False, "asset receipt records no Gold or answer-text read", checks)
    require(
        receipt["sources"]
        == {
            "outputs/cas_q2/empirical_analysis_v1/INTERVALS.json": "6d454afeec7c125c0cc4d182556af6db214a867aa4f62f7a6fbd1e6e22b09331",
            "outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json": "b03ddad8fa35f582a63403c029942104c3f5da1a961110edc2a62f09871f4d3b",
        },
        "private aggregate hashes remain declared without reading those files",
        checks,
    )
    for relative, expected in sorted(receipt["outputs"].items()):
        path = ROOT / relative
        require(path.is_file(), f"committed reporting asset exists: {relative}", checks)
        require(digest(path) == expected, f"committed reporting asset hash: {relative}", checks)

    abstract_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", manuscript, re.S)
    require(abstract_match is not None, "abstract exists", checks)
    abstract_words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+%-]*", abstract_match.group(1)))
    require(100 <= abstract_words <= 250, "journal-neutral abstract remains within bounded public range", checks)

    bib_keys = set(re.findall(r"^@\w+\{([^,]+),", bibliography, re.M))
    cited: set[str] = set()
    for group in re.findall(r"\\cite[pt]?\{([^}]+)\}", manuscript):
        cited.update(item.strip() for item in group.split(","))
    require(bool(cited), "manuscript contains citations", checks)
    require(cited == bib_keys, "all and only bibliography records are cited", checks)

    for label, text in (("manuscript", manuscript), ("supplement", supplement)):
        require(
            sorted(re.findall(r"\\begin\{([^}]+)\}", text))
            == sorted(re.findall(r"\\end\{([^}]+)\}", text)),
            f"{label} environments are balanced",
            checks,
        )
        require(text.rstrip().endswith(r"\end{document}"), f"{label} terminates", checks)

    required_claims = (
        "does not pass against the HGB-only policy",
        "does not advance over the two-signal policy",
        "rather than a new selector architecture",
        "one 3B-parameter Qwen reader",
        "original per-estimator fit-time ID/matrix receipts",
        "no external record independently certifies its timestamp",
    )
    for marker in required_claims:
        require(marker in manuscript, f"bounded manuscript claim retained: {marker}", checks)

    for marker in (
        "ROA-FULL - HGB_GBV_R",
        "HGB_GBV_R - HGB_ONLY_R",
        "HGB_GBV_R - GBV_ONLY_R",
        "does not support method novelty",
        "Phi evidence terminated",
        "Mistral extension",
        "stopped before engineering",
    ):
        require(marker in summary_flat, f"public claim summary retains: {marker}", checks)

    require("6,000 question groups and 18,000 traces" in readme, "public population statement", checks)
    require("900 traces" in readme, "public allocation statement", checks)
    require("cannot regenerate candidates" in availability.lower(), "public reproduction boundary", checks)
    require("Anonymous authors" in manuscript, "anonymous manuscript author surface", checks)
    require("qianxingji" not in manuscript.lower(), "local identity absent from manuscript", checks)
    require(not re.search(r"(?<![A-Za-z])[A-Za-z]:[/\\]", manuscript), "absolute Windows paths absent from manuscript", checks)
    require(not re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", manuscript), "email addresses absent from manuscript", checks)

    result = {
        "schema_version": 1,
        "decision": "PASS_COMMITTED_PUBLIC_REPORTING_SURFACE_ONLY",
        "checks": len(checks),
        "abstract_word_count": abstract_words,
        "committed_asset_hashes_verified": len(receipt["outputs"]),
        "private_scientific_outputs_read": False,
        "private_aggregate_hashes_authenticated": False,
        "bootstrap_recomputed": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
