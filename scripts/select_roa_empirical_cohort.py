"""Select the frozen empirical cohort from ID-only authenticated ledgers."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from statistics import NormalDist
import subprocess
import sys
from scripts.replay_roa_original import REPO, install_boundary, write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path
from scripts.select_v2_fresh_ids import read_id_ledger
from src.arbitration.empirical_contract import DATASETS, select_fresh_ids

AUDIT_SHA="d368dc747ec8dbc6d2208e97e7bd2da8ecbebf1dcdda080f02d2317661c1ad47"
PANEL_SHA="4579e712f5ad513d7a9ca1229809432f766c05d5d9033b9053563c076629a619"


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root",type=Path,required=True)
    parser.add_argument("--replay-root",type=Path,required=True)
    args=parser.parse_args();root=args.project_root.resolve()
    out=REPO/"outputs/cas_q2/empirical_fresh_cohort_v1"
    if out.exists() or (root/"outputs/cas_q2/empirical_fresh_cohort_v1").exists():parser.error("Never overwrite or reselect a cohort")
    if subprocess.check_output(["git","status","--porcelain"],cwd=REPO,text=True).strip():parser.error("Commit complete executable sources")
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip()
    out.mkdir(parents=True,exist_ok=False)
    boundary=install_boundary(out)
    report=dict(status="FAIL",cas_q2_status="NOT READY",scientific_fit_calls=0,new_inference_calls=0,fresh_outcomes_read=0,question_ids_selected=0,source_commit=commit,input_files=[])
    def rec(p):return dict(path=str(p),size_bytes=p.stat().st_size,sha256=digest(p))
    def check(p,sha,size=None):
        if digest(p)!=sha or (size is not None and p.stat().st_size!=size):raise RuntimeError("INPUT_HASH:"+str(p))
        report["input_files"].append(rec(p));return p
    def load(p):return json.loads(p.read_text(encoding="utf-8"))
    try:
        panel=REPO/"outputs/cas_q2/empirical_fixed_panel_v1"
        check(panel/"SHA256_MANIFEST.json",PANEL_SHA)
        for e in load(panel/"SHA256_MANIFEST.json")["files"]:check(safe_file(panel,relative_path(e["path"])),e["sha256"],e["size_bytes"])
        assert load(panel/"INDEPENDENT_VALIDATION.json")["status"]=="PASS_FIXED_EMPIRICAL_PANEL_REPLAY"
        audit=args.replay_root/"p0_1_upstream_v2/UPSTREAM_PROVENANCE.json"
        check(audit,AUDIT_SHA)
        m=next(r["manifest"] for r in load(audit)["manifests"] if r["manifest"]["path"].endswith("cohort_freeze/SHA256_MANIFEST.json"))
        mp=check(safe_file(root,relative_path(m["path"])),m["sha256"],m["size_bytes"])
        e=next(e for e in load(mp)["files"] if e["path"].endswith("/COHORT_FREEZE.json"))
        cohort=load(check(safe_file(root,relative_path(e["path"])),e["sha256"],e["size_bytes"]))
        sources={}
        for d,e in cohort["source_id_ledgers"].items():
            q=check(safe_file(root,relative_path(e["path"])),e["sha256"],e["size_bytes"])
            sources[d]=set(read_id_ledger(q))
        oldpath=check(root/"outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl",cohort["frozen_forbidden_union_sha256"])
        e=cohort["selected_id_ledger"]
        openedpath=check(safe_file(root,relative_path(e["path"])),e["sha256"],e["size_bytes"])
        old,opened=set(read_id_ledger(oldpath)),set(read_id_ledger(openedpath))
        assert not old&opened and len(old)==14100 and len(opened)==4500
        forbidden=old|opened
        source_names=["scripts/select_roa_empirical_cohort.py","scripts/validate_roa_empirical_cohort.py","scripts/select_v2_fresh_ids.py","src/arbitration/empirical_contract.py","docs/cas_q2/EMPIRICAL_REPLICATION_PROTOCOL_V1.md","docs/cas_q2/EMPIRICAL_PANEL_ACCEPTANCE.md","docs/cas_q2/COST_AND_PRECISION_RESULTS.json"]
        report["source_files"]=[rec(REPO/n) for n in source_names]
        write_json(out/"PRESELECTION_FREEZE.json",dict(source_commit=commit,command=sys.argv,input_files=report["input_files"],source_files=report["source_files"],samples_per_dataset=2000,selection_prefix="cas-q2-empirical-fresh-v1|20260925"))
        chosen=select_fresh_ids(sources,forbidden)
        with (out/"SELECTED_IDS_PRIVATE.jsonl").open("x",encoding="utf-8",newline="\n") as f:
            for d in DATASETS:
                for identifier in chosen[d]:f.write(json.dumps(dict(dataset=d,sample_id=identifier),sort_keys=True)+"\n")
        precision=load(REPO/"docs/cas_q2/COST_AND_PRECISION_RESULTS.json")["precision"]
        z=NormalDist().inv_cdf(1-.05/(2*6));plan={}
        for comparison in precision["repetitions"][0]["comparisons"]:
            plan[comparison]={}
            for endpoint in ("em_gain","damage_rate"):
                sds=[r["comparisons"][comparison][endpoint]["bootstrap_sd_pp"] for r in precision["repetitions"]]
                projected=max(sds)*(4500/6000)**.5
                plan[comparison][endpoint]=dict(development_sds_pp=sds,worst_sd_pp=max(sds),projected_sd_pp=projected,
                    approximate_halfwidth_pp={"multiplier_1":z*projected,"multiplier_1_5":z*projected*1.5})
        write_json(out/"PRECISION_PLANNING.json",dict(questions=6000,z_bonferroni_six=z,comparisons=plan,
            interpretation="Normal approximation and variance-inflation sensitivity only; not achieved precision, final-model power or a guaranteed effect",sample_size_reason="Largest balanced multiple of 100 below authenticated 2105-question Hotpot availability; one bounded study, no significance-driven enlargement"))
        report.update(status="SELECTED_PENDING_INDEPENDENT",question_ids_selected=6000,expected_trace_count=18000,
                      inventory={d:dict(source=len(sources[d]),available=len(sources[d]-forbidden),selected=len(chosen[d])) for d in DATASETS},
                      selected_sha256=digest(out/"SELECTED_IDS_PRIVATE.jsonl"),excluded_questions=len(forbidden),overlap_with_exclusion=0,
                      sampling="Prospectively fixed deterministic hash selection, not claimed randomized probability sampling",replacements_allowed=False,
                      generation_authorized_by_this_receipt=False)
        assert not boundary["blocked"]
        for e in report["input_files"]+report["source_files"]:assert digest(Path(e["path"]))==e["sha256"]
    except Exception as exc:
        import traceback
        report.update(error=repr(exc),traceback=traceback.format_exc())
    write_json(out/"COHORT_RECEIPT.json",report)
    write_json(out/"EXECUTION_MANIFEST.json",dict(files=[dict(path=p.name,size_bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(out.iterdir()) if p.is_file()]))
    print(json.dumps({k:report[k] for k in ("status","question_ids_selected","fresh_outcomes_read")}))
    return 2 if report["status"]=="FAIL" else 0


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
