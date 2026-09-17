"""Independent feature reconstruction; no imports from the native feature builder."""
from collections import Counter
from difflib import SequenceMatcher
import math
import re
import string


def normalized(text):
    value = str(text).lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(re.sub(r"\b(?:a|an|the)\b", " ", value).split())


def pair_eligibility(a0, a1):
    if not a0.strip():
        return False, "a0_empty"
    if not a1.strip():
        return False, "a1_empty"
    if normalized(a0) == normalized(a1):
        return False, "normalized_answers_equal"
    return True, None


def tokens(text):
    return re.findall(r"\b\w+\b", text.casefold())


def token_similarity(a, b):
    left, right = tokens(a), tokens(b)
    if not left or not right:
        return float(left == right)
    lc, rc = Counter(left), Counter(right)
    common = sum(min(count, rc[token]) for token, count in lc.items())
    if not common:
        return 0.
    precision, recall = common / len(left), common / len(right)
    return 2 * precision * recall / (precision + recall)


def feature_pair(trace, cells):
    """Independent formulas from the frozen published source schema, no learned fit."""
    before, after = trace["E0"], trace["E1"]
    ids0 = {r["document_id"] for r in before}
    ids1 = {r["document_id"] for r in after}
    added = [r for r in after if r["document_id"] not in ids0]
    removed = [r for r in before if r["document_id"] not in ids1]
    added_text, removed_text = " ".join(r["text"] for r in added), " ".join(r["text"] for r in removed)
    added_score, removed_score = (float(added[0]["score"]) if added else 0.), (float(removed[0]["score"]) if removed else 0.)
    new_tokens = set(tokens(added_text))
    overlaps = []
    for row in before:
        old_tokens = set(tokens(row["text"]))
        union = old_tokens | new_tokens
        overlaps.append(len(old_tokens & new_tokens) / len(union) if union else 1.)
    invariant = dict(evidence_id_overlap=len(ids0 & ids1) / len(ids0 | ids1) if ids0 | ids1 else 1.,
        added_document_score=added_score, removed_document_score=removed_score,
        added_minus_removed_score=added_score - removed_score, new_document_novelty=1. - max(overlaps, default=0.),
        answer_exact_agreement=float(normalized(trace["a0"]) == normalized(trace["a1"])),
        answer_token_similarity=token_similarity(trace["a0"], trace["a1"]),
        answer_semantic_similarity=float(trace["answer_semantic_agreement"]))
    likelihood = {k: float(cells[k]["mean_log_probability"]) for k in ("L00", "L01", "L10", "L11")}
    state_vectors = []
    for answer, own, cross in ((trace["a0"], "L00", "L01"), (trace["a1"], "L11", "L10")):
        state_vectors.append(dict(own_likelihood=likelihood[own], cross_likelihood=likelihood[cross],
            own_minus_cross=likelihood[own] - likelihood[cross], answer_token_length=float(len(tokens(answer))),
            added_lexical_compatibility=token_similarity(answer, added_text), removed_lexical_compatibility=token_similarity(answer, removed_text),
            added_semantic_compatibility=float(SequenceMatcher(a=normalized(answer), b=normalized(added_text)).ratio()),
            removed_semantic_compatibility=float(SequenceMatcher(a=normalized(answer), b=normalized(removed_text)).ratio())))
    delta = {"delta_" + name: state_vectors[1][name] - state_vectors[0][name] for name in state_vectors[0]}
    features = dict(delta)
    for name, value in delta.items():
        for invariant_name in ("evidence_id_overlap", "added_minus_removed_score", "new_document_novelty", "answer_token_similarity", "answer_semantic_similarity"):
            features[name + "_x_" + invariant_name] = value * invariant[invariant_name]
    diagnostics = dict(likelihood, m0=likelihood["L10"] - likelihood["L00"], m1=likelihood["L11"] - likelihood["L01"],
        B_repair=(likelihood["L11"] - likelihood["L01"]) - (likelihood["L10"] - likelihood["L00"]))
    return dict(sample_id=trace["sample_id"], dataset=trace["dataset"], split=trace["split"], retriever=trace["retriever"],
        schema_version="mars-state-symmetric-v1", features=features, invariant_features=invariant, diagnostics=diagnostics)


def check_numeric_tree(actual, expected, *, tolerance=1e-10):
    """Recursively compare schema and numeric values, rejecting NaN and booleans."""
    if type(expected) is dict:
        if type(actual) is not dict or set(actual) != set(expected):
            raise ValueError("Independent schema mismatch")
        counts, maximum = 0, 0.
        for name, value in expected.items():
            count, error = check_numeric_tree(actual[name], value, tolerance=tolerance)
            counts += count
            maximum = max(maximum, error)
        return counts, maximum
    if type(expected) in (int, float):
        if type(actual) not in (int, float) or not math.isfinite(actual) or not math.isfinite(expected):
            raise ValueError("Independent finite numeric type")
        error = abs(actual - expected)
        if error > tolerance:
            raise ValueError("Independent numerical mismatch")
        return 1, error
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError("Independent metadata mismatch")
    return 0, 0.
