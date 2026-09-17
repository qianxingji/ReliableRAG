import ast
from pathlib import Path
import unittest

from scripts.preflight_mistral_production_adapter import (
    EXPECTED_OPERATION_KEYS,
    EXPECTED_VERSIONS,
    MAX_WITNESS_BYTES,
)


REPO = Path(__file__).resolve().parents[1]


class MistralProductionAdapterPreflightTests(unittest.TestCase):
    def test_fixed_operation_and_witness_budget(self):
        self.assertEqual(len(EXPECTED_OPERATION_KEYS), 7)
        self.assertEqual(EXPECTED_OPERATION_KEYS[:3], (
            "invented:a0", "invented:repair_query", "invented:a1",
        ))
        self.assertEqual(MAX_WITNESS_BYTES, 8 * 1024 * 1024)
        self.assertEqual(EXPECTED_VERSIONS["bitsandbytes"], "0.50.2")
        self.assertEqual(EXPECTED_VERSIONS["transformers"], "4.53.2")

    def test_validator_is_independent_and_no_model_loader(self):
        path = REPO / "scripts/validate_mistral_production_adapter.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("src.arbitration.mistral_reader_runtime", imports)
        self.assertNotIn("scripts.preflight_mistral_production_adapter", imports)
        self.assertNotIn("AutoModelForCausalLM", source)
        self.assertNotIn(".generate(", source)
        self.assertNotIn("outputs/daa", source)
        self.assertNotIn("Gold", source)

    def test_cuda_context_is_initialized_before_peak_reset(self):
        source = (REPO / "scripts/preflight_mistral_production_adapter.py").read_text(encoding="utf-8")
        self.assertLess(
            source.index("torch.cuda.get_device_properties(0)"),
            source.index("torch.cuda.reset_peak_memory_stats(0)"),
        )


if __name__ == "__main__":
    unittest.main()
