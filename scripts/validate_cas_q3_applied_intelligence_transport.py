#!/usr/bin/env python3
"""Validate and clean-compile the private Applied Intelligence transport ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_cas_q3_applied_intelligence_preflight import OFFICIAL_TEMPLATE_SHA256
from scripts.package_cas_q3_applied_intelligence_transport import (
    AUTHORED_MEMBERS,
    TEMPLATE_MEMBERS,
    digest,
    safe_flat_member,
)


PREFLIGHT_RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT.json"
EXPECTED = sorted(AUTHORED_MEMBERS + TEMPLATE_MEMBERS)
EPOCH = 1789344000


class Checks:
    def __init__(self) -> None:
        self.count = 0

    def require(self, condition: bool, message: str) -> None:
        self.count += 1
        if not condition:
            raise AssertionError(message)


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
    completed = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, errors="replace")
    if completed.returncode:
        raise RuntimeError(f"command failed: {command}\n{completed.stdout}\n{completed.stderr}")
    return completed.stdout


def validate(archive: Path, expected_sha256: str) -> dict[str, object]:
    checks = Checks()
    archive = archive.resolve()
    checks.require(archive.is_file(), "archive exists")
    checks.require(digest(archive) == expected_sha256, "archive hash matches")
    preflight = json.loads(PREFLIGHT_RECEIPT.read_text(encoding="utf-8"))
    authored_path = ROOT / preflight["artifacts"]["authored_source_zip"]
    checks.require(digest(authored_path) == preflight["artifacts"]["authored_source_zip_sha256"], "authored ZIP pin")
    with zipfile.ZipFile(authored_path) as authored:
        authored_hashes = {name: hashlib.sha256(authored.read(name)).hexdigest() for name in authored.namelist()}

    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        names = bundle.namelist()
        checks.require(names == EXPECTED, "exact transport allowlist")
        checks.require(len(names) == len(set(names)) == 10, "ten unique members")
        for info in infos:
            checks.require(safe_flat_member(info.filename), f"safe flat path: {info.filename}")
            mode = info.external_attr >> 16
            checks.require(not stat.S_ISLNK(mode), f"not symlink: {info.filename}")
            checks.require(info.file_size > 0, f"nonempty member: {info.filename}")
        payloads = {name: bundle.read(name) for name in names}

    for name in AUTHORED_MEMBERS:
        checks.require(hashlib.sha256(payloads[name]).hexdigest() == authored_hashes[name], f"authored byte pin: {name}")
    checks.require(
        hashlib.sha256(payloads["sn-jnl.cls"]).hexdigest()
        == preflight["template_dependency"]["sn_jnl_class_sha256"],
        "official sn-jnl class pin",
    )
    checks.require(
        hashlib.sha256(payloads["sn-basic.bst"]).hexdigest()
        == preflight["template_dependency"]["sn_basic_bst_sha256"],
        "official sn-basic style pin",
    )
    source = payloads["manuscript.tex"].decode("utf-8")
    checks.require(r"\documentclass[pdflatex,sn-basic,Numbered]{sn-jnl}" in source, "modern class source")
    checks.require("Anonymous" in source and "qianxingji" not in source.lower() and "@" not in source, "anonymous source")
    checks.require("The same joint rule does not pass against the HGB-only policy" in source, "negative Claim retained")
    checks.require("not a new selector architecture" in source, "novelty boundary retained")

    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(EPOCH)
    env["FORCE_SOURCE_DATE"] = "1"
    with tempfile.TemporaryDirectory(prefix="reliablerag_ai_transport_validate_") as tmp_name:
        tmp = Path(tmp_name)
        for name, data in payloads.items():
            (tmp / name).write_bytes(data)
        latex = [executable("pdflatex"), "--enable-installer", "--interaction=nonstopmode", "--halt-on-error", "manuscript.tex"]
        run(latex, tmp, env)
        run([executable("bibtex"), "manuscript"], tmp, env)
        run(latex, tmp, env)
        run(latex, tmp, env)
        log = (tmp / "manuscript.log").read_text(encoding="utf-8", errors="replace")
        checks.require(not re.search(r"LaTeX Error|Undefined control sequence|Emergency stop|Fatal error", log, re.I), "no fatal log error")
        checks.require(not re.search(r"undefined (?:citations?|references?)|Citation .+ undefined|Reference .+ undefined", log, re.I), "no unresolved citation")
        checks.require(not re.search(r"^Overfull \\[hv]box", log, re.M), "no overfull box")
        visible = run([executable("pdftotext"), "manuscript.pdf", "-"], tmp, env)
        checks.require("??" not in visible and "[?]" not in visible, "no visible unresolved marker")
        pdfinfo = run([executable("pdfinfo"), "manuscript.pdf"], tmp, env)
        pages = int(next(line for line in pdfinfo.splitlines() if line.startswith("Pages:")).split(":", 1)[1])
        checks.require(pages == 12, "twelve compiled pages")
        font_rows = [row for row in run([executable("pdffonts"), "manuscript.pdf"], tmp, env).splitlines()[2:] if row.strip()]
        nonembedded = [row for row in font_rows if len(row.split()) >= 5 and row.split()[-5] == "no"]
        type3 = [row for row in font_rows if row.split()[1:3] == ["Type", "3"]]
        checks.require(not nonembedded, "all fonts embedded")
        checks.require(not type3, "no Type 3 fonts")
        pdf_sha256 = digest(tmp / "manuscript.pdf")

    result = {
        "schema_version": 1,
        "decision": "PASS_PRIVATE_COMPLETE_SOURCE_TRANSPORT_CLEAN_COMPILE_SUBMISSION_UNAUTHORIZED",
        "cas_q3_status": "NOT_READY",
        "checks": checks.count,
        "archive_sha256": expected_sha256,
        "archive_members": len(EXPECTED),
        "official_template_zip_sha256": OFFICIAL_TEMPLATE_SHA256,
        "clean_compile_pages": pages,
        "clean_compile_pdf_sha256": pdf_sha256,
        "nonembedded_fonts": len(nonembedded),
        "type3_fonts": len(type3),
        "smallcondensed_equivalence_proved": False,
        "submission_authorized": False,
        "distribution_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
    }
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    args = parser.parse_args()
    validate(args.archive, args.archive_sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
