import json
from pathlib import Path
import tempfile
import unittest

from scripts.mistral_development_acquisition_common import (
    DurableLedger,
    compact_generation_receipt,
    compact_likelihood_receipt,
    expected_counts,
    operation_key,
    recover_or_execute,
)
from src.arbitration.mistral_reader_runtime import DurableOperationJournal, object_sha256


class MistralDevelopmentAcquisitionCommonTests(unittest.TestCase):
    def test_fixed_operation_counts(self):
        self.assertEqual(expected_counts(), {
            "a0_query_operations": 27_000,
            "repair_operations": 13_500,
            "a1_likelihood_operations": 67_500,
            "generation_calls": 40_500,
            "likelihood_calls": 54_000,
            "total_model_operations": 94_500,
            "total_canonical_operations": 108_000,
            "witness_replay_model_operations": 126,
        })
        self.assertEqual(operation_key(12, "L11"), "00012:L11")

    def test_recovery_never_reexecutes_completed_or_durable_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); journal_path = root / "journal.jsonl"; ledger_path = root / "ledger.jsonl"
            journal = DurableOperationJournal(journal_path, resume=False)
            ledger = DurableLedger(ledger_path, resume=False)
            calls = []
            row, mode = recover_or_execute(
                journal=journal, ledger=ledger, key="00000:a0", operation="a0",
                input_sha256=object_sha256({"x": 1}), execute=lambda: calls.append(1) or {"answer": "a"},
            )
            self.assertEqual(mode, "executed"); self.assertEqual(calls, [1])
            row2, mode2 = recover_or_execute(
                journal=journal, ledger=ledger, key="00000:a0", operation="a0",
                input_sha256=object_sha256({"x": 1}), execute=lambda: calls.append(2) or {"answer": "b"},
            )
            self.assertEqual((row2, mode2), (row, "skipped_completed")); self.assertEqual(calls, [1])
            journal.close(); ledger.close()

            # Simulate crash after a durable result row but before its journal result.
            journal = DurableOperationJournal(journal_path, resume=True)
            ledger = DurableLedger(ledger_path, resume=True)
            pending_hash = object_sha256({"x": 2})
            self.assertFalse(journal.begin(operation_key="00000:a1", operation="a1", input_sha256=pending_hash))
            saved = ledger.append({"operation_key": "00000:a1", "operation": "a1",
                                   "input_sha256": pending_hash, "payload": {"answer": "c"}})
            journal.close(); ledger.close()
            journal = DurableOperationJournal(journal_path, resume=True)
            ledger = DurableLedger(ledger_path, resume=True)
            recovered, mode = recover_or_execute(
                journal=journal, ledger=ledger, key="00000:a1", operation="a1",
                input_sha256=pending_hash, execute=lambda: calls.append(3) or {"answer": "d"},
            )
            self.assertEqual((recovered, mode), (saved, "completed_from_durable_row"))
            self.assertEqual(calls, [1])
            journal.close(); ledger.close()

    def test_interrupted_intent_reissues_only_exact_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); journal_path = root / "journal.jsonl"; ledger_path = root / "ledger.jsonl"
            digest = object_sha256({"fixed": True})
            journal = DurableOperationJournal(journal_path, resume=False)
            journal.begin(operation_key="00001:a0", operation="a0", input_sha256=digest)
            journal.close()
            ledger = DurableLedger(ledger_path, resume=False); ledger.close()
            journal = DurableOperationJournal(journal_path, resume=True)
            ledger = DurableLedger(ledger_path, resume=True)
            with self.assertRaisesRegex(RuntimeError, "PENDING_OPERATION_INPUT_MISMATCH"):
                recover_or_execute(
                    journal=journal, ledger=ledger, key="00001:a0", operation="a0",
                    input_sha256="0" * 64, execute=lambda: {},
                )
            row, mode = recover_or_execute(
                journal=journal, ledger=ledger, key="00001:a0", operation="a0",
                input_sha256=digest, execute=lambda: {"answer": "fixed"},
            )
            self.assertEqual(mode, "reissued_pending")
            self.assertEqual(row["payload"], {"answer": "fixed"})
            events = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([event["event"] for event in events], ["intent", "resume_pending", "result"])
            journal.close(); ledger.close()

    def test_compaction_retains_hashes_counts_and_values(self):
        generation = compact_generation_receipt({
            "stage": "a0", "input_token_ids": [1, 3], "attention_mask": [1, 1],
            "input_token_ids_sha256": object_sha256([1, 3]), "input_tokens": 2,
            "generated_token_ids": [4], "chosen_log_probabilities": [-0.5],
        })
        self.assertNotIn("input_token_ids", generation); self.assertNotIn("attention_mask", generation)
        self.assertEqual(generation["input_tokens"], 2)
        likelihood = compact_likelihood_receipt({
            "prompt_token_ids": [1, 3], "target_token_ids": [4],
            "prompt_token_ids_sha256": object_sha256([1, 3]),
            "target_token_ids_sha256": object_sha256([4]),
            "prompt_tokens": 2, "target_tokens": 1,
            "chosen_log_probabilities": [-0.5], "mean_log_probability": -0.5,
            "minimum_log_probability": -0.5,
        }, cell="L00")
        self.assertNotIn("prompt_token_ids", likelihood); self.assertNotIn("target_token_ids", likelihood)
        self.assertEqual(likelihood["cell"], "L00")


if __name__ == "__main__":
    unittest.main()
