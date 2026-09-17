from pathlib import Path
import ast
import hashlib
import json
import math
import sys
import tempfile
import unittest

import numpy as np

from scripts.run_mistral_test_gbv import (
    BATCH_SIZE,
    EXPECTED_TRACES,
    GBV_MODEL_ID,
    GBV_MODEL_REVISION,
    GBV_PACKAGE_ROOT_RELATIVE,
    LOGIT_WIDTH,
    deterministic_nli_error,
    retain_scored_branch,
    softmax_entailment,
    validate_branch_payload,
)
from scripts.validate_mistral_test_gbv import (
    current_manifest_member_paths, entailment_probabilities,
)


class MistralTestGbVContractTests(unittest.TestCase):
    def test_exact_identity_and_batch_contract(self):
        self.assertEqual(EXPECTED_TRACES, 18_000)
        self.assertEqual(BATCH_SIZE, 8)
        self.assertEqual(LOGIT_WIDTH, 2)
        self.assertEqual(GBV_MODEL_ID, "MoritzLaurer/deberta-v3-large-zeroshot-v2.0")
        self.assertEqual(GBV_MODEL_REVISION, "5a4338ab2151dc8db04ad53b42b6153382bf4f99")
        self.assertEqual(
            GBV_PACKAGE_ROOT_RELATIVE.as_posix(),
            "outputs/published_baseline_gbv_nli_v1/infrastructure/python_packages",
        )

    def test_independent_softmax_matches_producer(self):
        logits = np.asarray([[2.0, 0.0], [-3.0, 4.0]], dtype=np.float32)
        producer = softmax_entailment(logits, 0)
        independent = entailment_probabilities(logits, 0)
        np.testing.assert_array_equal(producer, independent)

    def test_only_historical_context_failures_are_accepted(self):
        self.assertTrue(deterministic_nli_error("hypothesis does not fit the NLI context window"))
        self.assertTrue(deterministic_nli_error(
            "single-word premise at position 19 does not fit the NLI context window"
        ))
        self.assertFalse(deterministic_nli_error("CUDA out of memory"))

    def test_successful_f0_is_retained_if_f1_later_fails(self):
        row = {"F0": None, "F1": None, "e0_chunk_count": 0, "e1_chunk_count": 0}
        retain_scored_branch(row, "a0_e0", {
            "status": "scored", "score": 0.75, "chunk_count": 3,
        })
        self.assertEqual(row, {
            "F0": 0.75, "F1": None, "e0_chunk_count": 3, "e1_chunk_count": 0,
        })

    def test_branch_payload_recomputes_score_from_raw_logits(self):
        trace = {"dataset": "d", "retriever": "bm25", "sample_id": "s", "position": 0}
        role, state, question, answer = "test", "a0_e0", "q", "a"
        evidence = ["p"]
        pairs = [("p", "h"), ("p2", "h")]
        tokens = [{"input_ids": [[1, 2], [1, 3]], "attention_mask": [[1, 1], [1, 1]]}]
        logits = np.asarray([[2.0, 0.0], [0.0, 2.0]], dtype=np.float32)
        score = float(np.max(softmax_entailment(logits, 0)))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); path = root / "logits/00000_a0_e0_00.f32"
            path.parent.mkdir(); path.write_bytes(logits.tobytes())
            payload = {
                "status": "scored", **trace, "role": role, "state": state,
                "question_sha256": hashlib.sha256(b'"q"').hexdigest(),
                "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
                "evidence_sha256": hashlib.sha256(b'["p"]').hexdigest(),
                "premise_count": 1, "chunk_count": 2,
                "hypothesis_sha256": hashlib.sha256(b"h").hexdigest(),
                "pair_bindings": [{
                    "premise_sha256": hashlib.sha256(p.encode()).hexdigest(),
                    "hypothesis_sha256": hashlib.sha256(h.encode()).hexdigest(),
                } for p, h in pairs],
                "forwards": [{
                    "batch_index": 0, "pair_indices": [0, 1], "token_fields": tokens[0],
                    "logits": {
                        "path": "logits/00000_a0_e0_00.f32",
                        "size_bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "dtype": "float32", "shape": [2, 2], "byte_order": "little",
                    },
                }],
                "score": score, "diagnostic": None,
            }
            validate_branch_payload(
                payload, trace=trace, role=role, state=state, question=question,
                answer=answer, evidence_texts=evidence, expected_pairs=pairs,
                expected_tokens=tokens, stage_output=root, entailment_index=0,
            )
            payload["score"] = math.nextafter(score, 0.0) - 1e-5
            with self.assertRaisesRegex(RuntimeError, "GBV_SCORE_RECOMPUTATION"):
                validate_branch_payload(
                    payload, trace=trace, role=role, state=state, question=question,
                    answer=answer, evidence_texts=evidence, expected_pairs=pairs,
                    expected_tokens=tokens, stage_output=root, entailment_index=0,
                )

    def test_producer_gates_hgb_and_preserves_branch_order(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/run_mistral_test_gbv.py").read_text(encoding="utf-8")
        self.assertIn("PASS_INDEPENDENT_FORMULA_MISTRAL_TEST_HGB_SIGNAL", source)
        self.assertIn('("a0_e0", a0, e0), ("a1_e1", a1, e1)', source)
        self.assertIn("GBV_FROZEN_ENVIRONMENT", source)
        self.assertIn("GBV_UNSCORABLE_FORWARD", source)
        self.assertIn("GBV_SENTENCEPIECE_RUNTIME", source)
        self.assertIn('value["gbv"]["package_files"]', source)
        self.assertIn("test_gold_values_read", source)
        self.assertIn('"test_gold_access": "FORBIDDEN"', source)
        self.assertIn('dtype="<f4"', source)

    def test_unscorable_payload_rejects_hidden_hypothesis(self):
        trace = {"dataset": "d", "retriever": "bm25", "sample_id": "s", "position": 0}
        payload = {
            "status": "unscorable", **trace, "role": "test", "state": "a0_e0",
            "question_sha256": hashlib.sha256(b'"q"').hexdigest(),
            "answer_sha256": hashlib.sha256(b"a").hexdigest(),
            "evidence_sha256": hashlib.sha256(b'["p"]').hexdigest(),
            "premise_count": 1, "chunk_count": 0,
            "hypothesis_sha256": "unexpected", "pair_bindings": [],
            "forwards": [], "score": None, "diagnostic": "too long",
        }
        with self.assertRaisesRegex(RuntimeError, "GBV_UNSCORABLE_PAYLOAD"):
            validate_branch_payload(
                payload, trace=trace, role="test", state="a0_e0", question="q",
                answer="a", evidence_texts=["p"], expected_pairs=None,
                expected_tokens=None, stage_output=Path("."), entailment_index=0,
            )

    def test_validator_is_tokenizer_logit_only_and_independent_of_producer(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/validate_mistral_test_gbv.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn("scripts.run_mistral_test_gbv", imported_modules)
        self.assertNotIn("GBVPostAnsweringNLI", source)
        self.assertNotIn("AutoModel", source)
        self.assertIn("AutoTokenizer", source)
        self.assertIn("SCORE_RECOMPUTATION", source)
        self.assertIn("EXACT_LOGIT_COVERAGE", source)
        self.assertIn("RECEIPT_FILE_BINDINGS", source)
        self.assertIn("PASS_INDEPENDENT_TOKENIZER_LOGIT_MISTRAL_TEST_GBV", source)

    def test_freeze_requires_exact_direct_input_graph(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_test_gbv.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_test_gbv.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MISTRAL_TEST_GBV_INPUT_GRAPH_AMENDMENT", producer)
        self.assertIn("current_manifest_member_paths", validator)
        self.assertIn("NONEXACT_FROZEN_INPUT_GRAPH", validator)

    def test_current_manifest_coverage_rejects_extra_file(self):
        with tempfile.TemporaryDirectory() as folder:
            namespace = Path(folder)
            payload_path = namespace / "payload.bin"
            payload_path.write_bytes(b"payload")
            manifest = namespace / "SHA256_MANIFEST.json"
            value = {"files": [{
                "path": "payload.bin", "size_bytes": payload_path.stat().st_size,
                "sha256": hashlib.sha256(payload_path.read_bytes()).hexdigest(),
            }]}
            manifest.write_text(json.dumps(value), encoding="utf-8")
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            self.assertEqual(
                current_manifest_member_paths(namespace, manifest_sha),
                {manifest.resolve(), payload_path.resolve()},
            )
            (namespace / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "CURRENT_MANIFEST_COVERAGE"):
                current_manifest_member_paths(namespace, manifest_sha)


if __name__ == "__main__":
    unittest.main()
