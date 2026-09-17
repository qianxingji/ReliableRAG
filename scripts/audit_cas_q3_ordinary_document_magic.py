#!/usr/bin/env python3
"""Detect common document containers by file header, independent of suffix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable
import zipfile


EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
HEADER_BYTES = 4096
LEGACY_OLE_SUFFIXES = {".doc", ".xls", ".ppt", ".msg"}
ZIP_DOCUMENT_SUFFIXES = {
    "ooxml_word": {".docx", ".docm", ".dotx", ".dotm"},
    "ooxml_spreadsheet": {".xlsx", ".xlsm", ".xltx", ".xltm", ".xlsb"},
    "ooxml_presentation": {".pptx", ".pptm", ".potx", ".potm", ".ppsx", ".ppsm"},
    "odf_text": {".odt", ".ott"},
    "odf_spreadsheet": {".ods", ".ots"},
    "odf_presentation": {".odp", ".otp"},
}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _strict_magic(header: bytes) -> str | None:
    if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "ole_compound"
    normalized = header.removeprefix(b"\xef\xbb\xbf").lstrip(b"\x00\x09\x0a\x0d\x20")
    if normalized.startswith(b"%PDF-"):
        return "pdf"
    if normalized.startswith(b"{\\rtf"):
        return "rtf"
    if header.startswith(ZIP_MAGIC):
        return "zip"
    return None


def _classify_zip_document(path: Path) -> str | None:
    with zipfile.ZipFile(path) as archive:
        names = {member.filename.replace("\\", "/").lstrip("/").lower() for member in archive.infolist()}
        if "word/document.xml" in names:
            return "ooxml_word"
        if "xl/workbook.xml" in names:
            return "ooxml_spreadsheet"
        if "ppt/presentation.xml" in names:
            return "ooxml_presentation"
        if "mimetype" not in names:
            return None
        mimetype_member = next(
            member for member in archive.infolist()
            if member.filename.replace("\\", "/").lstrip("/").lower() == "mimetype"
        )
        mimetype = archive.read(mimetype_member).strip().lower()
        return {
            b"application/vnd.oasis.opendocument.text": "odf_text",
            b"application/vnd.oasis.opendocument.spreadsheet": "odf_spreadsheet",
            b"application/vnd.oasis.opendocument.presentation": "odf_presentation",
        }.get(mimetype)


def audit(roots: Iterable[Path]) -> dict[str, Any]:
    roots = tuple(roots)
    ordinary_files_seen = 0
    header_bytes_read = 0
    strict_magic_counts: dict[str, int] = {}
    strict_magic_suffix_counts: dict[str, dict[str, int]] = {}
    zip_document_family_counts = {family: 0 for family in ZIP_DOCUMENT_SUFFIXES}
    loose_pdf_marker_non_header_count = 0
    loose_pdf_marker_non_header_suffix_counts: dict[str, int] = {}
    mismatches: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in _files(roots):
        ordinary_files_seen += 1
        suffix = path.suffix.lower()
        try:
            with path.open("rb") as handle:
                header = handle.read(HEADER_BYTES)
        except OSError as exc:
            errors.append({"scope": "ordinary_file_header", "error": type(exc).__name__})
            continue
        header_bytes_read += len(header)
        magic = _strict_magic(header)
        if magic != "pdf" and b"%PDF-" in header[:1024]:
            loose_pdf_marker_non_header_count += 1
            loose_pdf_marker_non_header_suffix_counts[suffix] = (
                loose_pdf_marker_non_header_suffix_counts.get(suffix, 0) + 1
            )
        if magic is None:
            continue
        strict_magic_counts[magic] = strict_magic_counts.get(magic, 0) + 1
        suffix_counts = strict_magic_suffix_counts.setdefault(magic, {})
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1

        detected = magic
        expected_suffixes: set[str]
        if magic == "pdf":
            expected_suffixes = {".pdf"}
        elif magic == "rtf":
            expected_suffixes = {".rtf"}
        elif magic == "ole_compound":
            expected_suffixes = LEGACY_OLE_SUFFIXES
        else:
            try:
                family = _classify_zip_document(path)
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                errors.append({"scope": "ordinary_zip_classification", "error": type(exc).__name__})
                continue
            if family is None:
                expected_suffixes = {".zip"}
            else:
                detected = family
                zip_document_family_counts[family] += 1
                expected_suffixes = ZIP_DOCUMENT_SUFFIXES[family]
        if suffix not in expected_suffixes:
            mismatches.append(
                {
                    "file_sha256": _sha256_path(path),
                    "file_size": path.stat().st_size,
                    "suffix": suffix,
                    "detected_format": detected,
                    "expected_suffixes": sorted(expected_suffixes),
                }
            )

    decision = (
        "PASS_BOUNDED_ORDINARY_DOCUMENT_MAGIC_MATCHES_EXTENSIONS"
        if not errors and not mismatches
        else "REVIEW_ORDINARY_DOCUMENT_MAGIC_MISMATCHES_OR_ERRORS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "ordinary_files_seen": ordinary_files_seen,
        "header_bytes_per_file": HEADER_BYTES,
        "header_bytes_read": header_bytes_read,
        "strict_magic_counts": strict_magic_counts,
        "strict_magic_suffix_counts": strict_magic_suffix_counts,
        "zip_document_family_counts": zip_document_family_counts,
        "loose_pdf_marker_non_header_count": loose_pdf_marker_non_header_count,
        "loose_pdf_marker_non_header_suffix_counts": loose_pdf_marker_non_header_suffix_counts,
        "document_magic_suffix_mismatch_count": len(mismatches),
        "document_magic_suffix_mismatches": mismatches,
        "scan_error_count": len(errors),
        "scan_errors": errors,
        "excluded_path_parts": sorted(EXCLUDED_PARTS),
        "bounded_interpretation": {
            "common_pdf_rtf_ole_zip_document_magic_covered": True,
            "unknown_binary_formats_covered": False,
            "nested_archive_members_covered_here": False,
            "absence_outside_scanned_roots_proved": False,
            "institutional_record_recovered": False,
            "p0_g_closed": False,
            "p0_h_closed": False,
            "p0_i_closed": False,
        },
        "read_only": True,
        "files_executed": False,
        "scientific_payloads_interpreted": False,
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
