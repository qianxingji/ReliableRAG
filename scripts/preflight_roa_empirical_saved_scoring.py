"""CPU saved-model compatibility and invented numerical probes; no fresh branch read."""
import argparse
import importlib.metadata
from pathlib import Path
import platform
import subprocess
import sys

from scripts.empirical_scoring_io import REPO, inputs, native_scoring, saved_models, panel_scores, record, require
from scripts.empirical_scoring_guard import guard
from scripts.empirical_scoring_fixtures import invented_trace, invented_cells, direct_base, direct_v2, scalar_panel
from scripts.empirical_retrieval_io import configure_environment, boundary_record, seal
from scripts.replay_roa_original import write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--project-root",type=Path,required=True)
    args=parser.parse_args();root=args.project_root.resolve();out=REPO/"outputs/cas_q2/empirical_saved_scoring_preflight_v1"
    require(not out.exists(),"Single-use CPU model preflight")
    require(not subprocess.check_output(["git","status","--porcelain"],cwd=REPO,text=True).strip(),"Commit first")
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip()
    out.mkdir(parents=True,exist_ok=False)
    result=dict(status="FAIL",cas_q2_status="NOT READY",source_commit=commit,scientific_fit_calls=0,
        pretrained_neural_model_loads=0,neural_forward_calls=0,fresh_branch_rows_read=0,fresh_gold_values_materialized=0,
        numeric_checks=0,max_numeric_error=0.)
    boundary=None
    try:
        environment=configure_environment(out);platform_metadata=platform.uname()._asdict()
        import joblib
        import numpy as np
        import sklearn.ensemble, sklearn.linear_model, sklearn.pipeline, sklearn.preprocessing
        from threadpoolctl import threadpool_info, threadpool_limits
        # Resolve library metadata before the guarded scientific phase, not model data.
        threadpool_info();joblib.cpu_count(only_physical_cores=True)
        audit,pre,paths=inputs(root)
        source_names=("scripts/empirical_scoring_io.py","scripts/empirical_scoring_guard.py","scripts/empirical_scoring_fixtures.py",
            "scripts/preflight_roa_empirical_saved_scoring.py","docs/cas_q2/EMPIRICAL_C4_SCORING_CONTRACT.md",
            "tests/test_empirical_scoring.py","scripts/empirical_pool_io.py","scripts/empirical_retrieval_io.py",
            "scripts/replay_roa_original.py","scripts/verify_roa_artifacts.py")
        paths += [REPO/n for n in source_names]+[Path(sys.executable)]
        records=[record(p) for p in sorted(set(paths))]
        versions={n:importlib.metadata.version(n) for n in pre["environment"]["versions"]}
        require(versions==pre["environment"]["versions"],"Scoring package versions")
        write_json(out/"EXECUTABLE_FREEZE.json",dict(source_commit=commit,command=sys.argv,inputs=records,
            versions=versions,environment=environment,platform_metadata=platform_metadata,
            scope="Eight saved estimator bundles and five saved parameter heads; three invented traces only"))
        boundary=guard(root,out,paths,mode="cpu_models")
        wrapper,native,v2,eligibility,schema,nodes=native_scoring(root)
        models,bundle,panel=saved_models(root,native,v2)
        result["saved_upstream_estimators_loaded"]=len(models);result["saved_v2_ensemble_bundles_loaded"]=1
        def close(a,b):
            aa,bb=np.asarray(a),np.asarray(b);require(aa.shape==bb.shape and np.isfinite(aa).all() and np.isfinite(bb).all(),"Finite aligned probes")
            error=float(np.max(np.abs(aa-bb))) if aa.size else 0.
            result["numeric_checks"]+=aa.size;result["max_numeric_error"]=max(result["max_numeric_error"],error)
            require(error<=1e-10,"Unchanged numerical tolerance")
        traces=[invented_trace(i,r) for i,r in enumerate(("bm25","dense","hybrid"))]
        pairs=[native.symmetric.build_pair_record(t,invented_cells(i),schema_version="mars-state-symmetric-v1") for i,t in enumerate(traces)]
        for pair in pairs:
            close(pair["diagnostics"]["B_repair"],3.5);close(pair["diagnostics"]["m1"],1.5)
            close(pair["invariant_features"]["evidence_id_overlap"],4/6)
        keys=[(t["dataset"],t["retriever"],t["sample_id"]) for t in traces]
        with threadpool_limits(limits=1):
            base=[wrapper.base_scores(native,models,pair) for pair in pairs]
            expected=direct_base(models,pairs,native.ordinary.ORDINARY_NAMES)
            for field in v2.V2_SCORE_FEATURES:close([r[field] for r in base],expected[field])
            x=np.array([[r[field] for field in v2.V2_SCORE_FEATURES] for r in base],dtype=float)
            fused=v2.score_unseen(bundle,x);close(fused,direct_v2(bundle,x))
            numeric=[list(row)+[.125-i*.125] for i,row in enumerate(x)]
            predicted=panel_scores(panel,keys,numeric)
            for policy in panel:
                for i,key in enumerate(keys):
                    raw,prob=scalar_panel(panel[policy],key[1],numeric[i])
                    close(predicted[policy]["logit_R"][i],raw);close(predicted[policy]["pR"][i],prob)
            missing=[list(x) for x in numeric];missing[0][0]=None;missing[1][10]=None;missing[2][3]=float("nan")
            imputed=panel_scores(panel,keys,missing)
            for policy in panel:
                for i,key in enumerate(keys):
                    raw,prob=scalar_panel(panel[policy],key[1],missing[i])
                    close(imputed[policy]["logit_R"][i],raw);close(imputed[policy]["pR"][i],prob)
        for a,b,wanted in (("","x",False),("x","",False),("The cog","cog!",False),("silver","blue",True),("the","blue",True)):
            require(eligibility.assess_pair_eligibility(a,b).eligible is wanted,"Native eligibility semantics")
        for entry in records:require(record(Path(entry["path"]))==entry,"Scoring preflight inputs unchanged")
        require(not boundary["denied"],"CPU preflight boundary")
        result.update(status="PASS_SAVED_SCORING_CPU_INVENTED_ONLY",native_ast_nodes=nodes,
            invented_traces=3,fixed_parameter_heads=5,source_inputs_unchanged=True,
            limitation="Compatibility and synthetic downstream arithmetic only. HGB probabilities use the saved sklearn estimator; this is not independent tree traversal, fresh scoring, neural replay or evidence of answer quality.")
    except Exception as exc:
        result.update(error_type=type(exc).__name__,diagnostic=str(exc))
    finally:sys.setprofile(None)
    if boundary is not None:result["execution_boundary"]=boundary_record(boundary)
    write_json(out/"CPU_PREFLIGHT.json",result);seal(out)
    print(result["status"],result.get("diagnostic",""));return 2 if result["status"]=="FAIL" else 0


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
