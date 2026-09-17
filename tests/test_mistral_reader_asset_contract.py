"""Static asset-selection contract tests; no network or model execution."""

import unittest

from scripts.acquire_mistral_reader_assets import (
    EXCLUDED_DUPLICATE,
    EXPECTED_LFS_SHA256,
    EXPECTED_TOTAL_BYTES,
    FILES,
    REPO_ID,
    REVISION,
)


class MistralReaderAssetContractTests(unittest.TestCase):
    def test_exact_identity_and_nonduplicated_weight_selection(self):
        self.assertEqual(REPO_ID, "mistralai/Mistral-7B-Instruct-v0.3")
        self.assertEqual(REVISION, "c170c708c41dac9275d15a8fff4eca08d52bab71")
        self.assertEqual(EXCLUDED_DUPLICATE, "consolidated.safetensors")
        self.assertNotIn(EXCLUDED_DUPLICATE, FILES)
        shards = {name for name in FILES if name.startswith("model-") and name.endswith(".safetensors")}
        self.assertEqual(shards, {
            "model-00001-of-00003.safetensors",
            "model-00002-of-00003.safetensors",
            "model-00003-of-00003.safetensors",
        })
        self.assertEqual(EXPECTED_TOTAL_BYTES, 14_499_392_853)

    def test_all_selected_lfs_payloads_are_prebound(self):
        selected_lfs = {
            "model-00001-of-00003.safetensors",
            "model-00002-of-00003.safetensors",
            "model-00003-of-00003.safetensors",
            "tokenizer.model",
        }
        self.assertEqual(set(EXPECTED_LFS_SHA256), selected_lfs)
        self.assertTrue(all(len(value) == 64 for value in EXPECTED_LFS_SHA256.values()))


if __name__ == "__main__":
    unittest.main()
