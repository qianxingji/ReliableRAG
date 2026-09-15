"""Create a local ROA review ZIP after authenticating the original namespace.

Nothing is uploaded. A bundle is evidence for review, not a numerical replay.
The archive preserves original project-relative paths and excludes upstream
artifacts outside the pinned ROA namespace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from scripts.verify_roa_artifacts import SPEC_PATH, digest, relative_path, safe_file, verify


def package(project_root: Path, output: Path, spec: dict) -> dict:
    root = project_root.resolve()
    namespace = root / spec["namespace"]
    destination = output.resolve()
    if destination == namespace or namespace in destination.parents:
        raise ValueError("bundle must be outside the sealed namespace")
    if output.exists() or output.is_symlink():
        raise ValueError("bundle destination already exists")
    manifest_path = root / spec["manifest_path"]
    integrity = verify(root, manifest_path, spec)
    if integrity["integrity_status"] != "PASS":
        raise ValueError(f"artifact integrity failed: {len(integrity['issues'])} issue(s); run verify_roa_artifacts for details")
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != spec["manifest_sha256"]:
        raise ValueError("manifest changed after verification")
    entries = json.loads(manifest_bytes)["files"]
    created = False
    try:
        # Exclusive creation: an existing destination is never replaced.
        with output.open("xb") as archive_stream:
            created = True
            with zipfile.ZipFile(archive_stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for entry in entries:
                    path = safe_file(root, relative_path(entry["path"]))
                    h, size = hashlib.sha256(), 0
                    with path.open("rb") as source, archive.open(entry["path"], "w") as target:
                        for chunk in iter(lambda: source.read(1024 * 1024), b""):
                            h.update(chunk)
                            size += len(chunk)
                            target.write(chunk)
                    if h.hexdigest() != entry["sha256"] or size != entry["size_bytes"]:
                        raise ValueError(f"payload changed during packaging: {entry['path']}")
                archive.writestr(spec["manifest_path"], manifest_bytes)
        # Re-read archived bytes, not only CRC metadata, before returning success.
        with zipfile.ZipFile(output, "r") as archive:
            expected = {e["path"] for e in entries} | {spec["manifest_path"]}
            if len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
                raise ValueError("archive coverage mismatch")
            for entry in entries + [{"path": spec["manifest_path"],
                                     "sha256": spec["manifest_sha256"],
                                     "size_bytes": len(manifest_bytes)}]:
                h, size = hashlib.sha256(), 0
                with archive.open(entry["path"]) as member:
                    for chunk in iter(lambda: member.read(1024 * 1024), b""):
                        h.update(chunk)
                        size += len(chunk)
                if h.hexdigest() != entry["sha256"] or size != entry["size_bytes"]:
                    raise ValueError(f"archive member mismatch: {entry['path']}")
        return {"bundle_status": "PASS", "bundle_path": str(output.resolve()),
                "bundle_sha256": digest(output), "payload_files": len(entries),
                "manifest_sha256": spec["manifest_sha256"],
                "numeric_replay_status": "NOT_RUN", "upstream_dependencies_status": "NOT_CHECKED",
                "cas_q2_status": "NOT READY", "uploaded": False,
                "scientific_fit_calls": 0, "retrieval_generation_calls": 0}
    except Exception:
        if created:
            output.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New local ZIP outside the sealed namespace")
    args = parser.parse_args()
    try:
        result = package(args.project_root, args.output, json.loads(SPEC_PATH.read_text()))
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"bundle_status": "FAIL", "error": str(exc), "uploaded": False,
                          "numeric_replay_status": "NOT_RUN", "cas_q2_status": "NOT READY"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
