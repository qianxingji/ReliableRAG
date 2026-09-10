"""Authenticate upstream namespaces and reconstruct local training-ID provenance.

No model deserialization, fitting, inference, new-ID selection or raw Gold reads.
Historical training membership is explicitly source/ledger reconstruction, not a
new assertion that an unavailable per-fit execution receipt was recovered.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from scripts.replay_roa_original import REPO, bind_original, install_boundary, write_json
from scripts.verify_roa_artifacts import SPEC_PATH, digest, relative_path, safe_file, verify


def records(value):
    if isinstance(value, dict):
        if all(k in value for k in ("path", "sha256", "size_bytes")):
            yield value
        for item in value.values(): yield from records(item)
    elif isinstance(value, list):
        for item in value: yield from records(item)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    root, out = args.project_root.resolve(), args.output.resolve()
    if out == root or root in out.parents: p.error("New output outside original project required")
    out.mkdir(parents=True, exist_ok=False)
    report = dict(status="FAIL", cas_q2_status="NOT READY", scientific_fit_calls=0,
                  retrieval_generation_calls=0, source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip(),
                  script_sha256=digest(Path(__file__)), manifests=[], checks=[], gaps=[])
    cache = {}

    def check(entry):
        path = safe_file(root, relative_path(entry["path"]))
        if entry["path"] not in cache:
            cache[entry["path"]] = (path.stat().st_size, digest(path))
        if cache[entry["path"]] != (entry["size_bytes"], entry["sha256"]):
            raise RuntimeError("HASH_MISMATCH:" + entry["path"])
        return path

    def load(rel): return json.loads((root / rel).read_text(encoding="utf-8"))

    def manifest(entry):
        path = check(entry)
        data = json.loads(path.read_text())
        payload = data["files"]
        names = [e["path"] for e in payload]
        if len(names) != len(set(n.casefold() for n in names)): raise RuntimeError("DUPLICATE_MANIFEST")
        for e in payload: check(e)
        actual = {x.relative_to(root).as_posix() for x in path.parent.rglob("*") if x.is_file()}
        expected = set(names) | {entry["path"]}
        if actual != expected: raise RuntimeError("NAMESPACE_COVERAGE:" + entry["path"])
        report["manifests"].append(dict(manifest=entry, payload_files=len(payload), payload_bytes=sum(e["size_bytes"] for e in payload), status="PASS"))
        print("AUTHENTICATED",entry["path"],len(payload),flush=True)

    try:
        spec = json.loads(SPEC_PATH.read_text())
        result = verify(root, root / spec["manifest_path"], spec)
        if result["integrity_status"] != "PASS": raise RuntimeError("ROA_ANCHOR")
        c = bind_original(root, out)
        install_boundary(out)
        direct = c.parents()
        for item in direct["manifests"]: manifest(item["manifest"])
        failure = load("outputs/daa_v3_development/failure_audit_v1/INPUT_VERIFICATION.json")
        for k in ("prelabel_manifest", "final_manifest"): manifest(failure[k]["manifest"])
        pre = load("outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/PREFLIGHT_INPUT_VERIFICATION.json")
        for item in pre["parents"]["namespaces"]: manifest(item["manifest"])
        pool = load("outputs/daa_v2_fresh_v1/pool_freeze/PREFLIGHT_INPUT_VERIFICATION.json")
        seen = {r["manifest"]["path"] for r in report["manifests"]}
        for item in records(pool):
            if item["path"].endswith("/SHA256_MANIFEST.json") and item["path"] not in seen:
                manifest(item); seen.add(item["path"])
        # Authenticate the original historical model allowlist and nine model/control files.
        private = load("outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/private_artifacts.json")
        requirements_path = "docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json"
        if digest(root / requirements_path) != private["requirements_sha256"]: raise RuntimeError("MODEL_REQUIREMENTS")
        required = load(requirements_path)
        for item in required["required_historical_files"]:
            check(dict(item, path="outputs/mars_full/" + item["path"]))
        for item in pre["historical_source_authentication"]["sources"]: check(item)
        check(pre["historical_source_authentication"]["allowlist"])
        for item in pre["historical_development_ledgers"]: check(item)
        for item in records([pre["gbv"]["files"], pre["gbv_local_cache_copies"]]): check(item)
        report["gbv"] = dict(model="MoritzLaurer/deberta-v3-large-zeroshot-v2.0", revision="5a4338ab2151dc8db04ad53b42b6153382bf4f99", local_task_fit=False,
                              artifacts=pre["gbv"]["files"], pretraining_overlap="NOT_ESTABLISHED")
        inventories = pre["parents"]["runtime_model_inventory"]
        for inventory in inventories.values():
            for item in inventory["file_inventory"]:
                check(dict(item, path=inventory["cache_snapshot_path"] + "/" + item["path"]))
        report["reader_encoder"] = {k:{n:v[n] for n in ("expected_revision", "file_count", "cache_snapshot_path")} for k,v in inventories.items()}
        # The historical output manifest is not pinned by the new ROA manifest.
        # Distinguish its self-consistency from the byte-pinned model requirement list.
        hist = load("outputs/mars_full/manifest.json")
        hist_expected = {}
        for item in hist["files"]:
            mapped = dict(item, path="outputs/mars_full/" + item["path"])
            check(mapped); hist_expected[item["path"]] = mapped
        report["historical_manifest"] = dict(path="outputs/mars_full/manifest.json", sha256=digest(root / "outputs/mars_full/manifest.json"), verified_payloads=len(hist["files"]),
                                             trust="LOCAL_MANIFEST_SELF_CONSISTENCY; models additionally bound by authenticated V2 requirements")
        for name in ("features/development/pair_records.jsonl", "evaluation_only/development_labels.jsonl"):
            if name not in hist_expected: raise RuntimeError("HISTORICAL_LEDGER_MISSING")
        def lines(rel):
            return [json.loads(line) for line in (root / rel).read_text(encoding="utf-8").splitlines() if line.strip()]
        def key(row): return row["dataset"], row["sample_id"]
        def fullkey(row): return row["dataset"], row["split"], row["sample_id"], row["retriever"]
        current = lines(spec["namespace"] + "/NUMERIC_FEATURES_PRIVATE.jsonl")
        groups = {key(r) for r in current}
        labels = lines("outputs/mars_full/evaluation_only/development_labels.jsonl")
        pairs = lines("outputs/mars_full/features/development/pair_records.jsonl")
        bykey = {fullkey(r):r for r in labels}
        if len(bykey) != len(labels): raise RuntimeError("DUPLICATE_HISTORICAL_LABEL")
        training = [r for r in pairs if bykey[fullkey(r)]["preference_label"] in (0,1)]
        universe = {key(r) for r in labels}
        informative = {key(r) for r in training}
        forbidden = {key(r) for r in lines("outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl")}
        overlap = groups & universe
        if overlap or groups & forbidden or not universe <= forbidden: raise RuntimeError("UPSTREAM_TRAINING_OVERLAP_OR_EXCLUSION_GAP")
        models = load("outputs/mars_full/models/manifest.json")
        fields = ["state_symmetric_hgb","state_symmetric_logistic","no_cross_state","no_B","no_evidence_change","no_answer_form","ordinary_compact_logistic"]
        training_ledger = []
        for row in training:
            training_ledger.append({k:row[k] for k in ("dataset","split","sample_id","retriever","development_source")})
        with (out / "UPSTREAM_TRAINING_IDS_PRIVATE.jsonl").open("x",encoding="utf-8") as f:
            for row in training_ledger: f.write(json.dumps(row,sort_keys=True)+"\n")
        scope = dict(source_function="src/mars/full_experiment.py:freeze_method", rule="pair rows with preference_label in (0,1); same subset for seven final historical estimators",
                     development_trace_rows=len(labels), development_questions=len(universe), pair_rows=len(pairs), fit_trace_rows=len(training), fit_questions=len(informative),
                     all_development_overlap_with_ROA=len(overlap), fit_overlap_with_ROA=len(informative & groups), historical_forbidden_overlap_with_ROA=len(groups & forbidden),
                     development_roles=dict(Counter(r["split"] for r in labels)),fit_roles=dict(Counter(r["split"] for r in training)),
                     fit_datasets=dict(Counter(r["dataset"] for r in training)),
                     training_membership_evidence="RECONSTRUCTED_FROM_AUTHENTICATED_SOURCE_AND_LOCALLY_MANIFESTED_LEDGERS; not an original per-fit ID receipt",
                     input_records=[hist_expected[n] for n in ("features/development/pair_records.jsonl","evaluation_only/development_labels.jsonl")])
        report["learned_inputs"] = [dict(field=name,model=models[name],training_scope=scope) for name in fields]
        report["non_task_trained_inputs"] = dict(B_rule="deterministic feature from authenticated original code",higher_own_likelihood="L11-L00",likelihood_margin="m1",gbv_margin="frozen pretrained verifier; no local task fitting")
        old = lines("outputs/mars_full/predictions/confirmatory_decisions_frozen.jsonl")
        oldgroups = {key(r) for r in old}
        if oldgroups & groups: raise RuntimeError("V2_TRAINING_OVERLAP")
        report["V2_comparator"] = dict(role="comparison only, not ROA predictor",training_traces=len(old),training_questions=len(oldgroups),overlap_with_ROA=0,
                                      model_manifest=load("outputs/daa_v2_fresh_v1/prelabel_seal_v3/models/daa_v2_manifest.json"))
        report["lodo_scope"] = "ROA-head transport only: upstream historical estimators used all three datasets, including each LODO held-out dataset on different questions. Not end-to-end unseen-domain transfer."
        report["gaps"] = ["No independent pre-ROA pinned hash for the historical complete mars_full manifest recovered; its training ledger hashes are internally consistent only.",
                          "No original per-estimator training-ID/matrix execution receipt recovered for the seven historical estimators. Their membership is reconstructed from saved source and ledgers; unknown unlogged activity is not excluded.",
                          "Pretrained Qwen/BGE/NLI training-data overlap is not established; no pretraining-contamination-free claim.",
                          "This audit hashes upstream inference artifacts; it does not rerun retrieval, generation, likelihood, embeddings or NLI."]
        report["verified_unique_files"] = len(cache)
        report["verified_unique_bytes"] = sum(v[0] for v in cache.values())
        report["status"] = "AUTHENTICATED_LOCAL_LINEAGE_WITH_HISTORICAL_RECEIPT_LIMITATION"
    except Exception as exc:
        import traceback
        report["error"] = repr(exc); report["traceback"] = traceback.format_exc()
    write_json(out / "UPSTREAM_PROVENANCE.json",report)
    print(json.dumps({k:v for k,v in report.items() if k in ("status","error","verified_unique_files","verified_unique_bytes")}))
    return 2 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
