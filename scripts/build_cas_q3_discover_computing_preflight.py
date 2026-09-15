#!/usr/bin/env python3
"""Build a non-submittable Discover Computing technical preflight package."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SOURCE = PAPER / "manuscript.tex"
OUTPUT = ROOT / "output" / "target_profiles" / "discover_computing_preflight"
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_DISCOVER_COMPUTING_PREFLIGHT.json"
EPOCH = 1789344000  # 2026-09-14 00:00:00 UTC

FLAT_ASSETS = {
    "figures/paired_pipeline.pdf": "Fig1.pdf",
    "figures/recovery_damage.pdf": "Fig2.pdf",
    "tables/study_design.tex": "table_study_design.tex",
    "tables/main_results.tex": "table_main_results.tex",
    "tables/primary_comparisons.tex": "table_primary_comparisons.tex",
}


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


def run(command: list[str], cwd: Path, env: dict[str, str]) -> str:
    completed = subprocess.run(command, cwd=cwd, env=env, check=True, capture_output=True, text=True, errors="replace")
    return completed.stdout


def transformed_source(source: str) -> tuple[str, list[dict[str, str]]]:
    changes: list[dict[str, str]] = []
    old_class = r"\documentclass[11pt]{article}"
    new_class = r"\documentclass[12pt]{article}"
    if source.count(old_class) != 1:
        raise AssertionError("expected exactly one journal-neutral 11pt document class")
    source = source.replace(old_class, new_class)
    changes.append({"from": old_class, "to": new_class, "scope": "font-size profile only"})
    for old, new in FLAT_ASSETS.items():
        if source.count(old) != 1:
            raise AssertionError(f"expected exactly one source reference: {old}")
        source = source.replace(old, new)
        changes.append({"from": old, "to": new, "scope": "flat upload path only"})
    return source, changes


def deterministic_zip(path: Path, members: list[Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for member in sorted(members, key=lambda item: item.name):
            info = zipfile.ZipInfo(member.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, member.read_bytes())


def build() -> dict[str, object]:
    original_hash = sha256(SOURCE)
    source_text = SOURCE.read_text(encoding="utf-8")
    converted, changes = transformed_source(source_text)
    if r"\usepackage[numbers,sort&compress]{natbib}" not in converted:
        raise AssertionError("numeric citation profile is missing")

    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(EPOCH)
    env["FORCE_SOURCE_DATE"] = "1"
    pdflatex = executable("pdflatex")
    bibtex = executable("bibtex")

    with tempfile.TemporaryDirectory(prefix="reliablerag_discover_preflight_") as tmp_name:
        tmp = Path(tmp_name)
        (tmp / "manuscript.tex").write_text(converted, encoding="utf-8", newline="\n")
        shutil.copy2(PAPER / "references.bib", tmp / "references.bib")
        for old, new in FLAT_ASSETS.items():
            shutil.copy2(PAPER / old, tmp / new)

        latex_args = [pdflatex, "--enable-installer", "--interaction=nonstopmode", "--halt-on-error", "manuscript.tex"]
        run(latex_args, tmp, env)
        run([bibtex, "manuscript"], tmp, env)
        run(latex_args, tmp, env)
        run(latex_args, tmp, env)

        log_text = (tmp / "manuscript.log").read_text(encoding="utf-8", errors="replace")
        fatal_errors = re.findall(
            r"(?:LaTeX Error|Undefined control sequence|Emergency stop|Fatal error)", log_text, re.I
        )
        undefined_references = re.findall(
            r"undefined (?:citations?|references?)|Citation .+ undefined|Reference .+ undefined", log_text, re.I
        )
        box_warnings = re.findall(r"(?:Overfull|Underfull) \\[hv]box", log_text)
        visible_text = run([executable("pdftotext"), str(tmp / "manuscript.pdf"), "-"], tmp, env)
        unresolved_markers = visible_text.count("??") + visible_text.count("[?]")
        if fatal_errors or undefined_references or box_warnings or unresolved_markers:
            raise AssertionError(
                {
                    "fatal_errors": fatal_errors,
                    "undefined_references": undefined_references,
                    "box_warnings": box_warnings,
                    "unresolved_markers": unresolved_markers,
                }
            )

        if sha256(SOURCE) != original_hash:
            raise AssertionError("journal-neutral manuscript changed during preflight build")

        OUTPUT.mkdir(parents=True, exist_ok=True)
        pdf = OUTPUT / "manuscript_12pt_preflight.pdf"
        source_zip = OUTPUT / "discover_computing_source_preflight.zip"
        shutil.copy2(tmp / "manuscript.pdf", pdf)
        members = [
            tmp / "manuscript.tex",
            tmp / "references.bib",
            tmp / "manuscript.bbl",
            *(tmp / name for name in FLAT_ASSETS.values()),
        ]
        deterministic_zip(source_zip, members)

        pdfinfo = run([executable("pdfinfo"), str(pdf)], tmp, env)
        page_line = next(line for line in pdfinfo.splitlines() if line.startswith("Pages:"))
        pages = int(page_line.split(":", 1)[1].strip())
        font_rows = [row for row in run([executable("pdffonts"), str(pdf)], tmp, env).splitlines()[2:] if row.strip()]
        nonembedded = [row.split()[0] for row in font_rows if len(row.split()) >= 5 and row.split()[-5] == "no"]
        type3 = [row.split()[0] for row in font_rows if row.split()[1:3] == ["Type", "3"]]
        with zipfile.ZipFile(source_zip) as bundle:
            zip_members = bundle.namelist()
            nested_members = [name for name in zip_members if "/" in name or "\\" in name]

    result = {
        "schema_version": 1,
        "decision": "PASS_DISCOVER_COMPUTING_PROVISIONAL_TECHNICAL_PREFLIGHT_EXTERNAL_GATES_OPEN",
        "cas_q3_status": "NOT_READY",
        "target_journal": "Discover Computing",
        "article_type_profile": "Research",
        "final_target_selected": False,
        "institutional_cas_q3_qualification_verified": False,
        "submission_authorized": False,
        "distribution_authorized": False,
        "official_sources_checked_local_date": "2026-09-14",
        "official_sources": [
            "https://link.springer.com/journal/10791/submission-guidelines",
            "https://link.springer.com/journal/10791/aims-and-scope",
            "https://www.springernature.com/gp/authors/campaigns/latex-author-support",
        ],
        "profile": {
            "abstract_words": 142,
            "abstract_limit_words_exclusive": 250,
            "main_text_pt": 12,
            "numeric_citations": True,
            "flat_source_archive": True,
            "pdflatex_build": "PASS",
            "springer_nature_template_applied": False,
            "generic_article_class_is_final_journal_format": False,
        },
        "compile_checks": {
            "fatal_errors": len(fatal_errors),
            "undefined_citations_or_references": len(undefined_references),
            "overfull_or_underfull_boxes": len(box_warnings),
            "unresolved_markers": unresolved_markers,
        },
        "source_protection": {
            "journal_neutral_source_sha256_before_and_after": original_hash,
            "allowed_transformation_count": len(changes),
            "allowed_transformations": changes,
            "scientific_prose_or_numbers_changed": False,
        },
        "artifacts": {
            "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
            "pdf_sha256": sha256(pdf),
            "pdf_pages": pages,
            "pdf_font_rows": len(font_rows),
            "pdf_nonembedded_font_rows": nonembedded,
            "pdf_type3_font_rows": type3,
            "source_zip": str(source_zip.relative_to(ROOT)).replace("\\", "/"),
            "source_zip_sha256": sha256(source_zip),
            "source_zip_members": zip_members,
            "source_zip_nested_members": nested_members,
            "unchanged_journal_neutral_supplement": "output/pdf/supplement.pdf",
            "unchanged_journal_neutral_supplement_sha256": sha256(ROOT / "output" / "pdf" / "supplement.pdf"),
        },
        "open_external_or_final_gates": [
            "responsible-author identities, affiliations and corresponding-author details",
            "author contributions, mandatory funding statement, competing interests and approvals",
            "final ethics, acknowledgements and assistance disclosures",
            "cover letter and Snapp field completion",
            "owner acceptance of open-access fees or confirmed funding route",
            "project license and journal data/code-release policy",
            "institution-recognized CAS edition, category and current-title continuity rule",
            "final target-journal selection and exact final template/profile conversion",
            "final GPT-6 Astra xhigh artifact, fairness, claim and Submission Ready audit",
        ],
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
    }
    if nonembedded or type3 or nested_members:
        raise AssertionError("preflight artifact failed font or flat-archive checks")
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    result = build()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
