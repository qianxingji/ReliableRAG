import copy
import unittest

from scripts.phi_reader_preflight_common import (
    invented_evidence_rows,
    parse_answer,
    parse_query,
    render_evidence,
    render_generation_evidence,
    validate_logit_witness,
)


class PhiPreflightPureTests(unittest.TestCase):
    def test_short_render_is_complete(self):
        rows = invented_evidence_rows()
        text, cut, per_doc = render_evidence(rows)
        self.assertFalse(cut)
        self.assertEqual(per_doc, [False] * 5)
        self.assertEqual([text.count(f"invented-doc-{i}") for i in range(5)], [1] * 5)

    def test_long_render_hits_character_boundary(self):
        text, cut, per_doc = render_evidence(invented_evidence_rows(long=True))
        self.assertEqual(len(text), 16000)
        self.assertTrue(cut)
        self.assertTrue(any(per_doc))

    def test_generation_render_keeps_all_headers(self):
        text, cut, per_doc = render_generation_evidence(invented_evidence_rows(long=True))
        self.assertEqual(len(text), 16000)
        self.assertTrue(cut)
        self.assertEqual([text.count(f"invented-doc-{i}") for i in range(5)], [1] * 5)
        self.assertEqual(len(per_doc), 5)

    def test_independent_parsers(self):
        self.assertEqual(parse_answer("Final answer: silver\nreason"), "silver")
        self.assertEqual(parse_query("Search Query: silver cog", "fallback"), ("silver cog", False))
        self.assertEqual(parse_query("invented fallback", "question"), ("invented fallback", True))

    def test_logit_witness_reduction_and_counterfeit(self):
        row = {"chosen_logits": [2.0, 3.0], "log_normalizers": [4.0, 4.5],
            "token_log_probabilities": [-2.0, -1.5], "answer_token_count": 2}
        validate_logit_witness(row)
        bad = copy.deepcopy(row)
        bad["token_log_probabilities"][0] += 0.01
        with self.assertRaises(RuntimeError):
            validate_logit_witness(bad)


if __name__ == "__main__":
    unittest.main()
