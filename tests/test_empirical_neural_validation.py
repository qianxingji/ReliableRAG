"""Independent witness validators against native CPU fake-logit observations."""
import copy
from dataclasses import asdict
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from scripts.empirical_likelihood_witness import LikelihoodWitness
from scripts.empirical_likelihood_independent import LikelihoodValidation, prepare
from scripts.empirical_gbv_witness import GbVWitness
from scripts.empirical_gbv_independent import GbVValidation, chunks, positive_index, SOFTMAX_ABSOLUTE_BOUND
from scripts.empirical_semantic_witness import SemanticWitness
from scripts.empirical_semantic_independent import validate_semantics
from scripts.empirical_scoring_import_v2 import native_scoring
from scripts.empirical_scoring_pipeline import score_gbv_trace
from scripts.empirical_scoring_fixtures import invented_trace
from scripts.empirical_feature_independent import pair_eligibility
import test_empirical_likelihood_witness as likelihood_fixture
import test_empirical_gbv_witness as gbv_fixture
from test_empirical_scoring_integration import ToyAnswerTokenizer, ToyEmbedding


class NeuralValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        likelihood_fixture.LikelihoodWitnessTests.setUpClass()
        gbv_fixture.GbVWitnessTests.setUpClass()
        _, cls.native, _, cls.eligibility, _, _ = native_scoring(Path("E:/paper/ReliableRAG"))

    def likelihood(self, directory, *, limit=8192):
        fixture = likelihood_fixture.LikelihoodWitnessTests()
        scorer = fixture.scorer(directory)
        scorer.config["max_length"] = limit
        witness = LikelihoodWitness(scorer)
        checker = LikelihoodValidation(scorer.tokenizer, scorer.answer_template, scorer.resolved_revision, max_length=limit)
        return fixture, scorer, witness, checker

    def cells(self, results):
        return {name: asdict(value) for name, value in zip(("L00", "L01", "L10", "L11"), results, strict=True)}

    def test_native_likelihood_exact_reductions_and_current_run_cache_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture, scorer, witness, checker = self.likelihood(directory)
            trace = invented_trace(0, "bm25")
            first, requests, forwards = witness.score(fixture.items())
            one = checker.check(trace, self.cells(first), requests, forwards)
            self.assertEqual((one["forward_calls"], one["cache_hits"], one["cell_requests"]), (4, 0, 4))
            second, cached, no_forward = witness.score(fixture.items())
            two = checker.check(trace, self.cells(second), cached, no_forward)
            self.assertEqual((two["forward_calls"], two["cache_hits"], two["cell_requests"]), (4, 4, 8))
            self.assertEqual(scorer.model.training, False)
            witness.close()

    def test_independent_likelihood_renderer_token_limit_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture, scorer, witness, checker = self.likelihood(directory, limit=12)
            trace = invented_trace(0, "bm25")
            first, requests, forwards = witness.score(fixture.items())
            cells = self.cells(first)
            checker.check(trace, cells, requests, forwards)
            self.assertTrue(all(row["truncation"] for row in forwards))
            for mode in ("token", "position", "reduction", "key", "hit", "ordinal", "missing", "timing", "nan"):
                c, r, f = copy.deepcopy(cells), copy.deepcopy(requests), copy.deepcopy(forwards)
                if mode == "token": f[0]["input_token_ids"][0] += 1
                elif mode == "position": f[0]["answer_prediction_positions"][0] += 1
                elif mode == "reduction": c["L00"]["mean_log_probability"] += .01
                elif mode == "key": r[0]["cache_key"] = "0" * 64
                elif mode == "hit": r[0]["cache_hit"] = True
                elif mode == "ordinal": f[0]["forward_ordinal"] = 2
                elif mode == "missing": f.pop()
                elif mode == "timing":
                    c["L00"]["latency_seconds"] = -1.
                    r[0]["native_result"]["latency_seconds"] = -1.
                else: f[0]["token_log_probabilities"][0] = float("nan")
                fresh = LikelihoodValidation(scorer.tokenizer, scorer.answer_template, scorer.resolved_revision, max_length=12)
                with self.assertRaises(ValueError, msg=mode): fresh.check(trace, c, r, f)
            for item in fixture.items():
                actual = scorer._prepare(item)
                independent = prepare(scorer.tokenizer, scorer.answer_template, scorer.resolved_revision, item, max_length=12)
                self.assertEqual(independent["input_ids"], actual["input_ids"])
                self.assertEqual(independent["cache_key"], actual["cache_key"])
            witness.close()

    def test_cache_hits_cannot_be_imported_into_fresh_validator(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture, scorer, witness, checker = self.likelihood(directory)
            witness.score(fixture.items())
            results, requests, forwards = witness.score(fixture.items())
            with self.assertRaisesRegex(ValueError, "misses/forwards"):
                checker.check(invented_trace(0, "bm25"), self.cells(results), requests, forwards)
            witness.close()

    def gbv_pair(self, *, limit=24, fail_second=False):
        fixture = gbv_fixture.GbVWitnessTests()
        scorer = fixture.scorer(limit=limit)
        observer = GbVWitness(scorer, fixture.native)
        trace = invented_trace(0, "bm25")
        trace["E0"][0]["text"] = " ".join("word" + str(i) for i in range(35))
        if fail_second:
            trace["a1"] = "word " * 40
        recorded = score_gbv_trace(self.eligibility, trace, observer)
        checker = GbVValidation(scorer.tokenizer, scorer.model.config.id2label, max_length=limit)
        return scorer, observer, trace, recorded, checker

    def test_native_gbv_all_chunks_fp32_softmax_and_exact_maxima(self):
        scorer, observer, trace, record, checker = self.gbv_pair()
        report = checker.check_pair(trace, record, native_eligible=True, native_reason=None)
        self.assertEqual(report["forward_calls"], scorer.model.calls)
        self.assertEqual(report["completed_branches"], 2)
        self.assertGreater(report["nli_pairs"], 10)
        self.assertLessEqual(report["max_probability_error"], SOFTMAX_ABSOLUTE_BOUND)
        self.assertEqual(record["gbv_margin"], record["F1"] - record["F0"])
        observer.close()

    def test_gbv_corruption_of_chunk_token_class_logits_probability_and_margin_fails(self):
        scorer, observer, trace, original, _ = self.gbv_pair()
        for mode in ("chunk", "token", "class", "logit", "probability", "max", "margin", "ordinal", "missing"):
            record = copy.deepcopy(original)
            branch = record["completed_branches"][0]
            batch = branch["witness"]["batches"][0]
            if mode == "chunk": batch["pairs"][0]["premise"] += " omitted"
            elif mode == "token": batch["token_fields"]["input_ids"][0][0] += 1
            elif mode == "class": batch["entailment_index"] = 1
            elif mode == "logit": batch["logits"][0][0] = float(np.float32(batch["logits"][0][0] + 1))
            elif mode == "probability": batch["probabilities"][0][0] = float(np.float32(batch["probabilities"][0][0] - .001))
            elif mode == "max": branch["result"]["score"] = 0.
            elif mode == "margin": record["gbv_margin"] += .001
            elif mode == "ordinal": batch["forward_ordinal"] = 3
            else: branch["witness"]["batches"].pop()
            checker = GbVValidation(scorer.tokenizer, scorer.model.config.id2label, max_length=24)
            with self.assertRaises(ValueError, msg=mode):
                checker.check_pair(trace, record, native_eligible=True, native_reason=None)
        observer.close()

    def test_gbv_deterministic_second_branch_failure_preserves_first_and_rejects_fake_reason(self):
        scorer, observer, trace, record, checker = self.gbv_pair(fail_second=True)
        report = checker.check_pair(trace, record, native_eligible=True, native_reason=None)
        self.assertEqual(record["failed_branch"], "F1")
        self.assertEqual(report["deterministic_unscorable_pairs"], 1)
        self.assertEqual(report["forward_calls"], scorer.model.calls)
        self.assertIsNotNone(record["F0"])
        bad = copy.deepcopy(record)
        bad["forced_keep_reason"] = "nli_unscorable:unknown error"
        with self.assertRaises(ValueError):
            GbVValidation(scorer.tokenizer, scorer.model.config.id2label, max_length=24).check_pair(trace, bad, native_eligible=True, native_reason=None)
        # An equal-answer row produces zero model calls and retains all null fields.
        empty = invented_trace(1, "dense")
        empty["a1"] = empty["a0"]
        equal = score_gbv_trace(self.eligibility, empty, observer)
        good, reason = pair_eligibility(empty["a0"], empty["a1"])
        checker.check_pair(empty, equal, native_eligible=good, native_reason=reason)
        observer.close()

    def test_chunker_matches_original_and_label_resolution_is_exact(self):
        fixture = gbv_fixture.GbVWitnessTests()
        scorer = fixture.scorer(limit=24)
        claim = fixture.native.format_hypothesis("Color?", "silver")
        passages = ("", "  short passage  ", " ".join("word" + str(i) for i in range(70)))
        for passage in passages:
            self.assertEqual(chunks(scorer.tokenizer, passage, claim, max_length=24),
                fixture.native.split_passage_to_fit(scorer.tokenizer, passage, claim, max_length=24, overlap_words=20))
        self.assertEqual(positive_index({"0": "entailment", "1": "not_entailment"}), 0)
        for bad in ({0: "not_entailment", 1: "entailment"}, {0: "entailment", 1: "entailment"}, {0: "not_entailment", 1: "neutral"}):
            with self.assertRaises(ValueError): positive_index(bad)

    def test_semantic_full_native_tokens_vectors_order_and_corruptions(self):
        backend = self.native.HFEmbeddingBackend.__new__(self.native.HFEmbeddingBackend)
        backend.config = self.native.DenseConfig(max_length=12, batch_size=16)
        backend.device, backend._dimension = torch.device("cpu"), 2
        backend.tokenizer, backend.model = ToyAnswerTokenizer(), ToyEmbedding().eval()
        observer = SemanticWitness(backend)
        traces = [invented_trace(i, "bm25") for i in range(11)]
        traces[0]["a0"] = traces[0]["a1"] = ""
        traces[1]["a1"] = traces[1]["a0"]
        values, vectors, rows, batches = observer.score(self.native, traces)
        for trace, value in zip(traces, values): trace["answer_semantic_agreement"] = value
        report = validate_semantics(backend.tokenizer, traces, vectors, rows, batches, dimension=2, max_length=12)
        self.assertEqual((report["answer_texts"], report["forward_calls"]), (22, 2))
        for mode in ("row", "token", "hash", "vector", "tail", "dot", "boolean_token"):
            r, b, v = copy.deepcopy(rows), copy.deepcopy(batches), vectors.copy()
            if mode == "row": r[0]["vector_rows"] = [2, 3]
            elif mode == "token": b[0]["token_fields"]["input_ids"][0][0] += 1
            elif mode == "hash": r[0]["a0_sha256"] = "0" * 64
            elif mode == "vector": v[0, 0] += .1
            elif mode == "tail": b.pop()
            elif mode == "dot": r[0]["answer_semantic_agreement"] += .001
            else: b[0]["token_fields"]["input_ids"][0][0] = True
            with self.assertRaises(ValueError, msg=mode):
                validate_semantics(backend.tokenizer, traces, v, r, b, dimension=2, max_length=12)
        self.assertEqual(backend.model.calls, 2, "Independent validation never invokes the model")
        observer.close()

    def test_single_word_nli_failure_is_independently_reproduced(self):
        fixture = gbv_fixture.GbVWitnessTests()
        scorer = fixture.scorer(limit=11)
        claim = fixture.native.format_hypothesis("Color?", "silver")
        wanted = "single-word premise at position 0 does not fit the NLI context window"
        for function in (chunks, fixture.native.split_passage_to_fit):
            with self.assertRaisesRegex(ValueError, wanted):
                function(scorer.tokenizer, "word", claim, max_length=11)
        observer = GbVWitness(scorer, fixture.native)
        trace = invented_trace(0, "bm25")
        trace["question"] = "Color?"
        record = score_gbv_trace(self.eligibility, trace, observer)
        report = GbVValidation(scorer.tokenizer, scorer.model.config.id2label, max_length=11).check_pair(
            trace, record, native_eligible=True, native_reason=None)
        self.assertEqual((report["forward_calls"], report["deterministic_unscorable_pairs"]), (0, 1))
        observer.close()

    def test_character_budget_and_non_prefix_tokenization_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture, scorer, witness, _ = self.likelihood(directory)
            scorer.config["context_budget_characters"] = 128
            for item in fixture.items():
                original = scorer._prepare(item)
                independent = prepare(scorer.tokenizer, scorer.answer_template, scorer.resolved_revision, item, context_budget=128)
                self.assertEqual(independent["input_ids"], original["input_ids"])
                self.assertEqual(independent["payload"], original["payload"])
                self.assertEqual(independent["truncation"], True)
            class BadPrefix(likelihood_fixture.ToyTokenizer):
                def __call__(self, text, **kwargs):
                    result = super().__call__(text, **kwargs)
                    if text.endswith("silver"): result["input_ids"][0] += 1
                    return result
            with self.assertRaisesRegex(ValueError, "prefix alignment"):
                prepare(BadPrefix(), scorer.answer_template, scorer.resolved_revision, fixture.items()[0])
            witness.close()


if __name__ == "__main__":
    unittest.main()
