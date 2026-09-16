from pathlib import Path
import ast
import unittest

from scripts.empirical_feature_independent import check_numeric_tree, feature_pair
from scripts.run_mistral_test_hgb_signal import (
    EXPECTED_TRACES,
    HGB_MODEL_SHA256,
    load_exact_hgb,
)
from scripts.validate_mistral_test_hgb_signal import independent_scores


class MistralTestHGBSignalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state, cls.selector, *_ = load_exact_hgb(Path("E:/paper/ReliableRAG"))

    def test_exact_model_identity_and_feature_width(self):
        self.assertEqual(EXPECTED_TRACES, 18_000)
        self.assertEqual(HGB_MODEL_SHA256,
                         "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e")
        self.assertEqual(self.selector.family, "hgb")
        self.assertEqual(len(self.selector.feature_names), 48)
        self.assertIsNone(self.selector.scaler)

    def test_independent_feature_formula_matches_native_on_invented_pair(self):
        e0 = [
            {"rank": rank, "document_id": f"d{rank}", "content_hash": f"h{rank}",
             "score": 1.0 / rank, "title": f"t{rank}", "text": f"alpha evidence {rank}"}
            for rank in range(1, 6)
        ]
        e1 = [*e0[:4], {
            "rank": 5, "document_id": "new", "content_hash": "hn",
            "score": 0.42, "title": "new", "text": "beta replacement evidence",
        }]
        trace = {
            "dataset": "invented", "retriever": "bm25", "sample_id": "s",
            "split": "test", "a0": "Alpha city", "a1": "Beta city",
            "E0": e0, "E1": e1, "answer_semantic_agreement": 0.25,
        }
        cells = {
            "L00": {"mean_log_probability": -1.0},
            "L01": {"mean_log_probability": -1.3},
            "L10": {"mean_log_probability": -1.4},
            "L11": {"mean_log_probability": -0.8},
        }
        native = self.state.build_pair_record(
            trace, cells, schema_version="mars-state-symmetric-v1",
        )
        independent = feature_pair(trace, cells)
        count, error = check_numeric_tree(native, independent, tolerance=1e-12)
        self.assertGreater(count, 60)
        self.assertLessEqual(error, 1e-12)

    def test_independent_scoring_reconstructs_native_on_invented_zero_vector(self):
        pair = {"features": {name: 0.0 for name in self.selector.feature_names}}
        native = self.selector.scores([pair])
        independent = independent_scores(self.selector, [pair])
        self.assertEqual(native.tolist(), independent.tolist())
        self.assertEqual(native.tolist(), [0.5])

    def test_validator_uses_independent_formula_and_not_producer(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/validate_mistral_test_hgb_signal.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn("scripts.run_mistral_test_hgb_signal", imported_modules)
        self.assertIn("scripts.empirical_feature_independent", imported_modules)
        self.assertNotIn("selector.scores", source)
        self.assertNotIn(".fit(", source)
        self.assertIn("HGB_SCORE_RECONSTRUCTION", source)

    def test_producer_requires_accepted_semantics_and_forbids_neural_runtime(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/run_mistral_test_hgb_signal.py").read_text(encoding="utf-8")
        self.assertIn("PASS_INDEPENDENT_TOKENIZER_ONLY_MISTRAL_TEST_ANSWER_SEMANTICS", source)
        self.assertIn("NEURAL_RUNTIME_LOADED", source)
        self.assertIn("scientific_fits", source)
        self.assertIn("test_input_rows_read", source)
        self.assertIn('"test_gold_access": "FORBIDDEN"', source)
        self.assertIn('"test_outcome_access": "FORBIDDEN"', source)
        self.assertNotIn(".fit(", source)


if __name__ == "__main__":
    unittest.main()
