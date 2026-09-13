"""Bind accepted retrieval and predeclare all reader traces; no generation authority."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripts.empirical_retrieval_io import REPO, OUT as RETRIEVAL, inputs, verify_namespace, load, record, require, seal
from scripts.empirical_runtime_contract import make_traces, replay_subset, canonical, sha_json, trace_key
from scripts.replay_roa_original import install_boundary, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--retrieval-manifest-sha256", required=True)
    args = p.parse_args(); root = args.project_root.resolve()
    out = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
    require(not out.exists(), "Single-use runtime preparation")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    out.mkdir(parents=True, exist_ok=False); install_boundary(out)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, reader_generation_calls=0,
        model_load_calls=0, scientific_fit_calls=0, fresh_gold_values_materialized=0)
    try:
        cfg, pre, paths = inputs(root)
        paths += verify_namespace(RETRIEVAL, args.retrieval_manifest_sha256)
        require(load(RETRIEVAL / "INDEPENDENT_VALIDATION.json")["status"] == "PASS_INDEPENDENT_ORIGINAL_RETRIEVAL", "Independent retrieval required")
        by_dataset = {d: [json.loads(line) for line in (RETRIEVAL / "top5" / (d + ".jsonl")).read_text(encoding="utf-8").splitlines()]
                      for d in ("hotpotqa", "2wikimultihopqa", "musique")}
        traces = make_traces(by_dataset); replay = replay_subset(traces)
        paths += [Path(__file__), REPO / "scripts/empirical_runtime_contract.py", REPO / "tests/test_empirical_runtime_contract.py",
                  REPO / "docs/cas_q2/EMPIRICAL_C3_RUNTIME_CONTRACT.md"]
        paths += [REPO / name for name in ("scripts/empirical_retrieval_io.py", "scripts/empirical_pool_io.py",
                  "scripts/replay_roa_original.py", "scripts/verify_roa_artifacts.py")]
        records = [record(p) for p in sorted(set(paths))]
        write_json(out / "TRACE_PREPARATION_FREEZE.json", dict(source_commit=commit, command=sys.argv, inputs=records,
            original_runtime_config_sha256=record(root / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json")["sha256"],
            scientific_runtime_config=cfg["runtime_config"], acquisition_scope="Same fixed native generation parameters; new accepted cohort and pools",
            scope="Trace/replay membership freeze only; complete reader adapter and joint GPU preflight still required"))
        for name, rows in (("TRACE_MANIFEST_PRIVATE.jsonl", traces), ("REPLAY_SUBSET_PRIVATE.jsonl", replay)):
            with (out / name).open("xb") as stream:
                for row in rows: stream.write(canonical(row)+b"\n")
        for e in records: require(record(Path(e["path"])) == e, "Runtime preparation input changed")
        result.update(status="PASS_RUNTIME_TRACE_PREPARATION_ONLY", canonical_traces=len(traces), replay_traces=len(replay),
            canonical_generation_calls_planned=54000, replay_generation_calls_planned=540,
            trace_sequence_sha256=sha_json([trace_key(row) for row in traces]), replay_membership_sha256=sha_json([trace_key(row) for row in replay]),
            reader_execution_cleared=False)
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    write_json(out / "PREPARATION_RESULT.json", result); seal(out)
    print(json.dumps(result)); return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
