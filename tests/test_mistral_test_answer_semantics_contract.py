from pathlib import Path
import ast
import hashlib
import tempfile
import unittest

import numpy as np

from scripts.run_mistral_test_answer_semantics import (
    BATCH_SIZE,
    DATASET_ORDER,
    DIMENSION,
    EXPECTED_ANSWERS,
    EXPECTED_BATCHES,
    EXPECTED_TRACES,
    VECTOR_BYTES_PER_ANSWER,
    validate_semantic_payload,
)


class MistralTestAnswerSemanticsContractTests(unittest.TestCase):
    def test_exact_counts_and_order(self):
        self.assertEqual(EXPECTED_TRACES, 18_000)
        self.assertEqual(EXPECTED_ANSWERS, 36_000)
        self.assertEqual(EXPECTED_BATCHES, 2_250)
        self.assertEqual(BATCH_SIZE, 16)
        self.assertEqual(DIMENSION, 768)
        self.assertEqual(
            VECTOR_BYTES_PER_ANSWER * EXPECTED_ANSWERS, 110_592_000
        )
        self.assertEqual(
            DATASET_ORDER, ("hotpotqa", "2wikimultihopqa", "musique")
        )

    def test_payload_recomputes_little_endian_dot_product_and_norm(self):
        bindings = [
            {"position": 0, "answer_state": "a0"},
            {"position": 0, "answer_state": "a1"},
        ]
        token_fields = {
            "input_ids": [[101, 102], [101, 102]],
            "token_type_ids": [[0, 0], [0, 0]],
            "attention_mask": [[1, 1], [1, 1]],
        }
        vectors = np.zeros((2, DIMENSION), dtype="<f4")
        vectors[:, 0] = 1.0
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "vectors/d_0000.f32"
            path.parent.mkdir()
            path.write_bytes(vectors.tobytes(order="C"))
            payload = {
                "dataset": "d",
                "batch_index": 0,
                "global_batch_index": 0,
                "bindings": bindings,
                "token_fields": token_fields,
                "vector_shape": [2, DIMENSION],
                "model_forward_calls": 1,
                "vector": {
                    "path": "vectors/d_0000.f32",
                    "size_bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "dtype": "float32",
                    "shape": [2, DIMENSION],
                    "byte_order": "little",
                },
                "semantic_rows": [{"answer_semantic_agreement": 1.0}],
            }
            validate_semantic_payload(
                payload,
                dataset="d",
                batch_index=0,
                global_batch_index=0,
                bindings=bindings,
                token_fields=token_fields,
                stage_output=root,
            )
            vectors[1, 0] = 0.5
            path.write_bytes(vectors.tobytes(order="C"))
            payload["vector"]["sha256"] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            with self.assertRaisesRegex(
                RuntimeError, "SEMANTIC_VECTOR_NORMALIZATION"
            ):
                validate_semantic_payload(
                    payload,
                    dataset="d",
                    batch_index=0,
                    global_batch_index=0,
                    bindings=bindings,
                    token_fields=token_fields,
                    stage_output=root,
                )

    def test_producer_has_test_witness_gate_and_zero_forbidden_access(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "scripts/run_mistral_test_answer_semantics.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_WITNESS_REPLAY", source
        )
        for marker in (
            "project_gold_values_read",
            "test_gold_values_read",
            "test_outcome_values_read",
            "scientific_fits",
            "ONE_BGE_FORWARD_PER_BATCH",
            "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_ANSWER_SEMANTICS",
        ):
            self.assertIn(marker, source)
        self.assertIn('dtype="<f4"', source)
        self.assertIn('"test_gold_access": "FORBIDDEN"', source)

    def test_validator_is_tokenizer_only_and_independent_of_producer(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "scripts/validate_mistral_test_answer_semantics.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn(
            "scripts.run_mistral_test_answer_semantics", imported_modules
        )
        self.assertNotIn(
            "scripts.mistral_development_scoring_common", imported_modules
        )
        self.assertNotIn(
            "src.arbitration.mistral_reader_runtime", imported_modules
        )
        self.assertNotIn("AutoModel", source)
        self.assertNotIn("ExactLocalBGEBackend", source)
        self.assertIn("AutoTokenizer", source)
        self.assertIn('dtype="<f4"', source)
        self.assertIn("SEMANTIC_DOT_PRODUCT", source)
        self.assertIn(
            "PASS_INDEPENDENT_TOKENIZER_ONLY_", source
        )
        self.assertIn("MISTRAL_TEST_ANSWER_SEMANTICS", source)


if __name__ == "__main__":
    unittest.main()
