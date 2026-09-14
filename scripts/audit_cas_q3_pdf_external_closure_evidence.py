#!/usr/bin/env python3
"""Extract searchable PDF text for a bounded external-closure census."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Callable, Iterable
import zipfile


EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
MAX_PDF_BYTES = 20_000_000
MARKER = re.compile(
    rb"Applied Intelligence|2025 CAS Journal Partition|institutional manuscript approval|"
    rb"institutional release review|\xe4\xb8\xad\xe7\xa7\x91\xe9\x99\xa2|\xe5\x88\x86\xe5\x8c\xba|"
    rb"\xe6\x8a\x95\xe7\xa8\xbf\xe5\x89\x8d\xe5\xae\xa1\xe6\x89\xb9|\xe4\xbb\xa3\xe7\xa0\x81\xe5\x8f\x91\xe5\xb8\x83\xe5\xae\xa1\xe6\x9f\xa5",
    re.IGNORECASE,
)
Extractor = Callable[[Path | bytes], tuple[int, bytes, bytes]]
AttachmentInspector = Callable[[Path | bytes], tuple[int, bytes, bytes]]


def _sha256(data: bytes) -> str:
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


def _extract_pdf(source: Path | bytes) -> tuple[int, bytes, bytes]:
    if isinstance(source, Path):
        command = ["pdftotext", "-layout", str(source), "-"]
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    else:
        command = ["pdftotext", "-layout", "-", "-"]
        completed = subprocess.run(
            command,
            input=source,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    return completed.returncode, completed.stdout, completed.stderr


def _list_pdf_attachments(source: Path | bytes) -> tuple[int, bytes, bytes]:
    temporary_path: Path | None = None
    try:
        if isinstance(source, Path):
            input_path = source
        else:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
                handle.write(source)
                temporary_path = Path(handle.name)
            input_path = temporary_path
        completed = subprocess.run(
            ["pdfdetach", "-list", str(input_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def audit(
    roots: Iterable[Path],
    *,
    max_pdf_bytes: int = MAX_PDF_BYTES,
    extractor: Extractor = _extract_pdf,
    attachment_inspector: AttachmentInspector = _list_pdf_attachments,
) -> dict[str, Any]:
    roots = tuple(roots)
    ordinary_pdfs_seen = 0
    ordinary_pdfs_extracted = 0
    ordinary_pdf_bytes = 0
    ordinary_pdfs_skipped = 0
    zip_archives_scanned = 0
    zip_pdf_members_seen = 0
    zip_pdf_members_extracted = 0
    zip_pdf_member_bytes = 0
    zip_pdf_members_skipped = 0
    extracted_text_bytes = 0
    unique_pdf_hashes: set[str] = set()
    unique_pdfs_with_zero_text = 0
    unique_pdfs_with_low_text = 0
    unique_pdfs_attachment_inspected = 0
    embedded_attachment_count = 0
    temporary_zip_pdf_materializations = 0
    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    def inspect_unique(source: Path | bytes, digest: str, text: bytes) -> None:
        nonlocal unique_pdfs_with_zero_text
        nonlocal unique_pdfs_with_low_text
        nonlocal unique_pdfs_attachment_inspected
        nonlocal embedded_attachment_count
        nonlocal temporary_zip_pdf_materializations
        if digest in unique_pdf_hashes:
            return
        unique_pdf_hashes.add(digest)
        nonwhitespace = len(re.sub(rb"\s+", b"", text))
        if nonwhitespace == 0:
            unique_pdfs_with_zero_text += 1
        if nonwhitespace < 20:
            unique_pdfs_with_low_text += 1
        if isinstance(source, bytes):
            temporary_zip_pdf_materializations += 1
        try:
            returncode, stdout, stderr = attachment_inspector(source)
        except Exception as exc:  # pragma: no cover - external implementation dependent
            errors.append({"scope": "pdf_attachment_inventory", "error": type(exc).__name__})
            return
        if returncode != 0:
            errors.append(
                {
                    "scope": "pdf_attachment_inventory",
                    "returncode": returncode,
                    "pdf_sha256": digest,
                    "stderr_sha256": _sha256(stderr),
                }
            )
            return
        match = re.match(rb"\s*(\d+) embedded files?", stdout)
        if match is None:
            errors.append(
                {
                    "scope": "pdf_attachment_inventory",
                    "error": "UnrecognizedPdfdetachOutput",
                    "pdf_sha256": digest,
                    "stdout_sha256": _sha256(stdout),
                }
            )
            return
        unique_pdfs_attachment_inspected += 1
        embedded_attachment_count += int(match.group(1))

    for path in _files(roots):
        if path.suffix.lower() == ".zip":
            zip_archives_scanned += 1
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir() or Path(member.filename).suffix.lower() != ".pdf":
                            continue
                        zip_pdf_members_seen += 1
                        if member.file_size > max_pdf_bytes:
                            zip_pdf_members_skipped += 1
                            continue
                        try:
                            content = archive.read(member)
                            returncode, text, stderr = extractor(content)
                        except Exception as exc:  # pragma: no cover - external implementation dependent
                            errors.append({"scope": "zip_pdf_member", "error": type(exc).__name__})
                            continue
                        zip_pdf_member_bytes += len(content)
                        pdf_digest = _sha256(content)
                        if returncode != 0:
                            errors.append(
                                {
                                    "scope": "zip_pdf_member_extract",
                                    "returncode": returncode,
                                    "pdf_sha256": pdf_digest,
                                    "stderr_sha256": _sha256(stderr),
                                }
                            )
                            continue
                        zip_pdf_members_extracted += 1
                        extracted_text_bytes += len(text)
                        inspect_unique(content, pdf_digest, text)
                        if MARKER.search(text):
                            candidates.append(
                                {
                                    "scope": "zip_pdf_member",
                                    "pdf_sha256": pdf_digest,
                                    "size": len(content),
                                    "extracted_text_bytes": len(text),
                                }
                            )
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append({"scope": "zip_archive", "error": type(exc).__name__})
            continue

        if path.suffix.lower() != ".pdf":
            continue
        ordinary_pdfs_seen += 1
        try:
            size = path.stat().st_size
        except OSError as exc:
            errors.append({"scope": "ordinary_pdf_stat", "error": type(exc).__name__})
            continue
        if size > max_pdf_bytes:
            ordinary_pdfs_skipped += 1
            continue
        try:
            content = path.read_bytes()
            returncode, text, stderr = extractor(path)
        except Exception as exc:  # pragma: no cover - external implementation dependent
            errors.append({"scope": "ordinary_pdf", "error": type(exc).__name__})
            continue
        ordinary_pdf_bytes += size
        if returncode != 0:
            errors.append(
                {
                    "scope": "ordinary_pdf_extract",
                    "returncode": returncode,
                    "pdf_sha256": _sha256(content),
                    "stderr_sha256": _sha256(stderr),
                }
            )
            continue
        ordinary_pdfs_extracted += 1
        extracted_text_bytes += len(text)
        pdf_digest = _sha256(content)
        inspect_unique(path, pdf_digest, text)
        if MARKER.search(text):
            candidates.append(
                {
                    "scope": "ordinary_pdf",
                    "pdf_sha256": pdf_digest,
                    "size": size,
                    "extracted_text_bytes": len(text),
                }
            )

    decision = (
        "PASS_BOUNDED_PDF_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES"
        if not candidates
        and not errors
        and ordinary_pdfs_skipped == 0
        and zip_pdf_members_skipped == 0
        and unique_pdfs_with_low_text == 0
        and unique_pdfs_attachment_inspected == len(unique_pdf_hashes)
        and embedded_attachment_count == 0
        else "REVIEW_PDF_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_CANDIDATES_ERRORS_OR_SKIPS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "extractor": "Poppler pdftotext -layout",
        "max_pdf_bytes_inclusive": max_pdf_bytes,
        "ordinary_pdfs_seen": ordinary_pdfs_seen,
        "ordinary_pdfs_extracted": ordinary_pdfs_extracted,
        "ordinary_pdf_bytes_processed": ordinary_pdf_bytes,
        "ordinary_pdfs_skipped": ordinary_pdfs_skipped,
        "zip_archives_scanned": zip_archives_scanned,
        "zip_pdf_members_seen": zip_pdf_members_seen,
        "zip_pdf_members_extracted": zip_pdf_members_extracted,
        "zip_pdf_member_bytes_processed": zip_pdf_member_bytes,
        "zip_pdf_members_skipped": zip_pdf_members_skipped,
        "extracted_text_bytes_scanned": extracted_text_bytes,
        "unique_pdf_hashes": len(unique_pdf_hashes),
        "unique_pdfs_with_zero_extracted_text": unique_pdfs_with_zero_text,
        "unique_pdfs_with_fewer_than_20_nonwhitespace_text_bytes": unique_pdfs_with_low_text,
        "unique_pdfs_attachment_inspected": unique_pdfs_attachment_inspected,
        "embedded_attachment_count": embedded_attachment_count,
        "zip_pdf_members_temporarily_materialized_for_attachment_inventory": temporary_zip_pdf_materializations,
        "temporary_attachment_inventory_files_removed": True,
        "candidate_match_count": len(candidates),
        "candidate_matches": candidates,
        "scan_error_count": len(errors),
        "scan_errors": errors,
        "bounded_interpretation": {
            "pdf_image_ocr_performed": False,
            "embedded_attachment_inventory_complete": unique_pdfs_attachment_inspected == len(unique_pdf_hashes),
            "embedded_attachments_present": embedded_attachment_count > 0,
            "absence_outside_scanned_roots_proved": False,
            "other_binary_formats_covered": False,
            "institutional_record_recovered": False if not candidates else None,
            "p0_g_closed": False,
            "p0_h_closed": False,
            "p0_i_closed": False,
        },
        "read_only": True,
        "archives_extracted": False,
        "files_executed": False,
        "document_parser_executed": True,
        "scientific_payloads_interpreted": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--max-pdf-bytes", type=int, default=MAX_PDF_BYTES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(tuple(args.roots), max_pdf_bytes=args.max_pdf_bytes)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
