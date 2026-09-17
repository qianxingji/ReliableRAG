"""Build a local dependency-complete ROA saved-parameter replay package."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

from scripts.roa_release_io import (archive_check, package_bytes, record, records_index,
                                   safe, sha, verify_record, write_json)

REPO = Path(__file__).resolve().parents[1]
ROA = "outputs/daa_v3_development/recovery_only_isolation_v1"
ROA_PIN = "0921b3b15be2a58b7863911e60cd4ce10cb2b063055dda9823508c3ab2e6a8d6"
CONTROLS_PIN = "55eabaea1635d7903362625862c9d85bef8dd0451fe86a2d3d1126c111cc2f8e"
WRAPPER_PIN = "eadb0c20f97dd8d17a2dd8857e5f86922061b07f901d6bf3c08a5fa6def905c9"


def closure(root: Path) -> tuple[list[dict], dict]:
    """Decode only authenticated source constants and input-list metadata."""
    entries: dict[str, dict] = {}
    scopes = []

    def add(records):
        nonlocal entries
        entries = records_index([*entries.values(), *records])

    def metadata(name, pin=None):
        path = safe(root, name)
        if pin is None:
            verify_record(root, entries[name])
        elif sha(path) != pin:
            raise ValueError("METADATA_PIN:" + name)
        data = path.read_bytes()
        # Revalidate the exact decoded bytes after opening, not just an earlier stat.
        import hashlib
        expected = pin if pin else entries[name]["sha256"]
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("METADATA_CHANGED")
        add([dict(path=name, sha256=expected, size_bytes=len(data))])
        return json.loads(data)

    def namespace(name, pin):
        manifest_name = name + "/SHA256_MANIFEST.json"
        manifest = metadata(manifest_name, pin)
        rows = manifest["files"]
        names = records_index(rows)
        if len(names) != len(rows) or any(not p.startswith(name + "/") or p == manifest_name for p in names):
            raise ValueError("NAMESPACE_RECORDS")
        actual = set()
        for p in (root / name).rglob("*"):
            rel = p.relative_to(root).as_posix()
            safe(root, rel, exists=False)
            if p.is_file():
                actual.add(rel)
        if actual != set(names) | {manifest_name}:
            raise ValueError("NAMESPACE_COVERAGE:" + name)
        add(rows)
        scopes.append(dict(namespace=name, payload_files=len(rows), manifest_sha256=pin))
        return manifest

    namespace(ROA, ROA_PIN)
    controls_path = safe(root, ROA + "/controls.py")
    verify_record(root, entries[ROA + "/controls.py"])
    if sha(controls_path) != CONTROLS_PIN:
        raise ValueError("CONTROLS_PIN")
    constants = {}
    for node in ast.parse(controls_path.read_bytes()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in {"MANIFESTS", "ANCHORS"}:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
    if len(constants["MANIFESTS"]) != 4:
        raise ValueError("PARENT_COUNT")
    for name, pin in constants["MANIFESTS"].items():
        namespace("outputs/daa_v3_development/" + name, pin)
    dhc = "outputs/daa_v3_development/dual_head_constrained_v1/"
    for name, pin in constants["ANCHORS"].items():
        if entries[dhc + name]["sha256"] != pin:
            raise ValueError("DHC_ANCHOR")
    original = metadata(dhc + "INPUT_VERIFICATION.json")
    add(list(original["anchors"].values()) + original["task_and_protocol"])
    for name in (dhc + "EXECUTABLE_CONFIG_FREEZE_R1.json", ROA + "/EXECUTABLE_CONFIG_FREEZE.json"):
        add(metadata(name)["files"])
    records = [entries[name] for name in sorted(entries)]
    for entry in records:
        verify_record(root, entry)
    return records, dict(namespaces=scopes, data_files=len(records),
                         data_bytes=sum(e["size_bytes"] for e in records),
                         authentication_environment_files=[e for e in records if e["path"].startswith(".venv/")])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.project_root.resolve(), args.output.absolute()
    for forbidden in (root, REPO):
        if output.resolve() == forbidden or forbidden in output.resolve().parents:
            parser.error("Release must be outside original project and engineering worktree")
    safe(output.parent, output.name, exists=False)
    if output.exists():
        parser.error("Single-use release directory already exists")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip():
        parser.error("Commit the release code before execution")
    if sha(REPO / "scripts/replay_roa_original.py") != WRAPPER_PIN:
        parser.error("Original replay wrapper changed")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    output.mkdir(parents=True, exist_ok=False)
    state = dict(status="FAIL", started_utc=datetime.now(timezone.utc).isoformat(),
                 source_commit=commit, cas_q2_status="NOT READY", scientific_fit_calls=0,
                 retrieval_generation_calls=0, fresh_gold_values_materialized=0, uploaded=False)
    try:
        records, info = closure(root)
        write_json(output / "DATA_INVENTORY_PRIVATE.json", dict(files=records, **info))
        write_json(output / "ENVIRONMENT.json", dict(python=sys.version, executable=sys.executable,
            platform=platform.platform(), versions={n: importlib.metadata.version(n) for n in
            ("numpy", "scipy", "scikit-learn", "threadpoolctl")},
            scope="Reuses existing host runtime; six archived environment files are authentication bytes, not an install"))
        bundle = output / "SOURCE.bundle"
        subprocess.run(["git", "bundle", "create", str(bundle), "HEAD"], cwd=REPO, check=True, capture_output=True)
        verify = subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=REPO, check=True, capture_output=True)
        with (output / "SOURCE_BUNDLE_VERIFY.log").open("xb") as f:
            f.write(verify.stdout + verify.stderr)
        package_bytes(root, output / "DATA_PRIVATE.zip", records)
        archive_check(output / "DATA_PRIVATE.zip", records)
        state.update(info, status="PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY", archive_all_members_rehashed=True,
            original_inputs_unchanged=True, relocation_replay_status="NOT_RUN",
            source_bundle_sha256=sha(bundle), data_archive_sha256=sha(output / "DATA_PRIVATE.zip"),
            limits=["No clean environment/other host/OS test", "Not full upstream training or fresh empirical pipeline package"])
    except Exception as exc:
        state["error"] = repr(exc)
        state["partial_outputs_retained"] = True
    state["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "BUILD.json", state)
    manifest_name = "SHA256_MANIFEST.json" if state["status"] == "PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY" else "FAILURE_MANIFEST.json"
    write_json(output / manifest_name, dict(status=state["status"], source_commit=commit,
        files=[record(output, p) for p in sorted(output.iterdir()) if p.is_file()]))
    print(json.dumps({k: state[k] for k in ("status", "source_commit", "data_files", "data_bytes", "error") if k in state}))
    return 0 if state["status"] == "PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
