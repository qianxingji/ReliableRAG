"""Independent saved-parameter audit; imports no empirical executor/fitter."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.special import expit
from threadpoolctl import threadpool_info, threadpool_limits
from scripts.replay_roa_original import REPO, install_boundary, write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path

FIELDS = {"ROA-FULL":list(range(11)),"ROA-NOGBV":list(range(10)),"HGB_GBV_R":[0,10],"HGB_ONLY_R":[0],"GBV_ONLY_R":[10]}
RETRIEVERS = ("bm25","dense","hybrid")


def rows(p):
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():yield json.loads(line)


def key(r):return tuple(r[k] for k in ("dataset","retriever","sample_id"))
def kh(keys):
    return hashlib.sha256("".join(json.dumps(list(k),ensure_ascii=False,separators=(",",":"))+"\n" for k in sorted(keys)).encode()).hexdigest()
def ah(v):return hashlib.sha256(np.asarray(v,dtype="<f8").tobytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root",type=Path,required=True)
    args=parser.parse_args();root=args.project_root.resolve()
    out=REPO/"outputs/cas_q2/empirical_fixed_panel_v1"
    if (out/"INDEPENDENT_VALIDATION.json").exists() or (out/"SHA256_MANIFEST.json").exists():parser.error("Already independently sealed")
    threadpool_info()
    boundary=install_boundary(out)
    report=dict(status="FAIL",scientific_fit_calls=0,new_inference_calls=0,cas_q2_status="NOT READY",checks=0,max_numeric_error=0.0,probe_prediction_rows=0,no_executor_or_fitter_import=True)
    def eq(a,b):
        report["checks"]+=1
        if a!=b:raise RuntimeError("INDEPENDENT_VALUE_MISMATCH:"+repr((a,b))[:250])
    def close(a,b):
        aa,bb=np.asarray(a),np.asarray(b)
        eq(aa.shape,bb.shape)
        if not np.isfinite(aa).all() or not np.isfinite(bb).all():raise RuntimeError("NONFINITE")
        error=float(np.max(np.abs(aa-bb))) if aa.size else 0.0
        report["checks"]+=int(aa.size)
        report["max_numeric_error"]=max(error,report["max_numeric_error"])
        if error>1e-10:raise RuntimeError("NUMERIC_TOLERANCE")
    try:
        manifest=json.loads((out/"EXECUTION_MANIFEST.json").read_text())
        eq({p.name for p in out.iterdir() if p.is_file()},{e["path"] for e in manifest["files"]}|{"EXECUTION_MANIFEST.json"})
        for e in manifest["files"]:
            p=safe_file(out,relative_path(e["path"]));eq(p.stat().st_size,e["size_bytes"]);eq(digest(p),e["sha256"])
        frozen=json.loads((out/"EXECUTABLE_FREEZE.json").read_text())
        for e in frozen["source_files"]+frozen["input_files"]:
            p=Path(e["path"]);eq(digest(p),e["sha256"]);eq(p.stat().st_size,e["size_bytes"])
        eq(frozen["field_indices"],FIELDS)
        params=dict(C=1.0,solver="lbfgs",class_weight=None,max_iter=5000,penalty="l2",tol=1e-4,fit_intercept=True,random_state=None)
        platt_params=dict(params,C=1e6,max_iter=2000)
        eq(frozen["base_parameters"],params);eq(frozen["platt_parameters"],platt_params)
        feature_file=root/"outputs/daa_v3_development/recovery_only_isolation_v1/NUMERIC_FEATURES_PRIVATE.jsonl"
        outcome_file=root/"outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl"
        features={};ys={}
        for path,target in ((feature_file,features),(outcome_file,ys)):
            for row in rows(path):
                if key(row) in target:raise RuntimeError("DUPLICATE_INPUT")
                target[key(row)]=row
        eq(set(features),set(ys));eq(len(features),13500)
        groups={(k[0],k[2]) for k in features};eq(len(groups),4500)
        calgroups=set()
        for dataset in ("hotpotqa","2wikimultihopqa","musique"):
            gg=sorted([g for g in groups if g[0]==dataset],key=lambda g:(hashlib.sha256(("cas-q2-empirical-fit-v1|20260924|"+g[0]+"|"+g[1]).encode()).hexdigest(),g[1]))
            eq(len(gg),1500);calgroups.update(gg[:300])
        for d,i in groups:eq({(d,r,i) for r in RETRIEVERS}<=set(features),True)
        cal={k for k in features if (k[0],k[2]) in calgroups}
        parts={"fit":set(features)-cal,"cal":cal,"probe":set(features)}
        eq(parts["fit"]&parts["cal"],set());eq(parts["probe"],parts["fit"]|parts["cal"])
        expected_groups={(d,i):("cal" if (d,i) in calgroups else "fit") for d,i in groups}
        actual_groups={}
        for r in rows(out/"TRAINING_GROUPS_PRIVATE.jsonl"):
            eq((r["dataset"],r["sample_id"]) in actual_groups,False);actual_groups[(r["dataset"],r["sample_id"])]=r["role"]
        eq(actual_groups,expected_groups)
        split=json.loads((out/"SPLIT_MANIFEST.json").read_text())
        for role,kk in parts.items():
            eq(split[role],dict(N_all=len(kk),N_groups=len({(k[0],k[2]) for k in kk}),keys_sha256=kh(kk),N_eligible=sum(features[k]["eligible"] for k in kk)))
        receipt=json.loads((out/"FIT_RECEIPT.json").read_text())
        eq(receipt["scientific_fit_calls"],10);eq(receipt["scientific_fit_started_calls"],10);eq(receipt["status"],"FIT_COMPLETE_PENDING_INDEPENDENT")
        models=json.loads((out/"MODELS.json").read_text());eq(set(models),set(FIELDS))
        calls=list(rows(out/"FIT_EVENTS_PRIVATE.jsonl"))
        eq(Counter((r["variant"],r["stage"],r["event"]) for r in calls),Counter((v,s,e) for v in FIELDS for s in ("base","platt") for e in ("fit_started","fit_completed")))
        predictions={}
        for row in rows(out/"PROBE_PREDICTIONS_PRIVATE.jsonl"):
            token=(row["policy"],key(row));eq(token in predictions,False);predictions[token]=row
        eq(len(predictions),16010)
        kk={role:sorted(k for k in keys if features[k]["eligible"]) for role,keys in parts.items()}
        with threadpool_limits(limits=1):
            for name,indices in FIELDS.items():
                model=models[name];eq(model["numeric_indices"],indices);eq(model["feature_dimension"],2*len(indices)+3)
                x={p:np.array([[np.nan if features[k]["numeric"][i] is None else features[k]["numeric"][i] for i in indices] for k in keys],dtype=float) for p,keys in kk.items()}
                median=np.nanmedian(x["fit"],axis=0);filled=np.where(np.isfinite(x["fit"]),x["fit"],median)
                mean=filled.mean(axis=0);std=filled.std(axis=0,ddof=0);std=np.where(std==0,1,std)
                for label,value in (("median",median),("mean",mean),("std",std)):close(model["preprocessing"][label],value)
                xx={p:np.column_stack(((np.where(np.isfinite(v),v,median)-mean)/std,(~np.isfinite(v)).astype(float),np.array([[float(k[1]==r) for r in RETRIEVERS] for k in kk[p]]))) for p,v in x.items()}
                yy={p:np.array([int(ys[k]["a0_em"]==0 and ys[k]["a1_em"]==1) for k in kk[p]],dtype=np.uint8) for p in ("fit","cal")}
                for p in yy:eq(set(yy[p].tolist()),{0,1})
                for p in parts:eq(model["partition_key_hashes"][p],kh(kk[p]));eq(model["design_hashes"][p],ah(xx[p]))
                for p in yy:eq(model["target_counts"][p],np.bincount(yy[p],minlength=2).tolist())
                coef=np.array(model["coef"])
                cal_logits=xx["cal"]@coef+model["intercept"]
                for stage,role,design,expected_parameters in (("base","fit",xx["fit"],params),("platt","cal",cal_logits.reshape(-1,1),platt_params)):
                    target_hash=hashlib.sha256(yy[role].tobytes()).hexdigest()
                    for event in ("fit_started","fit_completed"):
                        call=next(r for r in calls if (r["variant"],r["stage"],r["event"])==(name,stage,event))
                        eq(call["design_sha256"],ah(design));eq(call["target_sha256"],target_hash);eq(call["keys_sha256"],kh(kk[role]))
                        eq(call["parameters"],expected_parameters);eq(call["sample_count"],len(yy[role]));eq(call["class_counts"],np.bincount(yy[role],minlength=2).tolist())
                        if event=="fit_completed":eq(call["iterations"],model["base_iterations" if stage=="base" else "platt_iterations"])
                raw=xx["probe"]@coef+model["intercept"];prob=expit(raw*model["platt_slope"]+model["platt_intercept"])
                close(raw,[predictions[(name,k)]["logit_R"] for k in kk["probe"]])
                close(prob,[predictions[(name,k)]["pR"] for k in kk["probe"]])
                report["probe_prediction_rows"]+=len(raw)
        eq(boundary["blocked"],[])
        for e in frozen["input_files"]:eq(digest(Path(e["path"])),e["sha256"])
        report.update(status="PASS_FIXED_EMPIRICAL_PANEL_REPLAY",model_bundles=5,scientific_fit_calls_verified=10,
                      total_takeover_scientific_fit_calls=178,fit_questions=3600,calibration_questions=900,
                      all_probe_predictions_replayed=True,probe_is_held_out=False,quality_metrics_computed=False,
                      final_novel_method_candidate_cleared=False,fresh_ids_allowed_under_protocol_stage_B=True)
    except Exception as exc:
        import traceback
        report.update(error=repr(exc),traceback=traceback.format_exc())
    write_json(out/"INDEPENDENT_VALIDATION.json",report)
    if report["status"]=="FAIL":
        print(json.dumps(report));return 2
    write_json(out/"SEAL.json",dict(status="PASS",independent_sha256=digest(out/"INDEPENDENT_VALIDATION.json"),model_sha256=digest(out/"MODELS.json"),protocol_role="Fixed empirical replication panel; not novel method success",cas_q2_status="NOT READY"))
    write_json(out/"SHA256_MANIFEST.json",dict(files=[dict(path=p.name,sha256=digest(p),size_bytes=p.stat().st_size) for p in sorted(out.iterdir()) if p.is_file()]))
    print(json.dumps(report));return 0


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
