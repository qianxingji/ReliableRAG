"""Independent normalized EM/F1 and seven-field outcome validation."""
from collections import Counter
import math
import re
import string

from scripts.empirical_neural_checks import Checks


def normalize(value):
    folded = value.lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(re.sub(r"\b(?:a|an|the)\b", " ", folded).split())


def metrics(answer, references):
    if type(answer) is not str or type(references) is not list or not references or any(type(x) is not str for x in references):
        raise ValueError("Original answer and nonempty string reference sequence")
    prediction = normalize(answer)
    matches, f1s = [], []
    for reference in references:
        target = normalize(reference)
        matches.append(prediction == target)
        if (prediction in {"yes", "no", "noanswer"} or target in {"yes", "no", "noanswer"}) and prediction != target:
            f1s.append(0.)
            continue
        left, right = prediction.split(), target.split()
        if not left or not right:
            f1s.append(float(left == right))
            continue
        a, b = Counter(left), Counter(right)
        overlap = sum(min(value, b.get(token, 0)) for token, value in a.items())
        if overlap == 0:
            f1s.append(0.)
        else:
            precision, recall = overlap/len(left), overlap/len(right)
            f1s.append(2.*precision*recall/(precision+recall))
    return int(any(matches)), max(f1s)


def validate_numeric_rows(branches, references, rows, *, question_count=6000):
    """No policy inputs; caller independently authenticates and obtains references."""
    a, seen, fields = Checks(), set(), {"dataset", "retriever", "sample_id", "a0_em", "a1_em", "a0_f1", "a1_f1"}
    expected = {(ds, r, sid) for ds, sid in references for r in ("bm25", "dense", "hybrid")}
    a.exact(len(references), question_count, "complete reference group count")
    for branch, row in zip(branches, rows, strict=True):
        a.schema(row, fields, "exact seven-field numeric outcome schema")
        key = tuple(row[k] for k in ("dataset", "retriever", "sample_id"))
        a.exact(key, tuple(branch[k] for k in ("dataset", "retriever", "sample_id")), "exact canonical outcome order")
        a.require(key in expected and key not in seen, "unique selected outcome identity")
        seen.add(key)
        for state in ("a0", "a1"):
            em, f1 = metrics(branch[state], references[(key[0], key[2])])
            a.require(type(row[state+"_em"]) is int and row[state+"_em"] in (0, 1), "binary integer outcome EM")
            a.exact(row[state+"_em"], em, "independent exact EM")
            actual = row[state+"_f1"]
            a.require(type(actual) in (int, float) and math.isfinite(actual) and 0 <= actual <= 1, "finite bounded outcome F1")
            a.require(abs(actual-f1) <= 1e-15, "independent native F1 agreement")
    a.require(seen == expected, "every selected question and all siblings retained")
    return dict(checks=a.count, traces=len(seen), question_groups=len(references), metric_values_checked=len(seen)*4,
        all_numeric_outcomes_match=True, f1_absolute_bound=1e-15, shared_reference_reader=True, independent_metric_formulas=True)
