#!/usr/bin/env python3
"""Audit document and text evidence inside first-level nested ZIP archives.

The earlier external-evidence censuses inspect ordinary files and direct members
of ZIP archives.  This bounded follow-up materializes ZIP-valued members into a
temporary directory, scans their direct members, and rejects deeper nesting.
It never extracts an archive tree or executes a scanned file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Iterable
import zipfile

try:
    from scripts import audit_cas_q3_document_container_inventory as document_audit
    from scripts import audit_cas_q3_pdf_external_closure_evidence as pdf_audit
except ModuleNotFoundError:  # Direct ``python scripts/<name>.py`` execution.
    import audit_cas_q3_document_container_inventory as document_audit
    import audit_cas_q3_pdf_external_closure_evidence as pdf_audit


EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
MAX_NESTED_ARCHIVE_BYTES = 1_000_000_000
MAX_TEXT_BYTES = 1_000_000_000
TEXT_SUFFIXES = {
    ".bib",
    ".cfg",
    ".csv",
    ".eml",
    ".htm",
    ".html",
    ".ini",
    ".json",
    ".log",
    ".md",
    ".rst",
    ".tex",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
DOCUMENT_SUFFIXES = set(document_audit.DOCUMENT_SUFFIXES)
MARKER = re.compile(
    rb"Applied Intelligence|2025 CAS Journal Partition|institutional manuscript approval|"
    rb"institutional release review|\xe4\xb8\xad\xe7\xa7\x91\xe9\x99\xa2|\xe5\x88\x86\xe5\x8c\xba|"
    rb"\xe6\x8a\x95\xe7\xa8\xbf\xe5\x89\x8d\xe5\xae\xa1\xe6\x89\xb9|"
    rb"\xe4\xbb\xa3\xe7\xa0\x81\xe5\x8f\x91\xe5\xb8\x83\xe5\xae\xa1\xe6\x9f\xa5",
    re.IGNORECASE,
)


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


def _stream_member(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
) -> tuple[str, bool, int]:
    digest = hashlib.sha256()
    matched = False
    read_bytes = 0
    carry = b""
    with archive.open(member) as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            read_bytes += len(chunk)
            searchable = carry + chunk
            if MARKER.search(searchable):
                matched = True
            carry = searchable[-256:]
    return digest.hexdigest(), matched, read_bytes


def audit(
    roots: Iterable[Path],
    *,
    max_nested_archive_bytes: int = MAX_NESTED_ARCHIVE_BYTES,
    max_text_bytes: int = MAX_TEXT_BYTES,
) -> dict[str, Any]:
    roots = tuple(roots)
    top_level_zip_archives_scanned = 0
    nested_archives_seen = 0
    nested_archives_materialized = 0
    nested_archive_bytes_materialized = 0
    nested_archive_descriptors: list[dict[str, Any]] = []
    skipped_nested_archives: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    parent_hash_cache: dict[Path, str] = {}

    with tempfile.TemporaryDirectory(prefix="reliablerag-nested-archive-audit-") as directory:
        temporary_paths: list[Path] = []
        for path in _files(roots):
            if path.suffix.lower() != ".zip":
                continue
            top_level_zip_archives_scanned += 1
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        try:
                            with archive.open(member) as handle:
                                header = handle.read(8)
                        except Exception as exc:  # pragma: no cover - implementation dependent
                            errors.append({"scope": "top_level_zip_member", "error": type(exc).__name__})
                            continue
                        if not header.startswith(ZIP_MAGIC):
                            continue
                        nested_archives_seen += 1
                        if path not in parent_hash_cache:
                            parent_hash_cache[path] = _sha256_path(path)
                        descriptor = {
                            "parent_archive_sha256": parent_hash_cache[path],
                            "member_size": member.file_size,
                            "member_crc32": f"{member.CRC:08x}",
                            "member_suffix": Path(member.filename).suffix.lower(),
                        }
                        if member.file_size > max_nested_archive_bytes:
                            skipped_nested_archives.append(descriptor)
                            continue
                        target = Path(directory) / f"nested-{nested_archives_materialized + 1}.zip"
                        digest = hashlib.sha256()
                        try:
                            with archive.open(member) as source, target.open("wb") as destination:
                                while True:
                                    chunk = source.read(1024 * 1024)
                                    if not chunk:
                                        break
                                    destination.write(chunk)
                                    digest.update(chunk)
                        except Exception as exc:  # pragma: no cover - implementation dependent
                            errors.append({"scope": "nested_archive_materialization", "error": type(exc).__name__})
                            target.unlink(missing_ok=True)
                            continue
                        descriptor["member_sha256"] = digest.hexdigest()
                        nested_archive_descriptors.append(descriptor)
                        temporary_paths.append(target)
                        nested_archives_materialized += 1
                        nested_archive_bytes_materialized += member.file_size
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append({"scope": "top_level_zip_archive", "error": type(exc).__name__})

        text_members_seen = 0
        text_members_scanned = 0
        text_bytes_scanned = 0
        text_members_skipped = 0
        text_candidates: list[dict[str, Any]] = []
        deeper_archives_seen = 0
        strict_magic_counts: dict[str, int] = {}
        strict_magic_suffix_mismatches: list[dict[str, Any]] = []
        nested_member_count = 0

        for archive_path in temporary_paths:
            archive_sha256 = _sha256_path(archive_path)
            try:
                with zipfile.ZipFile(archive_path) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        nested_member_count += 1
                        suffix = Path(member.filename).suffix.lower()
                        try:
                            with archive.open(member) as handle:
                                header = handle.read(4096)
                        except Exception as exc:  # pragma: no cover - implementation dependent
                            errors.append({"scope": "nested_archive_member", "error": type(exc).__name__})
                            continue
                        magic = _strict_magic(header)
                        if magic is not None:
                            strict_magic_counts[magic] = strict_magic_counts.get(magic, 0) + 1
                        if magic == "zip":
                            deeper_archives_seen += 1
                        elif magic == "pdf" and suffix != ".pdf":
                            strict_magic_suffix_mismatches.append(
                                {"archive_sha256": archive_sha256, "member_size": member.file_size,
                                 "member_crc32": f"{member.CRC:08x}", "suffix": suffix, "magic": magic}
                            )
                        elif magic == "rtf" and suffix != ".rtf":
                            strict_magic_suffix_mismatches.append(
                                {"archive_sha256": archive_sha256, "member_size": member.file_size,
                                 "member_crc32": f"{member.CRC:08x}", "suffix": suffix, "magic": magic}
                            )
                        elif magic == "ole_compound" and suffix not in {".doc", ".xls", ".ppt", ".msg"}:
                            strict_magic_suffix_mismatches.append(
                                {"archive_sha256": archive_sha256, "member_size": member.file_size,
                                 "member_crc32": f"{member.CRC:08x}", "suffix": suffix, "magic": magic}
                            )

                        if suffix not in TEXT_SUFFIXES:
                            continue
                        text_members_seen += 1
                        if member.file_size > max_text_bytes:
                            text_members_skipped += 1
                            continue
                        try:
                            member_sha256, matched, actual_bytes = _stream_member(archive, member)
                        except Exception as exc:  # pragma: no cover - implementation dependent
                            errors.append({"scope": "nested_text_member", "error": type(exc).__name__})
                            continue
                        text_members_scanned += 1
                        text_bytes_scanned += actual_bytes
                        if matched:
                            text_candidates.append(
                                {
                                    "archive_sha256": archive_sha256,
                                    "member_sha256": member_sha256,
                                    "member_size": member.file_size,
                                    "member_suffix": suffix,
                                }
                            )
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append({"scope": "nested_archive", "error": type(exc).__name__})

        pdf_result = pdf_audit.audit(temporary_paths)
        document_result = document_audit.audit(temporary_paths)

    candidate_count = len(text_candidates) + pdf_result["candidate_match_count"]
    decision = (
        "PASS_BOUNDED_FIRST_LEVEL_NESTED_ARCHIVE_CENSUS_NO_RECOVERY"
        if nested_archives_seen == nested_archives_materialized
        and not skipped_nested_archives
        and not errors
        and deeper_archives_seen == 0
        and not strict_magic_suffix_mismatches
        and candidate_count == 0
        and pdf_result["decision"].startswith("PASS_")
        else "REVIEW_FIRST_LEVEL_NESTED_ARCHIVE_CENSUS_CANDIDATES_SKIPS_OR_ERRORS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "top_level_zip_archives_scanned": top_level_zip_archives_scanned,
        "nested_archives_seen": nested_archives_seen,
        "nested_archives_materialized": nested_archives_materialized,
        "nested_archive_bytes_materialized": nested_archive_bytes_materialized,
        "nested_archive_descriptors": nested_archive_descriptors,
        "nested_archives_skipped": len(skipped_nested_archives),
        "skipped_nested_archive_descriptors": skipped_nested_archives,
        "nested_member_count": nested_member_count,
        "deeper_archives_seen": deeper_archives_seen,
        "expanded_text_suffixes": sorted(TEXT_SUFFIXES),
        "text_members_seen": text_members_seen,
        "text_members_scanned": text_members_scanned,
        "text_bytes_scanned": text_bytes_scanned,
        "text_members_skipped": text_members_skipped,
        "text_candidate_match_count": len(text_candidates),
        "text_candidate_matches": text_candidates,
        "strict_magic_counts": strict_magic_counts,
        "strict_magic_suffix_mismatch_count": len(strict_magic_suffix_mismatches),
        "strict_magic_suffix_mismatches": strict_magic_suffix_mismatches,
        "pdf_audit": pdf_result,
        "document_extension_inventory": document_result,
        "candidate_match_count": candidate_count,
        "scan_error_count": len(errors),
        "scan_errors": errors,
        "max_nested_archive_bytes": max_nested_archive_bytes,
        "max_text_bytes": max_text_bytes,
        "bounded_interpretation": {
            "first_level_nested_zip_members_covered": not skipped_nested_archives and not errors,
            "deeper_archive_members_present": deeper_archives_seen > 0,
            "incorrect_or_missing_extensions_outside_nested_archives_covered": False,
            "pdf_image_ocr_performed": False,
            "absence_outside_scanned_roots_proved": False,
            "institutional_record_recovered": False,
            "p0_g_closed": False,
            "p0_h_closed": False,
            "p0_i_closed": False,
        },
        "read_only_external_roots": True,
        "nested_archive_members_temporarily_materialized": True,
        "temporary_files_removed": True,
        "archive_trees_extracted": False,
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
    parser.add_argument("--max-nested-archive-bytes", type=int, default=MAX_NESTED_ARCHIVE_BYTES)
    parser.add_argument("--max-text-bytes", type=int, default=MAX_TEXT_BYTES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(
        tuple(args.roots),
        max_nested_archive_bytes=args.max_nested_archive_bytes,
        max_text_bytes=args.max_text_bytes,
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
