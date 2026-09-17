"""Authenticate fixed scoring assets without loading models or reading fresh branches."""
import argparse
import importlib.metadata
from pathlib import Path
import subprocess
import sys

from scripts.empirical_pool_io import checked, load, record, require
from scripts.replay_roa_original import REPO, install_boundary, write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path

PARENT = "0a5246a6d270ee01674d099b970a577936bd95d6200a53e1aa3e2ce524857bfd"
PANEL = "4579e712f5ad513d7a9ca1229809432f766c05d5d9033b9053563c076629a619"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args(); root = args.project_root.resolve()
    out = REPO / "outputs/cas_q2/empirical_scoring_input_audit_v1"
    require(not out.exists(), "Single-use scoring availability audit")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    out.mkdir(parents=True, exist_ok=False); install_boundary(out)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, model_load_calls=0,
                  model_forward_calls=0, scientific_fit_calls=0, fresh_branch_rows_read=0,
                  fresh_gold_values_materialized=0, checked_files=[])
    seen = set()
    try:
        def check(path, sha, size=None):
            path = checked(path, sha, size)
            if path not in seen: result["checked_files"].append(record(path)); seen.add(path)
            return path
        def old_record(entry):
            return check(safe_file(root, relative_path(entry["path"])), entry["sha256"], entry["size_bytes"])
        parent = root / "outputs/daa_v2_fresh_v1/prelabel_seal_v3"
        manifest = check(parent / "SHA256_MANIFEST.json", PARENT)
        entries = {e["path"]: e for e in load(manifest)["files"]}
        def parent_file(name):
            return old_record(entries[(parent / name).relative_to(root).as_posix()])
        pre = load(parent_file("preflight/PREFLIGHT_INPUT_VERIFICATION.json"))
        freeze = load(parent_file("EXECUTABLE_INPUT_FREEZE_CONTROL_R1.json"))
        compatibility = load(parent_file("preflight/GBV_RESOLVER_COMPATIBILITY.json"))
        require(pre["status"] == freeze["status"] == compatibility["status"] == "PASS", "Original scoring controls")
        require(compatibility["entailment_index"] == 0 and compatibility["resolver_monkeypatch_or_override"] is False, "Reviewed GbV resolver")
        for name in ("native_base.py", "v3_support.py", "score_base.py", "independent_validate_control_r1.py",
                     "models/daa_v2.joblib", "models/daa_v2_manifest.json"):
            parent_file(name)
        for entry in pre["historical_source_authentication"]["sources"] + compatibility["committed_sources"]:
            old_record(entry)
        for entry in pre["gbv"]["files"] + pre["gbv"]["package_files"]:
            old_record(entry)
        for entry in (pre["historical_config"]["source"], pre["phase3_config"]["source"], pre["environment"]["executable"]):
            old_record(entry)
        model_records = [e for e in freeze["files"] if e["path"].startswith("outputs/mars_full/models/")]
        require(sum(e["path"].endswith(".joblib") for e in model_records) == 7, "Exactly seven original upstream estimators")
        for entry in model_records: old_record(entry)
        old_record(next(e for e in freeze["files"] if e["path"] == "outputs/mars_full/method_freeze.json"))
        panel = REPO / "outputs/cas_q2/empirical_fixed_panel_v1"
        panel_mf = check(panel / "SHA256_MANIFEST.json", PANEL)
        panel_entries = {e["path"]: e for e in load(panel_mf)["files"]}
        for name in ("MODELS.json", "INDEPENDENT_VALIDATION.json", "EXECUTABLE_FREEZE.json"):
            entry = panel_entries[name]; check(panel/name, entry["sha256"], entry["size_bytes"])
        packages = {name: importlib.metadata.version(name) for name in pre["environment"]["versions"]}
        require(packages == pre["environment"]["versions"], "Original scoring package versions")
        require(record(Path(sys.executable))["sha256"] == pre["environment"]["executable"]["sha256"], "Same interpreter")
        v2 = load(parent / "models/daa_v2_manifest.json")
        require(v2["model_sha256"] == digest(parent / "models/daa_v2.joblib"), "V2 model self binding")
        require(v2["reference_trace_count"] == 9000 and v2["action_rate"] == 0.05, "Original V2 reference")
        for item in result["checked_files"]:
            require(record(Path(item["path"])) == item, "Scoring inventory input changed")
        result.update(status="PASS_SCORING_INPUT_INVENTORY_ONLY", packages=packages, source=record(Path(__file__)),
            command=sys.argv, original_prelabel_manifest_sha256=PARENT, fixed_panel_manifest_sha256=PANEL,
            original_upstream_estimator_files=7, fixed_panel_model_artifact=record(panel/"MODELS.json"),
            v2_model=record(parent/"models/daa_v2.joblib"), v2_refit_authorized=False,
            historical_reader_scorer=pre["historical_config"]["reader_scorer"], answer_embedding=pre["phase3_config"],
            gbv=dict(model_id=compatibility["model_id"],revision=compatibility["model_revision"],entailment_index=0,
                     model_files=len(pre["gbv"]["files"]),package_files=len(pre["gbv"]["package_files"])),
            limitations="Availability and byte/version authentication only. No estimator/model load, fresh branch access, scoring, action selection or outcome access. C3 completion and C4 executable adapter/preflight/independent acceptance remain required; historical fit-time receipts are not recovered.")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    write_json(out / "SCORING_INPUT_AUDIT.json", result)
    write_json(out / "SHA256_MANIFEST.json", dict(files=[dict(path=p.name,sha256=digest(p),size_bytes=p.stat().st_size)
        for p in sorted(out.iterdir()) if p.is_file()]))
    print(result["status"], result.get("diagnostic", "")); return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
