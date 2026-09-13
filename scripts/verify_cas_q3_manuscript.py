#!/usr/bin/env python3
"""Independently verify the CAS Q3 manuscript package and claim boundary."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"


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
    bib = (PAPER / "references.bib").read_text(encoding="utf-8")
    receipt = json.loads((PAPER / "ASSET_RECEIPT.json").read_text(encoding="utf-8"))
    point_path = ROOT / "outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json"
    interval_path = ROOT / "outputs/cas_q2/empirical_analysis_v1/INTERVALS.json"

    require(receipt["decision"] == "PASS_AGGREGATE_ONLY_MANUSCRIPT_ASSET_BUILD", "asset receipt passes", checks)
    require(receipt["scientific_fits"] == 0 and receipt["model_forwards"] == 0, "asset build ran no fits or model forwards", checks)
    require(receipt["gold_or_answer_text_read"] is False, "asset build did not read Gold or answer text", checks)
    require(digest(point_path) == receipt["sources"]["outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json"], "sealed point-estimate source hash matches receipt", checks)
    require(digest(interval_path) == receipt["sources"]["outputs/cas_q2/empirical_analysis_v1/INTERVALS.json"], "sealed interval source hash matches receipt", checks)
    for rel, expected in receipt["outputs"].items():
        require(digest(ROOT / rel) == expected, f"asset hash matches: {rel}", checks)

    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", manuscript, re.S)
    require(abstract is not None, "abstract exists", checks)
    abstract_words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+%-]*", abstract.group(1)))
    require(abstract_words <= 150, "abstract is at most 150 words", checks)

    bib_keys = set(re.findall(r"^@\w+\{([^,]+),", bib, re.M))
    cited: set[str] = set()
    for group in re.findall(r"\\cite[pt]?\{([^}]+)\}", manuscript):
        cited.update(x.strip() for x in group.split(","))
    require(bool(cited), "manuscript contains citations", checks)
    require(cited <= bib_keys, "all citation keys resolve", checks)
    require(bib_keys <= cited, "all bibliography records are used", checks)

    for text_name, text in (("manuscript", manuscript), ("supplement", supplement)):
        begins = re.findall(r"\\begin\{([^}]+)\}", text)
        ends = re.findall(r"\\end\{([^}]+)\}", text)
        require(sorted(begins) == sorted(ends), f"{text_name} environments are balanced", checks)
        require(text.rstrip().endswith(r"\end{document}"), f"{text_name} has document terminator", checks)

    main_table = (PAPER / "tables" / "main_results.tex").read_text(encoding="utf-8")
    comparison_table = (PAPER / "tables" / "primary_comparisons.tex").read_text(encoding="utf-8")
    points = json.loads(point_path.read_text(encoding="utf-8"))
    policies = ["Keep", "HGB", "GbV", "ROA-FULL", "ROA-NOGBV", "HGB+GbV", "HGB-only", "GbV-only", "V2"]
    for policy in policies:
        require(policy in main_table, f"complete table contains {policy}", checks)
    require(main_table.count(r"\\") == 10, "complete table has one header and nine policy rows", checks)
    display = {"HGB_GBV_R": r"HGB+GbV$_R$", "HGB_ONLY_R": r"HGB-only$_R$", "GBV_ONLY_R": r"GbV-only$_R$"}
    for policy, row in points["policies"].items():
        expected = (
            f"{display.get(policy, policy)} & {row['replacements']:,} & {row['recovery']:,} & "
            f"{row['damage']:,} & {row['neutral']:,} & {row['net']:+,} & "
            f"{100*row['em_rate']:.4f} & {row['delta_em_pp']:+.4f} & "
            f"{100*row['token_f1']:.4f} & {row['delta_f1_pp']:+.4f} & "
            f"{row['damage_rate_pp']:.4f}"
        )
        require(expected in main_table, f"complete table exactly matches sealed row: {policy}", checks)

    for dimension in ("dataset", "retriever"):
        table = (PAPER / "tables" / f"{dimension}_breakdown.tex").read_text(encoding="utf-8")
        for cell in points["fixed_global_action_breakdowns"][dimension]:
            label = cell["cell"].replace("_", r"\_")
            for policy, row in cell["policies"].items():
                expected = (
                    f"{label} & {display.get(policy, policy)} & {row['replacements']:,} & "
                    f"{row['recovery']:,} & {row['damage']:,} & {row['net']:+,} & "
                    f"{row['delta_em_pp']:+.4f} & {row['delta_f1_pp']:+.4f}"
                )
                require(expected in table, f"{dimension} table matches sealed row: {cell['cell']}/{policy}", checks)

    required_numeric = [
        "+0.2333", "[+0.0722, +0.4333]", "-0.0722", "[-0.1444, -0.0278]",
        "+0.0556", "[-0.1556, +0.3167]", "-0.0833", "[-0.1833, -0.0056]",
        "+0.0444", "[-0.1333, +0.2037]", "+0.0611", "[+0.0000, +0.1278]",
    ]
    for value in required_numeric:
        require(value in comparison_table, f"primary table contains {value}", checks)
    require(comparison_table.count("Not met") == 2 and comparison_table.count(" & Met") == 1, "primary table retains one pass and two failures", checks)

    lower = manuscript.lower()
    require("does not pass against the hgb-only policy" in lower, "abstract states failed HGB-only joint comparison", checks)
    require("does not advance over the two-signal policy" in lower, "abstract states failed ROA advancement", checks)
    require("rather than a new selector architecture" in lower, "abstract bounds method novelty", checks)
    require("one 3b-parameter qwen reader" in lower, "single-reader limitation is explicit", checks)
    require("public distribution is withheld" in lower, "license-dependent release boundary is explicit", checks)
    require("were not measured" in lower, "missing deployment measurements are explicit", checks)

    prohibited_assertions = [
        r"we propose (?:a )?novel", r"state[- ]of[- ]the[- ]art", r"reader[- ]agnostic",
        r"guarantees? (?:low )?damage",
        r"outperforms? hgb-only", r"superior to hgb-only",
    ]
    for pattern in prohibited_assertions:
        require(re.search(pattern, lower) is None, f"prohibited assertion absent: {pattern}", checks)

    require("[AUTHOR" not in manuscript and "[AFFILIATION" not in manuscript, "anonymous main manuscript has no author placeholders", checks)
    require("qianx" not in lower and "@" not in manuscript, "anonymous main manuscript has no local identity or email", checks)
    require(re.search(r"\b[A-Za-z]:[\\/][A-Za-z0-9_.-]", manuscript) is None, "anonymous main manuscript has no absolute Windows path", checks)
    require("Anonymous authors" in manuscript, "anonymous author surface is explicit", checks)

    for rel in ("figures/paired_pipeline.pdf", "figures/recovery_damage.pdf"):
        payload = (PAPER / rel).read_bytes()
        require(
            re.match(rb"%PDF-1\.[0-9]", payload) is not None and b"%%EOF" in payload[-64:],
            f"PDF structure present: {rel}",
            checks,
        )

    result = {
        "schema_version": 1,
        "decision": "PASS_MANUSCRIPT_STATIC_AND_CLAIM_CHECKS",
        "check_count": len(checks),
        "abstract_word_count": abstract_words,
        "bibliography_entries": len(bib_keys),
        "checks": checks,
        "limitations": [
            "compiled_PDF_mechanical_and_visual_checks_are_recorded_separately",
            "author_declarations_pending",
            "project_license_pending",
            "CAS_Q3_journal_qualification_pending",
            "final_Astra_xhigh_rebind_pending_after_target_specific_conversion",
        ],
    }
    out = PAPER / "MANUSCRIPT_VERIFICATION.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
