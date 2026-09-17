"""Static tests for the one-shot Mistral whole-model preflight contract."""

import unittest

from scripts.preflight_mistral_whole_model import (
    ANSWER_PREFLIGHT_MAX_NEW_TOKENS,
    EXPECTED_LINEAR4BIT_MODULES,
    MAX_GPU_RESERVED_BYTES,
    MAX_PROCESS_PEAK_WORKING_SET_BYTES,
    MAX_WALL_SECONDS,
    MAX_WITNESS_BYTES,
    MIN_GPU_FREE_BEFORE_BYTES,
    MIN_RAM_AVAILABLE_BEFORE_BYTES,
    REPAIR_PREFLIGHT_MAX_NEW_TOKENS,
    REQUIRED_ENVIRONMENT,
    REPO_ID,
    REVISION,
    SEED,
)


class MistralWholeModelPreflightContractTests(unittest.TestCase):
    def test_identity_and_finite_fixture_budget(self):
        self.assertEqual(REPO_ID, "mistralai/Mistral-7B-Instruct-v0.3")
        self.assertEqual(REVISION, "c170c708c41dac9275d15a8fff4eca08d52bab71")
        self.assertEqual(SEED, 20260917)
        self.assertEqual(ANSWER_PREFLIGHT_MAX_NEW_TOKENS, 8)
        self.assertEqual(REPAIR_PREFLIGHT_MAX_NEW_TOKENS, 32)
        self.assertEqual(MAX_WITNESS_BYTES, 8 * 1024 * 1024)

    def test_exact_projection_coverage(self):
        self.assertEqual(len(EXPECTED_LINEAR4BIT_MODULES), 224)
        self.assertEqual(len(set(EXPECTED_LINEAR4BIT_MODULES)), 224)
        self.assertIn("model.layers.0.self_attn.q_proj", EXPECTED_LINEAR4BIT_MODULES)
        self.assertIn("model.layers.31.mlp.down_proj", EXPECTED_LINEAR4BIT_MODULES)
        self.assertTrue(all(not name.endswith("lm_head") for name in EXPECTED_LINEAR4BIT_MODULES))

    def test_resource_and_determinism_guards_are_bound(self):
        gib = 1024 ** 3
        self.assertEqual(MIN_GPU_FREE_BEFORE_BYTES, 12 * gib)
        self.assertEqual(MAX_GPU_RESERVED_BYTES, 12 * gib)
        self.assertEqual(MIN_RAM_AVAILABLE_BEFORE_BYTES, 8 * gib)
        self.assertEqual(MAX_PROCESS_PEAK_WORKING_SET_BYTES, 20 * gib)
        self.assertEqual(MAX_WALL_SECONDS, 1200)
        self.assertEqual(REQUIRED_ENVIRONMENT, {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTHONHASHSEED": "0",
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        })


if __name__ == "__main__":
    unittest.main()
