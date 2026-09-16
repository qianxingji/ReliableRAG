from pathlib import Path
import tempfile
import unittest

from scripts.mistral_development_scoring_common import DurableStageJournal, write_bytes_once
from src.arbitration.mistral_reader_runtime import object_sha256


class MistralDevelopmentScoringCommonTests(unittest.TestCase):
    def test_journal_exact_resume_and_result(self):
        digest = object_sha256({"x": 1})
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "journal.jsonl"
            journal = DurableStageJournal(path, resume=False, allowed_operations={"batch"})
            self.assertFalse(journal.begin(operation_key="k", operation="batch", input_sha256=digest))
            journal.close()
            journal = DurableStageJournal(path, resume=True, allowed_operations={"batch"})
            self.assertFalse(journal.begin(operation_key="k", operation="batch", input_sha256=digest))
            journal.complete(operation_key="k", result_sha256=digest); journal.close()
            journal = DurableStageJournal(path, resume=True, allowed_operations={"batch"})
            self.assertTrue(journal.begin(operation_key="k", operation="batch", input_sha256=digest))
            journal.close()

    def test_journal_rejects_operation_vocabulary_change(self):
        digest = object_sha256({"x": 1})
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "journal.jsonl"
            journal = DurableStageJournal(path, resume=False, allowed_operations={"batch"})
            journal.begin(operation_key="k", operation="batch", input_sha256=digest); journal.close()
            with self.assertRaisesRegex(RuntimeError, "JOURNAL_OPERATION"):
                DurableStageJournal(path, resume=True, allowed_operations={"other"})

    def test_durable_bytes_are_idempotent_and_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "value.bin"
            write_bytes_once(path, b"abc"); write_bytes_once(path, b"abc")
            self.assertEqual(path.read_bytes(), b"abc")
            with self.assertRaisesRegex(RuntimeError, "EXISTING_DURABLE_BYTES_MISMATCH"):
                write_bytes_once(path, b"abd")


if __name__ == "__main__":
    unittest.main()
