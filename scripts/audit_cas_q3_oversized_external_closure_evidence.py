#!/usr/bin/env python3
"""Stream-scan oversized text excluded from the primary closure census.

The scan is read-only, does not extract archives, and reports hashes rather
than ordinary-file paths or matched text. It is a bounded evidence-recovery
aid, not an authority or submission decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, BinaryIO, Iterable
import zipfile


TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".tsv", ".yaml", ".yml", ".tex", ".html", ".htm", ".eml"}
EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
MIN_STREAM_BYTES = 5_000_000
MAX_STREAM_BYTES = 1_000_000_000
CHUNK_BYTES = 1_048_576
OVERLAP_BYTES = 256
MARKER = re.compile(
    rb"Applied Intelligence|2025 CAS Journal Partition|institutional manuscript approval|"
    rb"institutional release review|\xe4\xb8\xad\xe7\xa7\x91\xe9\x99\xa2|\xe5\x88\x86\xe5\x8c\xba|"
    rb"\xe6\x8a\x95\xe7\xa8\xbf\xe5\x89\x8d\xe5\xae\xa1\xe6\x89\xb9|\xe4\xbb\xa3\xe7\xa0\x81\xe5\x8f\x91\xe5\xb8\x83\xe5\xae\xa1\xe6\x9f\xa5",
    re.IGNORECASE,
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


def _scan_stream(handle: BinaryIO) -> tuple[str, bool, int]:
    digest = hashlib.sha256()
    matched = False
    total = 0
    tail = b""
    while True:
        chunk = handle.read(CHUNK_BYTES)
        if not chunk:
            break
        digest.update(chunk)
        total += len(chunk)
        window = tail + chunk
        if not matched and MARKER.search(window):
            matched = True
        tail = window[-OVERLAP_BYTES:]
    return digest.hexdigest(), matched, total


def audit(
    roots: Iterable[Path],
    *,
    min_stream_bytes: int = MIN_STREAM_BYTES,
    max_stream_bytes: int = MAX_STREAM_BYTES,
) -> dict[str, Any]:
    roots = tuple(roots)
    ordinary_large_seen = 0
    ordinary_large_stream_scanned = 0
    ordinary_large_bytes_scanned = 0
    ordinary_too_large_skipped = 0
    zip_archives_scanned = 0
    zip_large_members_seen = 0
    zip_large_members_stream_scanned = 0
    zip_large_member_bytes_scanned = 0
    zip_too_large_members_skipped = 0
    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in _files(roots):
        if path.suffix.lower() == ".zip":
            zip_archives_scanned += 1
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir() or Path(member.filename).suffix.lower() not in TEXT_SUFFIXES:
                            continue
                        if member.file_size <= min_stream_bytes:
                            continue
                        zip_large_members_seen += 1
                        if member.file_size > max_stream_bytes:
                            zip_too_large_members_skipped += 1
                            continue
                        try:
                            with archive.open(member) as handle:
                                digest, matched, total = _scan_stream(handle)
                        except Exception as exc:  # pragma: no cover - archive implementation dependent
                            errors.append({"scope": "zip_member", "error": type(exc).__name__})
                            continue
                        zip_large_members_stream_scanned += 1
                        zip_large_member_bytes_scanned += total
                        if total != member.file_size:
                            errors.append({"scope": "zip_member_size", "error": "SizeMismatch"})
                        if matched:
                            candidates.append(
                                {
                                    "scope": "zip_member",
                                    "member_sha256": digest,
                                    "member_size": member.file_size,
                                }
                            )
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append({"scope": "zip_archive", "error": type(exc).__name__})
            continue

        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            errors.append({"scope": "ordinary_text_stat", "error": type(exc).__name__})
            continue
        if size <= min_stream_bytes:
            continue
        ordinary_large_seen += 1
        if size > max_stream_bytes:
            ordinary_too_large_skipped += 1
            continue
        try:
            with path.open("rb") as handle:
                digest, matched, total = _scan_stream(handle)
        except OSError as exc:
            errors.append({"scope": "ordinary_text", "error": type(exc).__name__})
            continue
        ordinary_large_stream_scanned += 1
        ordinary_large_bytes_scanned += total
        if total != size:
            errors.append({"scope": "ordinary_text_size", "error": "SizeMismatch"})
        if matched:
            candidates.append({"scope": "ordinary_text", "file_sha256": digest, "size": size})

    decision = (
        "PASS_BOUNDED_OVERSIZED_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES"
        if not candidates and not errors and ordinary_too_large_skipped == 0 and zip_too_large_members_skipped == 0
        else "REVIEW_OVERSIZED_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_CANDIDATES_ERRORS_OR_SKIPS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "min_stream_bytes_exclusive": min_stream_bytes,
        "max_stream_bytes_inclusive": max_stream_bytes,
        "ordinary_large_text_files_seen": ordinary_large_seen,
        "ordinary_large_text_files_stream_scanned": ordinary_large_stream_scanned,
        "ordinary_large_text_bytes_scanned": ordinary_large_bytes_scanned,
        "ordinary_too_large_text_files_skipped": ordinary_too_large_skipped,
        "zip_archives_scanned": zip_archives_scanned,
        "zip_large_text_members_seen": zip_large_members_seen,
        "zip_large_text_members_stream_scanned": zip_large_members_stream_scanned,
        "zip_large_text_member_bytes_scanned": zip_large_member_bytes_scanned,
        "zip_too_large_text_members_skipped": zip_too_large_members_skipped,
        "candidate_match_count": len(candidates),
        "candidate_matches": candidates,
        "scan_error_count": len(errors),
        "scan_errors": errors,
        "bounded_interpretation": {
            "candidate_match_would_prove_authority": False,
            "absence_outside_scanned_roots_proved": False,
            "unsupported_binary_formats_covered": False,
            "institutional_record_recovered": False if not candidates else None,
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
    parser.add_argument("--min-stream-bytes", type=int, default=MIN_STREAM_BYTES)
    parser.add_argument("--max-stream-bytes", type=int, default=MAX_STREAM_BYTES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(
        tuple(args.roots),
        min_stream_bytes=args.min_stream_bytes,
        max_stream_bytes=args.max_stream_bytes,
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
