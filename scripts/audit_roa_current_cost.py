"""Reconcile existing ROA-input cost receipts; no inference or outcome reads.

The accepted upstream audit supplies manifest anchors. This report describes
the historical acquisition actually reused by ROA, not a new timing benchmark.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys

from scripts.replay_roa_original import REPO, install_boundary, write_json
from scripts.verify_roa_artifacts import digest, relative_path, safe_file

AUDIT_SHA = "d368dc747ec8dbc6d2208e97e7bd2da8ecbebf1dcdda080f02d2317661c1ad47"
PREFIX = "outputs/daa_v2_fresh_v1/"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--upstream-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.project_root.resolve(), args.output.resolve()
    if out == root or root in out.parents:
        parser.error("Output must be a new directory outside the original project")
    out.mkdir(parents=True, exist_ok=False)
    report = dict(status="FAIL", cas_q2_status="NOT READY", scientific_fit_calls=0,
                  new_inference_calls=0, new_outcomes_read=0,
                  source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                  script_sha256=digest(Path(__file__)), verified_inputs=[])
    install_boundary(out)
    checked = {}
    try:
        assert digest(args.upstream_audit) == AUDIT_SHA, "UPSTREAM_AUDIT_HASH"
        audit = json.loads(args.upstream_audit.read_text(encoding="utf-8"))
        assert audit["status"] == "AUTHENTICATED_LOCAL_LINEAGE_WITH_HISTORICAL_RECEIPT_LIMITATION"
        entries = {}
        for item in audit["manifests"]:
            m = item["manifest"]
            if not any(s in m["path"] for s in ("/runtime_branch_freeze/", "/retrieval_freeze/", "/prelabel_seal_v3/")):
                continue
            path = safe_file(root, relative_path(m["path"]))
            assert digest(path) == m["sha256"] and path.stat().st_size == m["size_bytes"], "MANIFEST_HASH"
            report["verified_inputs"].append(m)
            for entry in json.loads(path.read_text(encoding="utf-8"))["files"]:
                assert entry["path"] not in entries, "DUPLICATE_BINDING"
                entries[entry["path"]] = entry

        def path(name):
            rel = PREFIX + name
            entry = entries[rel]
            p = safe_file(root, relative_path(rel))
            if rel not in checked:
                assert digest(p) == entry["sha256"] and p.stat().st_size == entry["size_bytes"], "INPUT_HASH:" + rel
                checked[rel] = entry
                report["verified_inputs"].append(entry)
            return p

        def load(name):
            return json.loads(path(name).read_text(encoding="utf-8"))

        def rows(name):
            with path(name).open(encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)

        runtime = load("runtime_branch_freeze/BUILD_RECEIPT.json")
        seal = load("runtime_branch_freeze/RUNTIME_BRANCH_FREEZE.json")
        retrieval = load("retrieval_freeze/BUILD_RECEIPT.json")
        base = load("prelabel_seal_v3/scoring/BASE_SCORE_PROVENANCE.json")
        base_execution = load("prelabel_seal_v3/execution/base.json")
        nli_execution = load("prelabel_seal_v3/execution/gbv.json")
        nli = load("prelabel_seal_v3/scoring/gbv_provenance.json")
        reconciliation = load("prelabel_seal_v3/PRELABEL_SEAL.json")
        assert runtime["status"] == seal["status"] == retrieval["status"] == base["status"] == nli_execution["status"] == "PASS"
        assert runtime["counters"] == seal["canonical_counters"]
        generation = defaultdict(Counter)
        seen = set()
        for row in rows("runtime_branch_freeze/generation_receipts.jsonl"):
            key = tuple(row[k] for k in ("dataset", "retriever", "sample_id", "stage"))
            assert key not in seen, "DUPLICATE_GENERATION_RECEIPT"
            seen.add(key)
            assert row["input_tokens"] == sum(row["attention_mask"])
            assert row["logical_generation_calls"] == 1
            assert row["qwen_forward_calls"] == row["native_output_score_steps"]
            assert 0 <= row["output_tokens"] <= row["native_output_score_steps"]
            totals = generation[row["stage"]]
            for name in ("logical_generation_calls", "qwen_forward_calls", "input_tokens", "output_tokens", "native_output_score_steps"):
                totals[name] += row[name]
            totals["rows"] += 1
        assert set(generation) == {"a0", "a1", "repair_query"}
        for stage, values in generation.items():
            assert values["rows"] == values["logical_generation_calls"] == runtime["counters"][stage + "_generation_calls"] == 13500
            assert values["qwen_forward_calls"] == runtime["counters"][stage + "_forward_calls"]
        assert len(seen) == 40500
        nli_totals = Counter()
        eligible_keys = set()
        for row in rows("prelabel_seal_v3/scoring/gbv_scores.jsonl"):
            nli_totals["traces"] += 1
            if row["eligible"]:
                eligible_keys.add(tuple(row[k] for k in ("dataset", "retriever", "sample_id")))
                nli_totals["eligible"] += 1
                for name in ("e0_chunk_count", "e1_chunk_count", "e0_premise_count", "e1_premise_count"):
                    nli_totals[name] += row[name]
        assert nli_totals["traces"] == 13500 and nli_totals["eligible"] == len(eligible_keys) == 3202
        assert nli_totals["e0_chunk_count"] + nli_totals["e1_chunk_count"] == nli_execution["call_counters"]["gbv_nli_pairs"]
        cell_keys = set()
        cell_count = 0
        for row in rows("prelabel_seal_v3/scoring/likelihood_cells.jsonl"):
            key = tuple(row[k] for k in ("dataset", "retriever", "sample_id"))
            assert key not in cell_keys
            cell_keys.add(key)
            assert set(row["cells"]) == {"L00", "L01", "L10", "L11"}
            cell_count += len(row["cells"])
        assert cell_keys == eligible_keys
        assert cell_count == base["counters"]["likelihood_cell_requests"] == base["likelihood_sequences_computed"] + base["likelihood_cache_hits"] == 12808
        for name in ("runtime_branch_freeze/native_runtime.py", "runtime_branch_freeze/build_runtime.py", "prelabel_seal_v3/score_base.py", "prelabel_seal_v3/CPU_DIAGNOSTIC_CONTROL_NOTE.md"):
            path(name)
        report.update(
            status="PASS_RECEIPT_RECONCILIATION_WITH_COST_LIMITS",
            scope="Historical canonical acquisition shared by current ROA and all paired policies; no new timing benchmark or standalone policy measurement",
            upstream_audit_sha256=AUDIT_SHA,
            generation=dict(generation),
            runtime=dict(counters=runtime["counters"], elapsed_seconds=runtime["elapsed_seconds"]),
            retrieval=dict(counters=retrieval["execution_counters"], elapsed_seconds=retrieval["elapsed_seconds"]),
            base=dict(counters=base["counters"], wall_seconds=base["wall_seconds"], computed_likelihood_sequences=base["likelihood_sequences_computed"], likelihood_cache_hits=base["likelihood_cache_hits"]),
            nli=dict(ledger_totals=dict(nli_totals), call_counters=nli_execution["call_counters"], wall_seconds=nli_execution["wall_seconds"], model_id=nli["model_id"], revision=nli["model_revision"]),
            preserved_base_execution=dict(status=base_execution["status"], exit_code=base_execution["exit_code"], error=base_execution["error"], wall_seconds=base_execution["wall_seconds"], boundary_denials=base_execution["boundary_denials"]),
            prelabel_seal_status=reconciliation["status"],
            limitations=[
                "Base acquisition has an original FAIL receipt for blocked CPU-discovery subprocesses and a separate historical reconciliation; original FAIL is retained.",
                "Stage wall times have different boundaries and cache states; do not sum them into measured standalone end-to-end latency or claim policy speedups.",
                "Shared acquisition computed all historical base scores. An HGB-only deployment pipeline was not separately timed.",
                "Runtime candidate generation ran for every trace before answer-pair eligibility and top-K allocation; a 5% action cap is not a 5% compute budget.",
                "No measured per-current-policy CPU latency or new GPU peak-memory measurement is available from this audit.",
                "Generation token totals are saved native counters, not a measure of FLOPs; input prefix tokens are not counted once per autoregressive forward.",
            ])
        for rel, entry in checked.items():
            assert digest(root / rel) == entry["sha256"], "INPUT_CHANGED_DURING_AUDIT"
        report["inputs_unchanged"] = True
    except Exception as exc:
        import traceback
        report.update(error=repr(exc), traceback=traceback.format_exc())
    write_json(out / "CURRENT_COST_AUDIT.json", report)
    print(json.dumps({k:report[k] for k in ("status", "scientific_fit_calls", "new_inference_calls")}))
    return 2 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
