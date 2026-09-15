"""Synthetic only: native parser barriers and independent pool semantics."""
import io
import json
from pathlib import Path
import unittest

from scripts.empirical_pool_io import checked, load_native
from scripts.verify_roa_artifacts import digest
from scripts.validate_roa_empirical_pool import runtime_from_projection, independent_pool, parse_json


class EmpiricalPoolTests(unittest.TestCase):
    def setUp(self):
        root = Path("E:/paper/ReliableRAG")
        helper = root / "outputs/daa_v2_fresh_v1/pool_freeze/pool_support.py"
        # Tests exercise the byte-authenticated original helper, never raw data.
        manifest = json.loads((helper.parent / "SHA256_MANIFEST.json").read_text(encoding="utf-8"))
        entry = next(e for e in manifest["files"] if e["path"].endswith("pool_freeze/pool_support.py"))
        checked(helper, entry["sha256"], entry["size_bytes"])
        self.native = load_native(helper, root)
        self.accepted, _ = self.native.load_accepted()
        self.gate = self.native.MaterializationGate(self.accepted)

    def project(self, value, dataset="2wikimultihopqa"):
        return self.accepted.project_single_synthetic_object(json.dumps(value).encode(), dataset=dataset,
            wanted_id="toy", observer=self.gate.observer)

    def row(self):
        return dict(_id="toy", question="Invented?", context=[["Toy", ["A.", "B."]]])

    def test_forbidden_scalar_blocked_before_decode(self):
        stream = io.BytesIO(b'"SYNTHETIC_NEVER_DECODE"')
        cursor = self.accepted._JSONByteCursor(stream)
        with self.assertRaises(RuntimeError):
            cursor.read_string(path="2wikimultihopqa.answer")
        self.assertEqual(stream.tell(), 0)

    def test_skip_gold_and_unselected_runtime(self):
        selected = self.row()
        payload = json.dumps([dict(selected, _id="unselected", question={"unused": True}),
                              dict(selected, answer={"skip": [True, "SYNTHETIC"]}, supporting_facts=["SYNTHETIC"])]).encode()
        rows = self.accepted.project_selected_stream(lambda: io.BytesIO(payload), dataset="2wikimultihopqa",
            wanted={"toy"}, json_lines=False, observer=self.gate.observer)
        self.assertEqual(rows, [selected])
        self.assertEqual(self.gate.counts["2wikimultihopqa.question"], 1)
        self.assertEqual(self.gate.denied, 0)

    def test_unknown_and_duplicate_fields_rejected(self):
        with self.assertRaises(RuntimeError):
            self.project(dict(self.row(), unknown_label="SYNTHETIC"))
        with self.assertRaises(RuntimeError):
            parse_json('{"id":"toy","id":"toy"}')

    def test_musique_projection_and_adapter_match(self):
        row = dict(id="toy", question="Invented?", paragraphs=[dict(idx=3, title="Toy", paragraph_text="A. B.", is_supporting=True)])
        projected = self.project(dict(row, answer="SYNTHETIC"), "musique")
        expected = self.accepted._musique_runtime(projected, split="train").to_dict()
        self.assertEqual(runtime_from_projection(projected, "musique"), expected)
        self.assertEqual(expected["documents"][0]["sentences"], ["A. B."])
        row["paragraphs"].append(dict(row["paragraphs"][0]))
        with self.assertRaises(RuntimeError):
            self.project(row, "musique")

    def test_native_and_independent_pool_full_semantics(self):
        raw = self.row()
        raw["context"] += [["Second", ["AB"]], ["Toy", ["A.", "B."]], ["Toy", ["A.B."]]]
        projected = self.project(raw)
        native = self.accepted._hotpot_or_2wiki_runtime(projected, dataset="2wikimultihopqa", split="dev")
        independent = runtime_from_projection(projected, "2wikimultihopqa")
        self.assertEqual(independent, native.to_dict())
        actual = self.accepted.build_pooled_corpus([native])
        expected, counts = independent_pool([independent], "2wikimultihopqa")
        self.assertEqual(expected, [dict(id=d.id, dataset=d.dataset, title=d.title, sentences=list(d.sentences), content_hash=d.content_hash) for d in actual.documents])
        self.assertEqual(counts["duplicates_removed"], 1)
        self.assertEqual(counts["corpus_fingerprint"], actual.fingerprint)

    def test_original_title_collision_not_silently_merged(self):
        raw = self.row()
        raw["context"].append([" toy ", ["A.", "B."]])
        native = self.accepted._hotpot_or_2wiki_runtime(raw, dataset="2wikimultihopqa", split="dev")
        with self.assertRaises(RuntimeError):
            self.accepted.build_pooled_corpus([native])
        with self.assertRaises(RuntimeError):
            independent_pool([runtime_from_projection(raw, "2wikimultihopqa")], "2wikimultihopqa")


if __name__ == "__main__":
    unittest.main()
