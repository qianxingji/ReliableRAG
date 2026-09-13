"""Independent renderer, token/cache chronology and likelihood witness reductions."""
from scripts.empirical_neural_checks import Checks, object_sha, text_sha

CELL_ORDER = (("L00", "a0", "E0"), ("L01", "a0", "E1"), ("L10", "a1", "E0"), ("L11", "a1", "E1"))
RESULT_FIELDS = {"sum_log_probability", "mean_log_probability", "minimum_log_probability", "answer_token_count",
    "prompt_token_count", "truncation", "prompt_sha256", "model_revision", "ordered_evidence_ids",
    "ordered_evidence_hash", "answer_sha256", "cache_key", "cache_hit", "latency_seconds"}
WITNESS_FIELDS = {"forward_ordinal", "cache_key", "prompt_sha256", "answer_sha256", "evidence_hash", "input_token_ids",
    "attention_mask", "position_ids", "answer_token_ids", "answer_prediction_positions", "token_log_probabilities",
    "prompt_token_count", "answer_token_count", "truncation", "model_revision"}


def render(evidence, budget):
    """Reconstruct native order/headers/character budget without importing renderer."""
    context, truncated = "", False
    for entry in evidence:
        header = "[Evidence {} | id={} | title={}]\n".format(int(entry["rank"]), entry["document_id"], entry["title"])
        separator = "\n\n" if context else ""
        space = budget - len(context) - len(separator)
        if space <= len(header):
            truncated = True
            continue
        body = entry["text"].strip()
        limit = space - len(header)
        context += separator + header + body[:limit]
        truncated |= len(body) > limit
    return context, truncated


def prepare(tokenizer, template, revision, item, *, context_budget=16000, max_length=8192):
    context, cut = render(item["evidence"], context_budget)
    message = template.format(question=item["question"], evidence=context)
    prompt = tokenizer.apply_chat_template([dict(role="user", content=message)], tokenize=False, add_generation_prompt=True)
    prompt_ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    joined = list(tokenizer(prompt + item["answer"], add_special_tokens=False)["input_ids"])
    if not prompt_ids or joined[:len(prompt_ids)] != prompt_ids:
        raise ValueError("Independent witness: prompt/answer prefix alignment")
    answer_ids = joined[len(prompt_ids):]
    if not answer_ids:
        raise ValueError("Independent witness: empty answer tokens")
    token_cut = len(joined) > max_length
    if token_cut:
        remaining = max_length - len(answer_ids)
        if remaining <= 0:
            raise ValueError("Independent witness: answer exceeds scoring context")
        prompt_ids = prompt_ids[-remaining:]
    payload = dict(model_revision=revision, prompt_sha256=text_sha(prompt),
        ordered_evidence_hash=object_sha([dict(id=r["document_id"], content_hash=r["content_hash"]) for r in item["evidence"]]),
        answer_sha256=text_sha(item["answer"]), scorer_version="mars-answer-token-v4-answer-position-only-softmax")
    return dict(prompt_ids=prompt_ids, answer_ids=answer_ids, input_ids=prompt_ids + answer_ids,
        payload=payload, cache_key=object_sha(payload), evidence_ids=[r["document_id"] for r in item["evidence"]],
        truncation=bool(cut or token_cut))


class LikelihoodValidation:
    """One sequential initially-empty cache across the complete canonical pass."""
    def __init__(self, tokenizer, template, revision, *, context_budget=16000, max_length=8192):
        self.tokenizer, self.template, self.revision = tokenizer, template, revision
        self.context_budget, self.max_length = context_budget, max_length
        self.audit = Checks()
        self.cache = {}
        self.forwards = self.requests = self.hits = self.prompt_tokens = self.answer_tokens = 0

    def check_forward(self, prepared, observed):
        a = self.audit
        a.schema(observed, WITNESS_FIELDS, "likelihood witness schema")
        prompt, answer = len(prepared["prompt_ids"]), len(prepared["answer_ids"])
        wanted = dict(forward_ordinal=self.forwards + 1, cache_key=prepared["cache_key"],
            prompt_sha256=prepared["payload"]["prompt_sha256"], answer_sha256=prepared["payload"]["answer_sha256"],
            evidence_hash=prepared["payload"]["ordered_evidence_hash"], input_token_ids=prepared["input_ids"],
            attention_mask=[1] * (prompt + answer), position_ids=list(range(prompt + answer)),
            answer_token_ids=prepared["answer_ids"], answer_prediction_positions=list(range(prompt - 1, prompt + answer - 1)),
            prompt_token_count=prompt, answer_token_count=answer, truncation=prepared["truncation"], model_revision=self.revision)
        a.exact({k: v for k, v in observed.items() if k != "token_log_probabilities"}, wanted, "likelihood token/model/forward binding")
        values = observed["token_log_probabilities"]
        a.require(type(values) is list and len(values) == answer, "likelihood token-vector length")
        for value in values:
            a.finite(value, "finite token log probability")
            a.require(value <= 0, "token log probability at most zero")
        previous = self.cache.get(prepared["cache_key"])
        if previous is not None:
            a.exact(values, previous["token_log_probabilities"], "duplicate-key token equality")
        self.forwards += 1
        self.prompt_tokens += prompt
        self.answer_tokens += answer
        self.cache[prepared["cache_key"]] = dict(forward_ordinal=self.forwards, token_log_probabilities=values)

    def check(self, trace, cells, requests, forward_witnesses):
        """Call once per native eligible pair, in original request order."""
        a = self.audit
        a.schema(cells, [c for c, _, _ in CELL_ORDER], "four likelihood cell names")
        a.require(type(requests) is list and len(requests) == 4 and type(forward_witnesses) is list, "four likelihood requests")
        prepared = [prepare(self.tokenizer, self.template, self.revision,
            dict(question=trace["question"], answer=trace[answer], evidence=trace[evidence]),
            context_budget=self.context_budget, max_length=self.max_length) for _, answer, evidence in CELL_ORDER]
        # Native score() decides all hits before computing any miss from this call.
        hits = [p["cache_key"] in self.cache for p in prepared]
        misses = [p for p, hit in zip(prepared, hits) if not hit]
        a.require(len(forward_witnesses) == len(misses), "exact likelihood misses/forwards")
        for p, observed in zip(misses, forward_witnesses, strict=True):
            self.check_forward(p, observed)
        for i, ((name, _, _), p, hit, request) in enumerate(zip(CELL_ORDER, prepared, hits, requests, strict=True)):
            a.schema(request, {"cell_position", "cache_key", "cache_hit", "forward_ordinal", "native_result"}, "likelihood request schema")
            remembered = self.cache[p["cache_key"]]
            a.exact({k: v for k, v in request.items() if k != "native_result"}, dict(cell_position=i,
                cache_key=p["cache_key"], cache_hit=hit, forward_ordinal=remembered["forward_ordinal"]), "request cache chronology")
            actual = request["native_result"]
            a.schema(actual, RESULT_FIELDS, "native likelihood result schema")
            a.exact(cells[name], actual, "cell/request output equality")
            values = remembered["token_log_probabilities"]
            total = sum(values)
            expected = dict(sum_log_probability=total, mean_log_probability=total / len(values), minimum_log_probability=min(values),
                answer_token_count=len(p["answer_ids"]), prompt_token_count=len(p["prompt_ids"]), truncation=p["truncation"],
                prompt_sha256=p["payload"]["prompt_sha256"], model_revision=self.revision,
                ordered_evidence_ids=p["evidence_ids"], ordered_evidence_hash=p["payload"]["ordered_evidence_hash"],
                answer_sha256=p["payload"]["answer_sha256"], cache_key=p["cache_key"], cache_hit=hit)
            a.exact({k: v for k, v in actual.items() if k != "latency_seconds"}, expected, "exact native likelihood aggregates/bindings")
            latency = actual["latency_seconds"]
            a.finite(latency, "finite native likelihood timing")
            a.require(latency >= 0 and (not hit or latency == 0), "native cache-hit zero latency")
        self.requests += 4
        self.hits += sum(hits)
        a.require(self.requests == self.forwards + self.hits, "complete likelihood counters")
        return self.summary()

    def summary(self):
        return dict(checks=self.audit.count, forward_calls=self.forwards, cell_requests=self.requests, cache_hits=self.hits,
            computed_prompt_tokens=self.prompt_tokens, computed_answer_tokens=self.answer_tokens,
            scope="Exact saved token reductions/cache bindings; not vocabulary-softmax or neural-forward replay")
