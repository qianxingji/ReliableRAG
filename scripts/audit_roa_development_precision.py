"""Execute DEVELOPMENT_PRECISION_PROTOCOL on opened, sealed development data."""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

from scripts.replay_roa_original import REPO, install_boundary, write_json
from scripts.verify_roa_artifacts import digest, relative_path, safe_file
from src.evaluation.batch_allocation import weighted_top_k

ANCHOR = "cec3d2c2f085225c3995792a7839f6acbec6fac8b75edd8463ac18b9e2a75a8e"
OUTCOME_SHA = "2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576"
METHODS = ("ROA-FULL", "HGB_GBV_R", "HGB_ONLY_R", "GBV_ONLY_R")
PAIRS = ((0, 1), (1, 2), (1, 3))
DRAWS = 2000


def key(row):
    return tuple(row[n] for n in ("dataset", "retriever", "sample_id"))


def rows(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.project_root.resolve(), args.output.resolve()
    stage = REPO / "outputs/cas_q2/hgb_only_attribution_v1"
    if out == root or root in out.parents or out == stage or stage in out.parents:
        parser.error("New output must be outside both sealed projects/namespaces")
    out.mkdir(parents=True, exist_ok=False)
    report = dict(status="FAIL", cas_q2_status="NOT READY", scientific_fit_calls=0,
                  new_inference_calls=0, new_outcomes_acquired=0, draws_per_repetition=DRAWS,
                  numpy_version=np.__version__, source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                  source_hashes={p:digest(REPO/p) for p in ("scripts/audit_roa_development_precision.py", "docs/cas_q2/DEVELOPMENT_PRECISION_PROTOCOL.md", "src/evaluation/batch_allocation.py")},
                  repetitions=[], explicit_copy_checks=0)
    install_boundary(out)
    try:
        manifest = stage / "SHA256_MANIFEST.json"
        assert digest(manifest) == ANCHOR
        entries = json.loads(manifest.read_text())["files"]
        assert len({e["path"].casefold() for e in entries}) == len(entries)
        for entry in entries:
            p = safe_file(stage, relative_path(entry["path"]))
            assert p.stat().st_size == entry["size_bytes"] and digest(p) == entry["sha256"]
        assert {p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()} == {e["path"] for e in entries} | {"SHA256_MANIFEST.json"}
        assert json.loads((stage/"INDEPENDENT_VALIDATION.json").read_text())["status"] == "PASS"
        outcome = root / "outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl"
        assert digest(outcome) == OUTCOME_SHA
        ys = {}
        for row in rows(outcome):
            assert key(row) not in ys
            assert row["a0_em"] in (0, 1) and row["a1_em"] in (0, 1)
            ys[key(row)] = (row["a1_em"] - row["a0_em"], int(row["a0_em"] == 1 and row["a1_em"] == 0))
        assert len(ys) == 13500
        contexts = {x["context"]["id"]:x for x in json.loads((stage/"SPLIT_MANIFEST.json").read_text())["contexts"] if x["context"]["stage"] == "primary"}
        predicted = defaultdict(dict)
        for row in rows(stage/"PREDICTIONS_PRIVATE.jsonl"):
            if row["context_id"] in contexts:
                ctx = predicted[row["context_id"]]
                assert key(row) not in ctx
                ctx[key(row)] = row
        actions = defaultdict(dict)
        for row in rows(stage/"ACTIONS_PRIVATE.jsonl"):
            if row["context_id"] in contexts:
                ctx = actions[row["context_id"]]
                assert key(row) not in ctx
                ctx[key(row)] = row["actions"]
        assert set(predicted) == set(actions) == set(contexts) and len(contexts) == 25
        totals = {r["seed"]:r["pooled"]["methods"] for r in json.loads((stage/"OUTER_RESULTS.json").read_text())["repetitions"]}
        with (out/"BOOTSTRAP_DRAWS.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for rep_index, seed in enumerate(range(20260917, 20260922)):
                folds = []
                point = np.zeros((len(METHODS), 2), dtype=np.int64)
                all_keys = set()
                for outer in range(5):
                    cid = f"p_{seed}_{outer}_final"
                    bykey = predicted[cid]
                    kk = sorted(bykey)
                    assert set(kk) == set(actions[cid])
                    assert not all_keys.intersection(kk)
                    all_keys.update(kk)
                    assert len(kk) == contexts[cid]["partitions"]["test"]["N_all"]
                    groups = sorted({(k[0], k[2]) for k in kk})
                    group_index = {g:i for i,g in enumerate(groups)}
                    sibling_index = np.array([group_index[(k[0], k[2])] for k in kk])
                    assert np.all(np.bincount(sibling_index) == 3)
                    strata = [np.array([i for i,g in enumerate(groups) if g[0] == d]) for d in sorted({g[0] for g in groups})]
                    endpoints = np.array([ys[k] for k in kk], dtype=np.int64)
                    cap = round(0.05*len(kk))
                    assert cap == contexts[cid]["cap"]
                    orders = []
                    for method_index, method in enumerate(METHODS):
                        eligible = [i for i,k in enumerate(kk) if bykey[k]["eligible"]]
                        assert all(np.isfinite(bykey[kk[i]]["scores"][method]) for i in eligible)
                        order = np.array(sorted(eligible, key=lambda i:(-bykey[kk[i]]["scores"][method], kk[i])))
                        orders.append(order)
                        selected = weighted_top_k(order, np.ones(len(kk), dtype=np.int64), cap)
                        assert np.array_equal(selected, np.array([int(actions[cid][k][method]) for k in kk])), "POINT_ACTIONS"
                        point[method_index] += selected @ endpoints
                    folds.append((kk, bykey, sibling_index, strata, endpoints, orders, len(groups)))
                assert all_keys == set(ys)
                for method_index, method in enumerate(METHODS):
                    assert point[method_index].tolist() == [totals[seed][method]["net"], totals[seed][method]["damage"]], "POINT_TOTALS"
                rng = np.random.default_rng(2026092300 + rep_index)
                values = np.empty((DRAWS, len(PAIRS), 2), dtype=np.float64)
                for draw in range(DRAWS):
                    current = np.zeros_like(point)
                    for kk, bykey, sibling_index, strata, endpoints, orders, ng in folds:
                        qw = np.zeros(ng, dtype=np.int64)
                        for stratum in strata:
                            sampled = rng.choice(stratum, size=len(stratum), replace=True)
                            qw += np.bincount(sampled, minlength=ng)
                        rw = qw[sibling_index]
                        cap = round(0.05*int(rw.sum()))
                        assert int(rw.sum()) == len(kk)
                        for mi, order in enumerate(orders):
                            selected = weighted_top_k(order, rw, cap)
                            if draw == 0:
                                copies = [(i,c) for i,k in enumerate(kk) if bykey[k]["eligible"] for c in range(int(rw[i]))]
                                copies.sort(key=lambda x:(-bykey[kk[x[0]]]["scores"][METHODS[mi]], kk[x[0]], x[1]))
                                explicit = np.bincount([i for i,c in copies[:cap]], minlength=len(kk))
                                assert np.array_equal(selected, explicit), "EXPLICIT_COPY_ALLOCATION"
                                report["explicit_copy_checks"] += 1
                            current[mi] += selected @ endpoints
                    differences = np.array([current[a]-current[b] for a,b in PAIRS])
                    values[draw] = differences * (100.0/13500)
                    stream.write(json.dumps(dict(seed=seed, draw=draw, differences_event_counts=differences.tolist()), separators=(",", ":"))+"\n")
                comparisons = {}
                for i, (a,b) in enumerate(PAIRS):
                    comparisons[METHODS[a]+"_minus_"+METHODS[b]] = {
                        name:dict(point_pp=float((point[a,j]-point[b,j])*100.0/13500), point_event_difference=int(point[a,j]-point[b,j]),
                                  bootstrap_sd_pp=float(values[:,i,j].std(ddof=1)), percentile_95_range_pp=np.quantile(values[:,i,j],[0.025,0.975],method="linear").tolist())
                        for j,name in enumerate(("em_gain", "damage_rate"))}
                report["repetitions"].append(dict(seed=seed, bootstrap_seed=2026092300+rep_index, comparisons=comparisons))
                print("COMPLETE",seed,flush=True)
        assert report["explicit_copy_checks"] == 100
        assert digest(outcome) == OUTCOME_SHA and digest(manifest) == ANCHOR
        report.update(status="PASS_CONDITIONAL_DEVELOPMENT_PRECISION", inputs_unchanged=True,
                      input_manifest_sha256=ANCHOR, outcome_sha256=OUTCOME_SHA,
                      draws_sha256=digest(out/"BOOTSTRAP_DRAWS.jsonl"),
                      interpretation="Exploratory conditional OOF-score-panel ranges; no training uncertainty, multiplicity-adjusted claims, equivalence test, domain-generalization claim or final sample-size recommendation")
    except Exception as exc:
        import traceback
        report.update(error=repr(exc), traceback=traceback.format_exc())
    write_json(out/"DEVELOPMENT_PRECISION.json", report)
    return 2 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
