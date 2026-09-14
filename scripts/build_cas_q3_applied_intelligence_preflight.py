#!/usr/bin/env python3
"""Build a bounded Applied Intelligence preflight with the official SN template.

The journal page inspected on 2026-09-14 still requests ``smallcondensed``,
while the current Springer Nature author-support download supplies ``sn-jnl``.
This script authenticates that download and proves modern-template compilation;
it deliberately does not claim exact journal-template compliance.
"""

from __future__ import annotations

import argparse
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
OUTPUT = ROOT / "output" / "target_profiles" / "applied_intelligence_modern_preflight"
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT.json"
EPOCH = 1789344000  # 2026-09-14 00:00:00 UTC
OFFICIAL_TEMPLATE_SHA256 = "812e76dcaa9c28dc1bff1fb6065d51729b67d4ea140552a05088317414a3ecae"
OFFICIAL_TEMPLATE_URL = (
    "https://cms-resources.apps.public.k8s.springernature.io/"
    "springer-cms/rest/v1/content/18782940/data/v12"
)

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
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {command}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout


def transformed_source(source: str) -> tuple[str, list[dict[str, str]]]:
    changes: list[dict[str, str]] = []
    neutral_preamble = (
        r"\documentclass[11pt]{article}" + "\n"
        r"\usepackage[margin=1in]{geometry}" + "\n"
        r"\usepackage{amsmath,booktabs,longtable,graphicx,microtype}" + "\n"
        r"\usepackage[numbers,sort&compress]{natbib}" + "\n"
        r"\usepackage[hidelinks]{hyperref}" + "\n"
        r"\usepackage{xurl}" + "\n"
        r"\usepackage{caption}" + "\n"
        r"\usepackage{enumitem}"
    )
    modern_preamble = (
        r"\documentclass[pdflatex,sn-basic,Numbered]{sn-jnl}" + "\n"
        r"\usepackage{amsmath,booktabs,longtable,graphicx,microtype}" + "\n"
        r"\usepackage{xurl}" + "\n"
        r"\usepackage{enumitem}"
    )
    if source.count(neutral_preamble) != 1:
        raise AssertionError("expected exactly one journal-neutral preamble")
    source = source.replace(neutral_preamble, modern_preamble)
    changes.append(
        {
            "from": "journal-neutral article preamble",
            "to": "official modern sn-jnl / sn-basic Numbered preamble",
            "scope": "class, bibliography and package compatibility only",
        }
    )

    old_author = r"\author{Anonymous authors}" + "\n" + r"\date{}"
    new_author = (
        r"\author[1]{Anonymous \sur{Authors}}" + "\n"
        r"\affil[1]{Anonymous affiliation retained pending verified author inputs}"
    )
    if source.count(old_author) != 1:
        raise AssertionError("expected exactly one anonymous author block")
    source = source.replace(old_author, new_author)
    changes.append(
        {
            "from": "journal-neutral anonymous author block",
            "to": "sn-jnl anonymous placeholder front matter",
            "scope": "template syntax only; no identity inferred",
        }
    )

    front = re.compile(
        r"\\begin\{document\}\n\\maketitle\n\n"
        r"\\begin\{abstract\}\n(?P<abstract>.*?)\n\\end\{abstract\}\n\n"
        r"\\noindent\\textbf\{Keywords:\}\s*(?P<keywords>[^\n]+)\n",
        re.S,
    )
    match = front.search(source)
    if match is None:
        raise AssertionError("journal-neutral abstract/keyword front matter was not found")
    keywords = ", ".join(part.strip() for part in match.group("keywords").split(";"))
    new_front = (
        "\\begin{document}\n\n"
        f"\\abstract{{{match.group('abstract')}}}\n\n"
        f"\\keywords{{{keywords}}}\n\n"
        "\\maketitle\n"
    )
    source = source[: match.start()] + new_front + source[match.end() :]
    changes.append(
        {
            "from": "article abstract and visible keyword line",
            "to": "sn-jnl abstract and keywords front matter",
            "scope": "front-matter syntax only",
        }
    )

    old_bst = r"\bibliographystyle{plainnat}" + "\n"
    if source.count(old_bst) != 1:
        raise AssertionError("expected exactly one journal-neutral bibliography style")
    source = source.replace(old_bst, "")
    changes.append(
        {
            "from": "plainnat bibliography style",
            "to": "class-selected sn-basic Numbered style",
            "scope": "bibliography presentation only",
        }
    )

    for old, new in FLAT_ASSETS.items():
        if source.count(old) != 1:
            raise AssertionError(f"expected exactly one source reference: {old}")
        source = source.replace(old, new)
        changes.append({"from": old, "to": new, "scope": "flat upload path only"})

    old_design_body = "\\small\n\\input{table_study_design.tex}"
    new_design_body = (
        "\\begingroup\\setlength{\\tabcolsep}{5pt}\n"
        "\\small\n"
        "\\input{table_study_design.tex}\n"
        "\\endgroup"
    )
    if source.count(old_design_body) != 1:
        raise AssertionError("expected exactly one study-design table body")
    source = source.replace(old_design_body, new_design_body)
    changes.append(
        {
            "from": "small study-design table",
            "to": "study-design table with target-local 5pt column padding",
            "scope": "target-layout overflow correction only",
        }
    )

    old_bibliography = r"\bibliography{references}"
    new_bibliography = r"\renewcommand{\bibfont}{\small}" + "\n" + old_bibliography
    if source.count(old_bibliography) != 1:
        raise AssertionError("expected exactly one bibliography command")
    source = source.replace(old_bibliography, new_bibliography)
    changes.append(
        {
            "from": "sn-basic default bibliography font",
            "to": "small bibliography font",
            "scope": "target-layout orphan-page correction only",
        }
    )
    return source, changes


def template_member(bundle: zipfile.ZipFile, suffix: str) -> bytes:
    matches = [name for name in bundle.namelist() if name.replace("\\", "/").endswith(suffix)]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one official template member ending in {suffix}: {matches}")
    return bundle.read(matches[0])


def deterministic_zip(path: Path, members: list[Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for member in sorted(members, key=lambda item: item.name):
            info = zipfile.ZipInfo(member.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, member.read_bytes())


def build(template_zip: Path) -> dict[str, object]:
    template_zip = template_zip.resolve()
    if not template_zip.is_file():
        raise FileNotFoundError(template_zip)
    if sha256(template_zip) != OFFICIAL_TEMPLATE_SHA256:
        raise AssertionError("Springer Nature template ZIP hash does not match the inspected official download")

    original_hash = sha256(SOURCE)
    source_text = SOURCE.read_text(encoding="utf-8")
    converted, changes = transformed_source(source_text)
    abstract = re.search(r"\\abstract\{(.*?)\}\n\n\\keywords", converted, re.S)
    keyword_match = re.search(r"\\keywords\{(.*?)\}", converted)
    if abstract is None or keyword_match is None:
        raise AssertionError("converted abstract or keywords missing")
    abstract_words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+%-]*", abstract.group(1)))
    keyword_count = len([part for part in keyword_match.group(1).split(",") if part.strip()])
    if not 150 <= abstract_words <= 250 or not 4 <= keyword_count <= 6:
        raise AssertionError("converted abstract or keyword count is outside the selected-journal range")

    with zipfile.ZipFile(template_zip) as bundle:
        class_bytes = template_member(bundle, "/sn-jnl.cls")
        bst_bytes = template_member(bundle, "/bst/sn-basic.bst")

    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(EPOCH)
    env["FORCE_SOURCE_DATE"] = "1"
    pdflatex = executable("pdflatex")
    bibtex = executable("bibtex")
    engine_version = run([pdflatex, "--version"], ROOT, env).splitlines()[0]

    with tempfile.TemporaryDirectory(prefix="reliablerag_applied_intelligence_preflight_") as tmp_name:
        tmp = Path(tmp_name)
        (tmp / "manuscript.tex").write_text(converted, encoding="utf-8", newline="\n")
        (tmp / "sn-jnl.cls").write_bytes(class_bytes)
        (tmp / "sn-basic.bst").write_bytes(bst_bytes)
        shutil.copy2(PAPER / "references.bib", tmp / "references.bib")
        for old, new in FLAT_ASSETS.items():
            shutil.copy2(PAPER / old, tmp / new)

        latex_args = [pdflatex, "--enable-installer", "--interaction=nonstopmode", "--halt-on-error", "manuscript.tex"]
        run(latex_args, tmp, env)
        run([bibtex, "manuscript"], tmp, env)
        run(latex_args, tmp, env)
        run(latex_args, tmp, env)

        log_text = (tmp / "manuscript.log").read_text(encoding="utf-8", errors="replace")
        fatal_errors = re.findall(r"(?:LaTeX Error|Undefined control sequence|Emergency stop|Fatal error)", log_text, re.I)
        undefined_references = re.findall(
            r"undefined (?:citations?|references?)|Citation .+ undefined|Reference .+ undefined", log_text, re.I
        )
        overfull_warnings = re.findall(r"^Overfull \\[hv]box.*$", log_text, re.M)
        underfull_warnings = re.findall(r"^Underfull \\[hv]box.*$", log_text, re.M)
        visible_text = run([executable("pdftotext"), str(tmp / "manuscript.pdf"), "-"], tmp, env)
        unresolved_markers = visible_text.count("??") + visible_text.count("[?]")
        if fatal_errors or undefined_references or overfull_warnings or unresolved_markers:
            raise AssertionError(
                {
                    "fatal_errors": fatal_errors,
                    "undefined_references": undefined_references,
                    "overfull_warnings": overfull_warnings,
                    "underfull_warnings": underfull_warnings,
                    "unresolved_markers": unresolved_markers,
                }
            )
        if sha256(SOURCE) != original_hash:
            raise AssertionError("journal-neutral manuscript changed during target preflight")

        OUTPUT.mkdir(parents=True, exist_ok=True)
        pdf = OUTPUT / "manuscript_sn_jnl_preflight.pdf"
        source_zip = OUTPUT / "applied_intelligence_authored_source_preflight.zip"
        shutil.copy2(tmp / "manuscript.pdf", pdf)
        authored_members = [
            tmp / "manuscript.tex",
            tmp / "references.bib",
            tmp / "manuscript.bbl",
            *(tmp / name for name in FLAT_ASSETS.values()),
        ]
        deterministic_zip(source_zip, authored_members)

        pdfinfo = run([executable("pdfinfo"), str(pdf)], tmp, env)
        pages = int(next(line for line in pdfinfo.splitlines() if line.startswith("Pages:")).split(":", 1)[1])
        font_rows = [row for row in run([executable("pdffonts"), str(pdf)], tmp, env).splitlines()[2:] if row.strip()]
        nonembedded = [row for row in font_rows if len(row.split()) >= 5 and row.split()[-5] == "no"]
        type3 = [row for row in font_rows if row.split()[1:3] == ["Type", "3"]]
        with zipfile.ZipFile(source_zip) as authored:
            source_members = authored.namelist()
            nested_members = [name for name in source_members if "/" in name or "\\" in name]

    if nonembedded or type3 or nested_members:
        raise AssertionError("modern target preflight failed font or flat authored-source checks")

    result = {
        "schema_version": 1,
        "decision": "PARTIAL_PASS_APPLIED_INTELLIGENCE_MODERN_SN_JNL_PREFLIGHT_SMALLCONDENSED_EQUIVALENCE_OPEN",
        "cas_q3_status": "NOT_READY",
        "target_journal": "Applied Intelligence",
        "target_selected": True,
        "submission_authorized": False,
        "distribution_authorized": False,
        "official_sources_checked_local_date": "2026-09-14",
        "official_sources": [
            "https://link.springer.com/journal/10489/submission-guidelines",
            "https://www.springernature.com/gp/authors/campaigns/latex-author-support",
            OFFICIAL_TEMPLATE_URL,
        ],
        "template_dependency": {
            "official_download_sha256": OFFICIAL_TEMPLATE_SHA256,
            "sn_jnl_class_sha256": hashlib.sha256(class_bytes).hexdigest(),
            "sn_basic_bst_sha256": hashlib.sha256(bst_bytes).hexdigest(),
            "version_label": "Version 3.1 December 2024",
            "files_redistributed_in_repository_or_authored_source_zip": False,
        },
        "runtime": {
            "pdftex": engine_version,
            "latex_format": "LaTeX2e 2025-11-01",
            "class_required_package_observed": "sttools/cuted.sty",
        },
        "profile": {
            "class": "sn-jnl",
            "class_options": ["pdflatex", "sn-basic", "Numbered"],
            "abstract_words": abstract_words,
            "keywords": keyword_count,
            "numeric_citations": True,
            "flat_authored_source_archive": True,
            "smallcondensed_requested_on_journal_page": True,
            "smallcondensed_profile_used": False,
            "sn_jnl_equivalent_to_journal_smallcondensed_proved": False,
        },
        "compile_checks": {
            "fatal_errors": len(fatal_errors),
            "undefined_citations_or_references": len(undefined_references),
            "overfull_boxes": len(overfull_warnings),
            "underfull_boxes": len(underfull_warnings),
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
            "authored_source_zip": str(source_zip.relative_to(ROOT)).replace("\\", "/"),
            "authored_source_zip_sha256": sha256(source_zip),
            "authored_source_zip_members": source_members,
            "authored_source_zip_nested_members": nested_members,
            "template_dependency_included": False,
        },
        "open_gates": [
            "resolve the journal-page smallcondensed versus current sn-jnl package conflict",
            "complete verified author, affiliation, correspondence and declaration facts",
            "complete release review and create a corrected license-bearing archive",
            "retain the institution-recognized current-title and ISSN CAS record",
            "complete target-package visual inspection",
            "complete final GPT-6 Astra xhigh artifact, fairness, Claim and reviewer audit",
        ],
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
    }
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--template-zip",
        type=Path,
        default=os.environ.get("SPRINGER_NATURE_TEMPLATE_ZIP"),
        required=os.environ.get("SPRINGER_NATURE_TEMPLATE_ZIP") is None,
        help="Official December 2024 Springer Nature LaTeX template ZIP",
    )
    args = parser.parse_args()
    result = build(args.template_zip)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
