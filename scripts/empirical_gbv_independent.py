"""Independent NLI chunk/token/softmax/max/failure validation; no model forward."""
import re

import numpy as np

from scripts.empirical_neural_checks import Checks, key, text_sha, token_fields

FP32_EPS = 2.0 ** -23
SOFTMAX_ABSOLUTE_BOUND = 8 * FP32_EPS
SUM_ABSOLUTE_BOUND = 2 * FP32_EPS


def hypothesis(question, answer):
    return 'The answer to the question "' + question + '" is: "' + answer + '"'


def length(tokenizer, premise, claim):
    result = tokenizer(premise, claim, add_special_tokens=True, truncation=False,
        return_attention_mask=False, return_token_type_ids=False)["input_ids"]
    if hasattr(result, "tolist"):
        result = result.tolist()
    if result and isinstance(result[0], list):
        if len(result) != 1:
            raise ValueError("Independent witness: multiple NLI pairs in length probe")
        result = result[0]
    return len(result)


def chunks(tokenizer, passage, claim, *, max_length=512, overlap=20):
    """Independent native-boundary reconstruction plus explicit word coverage."""
    if max_length <= 0 or overlap < 0:
        raise ValueError("Independent witness: invalid fixed chunk configuration")
    if length(tokenizer, "", claim) > max_length:
        raise ValueError("hypothesis does not fit the NLI context window")
    if length(tokenizer, passage, claim) <= max_length:
        return [passage]
    words = passage.split()
    if not words:
        return [""]
    offset, covered, result = 0, set(), []
    while offset < len(words):
        lower, upper, accepted = offset + 1, len(words), None
        while lower <= upper:
            trial = (lower + upper) // 2
            segment = " ".join(words[offset:trial])
            if length(tokenizer, segment, claim) > max_length:
                upper = trial - 1
            else:
                accepted, lower = trial, trial + 1
        if accepted is None:
            raise ValueError(f"single-word premise at position {offset} does not fit the NLI context window")
        segment = " ".join(words[offset:accepted])
        if length(tokenizer, segment, claim) > max_length:
            raise ValueError("Independent witness: overlength emitted NLI chunk")
        result.append(segment)
        covered.update(range(offset, accepted))
        if accepted == len(words):
            break
        offset = max(offset + 1, accepted - overlap)
    if covered != set(range(len(words))):
        raise ValueError("Independent witness: lost NLI premise words")
    return result


def positive_index(labels):
    entries = {int(k): re.sub("[^a-z]", "", str(v).lower()) for k, v in labels.items()}
    if len(labels) != 2 or set(entries) != {0, 1} or [i for i, value in entries.items() if value == "entailment"] != [0]:
        raise ValueError("Independent witness: pinned binary positive entailment index zero")
    return 0


class GbVValidation:
    def __init__(self, tokenizer, labels, *, max_length=512, batch_size=8):
        self.tokenizer, self.max_length, self.batch_size = tokenizer, max_length, batch_size
        self.entailment_index = positive_index(labels)
        self.audit = Checks()
        self.forwards = self.pairs = self.branches = self.unscorable = 0
        self.max_probability_error = 0.

    def prepared(self, question, answer, evidence):
        claim = hypothesis(question, answer)
        by_premise = [chunks(self.tokenizer, passage, claim, max_length=self.max_length) for passage in evidence]
        return claim, by_premise, [(part, claim) for parts in by_premise for part in parts]

    def check_branch(self, question, answer, evidence, result, witness):
        a = self.audit
        claim, by_premise, pairs = self.prepared(question, answer, evidence)
        a.require(bool(pairs), "nonempty NLI chunk universe")
        a.schema(result, {"score", "premise_count", "chunk_count"}, "native branch-result schema")
        a.schema(witness, {"question_sha256", "answer_sha256", "hypothesis_sha256", "premise_sha256", "premise_chunk_counts",
            "batches", "native_score", "premise_count", "chunk_count"}, "NLI witness schema")
        a.exact({k: v for k, v in witness.items() if k not in {"batches", "native_score"}},
            dict(question_sha256=text_sha(question), answer_sha256=text_sha(answer), hypothesis_sha256=text_sha(claim),
                premise_sha256=[text_sha(p) for p in evidence], premise_chunk_counts=[len(parts) for parts in by_premise],
                premise_count=len(evidence), chunk_count=len(pairs)), "NLI hypothesis/premise/chunk bindings")
        a.require(len(witness["batches"]) == (len(pairs) + self.batch_size - 1) // self.batch_size, "NLI complete batch count")
        values = []
        for batch_index, offset in enumerate(range(0, len(pairs), self.batch_size)):
            batch = witness["batches"][batch_index]
            a.schema(batch, {"forward_ordinal", "pair_offset", "pairs", "token_fields", "logits", "probabilities", "entailment_index", "max_length"}, "NLI batch schema")
            selected = pairs[offset:offset + self.batch_size]
            expected_tokens = self.tokenizer([p for p, _ in selected], [h for _, h in selected],
                add_special_tokens=True, truncation=False, padding=True, return_tensors="pt")
            a.exact({k: v for k, v in batch.items() if k not in {"logits", "probabilities"}},
                dict(forward_ordinal=self.forwards + 1, pair_offset=offset,
                    pairs=[dict(premise=p, hypothesis=h) for p, h in selected], token_fields=token_fields(expected_tokens),
                    entailment_index=self.entailment_index, max_length=self.max_length), "NLI exact token/chunk/forward order")
            a.require(expected_tokens["input_ids"].shape[1] <= self.max_length, "NLI no scientific truncation")
            arrays = {}
            for field in ("logits", "probabilities"):
                raw = batch[field]
                a.require(type(raw) is list and len(raw) == len(selected) and all(type(row) is list and len(row) == 2 for row in raw), "NLI two-class array shape")
                for row in raw:
                    for value in row:
                        a.finite(value, "finite NLI value")
                        with np.errstate(over="ignore", invalid="ignore"):
                            a.require(float(np.float32(value)) == value, "exactly representable saved FP32 value")
                arrays[field] = np.asarray(raw, dtype=np.float64)
            logits, probabilities = arrays["logits"], arrays["probabilities"]
            shifted = logits - np.max(logits, axis=1, keepdims=True)
            exponentials = np.exp(shifted)
            independent = exponentials / np.sum(exponentials, axis=1, keepdims=True)
            error = float(np.max(np.abs(independent - probabilities)))
            a.require(error <= SOFTMAX_ABSOLUTE_BOUND, "prospective FP32 softmax bound")
            a.require(np.all((probabilities >= 0) & (probabilities <= 1)) and
                np.all(np.abs(np.sum(probabilities, axis=1) - 1) <= SUM_ABSOLUTE_BOUND), "NLI probability range/sum")
            self.max_probability_error = max(self.max_probability_error, error)
            values.extend(probabilities[:, self.entailment_index].tolist())
            self.forwards += 1
            self.pairs += len(selected)
        maximum = max(values)
        a.exact(witness["native_score"], maximum, "exact observed NLI branch maximum")
        a.exact(result, dict(score=maximum, premise_count=len(evidence), chunk_count=len(pairs)), "native NLI branch aggregation")
        self.branches += 1
        return maximum

    def check_pair(self, trace, record, *, native_eligible, native_reason):
        """Eligibility supplied from the separate independent answer-normalization check."""
        a = self.audit
        a.schema(record, {"dataset", "retriever", "sample_id", "eligible", "forced_keep_reason", "F0", "F1", "gbv_margin",
            "completed_branches", "failed_branch", "attempted_branches", "forward_calls"}, "paired NLI record schema")
        a.exact(key(record), key(trace), "NLI trace identity")
        start = self.forwards
        if not native_eligible:
            a.exact({k: v for k, v in record.items() if k not in {"dataset", "retriever", "sample_id"}},
                dict(eligible=False, forced_keep_reason=native_reason, F0=None, F1=None, gbv_margin=None,
                    completed_branches=[], failed_branch=None, attempted_branches=0, forward_calls=0), "native ineligible NLI row")
            return self.summary()
        completed, failure = [], None
        branch_values = {"F0": None, "F1": None}
        for i, (state, answer, evidence) in enumerate((("F0", "a0", "E0"), ("F1", "a1", "E1"))):
            passages = [r["text"] for r in trace[evidence]]
            try:
                self.prepared(trace["question"], trace[answer], passages)
            except ValueError as exc:
                message = str(exc)
                documented = message == "hypothesis does not fit the NLI context window" or bool(re.fullmatch(
                    r"single-word premise at position [0-9]+ does not fit the NLI context window", message))
                a.require(documented, "only reproduced deterministic NLI preparation failure")
                failure = (state, "nli_unscorable:" + message)
                break
            a.require(i < len(record["completed_branches"]), "retained successful NLI branch witness")
            observed = record["completed_branches"][i]
            a.schema(observed, {"state", "result", "witness"}, "paired NLI branch observation schema")
            a.exact(observed["state"], state, "native a0/E0 then a1/E1 branch order")
            branch_values[state] = self.check_branch(trace["question"], trace[answer], passages, observed["result"], observed["witness"])
            completed.append(state)
        expected = dict(eligible=failure is None, forced_keep_reason=None if failure is None else failure[1],
            **branch_values, gbv_margin=branch_values["F1"] - branch_values["F0"] if failure is None else None,
            failed_branch=None if failure is None else failure[0], attempted_branches=len(completed) + int(failure is not None),
            forward_calls=self.forwards - start)
        a.exact({k: v for k, v in record.items() if k not in {"dataset", "retriever", "sample_id", "completed_branches"}},
            expected, "exact paired NLI mask/margin/failure/counters")
        a.require(len(record["completed_branches"]) == len(completed), "no omitted or post-failure NLI branches")
        self.unscorable += int(failure is not None)
        return self.summary()

    def summary(self):
        return dict(checks=self.audit.count, forward_calls=self.forwards, nli_pairs=self.pairs, completed_branches=self.branches,
            deterministic_unscorable_pairs=self.unscorable, max_probability_error=self.max_probability_error,
            softmax_absolute_bound=SOFTMAX_ABSOLUTE_BOUND, probability_sum_absolute_bound=SUM_ABSOLUTE_BOUND,
            scope="Saved FP32 logits/softmax and exact observed maxima; not independent NLI forward replay")
