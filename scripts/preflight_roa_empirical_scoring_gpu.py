"""Single-use invented-only native BGE/Qwen/GbV scoring GPU preflight."""
import argparse
from dataclasses import asdict
import gc
from pathlib import Path
import sys

from scripts.empirical_scoring_stage_run import StageRun
from scripts.empirical_scoring_stage_io import EXPECTED_STATUS, require
from scripts.empirical_scoring_import_v2 import native_scoring
from scripts.empirical_scoring_models import make_bge, make_likelihood, make_gbv, stage_nli_cache
from scripts.empirical_semantic_witness import SemanticWitness
from scripts.empirical_likelihood_witness import LikelihoodWitness
from scripts.empirical_gbv_witness import GbVWitness
from scripts.empirical_semantic_independent import validate_semantics
from scripts.empirical_likelihood_independent import LikelihoodValidation
from scripts.empirical_gbv_independent import GbVValidation
from scripts.empirical_scoring_gpu_fixtures import semantic_traces, likelihood_traces, gbv_traces
from scripts.empirical_scoring_pipeline import score_gbv_trace
from scripts.empirical_scoring_journals import Ledger, ForwardCounter, ForwardJournal, DurableGbV, compact_gbv
from scripts.replay_roa_original import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--runtime-manifest-sha256", required=True)
    args = parser.parse_args()
    run = StageRun(args.project_root, "gpu_preflight", dict(runtime=args.runtime_manifest_sha256))
    resources, model, success = [], None, False
    try:
        run.prepare()
        import torch
        import numpy as np
        _, native, _, eligibility, _, nodes = native_scoring(run.root)
        native.configure_determinism(20260828)
        run.result["native_ast_nodes"] = nodes
        run.phase["stage"] = "invented_semantics"
        model = make_bge(native, run.root, run.out, run.pre)
        observer, counter = SemanticWitness(model), ForwardCounter(model.model)
        resources.extend([observer, counter])
        traces = semantic_traces()
        values, vectors, rows, batches = observer.score(native, traces)
        for trace, value in zip(traces, values, strict=True):
            trace["answer_semantic_agreement"] = value
        semantic_check = validate_semantics(model.tokenizer, traces, vectors, rows, batches)
        require(counter.calls == 2 and counter.rows == 22, "Two complete invented semantic batches")
        with (run.out / "invented_answer_vectors.npy").open("xb") as stream:
            np.save(stream, vectors, allow_pickle=False)
        write_json(run.out / "INVENTED_SEMANTICS.json", dict(traces=traces, rows=rows, batches=batches, validation=semantic_check))
        run.result["bge"] = dict(metadata=model.metadata, actual=counter.summary(), validation=semantic_check)
        counter.close(); observer.close(); resources.clear()
        model = None; observer = counter = None; gc.collect(); torch.cuda.empty_cache()

        run.phase["stage"] = "invented_likelihood"
        model = make_likelihood(native, run.root, run.out, run.pre)
        observer, counter = LikelihoodWitness(model), ForwardCounter(model.model)
        ledger = Ledger(run.out / "likelihood_forwards.jsonl")
        journal = ForwardJournal(model.model, observer, ledger, run.phase)
        resources.extend([observer, counter, ledger, journal])
        checker = LikelihoodValidation(model.tokenizer, model.answer_template, model.resolved_revision)
        observations = []
        short, long = likelihood_traces()
        for position, trace in enumerate((short, short, long)):
            run.phase.update({k: trace[k] for k in ("dataset", "retriever", "sample_id")})
            run.phase["position"] = position
            outputs, requests, forwards = observer.score(native.ordinary._score_items(trace))
            cells = {name: asdict(value) for name, value in zip(("L00", "L01", "L10", "L11"), outputs, strict=True)}
            checker.check(trace, cells, requests, forwards)
            observations.append(dict(trace=trace, cells=cells, requests=requests, forward_witnesses=[r["forward_ordinal"] for r in forwards]))
        require(counter.calls == model.calls == model.sequences_scored == checker.forwards == 8 and
            model.cache_hits == checker.hits == 4 and checker.requests == 12 and ledger.rows == 8, "Invented likelihood requests/computation/cache")
        require(all(c["prompt_token_count"] + c["answer_token_count"] == 8192 and c["truncation"] for c in observations[-1]["cells"].values()), "Invented long context exercises native token truncation")
        write_json(run.out / "INVENTED_LIKELIHOOD.json", dict(observations=observations, validation=checker.summary()))
        run.result["qwen"] = dict(metadata=model.metadata, actual=counter.summary(), validation=checker.summary())
        for item in reversed(resources): item.close()
        resources.clear(); model = observer = counter = journal = checker = item = None; gc.collect(); torch.cuda.empty_cache()

        run.phase["stage"] = "invented_gbv"
        run.result["nli_snapshot_copies"] = stage_nli_cache(run.root, run.out, run.pre)
        gbv_native, model = make_gbv(run.root, run.out)
        observer, counter = GbVWitness(model, gbv_native), ForwardCounter(model.model)
        ledger, branches = Ledger(run.out / "nli_forwards.jsonl"), Ledger(run.out / "nli_branches.jsonl")
        journal = ForwardJournal(model.model, observer, ledger, run.phase, nli=True)
        durable = DurableGbV(observer, branches, run.phase)
        resources.extend([observer, counter, ledger, branches, journal])
        checker = GbVValidation(model.tokenizer, model.model.config.id2label)
        observations = []
        for position, trace in enumerate(gbv_traces()):
            durable.begin(trace, position)
            record = score_gbv_trace(eligibility, trace, durable)
            checker.check_pair(trace, record, native_eligible=True, native_reason=None)
            observations.append(dict(trace=trace, record=compact_gbv(record)))
        require(checker.branches == branches.rows == 5 and checker.unscorable == 1 and
            checker.forwards == observer.forward_count == counter.calls == ledger.rows and checker.pairs == counter.rows, "Invented complete NLI branch/forward accounting")
        require(observations[-1]["record"]["failed_branch"] == "F1" and
            any(b["result"]["chunk_count"] > 5 for b in observations[1]["record"]["completed_branches"]), "NLI long-premise and second-hypothesis failure exercised")
        write_json(run.out / "INVENTED_GBV.json", dict(observations=observations, validation=checker.summary()))
        run.result["gbv"] = dict(revision=model.model.config._commit_hash, dtype=model.resolved_dtype,
            id2label=model.model.config.id2label, effective_max_length=model.max_length, actual=counter.summary(), validation=checker.summary())
        run.result.update(peak_allocated_cuda_bytes=torch.cuda.max_memory_allocated(),
            benchmark_branches_decoded=0, invented_only=True, limitation="Synthetic scoring compatibility and saved-witness checks; not full neural replay or fresh performance")
        success = True
    except Exception as exc:
        run.error(exc)
        if "counter" in locals() and counter is not None:
            run.result["failed_stage_actual_forward_counts"] = counter.summary()
    finally:
        for item in reversed(resources): item.close()
        resources.clear()
        model = item = None
        gc.collect()
    return run.finish(EXPECTED_STATUS["gpu_preflight"] if success else None)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
