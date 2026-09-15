"""Complete independent prelabel acceptance; tokenizers and saved CPU heads only."""
import argparse
from collections import Counter
from pathlib import Path
import sys

from scripts.empirical_scoring_stage_run import StageRun
from scripts.empirical_scoring_stage_io import STAGES, RUNTIME, PREPARATION, DATASETS, read_rows, EXPECTED_STATUS
from scripts.empirical_pool_io import load
from scripts.empirical_neural_checks import Checks, key
from scripts.empirical_scoring_stage_independent import bound_trace, JournalValidation, actual_counter
from scripts.empirical_feature_independent import pair_eligibility
from scripts.empirical_semantic_independent import validate_semantics
from scripts.empirical_likelihood_independent import LikelihoodValidation
from scripts.empirical_gbv_independent import GbVValidation
from scripts.empirical_policy_independent import validate_policies
from scripts.empirical_scoring_import_v2 import native_scoring
from scripts.empirical_scoring_io import saved_models


def restore_independently(context, audit):
    streams = [read_rows(RUNTIME / name) for name in
        ("canonical_branches.jsonl", "branch_provenance.jsonl", "repair_bindings.jsonl")]
    prepared = read_rows(PREPARATION / "TRACE_MANIFEST_PRIVATE.jsonl")
    traces = [bound_trace(branch, provenance, binding, repair, context, i, audit)
        for i, (branch, provenance, repair, binding) in enumerate(zip(*streams, prepared, strict=True))]
    audit.require(len(traces) == len({key(t) for t in traces}) == 18000, "full unique independent trace reconstruction")
    questions = {}
    for trace in traces:
        k = trace["dataset"], trace["sample_id"]
        if k in questions:
            audit.exact(trace["question"], questions[k], "three retriever siblings share question text")
        else:
            questions[k] = trace["question"]
    audit.exact(len(questions), 6000, "complete 6000-question independent coverage")
    audit.exact(sorted(Counter((t["dataset"], t["retriever"]) for t in traces).items()),
        sorted(((d, r), 2000) for d in DATASETS for r in ("bm25", "dense", "hybrid")), "nine complete frozen strata")
    return traces


def tokenizers(root, pre, audit):
    """Load only authenticated tokenizers; no model constructor or new model cache."""
    from transformers import AutoTokenizer
    cache = root / "data/models/huggingface"
    dense, reader = pre["phase3_config"]["dense"], pre["historical_config"]["reader_scorer"]
    audit.exact([dense["model_name"], dense["revision"], dense["max_length"], dense["batch_size"]],
        ["BAAI/bge-base-en-v1.5", "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a", 512, 16], "fixed BGE tokenizer configuration")
    audit.exact([reader["model_name"], reader["revision"], reader["max_length"], reader["batch_size"], reader["context_budget_characters"]],
        ["Qwen/Qwen2.5-3B-Instruct", "aa8e72537993ba99e69dfaafa59ed015b17504d1", 8192, 1, 16000], "fixed Qwen tokenizer configuration")
    bge = AutoTokenizer.from_pretrained(dense["model_name"], revision=dense["revision"], cache_dir=cache, local_files_only=True)
    qwen = AutoTokenizer.from_pretrained(reader["model_name"], revision=reader["revision"], cache_dir=cache, local_files_only=True)
    nli_path = root / "outputs/published_baseline_gbv_nli_v1/infrastructure/model_snapshot"
    nli = AutoTokenizer.from_pretrained(nli_path, use_fast=False, local_files_only=True)
    nli_config = load(nli_path / "config.json")
    audit.require(not nli.is_fast and type(nli).__name__ == "DebertaV2Tokenizer", "original slow NLI tokenizer")
    limits = [v for v in (nli.model_max_length, nli_config.get("max_position_embeddings"))
        if isinstance(v, int) and 0 < v < 1000000]
    audit.exact(min(limits), 512, "original effective NLI context")
    return bge, qwen, nli, nli_config


def semantics(traces, tokenizer, receipt, audit):
    import numpy as np
    reports, ordinal, tokens = {}, 1, 0
    for dataset in DATASETS:
        selected = [t for t in traces if t["dataset"] == dataset]
        folder = STAGES["base"] / "semantic"
        vectors = np.load(folder / (dataset + ".npy"), allow_pickle=False)
        rows = list(read_rows(folder / (dataset + ".jsonl")))
        batches = load(folder / (dataset + "_batches.json"))
        report = validate_semantics(tokenizer, selected, vectors, rows, batches, first_forward=ordinal)
        ordinal = report["next_forward"]
        tokens += sum(len(ids) for batch in batches for ids in batch["token_fields"]["input_ids"])
        for trace, row in zip(selected, rows, strict=True):
            trace["answer_semantic_agreement"] = row["answer_semantic_agreement"]
        reports[dataset] = report
    audit.exact(ordinal, 2251, "2250 answer-embedding forwards for all traces")
    actual_counter(audit, receipt["bge"]["actual"], calls=2250, rows=36000, tokens=tokens)
    return reports


def validate(run):
    from threadpoolctl import threadpool_limits
    a = Checks()
    run.phase["stage"] = "independent_C3_bindings"
    traces = restore_independently(run.context, a)
    bge, qwen, nli, nli_config = tokenizers(run.root, run.pre, a)
    base_receipt = load(STAGES["base"] / "BUILD_RECEIPT.json")
    gbv_receipt = load(STAGES["gbv"] / "BUILD_RECEIPT.json")
    policy_receipt = load(STAGES["policies"] / "BUILD_RECEIPT.json")
    for receipt in (base_receipt, gbv_receipt, policy_receipt):
        a.exact(receipt["trace_count"], 18000, "full scoring trace count")
        a.exact(receipt["completed_traces"], 18000, "complete scoring pass")
        for field in ("scientific_fit_calls", "answer_generation_calls", "new_retrieval_calls", "fresh_gold_values_materialized"):
            a.exact(receipt[field], 0, "zero forbidden scoring operation")
        a.exact(receipt["execution_boundary"]["denied"], [], "clean completed stage boundary")
    run.phase["stage"] = "independent_all_answer_semantics"
    semantic = semantics(traces, bge, base_receipt, a)
    qmeta = base_receipt["qwen"]["metadata"]
    for field, wanted in dict(resolved_revision="aa8e72537993ba99e69dfaafa59ed015b17504d1", dtype="torch.bfloat16",
        device="cuda:0", batch_size=1, max_length=8192, prompt_masking="answer_tokens_only").items():
        a.exact(qmeta[field], wanted, "native Qwen metadata")
    bmeta = base_receipt["bge"]["metadata"]
    for field, wanted in dict(resolved_revision="a5beb1e3e68b9ab74eb54cfd186867f64f240e1a", actual_dtype="torch.bfloat16",
        device="cuda:0", pooling="cls", normalize=True, index_backend="numpy_exact").items():
        a.exact(bmeta[field], wanted, "native BGE metadata")
    nmeta = gbv_receipt["gbv"]
    a.exact(nmeta["id2label"], nli_config["id2label"], "native NLI label direction")
    a.exact([nmeta["revision"], nmeta["dtype"], nmeta["effective_max_length"]],
        ["5a4338ab2151dc8db04ad53b42b6153382bf4f99", "torch.float32", 512], "native NLI metadata")
    likelihood = LikelihoodValidation(qwen, (run.root / "prompts/baseline_v1.txt").read_text(encoding="utf-8"), qmeta["resolved_revision"])
    gbv = GbVValidation(nli, nli_config["id2label"])
    journals = JournalValidation(read_rows(STAGES["base"] / "likelihood_forwards.jsonl"),
        read_rows(STAGES["gbv"] / "nli_forwards.jsonl"), read_rows(STAGES["gbv"] / "nli_branches.jsonl"))
    base_rows = list(read_rows(STAGES["base"] / "scores.jsonl"))
    gbv_rows = list(read_rows(STAGES["gbv"] / "scores.jsonl"))
    run.phase["stage"] = "independent_all_likelihood_and_NLI_witnesses"
    for i, (trace, base, nrecord) in enumerate(zip(traces, base_rows, gbv_rows, strict=True)):
        run.phase["position"] = i
        journals.base(trace, base, i, likelihood)
        journals.gbv(trace, nrecord, i, gbv)
        if (i + 1) % 100 == 0:
            print("C4_INDEPENDENT_TRACES", i + 1, 18000, flush=True)
    journal_summary = journals.finish()
    native_count = sum(pair_eligibility(t["a0"], t["a1"])[0] for t in traces)
    common_count = sum(row["eligible"] for row in gbv_rows)
    a.exact(base_receipt["native_eligible_traces"], native_count, "full native eligibility count")
    a.exact(gbv_receipt["native_eligible_traces"], native_count, "native NLI eligibility count")
    a.exact(gbv_receipt["common_eligible_traces"], common_count, "complete common eligibility count")
    a.exact(likelihood.requests, native_count * 4, "four cells for every native eligible trace")
    a.exact(base_receipt["likelihood_cell_requests"], likelihood.requests, "likelihood request receipt")
    for field, value in dict(sequences_computed=likelihood.forwards, cache_hits=likelihood.hits,
        computed_prompt_tokens=likelihood.prompt_tokens, computed_answer_tokens=likelihood.answer_tokens).items():
        a.exact(base_receipt["qwen"][field], value, "complete likelihood compute/cache receipt")
    a.exact(journal_summary["likelihood_forwards"], likelihood.forwards, "likelihood journal closure")
    actual_counter(a, base_receipt["qwen"]["actual"], calls=likelihood.forwards, rows=likelihood.forwards,
        tokens=likelihood.prompt_tokens + likelihood.answer_tokens)
    a.exact(journal_summary["likelihood_input_tokens"], likelihood.prompt_tokens + likelihood.answer_tokens, "likelihood journal token closure")
    a.exact(journal_summary["nli_forwards"], gbv.forwards, "NLI journal forward closure")
    a.exact(journal_summary["completed_nli_branches"], gbv.branches, "NLI journal branch closure")
    a.exact(gbv_receipt["completed_branches"], gbv.branches, "NLI completed branch receipt")
    a.exact(gbv_receipt["attempted_branches"], sum(r["attempted_branches"] for r in gbv_rows), "all attempted NLI branches including failure")
    a.exact(journal_summary["nli_input_rows"], gbv.pairs, "NLI pair coverage")
    actual_counter(a, gbv_receipt["gbv"]["actual"], calls=gbv.forwards, rows=gbv.pairs,
        tokens=journal_summary["nli_input_tokens_including_padding"])
    for rows, receipt in ((base_rows, base_receipt), (gbv_rows, gbv_receipt)):
        a.exact(receipt["forced_keep_counts"], dict(Counter(r["forced_keep_reason"] for r in rows if not r["eligible"])), "all forced-keep reasons")
    run.phase["stage"] = "independent_saved_head_and_all_action_replay"
    _, native, v2, _, _, nodes = native_scoring(run.root)
    models, bundle, panel = saved_models(run.root, native, v2)
    allocation = load(STAGES["policies"] / "POLICIES.json")
    a.exact(list(read_rows(STAGES["policies"] / "actions.jsonl")), allocation["ledger"], "complete duplicate action-file equality")
    selected = allocation["selected"]
    a.require(type(selected) is dict and all(type(v) is list and all(type(k) is list and len(k) == 3 for k in v)
        and v == sorted(v) and len(v) == len({tuple(k) for k in v}) for v in selected.values()), "canonical unique serialized memberships")
    allocation = {**allocation, "selected": {name: {tuple(k) for k in values} for name, values in selected.items()}}
    with threadpool_limits(limits=1):
        policies = validate_policies(traces, base_rows, gbv_rows, allocation, models, native.ordinary.ORDINARY_NAMES, bundle, panel)
    for field in ("N_all", "N_eligible", "cap", "replacement_counts", "forced_keep_counts"):
        a.exact(policy_receipt[field], allocation[field], "complete policy receipt")
    a.exact(allocation["N_all"], 18000, "full policy denominator")
    a.exact(allocation["cap"], 900, "fixed global five-percent cap")
    a.exact(allocation["N_eligible"], common_count, "shared nine-policy mask")
    a.exact(policy_receipt["neural_model_loads"], 0, "CPU-only policy models")
    a.exact(policy_receipt["neural_forward_calls"], 0, "CPU-only policy actions")
    a.exact(base_receipt["execution_boundary"]["top_level_forward_calls"],
        {**{"BertModel": 2250}, **({"Qwen2ForCausalLM": likelihood.forwards} if likelihood.forwards else {})}, "independently profiled base forward counts")
    a.exact(gbv_receipt["execution_boundary"]["top_level_forward_calls"],
        {"DebertaV2ForSequenceClassification": gbv.forwards} if gbv.forwards else {}, "independently profiled NLI forward counts")
    for receipt in (policy_receipt["execution_boundary"], run.boundary):
        a.exact(receipt["top_level_forward_calls"], {}, "no CPU-stage neural forwards")
        a.exact(receipt["call_counts"].get("neural_forward", 0), 0, "no CPU-stage nested neural forwards")
    report = dict(status=EXPECTED_STATUS["independent"], cas_q2_status="NOT READY", traces=18000, questions=6000,
        checks=a.count, native_eligible_traces=native_count, common_eligible_traces=common_count, cap=900,
        answer_semantics=semantic, likelihood=likelihood.summary(), gbv=gbv.summary(), journals=journal_summary,
        policies=policies, native_saved_class_definitions=nodes, predecessor_manifests=run.pins,
        model_forward_calls=0, neural_model_loads=0, scientific_fit_calls=0, fresh_gold_values_materialized=0,
        limitations=["Saved neural witnesses are validated; no second full model-forward replay is claimed.",
            "HGB predict_proba is shared with its authenticated saved estimator.", "No Gold outcomes or quality claim; readiness remains NOT READY."])
    run.result.update(trace_count=18000, completed_traces=18000, neural_model_loads=0, neural_forward_calls=0,
        native_eligible_traces=native_count, common_eligible_traces=common_count, numeric_checks=policies["numeric_checks"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    for name in ("runtime", "gpu", "base", "gbv", "policies"):
        parser.add_argument("--" + name + "-manifest-sha256", required=True)
    args = parser.parse_args()
    pins = {name: getattr(args, ("gpu" if name == "gpu_preflight" else name) + "_manifest_sha256")
        for name in ("runtime", "gpu_preflight", "base", "gbv", "policies")}
    run = StageRun(args.project_root, "independent", pins)
    accepted = None
    try:
        run.prepare()
        accepted = validate(run)
    except Exception as exc:
        run.error(exc)
    return run.finish(EXPECTED_STATUS["independent"] if accepted is not None else None, acceptance=accepted)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
