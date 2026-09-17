"""Independent C3-to-C4 binding reconstruction and complete journal consumption.

No scoring executor, native witness, trace adapter or policy allocator is imported.
The accepted C3 validator separately verifies retrieval/generation derivations.
"""
import re

from scripts.empirical_neural_checks import Checks, key, object_sha, text_sha
from scripts.empirical_feature_independent import pair_eligibility

IDENTITY = {"dataset", "retriever", "sample_id"}
BASE_FIELDS = IDENTITY | {"eligible", "forced_keep_reason", "scores", "cells", "pair", "requests", "forward_witnesses"}


def bound_trace(branch, provenance, prepared, repair, context, position, audit):
    """Reconstruct native E0/E1 directly from authenticated full C3 rows."""
    a = audit
    a.schema(branch, IDENTITY | {"question", "a0", "a1", "evidence0", "evidence1"}, "C3 branch")
    a.schema(prepared, IDENTITY | {"position", "original_top5_ids", "original_top5_row_sha256"}, "C3 prepared row")
    a.schema(provenance, IDENTITY | {"position", "original_top5_row_sha256", "e0", "e1", "question_sha256",
        "canonical_row_sha256", "runtime_config_sha256", "repair_binding_row_sha256", "pool_sha256"}, "C3 provenance")
    a.schema(repair, IDENTITY | {"position", "query_sha256", "ranking", "component_rankings", "dense_query_vector",
        "e0_ids", "e1_ids", "inserted_document_id", "inserted_candidate_rank", "replaced_document_id",
        "replacement_position_zero_based", "requested_depth", "repair_retrieval_calls", "pool_sha256", "fail_closed_reason"}, "C3 repair")
    a.require(all(type(branch[k]) is str and branch[k] for k in IDENTITY), "nonempty C3 identity")
    a.require(branch["dataset"] in ("hotpotqa", "2wikimultihopqa", "musique") and
        branch["retriever"] in ("bm25", "dense", "hybrid"), "fixed C3 stratum")
    for row in (prepared, provenance, repair):
        a.exact(key(row), key(branch), "aligned C3 identities")
        a.exact(row["position"], position, "exact C3 canonical position")
    a.require(all(type(branch[k]) is str for k in ("question", "a0", "a1")), "unmodified C3 strings")
    a.exact(provenance["canonical_row_sha256"], object_sha(branch), "C3 full branch digest")
    a.exact(provenance["question_sha256"], text_sha(branch["question"]), "C3 question digest")
    a.exact(provenance["repair_binding_row_sha256"], object_sha(repair), "C3 repair digest")
    a.exact(provenance["runtime_config_sha256"], context["runtime_config_sha"], "frozen C3 runtime config")
    for row in (provenance, repair):
        a.exact(row["pool_sha256"], context["pool_sha"][branch["dataset"]], "frozen C3 pool")
    trace = {k: branch[k] for k in (*sorted(IDENTITY), "question", "a0", "a1")}
    trace["split"] = "fresh_confirmatory"
    for source, texts, target in (("e0", "evidence0", "E0"), ("e1", "evidence1", "E1")):
        entries = provenance[source]
        a.require(type(entries) is list and type(branch[texts]) is list and len(entries) == len(branch[texts]) == 5, "five complete passages")
        result = []
        for i, (entry, text) in enumerate(zip(entries, branch[texts], strict=True)):
            a.schema(entry, {"rank", "document_id", "content_hash", "retrieval_score", "title", "text"}, "C3 full passage")
            a.exact(entry["rank"], i + 1, "C3 passage rank")
            a.require(all(type(entry[k]) is str for k in ("document_id", "content_hash", "title", "text")), "C3 passage strings")
            a.require(bool(entry["document_id"]) and bool(re.fullmatch("[0-9a-f]{64}", entry["content_hash"])), "C3 document/content identity")
            a.finite(entry["retrieval_score"], "C3 finite retrieval score")
            a.exact(entry["text"], text, "C3 exact passage string")
            result.append(dict(rank=i + 1, document_id=entry["document_id"], content_hash=entry["content_hash"],
                title=entry["title"], text=text, score=entry["retrieval_score"]))
        a.require(len({r["document_id"] for r in result}) == 5, "distinct C3 evidence identities")
        trace[target] = result
    ids0, ids1 = [[r["document_id"] for r in trace[s]] for s in ("E0", "E1")]
    a.exact(ids0, prepared["original_top5_ids"], "original C3 evidence IDs")
    a.exact(ids0, repair["e0_ids"], "C3 E0 repair IDs")
    a.exact(ids1, repair["e1_ids"], "C3 E1 repair IDs")
    original_sha = object_sha({**{k: branch[k] for k in IDENTITY}, "document_ids": ids0})
    for row in (prepared, provenance):
        a.exact(row["original_top5_row_sha256"], original_sha, "C3 Top-5 digest")
    a.exact(trace["E0"][:4], trace["E1"][:4], "unchanged first four C3 passages")
    a.require(ids1[4] not in ids0, "novel fifth C3 passage")
    for field, value in dict(inserted_document_id=ids1[4], replaced_document_id=ids0[4],
        replacement_position_zero_based=4, requested_depth=50, repair_retrieval_calls=1, fail_closed_reason=None).items():
        a.exact(repair[field], value, "C3 fixed repair operation")
    return trace


class JournalValidation:
    """Consume each durable forward/branch once, in exact canonical order."""
    def __init__(self, likelihood_rows, nli_rows, branch_rows):
        self.likelihood, self.nli, self.branches = map(iter, (likelihood_rows, nli_rows, branch_rows))
        self.audit = Checks()
        self.likelihood_count = self.nli_count = self.branch_count = 0
        self.likelihood_tokens = self.nli_tokens = self.nli_input_rows = 0

    def take(self, stream, trace, position, *, state=None):
        row = next(stream, None)
        a = self.audit
        a.require(row is not None, "no missing durable journal row")
        a.exact(key(row), key(trace), "journal trace identity")
        a.exact(row["position"], position, "journal canonical position")
        if state is not None:
            a.exact(row["state"], state, "journal NLI branch order")
        return row

    def base(self, trace, record, position, checker):
        a = self.audit
        a.schema(record, BASE_FIELDS, "complete base record schema")
        a.exact(key(record), key(trace), "base record trace order")
        eligible, reason = pair_eligibility(trace["a0"], trace["a1"])
        a.exact(record["eligible"], eligible, "independent native base eligibility")
        a.exact(record["forced_keep_reason"], reason, "independent native base reason")
        refs = record["forward_witnesses"]
        a.require(type(refs) is list, "explicit base forward references")
        witnesses = []
        for ref in refs:
            a.exact(ref, self.likelihood_count + 1, "contiguous likelihood reference")
            row = self.take(self.likelihood, trace, position)
            a.schema(row, IDENTITY | {"position", "witness"}, "durable likelihood schema")
            a.exact(row["witness"]["forward_ordinal"], ref, "exact durable likelihood reference")
            witnesses.append(row["witness"])
            self.likelihood_count += 1
            self.likelihood_tokens += len(row["witness"]["input_token_ids"])
        if eligible:
            checker.check(trace, record["cells"], record["requests"], witnesses)
        else:
            a.exact(refs, [], "no ineligible likelihood forwards")
            a.exact(record["requests"], [], "no ineligible likelihood requests")
            a.exact(record["cells"], None, "null ineligible likelihood cells")
            a.exact(record["pair"], None, "null ineligible native features")
            a.require(all(v is None for v in record["scores"].values()), "null ineligible base scores")

    def gbv(self, trace, record, position, checker):
        a = self.audit
        a.exact(key(record), key(trace), "GbV record trace order")
        completed = []
        a.require(type(record["completed_branches"]) is list, "explicit completed branch list")
        for observed in record["completed_branches"]:
            a.schema(observed, {"state", "result", "witness"}, "compact NLI branch schema")
            state = observed["state"]
            journal = self.take(self.branches, trace, position, state=state)
            a.schema(journal, IDENTITY | {"position", "state", "result", "witness"}, "durable completed branch schema")
            a.exact({k: journal[k] for k in observed}, observed, "score/durable completed branch equality")
            self.branch_count += 1
            batches = []
            refs = observed["witness"]["batches"]
            a.require(type(refs) is list, "explicit NLI batch references")
            for ref in refs:
                a.exact(ref, self.nli_count + 1, "contiguous NLI batch reference")
                row = self.take(self.nli, trace, position, state=state)
                a.schema(row, IDENTITY | {"position", "state", "witness"}, "durable NLI forward schema")
                batch = row["witness"]
                a.exact(batch["forward_ordinal"], ref, "exact durable NLI forward reference")
                batches.append(batch)
                self.nli_count += 1
                ids = batch["token_fields"]["input_ids"]
                self.nli_input_rows += len(ids)
                self.nli_tokens += sum(len(r) for r in ids)
            completed.append({**observed, "witness": {**observed["witness"], "batches": batches}})
        eligible, reason = pair_eligibility(trace["a0"], trace["a1"])
        checker.check_pair(trace, {**record, "completed_branches": completed}, native_eligible=eligible, native_reason=reason)

    def finish(self):
        for stream in (self.likelihood, self.nli, self.branches):
            self.audit.require(next(stream, None) is None, "no extra or orphan durable journal row")
        return dict(checks=self.audit.count, likelihood_forwards=self.likelihood_count, nli_forwards=self.nli_count,
            completed_nli_branches=self.branch_count, likelihood_input_tokens=self.likelihood_tokens,
            nli_input_rows=self.nli_input_rows, nli_input_tokens_including_padding=self.nli_tokens)


def actual_counter(audit, actual, *, calls, rows, tokens):
    audit.schema(actual, {"attempted_forward_calls", "attempted_input_rows", "attempted_input_tokens_including_padding", "devices"}, "actual pre-forward counter schema")
    audit.exact(actual["attempted_forward_calls"], calls, "all actual attempted forward calls")
    audit.exact(actual["attempted_input_rows"], rows, "all actual attempted input rows")
    audit.exact(actual["attempted_input_tokens_including_padding"], tokens, "all actual input tokens including padding")
    audit.exact(actual["devices"], ["cuda:0"] if calls else [], "actual single-GPU scoring devices")
