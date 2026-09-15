"""ID-only invented fixtures; no reader import or model calls."""
import hashlib
import unittest
from scripts.empirical_runtime_contract import DATASETS, RETRIEVERS, make_traces, replay_subset, trace_key


class RuntimeContractTests(unittest.TestCase):
    def fixture(self):
        return {d: [dict(dataset=d, sample_id="toy-"+str(i), retriever=r, document_ids=["doc-"+str(j) for j in range(5)])
                    for i in range(2000) for r in RETRIEVERS] for d in DATASETS}

    def test_complete_traces_and_independent_replay_selection(self):
        traces = make_traces(self.fixture()); replay = replay_subset(traces)
        self.assertEqual(len(traces), 18000); self.assertEqual(len(replay), 180)
        expected = set()
        for d in DATASETS:
            for r in RETRIEVERS:
                ordered = sorted((hashlib.sha256(f"daa-v2-runtime-replay-v1|{d}|{r}|toy-{i}".encode()).digest(), f"toy-{i}") for i in range(2000))
                expected.update((d, r, sid) for digest, sid in ordered[:20])
        self.assertEqual({trace_key(t) for t in replay}, expected)
        self.assertEqual([t["position"] for t in replay], sorted(t["position"] for t in replay))

    def test_duplicate_trace_and_duplicate_evidence_rejected(self):
        fixture = self.fixture(); fixture[DATASETS[0]][1] = fixture[DATASETS[0]][0]
        with self.assertRaises(ValueError): make_traces(fixture)
        fixture = self.fixture(); fixture[DATASETS[0]][0]["document_ids"] = ["same"] * 5
        with self.assertRaises(ValueError): make_traces(fixture)

    def test_incomplete_stratum_has_no_redraw(self):
        traces = make_traces(self.fixture())
        with self.assertRaises(ValueError): replay_subset(traces[:-1])


if __name__ == "__main__":
    unittest.main()
