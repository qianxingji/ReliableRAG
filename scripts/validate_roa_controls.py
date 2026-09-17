"""Independent full reconstruction of frozen controls; no executor or fit imports."""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import sys
import traceback

from scripts.replay_roa_original import REPO, bind_original, install_boundary, load_original, write_json
from scripts.verify_roa_artifacts import SPEC_PATH, digest, verify

CONTROL = {"GBV_ONLY_R": [10], "HGB_GBV_R": [0,10]}
METHODS = ["ROA-FULL","ROA-NOGBV","HGB","GbV","V2",*CONTROL]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();root=args.project_root.resolve();out=args.output.resolve()
    if root==out or root in out.parents: parser.error("Output must be separate from original project")
    if (out/"INDEPENDENT_VALIDATION.json").exists(): parser.error("Validation receipt exists; do not replace")
    def load(rel):return json.loads((out/rel).read_text())
    spec=json.loads(SPEC_PATH.read_text())
    integrity=verify(root,root/spec["manifest_path"],spec)
    if integrity["integrity_status"]!="PASS":parser.error("Original integrity")
    c=bind_original(root,out)
    ind=load_original("independent");ind.METHODS=METHODS
    if any(n in sys.modules for n in ("design","learning","metrics","execute","src.arbitration.recovery_controls","scripts.run_roa_controls")):
        parser.error("Independent oracle import")
    import numpy as np
    from scipy.special import expit
    from threadpoolctl import threadpool_limits,threadpool_info
    threadpool_info()
    boundary=install_boundary(out)
    state=dict(status="FAIL",scientific_fit_calls=0,cas_q2_status="NOT READY",tolerance=1e-10)
    eq=ind.equal
    def check(entry,base=out):
        path=(base/entry["path"]).resolve();path.relative_to(base)
        eq(path.stat().st_size,entry["size_bytes"]);eq(digest(path),entry["sha256"])
    try:
        c.parents();c.frozen()
        freeze=load("PROTOCOL_FREEZE.json")
        for entry in freeze["files"]:check(entry,REPO)
        for record in load("INPUT_VERIFICATION.json")["sources"].values():c.check(record)
        eq(freeze["controls"],CONTROL)
        primary_seal=load("PRIMARY_OUTPUT_SEAL.json")
        for entry in primary_seal["files"]:check(entry)
        stage_seals={s:load("PRIMARY_ACTION_SEAL.json" if s=="primary" else "LODO_ACTION_SEAL.json") for s in ("primary","lodo")}
        for stage in stage_seals.values():
            eq(stage["heldout_metrics_computed"],False)
            for entry in stage["files"]:check(entry)
        split=load("SPLIT_MANIFEST.json");eq(split,c.load(c.OUT/"SPLIT_MANIFEST.json"))
        features=c.keyed(c.OUT/"NUMERIC_FEATURES_PRIVATE.jsonl");ys=c.keyed(c.SOURCES["outcomes"])
        comparator=c.keyed(c.OUT/"FROZEN_COMPARATORS_PRIVATE.jsonl")
        manifest=load("MODEL_FIT_MANIFEST.json")
        jobs={r["job_id"]:r for r in manifest["jobs"]};eq(len(jobs),56)
        calls={(r["job_id"],r["stage"]):r for r in manifest["calls"]};eq(len(calls),112)
        events=list(c.lines(out/"MODEL_FIT_CALLS_PRIVATE.jsonl"));eq(len(events),224)
        eq([r for r in events if r["event"]=="fit_completed"],manifest["calls"])
        eq(manifest["scientific_fit_calls"],112)
        schema=load("FEATURE_SCHEMA.json")
        original_schema=c.load(c.OUT/"FEATURE_SCHEMA.json")
        eq(schema["base"],original_schema["base"]);eq(schema["platt"],original_schema["platt"])
        contexts=[];rankings=[];prediction_count=0;model_count=0;metric_rows=[]
        all_action_expected=[];all_predictions_expected=[]
        primary=load("OUTER_RESULTS.json");allocation=load("ALLOCATION_SENSITIVITY.json");lodo=load("LODO_TRANSPORT.json")
        with threadpool_limits(1):
            for item in split["contexts"]:
                context=item["context"];parts=ind.split(set(features),context)
                eligible={p:sorted(k for k in keys if features[k]["eligible"]) for p,keys in parts.items()}
                groups={p:{(k[0],k[2]) for k in keys} for p,keys in parts.items()}
                c.require(groups["fit"].isdisjoint(groups["cal"]|groups["test"]) and groups["cal"].isdisjoint(groups["test"]),"GROUP_LEAKAGE")
                for p,kk in parts.items():
                    eq(item["partitions"][p],dict(N_all=len(kk),N_groups=len(groups[p]),N_eligible=len(eligible[p]),keys_sha256=c.kh(kk),eligible_keys_sha256=c.kh(eligible[p]),
                                                 recovery_target_counts=[sum(int(ys[k]["a0_em"]==0 and ys[k]["a1_em"]==1)==v for k in eligible[p]) for v in (0,1)]))
                cap=round(.05*len(parts["test"]));eq(cap,item["cap"])
                scores={};select={};second={}
                for name,indices in CONTROL.items():
                    jid=context["id"]+"_"+name;job=jobs[jid];check(job["model"]);check(job["predictions"])
                    eq(job["context"],context);eq(job["variant"],name)
                    model=load(job["model"]["path"]);eq(model["context"],context);eq(model["partitions"],item["partitions"])
                    eq(model["head"],"R");eq(model["variant"],name);eq(model["feature_dimension"],2*len(indices)+3)
                    names=[ind.FIELDS[i] for i in indices]
                    eq(schema["variants"][name],dict(numeric=names,dimension=2*len(indices)+3,feature_order=names+["missing."+n for n in names]+["retriever."+r for r in ind.RET]))
                    values={p:np.asarray([[np.nan if features[k]["numeric"][i] is None else features[k]["numeric"][i] for i in indices] for k in keys]) for p,keys in eligible.items()}
                    c.require(np.isfinite(values["fit"]).any(axis=0).all(),"ALL_MISSING_FIT")
                    median=np.nanmedian(values["fit"],axis=0);filled=np.where(np.isfinite(values["fit"]),values["fit"],median)
                    mean=filled.mean(axis=0);std=filled.std(axis=0);std[std==0]=1
                    eq(model["preprocessing"],dict(median=median.tolist(),mean=mean.tolist(),std=std.tolist()))
                    matrices={}
                    for p,arr in values.items():
                        missing=~np.isfinite(arr)
                        hot=np.asarray([[float(k[1]==r) for r in ind.RET] for k in eligible[p]])
                        matrices[p]=np.hstack(((np.where(missing,median,arr)-mean)/std,missing.astype(float),hot))
                        eq(model["design_hashes"][p],ind.ah(matrices[p]));eq(model["partition_key_hashes"][p],c.kh(eligible[p]))
                    coef=np.asarray(model["coef"]);logit=matrices["test"]@coef+model["intercept"]
                    prob=expit(logit*model["platt_slope"]+model["platt_intercept"])
                    predictions={k:dict(**c.keydict(k),logit_R=float(logit[i]),pR=float(prob[i])) for i,k in enumerate(eligible["test"])}
                    eq(c.keyed(out/job["predictions"]["path"]),predictions)
                    prediction_count+=len(predictions);model_count+=1
                    scores[name]={k:r["pR"] for k,r in predictions.items()}
                    select[name]=set(sorted(scores[name],key=lambda k:(-scores[name][k],k))[:cap])
                    previous=-math.inf;reversals=0;ties=0
                    order=sorted(predictions,key=lambda k:(predictions[k]["pR"],k))
                    for _,block in itertools.groupby(order,key=lambda k:predictions[k]["pR"]):
                        vv=[predictions[k]["logit_R"] for k in block];reversals+=int(min(vv)<previous);previous=max(previous,max(vv));ties+=int(len(vv)>1)
                    rankings.append(dict(job_id=jid,platt_slope=model["platt_slope"],strict_order_reversal_blocks=reversals,calibrated_tie_blocks=ties,ranking_unchanged_except_ties=reversals==0,calibrated_ranking_always_used=True))
                    for stage,p in (("base","fit"),("platt","cal")):
                        call=calls[jid,stage]
                        target=np.asarray([int(ys[k]["a0_em"]==0 and ys[k]["a1_em"]==1) for k in eligible[p]],dtype=np.uint8)
                        c.require(set(target)=={0,1},"FIT_CLASSES")
                        mat=matrices[p] if stage=="base" else (matrices[p]@coef+model["intercept"]).reshape(-1,1)
                        eq(call["design_sha256"],ind.ah(mat));eq(call["target_sha256"],hashlib.sha256(target.tobytes()).hexdigest())
                        eq(call["keys_sha256"],c.kh(eligible[p]));eq(call["sample_count"],len(target));eq(call["class_counts"],np.bincount(target,minlength=2).tolist())
                        eq(model["target_counts"][p],call["class_counts"]);eq(call["parameters"],schema["base" if stage=="base" else "platt"])
                        eq(call["warnings"],[]);eq(call["head"],"R");eq(call["variant"],name)
                        eq(call["iterations"],model["base_iterations" if stage=="base" else "platt_iterations"])
                        matched=[r for r in events if r["job_id"]==jid and r["stage"]==stage]
                        eq([r["event"] for r in matched],["fit_started","fit_completed"])
                        eq({k:v for k,v in matched[0].items() if k!="event"},{k:v for k,v in matched[1].items() if k not in ("event","completed_utc","iterations","warnings")})
                        c.require(freeze["frozen_utc"]<call["started_utc"]<=call["completed_utc"],"PRE_FIT_FREEZE")
                        if context["stage"]=="lodo":c.require(primary_seal["sealed_utc"]<call["started_utc"],"LODO_AFTER_PRIMARY")
                oldseal=c.load(c.OUT/"partitions"/context["id"]/"ACTION_SEAL.json")
                for name in METHODS[:5]:
                    if name in ("ROA-FULL","ROA-NOGBV"):
                        saved=c.keyed(c.OUT/"jobs"/(context["id"]+"_"+name)/"PREDICTIONS_PRIVATE.jsonl")
                        scores[name]={k:r["pR"] for k,r in saved.items()}
                    else:scores[name]={k:comparator[k][name] for k in eligible["test"]}
                    select[name]=set(sorted(scores[name],key=lambda k:(-scores[name][k],k))[:cap])
                    eq([list(k) for k in sorted(select[name])],oldseal["selected_keys"][name])
                for name in CONTROL:
                    second[name]=set()
                    for ds in ind.DS:
                        for retr in ind.RET:
                            n=sum(k[:2]==(ds,retr) for k in select["ROA-FULL"])
                            kk=[k for k in scores[name] if k[:2]==(ds,retr)]
                            selected=set(sorted(kk,key=lambda k:(-scores[name][k],k))[:n]);eq(len(selected),n);second[name]|=selected
                for name in METHODS[:5]:second[name]=select[name]
                for valueset in (select,second):
                    for keys in valueset.values():eq(len(keys),cap)
                seal=load("partitions/"+context["id"]+"/ACTION_SEAL.json")
                eq(seal["context"],context);eq(seal["cap"],cap);eq(seal["heldout_metrics_computed"],False)
                for field,ss in (("selected_keys",select),("secondary_selected_keys",second)):eq(seal[field],{m:[list(k) for k in sorted(v)] for m,v in ss.items()})
                result=load("partitions/"+context["id"]+"/RESULT.json")
                latest=max(calls[context["id"]+"_"+m,"platt"]["completed_utc"] for m in CONTROL)
                c.require(latest<=seal["sealed_utc"]<=stage_seals[context["stage"]]["sealed_utc"]<=result["metrics_computed_utc"],"ALL_ACTIONS_BEFORE_METRICS")
                eq(result["summary"],ind.summarize(parts["test"],select,ys,cap));eq(result["breakdown"],ind.groups(parts["test"],select,ys))
                eq(result["allocation_sensitivity"],ind.summarize(parts["test"],second,ys,cap));eq(result["allocation_breakdown"],ind.groups(parts["test"],second,ys))
                contexts.append(dict(context=context,select=select,second=second,cap=cap));metric_rows.append(result)
                for k in sorted(parts["test"]):
                    all_predictions_expected.append(dict(context_id=context["id"],**c.keydict(k),eligible=features[k]["eligible"],scores={m:scores[m].get(k) for m in METHODS}))
                    all_action_expected.append(dict(context_id=context["id"],**c.keydict(k),actions={m:k in select[m] for m in METHODS},secondary_actions={m:k in second[m] for m in METHODS}))
                print("INDEPENDENT_VERIFIED",context["id"],flush=True)
        eq(model_count,56);eq(prediction_count,38424);eq(len(contexts),28)
        eq(load("CALIBRATION_RANKING_CHECK.json"),dict(jobs=rankings))
        for name,expected in (("PREDICTIONS_PRIVATE.jsonl",all_predictions_expected),("ACTIONS_PRIVATE.jsonl",all_action_expected)):
            eq(len(expected),81000);eq(len({(r["context_id"],c.key(r)) for r in expected}),81000);eq(list(c.lines(out/name)),expected)
        eq(primary["folds"],[r for r in metric_rows if r["context"]["stage"]=="primary"])
        for i,seed in enumerate(ind.SEEDS):
            subset=[x for x in contexts if x["context"]["stage"]=="primary" and x["context"]["seed"]==seed]
            cap=sum(x["cap"] for x in subset)
            for label,target in (("select",primary),("second",allocation)):
                pooled={m:set().union(*(x[label][m] for x in subset)) for m in METHODS}
                eq(target["repetitions"][i],dict(seed=seed,pooled=ind.summarize(set(features),pooled,ys,cap),breakdown=ind.groups(set(features),pooled,ys)))
        eq(allocation["folds"],[dict(context=r["context"],summary=r["allocation_sensitivity"],breakdown=r["allocation_breakdown"]) for r in metric_rows if r["context"]["stage"]=="primary"])
        eq(lodo["transports"],[dict(heldout=r["context"]["heldout"],summary=r["summary"],breakdown=r["breakdown"],allocation_sensitivity=r["allocation_sensitivity"]) for r in metric_rows if r["context"]["stage"]=="lodo"])
        reps=primary["repetitions"]
        for m in METHODS:
            for metric,values in primary["statistics"][m].items():
                v=[r["pooled"]["methods"][m][metric] for r in reps]
                eq(values,dict(values=v,mean=statistics.mean(v),sample_std=statistics.stdev(v),median=statistics.median(v)))
        wins={m:sum(r["pooled"]["methods"]["ROA-FULL"]["net"]>r["pooled"]["methods"][m]["net"] and r["pooled"]["methods"]["ROA-FULL"]["damage"]<=r["pooled"]["methods"][m]["damage"] for r in reps) for m in CONTROL}
        med={m:statistics.median(r["pooled"]["comparisons"]["ROA-FULL"][m]["delta_em_pp"] for r in reps) for m in CONTROL}
        transport={m:{r["heldout"]:r["summary"]["comparisons"]["ROA-FULL"][m]["delta_em_pp"] for r in lodo["transports"]} for m in CONTROL}
        support=all(wins[m]>=4 and med[m]>0 and all(v>=-.10 for v in transport[m].values()) for m in CONTROL)
        eq(load("DEVELOPMENT_DECISION.json"),dict(decision="COMPLEXITY_SUPPORTED_FOR_CONFIRMATION" if support else "SIMPLER_CONTROL_COMPETITIVE_REVIEW_CONTRIBUTION",successes=wins,median_full_minus_control_em_pp=med,lodo_full_minus_control_em_pp=transport,development_only=True,final_candidate_selected=False,new_confirmation_started=False))
        receipt=load("SCIENTIFIC_EXECUTION_RECEIPT.json");eq(receipt["status"],"SCIENTIFIC_EXECUTION_COMPLETE_PENDING_INDEPENDENT");eq(receipt["scientific_fit_calls"],112);eq(receipt["started_calls"],112);eq(receipt["boundary"]["blocked"],[])
        c.parents();c.frozen()
        for record in c.load(root/spec["manifest_path"])["files"]:c.check(record)
        state.update(status="PASS",checks=ind.CHECKS,max_numeric_error=ind.MAX_ERROR,contexts=28,model_bundles=56,prediction_rows=38424,aggregate_prediction_rows=81000,aggregate_action_rows=81000,
                     action_membership_differences=0,historical_control_fit_calls_verified=112,no_executor_or_fitter_import=True,original_artifacts_unchanged=True,validated_utc=c.now())
    except Exception as exc:state.update(error=repr(exc),traceback=traceback.format_exc())
    write_json(out/"INDEPENDENT_VALIDATION.json",state)
    if state["status"]=="PASS":
        payload=[dict(path=p.relative_to(out).as_posix(),sha256=digest(p),size_bytes=p.stat().st_size) for p in sorted(out.rglob("*")) if p.is_file()]
        write_json(out/"SEAL.json",dict(status="PASS",sealed_utc=c.now(),files=payload,scientific_fit_calls=112,independent_fit_calls=0,decision=load("DEVELOPMENT_DECISION.json")["decision"],hard_stop=True,cas_q2_status="NOT READY"))
        payload.append(dict(path="SEAL.json",sha256=digest(out/"SEAL.json"),size_bytes=(out/"SEAL.json").stat().st_size))
        write_json(out/"SHA256_MANIFEST.json",dict(status="PASS",files=sorted(payload,key=lambda x:x["path"]),payload_files=len(payload),excludes_only="SHA256_MANIFEST.json",exact_recursive_coverage=True,hard_stop=True))
    print(json.dumps({k:v for k,v in state.items() if k in ("status","error","checks","max_numeric_error")}))
    return 0 if state["status"]=="PASS" else 2


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
