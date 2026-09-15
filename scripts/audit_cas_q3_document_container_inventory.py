#!/usr/bin/env python3
"""Inventory common document containers in the bounded closure-evidence roots."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable
import zipfile


EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
DOCUMENT_SUFFIXES = (
    ".doc",
    ".docx",
    ".msg",
    ".odp",
    ".ods",
    ".odt",
    ".pdf",
    ".ppt",
    ".pptx",
    ".rtf",
    ".xls",
    ".xlsx",
)


def _files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for raw in roots:
        root = raw.resolve()
        if root.is_file():
            candidates = (root,)
        elif root.is_dir():
            def walk() -> Iterable[Path]:
                for directory, subdirectories, names in os.walk(root):
                    subdirectories[:] = [
                        name
                        for name in subdirectories
                        if name not in EXCLUDED_PARTS and not name.startswith("chrome-render-profile")
                    ]
                    yield from (Path(directory) / name for name in names)

            candidates = walk()
        else:
            candidates = ()
        for path in candidates:
            if path.is_file():
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield resolved


def audit(roots: Iterable[Path]) -> dict[str, Any]:
    roots = tuple(roots)
    ordinary_counts = {suffix: 0 for suffix in DOCUMENT_SUFFIXES}
    zip_member_counts = {suffix: 0 for suffix in DOCUMENT_SUFFIXES}
    zip_archives_scanned = 0
    errors: list[dict[str, str]] = []

    for path in _files(roots):
        suffix = path.suffix.lower()
        if suffix in ordinary_counts:
            ordinary_counts[suffix] += 1
        if suffix != ".zip":
            continue
        zip_archives_scanned += 1
        try:
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    member_suffix = Path(member.filename).suffix.lower()
                    if member_suffix in zip_member_counts:
                        zip_member_counts[member_suffix] += 1
        except (OSError, zipfile.BadZipFile) as exc:
            errors.append({"scope": "zip_archive", "error": type(exc).__name__})

    non_pdf_count = sum(
        ordinary_counts[suffix] + zip_member_counts[suffix]
        for suffix in DOCUMENT_SUFFIXES
        if suffix != ".pdf"
    )
    decision = (
        "PASS_BOUNDED_COMMON_DOCUMENT_CONTAINER_INVENTORY_PDF_ONLY"
        if not errors and non_pdf_count == 0
        else "REVIEW_COMMON_DOCUMENT_CONTAINER_INVENTORY_NON_PDF_OR_ERRORS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "zip_archives_scanned": zip_archives_scanned,
        "document_suffixes_in_scope": list(DOCUMENT_SUFFIXES),
        "ordinary_file_counts": ordinary_counts,
        "zip_member_counts": zip_member_counts,
        "ordinary_document_count": sum(ordinary_counts.values()),
        "zip_document_member_count": sum(zip_member_counts.values()),
        "non_pdf_document_count": non_pdf_count,
        "scan_error_count": len(errors),
        "scan_errors": errors,
        "bounded_interpretation": {
            "files_with_incorrect_or_missing_extensions_covered": False,
            "unknown_binary_formats_covered": False,
            "absence_outside_scanned_roots_proved": False,
            "institutional_record_recovered": False,
            "p0_g_closed": False,
            "p0_h_closed": False,
            "p0_i_closed": False,
        },
        "read_only": True,
        "archives_extracted": False,
        "files_executed": False,
        "file_contents_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(tuple(args.roots))
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
