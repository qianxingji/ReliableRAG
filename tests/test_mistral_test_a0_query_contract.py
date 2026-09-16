from pathlib import Path
import ast
import unittest

from scripts.run_mistral_test_a0_query import (
    EXPECTED_OPERATIONS,
    EXPECTED_QUESTIONS,
    EXPECTED_TRACES,
    object_sha256,
    source_pair as producer_source_pair,
    validate_test_binding as producer_binding,
)
from scripts.validate_mistral_test_a0_query import (
    object_sha,
    source_pair as validator_source_pair,
    validate_test_binding as validator_binding,
)


def trace_and_frozen_rows():
    traces = []
    frozen = []
    position = 0
    for dataset in ("hotpotqa", "2wikimultihopqa", "musique"):
        for question in range(2_000):
            sample_id = f"{dataset}-{question}"
            for retriever in ("bm25", "dense", "hybrid"):
                ids = [f"{dataset}:doc-{question}-{rank}" for rank in range(5)]
                trace = {
                    "dataset": dataset,
                    "retriever": retriever,
                    "sample_id": sample_id,
                    "position": position,
                    "original_top5_ids": ids,
                }
                traces.append(trace)
                frozen.append({
                    "cohort": "test",
                    "dataset": dataset,
                    "retriever": retriever,
                    "sample_id": sample_id,
                    "position": position,
                    "role": "test",
                    "original_top5_ids_sha256": object_sha(ids),
                })
                position += 1
    return traces, frozen


class MistralTestA0QueryContractTests(unittest.TestCase):
    def test_exact_test_counts(self):
        self.assertEqual((EXPECTED_TRACES, EXPECTED_QUESTIONS,
                          EXPECTED_OPERATIONS), (18_000, 6_000, 36_000))
        traces, frozen = trace_and_frozen_rows()
        self.assertEqual(producer_binding(traces, frozen), frozen)
        self.assertEqual(validator_binding(traces, frozen), frozen)

    def test_identity_and_role_mutations_fail_closed(self):
        traces, frozen = trace_and_frozen_rows()
        frozen[0] = dict(frozen[0], role="fit")
        with self.assertRaisesRegex(RuntimeError, "TEST_ROLE"):
            producer_binding(traces, frozen)
        with self.assertRaisesRegex(RuntimeError, "TEST_ROLE"):
            validator_binding(traces, frozen)
        frozen[0] = dict(frozen[0], role="test", sample_id="changed")
        with self.assertRaisesRegex(RuntimeError, "TEST_IDENTITY"):
            producer_binding(traces, frozen)

    def test_source_pair_preserves_frozen_document_order(self):
        trace = {
            "dataset": "hotpotqa", "sample_id": "q1",
            "original_top5_ids": [f"d{i}" for i in range(5)],
        }
        assets = {"hotpotqa": {
            "questions": {"q1": "Where?"},
            "documents": {
                f"d{i}": {
                    "id": f"d{i}", "title": f"T{i}",
                    "sentences": [f"S{i}."], "content_hash": f"h{i}",
                } for i in range(5)
            },
        }}
        produced = producer_source_pair(trace, assets)
        audited = validator_source_pair(trace, assets)
        self.assertEqual(produced, audited)
        self.assertEqual(produced[0], "Where?")
        self.assertEqual([row["document_id"] for row in produced[1]],
                         [f"d{i}" for i in range(5)])
        self.assertEqual(produced[1][0]["text"], "T0\nS0.")

    def test_producer_pins_label_blind_test_sources_and_shared_mutex(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts/run_mistral_test_a0_query.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("EXPECTED_TEST_PREPARATION_MANIFEST_SHA256", source)
        self.assertIn("EXPECTED_TEST_POOL_MANIFEST_SHA256", source)
        self.assertIn("EXPECTED_TEST_TRACE_SHA256", source)
        self.assertIn("validate_selected_manifest", source)
        self.assertNotIn("projected/", source)
        self.assertNotIn("REPLAY_SUBSET_PRIVATE", source)
        self.assertIn("ReliableRAG_Mistral_Development_Acquisition", source)
        self.assertIn('"test_gold_values_read": 0', source)
        self.assertNotIn("runtime_branch_freeze/trace_manifest.jsonl", source)

    def test_validator_imports_no_producer_or_neural_model(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "scripts/validate_mistral_test_a0_query.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)}
        direct = {alias.name for node in ast.walk(tree)
                  if isinstance(node, ast.Import) for alias in node.names}
        self.assertNotIn("scripts.run_mistral_test_a0_query", imported)
        self.assertTrue({"torch", "bitsandbytes"}.isdisjoint(imported | direct))
        self.assertNotIn("MistralNF4Reader", source)
        self.assertIn("PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY",
                      source)

    def test_producer_and_validator_hash_canonicalization_match(self):
        value = {"z": [3, 2, 1], "a": "测试"}
        self.assertEqual(object_sha256(value), object_sha(value))


if __name__ == "__main__":
    unittest.main()
