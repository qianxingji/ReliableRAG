import ast
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from scripts.run_mistral_test_a1_likelihood import (
    EXPECTED_A1_GENERATIONS,
    EXPECTED_LIKELIHOODS,
    EXPECTED_OPERATIONS,
    EXPECTED_TRACES,
    reconstruct_e1,
    validate_generation_payload,
    validate_likelihood_payload,
)
from scripts.validate_mistral_test_a0_query import current_manifest_member_paths


def trace():
    return {
        "dataset": "hotpotqa",
        "retriever": "dense",
        "sample_id": "q1",
        "position": 0,
    }


def evidence(document_id, rank):
    return {
        "rank": rank,
        "document_id": document_id,
        "title": "Title " + document_id,
        "text": "Text " + document_id,
        "content_hash": str(rank) * 64,
    }


class MistralTestA1LikelihoodContractTests(unittest.TestCase):
    def test_exact_operation_counts(self):
        self.assertEqual(EXPECTED_TRACES, 18_000)
        self.assertEqual(EXPECTED_A1_GENERATIONS, 18_000)
        self.assertEqual(EXPECTED_LIKELIHOODS, 72_000)
        self.assertEqual(EXPECTED_OPERATIONS, 90_000)

    def test_reconstruct_e1_changes_only_rank_five(self):
        e0 = [evidence(f"d{i}", i) for i in range(1, 6)]
        assets = {"hotpotqa": {"documents": {
            "d6": {
                "id": "d6", "title": "Title d6", "sentences": ["Text d6"],
                "content_hash": "6" * 64, "dataset": "hotpotqa",
            },
        }}}
        repair = {
            "inserted_document_id": "d6",
            "inserted_candidate_rank": 6,
            "ranking": [
                {"document_id": f"d{i}", "rank": i, "score": 1.0 / i}
                for i in range(1, 51)
            ],
            "e0_ids": [f"d{i}" for i in range(1, 6)],
            "e1_ids": ["d1", "d2", "d3", "d4", "d6"],
            "replaced_document_id": "d5",
        }
        e1 = reconstruct_e1(e0, repair, assets, "hotpotqa")
        self.assertEqual([row["document_id"] for row in e1],
                         ["d1", "d2", "d3", "d4", "d6"])
        self.assertEqual(e1[4]["rank"], 5)

    def test_generation_and_likelihood_payload_guards(self):
        value = trace()
        e1 = [evidence(f"d{i}", i) for i in range(1, 6)]
        from src.arbitration.mistral_reader_runtime import (
            object_sha256, text_sha256,
        )
        generation = {
            "stage": "a1", **value, "role": "test",
            "question_sha256": object_sha256("Question?"),
            "evidence_sha256": object_sha256(e1),
            "input_tokens": 12, "output_tokens": 2,
            "generated_token_ids": [1, 2],
            "chosen_log_probabilities": [-1.0, -2.0],
            "compact_schema":
                "generation-v1-reconstruct-input-from-bound-evidence",
        }
        validate_generation_payload(
            generation, trace=value, question="Question?", private_e1=e1,
        )
        generation["role"] = "fit"
        with self.assertRaisesRegex(RuntimeError, "A1_IDENTITY"):
            validate_generation_payload(
                generation, trace=value, question="Question?", private_e1=e1,
            )

        likelihood = {
            **value, "role": "test", "cell": "L11",
            "question_sha256": object_sha256("Question?"),
            "evidence_sha256": object_sha256(e1),
            "answer_sha256": text_sha256("Answer"),
            "chosen_log_probabilities": [-1.0, -2.0],
            "target_tokens": 2, "prompt_tokens": 10, "total_tokens": 12,
            "mean_log_probability": -1.5,
            "minimum_log_probability": -2.0,
            "compact_schema":
                "likelihood-v1-reconstruct-prompt-and-target-from-bound-branch",
        }
        validate_likelihood_payload(
            likelihood, trace=value, cell="L11", question="Question?",
            evidence=e1, answer="Answer",
        )
        likelihood["mean_log_probability"] = math.nextafter(-1.5, 0.0)
        with self.assertRaisesRegex(RuntimeError, "LIKELIHOOD_SUMMARIES"):
            validate_likelihood_payload(
                likelihood, trace=value, cell="L11", question="Question?",
                evidence=e1, answer="Answer",
            )

    def test_producer_requires_both_accepted_predecessors(self):
        root = Path(__file__).resolve().parents[1]
        source = (
            root / "scripts/run_mistral_test_a1_likelihood.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY", source,
        )
        self.assertIn(
            "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_REPAIR", source,
        )
        self.assertIn('"L00": (private_e0, a0)', source)
        self.assertIn('"L01": (private_e1, a0)', source)
        self.assertIn('"L10": (private_e0, a1)', source)
        self.assertIn('"L11": (private_e1, a1)', source)
        self.assertIn('"test_gold_values_read": 0', source)
        self.assertIn('"scientific_fits": 0', source)
        self.assertIn("BGE/NLI/Gold/fit/tuning forbidden", source)

    def test_validator_is_independent_and_no_model(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "scripts/validate_mistral_test_a1_likelihood.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn("scripts.run_mistral_test_a1_likelihood", imports)
        self.assertNotIn("MistralNF4Reader", source)
        self.assertNotIn("torch", source)
        self.assertIn("PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_A1_LIKELIHOOD",
                      source)
        self.assertIn("source_prompts_reconstructed", source)

    def test_freeze_requires_exact_direct_input_graph(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_test_a1_likelihood.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_test_a1_likelihood.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MISTRAL_TEST_A1_INPUT_GRAPH_AMENDMENT", producer)
        self.assertIn("current_manifest_member_paths", validator)
        self.assertIn("asset_member_paths", validator)
        self.assertIn("NONEXACT_FROZEN_INPUT_GRAPH", validator)

    def test_current_manifest_coverage_rejects_extra_file(self):
        with tempfile.TemporaryDirectory() as folder:
            namespace = Path(folder)
            payload = namespace / "payload.bin"; payload.write_bytes(b"payload")
            manifest = namespace / "SHA256_MANIFEST.json"
            value = {
                "status": "PASS", "exact_recursive_coverage": True,
                "files": [{
                    "path": "payload.bin", "size_bytes": payload.stat().st_size,
                    "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
                }],
            }
            manifest.write_text(json.dumps(value), encoding="utf-8")
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            self.assertEqual(
                current_manifest_member_paths(namespace, manifest_sha),
                {manifest.resolve(), payload.resolve()},
            )
            (namespace / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "CURRENT_MANIFEST_COVERAGE"):
                current_manifest_member_paths(namespace, manifest_sha)


if __name__ == "__main__":
    unittest.main()
