"""Receipt-only cost accounting; no answers, labels or model computation."""
from collections import Counter, defaultdict
import math

from scripts.empirical_neural_checks import Checks

DATASETS = ("2wikimultihopqa", "hotpotqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
STAGES = ("a0", "repair_query", "a1")
POLICIES = ("Keep", "HGB", "GbV", "ROA-FULL", "ROA-NOGBV", "HGB_GBV_R", "HGB_ONLY_R", "GBV_ONLY_R", "V2")
IDENTITY = {"dataset", "retriever", "sample_id", "stage"}
COUNTERS = {"input_tokens", "output_tokens", "native_output_score_steps", "logical_generation_calls", "qwen_forward_calls"}
ARRAYS = {"input_token_ids", "attention_mask", "generated_token_ids"}
SKIPPED = {"prompt_sha256", "raw_text", "render", "parsed_text", "parser_fallback", "runtime_config_sha256"}
SCHEMA = IDENTITY | COUNTERS | ARRAYS | SKIPPED | {"position"}


def generation_projection(path, Cursor):
    """Skip text values at the authenticated byte cursor, retaining no token IDs."""
    audit = Checks()
    with path.open("rb") as stream:
        cursor = Cursor(stream)
        while True:
            cursor.skip_whitespace()
            if cursor.peek() is None:
                return
            cursor.expect(ord("{"), path="cost_row")
            seen, row = set(), {}
            while True:
                cursor.skip_whitespace()
                field = cursor.read_string(path="cost_key")
                audit.require(field in SCHEMA and field not in seen, "exact unique generation receipt field")
                seen.add(field)
                cursor.expect(ord(":"), path="cost_value")
                cursor.skip_whitespace()
                if field in IDENTITY:
                    row[field] = cursor.read_string(path="cost_identity")
                elif field in COUNTERS or field == "position":
                    row[field] = cursor.read_integer(path="cost_integer")
                elif field in ARRAYS:
                    cursor.expect(ord("["), path="cost_integer_array")
                    count = total = 0
                    while True:
                        cursor.skip_whitespace()
                        if cursor.peek() == ord("]"):
                            cursor.take()
                            break
                        value = cursor.read_integer(path="cost_array_integer")
                        audit.require(value >= 0 and (field != "attention_mask" or value in (0, 1)), "nonnegative token IDs or binary mask")
                        count += 1
                        if field == "attention_mask": total += value
                        cursor.skip_whitespace()
                        if cursor.peek() == ord("]"):
                            cursor.take()
                            break
                        cursor.expect(ord(","), path="cost_array_separator")
                        cursor.skip_whitespace()
                        audit.require(cursor.peek() != ord("]"), "no trailing array comma")
                    row[field + "_length"] = count
                    if field == "attention_mask": row["attention_mask_sum"] = total
                else:
                    cursor.skip_value(path="unneeded_generation_text_or_metadata")
                cursor.skip_whitespace()
                if cursor.peek() == ord("}"):
                    cursor.take()
                    break
                cursor.expect(ord(","), path="cost_row_separator")
            audit.exact(sorted(seen), sorted(SCHEMA), "complete generation receipt schema")
            yield row


def generation_cost(rows, build, independent, *, questions_per_stratum):
    """Reconcile every receipt for a canonical or bounded verification pass."""
    a = Checks()
    a.require(type(questions_per_stratum) is int and questions_per_stratum > 0, "positive fixed pass size")
    totals, cells, strata = defaultdict(Counter), defaultdict(Counter), Counter()
    seen, positions, active = set(), set(), None
    count = 0
    for row in rows:
        a.schema(row, IDENTITY | COUNTERS | {"position", "input_token_ids_length", "generated_token_ids_length", "attention_mask_length", "attention_mask_sum"}, "numeric generation projection")
        ds, retriever, sid, stage = (row[k] for k in ("dataset", "retriever", "sample_id", "stage"))
        a.require(ds in DATASETS and retriever in RETRIEVERS and type(sid) is str and bool(sid), "fixed receipt identities")
        a.exact(stage, STAGES[count % 3], "native generation stage order")
        key = ds, retriever, sid
        a.require(all(type(row[k]) is int and row[k] >= 0 for k in set(row) - IDENTITY), "integer nonnegative cost counters")
        if count % 3 == 0:
            a.require(key not in seen and row["position"] not in positions, "unique trace and position")
            seen.add(key); positions.add(row["position"])
            active = key, row["position"]
            strata[(ds, retriever)] += 1
        a.exact([list(key), row["position"]], [list(active[0]), active[1]], "three stages share trace and position")
        a.exact(row["logical_generation_calls"], 1, "one logical call per receipt")
        a.exact(row["input_tokens"], row["attention_mask_sum"], "native prompt token sum")
        a.exact(row["input_token_ids_length"], row["attention_mask_length"], "input token/mask length")
        a.exact(row["qwen_forward_calls"], row["native_output_score_steps"], "each generated score step counts a forward")
        a.require(0 < row["input_tokens"] <= row["input_token_ids_length"] and
            0 <= row["output_tokens"] <= row["native_output_score_steps"] <= row["generated_token_ids_length"], "generation token bounds")
        for bucket in (totals[stage], cells[(ds, retriever, stage)]):
            bucket["receipts"] += 1
            for name in sorted(COUNTERS): bucket[name] += row[name]
        count += 1
    expected = questions_per_stratum * 9
    a.exact(count, expected * 3, "complete generation receipts")
    a.exact(sorted(strata.items()), sorted(((ds, r), questions_per_stratum) for ds in DATASETS for r in RETRIEVERS), "nine complete pass strata")
    a.exact(build["completed_traces"], expected, "complete executed pass")
    a.exact(independent["trace_count"], expected, "complete independently accepted pass")
    counters = build["execution_counters"]
    a.exact(counters, independent["counters"], "independently accepted complete counter closure")
    for stage in STAGES:
        a.exact(totals[stage]["receipts"], expected, "complete stage receipts")
        for suffix in ("generation_calls", "generation_completed"):
            a.exact(counters[stage + "_" + suffix], expected, "actual generation counter")
        a.exact(counters[stage + "_forward_calls"], totals[stage]["qwen_forward_calls"], "actual per-stage forward counter")
    a.exact(counters["qwen_forward_calls"], sum(v["qwen_forward_calls"] for v in totals.values()), "total Qwen forward count")
    for field, value in dict(repair_retrieval_calls=expected, repair_retrieval_completed=expected,
        repair_query_embedding_calls=expected*2//3, bge_query_forward_calls=expected*2//3,
        **{"repair_" + r + "_calls": expected//3 for r in RETRIEVERS}).items():
        a.exact(counters[field], value, "actual repair retrieval counts")
    for field in ("scientific_fit_calls", "fresh_gold_values_materialized", "original_question_retrieval_calls", "document_embedding_calls", "bm25_structure_rebuild_calls", "generation_failure_count", "repair_failure_count"):
        a.exact(build[field], 0, "no hidden pass computation or failure")
    return dict(checks=a.count, traces=expected, generation_by_stage=dict(totals),
        generation_by_cell=[dict(dataset=d, retriever=r, stage=s, counters=dict(cells[(d,r,s)])) for d in DATASETS for r in RETRIEVERS for s in STAGES],
        logical_repair_retrievals=expected, bm25_component_calls=expected*2//3, dense_component_calls=expected*2//3,
        bge_query_forwards=expected*2//3, document_reembedding_forwards=0,
        new_raw_or_parsed_answer_strings_decoded=0)


def retrieval_cost(build):
    a = Checks()
    expected = dict(bm25_structure_builds=3, embedding_document_rows=54716, embedding_forward_documents=3422,
        embedding_query_rows=12000, embedding_forward_queries=12000, embedding_forward_calls=15422,
        original_retrieval_calls=18000, original_bm25_calls=6000, original_dense_calls=6000, original_hybrid_calls=6000)
    a.exact(build["execution_counters"], expected, "full original retrieval accounting")
    a.exact(sum(v["pool_documents"] for v in build["datasets"].values()), 54716, "shared document pool sizes")
    a.require(all(v["questions"] == 2000 and v["traces"] == 6000 for v in build["datasets"].values()), "complete retrieval dataset counts")
    return dict(checks=a.count, execution_counters=expected, bm25_component_calls=12000, dense_component_calls=12000,
        note="Hybrid includes one BM25 and one dense component; logical requests are not component counts.")


def scoring_cost(base, gbv, policy, independent):
    a = Checks()
    a.exact(independent["traces"], 18000, "complete independently accepted scoring")
    native, common = independent["native_eligible_traces"], independent["common_eligible_traces"]
    a.require(type(native) is int and type(common) is int and 0 <= common <= native <= 18000, "common and native populations")
    a.exact(base["native_eligible_traces"], native, "native score population")
    a.exact(gbv["common_eligible_traces"], common, "common score population")
    semantic = independent["answer_semantics"]
    a.exact(sorted(semantic), sorted(DATASETS), "all answer-embedding datasets")
    a.exact(sum(v["answer_texts"] for v in semantic.values()), 36000, "all answers before eligibility")
    a.exact(sum(v["forward_calls"] for v in semantic.values()), 2250, "all answer embedding batches")
    bge_actual = base["bge"]["actual"]
    a.exact([bge_actual["attempted_forward_calls"], bge_actual["attempted_input_rows"]], [2250, 36000], "actual semantic forwards and rows")
    likelihood, journal, nli = independent["likelihood"], independent["journals"], independent["gbv"]
    qwen = base["qwen"]
    a.exact(base["likelihood_cell_requests"], 4*native, "all four-cell requests")
    a.exact(likelihood["cell_requests"], 4*native, "independent requests")
    a.exact(qwen["sequences_computed"] + qwen["cache_hits"], 4*native, "requests equal computed plus cached")
    for k, source in (("forward_calls", "sequences_computed"), ("cache_hits", "cache_hits"),
        ("computed_prompt_tokens", "computed_prompt_tokens"), ("computed_answer_tokens", "computed_answer_tokens")):
        a.exact(likelihood[k], qwen[source], "independent native likelihood counters")
    qwen_tokens = likelihood["computed_prompt_tokens"] + likelihood["computed_answer_tokens"]
    a.exact(journal["likelihood_input_tokens"], qwen_tokens, "complete likelihood token journal")
    a.exact(journal["likelihood_forwards"], likelihood["forward_calls"], "complete likelihood forward journal")
    for actual, calls, rows, tokens in ((qwen["actual"], likelihood["forward_calls"], likelihood["forward_calls"], qwen_tokens),
        (gbv["gbv"]["actual"], nli["forward_calls"], nli["nli_pairs"], journal["nli_input_tokens_including_padding"])):
        a.exact([actual["attempted_forward_calls"], actual["attempted_input_rows"], actual["attempted_input_tokens_including_padding"]],
            [calls, rows, tokens], "actual top-level neural counters against complete journals")
    for field, source in (("nli_forwards", "forward_calls"), ("nli_input_rows", "nli_pairs"), ("completed_nli_branches", "completed_branches")):
        a.exact(journal[field], nli[source], "complete NLI journal closure")
    a.exact(gbv["completed_branches"], nli["completed_branches"], "all completed NLI work, including failed-pair first branches")
    a.exact(nli["deterministic_unscorable_pairs"], native-common, "only deterministic preparation failures extend mask")
    a.exact(gbv["attempted_branches"]-gbv["completed_branches"], native-common, "every deterministic failing branch counted")
    a.exact([policy["N_all"], policy["N_eligible"], policy["cap"]], [18000, common, 900], "complete global action budget")
    a.exact(policy["replacement_counts"], {p: 0 if p == "Keep" else min(common,900) for p in POLICIES}, "all nine fixed-policy allocations")
    a.exact([policy["neural_model_loads"], policy["neural_forward_calls"]], [0,0], "CPU-only allocation")
    return dict(checks=a.count, native_eligible_traces=native, common_eligible_traces=common,
        semantic_actual=bge_actual, likelihood={k:qwen[k] for k in ("actual","sequences_computed","cache_hits","computed_prompt_tokens","computed_answer_tokens")},
        likelihood_cell_requests=4*native, nli_actual=gbv["gbv"]["actual"], nli_pairs=nli["nli_pairs"],
        attempted_nli_branches=gbv["attempted_branches"], completed_nli_branches=gbv["completed_branches"],
        deterministic_unscorable_pairs=native-common, replacement_counts=policy["replacement_counts"],
        validation_scope="Cost reconciliation reuses the complete independently accepted C4 witness checks; no new neural replay.")


def timing(receipt, *, boundary, peak=False):
    elapsed = receipt.get("elapsed_seconds")
    if elapsed is not None and not (type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed >= 0):
        raise ValueError("Invalid saved stage time")
    value = receipt.get("peak_allocated_cuda_bytes") if peak else None
    if value is not None and not (type(value) is int and value >= 0):
        raise ValueError("Invalid saved allocator peak")
    return dict(elapsed_seconds=elapsed, cuda_allocator_peak_bytes=value, timing_boundary=boundary,
        missing_measurements=[name for name, item in (("elapsed_seconds",elapsed),("cuda_allocator_peak_bytes",value)) if item is None])
