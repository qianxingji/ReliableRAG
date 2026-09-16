from pathlib import Path
import ast
import math
import tempfile
import unittest

import numpy as np

from scripts.run_mistral_development_witness_replay import (
    EXPECTED_OPERATIONS,
    EXPECTED_POSITIONS,
    OPERATIONS,
    VECTOR_BYTES,
    VECTOR_SIZE,
    vector_log_probability,
    write_vector_once,
)


class MistralDevelopmentWitnessReplayContractTests(unittest.TestCase):
    def test_exact_position_operation_and_vector_counts(self):
        self.assertEqual(EXPECTED_POSITIONS, 18)
        self.assertEqual(OPERATIONS, ("a0", "repair_query", "a1", "L00", "L01", "L10", "L11"))
        self.assertEqual(EXPECTED_OPERATIONS, 126)
        self.assertEqual(VECTOR_SIZE, 32_768)
        self.assertEqual(VECTOR_BYTES * EXPECTED_OPERATIONS, 16_515_072)

    def test_vector_is_raw_float32_durable_and_mismatch_fails(self):
        vector = np.zeros(VECTOR_SIZE, dtype=np.float32)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "v.f32"
            first = write_vector_once(path, vector)
            second = write_vector_once(path, vector.copy())
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(path.stat().st_size, VECTOR_BYTES)
            self.assertAlmostEqual(vector_log_probability(vector, 7), -math.log(VECTOR_SIZE), places=12)
            changed = vector.copy(); changed[0] = 1.0
            with self.assertRaisesRegex(RuntimeError, "EXISTING_VECTOR_MISMATCH"):
                write_vector_once(path, changed)

    def test_producer_has_all_prior_independent_gates(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/run_mistral_development_witness_replay.py").read_text(encoding="utf-8")
        for status in (
            "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY",
            "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_REPAIR",
            "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_A1_LIKELIHOOD",
        ):
            self.assertIn(status, source)
        self.assertIn("EXISTING_VECTOR_MISMATCH", source)
        self.assertIn("REPLAY_NOT_CANONICAL", source)

    def test_validator_is_tokenizer_only_and_independent_of_replay_producer(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/validate_mistral_development_witness_replay.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn("scripts.run_mistral_development_witness_replay", imported_modules)
        self.assertNotIn("src.arbitration.mistral_reader_runtime", imported_modules)
        self.assertNotIn("AutoModel", source)
        self.assertNotIn("ExactLocalBGEBackend", source)
        self.assertIn("AutoTokenizer", source)
        self.assertIn("SOFTMAX_RECOMPUTATION", source)


if __name__ == "__main__":
    unittest.main()
