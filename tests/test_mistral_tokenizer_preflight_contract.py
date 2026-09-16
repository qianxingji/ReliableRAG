"""Static tests for the prospectively frozen Mistral tokenizer contract."""

import unittest

from scripts.preflight_mistral_tokenizer import (
    ANSWER_MAX_NEW_TOKENS,
    EXPECTED_TOKENIZER_ASSET_HASHES,
    EXPECTED_VERSIONS,
    EXPECTED_WHEELS,
    GENERATION_PROMPT_GUARD,
    INVENTED_FIXTURES,
    LIKELIHOOD_TOTAL_GUARD,
    REPAIR_QUERY_MAX_NEW_TOKENS,
    REPO_ID,
    REVISION,
)


class MistralTokenizerPreflightContractTests(unittest.TestCase):
    def test_exact_reader_and_runtime_identity(self):
        self.assertEqual(REPO_ID, "mistralai/Mistral-7B-Instruct-v0.3")
        self.assertEqual(REVISION, "c170c708c41dac9275d15a8fff4eca08d52bab71")
        self.assertEqual(EXPECTED_VERSIONS, {
            "transformers": "4.53.2",
            "tokenizers": "0.21.4",
            "sentencepiece": "0.2.1",
            "protobuf": "7.36.1",
        })

    def test_native_tokenizer_assets_and_dependency_wheels_are_hash_bound(self):
        self.assertEqual(set(EXPECTED_TOKENIZER_ASSET_HASHES), {
            "special_tokens_map.json", "tokenizer.json", "tokenizer.model",
            "tokenizer.model.v3", "tokenizer_config.json",
        })
        self.assertEqual(len(EXPECTED_WHEELS), 2)
        self.assertTrue(all(len(value) == 64 for value in EXPECTED_WHEELS.values()))
        self.assertTrue(all(len(value) == 64 for value in EXPECTED_TOKENIZER_ASSET_HASHES.values()))

    def test_length_and_fixture_scope_is_finite(self):
        self.assertEqual(GENERATION_PROMPT_GUARD, 8192)
        self.assertEqual(LIKELIHOOD_TOTAL_GUARD, 8192)
        self.assertEqual(ANSWER_MAX_NEW_TOKENS, 48)
        self.assertEqual(REPAIR_QUERY_MAX_NEW_TOKENS, 64)
        self.assertEqual(len(INVENTED_FIXTURES), 3)
        self.assertEqual({row["prompt_kind"] for row in INVENTED_FIXTURES}, {"answer", "repair"})


if __name__ == "__main__":
    unittest.main()
