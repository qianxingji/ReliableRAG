"""Execute the three frozen C4 scoring stages once, after accepted prerequisites."""
import argparse
from collections import Counter
import gc
from pathlib import Path
import sys

from scripts.empirical_scoring_stage_run import StageRun
from scripts.empirical_scoring_stage_io import STAGES, DATASETS, EXPECTED_STATUS, read_rows, restore_traces, serialize_allocation, require
from scripts.empirical_scoring_import_v2 import native_scoring
from scripts.empirical_scoring_io import saved_models
from scripts.empirical_scoring_models import make_bge, make_likelihood, make_gbv, stage_nli_cache
from scripts.empirical_semantic_witness import SemanticWitness
from scripts.empirical_likelihood_witness import LikelihoodWitness
from scripts.empirical_gbv_witness import GbVWitness
from scripts.empirical_scoring_pipeline import score_likelihood_trace, score_gbv_trace, common_policy_ledger
from scripts.empirical_scoring_journals import Ledger, ForwardCounter, ForwardJournal, DurableGbV, compact_base, compact_gbv
from scripts.empirical_runtime_contract import trace_key
from scripts.replay_roa_original import write_json


def base_stage(run, wrapper, native, v2, eligibility, handles):
    import numpy as np
    import torch
    from threadpoolctl import threadpool_limits
    traces = restore_traces(wrapper, run.context)
    run.result.update(trace_count=len(traces), completed_traces=0, native_eligible_traces=0)
    run.phase["stage"] = "all_answer_semantics"
    model = make_bge(native, run.root, run.out, run.pre)
    observer, counter = SemanticWitness(model), ForwardCounter(model.model)
    run.active_counter = counter
    handles.extend([observer, counter])
    semantic = run.out / "semantic"
    semantic.mkdir()
    for dataset in DATASETS:
        selected = [t for t in traces if t["dataset"] == dataset]
        require(len(selected) == 6000, "Complete canonical dataset answer batch")
        run.phase["dataset"] = dataset
        values, vectors, rows, batches = observer.score(native, selected)
        with (semantic / (dataset + ".npy")).open("xb") as stream:
            np.save(stream, vectors, allow_pickle=False)
        ledger = Ledger(semantic / (dataset + ".jsonl"))
        try:
            for trace, row, value in zip(selected, rows, values, strict=True):
                trace["answer_semantic_agreement"] = value
                ledger.append(row)
        finally:
            ledger.close()
        write_json(semantic / (dataset + "_batches.json"), batches)
        print("C4_ANSWER_SEMANTICS", dataset, len(rows), flush=True)
    require(counter.calls == observer.forward_count == 2250 and counter.rows == 36000, "All answer semantic cost before eligibility")
    run.result["bge"] = dict(metadata=model.metadata, actual=counter.summary())
    for item in reversed(handles): item.close()
    handles.clear()
    model = observer = counter = item = None; run.active_counter = None; gc.collect(); torch.cuda.empty_cache()

    run.phase["stage"] = "native_likelihood_and_base_scores"
    models, bundle, panel = saved_models(run.root, native, v2)
    run.result["saved_artifacts_loaded"] = dict(upstream_estimators=7, v2_ensemble_bundles=1, fixed_parameter_heads=5)
    model = make_likelihood(native, run.root, run.out, run.pre)
    observer, counter = LikelihoodWitness(model), ForwardCounter(model.model)
    run.active_counter = counter
    forward_ledger, scores = Ledger(run.out / "likelihood_forwards.jsonl"), Ledger(run.out / "scores.jsonl")
    journal = ForwardJournal(model.model, observer, forward_ledger, run.phase)
    handles.extend([observer, counter, forward_ledger, scores, journal])
    forced = Counter()
    with threadpool_limits(limits=1):
        for position, trace in enumerate(traces):
            run.phase.update({k: trace[k] for k in ("dataset", "retriever", "sample_id")})
            run.phase["position"] = position
            record = score_likelihood_trace(wrapper, native, models, eligibility, trace, observer)
            scores.append(compact_base(record))
            if record["eligible"]:
                run.result["native_eligible_traces"] += 1
            else:
                forced[record["forced_keep_reason"]] += 1
            run.result["completed_traces"] += 1
            if (position + 1) % 100 == 0:
                print("C4_BASE_TRACES", position + 1, 18000, flush=True)
    requests = 4 * run.result["native_eligible_traces"]
    require(scores.rows == 18000 and model.calls == model.sequences_scored == counter.calls == observer.forward_count == forward_ledger.rows and
        requests == model.sequences_scored + model.cache_hits, "Complete native likelihood cost accounting")
    run.result.update(forced_keep_counts=dict(forced), likelihood_cell_requests=requests,
        qwen=dict(metadata=model.metadata, actual=counter.summary(), sequences_computed=model.sequences_scored,
            cache_hits=model.cache_hits, computed_prompt_tokens=model.prompt_tokens, computed_answer_tokens=model.answer_tokens),
        peak_allocated_cuda_bytes=torch.cuda.max_memory_allocated())


def gbv_stage(run, wrapper, eligibility, handles):
    import torch
    traces = restore_traces(wrapper, run.context)
    run.result.update(trace_count=len(traces), completed_traces=0, native_eligible_traces=0, common_eligible_traces=0)
    run.result["nli_snapshot_copies"] = stage_nli_cache(run.root, run.out, run.pre)
    native, model = make_gbv(run.root, run.out)
    run.phase["stage"] = "paired_native_gbv"
    observer, counter = GbVWitness(model, native), ForwardCounter(model.model)
    run.active_counter = counter
    forwards, branches, scores = Ledger(run.out / "nli_forwards.jsonl"), Ledger(run.out / "nli_branches.jsonl"), Ledger(run.out / "scores.jsonl")
    journal = ForwardJournal(model.model, observer, forwards, run.phase, nli=True)
    durable = DurableGbV(observer, branches, run.phase)
    handles.extend([observer, counter, forwards, branches, scores, journal])
    forced, requested = Counter(), 0
    for position, trace in enumerate(traces):
        durable.begin(trace, position)
        decision = eligibility.assess_pair_eligibility(trace["a0"], trace["a1"])
        run.result["native_eligible_traces"] += int(decision.eligible)
        record = score_gbv_trace(eligibility, trace, durable)
        requested += record["attempted_branches"]
        scores.append(compact_gbv(record))
        run.result["common_eligible_traces"] += int(record["eligible"])
        if not record["eligible"]:
            forced[record["forced_keep_reason"]] += 1
        run.result["completed_traces"] += 1
        if (position + 1) % 100 == 0:
            print("C4_GBV_TRACES", position + 1, 18000, flush=True)
    require(scores.rows == 18000 and counter.calls == observer.forward_count == forwards.rows, "All native NLI forward accounting")
    run.result.update(forced_keep_counts=dict(forced), attempted_branches=requested, completed_branches=branches.rows,
        gbv=dict(revision=model.model.config._commit_hash, dtype=model.resolved_dtype, id2label=model.model.config.id2label,
            effective_max_length=model.max_length, actual=counter.summary()), peak_allocated_cuda_bytes=torch.cuda.max_memory_allocated())


def policies_stage(run, wrapper, native, v2, eligibility):
    from threadpoolctl import threadpool_limits
    traces = restore_traces(wrapper, run.context)
    base = list(read_rows(STAGES["base"] / "scores.jsonl"))
    gbv = list(read_rows(STAGES["gbv"] / "scores.jsonl"))
    models, bundle, panel = saved_models(run.root, native, v2)
    run.phase["stage"] = "fixed_policy_allocation"
    with threadpool_limits(limits=1):
        allocation = common_policy_ledger(traces, base, gbv, eligibility, v2, bundle, panel)
    require(allocation["N_all"] == 18000 and allocation["cap"] == 900, "Prespecified all-trace global budget")
    write_json(run.out / "POLICIES.json", serialize_allocation(allocation))
    actions = Ledger(run.out / "actions.jsonl")
    try:
        for row in allocation["ledger"]:
            actions.append(row)
    finally:
        actions.close()
    require(actions.rows == 18000, "Every prelabel action retained")
    run.result.update(trace_count=18000, completed_traces=18000, N_all=18000, N_eligible=allocation["N_eligible"], cap=900,
        replacement_counts=allocation["replacement_counts"], forced_keep_counts=allocation["forced_keep_counts"],
        neural_model_loads=0, neural_forward_calls=0, saved_artifacts_loaded=dict(upstream_estimators=7, v2_ensemble_bundles=1, fixed_parameter_heads=5))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--stage", choices=("base", "gbv", "policies"), required=True)
    parser.add_argument("--runtime-manifest-sha256", required=True)
    parser.add_argument("--gpu-manifest-sha256", required=True)
    parser.add_argument("--base-manifest-sha256")
    parser.add_argument("--gbv-manifest-sha256")
    args = parser.parse_args()
    pins = dict(runtime=args.runtime_manifest_sha256, gpu_preflight=args.gpu_manifest_sha256)
    if args.base_manifest_sha256 is not None: pins["base"] = args.base_manifest_sha256
    if args.gbv_manifest_sha256 is not None: pins["gbv"] = args.gbv_manifest_sha256
    run = StageRun(args.project_root, args.stage, pins)
    handles, success = [], False
    run.active_counter = None
    try:
        run.prepare()
        wrapper, native, v2, eligibility, _, nodes = native_scoring(run.root)
        run.result["native_ast_nodes"] = nodes
        if args.stage != "policies": native.configure_determinism(20260828)
        if args.stage == "base": base_stage(run, wrapper, native, v2, eligibility, handles)
        elif args.stage == "gbv": gbv_stage(run, wrapper, eligibility, handles)
        else: policies_stage(run, wrapper, native, v2, eligibility)
        success = True
    except Exception as exc:
        run.error(exc)
        if run.active_counter is not None:
            run.result["failed_stage_actual_forward_counts"] = run.active_counter.summary()
    finally:
        for item in reversed(handles): item.close()
        handles.clear()
        item = None
        gc.collect()
    return run.finish(EXPECTED_STATUS[args.stage] if success else None)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
