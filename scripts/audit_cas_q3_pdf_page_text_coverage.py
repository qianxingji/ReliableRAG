#!/usr/bin/env python3
"""Audit per-page text coverage across direct and first-level nested PDFs."""

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
from typing import Any, Callable, Iterable
import zipfile


EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
MAX_PDF_BYTES = 20_000_000
MAX_NESTED_ARCHIVE_BYTES = 1_000_000_000
Inspector = Callable[[Path], dict[str, Any]]


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


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inspect_pdf(path: Path) -> dict[str, Any]:
    pdfinfo = subprocess.run(
        ["pdfinfo", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    match = re.search(rb"^Pages:\s+(\d+)", pdfinfo.stdout, re.MULTILINE)
    if pdfinfo.returncode != 0 or match is None:
        return {"error": "PdfInfoFailure", "returncode": pdfinfo.returncode}
    pages = int(match.group(1))

    pdfimages = subprocess.run(
        ["pdfimages", "-list", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if pdfimages.returncode != 0:
        return {"error": "PdfImagesFailure", "returncode": pdfimages.returncode}
    image_pages: set[int] = set()
    for line in pdfimages.stdout.splitlines():
        image_match = re.match(rb"^\s*(\d+)\s+\d+\s+", line)
        if image_match is not None:
            image_pages.add(int(image_match.group(1)))

    nonwhitespace_by_page: list[int] = []
    for page in range(1, pages + 1):
        extracted = subprocess.run(
            ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(path), "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if extracted.returncode != 0:
            return {"error": "PdfTextPageFailure", "returncode": extracted.returncode, "page": page}
        nonwhitespace_by_page.append(len(re.sub(rb"\s+", b"", extracted.stdout)))
    return {
        "pages": pages,
        "nonwhitespace_text_bytes_by_page": nonwhitespace_by_page,
        "raster_image_pages": sorted(image_pages),
    }


def audit(
    roots: Iterable[Path],
    *,
    max_pdf_bytes: int = MAX_PDF_BYTES,
    max_nested_archive_bytes: int = MAX_NESTED_ARCHIVE_BYTES,
    inspector: Inspector = _inspect_pdf,
) -> dict[str, Any]:
    roots = tuple(roots)
    ordinary_pdf_occurrences = 0
    direct_zip_pdf_occurrences = 0
    nested_zip_pdf_occurrences = 0
    nested_archives_seen = 0
    nested_archives_materialized = 0
    skipped_pdf_occurrences = 0
    skipped_nested_archives = 0
    errors: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="reliablerag-pdf-page-audit-") as directory:
        temporary_root = Path(directory)
        unique_pdfs: dict[str, Path] = {}
        top_level_zips: list[Path] = []

        def retain_bytes(content: bytes) -> None:
            digest = hashlib.sha256(content).hexdigest()
            if digest in unique_pdfs:
                return
            target = temporary_root / f"{digest}.pdf"
            target.write_bytes(content)
            unique_pdfs[digest] = target

        def retain_path(path: Path) -> None:
            digest = _sha256_path(path)
            if digest in unique_pdfs:
                return
            target = temporary_root / f"{digest}.pdf"
            shutil.copyfile(path, target)
            unique_pdfs[digest] = target

        for path in _files(roots):
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                ordinary_pdf_occurrences += 1
                try:
                    if path.stat().st_size > max_pdf_bytes:
                        skipped_pdf_occurrences += 1
                    else:
                        retain_path(path)
                except OSError as exc:
                    errors.append({"scope": "ordinary_pdf", "error": type(exc).__name__})
            elif suffix == ".zip":
                top_level_zips.append(path)

        for archive_path in top_level_zips:
            try:
                with zipfile.ZipFile(archive_path) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        suffix = Path(member.filename).suffix.lower()
                        if suffix == ".pdf":
                            direct_zip_pdf_occurrences += 1
                            if member.file_size > max_pdf_bytes:
                                skipped_pdf_occurrences += 1
                                continue
                            try:
                                retain_bytes(archive.read(member))
                            except Exception as exc:  # pragma: no cover - implementation dependent
                                errors.append({"scope": "direct_zip_pdf", "error": type(exc).__name__})
                            continue
                        if suffix != ".zip":
                            continue
                        try:
                            with archive.open(member) as handle:
                                header = handle.read(8)
                        except Exception as exc:  # pragma: no cover - implementation dependent
                            errors.append({"scope": "nested_zip_header", "error": type(exc).__name__})
                            continue
                        if not header.startswith(ZIP_MAGIC):
                            continue
                        nested_archives_seen += 1
                        if member.file_size > max_nested_archive_bytes:
                            skipped_nested_archives += 1
                            continue
                        nested_path = temporary_root / f"nested-{nested_archives_materialized + 1}.zip"
                        try:
                            with archive.open(member) as source, nested_path.open("wb") as destination:
                                shutil.copyfileobj(source, destination, 1024 * 1024)
                            nested_archives_materialized += 1
                            with zipfile.ZipFile(nested_path) as nested:
                                for nested_member in nested.infolist():
                                    if nested_member.is_dir() or Path(nested_member.filename).suffix.lower() != ".pdf":
                                        continue
                                    nested_zip_pdf_occurrences += 1
                                    if nested_member.file_size > max_pdf_bytes:
                                        skipped_pdf_occurrences += 1
                                        continue
                                    retain_bytes(nested.read(nested_member))
                        except Exception as exc:  # pragma: no cover - implementation dependent
                            errors.append({"scope": "nested_zip_pdf", "error": type(exc).__name__})
                        finally:
                            nested_path.unlink(missing_ok=True)
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append({"scope": "top_level_zip", "error": type(exc).__name__})

        total_pages = 0
        pages_with_raster_images = 0
        zero_text_pages: list[dict[str, Any]] = []
        low_text_pages: list[dict[str, Any]] = []
        for digest, path in unique_pdfs.items():
            inspected = inspector(path)
            if "error" in inspected:
                errors.append({"scope": "unique_pdf_page_inspection", "pdf_sha256": digest, **inspected})
                continue
            pages = inspected["pages"]
            counts = inspected["nonwhitespace_text_bytes_by_page"]
            image_pages = set(inspected["raster_image_pages"])
            if pages != len(counts):
                errors.append({"scope": "unique_pdf_page_inspection", "error": "PageCountMismatch"})
                continue
            total_pages += pages
            pages_with_raster_images += len(image_pages)
            for page, count in enumerate(counts, start=1):
                record = {
                    "pdf_sha256": digest,
                    "page": page,
                    "nonwhitespace_text_bytes": count,
                    "has_raster_image": page in image_pages,
                }
                if count == 0:
                    zero_text_pages.append(record)
                if count < 20:
                    low_text_pages.append(record)

    total_occurrences = ordinary_pdf_occurrences + direct_zip_pdf_occurrences + nested_zip_pdf_occurrences
    decision = (
        "PASS_BOUNDED_UNIQUE_PDF_PAGE_TEXT_COVERAGE_NO_LOW_TEXT_PAGES"
        if not errors
        and skipped_pdf_occurrences == 0
        and skipped_nested_archives == 0
        and nested_archives_seen == nested_archives_materialized
        and not low_text_pages
        else "REVIEW_UNIQUE_PDF_PAGE_TEXT_COVERAGE_LOW_TEXT_SKIPS_OR_ERRORS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "ordinary_pdf_occurrences": ordinary_pdf_occurrences,
        "direct_zip_pdf_occurrences": direct_zip_pdf_occurrences,
        "nested_zip_pdf_occurrences": nested_zip_pdf_occurrences,
        "total_pdf_occurrences": total_occurrences,
        "unique_pdf_hashes": len(unique_pdfs),
        "nested_archives_seen": nested_archives_seen,
        "nested_archives_materialized": nested_archives_materialized,
        "total_unique_pdf_pages": total_pages,
        "pages_with_raster_images": pages_with_raster_images,
        "zero_text_page_count": len(zero_text_pages),
        "zero_text_pages": zero_text_pages,
        "fewer_than_20_nonwhitespace_text_page_count": len(low_text_pages),
        "fewer_than_20_nonwhitespace_text_pages": low_text_pages,
        "skipped_pdf_occurrences": skipped_pdf_occurrences,
        "skipped_nested_archives": skipped_nested_archives,
        "scan_error_count": len(errors),
        "scan_errors": errors,
        "max_pdf_bytes": max_pdf_bytes,
        "max_nested_archive_bytes": max_nested_archive_bytes,
        "bounded_interpretation": {
            "all_unique_pdf_pages_have_at_least_20_nonwhitespace_extracted_text_bytes": not low_text_pages,
            "wholly_textless_raster_pages_detected": any(row["has_raster_image"] for row in zero_text_pages),
            "text_inside_raster_images_ocr_performed": False,
            "text_inside_images_on_text_bearing_pages_excluded": True,
            "absence_outside_scanned_roots_proved": False,
            "institutional_record_recovered": False,
            "p0_g_closed": False,
            "p0_h_closed": False,
            "p0_i_closed": False,
        },
        "read_only_external_roots": True,
        "temporary_files_removed": True,
        "files_executed": False,
        "document_parsers_executed": ["pdfinfo", "pdftotext -layout", "pdfimages -list"],
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
    parser.add_argument("--max-nested-archive-bytes", type=int, default=MAX_NESTED_ARCHIVE_BYTES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(
        tuple(args.roots),
        max_pdf_bytes=args.max_pdf_bytes,
        max_nested_archive_bytes=args.max_nested_archive_bytes,
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
