"""Independent ID-only cohort reconstruction, with no selector-module import."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import NormalDist
import sys
from scripts.replay_roa_original import REPO, install_boundary, write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path
from scripts.select_v2_fresh_ids import read_id_ledger


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root",type=Path,required=True)
    args=p.parse_args();root=args.project_root.resolve()
    out=REPO/"outputs/cas_q2/empirical_fresh_cohort_v1"
    if (out/"INDEPENDENT_VALIDATION.json").exists():p.error("Already validated; no duplicate run")
    install_boundary(out)
    result=dict(status="FAIL",cas_q2_status="NOT READY",scientific_fit_calls=0,new_inference_calls=0,fresh_outcomes_read=0,checks=0,no_selector_import=True)
    def load(p):return json.loads(p.read_text(encoding="utf-8"))
    def eq(a,b):
        result["checks"]+=1
        if a!=b:raise RuntimeError("COHORT_INDEPENDENT_MISMATCH")
    def close(a,b):
        result["checks"]+=1
        if abs(a-b)>1e-10:raise RuntimeError("PLANNING_NUMERIC_MISMATCH")
    try:
        manifest=load(out/"EXECUTION_MANIFEST.json")
        eq({q.name for q in out.iterdir() if q.is_file()},{e["path"] for e in manifest["files"]}|{"EXECUTION_MANIFEST.json"})
        for e in manifest["files"]:
            q=safe_file(out,relative_path(e["path"]));eq(digest(q),e["sha256"]);eq(q.stat().st_size,e["size_bytes"])
        freeze=load(out/"PRESELECTION_FREEZE.json")
        for e in freeze["source_files"]+freeze["input_files"]:
            q=Path(e["path"]);eq(digest(q),e["sha256"]);eq(q.stat().st_size,e["size_bytes"])
        cohort=load(root/"outputs/daa_v2_fresh_v1/cohort_freeze/COHORT_FREEZE.json")
        old=set(read_id_ledger(root/"outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl"))
        opened=set(read_id_ledger(root/cohort["selected_id_ledger"]["path"]))
        eq(old&opened,set());eq(len(old),14100);eq(len(opened),4500)
        forbidden=old|opened;actual=read_id_ledger(out/"SELECTED_IDS_PRIVATE.jsonl")
        eq(len(actual),6000);eq(len(set(actual)),6000);eq(set(actual)&forbidden,set())
        datasets=("hotpotqa","2wikimultihopqa","musique")
        eq(Counter(d for d,i in actual),Counter({d:2000 for d in datasets}))
        expected=[];inventory={}
        for d in datasets:
            source=set(read_id_ledger(root/cohort["source_id_ledgers"][d]["path"]))
            eq({x[0] for x in source},{d})
            available=source-forbidden
            ordered=sorted(available,key=lambda k:(hashlib.sha256(("cas-q2-empirical-fresh-v1|20260925|"+k[0]+"|"+k[1]).encode("utf-8")).hexdigest(),k[1]))
            expected.extend(ordered[:2000]);inventory[d]=dict(source=len(source),available=len(available),selected=2000)
        eq(actual,expected)
        receipt=load(out/"COHORT_RECEIPT.json")
        eq(receipt["inventory"],inventory);eq(receipt["question_ids_selected"],6000);eq(receipt["selected_sha256"],digest(out/"SELECTED_IDS_PRIVATE.jsonl"))
        eq(receipt["status"],"SELECTED_PENDING_INDEPENDENT");eq(receipt["overlap_with_exclusion"],0);eq(receipt["excluded_questions"],18600)
        plan=load(out/"PRECISION_PLANNING.json")
        precision=load(REPO/"docs/cas_q2/COST_AND_PRECISION_RESULTS.json")["precision"]
        z=NormalDist().inv_cdf(1-.05/12);close(plan["z_bonferroni_six"],z)
        for comparison,values in plan["comparisons"].items():
            for endpoint,value in values.items():
                sds=[r["comparisons"][comparison][endpoint]["bootstrap_sd_pp"] for r in precision["repetitions"]]
                eq(value["development_sds_pp"],sds);close(value["worst_sd_pp"],max(sds))
                projected=max(sds)*(4500/6000)**.5;close(value["projected_sd_pp"],projected)
                close(value["approximate_halfwidth_pp"]["multiplier_1"],z*projected)
                close(value["approximate_halfwidth_pp"]["multiplier_1_5"],z*projected*1.5)
        result.update(status="PASS_ID_ONLY_EMPIRICAL_COHORT",selected_questions=6000,expected_traces=18000,excluded_questions=18600,
                      overlap_with_known_exclusions=0,exact_order_reconstruction=True,precision_planning_reconciled=True,
                      novel_method_candidate_cleared=False,stage_C_engineering_freeze_required=True,
                      limitations="ID-level known-use exclusion only; not text/semantic deduplication, pretraining decontamination or random-probability sampling")
    except Exception as exc:
        import traceback
        result.update(error=repr(exc),traceback=traceback.format_exc())
    write_json(out/"INDEPENDENT_VALIDATION.json",result)
    if result["status"]=="FAIL":print(json.dumps(result));return 2
    write_json(out/"SEAL.json",dict(status="PASS",selected_id_sha256=digest(out/"SELECTED_IDS_PRIVATE.jsonl"),independent_sha256=digest(out/"INDEPENDENT_VALIDATION.json"),cas_q2_status="NOT READY",fresh_outcomes_read=0))
    write_json(out/"SHA256_MANIFEST.json",dict(files=[dict(path=q.name,size_bytes=q.stat().st_size,sha256=digest(q)) for q in sorted(out.iterdir()) if q.is_file()]))
    print(json.dumps(result));return 0


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
