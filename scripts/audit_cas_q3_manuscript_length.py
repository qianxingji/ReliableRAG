#!/usr/bin/env python3
"""Record a reproducible PDF-text length proxy without calling it a publisher count."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "output" / "pdf" / "manuscript.pdf"
STATIC_RECEIPT = ROOT / "paper" / "MANUSCRIPT_VERIFICATION.json"
OUTPUT = ROOT / "docs" / "cas_q3" / "P0_I_MANUSCRIPT_LENGTH_VERIFICATION.json"
TOKEN = re.compile(r"[A-Za-z0-9]+(?:[.'’-][A-Za-z0-9]+)*")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def token_count(text: str) -> int:
    return len(TOKEN.findall(text))


def text_before_references(text: str) -> str:
    marker = re.search(r"(?m)^\s*References\s*$", text)
    if marker is None:
        raise AssertionError("standalone References heading not found in PDF text")
    return text[: marker.start()]


def audit() -> dict[str, object]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError("pdftotext is required")
    text = subprocess.run(
        [pdftotext, "-layout", str(PDF), "-"],
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    ).stdout
    static = json.loads(STATIC_RECEIPT.read_text(encoding="utf-8"))
    pre_reference = token_count(text_before_references(text))
    full = token_count(text)
    if static["abstract_word_count"] > 150:
        raise AssertionError("abstract exceeds the inspected 150-word ceiling")
    if pre_reference >= full:
        raise AssertionError("reference split did not reduce the full PDF count")
    return {
        "schema_version": 1,
        "decision": "PASS_REPRODUCIBLE_LENGTH_PROXY_WITH_JIS_BELOW_AVERAGE_DISCLOSURE",
        "manuscript_pdf_sha256": sha256(PDF),
        "count_method": "Poppler pdftotext -layout plus documented regex tokenization",
        "pdf_tokens_before_references": pre_reference,
        "pdf_tokens_full_document": full,
        "static_abstract_word_count": static["abstract_word_count"],
        "journal_of_information_science_official_average_words": [5000, 7500],
        "journal_of_information_science_official_average_printed_pages": [8, 12],
        "journal_of_information_science_current_risk": "CURRENT_PROXY_BELOW_PUBLISHED_AVERAGE_NOT_A_FORMAL_MINIMUM_FAILURE",
        "publisher_word_count_claimed": False,
        "texcount_used": False,
        "limitations": [
            "This is a reproducible PDF-text token proxy, not the journal submission system's official word count.",
            "The PDF proxy includes visible titles, captions, tables and page text before References.",
            "The full-document proxy includes the reference list.",
            "The official 5,000-7,500 wording describes average paper length, not a stated hard minimum.",
        ],
        "official_requirement_url": "https://journals.sagepub.com/author-instructions/jis",
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    result = audit()
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
