#!/usr/bin/env python3
"""Build ignored identity/declaration drafts from validated private owner inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.verify_cas_q3_owner_inputs import ROOT, validate
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from verify_cas_q3_owner_inputs import ROOT, validate


DEFAULT_INPUT = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"
DEFAULT_OUTPUT = ROOT / "output" / "private_submission"
MANUSCRIPT_TITLE = "Supervision-Matched Selection of Paired RAG Repairs: An Empirical Study of Accuracy and Damage"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tex(value: Any) -> str:
    mapping = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "#": r"\#",
        "$": r"\$",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(character, character) for character in str(value))


def normalize_statement(value: Any) -> str:
    return " ".join(str(value).split())


def render_title_page(data: dict[str, Any]) -> str:
    authorship = data["authorship"]
    authors = authorship["authors_in_order"]
    affiliations = {item["id"]: item for item in authorship["affiliations"]}
    aff_order = [item["id"] for item in authorship["affiliations"]]
    aff_number = {identifier: index + 1 for index, identifier in enumerate(aff_order)}
    author_parts = []
    for author in authors:
        superscripts = ",".join(str(aff_number[identifier]) for identifier in author["affiliation_ids"])
        author_parts.append(f"{tex(author['name'])}$^{{{superscripts}}}$")
    affiliation_lines = []
    for identifier in aff_order:
        item = affiliations[identifier]
        address = ", ".join(
            tex(item[key]) for key in ("department", "institution", "city", "postal_code", "country")
        )
        affiliation_lines.append(f"$^{{{aff_number[identifier]}}}${address}")
    orcid_lines = [f"{tex(author['name'])}: {tex(author['orcid'])}" for author in authors]
    return "\n".join(
        [
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=1in]{geometry}",
            r"\usepackage[hidelinks]{hyperref}",
            f"\\title{{{tex(MANUSCRIPT_TITLE)}}}",
            "\\author{" + r" \and ".join(author_parts) + "}",
            r"\date{}",
            r"\begin{document}",
            r"\maketitle",
            r"\noindent\textbf{Private draft status:} Generated from owner-supplied facts; independent journal, authority, and final-artifact gates remain open.",
            "",
            r"\section*{Affiliations}",
            r"\\".join(affiliation_lines),
            "",
            r"\section*{Corresponding author}",
            tex(authorship["corresponding_author_name"]) + r"\\" + tex(authorship["corresponding_author_postal_address"]) + r"\\" + tex(authorship["corresponding_author_email"]),
            "",
            r"\section*{ORCID}",
            r"\\".join(orcid_lines),
            r"\end{document}",
            "",
        ]
    )


def render_declarations(data: dict[str, Any]) -> str:
    authorship = data["authorship"]
    declarations = data["declarations"]
    credit_lines = []
    for role, names in authorship["credit_role_mapping"].items():
        if names:
            credit_lines.append(f"\\textbf{{{tex(role)}:}} {tex(', '.join(names))}")
    sections = [
        ("Author contributions", r"\\".join(credit_lines)),
        ("Funding", tex(normalize_statement(declarations["funding_statement"]))),
        ("Competing interests", tex(normalize_statement(declarations["competing_interests_statement"]))),
        ("Ethics approval", tex(normalize_statement(declarations["ethics_statement_or_approval"]))),
        ("Acknowledgements", tex(normalize_statement(declarations["acknowledgements"]))),
        ("Generative AI and writing assistance", tex(normalize_statement(declarations["ai_assistance_statement"]))),
        ("AI tool/version/use dates", tex(normalize_statement(declarations["ai_tool_version_and_use_dates"]))),
        ("Overlapping work or preprint", tex(normalize_statement(declarations["overlapping_work_or_preprint_disclosure"]))),
        ("Institutional manuscript approval evidence", tex(normalize_statement(declarations["institutional_manuscript_approval_evidence"]))),
    ]
    rows = [
        "% Private draft generated from owner-supplied facts; not submission-authorized.",
        r"\section*{Declarations}",
    ]
    for heading, body in sections:
        rows.extend([f"\\subsection*{{{tex(heading)}}}", body, ""])
    rows.extend(
        [
            r"\subsection*{Author approval and originality}",
            "The responsible authors confirmed originality, exclusive submission, and approval of the final manuscript and author order in the private intake. This generated statement remains subject to target-journal form and final independent verification.",
            "",
        ]
    )
    return "\n".join(rows)


def render_cover_letter(data: dict[str, Any]) -> str:
    journal = normalize_statement(data["target_journal"]["selected_journal"])
    corresponding = normalize_statement(data["authorship"]["corresponding_author_name"])
    return f"""# Private cover-letter draft

**Draft status:** Owner facts supplied; independent CAS/journal and final-artifact gates remain open.

**Target journal:** {journal}

**Manuscript title:** {MANUSCRIPT_TITLE}

Dear Editors,

Please consider our Research Article, “{MANUSCRIPT_TITLE}.” The manuscript studies which label-free signals help select between already-generated original and repaired answers under shared candidates, matched development supervision, and a fixed global action allocation.

Across 6,000 question groups and 18,000 traces from three multi-hop QA datasets and three retrieval conditions, HGB+GbV_R improves exact match and reduces full-population Damage relative to the matched GbV-only selector. The same joint rule does not pass against HGB-only, and the larger 25-feature policy does not establish an advance. The paper therefore presents a bounded empirical attribution result rather than a new selector architecture or a reader-general claim.

The responsible authors supplied originality, exclusive-submission, contribution, funding, interest, ethics, acknowledgement, and AI-assistance declarations in the private intake. Their exact target-journal wording and all final artifacts remain subject to independent verification.

Sincerely,

{corresponding}
"""


def build(data: dict[str, Any], output: Path) -> dict[str, Any]:
    validation = validate(data)
    if not validation["complete"]:
        raise ValueError("owner inputs are incomplete or invalid")
    if output.exists():
        raise FileExistsError("output path already exists; use a new versioned private directory")
    output.mkdir(parents=True)
    files = {
        "title_page.tex": render_title_page(data),
        "declarations.tex": render_declarations(data),
        "cover_letter.md": render_cover_letter(data),
    }
    for name, content in files.items():
        (output / name).write_text(content, encoding="utf-8", newline="\n")
    receipt = {
        "schema_version": 1,
        "decision": "PASS_PRIVATE_IDENTITY_DRAFT_BUILD_PENDING_INDEPENDENT_TARGET_AND_FINAL_ARTIFACT_GATES",
        "files": {name: sha256(output / name) for name in sorted(files)},
        "author_count": len(data["authorship"]["authors_in_order"]),
        "affiliation_count": len(data["authorship"]["affiliations"]),
        "personal_values_in_receipt": False,
        "independent_cas_authority_verified": False,
        "target_specific_format_verified": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }
    (output / "PRIVATE_BUILD_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    if not input_path.is_file():
        print(json.dumps({"decision": "FAIL_CLOSED_OWNER_INPUT_FILE_MISSING", "personal_values_emitted": False}))
        return 2
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
        receipt = build(data, output_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"decision": "FAIL_CLOSED_PRIVATE_IDENTITY_DRAFT_BUILD", "error_type": type(exc).__name__, "personal_values_emitted": False}))
        return 2
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
