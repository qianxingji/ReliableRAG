import ast
from pathlib import Path
import unittest

from scripts.run_mistral_development_a0_query import (
    EXPECTED_ASSET_MANIFEST_SHA256,
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_INPUT_LEDGER_SHA256,
    EXPECTED_OPERATIONS,
    EXPECTED_POOL_MANIFEST_SHA256,
    EXPECTED_RETRIEVAL_MANIFEST_SHA256,
    EXPECTED_RUNTIME_MANIFEST_SHA256,
    EXPECTED_TRACES,
    validate_frozen_receipt,
)


REPO = Path(__file__).resolve().parents[1]


class MistralDevelopmentA0QueryContractTests(unittest.TestCase):
    def test_pins_counts_and_no_forbidden_stage_text(self):
        self.assertEqual(EXPECTED_TRACES, 13_500)
        self.assertEqual(EXPECTED_OPERATIONS, 27_000)
        for value in (
            EXPECTED_ASSET_MANIFEST_SHA256, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
            EXPECTED_INPUT_LEDGER_SHA256, EXPECTED_POOL_MANIFEST_SHA256,
            EXPECTED_RETRIEVAL_MANIFEST_SHA256, EXPECTED_RUNTIME_MANIFEST_SHA256,
        ):
            self.assertEqual(len(value), 64)
            int(value, 16)
        source = (REPO / "scripts/run_mistral_development_a0_query.py").read_text(encoding="utf-8")
        self.assertIn("project_gold_values_read", source)
        self.assertIn("test_rows_read", source)
        self.assertIn('value["selected_files"]', source)
        self.assertNotIn("score_likelihoods", source)

    def test_frozen_receipt_requires_exact_prompt_token_and_render(self):
        frozen = {
            "answer": {
                "prompt_sha256": "a" * 64, "input_token_ids_sha256": "b" * 64,
                "input_tokens": 3, "context_truncated": False,
                "per_document_truncated": [False] * 5,
            }
        }
        payload = {
            "stage": "a0", "prompt_sha256": "a" * 64,
            "input_token_ids_sha256": "b" * 64, "input_tokens": 3,
            "render": {"context_truncated": False, "per_document_truncated": [False] * 5},
        }
        validate_frozen_receipt(payload, frozen, "a0")
        for field in ("prompt_sha256", "input_token_ids_sha256", "input_tokens"):
            changed = {**payload, field: 4 if field == "input_tokens" else "c" * 64}
            with self.assertRaises(RuntimeError):
                validate_frozen_receipt(changed, frozen, "a0")

    def test_independent_validator_has_no_model_loader(self):
        path = REPO / "scripts/validate_mistral_development_a0_query.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("scripts.run_mistral_development_a0_query", imports)
        self.assertNotIn("src.arbitration.mistral_reader_runtime", imports)
        self.assertNotIn("AutoModelForCausalLM", source)
        self.assertNotIn(".generate(", source)


if __name__ == "__main__":
    unittest.main()
