"""Contract tests for the value-blind Mistral input freeze."""

from pathlib import Path
import unittest

from scripts.freeze_mistral_reader_inputs import input_paths
from scripts.mistral_reader_input_freeze_common import (
    MAXIMUM_GENERATION_INPUT_TOKENS,
    render_generation_evidence,
    require_generation_admission,
)


class MistralReaderInputFreezeTests(unittest.TestCase):
    def test_generation_admission_exact_boundary(self):
        ids = [[1] * MAXIMUM_GENERATION_INPUT_TOKENS]
        self.assertEqual(
            require_generation_admission(
                stage="a1", input_ids=ids, attention_mask=ids
            ),
            MAXIMUM_GENERATION_INPUT_TOKENS,
        )

    def test_generation_admission_rejects_length_batch_mask_and_stage(self):
        over = [[1] * (MAXIMUM_GENERATION_INPUT_TOKENS + 1)]
        with self.assertRaises(RuntimeError):
            require_generation_admission(
                stage="a0", input_ids=over, attention_mask=over
            )
        with self.assertRaises(RuntimeError):
            require_generation_admission(
                stage="a0", input_ids=[[1], [1]], attention_mask=[[1], [1]]
            )
        with self.assertRaises(RuntimeError):
            require_generation_admission(
                stage="repair_query", input_ids=[[1, 2]], attention_mask=[[1, 0]]
            )
        with self.assertRaises(RuntimeError):
            require_generation_admission(
                stage="unknown", input_ids=[[1]], attention_mask=[[1]]
            )

    def test_render_reserves_all_headers(self):
        evidence = [
            {
                "rank": index,
                "document_id": f"doc-{index}",
                "title": "title",
                "text": "x" * 10000,
            }
            for index in range(1, 6)
        ]
        rendered, truncated, flags = render_generation_evidence(evidence)
        self.assertEqual(len(rendered), 16000)
        self.assertTrue(truncated)
        self.assertEqual(len(flags), 5)
        self.assertTrue(all(f"doc-{index}" in rendered for index in range(1, 6)))

    def test_source_chain_does_not_depend_on_phi_artifacts(self):
        paths = input_paths(
            Path("E:/paper/ReliableRAG"),
            Path("E:/paper/ReliableRAG-mistral-runtime-v1/assets/exact-mistral"),
        )
        lowered = [str(path).casefold() for path in paths]
        self.assertFalse(any("phi_reader" in path for path in lowered))
        self.assertTrue(any("empirical_runtime_preparation_v1" in path for path in lowered))
        self.assertTrue(any("daa_v2_fresh_v1" in path for path in lowered))


if __name__ == "__main__":
    unittest.main()
