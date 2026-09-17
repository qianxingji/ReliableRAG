from pathlib import Path
import ast
import hashlib
import json
import tempfile
import unittest

from scripts.empirical_outcome_independent import metrics
from scripts.run_mistral_test_outcomes import (
    EXPECTED_DATASET_QUESTIONS,
    EXPECTED_METRIC_VALUES,
    EXPECTED_QUESTIONS,
    EXPECTED_TRACES,
    OUTCOME_FIELDS,
    answer_maps,
    metric_values,
    test_action_scope as producer_action_scope,
    validate_manifest as producer_manifest,
)
from scripts.validate_mistral_test_outcomes import (
    action_groups, validate_manifest as validator_manifest,
)


class NativeMetric:
    @staticmethod
    def exact_match(answer, references):
        return metrics(answer, references)[0]

    @staticmethod
    def token_f1(answer, references):
        return metrics(answer, references)[1]


def action_rows():
    rows = []
    for dataset in ("hotpotqa", "2wikimultihopqa", "musique"):
        for question in range(EXPECTED_DATASET_QUESTIONS):
            sample_id = f"{dataset}-{question}"
            for retriever in ("bm25", "dense", "hybrid"):
                rows.append({
                    "dataset": dataset,
                    "retriever": retriever,
                    "sample_id": sample_id,
                    "eligible": True,
                    "scores": {},
                    "actions": {},
                    "forced_keep_reason": None,
                })
    return rows


def write_rows(path, rows):
    with path.open("wb") as handle:
        for row in rows:
            handle.write(json.dumps(
                row, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            ).encode("utf-8") + b"\n")


class MistralTestOutcomesContractTests(unittest.TestCase):
    def test_exact_test_scope_and_numeric_count(self):
        self.assertEqual((EXPECTED_TRACES, EXPECTED_QUESTIONS,
                          EXPECTED_DATASET_QUESTIONS, EXPECTED_METRIC_VALUES),
                         (18_000, 6_000, 2_000, 72_000))
        rows = action_rows()
        self.assertEqual(producer_action_scope(rows), action_groups(rows))
        self.assertEqual(len(producer_action_scope(rows)), EXPECTED_QUESTIONS)

    def test_duplicate_identity_fails_closed(self):
        rows = action_rows()
        rows[-1] = dict(rows[0])
        with self.assertRaisesRegex(RuntimeError,
                                    "UNIQUE_TEST_ACTION_IDENTITY"):
            producer_action_scope(rows)
        with self.assertRaisesRegex(RuntimeError,
                                    "UNIQUE_TEST_ACTION_IDENTITY"):
            action_groups(rows)

    def test_missing_trace_fails_closed(self):
        rows = action_rows()[:-1]
        with self.assertRaisesRegex(RuntimeError, "TEST_ACTION_COUNT"):
            producer_action_scope(rows)
        with self.assertRaisesRegex(RuntimeError, "TEST_ACTION_COUNT"):
            action_groups(rows)

    def test_native_and_independent_metrics_match_edge_cases(self):
        cases = (
            ("The, Capital!", ["capital"]),
            ("yes", ["no", "yes"]),
            ("noanswer", ["no answer"]),
            ("a a b", ["a b b"]),
            ("", [""]),
            ("Wuhan", ["Hubei", "Wuhan"]),
        )
        for answer, references in cases:
            with self.subTest(answer=answer, references=references):
                actual = metric_values(NativeMetric, answer, answer, references)
                expected = metrics(answer, references)
                self.assertEqual(actual["a0_em"], expected[0])
                self.assertEqual(actual["a0_f1"], expected[1])
                self.assertEqual(actual["a1_em"], expected[0])
                self.assertEqual(actual["a1_f1"], expected[1])

    def test_invalid_metric_input_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "OUTCOME_METRIC_INPUT"):
            metric_values(NativeMetric, "answer", "answer", [])
        with self.assertRaisesRegex(RuntimeError, "OUTCOME_METRIC_INPUT"):
            metric_values(NativeMetric, "answer", "answer", [1])

    def test_answer_maps_select_only_a0_and_a1(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a0 = root / "a0.jsonl"
            a1 = root / "a1.jsonl"
            write_rows(a0, [
                {"operation": "a0", "payload": {"position": 0}},
                {"operation": "repair_query", "payload": {"position": 0}},
            ])
            write_rows(a1, [
                {"operation": "a1", "payload": {"position": 0}},
                {"operation": "likelihood", "payload": {"position": 0}},
                {"operation": "likelihood", "payload": {"position": 0}},
                {"operation": "likelihood", "payload": {"position": 0}},
                {"operation": "likelihood", "payload": {"position": 0}},
            ])
            import scripts.run_mistral_test_outcomes as module
            old = module.EXPECTED_TRACES
            module.EXPECTED_TRACES = 1
            try:
                produced0, produced1 = answer_maps(a0, a1)
            finally:
                module.EXPECTED_TRACES = old
            self.assertEqual(produced0, {0: {"position": 0}})
            self.assertEqual(produced1, {0: {"position": 0}})

    def test_outcome_schema_is_numeric_only(self):
        self.assertEqual(OUTCOME_FIELDS, {
            "dataset", "retriever", "sample_id",
            "a0_em", "a1_em", "a0_f1", "a1_f1",
        })
        self.assertTrue({"question", "references", "answer", "a0", "a1"}
                        .isdisjoint(OUTCOME_FIELDS))

    def test_action_acceptance_precedes_gold_access(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts/run_mistral_test_outcomes.py").read_text(
            encoding="utf-8"
        )
        main = source[source.index("def main()"):]
        self.assertLess(main.index("validate_action_gate(root)"),
                        main.index("GOLD_ACCESS_STARTED.json"))
        self.assertLess(main.index("GOLD_ACCESS_STARTED.json"),
                        main.index("test_references("))
        self.assertIn("DETAILS_WITHHELD_TO_PREVENT_TEST_REFERENCE_TEXT_LOGGING",
                      source)
        self.assertIn('"raw_reference_strings_written": 0', source)

    def test_validator_is_independent_model_free_and_recomputes_metrics(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "scripts/validate_mistral_test_outcomes.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)}
        direct = {alias.name for node in ast.walk(tree)
                  if isinstance(node, ast.Import) for alias in node.names}
        self.assertNotIn("scripts.run_mistral_test_outcomes", imported)
        self.assertIn("scripts.empirical_outcome_independent", imported)
        self.assertTrue({"torch", "transformers", "sklearn"}.isdisjoint(
            imported | direct
        ))
        self.assertIn("PASS_INDEPENDENT_MISTRAL_TEST_OUTCOMES", source)
        self.assertIn("expected0 = metrics", source)
        self.assertIn("expected1 = metrics", source)

    def test_outcome_freeze_requires_exact_recursive_input_graph(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_test_outcomes.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_test_outcomes.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MISTRAL_TEST_OUTCOMES_INPUT_GRAPH_AMENDMENT", producer)
        self.assertIn("NONEXACT_FROZEN_INPUT_GRAPH", validator)
        self.assertIn("authenticated_paths", validator)

    def test_outcome_manifest_path_sets_reject_unexpected_file(self):
        with tempfile.TemporaryDirectory() as directory:
            namespace = Path(directory)
            member = namespace / "member.txt"
            member.write_bytes(b"invented-only\n")
            manifest_path = namespace / "SHA256_MANIFEST.json"
            manifest_path.write_text(json.dumps({
                "status": "PASS",
                "files": [{
                    "path": "member.txt", "size_bytes": member.stat().st_size,
                    "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                }],
                "excludes_only": "SHA256_MANIFEST.json",
                "exact_recursive_coverage": True,
            }), encoding="utf-8")
            expected = {manifest_path.resolve(), member.resolve()}
            self.assertEqual(producer_manifest(namespace), expected)
            self.assertEqual(validator_manifest(namespace), expected)
            (namespace / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            for check in (producer_manifest, validator_manifest):
                with self.assertRaises(RuntimeError):
                    check(namespace)


if __name__ == "__main__":
    unittest.main()
