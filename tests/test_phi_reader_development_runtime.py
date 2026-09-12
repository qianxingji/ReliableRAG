import tempfile
import unittest
from pathlib import Path

from scripts.phi_reader_development_runtime_common import (
    DurableJsonl,
    GuardedGenerationTokenizer,
    validate_resume_prefix,
)


class FakeTensor:
    def __init__(self, rows): self.rows = rows; self.shape = (len(rows), len(rows[0]))
    def __getitem__(self, index): return self.rows[index]


class FakeTokenizer:
    eos_token_id = 7
    def __call__(self, *args, **kwargs):
        return {"input_ids": FakeTensor([[2, 3]]), "attention_mask": FakeTensor([[1, 1]])}


def trace(position=0):
    return {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": f"s{position}", "position": position}


class PhiDevelopmentRuntimeTests(unittest.TestCase):
    def test_guard_observes_exact_native_batch(self):
        phase = {"stage": "a1", "position": 9}; admissions = []
        value = GuardedGenerationTokenizer(FakeTokenizer(), phase, admissions)(["prompt"], return_tensors="pt")
        self.assertEqual(value["input_ids"].shape, (1, 2))
        self.assertEqual(admissions, [{"stage": "a1", "position": 9, "input_tokens": 2}])

    def test_durable_ledger_round_trip_and_noncanonical_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rows.jsonl"; ledger = DurableJsonl(path, resume=False)
            ledger.append({"b": 2, "a": 1}); ledger.close()
            resumed = DurableJsonl(path, resume=True); self.assertEqual(resumed.rows, [{"a": 1, "b": 2}]); resumed.close()
            path.write_text('{"b":2,"a":1}\n', encoding="utf-8")
            with self.assertRaises(RuntimeError): DurableJsonl(path, resume=True)

    def test_resume_prefix_accepts_one_partial_trace(self):
        traces = [trace(0), trace(1)]
        key = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s0"}
        generations = [dict(key, stage=s) for s in ("a0", "repair_query")]
        ledgers = {"generation_receipts": generations, "repair_bindings": [], "canonical_branches": [], "branch_provenance": []}
        completed, partial = validate_resume_prefix(traces, ledgers)
        self.assertEqual(completed, 0); self.assertEqual(partial["present"]["repair_query"], True)

    def test_resume_prefix_rejects_stage_gap(self):
        traces = [trace(0)]
        key = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s0"}
        ledgers = {"generation_receipts": [dict(key, stage="a1")], "repair_bindings": [], "canonical_branches": [], "branch_provenance": []}
        with self.assertRaises(RuntimeError): validate_resume_prefix(traces, ledgers)


if __name__ == "__main__": unittest.main()
