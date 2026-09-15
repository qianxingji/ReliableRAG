"""Opaque model/source byte inventory only; no model loading or fresh acquisition."""
import argparse
import importlib.metadata
from pathlib import Path
import subprocess
import sys

from scripts.empirical_pool_io import checked, load, record, require
from scripts.replay_roa_original import REPO, install_boundary, write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--replay-root", type=Path, required=True)
    args = p.parse_args(); root = args.project_root.resolve()
    out = REPO / "outputs/cas_q2/empirical_acquisition_input_audit_v1"
    require(not out.exists(), "Single-use input audit")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    out.mkdir(parents=True, exist_ok=False); install_boundary(out)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit,
                  model_load_calls=0, model_forward_calls=0, scientific_fit_calls=0,
                  fresh_gold_values_materialized=0, checked_files=[], models={})
    try:
        audit = checked(args.replay_root / "p0_1_upstream_v2/UPSTREAM_PROVENANCE.json",
                        "d368dc747ec8dbc6d2208e97e7bd2da8ecbebf1dcdda080f02d2317661c1ad47")
        manifests = {x["manifest"]["path"]: x["manifest"] for x in load(audit)["manifests"]}
        seen = set()
        def check(path, sha, size=None):
            q = checked(path, sha, size)
            if q not in seen:
                result["checked_files"].append(record(q)); seen.add(q)
            return q
        def old(namespace, names):
            base = "outputs/daa_v2_fresh_v1/" + namespace + "/"
            e = manifests[base + "SHA256_MANIFEST.json"]
            mp = check(root / e["path"], e["sha256"], e["size_bytes"])
            entries = {x["path"]: x for x in load(mp)["files"]}
            answer = {}
            for name in names:
                e = entries[base + name]
                answer[name] = check(safe_file(root, relative_path(e["path"])), e["sha256"], e["size_bytes"])
            return answer
        runtime = old("runtime_branch_freeze", ("RUNTIME_CONFIG_FREEZE.json", "native_runtime.py", "runtime_support.py", "build_runtime.py"))
        retrieval = old("retrieval_freeze", ("PREFLIGHT_INPUT_VERIFICATION.json", "native_retrieval.py", "retrieval_support.py", "build_retrieval.py"))
        cfg = load(runtime["RUNTIME_CONFIG_FREEZE.json"])
        pre = load(retrieval["PREFLIGHT_INPUT_VERIFICATION.json"])
        require(cfg["status"] == "PASS" and pre["status"] == "PASS", "Original config status")
        for e in cfg["accepted_sources"] + cfg["native_controls"] + pre["accepted_source_files"]:
            check(safe_file(root, relative_path(e["path"])), e["sha256"], e["size_bytes"])
        for name, model in cfg["models"].items():
            folder = safe_file(root, relative_path(model["snapshot_relative_path"] + "/config.json")).parent
            require({p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} ==
                    {e["path"] for e in model["file_inventory"]}, "Model snapshot exact inventory")
            for e in model["file_inventory"]:
                check(safe_file(folder, relative_path(e["path"])), e["sha256"], e["size_bytes"])
            result["models"][name] = dict(model_id=model["model_id"], revision=model["revision"],
                files=model["file_count"], bytes=model["total_size_bytes"], status="MATCHES_AUTHENTICATED_SNAPSHOT")
            print("MODEL_BYTES_PASS", name, flush=True)
        packages = {name: importlib.metadata.version(name) for name in cfg["environment"]["packages"]}
        require(packages == cfg["environment"]["packages"], "Package versions differ from frozen runtime")
        e = cfg["environment"]["interpreter"]
        check(Path(sys.executable), e["sha256"], e["size_bytes"])
        result.update(status="PASS_ACQUISITION_INPUT_INVENTORY_ONLY", packages=packages,
            interpreter=record(Path(sys.executable)), source=record(Path(__file__)), command=sys.argv,
            scientific_runtime_config=cfg["runtime_config"],
            limitations="Byte/version availability only. New pool binding, complete executable adapter freeze, GPU compatibility check and independent runtime validation are still required. This is not acquisition execution approval or fresh outcome evidence.")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    write_json(out / "ACQUISITION_INPUT_AUDIT.json", result)
    write_json(out / "SHA256_MANIFEST.json", dict(files=[dict(path=q.name, sha256=digest(q), size_bytes=q.stat().st_size)
        for q in sorted(out.iterdir()) if q.is_file()]))
    print(result["status"]); return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
