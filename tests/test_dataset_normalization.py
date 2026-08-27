"""Unit tests for Phase 0 dataset normalization and label isolation."""

from __future__ import annotations

import unittest

from src.datasets import (
    DatasetFormatError,
    RuntimeExample,
    normalize_2wiki,
    normalize_hotpotqa,
)
from src.datasets.download import _hf_viewer_row_to_authors_json


class DatasetNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_record = {
            "_id": "example-1",
            "question": "Which city is associated with both facts?",
            "answer": "Example City",
            "context": [
                ["First article", ["Sentence zero.", "Sentence one."]],
                ["Second article", ["Another sentence."]],
            ],
            "supporting_facts": [
                ["First article", 1],
                ["Second article", 0],
            ],
        }

    def test_hotpotqa_normalization(self) -> None:
        raw_record = {
            **self.base_record,
            "type": "bridge",
            "level": "hard",
        }
        example = normalize_hotpotqa(raw_record, "dev_distractor")

        self.assertEqual(example.dataset, "hotpotqa")
        self.assertEqual(example.id, "example-1")
        self.assertEqual(len(example.documents), 2)
        self.assertEqual(example.documents[0].sentences[1], "Sentence one.")
        self.assertEqual(
            example.evaluation_only.gold_supporting_facts[0].sentence_index, 1
        )
        self.assertEqual(example.evaluation_only.source_fields["level"], "hard")

    def test_2wiki_normalization_preserves_evaluation_annotations(self) -> None:
        raw_record = {
            **self.base_record,
            "type": "compositional",
            "evidences": [["subject", "relation", "object"]],
            "evidences_id": [["Q1", "P1", "Q2"]],
            "answer_id": "Q2",
            "entity_ids": "Q1_Q2",
        }
        example = normalize_2wiki(raw_record, "dev")

        self.assertEqual(example.dataset, "2wikimultihopqa")
        self.assertEqual(
            example.evaluation_only.source_fields["evidences"][0][1], "relation"
        )
        serialized = example.to_dict()
        self.assertIn("evaluation_only", serialized)
        self.assertNotIn("gold_supporting_facts", serialized)
        self.assertIn(
            "gold_supporting_facts", serialized["evaluation_only"]
        )

    def test_runtime_view_excludes_gold_labels_and_answer(self) -> None:
        example = normalize_hotpotqa(self.base_record, "dev_distractor")
        runtime_example = example.runtime_view()

        self.assertIsInstance(runtime_example, RuntimeExample)
        runtime_record = runtime_example.to_dict()
        self.assertNotIn("answer", runtime_record)
        self.assertNotIn("evaluation_only", runtime_record)
        self.assertNotIn("supporting_facts", runtime_record)

    def test_invalid_context_is_rejected(self) -> None:
        invalid_record = {**self.base_record, "context": "not paragraphs"}
        with self.assertRaises(DatasetFormatError):
            normalize_hotpotqa(invalid_record, "dev_distractor")

    def test_invalid_supporting_fact_is_rejected(self) -> None:
        invalid_record = {
            **self.base_record,
            "supporting_facts": [["First article", -1]],
        }
        with self.assertRaises(DatasetFormatError):
            normalize_2wiki(invalid_record, "dev")

    def test_hugging_face_hotpot_row_adapter(self) -> None:
        viewer_row = {
            "id": "viewer-1",
            "question": "Question?",
            "answer": "Answer",
            "context": {
                "title": ["Article A", "Article B"],
                "sentences": [["A sentence."], ["B sentence."]],
            },
            "supporting_facts": {
                "title": ["Article A"],
                "sent_id": [0],
            },
        }

        converted = _hf_viewer_row_to_authors_json(viewer_row)

        self.assertEqual(converted["_id"], "viewer-1")
        self.assertEqual(converted["context"][1], ["Article B", ["B sentence."]])
        self.assertEqual(converted["supporting_facts"], [["Article A", 0]])


if __name__ == "__main__":
    unittest.main()
