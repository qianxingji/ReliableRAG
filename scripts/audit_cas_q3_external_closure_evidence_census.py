#!/usr/bin/env python3
"""Bounded read-only census for pre-existing external-closure evidence.

This scans ordinary text files and small text members inside ZIP archives. It
does not extract archives, execute files, interpret evidence authority, or
modify any scanned root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable
import zipfile


TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".tsv", ".yaml", ".yml", ".tex", ".html", ".htm", ".eml"}
EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
MAX_TEXT_BYTES = 5_000_000
MARKER = re.compile(
    rb"Applied Intelligence|2025 CAS Journal Partition|institutional manuscript approval|"
    rb"institutional release review|\xe4\xb8\xad\xe7\xa7\x91\xe9\x99\xa2|\xe5\x88\x86\xe5\x8c\xba|"
    rb"\xe6\x8a\x95\xe7\xa8\xbf\xe5\x89\x8d\xe5\xae\xa1\xe6\x89\xb9|\xe4\xbb\xa3\xe7\xa0\x81\xe5\x8f\x91\xe5\xb8\x83\xe5\xae\xa1\xe6\x9f\xa5",
    re.IGNORECASE,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def audit(roots: Iterable[Path], *, max_text_bytes: int = MAX_TEXT_BYTES) -> dict[str, Any]:
    roots = tuple(roots)
    ordinary_files_seen = 0
    ordinary_text_files_scanned = 0
    ordinary_large_text_files_skipped = 0
    zip_archives_scanned = 0
    zip_text_members_scanned = 0
    zip_large_text_members_skipped = 0
    matches: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in _files(roots):
        ordinary_files_seen += 1
        if path.suffix.lower() == ".zip":
            zip_archives_scanned += 1
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir() or Path(member.filename).suffix.lower() not in TEXT_SUFFIXES:
                            continue
                        if member.file_size > max_text_bytes:
                            zip_large_text_members_skipped += 1
                            continue
                        try:
                            content = archive.read(member)
                        except Exception as exc:  # pragma: no cover - archive implementation dependent
                            errors.append({"scope": "zip_member", "error": type(exc).__name__})
                            continue
                        zip_text_members_scanned += 1
                        if MARKER.search(content):
                            matches.append(
                                {
                                    "scope": "zip_member",
                                    "archive_sha256": _sha256_bytes(path.read_bytes()),
                                    "member": member.filename,
                                    "member_size": member.file_size,
                                    "member_sha256": _sha256_bytes(content),
                                }
                            )
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append({"scope": "zip_archive", "error": type(exc).__name__})
            continue

        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
            if size > max_text_bytes:
                ordinary_large_text_files_skipped += 1
                continue
            content = path.read_bytes()
        except OSError as exc:
            errors.append({"scope": "ordinary_text", "error": type(exc).__name__})
            continue
        ordinary_text_files_scanned += 1
        if MARKER.search(content):
            matches.append(
                {
                    "scope": "ordinary_text",
                    "file_sha256": _sha256_bytes(content),
                    "size": size,
                }
            )

    decision = (
        "PASS_BOUNDED_ACCESSIBLE_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_RECOVERY"
        if not matches and not errors
        else "REVIEW_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_CANDIDATES_OR_ERRORS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "ordinary_files_seen": ordinary_files_seen,
        "ordinary_text_files_scanned": ordinary_text_files_scanned,
        "ordinary_large_text_files_skipped": ordinary_large_text_files_skipped,
        "zip_archives_scanned": zip_archives_scanned,
        "zip_text_members_scanned": zip_text_members_scanned,
        "zip_large_text_members_skipped": zip_large_text_members_skipped,
        "candidate_match_count": len(matches),
        "candidate_matches": matches,
        "scan_error_count": len(errors),
        "scan_errors": errors,
        "max_text_bytes": max_text_bytes,
        "excluded_path_parts": sorted(EXCLUDED_PARTS),
        "bounded_interpretation": {
            "absence_outside_scanned_roots_proved": False,
            "large_skipped_files_proved_irrelevant": False,
            "candidate_match_would_prove_authority": False,
            "institutional_record_recovered": False,
            "p0_g_closed": False,
            "p0_h_closed": False,
            "p0_i_closed": False,
        },
        "read_only": True,
        "archives_extracted": False,
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
    parser.add_argument("--max-text-bytes", type=int, default=MAX_TEXT_BYTES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    roots = tuple(args.roots)
    result = audit(roots, max_text_bytes=args.max_text_bytes)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
