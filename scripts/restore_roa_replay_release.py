"""Restore a pinned private replay package into new source/data directories."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

from scripts.roa_release_io import extract_bytes, safe, sha, verify_record, write_json


def restore(package: Path, pin: str, destination: Path) -> dict:
    package, destination = package.resolve(), destination.absolute()
    if package == destination.resolve() or package in destination.resolve().parents or destination.resolve() in package.parents:
        raise ValueError("PACKAGE_DESTINATION_OVERLAP")
    if not re.fullmatch("[0-9a-f]{64}", pin) or sha(package / "SHA256_MANIFEST.json") != pin:
        raise ValueError("RELEASE_MANIFEST_PIN")
    manifest = json.loads((package / "SHA256_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["status"] != "PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY":
        raise ValueError("RELEASE_NOT_ACCEPTED")
    names = [e["path"] for e in manifest["files"]]
    actual = {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    if len(names) != len(set(names)) or actual != set(names) | {"SHA256_MANIFEST.json"}:
        raise ValueError("RELEASE_COVERAGE")
    for entry in manifest["files"]:
        verify_record(package, entry)
    build = json.loads((package / "BUILD.json").read_text(encoding="utf-8"))
    commit = build["source_commit"]
    if not re.fullmatch("[0-9a-f]{40}", commit) or commit != manifest["source_commit"]:
        raise ValueError("SOURCE_COMMIT")
    entries = json.loads((package / "DATA_INVENTORY_PRIVATE.json").read_text(encoding="utf-8"))["files"]
    safe(destination.parent, destination.name, exists=False)
    destination.mkdir(parents=True, exist_ok=False)
    receipt = dict(status="FAIL", release_manifest_sha256=pin, source_commit=commit,
                   cas_q2_status="NOT READY", clean_environment_tested=False)
    try:
        extract_bytes(package / "DATA_PRIVATE.zip", destination / "data", entries)
        clone = subprocess.run(["git", "clone", "--no-checkout", "--config", "core.autocrlf=false",
            str((package / "SOURCE.bundle").resolve()), str(destination / "source")], capture_output=True, check=True)
        checkout = subprocess.run(["git", "checkout", "--detach", commit], cwd=destination / "source", capture_output=True, check=True)
        with (destination / "GIT_RESTORE.log").open("xb") as f:
            f.write(clone.stdout + clone.stderr + checkout.stdout + checkout.stderr)
        actual_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=destination / "source", text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=destination / "source", text=True).strip()
        if actual_commit != commit or dirty:
            raise ValueError("RESTORED_SOURCE_STATE")
        for entry in manifest["files"]:
            verify_record(package, entry)
        receipt.update(status="PASS_ARCHIVE_RESTORED_ONLY", data_files=len(entries),
                       source_clean=True, numerical_replay_status="NOT_RUN")
    except Exception as exc:
        receipt.update(error=repr(exc), partial_outputs_retained=True)
    write_json(destination / "RESTORE.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    result = restore(args.package.resolve(), args.manifest_sha256, args.destination.absolute())
    print(json.dumps(result))
    return 0 if result["status"] == "PASS_ARCHIVE_RESTORED_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
