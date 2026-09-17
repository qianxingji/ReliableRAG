from pathlib import Path
import ast
import hashlib
import json
import tempfile
import unittest

from scripts.run_mistral_test_repair import (
    EXPECTED_DENSE_QUERY_FORWARDS,
    EXPECTED_TRACES,
    validate_repair_payload,
)
from scripts.validate_mistral_test_repair import current_manifest_member_paths


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

    def test_freeze_requires_exact_direct_input_graph(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_test_repair.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_test_repair.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MISTRAL_TEST_REPAIR_INPUT_GRAPH_AMENDMENT", producer)
        self.assertIn("bge_asset_paths", validator)
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
