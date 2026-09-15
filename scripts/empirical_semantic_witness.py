"""Record native answer embedding tokens, returned vectors and paired similarities."""
import math
import types

from scripts.empirical_scoring_bindings import text_sha
from scripts.empirical_runtime_contract import trace_key


class SemanticWitness:
    """A backend proxy, never a replacement embedding implementation."""

    def __init__(self, backend):
        self.backend = backend
        self.active = False
        self.forward_count = 0
        self.hook = backend.model.register_forward_hook(self._forward, with_kwargs=True)

    def _forward(self, model, args, kwargs, output):
        import torch
        if not self.active or self.cursor >= len(self.texts):
            raise RuntimeError("Unexpected answer embedding forward")
        if not torch.is_inference_mode_enabled() or torch.is_grad_enabled() or model.training:
            raise RuntimeError("Answer embedding inference context")
        batch = self.texts[self.cursor:self.cursor + self.backend.config.batch_size]
        expected = self.backend.tokenizer(batch, padding=True, truncation=True,
            max_length=self.backend.config.max_length, return_tensors="pt")
        actual = {k: v.detach().cpu().tolist() for k, v in kwargs.items()}
        if actual != {k: v.tolist() for k, v in expected.items()}:
            raise RuntimeError("Native document-mode answer token binding")
        if output.last_hidden_state.shape[:2] != kwargs["input_ids"].shape:
            raise RuntimeError("Answer embedding output shape")
        self.forward_count += 1
        self.batches.append(dict(forward_ordinal=self.forward_count, text_offset=self.cursor,
            text_sha256=[text_sha(t) for t in batch], token_fields=actual))
        self.cursor += len(batch)
        return None

    def encode_documents(self, texts):
        import numpy as np
        if not self.active or list(texts) != self.texts or self.encode_calls:
            raise RuntimeError("One original flat answer encoding call required")
        self.encode_calls += 1
        self.vectors = self.backend.encode_documents(texts)
        if (self.vectors.dtype != np.float32 or self.vectors.shape != (len(texts), self.backend.dimension)
                or not np.isfinite(self.vectors).all()):
            raise RuntimeError("Complete finite native float32 answer embeddings")
        return self.vectors

    def encode_queries(self, texts):
        raise RuntimeError("Query encoding is forbidden in answer semantics")

    def score(self, native, traces):
        if self.active or not traces:
            raise ValueError("Nonempty canonical dataset trace list required")
        keys = [trace_key(t) for t in traces]
        if len(keys) != len(set(keys)) or len({k[0] for k in keys}) != 1:
            raise ValueError("Unique one-dataset semantic batch")
        pairs = [(t["a0"], t["a1"]) for t in traces]
        if any(type(a) is not str for pair in pairs for a in pair):
            raise ValueError("Original answer strings required")
        self.texts = [a for pair in pairs for a in pair]
        self.cursor = self.encode_calls = 0
        self.batches = []
        self.active = True
        try:
            values = native._semantic_agreements(types.SimpleNamespace(dense_backend=self), pairs)
        finally:
            self.active = False
        if self.cursor != len(self.texts) or self.encode_calls != 1 or len(values) != len(traces):
            raise RuntimeError("All answers encoded exactly once before eligibility")
        rows = []
        for i, (trace, value) in enumerate(zip(traces, values, strict=True)):
            if not math.isfinite(value) or value != float(self.vectors[2*i] @ self.vectors[2*i+1]):
                raise RuntimeError("Native saved-vector paired similarity")
            rows.append(dict(dataset=trace["dataset"], retriever=trace["retriever"], sample_id=trace["sample_id"],
                a0_sha256=text_sha(trace["a0"]), a1_sha256=text_sha(trace["a1"]),
                vector_rows=[2*i, 2*i+1], answer_semantic_agreement=value))
        return values, self.vectors, rows, list(self.batches)

    def close(self):
        self.hook.remove()
