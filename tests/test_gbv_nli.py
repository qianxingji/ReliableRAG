import unittest

from src.evaluation.answer_normalization import assess_pair_eligibility, normalize_answer
from src.verification.gbv_nli import (
    format_hypothesis,
    resolve_entailment_index,
    split_passage_to_fit,
)


class DummyTokenizer:
    model_max_length = 12

    def __call__(self, premise, hypothesis, **kwargs):
        # One token per whitespace word plus three pair-special tokens.
        ids = list(
            range(len(str(premise).split()) + len(str(hypothesis).split()) + 3)
        )
        return {"input_ids": ids}


class TestNormalization(unittest.TestCase):
    def test_hotpot_style_normalization(self):
        self.assertEqual(normalize_answer("The, Eiffel Tower!"), "eiffel tower")
        self.assertEqual(normalize_answer("  An  Answer "), "answer")

    def test_pair_eligibility(self):
        equal = assess_pair_eligibility("The Cat", "cat")
        self.assertFalse(equal.eligible)
        self.assertEqual(equal.reason, "normalized_answers_equal")
        self.assertTrue(assess_pair_eligibility("cat", "dog").eligible)
        self.assertEqual(assess_pair_eligibility("", "dog").reason, "a0_empty")


class TestGBVHelpers(unittest.TestCase):
    def test_hypothesis_format(self):
        self.assertEqual(
            format_hypothesis("Who?", "Ada"),
            'The answer to the question "Who?" is: "Ada"',
        )

    def test_entailment_label_resolution(self):
        self.assertEqual(
            resolve_entailment_index(
                {0: "ENTAILMENT", 1: "NEUTRAL", 2: "CONTRADICTION"}
            ),
            0,
        )
        with self.assertRaises(ValueError):
            resolve_entailment_index({0: "LABEL_0", 1: "LABEL_1"})

    def test_pinned_binary_entailment_label_resolution(self):
        self.assertEqual(
            resolve_entailment_index({0: "entailment", 1: "not_entailment"}),
            0,
        )

    def test_reversed_binary_entailment_label_resolution(self):
        self.assertEqual(
            resolve_entailment_index({0: "not_entailment", 1: "entailment"}),
            1,
        )

    def test_negative_entailment_substring_does_not_match(self):
        with self.assertRaises(ValueError):
            resolve_entailment_index({0: "not_entailment", 1: "neutral"})

    def test_twenty_word_style_overlap_chunking_contract(self):
        tokenizer = DummyTokenizer()
        passage = "one two three four five six seven eight nine ten"
        chunks = split_passage_to_fit(
            tokenizer,
            passage,
            "h1 h2",
            max_length=12,
            overlap_words=2,
        )
        self.assertEqual(chunks[0], "one two three four five six seven")
        self.assertTrue(chunks[1].startswith("six seven"))
        self.assertEqual(chunks[-1].split()[-1], "ten")
        for chunk in chunks:
            self.assertLessEqual(len(chunk.split()) + 2 + 3, 12)


if __name__ == "__main__":
    unittest.main()
