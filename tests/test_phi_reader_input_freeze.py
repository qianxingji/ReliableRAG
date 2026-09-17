import unittest

from scripts.phi_reader_input_freeze_common import (
    MAXIMUM_GENERATION_INPUT_TOKENS,
    render_generation_evidence,
    require_generation_admission,
)


class PhiReaderInputFreezeTests(unittest.TestCase):
    def test_generation_admission_exact_boundary(self):
        ids = [[1] * MAXIMUM_GENERATION_INPUT_TOKENS]
        self.assertEqual(require_generation_admission(stage="a1", input_ids=ids, attention_mask=ids), MAXIMUM_GENERATION_INPUT_TOKENS)

    def test_generation_admission_rejects_overlength(self):
        ids = [[1] * (MAXIMUM_GENERATION_INPUT_TOKENS + 1)]
        with self.assertRaises(RuntimeError):
            require_generation_admission(stage="a0", input_ids=ids, attention_mask=ids)

    def test_generation_admission_rejects_batch_mask_and_stage(self):
        with self.assertRaises(RuntimeError):
            require_generation_admission(stage="a0", input_ids=[[1], [1]], attention_mask=[[1], [1]])
        with self.assertRaises(RuntimeError):
            require_generation_admission(stage="a0", input_ids=[[1, 2]], attention_mask=[[1, 0]])
        with self.assertRaises(RuntimeError):
            require_generation_admission(stage="unknown", input_ids=[[1]], attention_mask=[[1]])

    def test_render_reserves_all_headers(self):
        evidence = [{"rank": i, "document_id": f"doc-{i}", "title": "title", "text": "x" * 10000} for i in range(1, 6)]
        text, truncated, flags = render_generation_evidence(evidence)
        self.assertEqual(len(text), 16000)
        self.assertTrue(truncated)
        self.assertEqual(len(flags), 5)
        self.assertTrue(all(f"doc-{i}" in text for i in range(1, 6)))


if __name__ == "__main__":
    unittest.main()
