"""Independent saved-vector/token binding validation; no encoder forward."""
import numpy as np

from scripts.empirical_neural_checks import Checks, key, text_sha, token_fields


def validate_semantics(tokenizer, traces, vectors, rows, batches, *, first_forward=1, dimension=768, batch_size=16, max_length=512):
    a = Checks()
    keys = [key(t) for t in traces]
    a.require(keys and len(keys) == len(set(keys)) and len({k[0] for k in keys}) == 1, "one complete canonical semantic dataset")
    a.require(len(rows) == len(traces), "every semantic pair binding")
    a.require(type(vectors) is np.ndarray and vectors.dtype == np.float32 and vectors.shape == (2 * len(traces), dimension)
        and np.isfinite(vectors).all(), "finite saved float32 semantic vectors")
    texts = [t[field] for t in traces for field in ("a0", "a1")]
    a.require(len(batches) == (len(texts) + batch_size - 1) // batch_size, "complete semantic forward batches")
    for j, offset in enumerate(range(0, len(texts), batch_size)):
        batch = batches[j]
        a.schema(batch, {"forward_ordinal", "text_offset", "text_sha256", "token_fields"}, "semantic batch schema")
        selected = texts[offset:offset + batch_size]
        expected = tokenizer(selected, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        a.exact(batch, dict(forward_ordinal=first_forward + j, text_offset=offset,
            text_sha256=[text_sha(t) for t in selected], token_fields=token_fields(expected)), "semantic document tokens/order/coverage")
    for i, (trace, row) in enumerate(zip(traces, rows, strict=True)):
        expected = dict(dataset=trace["dataset"], retriever=trace["retriever"], sample_id=trace["sample_id"],
            a0_sha256=text_sha(trace["a0"]), a1_sha256=text_sha(trace["a1"]), vector_rows=[2 * i, 2 * i + 1],
            answer_semantic_agreement=float(np.dot(vectors[2 * i], vectors[2 * i + 1])))
        a.exact(row, expected, "exact paired semantic saved-array value")
        if "answer_semantic_agreement" in trace:
            a.exact(trace["answer_semantic_agreement"], expected["answer_semantic_agreement"], "semantic value attached to native trace")
    return dict(checks=a.count, traces=len(traces), answer_texts=len(texts), forward_calls=len(batches),
        next_forward=first_forward + len(batches), scope="Exact saved-vector dot products/token bindings; not independent encoder or CLS normalization replay")
