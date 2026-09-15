#!/usr/bin/env python3
"""Build a private author-populated Applied Intelligence submission candidate.

The builder fails closed on incomplete owner inputs and authenticates the
anonymous complete-source transport before replacing only its front matter and
declaration placeholder.  Its outputs contain private facts and must remain in
an ignored external or ``output/private_submission`` directory.
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

try:
    from scripts.build_cas_q3_private_submission_packet import normalize_statement, render_cover_letter, tex
    from scripts.package_cas_q3_applied_intelligence_transport import deterministic_zip, digest
    from scripts.validate_cas_q3_applied_intelligence_transport import EXPECTED, EPOCH, executable, run
    from scripts.verify_cas_q3_owner_inputs import ROOT, validate
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from build_cas_q3_private_submission_packet import normalize_statement, render_cover_letter, tex
    from package_cas_q3_applied_intelligence_transport import deterministic_zip, digest
    from validate_cas_q3_applied_intelligence_transport import EXPECTED, EPOCH, executable, run
    from verify_cas_q3_owner_inputs import ROOT, validate


DEFAULT_INPUT = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"
DEFAULT_TRANSPORT = Path(
    "E:/paper/ReliableRAG-applied-intelligence-transport-candidate-20260915-policy-a/"
    "applied_intelligence_complete_source_transport_candidate.zip"
)
EXPECTED_TRANSPORT_SHA256 = "d55ffb74cb8f88a9ec261c9a414219f511d92bd10eb4d888f5dbaa185d1c681e"
SOURCE_ARCHIVE_NAME = "applied_intelligence_author_populated_source.zip"

ANONYMOUS_FRONT_MATTER = """\\author[1]{Anonymous \\sur{Authors}}
\\affil[1]{Anonymous affiliation retained pending verified author inputs}"""

DECLARATION_PLACEHOLDER = """\\section*{Declarations}
Author identities, affiliations, contributions, funding, competing interests, institutional ethics wording, acknowledgements, and any required disclosure of writing assistance are maintained in the separate title-page/declarations template and must be completed by the responsible authors before submission."""

AI_METHOD_ANCHOR = "\\section{Results}"


def author_front_matter(data: dict[str, object]) -> str:
    authorship = data["authorship"]
    authors = authorship["authors_in_order"]
    affiliations = authorship["affiliations"]
    affiliation_number = {item["id"]: index + 1 for index, item in enumerate(affiliations)}
    corresponding = authorship["corresponding_author_name"]
    rows: list[str] = []
    for author in authors:
        numbers = ",".join(str(affiliation_number[item]) for item in author["affiliation_ids"])
        marker = "*" if author["name"] == corresponding else ""
        rows.append(f"\\author{marker}[{numbers}]{{{tex(author['name'])}}}")
        if marker:
            rows.append(f"\\email{{{tex(authorship['corresponding_author_email'])}}}")
    for index, affiliation in enumerate(affiliations, start=1):
        star = "*" if index == 1 else ""
        rows.append(
            f"\\affil{star}[{index}]{{"
            f"\\orgdiv{{{tex(affiliation['department'])}}}, "
            f"\\orgname{{{tex(affiliation['institution'])}}}, "
            f"\\orgaddress{{\\city{{{tex(affiliation['city'])}}}, "
            f"\\postcode{{{tex(affiliation['postal_code'])}}}, "
            f"\\country{{{tex(affiliation['country'])}}}}}}}"
        )
    return "\n".join(rows)


def declaration_text(data: dict[str, object]) -> str:
    authorship = data["authorship"]
    declarations = data["declarations"]
    credit = []
    for role, names in authorship["credit_role_mapping"].items():
        if names:
            credit.append(f"{tex(role)}: {tex(', '.join(names))}")
    orcids = []
    for author in authorship["authors_in_order"]:
        if isinstance(author.get("orcid"), str) and author["orcid"].strip() and not author["orcid"].startswith("NONE_"):
            orcids.append(f"{tex(author['name'])}: {tex(author['orcid'])}")
    corresponding = tex(authorship["corresponding_author_name"])
    if isinstance(authorship.get("corresponding_author_postal_address"), str) and authorship["corresponding_author_postal_address"].strip():
        corresponding += "; " + tex(normalize_statement(authorship["corresponding_author_postal_address"]))
    corresponding += "; " + tex(authorship["corresponding_author_email"]) + "."
    rows = [
        r"\section*{Declarations}",
        r"\paragraph{Corresponding author.} " + corresponding,
        r"\paragraph{Author contributions.} " + "; ".join(credit) + ".",
        r"\paragraph{Funding.} " + tex(normalize_statement(declarations["funding_statement"])),
        r"\paragraph{Competing interests.} "
        + tex(normalize_statement(declarations["competing_interests_statement"])),
        r"\paragraph{Ethics approval.} "
        + tex(normalize_statement(declarations["ethics_statement_or_approval"])),
        r"\paragraph{Overlapping work or preprint.} "
        + tex(normalize_statement(declarations["overlapping_work_or_preprint_disclosure"])),
    ]
    if isinstance(declarations.get("acknowledgements"), str) and declarations["acknowledgements"].strip():
        rows.insert(6, r"\paragraph{Acknowledgements.} " + tex(normalize_statement(declarations["acknowledgements"])))
    if orcids:
        rows.append(r"\paragraph{ORCID.} " + "; ".join(orcids) + ".")
    return "\n\n".join(rows)


def ai_method_text(data: dict[str, object]) -> str:
    declarations = data["declarations"]
    return (
        r"\subsection{Generative AI use and human validation}" + "\n"
        + tex(normalize_statement(declarations["ai_assistance_statement"]))
        + " "
        + tex(normalize_statement(declarations["ai_tool_version_and_use_dates"]))
        + "\n\n"
    )


def render_target_source(source: str, data: dict[str, object]) -> str:
    if source.count(ANONYMOUS_FRONT_MATTER) != 1:
        raise AssertionError("anonymous front matter anchor must occur exactly once")
    if source.count(DECLARATION_PLACEHOLDER) != 1:
        raise AssertionError("declaration placeholder anchor must occur exactly once")
    if source.count(AI_METHOD_ANCHOR) != 1:
        raise AssertionError("Methods-to-Results anchor must occur exactly once")
    rendered = source.replace(ANONYMOUS_FRONT_MATTER, author_front_matter(data))
    rendered = rendered.replace(AI_METHOD_ANCHOR, ai_method_text(data) + AI_METHOD_ANCHOR)
    rendered = rendered.replace(DECLARATION_PLACEHOLDER, declaration_text(data))
    if "Anonymous affiliation retained" in rendered or "must be completed by the responsible authors" in rendered:
        raise AssertionError("private target source retains a public placeholder")
    for marker in (
        "The same joint rule does not pass against the HGB-only policy",
        "not a new selector architecture",
        "Public distribution of the aggregate candidate remains withheld",
    ):
        if marker not in rendered:
            raise AssertionError(f"scientific/release boundary missing after render: {marker}")
    return rendered


def compile_source(members: dict[str, bytes], output_pdf: Path) -> dict[str, object]:
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(EPOCH)
    env["FORCE_SOURCE_DATE"] = "1"
    with tempfile.TemporaryDirectory(prefix="reliablerag_ai_private_submission_") as temporary:
        root = Path(temporary)
        for name, payload in members.items():
            (root / name).write_bytes(payload)
        latex = [executable("pdflatex"), "--enable-installer", "--interaction=nonstopmode", "--halt-on-error", "manuscript.tex"]
        run(latex, root, env)
        run([executable("bibtex"), "manuscript"], root, env)
        run(latex, root, env)
        run(latex, root, env)
        log = (root / "manuscript.log").read_text(encoding="utf-8", errors="replace")
        if re.search(r"LaTeX Error|Undefined control sequence|Emergency stop|Fatal error", log, re.I):
            raise AssertionError("private target compilation has a fatal log error")
        if re.search(r"undefined (?:citations?|references?)|Citation .+ undefined|Reference .+ undefined", log, re.I):
            raise AssertionError("private target compilation has an unresolved citation/reference")
        if re.search(r"^Overfull \\[hv]box", log, re.M):
            raise AssertionError("private target compilation has an overfull box")
        visible = run([executable("pdftotext"), "manuscript.pdf", "-"], root, env)
        if "??" in visible or "[?]" in visible:
            raise AssertionError("private target compilation has a visible unresolved marker")
        for forbidden in ("Anonymous affiliation retained", "must be completed by the responsible authors"):
            if forbidden in visible:
                raise AssertionError(f"private target PDF retains placeholder: {forbidden}")
        pdfinfo = run([executable("pdfinfo"), "manuscript.pdf"], root, env)
        pages = int(next(line for line in pdfinfo.splitlines() if line.startswith("Pages:")).split(":", 1)[1])
        font_rows = [row for row in run([executable("pdffonts"), "manuscript.pdf"], root, env).splitlines()[2:] if row.strip()]
        nonembedded = [row for row in font_rows if len(row.split()) >= 5 and row.split()[-5] == "no"]
        type3 = [row for row in font_rows if row.split()[1:3] == ["Type", "3"]]
        if nonembedded or type3:
            raise AssertionError("private target compilation has unacceptable fonts")
        shutil.copyfile(root / "manuscript.pdf", output_pdf)
    return {"pages": pages, "nonembedded_fonts": 0, "type3_fonts": 0}


def build(data: dict[str, object], transport: Path, expected_transport_sha256: str, output: Path) -> dict[str, object]:
    validation = validate(data)
    if not validation["complete"]:
        raise ValueError("owner inputs are incomplete or invalid")
    if data["target_journal"]["selected_journal"] != "Applied Intelligence":
        raise ValueError("private target builder requires Applied Intelligence")
    if output.exists():
        raise FileExistsError("output path already exists; use a new private version directory")
    transport = transport.resolve()
    if not transport.is_file() or digest(transport) != expected_transport_sha256:
        raise AssertionError("anonymous complete-source transport hash mismatch")
    with zipfile.ZipFile(transport) as bundle:
        if bundle.namelist() != EXPECTED:
            raise AssertionError("anonymous transport member allowlist mismatch")
        members = {name: bundle.read(name) for name in EXPECTED}
    source = members["manuscript.tex"].decode("utf-8")
    members["manuscript.tex"] = render_target_source(source, data).encode("utf-8")

    output.mkdir(parents=True)
    archive = output / SOURCE_ARCHIVE_NAME
    deterministic_zip(archive, members)
    pdf = output / "manuscript.pdf"
    compile_result = compile_source(members, pdf)
    cover = output / "cover_letter.md"
    cover.write_text(render_cover_letter(data), encoding="utf-8", newline="\n")
    receipt = {
        "schema_version": 1,
        "decision": "PASS_PRIVATE_APPLIED_INTELLIGENCE_AUTHOR_POPULATED_CANDIDATE_FINAL_AUDITS_OPEN",
        "source_archive_sha256": digest(archive),
        "compiled_pdf_sha256": digest(pdf),
        "cover_letter_sha256": digest(cover),
        "source_members": len(members),
        "compiled_pages": compile_result["pages"],
        "nonembedded_fonts": compile_result["nonembedded_fonts"],
        "type3_fonts": compile_result["type3_fonts"],
        "author_count": len(data["authorship"]["authors_in_order"]),
        "affiliation_count": len(data["authorship"]["affiliations"]),
        "personal_values_in_receipt": False,
        "independent_cas_authority_verified": False,
        "publisher_template_path_accepted": False,
        "final_astra_xhigh_audit_complete": False,
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
    parser.add_argument("--transport", type=Path, default=DEFAULT_TRANSPORT)
    parser.add_argument("--transport-sha256", default=EXPECTED_TRANSPORT_SHA256)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(build(data, args.transport, args.transport_sha256, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
