#!/usr/bin/env python3
"""Bounded read-only census for historical seven-estimator fit receipts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/cas_q3/P0_E_ORIGINAL_FIT_RECEIPT_CENSUS.json"
DEFAULT_ROOTS = [
    ("original_workspace", Path("E:/paper/ReliableRAG")),
    ("static_original", Path("E:/paper/ReliableRAG-static-roots-v1/original")),
    ("static_engineering", Path("E:/paper/ReliableRAG-static-roots-v1/engineering")),
    ("static_task", Path("E:/paper/ReliableRAG-static-roots-v1/task")),
]
DEFAULT_TOP_LEVEL_ARCHIVE_ROOT = Path("E:/paper")
SKIP_COMPONENTS = {".git", ".venv", "venv", "site-packages", "node_modules", "data"}
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".log", ".csv", ".yaml", ".yml"}
CANDIDATE_NAME = re.compile(r"(fit|train|receipt|manifest|model)", re.IGNORECASE)
RECEIPT_MARKER = re.compile(
    rb"(fit[_ -]?time|training[_ -]?receipt|matrix_sha256|ids_sha256|keys_sha256)",
    re.IGNORECASE,
)
MAX_CANDIDATE_BYTES = 2_000_000
MODEL_SPECS = {
    "state_symmetric_logistic": (5404, "0adde50ca869a216edb4a2b4a7898e5b60a9f148ec279a0c4b757d1c439fd0bf"),
    "no_cross_state": (4476, "5ca5fc84e5b58e44b9271282e8629af3c3d8a579bc51bf536ce65abd3a78a64b"),
    "no_B": (4940, "8c9dd6cccb5081e12f67ac21efc7d268635cee0a279f3dd48c9e5f7ca4980e11"),
    "no_evidence_change": (1852, "bd225da486eeab63bfa64c2f50a2d85910a1042bfe6c2314066ac7f5d0757336"),
    "no_answer_form": (3644, "cc6cb1ba307ade2440a4423c268641077217eac6b7490c28a0f258ca3cea53dd"),
    "state_symmetric_hgb": (639652, "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e"),
    "ordinary_compact_logistic": (2165, "761dc0238f4da181a5693da881b914134ca7603269f6fee21d66a32539d01242"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iso_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def candidate_payload_matches(payload: bytes, specs: dict[str, tuple[int, str]] = MODEL_SPECS) -> bool:
    if not RECEIPT_MARKER.search(payload):
        return False
    lower = payload.lower()
    identities = [name.lower().encode("utf-8") for name in specs]
    identities.extend(digest.encode("ascii") for _, digest in specs.values())
    identities.append(b"mars_full")
    return any(identity in lower for identity in identities)


def scan(
    roots: list[tuple[str, Path]],
    *,
    top_level_archive_root: Path | None,
    specs: dict[str, tuple[int, str]] = MODEL_SPECS,
) -> dict[str, object]:
    expected_by_size: dict[int, dict[str, str]] = {}
    for model, (size, digest) in specs.items():
        expected_by_size.setdefault(size, {})[digest] = model

    seen_files: set[str] = set()
    archive_paths: list[Path] = []
    exact_copies: list[dict[str, object]] = []
    text_hits: list[dict[str, object]] = []
    archive_hits: list[dict[str, object]] = []
    files_scanned = 0
    candidate_text_files = 0
    errors: list[str] = []

    for label, root in roots:
        if not root.is_dir():
            errors.append(f"missing_root:{label}")
            continue
        for path in root.rglob("*"):
            try:
                if not path.is_file() or any(part.lower() in SKIP_COMPONENTS for part in path.parts):
                    continue
                identity = str(path.resolve()).lower()
                if identity in seen_files:
                    continue
                seen_files.add(identity)
                files_scanned += 1
                stat = path.stat()
                relative = path.relative_to(root).as_posix()
                if path.suffix.lower() == ".zip":
                    archive_paths.append(path)
                if stat.st_size in expected_by_size and path.suffix.lower() in {".joblib", ".pkl", ".pickle", ".bin"}:
                    digest = sha256(path)
                    if digest in expected_by_size[stat.st_size]:
                        exact_copies.append({
                            "root": label,
                            "relative_path": relative,
                            "model": expected_by_size[stat.st_size][digest],
                            "bytes": stat.st_size,
                            "sha256": digest,
                            "filesystem_last_write_utc": iso_utc(stat.st_mtime),
                        })
                if (
                    path.suffix.lower() in TEXT_SUFFIXES
                    and stat.st_size <= MAX_CANDIDATE_BYTES
                    and CANDIDATE_NAME.search(path.name)
                ):
                    candidate_text_files += 1
                    if candidate_payload_matches(path.read_bytes(), specs):
                        text_hits.append({"root": label, "relative_path": relative, "bytes": stat.st_size})
            except Exception as exc:  # pragma: no cover - host-specific failures are retained.
                errors.append(f"filesystem:{label}:{type(exc).__name__}")

    if top_level_archive_root is not None and top_level_archive_root.is_dir():
        archive_paths.extend(top_level_archive_root.glob("*.zip"))
    unique_archives: list[Path] = []
    seen_archives: set[str] = set()
    for path in archive_paths:
        identity = str(path.resolve()).lower()
        if identity not in seen_archives:
            seen_archives.add(identity)
            unique_archives.append(path)

    for archive in unique_archives:
        try:
            with zipfile.ZipFile(archive) as bundle:
                for info in bundle.infolist():
                    member = Path(info.filename)
                    if (
                        info.is_dir()
                        or info.file_size > MAX_CANDIDATE_BYTES
                        or member.suffix.lower() not in TEXT_SUFFIXES
                        or not CANDIDATE_NAME.search(member.name)
                    ):
                        continue
                    if candidate_payload_matches(bundle.read(info), specs):
                        archive_hits.append({
                            "archive_name": archive.name,
                            "member": info.filename,
                            "bytes": info.file_size,
                            "zip_member_timestamp": list(info.date_time),
                        })
        except Exception as exc:  # pragma: no cover - host-specific failures are retained.
            errors.append(f"archive:{archive.name}:{type(exc).__name__}")

    exact_copies.sort(key=lambda item: (str(item["root"]), str(item["model"]), str(item["relative_path"])))
    text_hits.sort(key=lambda item: (str(item["root"]), str(item["relative_path"])))
    archive_hits.sort(key=lambda item: (str(item["archive_name"]), str(item["member"])))
    models_by_root: dict[str, list[str]] = {}
    for copy in exact_copies:
        models_by_root.setdefault(str(copy["root"]), []).append(str(copy["model"]))
    models_by_root = {key: sorted(set(value)) for key, value in sorted(models_by_root.items())}

    recovered = bool(text_hits or archive_hits)
    return {
        "schema_version": 1,
        "decision": (
            "REVIEW_REQUIRED_CANDIDATE_ORIGINAL_FIT_RECEIPT_FOUND"
            if recovered
            else "PASS_BOUNDED_ACCESSIBLE_HISTORICAL_RECEIPT_CENSUS_NO_RECOVERY"
        ),
        "cas_q3_status": "NOT_READY",
        "scope": "read-only filename, bounded metadata-text, ZIP-central-directory and exact-model-hash census",
        "roots": [{"label": label, "path": str(path)} for label, path in roots],
        "top_level_archive_root": str(top_level_archive_root) if top_level_archive_root else None,
        "counts": {
            "filesystem_files_scanned": files_scanned,
            "candidate_text_files_scanned": candidate_text_files,
            "zip_archives_scanned": len(unique_archives),
            "exact_original_model_hash_copies": len(exact_copies),
            "candidate_files_with_receipt_markers_and_model_identity": len(text_hits),
            "candidate_archive_members_with_receipt_markers_and_model_identity": len(archive_hits),
            "scan_errors": len(errors),
        },
        "exact_model_copies": exact_copies,
        "exact_models_by_root": models_by_root,
        "candidate_files": text_hits,
        "candidate_archive_members": archive_hits,
        "errors": errors,
        "interpretation": {
            "third_independent_model_copy_found": len(models_by_root) > 2,
            "original_per_estimator_fit_time_id_receipts_recovered": False,
            "original_per_estimator_fit_time_matrix_receipts_recovered": False,
            "independent_original_fit_witness_recovered": False,
            "absence_outside_scanned_roots_proved": False,
            "filesystem_or_zip_timestamps_are_independent_certification": False,
            "p0_1_authenticity_gap_closed": False,
        },
        "operations": {
            "scientific_payloads_decoded": False,
            "model_deserialization": False,
            "model_forwards": 0,
            "scientific_fits": 0,
            "gold_or_answer_text_interpreted": False,
            "source_or_sealed_artifacts_modified": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--root", action="append", default=[], metavar="LABEL=PATH")
    parser.add_argument("--top-level-archive-root", type=Path, default=DEFAULT_TOP_LEVEL_ARCHIVE_ROOT)
    args = parser.parse_args()
    roots = DEFAULT_ROOTS
    if args.root:
        roots = []
        for value in args.root:
            label, separator, raw_path = value.partition("=")
            if not separator or not label or not raw_path:
                parser.error("--root must use LABEL=PATH")
            roots.append((label, Path(raw_path)))
    result = scan(roots, top_level_archive_root=args.top_level_archive_root)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
