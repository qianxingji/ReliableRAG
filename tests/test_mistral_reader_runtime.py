import json
from pathlib import Path
import tempfile
import unittest

from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal,
    frozen_witness_positions,
    object_sha256,
    parse_answer,
    parse_repair_query,
    prepare_generation,
    prepare_likelihood,
    require_generation_admission,
)


class FakeTokenizer:
    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        return "<s>[INST] " + messages[0]["content"] + " [/INST]"

    def __call__(self, text, *, add_special_tokens=False, return_tensors=None, truncation=None):
        assert add_special_tokens is False
        if isinstance(text, list):
            assert return_tensors == "pt" and truncation is False and len(text) == 1
            values = list(text[0].encode("utf-8"))
            class Row(list):
                def tolist(self):
                    return list(self)
            return {"input_ids": [Row(values)], "attention_mask": [Row([1] * len(values))]}
        return {"input_ids": list(text.encode("utf-8"))}


def evidence():
    return [
        {"rank": rank, "document_id": f"d{rank}", "title": f"t{rank}", "text": f"body {rank}"}
        for rank in range(1, 6)
    ]


class MistralReaderRuntimeTests(unittest.TestCase):
    def test_guard_and_target_preserving_likelihood_truncation(self):
        self.assertEqual(
            require_generation_admission(stage="a0", input_ids=[[1, 2]], attention_mask=[[1, 1]]), 2
        )
        with self.assertRaisesRegex(RuntimeError, "EXCEEDS_GUARD"):
            require_generation_admission(
                stage="a1", input_ids=[[1] * 8193], attention_mask=[[1] * 8193]
            )
        prepared = prepare_likelihood(
            FakeTokenizer(), template="Q={question}\nE={evidence}" + ("x" * 9000),
            question="invented", evidence=evidence(), answer="target",
        )
        self.assertIs(prepared["token_truncated"], True)
        self.assertEqual(prepared["total_tokens"], 8192)
        self.assertEqual(prepared["target_token_ids"], list(b"target"))
        self.assertEqual(prepared["full_token_ids"][-6:], list(b"target"))

    def test_generation_uses_no_second_special_token_pass(self):
        prepared = prepare_generation(
            FakeTokenizer(), stage="a0", template="Q={question}\nE={evidence}",
            question="invented", evidence=evidence(),
        )
        self.assertEqual(prepared["input_token_ids"][:3], list(b"<s>"))
        self.assertEqual(prepared["attention_mask"], [1] * prepared["input_tokens"])

    def test_journal_resumes_only_pending_exact_input_and_skips_completed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "calls.jsonl"
            first = DurableOperationJournal(path, resume=False)
            digest = object_sha256({"invented": 1})
            self.assertIs(first.begin(operation_key="0:a0", operation="a0", input_sha256=digest), False)
            first.close()

            resumed = DurableOperationJournal(path, resume=True)
            with self.assertRaisesRegex(RuntimeError, "PENDING_OPERATION_INPUT_MISMATCH"):
                resumed.begin(operation_key="0:a0", operation="a0", input_sha256="0" * 64)
            self.assertIs(resumed.begin(operation_key="0:a0", operation="a0", input_sha256=digest), False)
            result = object_sha256({"invented_output": 2})
            resumed.complete(operation_key="0:a0", result_sha256=result)
            resumed.close()

            final = DurableOperationJournal(path, resume=True)
            self.assertIs(final.begin(operation_key="0:a0", operation="a0", input_sha256=digest), True)
            with self.assertRaisesRegex(RuntimeError, "COMPLETED_OPERATION_INPUT_MISMATCH"):
                final.begin(operation_key="0:a0", operation="a0", input_sha256="f" * 64)
            final.close()
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["event"] for row in events], ["intent", "resume_pending", "result"])

    def test_journal_rejects_partial_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "calls.jsonl"
            path.write_bytes(b'{"event":"intent"}')
            with self.assertRaisesRegex(RuntimeError, "PARTIAL_JOURNAL_LINE"):
                DurableOperationJournal(path, resume=True)

    def test_witness_positions_and_parsers(self):
        rows = []
        position = 0
        for dataset in ("hotpotqa", "2wikimultihopqa", "musique"):
            for retriever in ("bm25", "dense", "hybrid"):
                for _ in range(3):
                    rows.append({
                        "cohort": "development", "dataset": dataset,
                        "retriever": retriever, "position": position,
                    })
                    position += 1
        selected = frozen_witness_positions(rows)
        self.assertEqual(len(selected), 18)
        self.assertEqual(parse_answer("Final answer: Paris"), "Paris")
        self.assertEqual(parse_answer("Paris"), "Paris")
        self.assertEqual(
            parse_repair_query("Missing fact: X\nSearch query: alpha beta", "fallback"),
            ("alpha beta", False),
        )
        self.assertEqual(parse_repair_query("line one\nline two", "fallback"), ("line two", True))


if __name__ == "__main__":
    unittest.main()
