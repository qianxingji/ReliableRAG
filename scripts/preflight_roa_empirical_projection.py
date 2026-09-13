"""Value-blind native projection preflight; no fresh runtime text or models."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
from scripts.replay_roa_original import REPO,install_boundary,write_json
from scripts.verify_roa_artifacts import digest,safe_file,relative_path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root",type=Path,required=True)
    p.add_argument("--replay-root",type=Path,required=True)
    args=p.parse_args();root=args.project_root.resolve()
    out=REPO/"outputs/cas_q2/empirical_projection_preflight_v1"
    if out.exists() or (root/"outputs/cas_q2/empirical_projection_preflight_v1").exists():p.error("Single-use preflight namespace")
    if subprocess.check_output(["git","status","--porcelain"],cwd=REPO,text=True).strip():p.error("Commit sources first")
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip()
    out.mkdir(parents=True,exist_ok=False);install_boundary(out)
    result=dict(status="FAIL",source_commit=commit,cas_q2_status="NOT READY",scientific_fit_calls=0,model_calls=0,
                fresh_gold_values_materialized=0,new_runtime_questions_projected=0,inputs=[],censuses={})
    def load(q):return json.loads(q.read_text(encoding="utf-8"))
    def check(q,sha,size=None):
        if digest(q)!=sha or (size is not None and q.stat().st_size!=size):raise RuntimeError("SOURCE_HASH:"+str(q))
        result["inputs"].append(dict(path=str(q),sha256=sha,size_bytes=q.stat().st_size));return q
    try:
        audit=check(args.replay_root/"p0_1_upstream_v2/UPSTREAM_PROVENANCE.json","d368dc747ec8dbc6d2208e97e7bd2da8ecbebf1dcdda080f02d2317661c1ad47")
        entry=next(r["manifest"] for r in load(audit)["manifests"] if r["manifest"]["path"].endswith("pool_freeze/SHA256_MANIFEST.json"))
        mp=check(root/entry["path"],entry["sha256"],entry["size_bytes"])
        records={e["path"]:e for e in load(mp)["files"]}
        def oldfile(name):
            rel="outputs/daa_v2_fresh_v1/pool_freeze/"+name;e=records[rel]
            return check(safe_file(root,relative_path(rel)),e["sha256"],e["size_bytes"])
        helper=oldfile("pool_support.py")
        oldfile("ACCEPTED_IMPLEMENTATION_PROVENANCE.json")
        prior=load(oldfile("PREFLIGHT_INPUT_VERIFICATION.json"))
        source={d:check(safe_file(root,relative_path(e["path"])),e["sha256"],e["size_bytes"]) for d,e in prior["source_byte_inputs"].items()}
        cohort=REPO/"outputs/cas_q2/empirical_fresh_cohort_v1"
        check(cohort/"SHA256_MANIFEST.json","6070c63b9cbf3277ef328d059dcaabc98480ba2bb60503b66ad2faa5e816b62a")
        for e in load(cohort/"SHA256_MANIFEST.json")["files"]:check(safe_file(cohort,relative_path(e["path"])),e["sha256"],e["size_bytes"])
        spec=importlib.util.spec_from_file_location("empirical_native_pool_preflight",helper)
        native=importlib.util.module_from_spec(spec);sys.modules[spec.name]=native;spec.loader.exec_module(native)
        native.ROOT=root
        accepted,nodes=native.load_accepted()
        gate=native.MaterializationGate(accepted);gate.mode="keys_only"
        # Invented canary. A forbidden value must be rejected BEFORE string decoding.
        cursor=accepted._JSONByteCursor(io.BytesIO(b'"invented-canary"'))
        try:
            cursor._consume_string(materialize=True,path="2wikimultihopqa.answer")
        except RuntimeError:pass
        else:raise RuntimeError("FORBIDDEN_SCALAR_GUARD_FAILED")
        assert gate.denied==1
        before=gate.denied
        write_json(out/"EXECUTABLE_PREFLIGHT_FREEZE.json",dict(commit=commit,command=sys.argv,inputs=result["inputs"],
            source=dict(path=str(Path(__file__)),sha256=digest(Path(__file__))),protocol_sha256=digest(REPO/"docs/cas_q2/EMPIRICAL_REPLICATION_PROTOCOL_V1.md"),
            correction_sha256=digest(REPO/"docs/cas_q2/EMPIRICAL_SAMPLE_SIZE_CORRIGENDUM.md"),
            scope="Keys/shapes only; no selected runtime projection, pool build, model or Gold decoding",native_ast_nodes=nodes))
        for dataset,expected in (("2wikimultihopqa",12576),("musique",19938)):
            census=accepted.census_source_file(source[dataset],dataset=dataset,source_path=str(source[dataset]))
            assert census["status"]=="PASS" and not census["unclassified_key_paths"] and census["row_count"]==expected
            write_json(out/(dataset+"_CENSUS.json"),census)
            result["censuses"][dataset]=dict(status=census["status"],row_count=census["row_count"],unclassified_key_paths=census["unclassified_key_paths"])
            print("CENSUS_PASS",dataset,expected,flush=True)
        assert gate.denied==before
        for e in result["inputs"]:assert digest(Path(e["path"]))==e["sha256"]
        result.update(status="PASS_VALUE_BLIND_PROJECTION_PREFLIGHT_ONLY",synthetic_forbidden_scalar_attempts_blocked=1,
                      actual_forbidden_scalar_attempts=gate.denied-before,materialization_path_counts=gate.report()["scalar_decode_path_counts"],
                      sources_unchanged=True,hotpot_scope="Existing authenticated full gold-free runtime projection; no fresh row projected in this stage",
                      remaining="Complete stage C pool adapter/independent validator and its input freeze, then retrieval/runtime/scoring adapters; inference/outcome mapping not started")
    except Exception as exc:
        import traceback
        result.update(error=repr(exc),traceback=traceback.format_exc())
    write_json(out/"PREFLIGHT_RESULT.json",result)
    write_json(out/"SHA256_MANIFEST.json",dict(files=[dict(path=q.name,sha256=digest(q),size_bytes=q.stat().st_size) for q in sorted(out.iterdir()) if q.is_file()]))
    print(json.dumps({k:result[k] for k in ("status","new_runtime_questions_projected","model_calls")}))
    return 2 if result["status"]=="FAIL" else 0


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
