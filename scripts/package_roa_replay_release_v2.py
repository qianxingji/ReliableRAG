"""Complete direct-input closure; v1 package is preserved and rejected."""
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

from scripts import package_roa_replay_release as v1
from scripts.roa_release_io import package_bytes, record, records_index, safe, sha, verify_record, write_json

PARENT_RECEIPT_PIN = "232276f623c611af3e82814a25a03100965f77ab4935f9c1934156a4be04c770"
DIRECT_PATHS = {
    "actions": "outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/v2_actions.jsonl",
    "base": "outputs/daa_v2_fresh_v1/prelabel_seal_v3/scoring/v2_base_scores.jsonl",
    "gbv": "outputs/daa_v2_fresh_v1/prelabel_seal_v3/scoring/gbv_scores.jsonl",
    "outcomes": "outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl",
}


def parent_coverage(records: list[dict], accepted: list[dict]) -> int:
    present = records_index(records)
    prior = records_index(accepted)
    if len(prior) != len(accepted):
        raise ValueError("DUPLICATE_ACCEPTED_PARENT")
    for name, entry in prior.items():
        if present.get(name) != entry:
            raise ValueError("ACCEPTED_PARENT_MISSING_OR_DIFFERENT:" + name)
    return len(prior)


def closure(root: Path, accepted: list[dict]) -> tuple[list[dict], dict]:
    records, info = v1.closure(root)
    controls = safe(root, v1.ROA + "/controls.py")
    if sha(controls) != v1.CONTROLS_PIN:
        raise ValueError("CONTROLS_PIN")
    # Literal data only: do not run controls.parents() or any scientific code.
    tree = ast.parse(controls.read_bytes())
    parents = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "parents")
    assignment = next(n for n in parents.body if isinstance(n, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == "expected_sources" for t in n.targets))
    value = assignment.value
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name) or value.func.id != "dict" or value.args:
        raise ValueError("DIRECT_DIGEST_LITERAL")
    pins = {k.arg: ast.literal_eval(k.value) for k in value.keywords}
    if set(pins) != set(DIRECT_PATHS) or len(value.keywords) != 4:
        raise ValueError("DIRECT_SOURCE_COVERAGE")
    direct = []
    for name, rel in DIRECT_PATHS.items():
        path = safe(root, rel)
        entry = record(root, path)
        if entry["sha256"] != pins[name]:
            raise ValueError("DIRECT_INPUT_PIN:" + name)
        direct.append(entry)
    entries = records_index([*records, *direct])
    records = [entries[name] for name in sorted(entries)]
    matched = parent_coverage(records, accepted)
    if matched != 2601:
        raise ValueError("ACCEPTED_PARENT_COUNT")
    for entry in records:
        verify_record(root, entry)
    info.update(data_files=len(records), data_bytes=sum(e["size_bytes"] for e in records),
                direct_sources=direct, accepted_parent_records_matched=matched,
                dependency_closure_status="PASS_FIVE_NAMESPACES_FOUR_DIRECT_INPUTS_AND_ACCEPTED_PARENT_RECEIPT")
    return records, info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--primary-parent-receipt", type=Path, required=True)
    parser.add_argument("--independent-parent-receipt", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.project_root.resolve(), args.output.absolute()
    for forbidden in (root, v1.REPO):
        if output.resolve() == forbidden or forbidden in output.resolve().parents:
            parser.error("Release must be outside original project and engineering worktree")
    safe(output.parent, output.name, exists=False)
    if output.exists():
        parser.error("Single-use release directory already exists")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=v1.REPO, text=True).strip():
        parser.error("Commit release v2 code before execution")
    if sha(v1.REPO / "scripts/replay_roa_original.py") != v1.WRAPPER_PIN:
        parser.error("Original replay wrapper changed")
    for path in (args.primary_parent_receipt, args.independent_parent_receipt):
        if sha(path) != PARENT_RECEIPT_PIN:
            parser.error("Accepted primary/independent parent receipt pin mismatch")
    parent_bytes = args.primary_parent_receipt.read_bytes()
    import hashlib
    if hashlib.sha256(parent_bytes).hexdigest() != PARENT_RECEIPT_PIN:
        parser.error("Parent receipt changed while reading")
    parent = json.loads(parent_bytes)
    if parent["status"] != "PASS":
        parser.error("Parent receipt not PASS")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=v1.REPO, text=True).strip()
    output.mkdir(parents=True, exist_ok=False)
    state = dict(status="FAIL", started_utc=datetime.now(timezone.utc).isoformat(), source_commit=commit,
                 package_version=2, cas_q2_status="NOT READY", scientific_fit_calls=0,
                 retrieval_generation_calls=0, fresh_gold_values_materialized=0, uploaded=False,
                 accepted_parent_receipt_sha256=PARENT_RECEIPT_PIN,
                 prior_v1_rejected_manifest="d079da6c2c4b4090df7083b06bdc35ebeeca4bfa51d8b74a8418c11d1405f54f")
    try:
        records, info = closure(root, parent["files"])
        write_json(output / "DATA_INVENTORY_PRIVATE.json", dict(files=records, **info))
        with (output / "ACCEPTED_PARENT_VERIFICATION_PRIVATE.json").open("xb") as f:
            f.write(parent_bytes)
        write_json(output / "ENVIRONMENT.json", dict(python=sys.version, executable=sys.executable,
            platform=platform.platform(), versions={n: importlib.metadata.version(n) for n in
            ("numpy", "scipy", "scikit-learn", "threadpoolctl")},
            scope="Existing host runtime; six archived environment files authenticate bytes, not an install"))
        bundle = output / "SOURCE.bundle"
        subprocess.run(["git", "bundle", "create", str(bundle), "HEAD"], cwd=v1.REPO, check=True, capture_output=True)
        check = subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=v1.REPO, check=True, capture_output=True)
        with (output / "SOURCE_BUNDLE_VERIFY.log").open("xb") as f:
            f.write(check.stdout + check.stderr)
        package_bytes(root, output / "DATA_PRIVATE.zip", records)
        state.update(info, status="PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY", archive_all_members_rehashed=True,
            original_inputs_unchanged=True, relocation_replay_status="NOT_RUN",
            source_bundle_sha256=sha(bundle), data_archive_sha256=sha(output / "DATA_PRIVATE.zip"),
            limits=["Not clean environment/other host/OS", "Not upstream training or full fresh empirical pipeline"])
    except Exception as exc:
        state.update(error=repr(exc), partial_outputs_retained=True)
    state["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "BUILD.json", state)
    manifest_name = "SHA256_MANIFEST.json" if state["status"] == "PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY" else "FAILURE_MANIFEST.json"
    write_json(output / manifest_name, dict(status=state["status"], source_commit=commit,
        files=[record(output, p) for p in sorted(output.iterdir()) if p.is_file()]))
    print(json.dumps({k: state[k] for k in ("status", "source_commit", "data_files", "data_bytes", "accepted_parent_records_matched", "error") if k in state}))
    return 0 if state["status"] == "PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
