from pathlib import Path
import ast
import math
import unittest

from scripts.run_mistral_development_a1_likelihood import (
    EXPECTED_A1_GENERATIONS,
    EXPECTED_LIKELIHOODS,
    EXPECTED_OPERATIONS,
    EXPECTED_TRACES,
    validate_generation_payload,
    validate_likelihood_payload,
)


class MistralDevelopmentA1LikelihoodContractTests(unittest.TestCase):
    def test_exact_counts(self):
        self.assertEqual(EXPECTED_TRACES, 13_500)
        self.assertEqual(EXPECTED_A1_GENERATIONS, 13_500)
        self.assertEqual(EXPECTED_LIKELIHOODS, 54_000)
        self.assertEqual(EXPECTED_OPERATIONS, 67_500)

    def test_generation_and_likelihood_payload_guards(self):
        trace = {"dataset": "d", "retriever": "bm25", "sample_id": "s", "position": 0}
        question, evidence = "q", [{"rank": i} for i in range(1, 6)]
        from src.arbitration.mistral_reader_runtime import object_sha256, text_sha256
        generation = {
            "stage": "a1", **trace, "role": "fit",
            "question_sha256": object_sha256(question),
            "evidence_sha256": object_sha256(evidence),
            "input_tokens": 7, "output_tokens": 2,
            "generated_token_ids": [3, 4], "chosen_log_probabilities": [-1.0, -2.0],
            "compact_schema": "generation-v1-reconstruct-input-from-bound-evidence",
        }
        validate_generation_payload(generation, trace=trace, role="fit",
                                    question=question, private_e1=evidence)
        values = [-1.0, -3.0]
        likelihood = {
            **trace, "role": "fit", "cell": "L11",
            "question_sha256": object_sha256(question),
            "evidence_sha256": object_sha256(evidence),
            "answer_sha256": text_sha256("a"), "target_tokens": 2,
            "prompt_tokens": 7, "total_tokens": 9,
            "chosen_log_probabilities": values,
            "mean_log_probability": float(sum(values) / len(values)),
            "minimum_log_probability": float(min(values)),
            "compact_schema": "likelihood-v1-reconstruct-prompt-and-target-from-bound-branch",
        }
        validate_likelihood_payload(likelihood, trace=trace, role="fit", cell="L11",
                                    question=question, evidence=evidence, answer="a")
        likelihood["mean_log_probability"] = math.nextafter(-2.0, 0.0)
        with self.assertRaisesRegex(RuntimeError, "LIKELIHOOD_SUMMARIES"):
            validate_likelihood_payload(likelihood, trace=trace, role="fit", cell="L11",
                                        question=question, evidence=evidence, answer="a")

    def test_cell_order_and_prerequisite_gates_are_static(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/run_mistral_development_a1_likelihood.py").read_text(encoding="utf-8")
        self.assertIn('"L00": (private_e0, a0)', source)
        self.assertIn('"L01": (private_e1, a0)', source)
        self.assertIn('"L10": (private_e0, a1)', source)
        self.assertIn('"L11": (private_e1, a1)', source)
        self.assertIn("PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY", source)
        self.assertIn("PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_REPAIR", source)

    def test_validator_is_no_model_and_independent_of_producer_adapter(self):
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/validate_mistral_development_a1_likelihood.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("scripts.run_mistral_development_a1_likelihood", imports)
        self.assertNotIn("src.arbitration.mistral_reader_runtime", imports)
        self.assertNotIn("AutoModel", source)
        self.assertNotIn("ExactLocalBGEBackend", source)
        self.assertIn("AutoTokenizer", source)
        self.assertIn("PROMPT_TARGET_PREFIX", source)


if __name__ == "__main__":
    unittest.main()
