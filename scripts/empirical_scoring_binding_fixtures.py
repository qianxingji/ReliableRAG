"""Invented-only C3-shaped records for adapter tests; never benchmark substitutes."""
from dataclasses import asdict, dataclass

from scripts.empirical_runtime_contract import sha_json
from scripts.empirical_scoring_bindings import text_sha
from scripts.empirical_scoring_fixtures import invented_trace, invented_cells

POOL_SHA = "a" * 64
CONFIG_SHA = "b" * 64


def invented_bound_rows(index=0, retriever="bm25", dataset="hotpotqa", answers=None):
    trace = invented_trace(index, retriever)
    trace["dataset"] = dataset
    if answers is not None:
        trace["a0"], trace["a1"] = answers
    keys = {k: trace[k] for k in ("dataset", "retriever", "sample_id")}
    branch = {**keys, **{k: trace[k] for k in ("question", "a0", "a1")},
        "evidence0": [r["text"] for r in trace["E0"]], "evidence1": [r["text"] for r in trace["E1"]]}
    def evidence(name):
        return [{**{k: v for k, v in r.items() if k != "score"}, "retrieval_score": r["score"]} for r in trace[name]]
    ids0, ids1 = [[r["document_id"] for r in trace[state]] for state in ("E0", "E1")]
    top_hash = sha_json(dict(**keys, document_ids=ids0))
    prepared = dict(**keys, position=index, original_top5_ids=ids0, original_top5_row_sha256=top_hash)
    ranked = [dict(document_id=ids1[4], rank=1, score=trace["E1"][4]["score"])]
    repair = dict(**keys, position=index, query_sha256=text_sha("invented query"), ranking=ranked,
        component_rankings={retriever: ranked}, dense_query_vector=None, e0_ids=ids0, e1_ids=ids1,
        inserted_document_id=ids1[4], inserted_candidate_rank=1, replaced_document_id=ids0[4],
        replacement_position_zero_based=4, requested_depth=50, repair_retrieval_calls=1,
        pool_sha256=POOL_SHA, fail_closed_reason=None)
    provenance = dict(**keys, position=index, original_top5_row_sha256=top_hash,
        e0=evidence("E0"), e1=evidence("E1"), question_sha256=text_sha(branch["question"]),
        canonical_row_sha256=sha_json(branch), runtime_config_sha256=CONFIG_SHA,
        repair_binding_row_sha256=sha_json(repair), pool_sha256=POOL_SHA)
    return branch, provenance, prepared, repair


class InventedLikelihood:
    """Static likelihood values for CPU downstream integration, zero forwards."""
    def __init__(self, native, index=0):
        self.native = native
        self.index = index

    def score(self, items):
        results = []
        for i, cell in enumerate(invented_cells(self.index).values()):
            result = self.native.likelihood.ReaderLikelihoodResult(
                sum_log_probability=cell["mean_log_probability"], mean_log_probability=cell["mean_log_probability"],
                minimum_log_probability=cell["mean_log_probability"], answer_token_count=1, prompt_token_count=1,
                truncation=False, prompt_sha256=text_sha("invented prompt"), model_revision="invented-no-model",
                ordered_evidence_ids=tuple(r["document_id"] for r in items[i]["evidence"]),
                ordered_evidence_hash=sha_json(items[i]["evidence"]), answer_sha256=text_sha(items[i]["answer"]),
                cache_key=text_sha("invented-cell-" + str(i)), cache_hit=False, latency_seconds=0.)
            results.append(result)
        return results, [dict(cell_position=i, native_result=asdict(r), invented_only=True) for i, r in enumerate(results)], []


@dataclass
class InventedBranchScore:
    score: float
    premise_count: int = 5
    chunk_count: int = 5


class InventedGbV:
    """Static invented probabilities; forward_count truthfully stays zero."""
    def __init__(self, fail_second=False):
        self.forward_count = 0
        self.calls = 0
        self.fail_second = fail_second

    def score_branch(self, question, answer, evidence):
        state = self.calls
        self.calls += 1
        if state == 1 and self.fail_second:
            raise ValueError("hypothesis does not fit the NLI context window")
        return InventedBranchScore(.25 if state == 0 else .75), dict(invented_only=True, actual_neural_forwards=0)
