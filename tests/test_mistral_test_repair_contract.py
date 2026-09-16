from pathlib import Path
import ast
import unittest

from scripts.run_mistral_test_repair import (
    EXPECTED_DENSE_QUERY_FORWARDS,
    EXPECTED_TRACES,
    validate_repair_payload,
)


def trace(retriever="dense"):
    return {
        "dataset": "hotpotqa", "retriever": retriever,
        "sample_id": "q1", "position": 0,
        "original_top5_ids": [f"d{i}" for i in range(1, 6)],
    }


def payload(retriever="dense"):
    component_names = ("bm25", "dense") if retriever == "hybrid" else (retriever,)
    return {
        "dataset": "hotpotqa", "retriever": retriever,
        "sample_id": "q1", "position": 0, "role": "test",
        "query_sha256": "0" * 64,
        "ranking": [
            {"document_id": f"d{i}", "rank": i, "score": 1.0 / i}
            for i in range(1, 51)
        ],
        "component_rankings": {name: [] for name in component_names},
        "dense_query_vector": None if retriever == "bm25" else [0.0] * 768,
        "e0_ids": [f"d{i}" for i in range(1, 6)],
        "e1_ids": ["d1", "d2", "d3", "d4", "d6"],
        "inserted_document_id": "d6", "inserted_candidate_rank": 6,
        "replaced_document_id": "d5",
        "replacement_position_zero_based": 4,
        "requested_depth": 50, "repair_retrieval_calls": 1,
        "pool_sha256": "1" * 64, "fail_closed_reason": None,
    }


class MistralTestRepairContractTests(unittest.TestCase):
    def test_exact_trace_and_dense_query_counts(self):
        self.assertEqual(EXPECTED_TRACES, 18_000)
        self.assertEqual(EXPECTED_DENSE_QUERY_FORWARDS, 12_000)

    def test_payload_accepts_all_three_retrievers(self):
        for retriever in ("bm25", "dense", "hybrid"):
            with self.subTest(retriever=retriever):
                validate_repair_payload(payload(retriever), trace(retriever))

    def test_changed_rank_five_and_inserted_rank_fail_closed(self):
        value = payload()
        value["replaced_document_id"] = "d4"
        with self.assertRaisesRegex(RuntimeError, "REPAIR_REPLACEMENT"):
            validate_repair_payload(value, trace())
        value = payload()
        value["inserted_candidate_rank"] = 7
        with self.assertRaisesRegex(RuntimeError, "REPAIR_INSERTED_RANK"):
            validate_repair_payload(value, trace())

    def test_producer_requires_accepted_a0_and_forbids_other_components(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts/run_mistral_test_repair.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("validate_a0_gate(root)", source)
        self.assertIn("PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY",
                      source)
        self.assertIn("EXPECTED_RETRIEVAL_MANIFEST_SHA256", source)
        self.assertIn("EXPECTED_BGE_PREFLIGHT_MANIFEST_SHA256", source)
        self.assertIn('"mistral_model_loads": 0', source)
        self.assertIn('"nli_model_loads": 0', source)
        self.assertIn('"test_gold_values_read": 0', source)
        self.assertIn("DOCUMENT_REEMBEDDING_FORBIDDEN", source)
        self.assertNotIn("MistralNF4Reader", source)

    def test_validator_is_no_model_and_independent_of_repair_producer(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "scripts/validate_mistral_test_repair.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)}
        direct = {alias.name for node in ast.walk(tree)
                  if isinstance(node, ast.Import) for alias in node.names}
        self.assertNotIn("scripts.run_mistral_test_repair", imported)
        self.assertTrue({"torch", "transformers"}.isdisjoint(imported | direct))
        self.assertNotIn("ExactLocalBGEBackend", source)
        self.assertIn("PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_REPAIR", source)
        self.assertIn("SavedVectorBackend", source)


if __name__ == "__main__":
    unittest.main()
