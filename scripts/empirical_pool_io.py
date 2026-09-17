"""Authentication and IO only; contains no projector, builder or model."""
import importlib.util
import json
import os
from pathlib import Path
import sys

from scripts.replay_roa_original import REPO, write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path

DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
SPLITS = dict(hotpotqa="validation", **{"2wikimultihopqa": "dev"}, musique="train")
OUT = REPO / "outputs/cas_q2/empirical_candidate_pool_v1"
PREFLIGHT_SHA = "289a19f1ff3f8ec7fea2b835f2e19b4c5d2afc5d56cf2b96d9f7c81629e17c35"
COHORT_SHA = "6070c63b9cbf3277ef328d059dcaabc98480ba2bb60503b66ad2faa5e816b62a"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def record(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=digest(path), size_bytes=path.stat().st_size)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def checked(path, sha, size=None):
    require(digest(path) == sha, "Input digest mismatch")
    require(size is None or path.stat().st_size == size, "Input size mismatch")
    return path


def verify_namespace(folder, anchor):
    mp = checked(folder / "SHA256_MANIFEST.json", anchor)
    entries = load(mp)["files"]
    require({p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} ==
            {e["path"] for e in entries} | {"SHA256_MANIFEST.json"}, "Namespace file set")
    paths = [mp]
    for e in entries:
        paths.append(checked(safe_file(folder, relative_path(e["path"])), e["sha256"], e["size_bytes"]))
    return paths


def authenticate(root, replay_root):
    audit = checked(replay_root / "p0_1_upstream_v2/UPSTREAM_PROVENANCE.json",
                    "d368dc747ec8dbc6d2208e97e7bd2da8ecbebf1dcdda080f02d2317661c1ad47")
    entry = next(r["manifest"] for r in load(audit)["manifests"]
                 if r["manifest"]["path"].endswith("pool_freeze/SHA256_MANIFEST.json"))
    old_manifest = checked(root / entry["path"], entry["sha256"], entry["size_bytes"])
    records = {e["path"]: e for e in load(old_manifest)["files"]}
    paths = [audit, old_manifest]
    def oldfile(name):
        rel = "outputs/daa_v2_fresh_v1/pool_freeze/" + name
        e = records[rel]
        path = checked(safe_file(root, relative_path(rel)), e["sha256"], e["size_bytes"])
        paths.append(path)
        return path
    helper = oldfile("pool_support.py")
    oldfile("construct_pools.py")
    provenance = load(oldfile("ACCEPTED_IMPLEMENTATION_PROVENANCE.json"))
    for e in provenance["sources"] + provenance["evidence_controls"]:
        paths.append(checked(safe_file(root, relative_path(e["path"])), e["sha256"]))
    prior = load(oldfile("PREFLIGHT_INPUT_VERIFICATION.json"))
    sources = {}
    for d, e in prior["source_byte_inputs"].items():
        sources[d] = checked(safe_file(root, relative_path(e["path"])), e["sha256"], e["size_bytes"])
        paths.append(sources[d])
    require(set(sources) == set(DATASETS), "Source datasets")
    preflight = REPO / "outputs/cas_q2/empirical_projection_preflight_v1"
    paths.extend(verify_namespace(preflight, PREFLIGHT_SHA))
    require(load(preflight / "PREFLIGHT_RESULT.json")["status"] ==
            "PASS_VALUE_BLIND_PROJECTION_PREFLIGHT_ONLY", "Preflight status")
    # Reuse the exact census results only after all source bytes match again.
    for d in ("2wikimultihopqa", "musique"):
        census = load(preflight / (d + "_CENSUS.json"))
        require(census["source_sha256"] == digest(sources[d]), "Census source binding")
    cohort = REPO / "outputs/cas_q2/empirical_fresh_cohort_v1"
    paths.extend(verify_namespace(cohort, COHORT_SHA))
    require(load(cohort / "INDEPENDENT_VALIDATION.json")["status"] ==
            "PASS_ID_ONLY_EMPIRICAL_COHORT", "Cohort status")
    ids = [json.loads(line) for line in (cohort / "SELECTED_IDS_PRIVATE.jsonl").read_text(encoding="utf-8").splitlines()]
    require(len(ids) == 6000 and len({(r["dataset"], r["sample_id"]) for r in ids}) == 6000, "Cohort count")
    require(all(sum(r["dataset"] == d for r in ids) == 2000 for d in DATASETS), "Balanced cohort")
    return helper, sources, ids, sorted(set(paths)), preflight


def load_native(helper, root):
    spec = importlib.util.spec_from_file_location("empirical_native_pool_support", helper)
    native = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = native
    spec.loader.exec_module(native)
    native.ROOT = root
    native.OUT = root / "outputs/daa_v2_fresh_v1/pool_freeze"
    return native


def restrict_reads(paths, output):
    exact = {Path(p).resolve() for p in paths}
    runtime = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), output]
    reads = set()
    def audit(event, args):
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        require(path in exact or any(path == d or d in path.parents for d in runtime), "Read outside C1 allowlist")
        reads.add(str(path))
    sys.addaudithook(audit)
    return reads


def seal_execution(output):
    write_json(output / "EXECUTION_MANIFEST.json", dict(files=[
        dict(path=p.relative_to(output).as_posix(), sha256=digest(p), size_bytes=p.stat().st_size)
        for p in sorted(output.rglob("*")) if p.is_file()]))
