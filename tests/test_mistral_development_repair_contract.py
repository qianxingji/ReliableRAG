from pathlib import Path
import ast
import unittest

from scripts.run_mistral_development_repair import (
    BGE_REVISION,
    EXPECTED_DENSE_QUERY_FORWARDS,
    EXPECTED_TRACES,
    validate_repair_payload,
)


class MistralDevelopmentRepairContractTests(unittest.TestCase):
    def test_counts_identity_and_component_exclusivity(self):
        self.assertEqual(EXPECTED_TRACES, 13_500)
        self.assertEqual(EXPECTED_DENSE_QUERY_FORWARDS, 9_000)
        self.assertEqual(BGE_REVISION, "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a")
        source = (Path(__file__).resolve().parents[1] / "scripts/run_mistral_development_repair.py").read_text(encoding="utf-8")
        self.assertNotIn("MistralNF4Reader", source)
        self.assertNotIn("AutoModelForCausalLM", source)
        self.assertIn("DOCUMENT_REEMBEDDING_FORBIDDEN", source)

    def test_repair_invariants_accept_exact_and_reject_changed_rank(self):
        trace = {"dataset": "d", "retriever": "bm25", "sample_id": "s", "position": 0,
                 "original_top5_ids": ["a", "b", "c", "d", "e"]}
        ranking = [{"document_id": f"x{i}", "rank": i, "score": float(51 - i)} for i in range(1, 51)]
        payload = {
            "dataset": "d", "retriever": "bm25", "sample_id": "s", "position": 0,
            "ranking": ranking, "component_rankings": {"bm25": ranking}, "dense_query_vector": None,
            "e0_ids": ["a", "b", "c", "d", "e"], "e1_ids": ["a", "b", "c", "d", "x1"],
            "inserted_document_id": "x1", "inserted_candidate_rank": 1,
            "replaced_document_id": "e", "requested_depth": 50,
            "replacement_position_zero_based": 4, "repair_retrieval_calls": 1,
            "fail_closed_reason": None,
        }
        validate_repair_payload(payload, trace)
        payload["ranking"][0]["rank"] = 2
        with self.assertRaisesRegex(RuntimeError, "REPAIR_RANKING"):
            validate_repair_payload(payload, trace)

    def test_repair_invariants_reject_unbound_inserted_rank_and_replaced_id(self):
        trace = {"dataset": "d", "retriever": "bm25", "sample_id": "s", "position": 0,
                 "original_top5_ids": ["a", "b", "c", "d", "e"]}
        ranking = [{"document_id": f"x{i}", "rank": i, "score": float(51 - i)} for i in range(1, 51)]
        payload = {
            "dataset": "d", "retriever": "bm25", "sample_id": "s", "position": 0,
            "ranking": ranking, "component_rankings": {"bm25": ranking}, "dense_query_vector": None,
            "e0_ids": ["a", "b", "c", "d", "e"], "e1_ids": ["a", "b", "c", "d", "x1"],
            "inserted_document_id": "x1", "inserted_candidate_rank": 2,
            "replaced_document_id": "e", "requested_depth": 50,
            "replacement_position_zero_based": 4, "repair_retrieval_calls": 1,
            "fail_closed_reason": None,
        }
        with self.assertRaisesRegex(RuntimeError, "REPAIR_INSERTED_RANK"):
            validate_repair_payload(payload, trace)
        payload["inserted_candidate_rank"] = 1
        payload["replaced_document_id"] = "d"
        with self.assertRaisesRegex(RuntimeError, "REPAIR_REPLACEMENT"):
            validate_repair_payload(payload, trace)

    def test_validator_is_no_model_and_independent_of_repair_producer(self):
        source = (Path(__file__).resolve().parents[1] / "scripts/validate_mistral_development_repair.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("scripts.run_mistral_development_repair", imports)
        self.assertNotIn("AutoModel", source)
        self.assertNotIn("ExactLocalBGEBackend", source)
        self.assertIn("SavedVectorBackend", source)


if __name__ == "__main__":
    unittest.main()
