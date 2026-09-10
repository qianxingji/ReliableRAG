"""Execute the one prospectively frozen HGB-only attribution control.

All original artifacts remain read-only. All primary actions, including the
secondary allocation sensitivity, are sealed before held-out metrics; primary
outputs seal before LODO fits. Single use; failures are never erased or retried.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import statistics
import subprocess
import sys
import traceback

from scripts.replay_roa_original import REPO, bind_original, install_boundary, load_original, write_json
from scripts.cas_q2_seals import verify_controls
from scripts.verify_roa_artifacts import SPEC_PATH, digest, verify

CONTROL_FIELDS = {"HGB_ONLY_R": [0]}
REFERENCES = ["ROA-FULL", "ROA-NOGBV", "HGB", "GbV", "V2", "GBV_ONLY_R", "HGB_GBV_R"]
PREVIOUS = REPO / "outputs/cas_q2/supervision_matched_controls_v1"
METHODS = REFERENCES + list(CONTROL_FIELDS)
NAMESPACE = "outputs/cas_q2/hgb_only_attribution_v1"


def attribution(repetitions, transports):
    successes, medians, lodo = {}, {}, {}
    for m in ("HGB_ONLY_R", "GBV_ONLY_R"):
        successes[m] = sum(r["pooled"]["methods"]["HGB_GBV_R"]["net"] > r["pooled"]["methods"][m]["net"] and
                           r["pooled"]["methods"]["HGB_GBV_R"]["damage"] <= r["pooled"]["methods"][m]["damage"] for r in repetitions)
        medians[m] = statistics.median(r["pooled"]["comparisons"]["HGB_GBV_R"][m]["delta_em_pp"] for r in repetitions)
        lodo[m] = {r["heldout"]:r["summary"]["comparisons"]["HGB_GBV_R"][m]["delta_em_pp"] for r in transports}
    support = all(successes[m] >= 4 and medians[m] > 0 and min(lodo[m].values()) >= -.10 for m in ("HGB_ONLY_R", "GBV_ONLY_R"))
    return dict(decision="TWO_SIGNAL_INCREMENT_SUPPORTED_FOR_DESIGN_REVIEW" if support else "TWO_SIGNAL_INCREMENT_NOT_ESTABLISHED",
                successes=successes, median_fusion_minus_single_em_pp=medians, lodo_fusion_minus_single_em_pp=lodo,
                development_only=True, final_candidate_selected=False, new_confirmation_started=False)


def repetition_stats(reps):
    return {m:{v:{"values":[r["pooled"]["methods"][m][v] for r in reps],
                     "mean":statistics.mean(r["pooled"]["methods"][m][v] for r in reps),
                     "sample_std":statistics.stdev(r["pooled"]["methods"][m][v] for r in reps),
                     "median":statistics.median(r["pooled"]["methods"][m][v] for r in reps)}
               for v in ("actions","recovery","damage","neutral","net","delta_em_pp","delta_f1_pp")} for m in METHODS}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", required=True, type=Path)
    p.add_argument("--replay-root", required=True, type=Path, help="Client outputs containing accepted P0-1 reports")
    args = p.parse_args()
    root, out = args.project_root.resolve(), (REPO / NAMESPACE).resolve()
    if out.exists() or (root / NAMESPACE).exists(): p.error("Control namespace already exists; reconcile, never overwrite")
    commit = subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip()
    dirty = subprocess.check_output(["git","status","--porcelain"],cwd=REPO,text=True)
    if dirty.strip(): p.error("Commit all executable sources before the single-use freeze")
    spec = json.loads(SPEC_PATH.read_text())
    integrity = verify(root, root / spec["manifest_path"],spec)
    if integrity["integrity_status"] != "PASS": p.error("Original integrity failed")
    accepted = []
    for rel in ("p0_1_primary_replay_v1/REPLAY_VALIDATION.json","p0_1_independent_replay_v1/REPLAY_VALIDATION.json"):
        path = args.replay_root / rel
        data = json.loads(path.read_text())
        if data["status"] != "PASS" or data["scientific_fit_calls"] != 0: p.error("Replay gate failed")
        accepted.append(dict(path=str(path.resolve()),sha256=digest(path)))
    upstream_path = args.replay_root / "p0_1_upstream_v2/UPSTREAM_PROVENANCE.json"
    upstream = json.loads(upstream_path.read_text())
    if upstream["status"] != "AUTHENTICATED_LOCAL_LINEAGE_WITH_HISTORICAL_RECEIPT_LIMITATION": p.error("Provenance gate failed")
    if any(x["training_scope"]["all_development_overlap_with_ROA"] for x in upstream["learned_inputs"]): p.error("Provenance overlap")
    accepted.append(dict(path=str(upstream_path.resolve()),sha256=digest(upstream_path)))
    previous_receipt = verify_controls(PREVIOUS)
    c = bind_original(root,out)
    # Restore scientific writer destinations only for this new experiment.
    def destination(name):
        path = (out / name).resolve(); path.relative_to(out)
        path.parent.mkdir(parents=True,exist_ok=True)
        return path
    c.dest = destination
    c.write = lambda name,value: write_json(destination(name),value)
    def linewrite(name,rows):
        with destination(name).open("x",encoding="utf-8",newline="\n") as f:
            for row in rows: f.write(json.dumps(row,sort_keys=True,allow_nan=False)+"\n")
    def rec(path): return dict(path=path.relative_to(out).as_posix(),sha256=digest(path),size_bytes=path.stat().st_size)
    from threadpoolctl import threadpool_info,threadpool_limits
    import numpy
    import scipy
    d = load_original("design")
    metric = load_original("metrics")
    metric.METHODS = METHODS
    metric.VARIANTS = ["ROA-FULL", "HGB_GBV_R"]
    from src.arbitration.recovery_hgb_control import fit_control
    threadpool_info()
    parents = c.parents(); c.frozen()
    out.mkdir(parents=True,exist_ok=False)
    boundary = install_boundary(out)
    state = dict(status="FAIL",scientific_fit_calls=0,started_calls=0,cas_q2_status="NOT READY")
    try:
        allowed = {r["path"] for r in parents["files"]} | {x["path"] for x in c.frozen()["files"]}
        source_files = ["scripts/run_roa_hgb_only.py","scripts/validate_roa_hgb_only.py","scripts/replay_roa_original.py","src/arbitration/recovery_hgb_control.py",
                        "docs/cas_q2/HGB_ONLY_PROTOCOL.md","scripts/cas_q2_seals.py","docs/cas_q2/P0_1_CLIENT_ACCEPTANCE.md"]
        source_files += ["src/arbitration/roa_original/"+x+".py" for x in ("controls","design","learning","metrics","independent")]
        freeze = dict(frozen_utc=c.now(),commit=commit,command=sys.argv,
                      files=[dict(path=x,sha256=digest(REPO/x),size_bytes=(REPO/x).stat().st_size) for x in source_files],
                      versions={n:importlib.metadata.version(n) for n in ("numpy","scipy","scikit-learn","threadpoolctl")},
                      executable=dict(path=sys.executable,sha256=digest(Path(sys.executable))),threads=1,
                      accepted_replay=accepted,original_manifest_sha256=spec["manifest_sha256"],
                      expected_model_bundles=28,expected_fit_calls=56,scientific_fit_calls_before_freeze=0,
                      controls=CONTROL_FIELDS,synthetic_fit_calls=0,previous_control_manifest=previous_receipt)
        c.write("PROTOCOL_FREEZE.json",freeze)
        c.write("INPUT_VERIFICATION.json",dict(integrity=integrity,parent_manifests=parents["manifests"],sources={n:c.rec(p) for n,p in c.SOURCES.items()},
                                                provenance=accepted[-1],client_acceptance_sha256=digest(REPO/"docs/cas_q2/P0_1_CLIENT_ACCEPTANCE.md")))
        features = c.keyed(c.OUT / "NUMERIC_FEATURES_PRIVATE.jsonl")
        comparison = c.keyed(c.OUT / "FROZEN_COMPARATORS_PRIVATE.jsonl")
        ys = c.keyed(c.SOURCES["outcomes"])
        split = c.load(c.OUT / "SPLIT_MANIFEST.json")
        c.write("SPLIT_MANIFEST.json",split)
        c.write("FEATURE_SCHEMA.json",dict(variants={m:dict(numeric=[d.NUMERIC[i] for i in ix],dimension=2*len(ix)+3,
                                                          feature_order=[d.NUMERIC[i] for i in ix]+["missing."+d.NUMERIC[i] for i in ix]+["retriever."+r for r in d.RETRIEVERS]) for m,ix in CONTROL_FIELDS.items()},
                                                  base=d.BASE,platt=d.PLATT,preprocessing="unchanged original ROA recipe; all-missing fit column fails; zero std becomes 1",no_dataset_predictor=True))
        projected = {m:{k:dict(row,numeric=[row["numeric"][i] for i in ix]) for k,row in features.items()} for m,ix in CONTROL_FIELDS.items()}
        jobs,calls,rankings,contexts = [],[],[],[]
        c.write("SCIENTIFIC_EXECUTION_STARTED.json",dict(started_utc=c.now(),expected_calls=56))
        with destination("MODEL_FIT_CALLS_PRIVATE.jsonl").open("x",encoding="utf-8",newline="\n") as journal, threadpool_limits(1):
            def event(value):
                journal.write(json.dumps(value,sort_keys=True,allow_nan=False)+"\n");journal.flush()
                if value["event"] == "fit_started": state["started_calls"] += 1
                if value["event"] == "fit_completed": calls.append(value);state["scientific_fit_calls"] += 1
            stage_results = {}
            for stage in ("primary","lodo"):
                stage_contexts = []
                for item in split["contexts"]:
                    context = item["context"]
                    if context["stage"] != stage: continue
                    parts = d.partition(set(features),context)
                    if d.receipt(parts,features,ys) != item["partitions"]: raise RuntimeError("SPLIT_RECEIPT")
                    eligible = sorted(k for k in parts["test"] if features[k]["eligible"])
                    train_y = {k:ys[k] for k in parts["fit"]|parts["cal"]}
                    scores, selections, secondary = {}, {}, {}
                    for m in CONTROL_FIELDS:
                        jid = context["id"]+"_"+m
                        model,pred,ranking = fit_control(projected[m],train_y,parts,m,jid,event)
                        model.update(context=context,partitions=item["partitions"])
                        c.write("jobs/"+jid+"/MODEL.json",model)
                        linewrite("jobs/"+jid+"/PREDICTIONS_PRIVATE.jsonl",[dict(**c.keydict(k),**pred[k]) for k in sorted(pred)])
                        scores[m] = {k:v["pR"] for k,v in pred.items()}
                        selections[m] = d.top(scores[m],item["cap"])
                        jobs.append(dict(job_id=jid,variant=m,context=context,model=rec(out/"jobs"/jid/"MODEL.json"),predictions=rec(out/"jobs"/jid/"PREDICTIONS_PRIVATE.jsonl")))
                        rankings.append(dict(job_id=jid,**ranking))
                    oldseal = c.load(PREVIOUS/"partitions"/context["id"]/"ACTION_SEAL.json")
                    for m in REFERENCES:
                        selections[m] = set(map(tuple,oldseal["selected_keys"][m]))
                        if m in ("ROA-FULL","ROA-NOGBV","GBV_ONLY_R","HGB_GBV_R"):
                            scores[m] = {k:v["pR"] for k,v in c.keyed((PREVIOUS if m in ("GBV_ONLY_R","HGB_GBV_R") else c.OUT)/"jobs"/(context["id"]+"_"+m)/"PREDICTIONS_PRIVATE.jsonl").items()}
                        else: scores[m] = {k:comparison[k][m] for k in eligible}
                        if d.top(scores[m],item["cap"]) != selections[m]: raise RuntimeError("REFERENCE_ACTION_REPLAY")
                    if any(len(s)!=item["cap"] for s in selections.values()): raise RuntimeError("SAME_CAP")
                    for m in CONTROL_FIELDS:
                        secondary[m] = set()
                        for ds in d.HELDOUT:
                            for retriever in d.RETRIEVERS:
                                cap = sum(k[:2]==(ds,retriever) for k in selections["HGB_GBV_R"])
                                secondary[m] |= d.top({k:v for k,v in scores[m].items() if k[:2]==(ds,retriever)},cap)
                    secondary.update({m:selections[m] for m in REFERENCES})
                    seal = dict(context=context,cap=item["cap"],sealed_utc=c.now(),heldout_metrics_computed=False,
                                selected_keys={m:[list(k) for k in sorted(v)] for m,v in selections.items()},
                                secondary_selected_keys={m:[list(k) for k in sorted(v)] for m,v in secondary.items()})
                    c.write("partitions/"+context["id"]+"/ACTION_SEAL.json",seal)
                    record = dict(context=context,parts=parts,cap=item["cap"],selections=selections,secondary=secondary,scores=scores)
                    contexts.append(record);stage_contexts.append(record)
                    print("FIT_AND_ACTION_SEAL",context["id"],"calls",len(calls),flush=True)
                # No held-out metric has been calculated until every action in this stage is sealed.
                c.write("PRIMARY_ACTION_SEAL.json" if stage=="primary" else "LODO_ACTION_SEAL.json",dict(sealed_utc=c.now(),heldout_metrics_computed=False,
                        files=[rec(out/"partitions"/x["context"]["id"]/"ACTION_SEAL.json") for x in stage_contexts],scientific_fit_calls=len(calls)))
                results = []
                for x in stage_contexts:
                    ss = metric.summary(x["parts"]["test"],x["selections"],ys,x["cap"])
                    second = metric.summary(x["parts"]["test"],x["secondary"],ys,x["cap"])
                    result = dict(context=x["context"],metrics_computed_utc=c.now(),summary=ss,
                                  breakdown=metric.breakdown(x["parts"]["test"],x["selections"],ys),
                                  allocation_sensitivity=second,allocation_breakdown=metric.breakdown(x["parts"]["test"],x["secondary"],ys))
                    c.write("partitions/"+x["context"]["id"]+"/RESULT.json",result);results.append(result)
                if stage=="primary":
                    reps,secondary_reps = [],[]
                    for seed in d.SEEDS:
                        subset = [x for x in stage_contexts if x["context"]["seed"]==seed]
                        cap = sum(x["cap"] for x in subset)
                        for selector,target in (("selections",reps),("secondary",secondary_reps)):
                            actions = {m:set().union(*(x[selector][m] for x in subset)) for m in METHODS}
                            if any(len(v)!=cap for v in actions.values()): raise RuntimeError("POOLED_ACTION_DUPLICATE")
                            target.append(dict(seed=seed,pooled=metric.summary(set(features),actions,ys,cap),breakdown=metric.breakdown(set(features),actions,ys)))
                    c.write("OUTER_RESULTS.json",dict(repetitions=reps,folds=results,statistics=repetition_stats(reps),std_interpretation="partition sensitivity; not a new-data confidence interval"))
                    c.write("ALLOCATION_SENSITIVITY.json",dict(repetitions=secondary_reps,folds=[dict(context=r["context"],summary=r["allocation_sensitivity"],breakdown=r["allocation_breakdown"]) for r in results],label="SECONDARY_ONLY; exact HGB_GBV_R stratum counts per partition"))
                    c.write("PRIMARY_OUTPUT_SEAL.json",dict(sealed_utc=c.now(),LODO_fit_calls=0,files=[rec(out/n) for n in ("OUTER_RESULTS.json","ALLOCATION_SENSITIVITY.json","PRIMARY_ACTION_SEAL.json")]))
                else:
                    transports = [dict(heldout=r["context"]["heldout"],summary=r["summary"],breakdown=r["breakdown"],allocation_sensitivity=r["allocation_sensitivity"]) for r in results]
                    c.write("LODO_TRANSPORT.json",dict(transports=transports,seed=d.LODO_SEED,scope="ROA head only; upstream historical models saw all three datasets on other IDs"))
        if len(jobs)!=28 or len(calls)!=56 or state["started_calls"]!=56: raise RuntimeError("FIT_COUNT")
        c.write("MODEL_FIT_MANIFEST.json",dict(jobs=jobs,calls=calls,base_fit_calls=28,platt_fit_calls=28,scientific_fit_calls=56))
        c.write("CALIBRATION_RANKING_CHECK.json",dict(jobs=rankings))
        linewrite("PREDICTIONS_PRIVATE.jsonl",(dict(context_id=x["context"]["id"],**c.keydict(k),eligible=features[k]["eligible"],scores={m:x["scores"][m].get(k) for m in METHODS}) for x in contexts for k in sorted(x["parts"]["test"])))
        linewrite("ACTIONS_PRIVATE.jsonl",(dict(context_id=x["context"]["id"],**c.keydict(k),actions={m:k in x["selections"][m] for m in METHODS},secondary_actions={m:k in x["secondary"][m] for m in METHODS}) for x in contexts for k in sorted(x["parts"]["test"])))
        decision = attribution(reps,transports);c.write("DEVELOPMENT_DECISION.json",decision)
        c.parents();c.frozen();verify_controls(PREVIOUS)
        for entry in c.load(root/spec["manifest_path"])["files"]: c.check(entry)
        state.update(status="SCIENTIFIC_EXECUTION_COMPLETE_PENDING_INDEPENDENT",model_bundles=28,completed_utc=c.now(),retrieval_generation_calls=0,
                     original_artifacts_unchanged=True,boundary={k:sorted(v) if isinstance(v,set) else v for k,v in boundary.items()},decision=decision["decision"])
        lines=["# HGB-only development attribution", "", "CAS Q2 STATUS: NOT READY.", "", "Decision: "+decision["decision"], "", "| Seed | HGB_GBV_R Net / Damage | HGB_ONLY_R Net / Damage | GBV_ONLY_R Net / Damage |", "|---|---|---|---|"]
        for r in reps:
            mm=r["pooled"]["methods"];lines.append("| "+str(r["seed"])+" | "+" | ".join(str(mm[m]["net"])+" / "+str(mm[m]["damage"]) for m in ("HGB_GBV_R","HGB_ONLY_R","GBV_ONLY_R"))+" |")
        lines += ["", "All five repetitions and three LODO datasets retained. Same total cap is primary; allocation sensitivity is secondary. These are development results, not confirmation.", "", "No final model or fresh confirmation has been run. Independent verification pending."]
        with destination("AUTHOR_REPORT.md").open("x",encoding="utf-8") as f:f.write("\n".join(lines)+"\n")
    except Exception as exc: state.update(error=repr(exc),traceback=traceback.format_exc())
    c.write("SCIENTIFIC_EXECUTION_RECEIPT.json",state)
    print(json.dumps({k:v for k,v in state.items() if k in ("status","error","scientific_fit_calls","decision")}))
    return 2 if state["status"]=="FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
