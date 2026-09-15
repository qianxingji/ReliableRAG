#!/usr/bin/env python3
"""Inventory common raster images in bounded external-evidence roots."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, BinaryIO, Iterable
import zipfile


EXCLUDED_PARTS = {".git", ".venv", "tmp", "__pycache__"}
IMAGE_SUFFIXES = {
    "png": {".png"},
    "jpeg": {".jpg", ".jpeg", ".jpe"},
    "gif": {".gif"},
    "bmp": {".bmp"},
    "tiff": {".tif", ".tiff"},
    "webp": {".webp"},
    "heif": {".heic", ".heif", ".avif"},
}
ALL_IMAGE_SUFFIXES = set().union(*IMAGE_SUFFIXES.values())
HEADER_BYTES = 64
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


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
                        if name not in EXCLUDED_PARTS
                        and not name.startswith("chrome-render-profile")
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


def _root_boundaries(roots: Iterable[Path]) -> tuple[tuple[Path, bool], ...]:
    boundaries = []
    for raw in roots:
        resolved = raw.resolve()
        boundaries.append((resolved, resolved.is_dir()))
    return tuple(boundaries)


def _is_within_boundaries(
    path: Path, boundaries: Iterable[tuple[Path, bool]]
) -> bool:
    for root, is_directory in boundaries:
        if not is_directory and path == root:
            return True
        if is_directory and (path == root or path.is_relative_to(root)):
            return True
    return False


def _is_within_declared_roots(path: Path, roots: Iterable[Path]) -> bool:
    return _is_within_boundaries(path, _root_boundaries(roots))


def _image_magic(header: bytes) -> str | None:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if header.startswith(b"BM"):
        return "bmp"
    if header.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        brands = {header[8:12]}
        brands.update(header[offset : offset + 4] for offset in range(16, len(header) - 3, 4))
        if brands & {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1", b"avif", b"avis"}:
            return "heif"
    return None


def _hash_stream(handle: BinaryIO, prefix: bytes = b"") -> str:
    digest = hashlib.sha256(prefix)
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _new_state() -> dict[str, Any]:
    return {
        "ordinary_files_seen": 0,
        "resolved_outside_declared_roots_files": 0,
        "header_bytes_read": 0,
        "extension_labeled_image_files": 0,
        "strict_magic_counts": {},
        "ordinary_image_occurrences": 0,
        "resolved_outside_declared_roots_image_occurrences": 0,
        "zip_archives_scanned": 0,
        "nested_zip_archives_scanned": 0,
        "direct_zip_members_seen": 0,
        "nested_zip_members_seen": 0,
        "direct_zip_image_members": 0,
        "nested_zip_image_members": 0,
        "unique": {},
        "mismatches": [],
        "errors": [],
    }


def _record_image(
    state: dict[str, Any],
    *,
    file_hash: str,
    size: int,
    detected: str,
    suffix: str,
    basename: str,
    scope: str,
) -> None:
    counts = state["strict_magic_counts"]
    counts[detected] = counts.get(detected, 0) + 1
    record = state["unique"].setdefault(
        file_hash,
        {
            "file_sha256": file_hash,
            "file_size": size,
            "detected_format": detected,
            "occurrences": 0,
            "basenames": set(),
            "scopes": set(),
        },
    )
    record["occurrences"] += 1
    record["basenames"].add(basename)
    record["scopes"].add(scope)
    if suffix not in IMAGE_SUFFIXES[detected]:
        state["mismatches"].append(
            {
                "file_sha256": file_hash,
                "file_size": size,
                "suffix": suffix,
                "detected_format": detected,
                "scope": scope,
            }
        )


def _scan_archive(
    archive: zipfile.ZipFile,
    state: dict[str, Any],
    *,
    depth: int,
) -> None:
    for member in archive.infolist():
        if member.is_dir():
            continue
        if depth == 0:
            state["direct_zip_members_seen"] += 1
            scope = "direct_zip_member"
        else:
            state["nested_zip_members_seen"] += 1
            scope = "nested_zip_member"
        suffix = Path(member.filename).suffix.lower()
        try:
            with archive.open(member) as handle:
                header = handle.read(HEADER_BYTES)
                detected = _image_magic(header)
                if detected is not None:
                    file_hash = _hash_stream(handle, header)
                    _record_image(
                        state,
                        file_hash=file_hash,
                        size=member.file_size,
                        detected=detected,
                        suffix=suffix,
                        basename=Path(member.filename).name,
                        scope=scope,
                    )
                    key = "direct_zip_image_members" if depth == 0 else "nested_zip_image_members"
                    state[key] += 1
                elif suffix in ALL_IMAGE_SUFFIXES:
                    file_hash = _hash_stream(handle, header)
                    state["mismatches"].append(
                        {
                            "file_sha256": file_hash,
                            "file_size": member.file_size,
                            "suffix": suffix,
                            "detected_format": None,
                            "scope": scope,
                        }
                    )
                elif header.startswith(ZIP_MAGIC):
                    nested_bytes = header + handle.read()
                    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
                        state["nested_zip_archives_scanned"] += 1
                        _scan_archive(nested, state, depth=depth + 1)
        except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
            state["errors"].append(
                {"scope": scope, "error": type(exc).__name__, "depth": depth}
            )


def audit(roots: Iterable[Path]) -> dict[str, Any]:
    roots = tuple(roots)
    boundaries = _root_boundaries(roots)
    state = _new_state()

    for path in _files(roots):
        state["ordinary_files_seen"] += 1
        outside_declared_roots = not _is_within_boundaries(path, boundaries)
        if outside_declared_roots:
            state["resolved_outside_declared_roots_files"] += 1
        suffix = path.suffix.lower()
        if suffix in ALL_IMAGE_SUFFIXES:
            state["extension_labeled_image_files"] += 1
        try:
            with path.open("rb") as handle:
                header = handle.read(HEADER_BYTES)
        except OSError as exc:
            state["errors"].append(
                {"scope": "ordinary_file_header", "error": type(exc).__name__}
            )
            continue
        state["header_bytes_read"] += len(header)
        detected = _image_magic(header)
        if detected is None:
            if suffix in ALL_IMAGE_SUFFIXES:
                state["mismatches"].append(
                    {
                        "file_sha256": _sha256_path(path),
                        "file_size": path.stat().st_size,
                        "suffix": suffix,
                        "detected_format": None,
                        "scope": "ordinary_file",
                    }
                )
            elif header.startswith(ZIP_MAGIC):
                try:
                    with zipfile.ZipFile(path) as archive:
                        state["zip_archives_scanned"] += 1
                        _scan_archive(archive, state, depth=0)
                except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                    state["errors"].append(
                        {"scope": "ordinary_zip", "error": type(exc).__name__}
                    )
            continue

        file_hash = _sha256_path(path)
        size = path.stat().st_size
        state["ordinary_image_occurrences"] += 1
        if outside_declared_roots:
            state["resolved_outside_declared_roots_image_occurrences"] += 1
        _record_image(
            state,
            file_hash=file_hash,
            size=size,
            detected=detected,
            suffix=suffix,
            basename=path.name,
            scope=(
                "ordinary_file_via_external_reparse_target"
                if outside_declared_roots
                else "ordinary_file"
            ),
        )

    unique_images = []
    for record in state["unique"].values():
        normalized = dict(record)
        normalized["basenames"] = sorted(record["basenames"])
        normalized["scopes"] = sorted(record["scopes"])
        unique_images.append(normalized)
    unique_images.sort(key=lambda item: item["file_sha256"])
    occurrence_sum = sum(item["occurrences"] for item in unique_images)
    outside_unique_images = sum(
        "ordinary_file_via_external_reparse_target" in item["scopes"]
        for item in unique_images
    )
    image_occurrences = (
        state["ordinary_image_occurrences"]
        + state["direct_zip_image_members"]
        + state["nested_zip_image_members"]
    )

    decision = (
        "PASS_BOUNDED_COMMON_RASTER_IMAGE_INVENTORY_NO_EXTENSION_MISMATCH"
        if not state["errors"]
        and not state["mismatches"]
        and occurrence_sum == image_occurrences
        else "REVIEW_COMMON_RASTER_IMAGE_INVENTORY_MISMATCHES_OR_ERRORS"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "roots_scanned": len(roots),
        "ordinary_files_seen": state["ordinary_files_seen"],
        "resolved_outside_declared_roots_files": state[
            "resolved_outside_declared_roots_files"
        ],
        "header_bytes_per_file": HEADER_BYTES,
        "header_bytes_read": state["header_bytes_read"],
        "extension_labeled_image_files": state["extension_labeled_image_files"],
        "strict_image_magic_counts": state["strict_magic_counts"],
        "image_occurrences": image_occurrences,
        "ordinary_image_occurrences": state["ordinary_image_occurrences"],
        "resolved_outside_declared_roots_image_occurrences": state[
            "resolved_outside_declared_roots_image_occurrences"
        ],
        "resolved_outside_declared_roots_unique_image_hashes": outside_unique_images,
        "zip_archives_scanned": state["zip_archives_scanned"],
        "nested_zip_archives_scanned": state["nested_zip_archives_scanned"],
        "direct_zip_members_seen": state["direct_zip_members_seen"],
        "nested_zip_members_seen": state["nested_zip_members_seen"],
        "direct_zip_image_members": state["direct_zip_image_members"],
        "nested_zip_image_members": state["nested_zip_image_members"],
        "unique_image_hashes": len(unique_images),
        "unique_images": unique_images,
        "image_magic_suffix_mismatch_count": len(state["mismatches"]),
        "image_magic_suffix_mismatches": state["mismatches"],
        "scan_error_count": len(state["errors"]),
        "scan_errors": state["errors"],
        "excluded_path_parts": sorted(EXCLUDED_PARTS),
        "bounded_interpretation": {
            "common_png_jpeg_gif_bmp_tiff_webp_heif_magic_covered": True,
            "image_pixel_text_ocr_performed": False,
            "unique_image_content_requires_manual_visual_review": True,
            "unknown_binary_formats_covered": False,
            "direct_and_nested_archive_image_members_covered": True,
            "logical_root_reparse_targets_disclosed": True,
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
