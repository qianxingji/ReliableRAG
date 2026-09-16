from pathlib import Path
import ast
import hashlib
import json
import tempfile
import unittest

from scripts.empirical_outcome_independent import metrics
from scripts.run_mistral_development_outcomes import (
    EXPECTED_DATASET_QUESTIONS,
    EXPECTED_QUESTIONS,
    EXPECTED_TRACES,
    development_group_roles,
    metric_values,
)
from scripts.validate_mistral_development_outcomes import (
    current_manifest_member_paths,
    development_groups,
)


class NativeMetric:
    @staticmethod
    def exact_match(answer, references):
        return metrics(answer, references)[0]

    @staticmethod
    def token_f1(answer, references):
        return metrics(answer, references)[1]


def prelabel_rows():
    rows = []
    position = 0
    for dataset in ("hotpotqa", "2wikimultihopqa", "musique"):
        for question in range(EXPECTED_DATASET_QUESTIONS):
            role = "fit" if question < 1_200 else "cal"
            for retriever in ("bm25", "dense", "hybrid"):
                rows.append({
                    "dataset": dataset,
                    "retriever": retriever,
                    "sample_id": f"{dataset}-{question}",
                    "position": position,
                    "role": role,
                })
                position += 1
    return rows


class MistralDevelopmentOutcomesContractTests(unittest.TestCase):
    def test_exact_development_scope(self):
        self.assertEqual((EXPECTED_TRACES, EXPECTED_QUESTIONS,
                          EXPECTED_DATASET_QUESTIONS), (13_500, 4_500, 1_500))
        rows = prelabel_rows()
        produced, produced_counts = development_group_roles(rows)
        independent, independent_counts = development_groups(rows)
        self.assertEqual(produced, independent)
        self.assertEqual(produced_counts, independent_counts)
        self.assertEqual(produced_counts, {"fit": 3_600, "cal": 900})

    def test_mixed_sibling_roles_fail_closed(self):
        rows = prelabel_rows()
        rows[1]["role"] = "cal"
        with self.assertRaisesRegex(RuntimeError, "DEVELOPMENT_SIBLING_ROLE"):
            development_group_roles(rows)
        with self.assertRaisesRegex(RuntimeError, "SIBLING_ROLE"):
            development_groups(rows)

    def test_missing_sibling_fails_closed(self):
        rows = prelabel_rows()[:-1]
        with self.assertRaisesRegex(RuntimeError, "DEVELOPMENT_GROUP_SCOPE"):
            development_group_roles(rows)
        with self.assertRaisesRegex(RuntimeError, "DEVELOPMENT_GROUP_SCOPE"):
            development_groups(rows)

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

    def test_invalid_metric_inputs_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError, "OUTCOME_METRIC_INPUT"):
            metric_values(NativeMetric, "answer", "answer", [])
        with self.assertRaisesRegex(RuntimeError, "OUTCOME_METRIC_INPUT"):
            metric_values(NativeMetric, "answer", "answer", [1])

    def test_validator_is_independent_and_model_free(self):
        path = (Path(__file__).resolve().parents[1]
                / "scripts/validate_mistral_development_outcomes.py")
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)}
        direct_imports = {alias.name for node in ast.walk(tree)
                          if isinstance(node, ast.Import) for alias in node.names}
        self.assertNotIn("scripts.run_mistral_development_outcomes", imported)
        self.assertIn("scripts.empirical_outcome_independent", imported)
        self.assertTrue({"torch", "transformers", "sklearn"}.isdisjoint(
            imported | direct_imports
        ))
        self.assertIn("PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_OUTCOMES", source)

    def test_gold_and_test_access_contracts_are_explicit(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_development_outcomes.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_development_outcomes.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("DETAILS_WITHHELD_TO_PREVENT_REFERENCE_TEXT_LOGGING", producer)
        self.assertIn('"raw_reference_strings_written": 0', producer)
        self.assertIn('"test_rows_read": 0', producer)
        self.assertIn('"test_rows_read": 0', validator)
        self.assertNotIn('"references": references', producer)

    def test_outcome_freeze_requires_exact_gold_and_predecessor_graph(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_development_outcomes.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_development_outcomes.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("validate_mistral_development_outcomes.py", producer)
        self.assertIn("verify_manifest(\n                prelabel", producer)
        self.assertIn("NONEXACT_FROZEN_INPUT_GRAPH", validator)
        self.assertIn("authenticated_paths", validator)

    def test_independent_current_manifest_coverage_rejects_extra_file(self):
        with tempfile.TemporaryDirectory() as folder:
            namespace = Path(folder)
            payload = namespace / "payload.bin"; payload.write_bytes(b"payload")
            manifest = namespace / "SHA256_MANIFEST.json"
            value = {"files": [{
                "path": "payload.bin", "size_bytes": payload.stat().st_size,
                "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
            }]}
            manifest.write_text(json.dumps(value), encoding="utf-8")
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            self.assertEqual(
                current_manifest_member_paths(namespace, manifest_sha),
                {manifest.resolve(), payload.resolve()},
            )
            (namespace / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "CURRENT_MANIFEST_COVERAGE"):
                current_manifest_member_paths(namespace, manifest_sha)


if __name__ == "__main__":
    unittest.main()
