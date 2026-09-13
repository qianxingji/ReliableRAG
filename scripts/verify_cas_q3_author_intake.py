#!/usr/bin/env python3
"""Verify the author/declaration intake and compile its placeholder title page."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "docs" / "cas_q3" / "P0_I_AUTHOR_DECLARATION_INTAKE.md"
TITLE = ROOT / "paper" / "title_page_template.tex"
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_AUTHOR_INTAKE_VERIFICATION.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    local = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64" / f"{name}.exe"
    if local.is_file():
        return str(local)
    raise RuntimeError(f"missing executable: {name}")


def main() -> int:
    checks = 0
    intake = INTAKE.read_text(encoding="utf-8")
    title = TITLE.read_text(encoding="utf-8")
    required_intake = (
        "Authors in order:",
        "CRediT role mapping:",
        "Funding statement:",
        "Competing interests:",
        "Ethics statement",
        "AI/writing-assistance disclosure",
        "Originality/exclusive-submission/all-author approval",
        "No identity or declaration guessed".upper(),
    )
    for marker in required_intake:
        checks += 1
        if marker not in intake:
            raise AssertionError(f"missing intake marker: {marker}")
    required_title = (
        "[AUTHOR NAMES AND ORDER REQUIRED]",
        "[AFFILIATIONS REQUIRED]",
        "[CRediT ROLES AND AUTHOR APPROVAL REQUIRED]",
        "[AUTHOR-CONFIRMED DECLARATION REQUIRED]",
        "Generative AI and writing assistance",
        "Data and code availability",
        "Author approval and originality",
    )
    for marker in required_title:
        checks += 1
        if marker not in title:
            raise AssertionError(f"missing title-page marker: {marker}")
    checks += 1
    if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", title, re.I):
        raise AssertionError("title-page template contains a populated email")

    pdflatex = executable("pdflatex")
    pdfinfo = executable("pdfinfo")
    with tempfile.TemporaryDirectory(prefix="cas_q3_title_page_") as temporary:
        process = subprocess.run(
            [pdflatex, "--enable-installer", "--interaction=nonstopmode", "--halt-on-error", f"-output-directory={temporary}", str(TITLE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
        checks += 1
        if process.returncode != 0:
            raise AssertionError(process.stdout[-3000:] + process.stderr[-3000:])
        pdf = Path(temporary) / "title_page_template.pdf"
        checks += 1
        if not pdf.is_file():
            raise AssertionError("title-page PDF missing")
        info = subprocess.run([pdfinfo, str(pdf)], check=True, capture_output=True, text=True, errors="replace").stdout
        match = re.search(r"^Pages:\s+(\d+)", info, re.M)
        pages = int(match.group(1)) if match else 0
        checks += 1
        if pages != 2:
            raise AssertionError(f"unexpected placeholder title-page count: {pages}")

    result = {
        "schema_version": 1,
        "decision": "PASS_AUTHOR_INTAKE_STRUCTURE_AND_PLACEHOLDER_TITLE_PAGE_COMPILE",
        "checks": checks,
        "title_page_pages": pages,
        "title_page_template_sha256": sha(TITLE),
        "author_intake_sha256": sha(INTAKE),
        "author_facts_populated": False,
        "author_identity_guessed": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
