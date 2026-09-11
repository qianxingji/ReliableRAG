"""Fit the five fixed empirical policies once, with no test or action metrics."""
from __future__ import annotations
import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
from scripts.replay_roa_original import REPO, bind_original, load_original, install_boundary, write_json
from scripts.verify_roa_artifacts import SPEC_PATH, digest, verify, safe_file, relative_path
from scripts.cas_q2_seals import verify_controls
from src.arbitration.empirical_contract import FIELDS, split_development

NAMESPACE = "outputs/cas_q2/empirical_fixed_panel_v1"
HGB_ANCHOR = "cec3d2c2f085225c3995792a7839f6acbec6fac8b75edd8463ac18b9e2a75a8e"
AUDIT_ANCHOR = "d368dc747ec8dbc6d2208e97e7bd2da8ecbebf1dcdda080f02d2317661c1ad47"


def verify_hgb():
    root = REPO/"outputs/cas_q2/hgb_only_attribution_v1"
    assert digest(root/"SHA256_MANIFEST.json") == HGB_ANCHOR
    files = json.loads((root/"SHA256_MANIFEST.json").read_text())["files"]
    assert len({e["path"].casefold() for e in files}) == len(files)
    for e in files:
        p = safe_file(root, relative_path(e["path"]))
        assert p.stat().st_size == e["size_bytes"] and digest(p) == e["sha256"]
    assert {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} == {e["path"] for e in files}|{"SHA256_MANIFEST.json"}
    assert json.loads((root/"INDEPENDENT_VALIDATION.json").read_text())["status"] == "PASS"
    return HGB_ANCHOR


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--replay-root", type=Path, required=True)
    args = p.parse_args()
    root, out = args.project_root.resolve(), REPO/NAMESPACE
    if out.exists() or (root/NAMESPACE).exists():p.error("Single-use namespace already exists")
    commit = subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip()
    if subprocess.check_output(["git","status","--porcelain"],cwd=REPO,text=True).strip():p.error("Commit executable sources first")
    spec = json.loads(SPEC_PATH.read_text())
    if verify(root,root/spec["manifest_path"],spec)["integrity_status"] != "PASS":p.error("Original integrity")
    audit = args.replay_root/"p0_1_upstream_v2/UPSTREAM_PROVENANCE.json"
    if digest(audit) != AUDIT_ANCHOR:p.error("Accepted provenance report changed")
    controls_receipt = verify_controls(REPO/"outputs/cas_q2/supervision_matched_controls_v1")
    verify_hgb()
    c = bind_original(root,out)
    d = load_original("design")
    from src.arbitration.empirical_panel import fit_panel
    from threadpoolctl import threadpool_info, threadpool_limits
    threadpool_info()
    parent_receipt = c.parents()
    c.frozen()
    feature_path = c.OUT/"NUMERIC_FEATURES_PRIVATE.jsonl"
    ys_path = c.SOURCES["outcomes"]
    features, ys = c.keyed(feature_path), c.keyed(ys_path)
    assert set(features) == set(ys) and sum(r["eligible"] for r in features.values()) == 3202
    parts = split_development(features)
    assert parts["fit"].isdisjoint(parts["cal"])
    out.mkdir(parents=True,exist_ok=False)
    boundary = install_boundary(out)
    state = dict(status="FAIL", cas_q2_status="NOT READY", scientific_fit_calls=0,
                 scientific_fit_started_calls=0, new_retrieval_generation_calls=0,
                 new_confirmation_ids_selected=0, held_out_evaluation_performed=False,
                 role="Fixed empirical policies, not cleared novel-method advancement")
    def save(name, value):write_json(out/name,value)
    def file_record(path):return dict(path=str(path),sha256=digest(path),size_bytes=path.stat().st_size)
    events = []
    try:
        source_names = ["scripts/fit_roa_empirical_panel.py","scripts/validate_roa_empirical_panel.py",
            "scripts/replay_roa_original.py","src/arbitration/empirical_contract.py","src/arbitration/empirical_panel.py",
            "src/arbitration/recovery_controls.py","src/arbitration/roa_original/controls.py","src/arbitration/roa_original/design.py",
            "docs/cas_q2/EMPIRICAL_REPLICATION_PROTOCOL_V1.md","tests/test_empirical_contract.py"]
        freeze = dict(commit=commit, command=sys.argv, source_files=[file_record(REPO/n) for n in source_names],
            input_files=[file_record(feature_path),file_record(ys_path),file_record(audit)],
            original_manifest_sha256=spec["manifest_sha256"], prior_hgb_manifest_sha256=HGB_ANCHOR,
            prior_controls=controls_receipt, field_indices=FIELDS, target="a0_em==0 and a1_em==1",
            base_parameters=d.BASE, platt_parameters=d.PLATT, threads=1,
            executable=file_record(Path(sys.executable)), versions={n:importlib.metadata.version(n) for n in ("numpy","scipy","scikit-learn","threadpoolctl")},
            frozen_utc=c.now(), probe_role="All opened development features; overlaps fit/cal; no quality evaluation")
        save("EXECUTABLE_FREEZE.json",freeze)
        save("PARENT_VERIFICATION.json",parent_receipt)
        save("SPLIT_MANIFEST.json",{name:dict(N_all=len(kk),N_groups=len({(k[0],k[2]) for k in kk}),
            keys_sha256=c.kh(kk),N_eligible=sum(features[k]["eligible"] for k in kk)) for name,kk in parts.items()})
        with (out/"TRAINING_GROUPS_PRIVATE.jsonl").open("x",encoding="utf-8",newline="\n") as f:
            for dataset,identifier in sorted({(k[0],k[2]) for k in features}):
                role="cal" if (dataset,"bm25",identifier) in parts["cal"] else "fit"
                f.write(json.dumps(dict(dataset=dataset,sample_id=identifier,role=role))+"\n")
        with (out/"FIT_EVENTS_PRIVATE.jsonl").open("x",encoding="utf-8",newline="\n") as f:
            def event(e):
                events.append(e)
                f.write(json.dumps(e,sort_keys=True,allow_nan=False)+"\n");f.flush()
                if e["event"] == "fit_started":
                    state["scientific_fit_started_calls"] += 1
                    assert state["scientific_fit_started_calls"] <= 10
                else:state["scientific_fit_calls"] += 1
            models = {}
            with (out/"PROBE_PREDICTIONS_PRIVATE.jsonl").open("x",encoding="utf-8",newline="\n") as pred:
                with threadpool_limits(limits=1):
                    for name,indices in FIELDS.items():
                        ff = {k:dict(r,numeric=[r["numeric"][i] for i in indices]) for k,r in features.items()}
                        model, predictions, ranking = fit_panel(ff,ys,parts,name,"fixed_"+name,event)
                        model.update(numeric_indices=indices,probe_role=freeze["probe_role"],ranking=ranking)
                        models[name] = model
                        for k,row in sorted(predictions.items()):
                            pred.write(json.dumps(dict(policy=name,**c.keydict(k),**row),sort_keys=True)+"\n")
                        pred.flush()
                        print("FITTED",name,flush=True)
            save("MODELS.json",models)
        assert state["scientific_fit_calls"] == state["scientific_fit_started_calls"] == 10
        assert Counter((e["variant"],e["stage"],e["event"]) for e in events) == Counter((v,s,e) for v in FIELDS for s in ("base","platt") for e in ("fit_started","fit_completed"))
        assert not boundary["blocked"]
        for entry in freeze["input_files"]+freeze["source_files"]:assert digest(Path(entry["path"])) == entry["sha256"]
        assert verify(root,root/spec["manifest_path"],spec)["integrity_status"] == "PASS"
        verify_hgb();verify_controls(REPO/"outputs/cas_q2/supervision_matched_controls_v1")
        state.update(status="FIT_COMPLETE_PENDING_INDEPENDENT", scientific_fit_call_history_before=168,
                     scientific_fit_call_history_total=178, original_artifacts_unchanged=True)
    except Exception as exc:
        import traceback
        state.update(error=repr(exc),traceback=traceback.format_exc())
    save("FIT_RECEIPT.json",state)
    save("EXECUTION_MANIFEST.json",dict(files=[dict(path=x.name,sha256=digest(x),size_bytes=x.stat().st_size) for x in sorted(out.iterdir()) if x.is_file()]))
    print(json.dumps(state))
    return 2 if state["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
