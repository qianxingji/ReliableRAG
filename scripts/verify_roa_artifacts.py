"""Authenticate the sealed ROA namespace without executing scientific code.

A PASS establishes byte integrity and namespace coverage only. Numerical replay,
upstream dependency validation and scientific readiness are separate operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any

SPEC_PATH = Path(__file__).resolve().parents[1] / "docs/cas_q2/ROA_MANIFEST_SPEC.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative_path(value: str) -> PurePosixPath:
    """Accept canonical portable relative paths; reject aliases before I/O."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("non-canonical relative path")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("empty or traversal path component")
    p = PurePosixPath(value)
    if p.is_absolute():
        raise ValueError("absolute path")
    return p


def safe_file(root: Path, relative: PurePosixPath) -> Path:
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError("symlink in artifact path")
    current.resolve().relative_to(root)
    if not stat.S_ISREG(current.stat().st_mode):
        raise ValueError("artifact is not a regular file")
    return current


def verify(project_root: Path, manifest_path: Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Verify the trusted manifest and all payloads; return explicit stage states."""
    result: dict[str, Any] = {
        "integrity_status": "FAIL", "numeric_replay_status": "NOT_RUN",
        "upstream_dependencies_status": "NOT_CHECKED",
        "controls_status": "NOT_RUN", "cas_q2_status": "NOT READY",
        "scientific_fit_calls": 0, "retrieval_generation_calls": 0,
        "verified_files": 0, "issues": [],
    }
    issues = result["issues"]
    root = project_root.resolve()
    try:
        if not root.is_dir():
            raise ValueError("project root is not a directory")
        if spec["schema_version"] != 1:
            raise ValueError("unsupported spec schema")
        namespace = relative_path(spec["namespace"])
        canonical_manifest = relative_path(spec["manifest_path"])
        if canonical_manifest != namespace / "SHA256_MANIFEST.json":
            raise ValueError("manifest outside declared namespace")
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise ValueError("manifest missing or not a regular file")
        manifest_bytes = manifest_path.read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest() != spec["manifest_sha256"]:
            raise ValueError("manifest hash mismatch")
        manifest = json.loads(manifest_bytes)
        if manifest["status"] != "PASS" or manifest["hard_stop"] is not True:
            raise ValueError("manifest is not a completed sealed stage")
        if manifest["exact_recursive_coverage"] is not True:
            raise ValueError("manifest does not assert exact coverage")
        if manifest["excludes_only"] != "SHA256_MANIFEST.json":
            raise ValueError("unexpected manifest exclusions")
        entries = manifest["files"]
        if not isinstance(entries, list) or not entries:
            raise ValueError("empty or invalid payload list")
        if len(entries) != spec["payload_file_count"] or len(entries) != manifest["payload_file_count"]:
            raise ValueError("payload count mismatch")
        seen: set[str] = set()
        checked = []
        for entry in entries:
            rel = relative_path(entry["path"])
            if namespace not in rel.parents or rel == canonical_manifest:
                raise ValueError("payload outside namespace or manifest included")
            key = rel.as_posix().casefold()
            if key in seen:
                raise ValueError("duplicate or case-aliased payload path")
            seen.add(key)
            if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
                raise ValueError("invalid payload digest")
            size = entry["size_bytes"]
            if type(size) is not int or size < 0:
                raise ValueError("invalid payload size")
            checked.append((entry, rel))
        if sum(e["size_bytes"] for e, _ in checked) != spec["payload_size_bytes"]:
            raise ValueError("payload total size mismatch")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append({"kind": "MANIFEST_ERROR", "detail": str(exc)})
        return result

    result["expected_files"] = len(checked)
    result["manifest_sha256"] = spec["manifest_sha256"]
    # An external copy can diagnose missing payloads, but cannot hide a changed
    # or absent manifest in the original namespace.
    try:
        original_manifest = safe_file(root, canonical_manifest)
        if digest(original_manifest) != spec["manifest_sha256"]:
            raise ValueError("original namespace manifest hash mismatch")
    except (OSError, ValueError) as exc:
        issues.append({"kind": "ORIGINAL_MANIFEST_ERROR", "detail": str(exc)})
    for entry, rel in checked:
        try:
            path = safe_file(root, rel)
            before = path.stat()
            actual_hash = digest(path)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (
                after.st_size, after.st_mtime_ns, after.st_ino
            ):
                raise ValueError("artifact changed during hashing")
            if after.st_size != entry["size_bytes"] or actual_hash != entry["sha256"]:
                raise ValueError("artifact size/hash mismatch")
            result["verified_files"] += 1
        except (OSError, ValueError) as exc:
            issues.append({"kind": "PAYLOAD_ERROR", "path": str(rel), "detail": str(exc)})

    ns_path = root.joinpath(*namespace.parts)
    # Refuse to walk symlinked namespace ancestors even if no payload was readable.
    cursor = root
    unsafe_namespace = False
    for part in namespace.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            unsafe_namespace = True
            issues.append({"kind": "UNSAFE_NAMESPACE", "path": str(namespace)})
            break
    if not unsafe_namespace:
        expected_paths = {str(rel) for _, rel in checked}
        def on_walk_error(exc: OSError) -> None:
            issues.append({"kind": "COVERAGE_ERROR", "detail": str(exc)})

        try:
            for directory, directories, files in os.walk(ns_path, onerror=on_walk_error):
                for name in directories + files:
                    path = Path(directory) / name
                    rel = path.relative_to(root).as_posix()
                    if path.is_symlink():
                        issues.append({"kind": "SYMLINK", "path": rel})
                    elif not path.is_dir() and rel != str(canonical_manifest):
                        if rel not in expected_paths:
                            issues.append({"kind": "UNLISTED_FILE", "path": rel})
        except OSError as exc:
            issues.append({"kind": "COVERAGE_ERROR", "detail": str(exc)})
    result["integrity_status"] = "PASS" if not issues else "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, help="Optional copy of the pinned manifest; payloads still use project-root")
    parser.add_argument("--output", type=Path, help="New JSON report outside the sealed namespace; never overwritten")
    args = parser.parse_args()
    try:
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        manifest_path = args.manifest or args.project_root / spec["manifest_path"]
        if args.output:
            destination = args.output.resolve()
            sealed_root = (args.project_root / spec["namespace"]).resolve()
            if destination == sealed_root or sealed_root in destination.parents:
                raise ValueError("report must be outside the sealed namespace")
            if destination.exists() or args.output.is_symlink():
                raise ValueError("report destination already exists")
        result = verify(args.project_root, manifest_path, spec)
        rendered = json.dumps(result, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        sys.stdout.write(rendered)
        return 0 if result["integrity_status"] == "PASS" else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"integrity_status": "FAIL", "error": str(exc),
                          "numeric_replay_status": "NOT_RUN", "cas_q2_status": "NOT READY"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
