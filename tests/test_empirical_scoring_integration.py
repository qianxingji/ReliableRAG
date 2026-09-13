"""Invented native path integration, corruption and shared-mask regression tests."""
import copy
from dataclasses import dataclass
from pathlib import Path
import types
import unittest

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from scripts.empirical_scoring_import_v2 import native_scoring
from scripts.empirical_scoring_io import saved_models
from scripts.empirical_scoring_bindings import restore_bound_trace
from scripts.empirical_scoring_binding_fixtures import invented_bound_rows, InventedLikelihood, POOL_SHA, CONFIG_SHA
from scripts.empirical_semantic_witness import SemanticWitness
from scripts.empirical_scoring_pipeline import score_likelihood_trace, score_gbv_trace, common_policy_ledger
from scripts.empirical_feature_independent import feature_pair, check_numeric_tree
from scripts.empirical_policy_independent import validate_policies


@dataclass
class ToyBranchScore:
    score: float
    premise_count: int = 5
    chunk_count: int = 5


class ToyGbV:
    def __init__(self, *, failure=None, failed_state=1, forward_failure=False):
        self.forward_count = 0
        self.calls = 0
        self.failure, self.failed_state, self.forward_failure = failure, failed_state, forward_failure

    def score_branch(self, question, answer, evidence):
        state = self.calls
        self.calls += 1
        if self.failure is not None and state == self.failed_state:
            if self.forward_failure:
                self.forward_count += 1
            raise ValueError(self.failure)
        self.forward_count += 1
        return ToyBranchScore(.25 if state == 0 else .75), dict(invented_only=True)


class ToyAnswerTokenizer:
    def __init__(self):
        self.seen = []

    def __call__(self, texts, *, max_length, **kwargs):
        self.seen.append(list(texts))
        rows = [[1] + [ord(c) % 20 + 2 for c in text][:max_length - 2] + [2] for text in texts]
        width = max(map(len, rows))
        return dict(input_ids=torch.tensor([r + [0] * (width - len(r)) for r in rows]),
            attention_mask=torch.tensor([[1] * len(r) + [0] * (width - len(r)) for r in rows]))


class ToyEmbedding(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def forward(self, input_ids, attention_mask):
        self.calls += 1
        value = input_ids.float().sum(dim=1)[:, None].expand_as(input_ids)
        hidden = torch.stack((value, value * .125 + 1), dim=-1)
        return types.SimpleNamespace(last_hidden_state=hidden)


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper, cls.native, cls.v2, cls.eligibility, _, _ = native_scoring(Path("E:/paper/ReliableRAG"))
        cls.models, cls.bundle, cls.panel = saved_models(Path("E:/paper/ReliableRAG"), cls.native, cls.v2)

    def trace(self, index=0, answers=None):
        rows = invented_bound_rows(index=index, retriever=("bm25", "dense", "hybrid")[index % 3], answers=answers)
        trace = restore_bound_trace(self.wrapper, *rows, pool_sha=POOL_SHA, runtime_config_sha=CONFIG_SHA)
        trace["answer_semantic_agreement"] = .125
        return trace

    def allocation(self):
        traces = [self.trace(i, answers=("The cog", "cog!") if i == 2 else ("", "blue") if i == 3 else None) for i in range(40)]
        with threadpool_limits(limits=1):
            base = [score_likelihood_trace(self.wrapper, self.native, self.models, self.eligibility, trace,
                InventedLikelihood(self.native, i)) for i, trace in enumerate(traces)]
            gbv = [score_gbv_trace(self.eligibility, trace, ToyGbV(
                failure="hypothesis does not fit the NLI context window" if i == 1 else None)) for i, trace in enumerate(traces)]
            allocation = common_policy_ledger(traces, base, gbv, self.eligibility, self.v2, self.bundle, self.panel)
        return traces, base, gbv, allocation

    def test_strict_c3_metadata_text_and_hash_binding(self):
        rows = invented_bound_rows()
        pristine = copy.deepcopy(rows)
        trace = restore_bound_trace(self.wrapper, *rows, pool_sha=POOL_SHA, runtime_config_sha=CONFIG_SHA)
        self.assertEqual(rows, pristine)
        self.assertEqual(trace["E0"][0]["score"], rows[1]["e0"][0]["retrieval_score"])
        self.assertEqual(trace["split"], "fresh_confirmatory")
        mutations = ((0, "answer", "Gold forbidden"), (1, "canonical_row_sha256", "0" * 64),
                     (2, "position", True), (3, "pool_sha256", "0" * 64))
        for index, field, value in mutations:
            broken = copy.deepcopy(rows)
            broken[index][field] = value
            with self.assertRaises(ValueError):
                restore_bound_trace(self.wrapper, *broken, pool_sha=POOL_SHA, runtime_config_sha=CONFIG_SHA)
        broken = copy.deepcopy(rows)
        broken[1]["e0"][0]["text"] = "altered passage"
        with self.assertRaisesRegex(ValueError, "text binding"):
            restore_bound_trace(self.wrapper, *broken, pool_sha=POOL_SHA, runtime_config_sha=CONFIG_SHA)
        broken = copy.deepcopy(rows)
        broken[1]["e0"][0].pop("retrieval_score")
        with self.assertRaisesRegex(ValueError, "evidence schema"):
            restore_bound_trace(self.wrapper, *broken, pool_sha=POOL_SHA, runtime_config_sha=CONFIG_SHA)

    def test_semantics_native_document_mode_includes_equal_empty_and_batch_tail(self):
        backend = self.native.HFEmbeddingBackend.__new__(self.native.HFEmbeddingBackend)
        backend.config = self.native.DenseConfig(max_length=12, batch_size=16)
        backend.device = torch.device("cpu")
        backend._dimension = 2
        backend.tokenizer = ToyAnswerTokenizer()
        backend.model = ToyEmbedding().eval()
        recorder = SemanticWitness(backend)
        traces = [self.trace(i, answers=("", "") if i == 0 else ("cog", "cog") if i == 1 else None) for i in range(11)]
        values, vectors, rows, batches = recorder.score(self.native, traces)
        self.assertEqual((len(values), vectors.shape, backend.model.calls), (11, (22, 2), 2))
        self.assertEqual([len(b["text_sha256"]) for b in batches], [16, 6])
        self.assertTrue(all(not text.startswith(backend.config.query_prefix) for batch in backend.tokenizer.seen for text in batch))
        self.assertEqual(rows[0]["vector_rows"], [0, 1])
        self.assertEqual(rows[-1]["vector_rows"], [20, 21])
        np.testing.assert_array_equal(values, [float(np.dot(vectors[2*i], vectors[2*i+1])) for i in range(11)])
        with self.assertRaises(RuntimeError):
            recorder.encode_queries(["invented query"])
        recorder.close()

    def test_full_saved_models_common_mask_and_independent_whole_ledger(self):
        traces, base, gbv, allocation = self.allocation()
        snapshot = copy.deepcopy((base, gbv))
        with threadpool_limits(limits=1):
            validated = validate_policies(traces, base, gbv, allocation, self.models,
                self.native.ordinary.ORDINARY_NAMES, self.bundle, self.panel)
        self.assertLessEqual(validated["max_numeric_error"], 1e-10)
        self.assertGreater(validated["numeric_checks"], 2000)
        self.assertEqual((allocation["N_all"], allocation["N_eligible"], allocation["cap"]), (40, 37, 2))
        self.assertEqual(allocation["replacement_counts"]["Keep"], 0)
        self.assertTrue(all(count == 2 for name, count in allocation["replacement_counts"].items() if name != "Keep"))
        failed_row = next(row for row in allocation["ledger"] if row["sample_id"] == traces[1]["sample_id"])
        self.assertTrue(all(v is None for v in failed_row["scores"].values()))
        self.assertIsNotNone(base[1]["scores"]["state_symmetric_hgb"])
        self.assertEqual((gbv[1]["F0"], gbv[1]["failed_branch"], gbv[1]["forward_calls"]), (.25, "F1", 1))
        self.assertEqual((base, gbv), snapshot)

    def test_independent_validator_detects_feature_score_mask_action_and_coverage_corruption(self):
        traces, base, gbv, allocation = self.allocation()
        for mode in ("feature", "score", "mask", "action", "coverage", "unknown_reason"):
            b, g, a = copy.deepcopy(base), copy.deepcopy(gbv), copy.deepcopy(allocation)
            if mode == "feature":
                b[0]["pair"]["features"]["delta_own_likelihood"] += .01
            elif mode == "score":
                a["ledger"][0]["scores"]["HGB"] += .01
            elif mode == "mask":
                a["ledger"][0]["eligible"] = False
            elif mode == "action":
                a["ledger"][0]["actions"]["Keep"] = "REPLACE"
            elif mode == "coverage":
                a["ledger"].pop()
            else:
                g[1]["forced_keep_reason"] = "nli_unscorable:unexpected CUDA error"
            with threadpool_limits(limits=1), self.assertRaises(ValueError, msg=mode):
                validate_policies(traces, b, g, a, self.models, self.native.ordinary.ORDINARY_NAMES, self.bundle, self.panel)

    def test_only_known_preparation_failures_become_common_exclusions(self):
        trace = self.trace()
        for message in ("hypothesis does not fit the NLI context window",
                        "single-word premise at position 17 does not fit the NLI context window"):
            failed = score_gbv_trace(self.eligibility, trace, ToyGbV(failure=message, failed_state=0))
            self.assertEqual((failed["eligible"], failed["attempted_branches"], failed["forward_calls"]), (False, 1, 0))
        for fake in (ToyGbV(failure="unknown error"), ToyGbV(failure="hypothesis does not fit the NLI context window", forward_failure=True)):
            with self.assertRaises(ValueError):
                score_gbv_trace(self.eligibility, trace, fake)
        # Native normalized-empty text can still be eligible if the raw text exists.
        t = self.trace(4, answers=("the", "blue"))
        with threadpool_limits(limits=1):
            scored = score_likelihood_trace(self.wrapper, self.native, self.models, self.eligibility, t, InventedLikelihood(self.native))
        self.assertTrue(scored["eligible"])
        check_numeric_tree(scored["pair"], feature_pair(t, scored["cells"]))

    def test_reconciliation_rejects_missing_eligible_score_or_unexplained_mask(self):
        traces, base, gbv, allocation = self.allocation()
        for mode in ("missing", "mask", "misordered"):
            b, g = copy.deepcopy(base), copy.deepcopy(gbv)
            if mode == "missing":
                b[0]["scores"]["no_B"] = None
            elif mode == "mask":
                g[0]["eligible"] = False
            else:
                b[0], b[1] = b[1], b[0]
            with self.assertRaises(RuntimeError, msg=mode):
                common_policy_ledger(traces, b, g, self.eligibility, self.v2, self.bundle, self.panel)
        equal = [self.trace(0, answers=("same", "same"))]
        b = [score_likelihood_trace(self.wrapper, self.native, self.models, self.eligibility, equal[0], InventedLikelihood(self.native))]
        g = [score_gbv_trace(self.eligibility, equal[0], ToyGbV())]
        empty = common_policy_ledger(equal, b, g, self.eligibility, self.v2, self.bundle, self.panel)
        self.assertEqual((empty["N_eligible"], empty["policy_details"]), (0, []))
        self.assertTrue(all(v == 0 for v in empty["replacement_counts"].values()))


if __name__ == "__main__":
    unittest.main()
