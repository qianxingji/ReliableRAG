"""Static tests for the Mistral longest-observed-shape preflight."""

import unittest

from scripts.preflight_mistral_longest_shape import (
    DECODE_STEPS,
    MAX_GPU_RESERVED_BYTES,
    MAX_WITNESS_BYTES,
    MIDDLE_TOKEN_ID,
    MIN_GPU_FREE_BEFORE_BYTES,
    PROMPT_TOKENS,
)


class MistralLongestShapePreflightContractTests(unittest.TestCase):
    def test_exact_accepted_shape_and_invented_content(self):
        self.assertEqual(PROMPT_TOKENS, 3675)
        self.assertEqual(DECODE_STEPS, 64)
        self.assertEqual(MIDDLE_TOKEN_ID, 1000)

    def test_resource_limits_are_finite(self):
        gib = 1024 ** 3
        self.assertEqual(MIN_GPU_FREE_BEFORE_BYTES, 14 * gib)
        self.assertEqual(MAX_GPU_RESERVED_BYTES, 14 * gib)
        self.assertEqual(MAX_WITNESS_BYTES, 12 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
