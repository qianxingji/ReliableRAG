from pathlib import Path
import ast
import copy
import hashlib
import json
import tempfile
import unittest

from scripts.run_mistral_test_prelabel_freeze import (
    EXPECTED_TRACES, METHOD_FEATURES, merge_prelabel_row,
)
from scripts.validate_mistral_test_prelabel_freeze import (
    current_manifest_member_paths, reconstruct_prelabel_row,
)


def source_rows():
    identity = {
        "dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s",
        "position": 0, "role": "test",
    }
    hgb = {
        **identity, "eligible": True, "forced_keep_reason": None,
        "bindings": {}, "feature_row_sha256": "a" * 64, "hgb_score": 0.7,
    }
    gbv = {
        **identity, "pair_eligible": True, "eligible": True,
        "forced_keep_reason": None, "F0": 0.2, "F1": 0.8,
        "gbv_margin": 0.6000000000000001,
        "e0_premise_count": 5, "e1_premise_count": 5,
        "e0_chunk_count": 5, "e1_chunk_count": 6,
        "branch_receipt_sha256": {"a0_e0": "b" * 64, "a1_e1": "c" * 64},
        "model_id": "m", "model_revision": "r",
    }
    return hgb, gbv


class MistralTestPrelabelFreezeContractTests(unittest.TestCase):
    def test_exact_scope_and_feature_order(self):
        self.assertEqual(EXPECTED_TRACES, 18_000)
        self.assertEqual(METHOD_FEATURES, {
            "HGB_GBV_R": ("hgb_score", "gbv_margin"),
            "HGB_ONLY_R": ("hgb_score",),
            "GBV_ONLY_R": ("gbv_margin",),
        })

    def test_producer_and_independent_merge_agree(self):
        hgb, gbv = source_rows()
        produced = merge_prelabel_row(hgb, gbv)
        independent = reconstruct_prelabel_row(hgb, gbv)
        self.assertEqual(produced, independent)
        self.assertTrue(produced["eligible"])
        self.assertEqual(produced["feature_vectors"]["HGB_GBV_R"],
                         [0.7, 0.6000000000000001])

    def test_nli_failure_forces_common_keep_and_retains_completed_f0(self):
        hgb, gbv = source_rows(); gbv = copy.deepcopy(gbv)
        gbv.update(eligible=False,
                   forced_keep_reason="nli_unscorable:hypothesis does not fit the NLI context window",
                   F1=None, gbv_margin=None, e1_chunk_count=0)
        produced = merge_prelabel_row(hgb, gbv)
        self.assertFalse(produced["eligible"])
        self.assertEqual(produced["hgb_score"], 0.7)
        self.assertEqual(produced["gbv_F0"], 0.2)
        self.assertIsNone(produced["gbv_margin"])
        self.assertEqual(produced["feature_vectors"]["HGB_ONLY_R"], [0.7])

    def test_first_branch_nli_failure_retains_no_partial_score(self):
        hgb, gbv = source_rows(); gbv = copy.deepcopy(gbv)
        gbv.update(eligible=False,
                   forced_keep_reason="nli_unscorable:hypothesis does not fit the NLI context window",
                   F0=None, F1=None, gbv_margin=None,
                   e0_chunk_count=0, e1_chunk_count=0,
                   branch_receipt_sha256={"a0_e0": "b" * 64})
        produced = merge_prelabel_row(hgb, gbv)
        self.assertFalse(produced["eligible"])
        self.assertIsNone(produced["gbv_F0"])

    def test_native_ineligible_pair_makes_no_gbv_feature(self):
        hgb, gbv = source_rows()
        hgb.update(eligible=False, forced_keep_reason="normalized_answers_equal",
                   feature_row_sha256=None, hgb_score=None)
        gbv.update(pair_eligible=False, eligible=False,
                   forced_keep_reason="normalized_answers_equal",
                   F0=None, F1=None, gbv_margin=None,
                   e0_chunk_count=0, e1_chunk_count=0,
                   branch_receipt_sha256={})
        produced = merge_prelabel_row(hgb, gbv)
        self.assertFalse(produced["pair_eligible"])
        self.assertFalse(produced["eligible"])
        self.assertEqual(produced["feature_vectors"], {
            "HGB_GBV_R": [None, None],
            "HGB_ONLY_R": [None],
            "GBV_ONLY_R": [None],
        })

    def test_native_mask_or_reason_mismatch_fails_closed(self):
        hgb, gbv = source_rows(); gbv["pair_eligible"] = False
        with self.assertRaisesRegex(RuntimeError, "PRELABEL_NATIVE_ELIGIBILITY"):
            merge_prelabel_row(hgb, gbv)
        hgb, gbv = source_rows()
        hgb.update(eligible=False, forced_keep_reason="a0_empty", hgb_score=None,
                   feature_row_sha256=None)
        gbv.update(pair_eligible=False, eligible=False,
                   forced_keep_reason="a1_empty", F0=None, F1=None,
                   gbv_margin=None, e0_chunk_count=0, e1_chunk_count=0,
                   branch_receipt_sha256={})
        with self.assertRaisesRegex(RuntimeError, "PRELABEL_NATIVE_FORCED_KEEP"):
            merge_prelabel_row(hgb, gbv)

    def test_validator_does_not_import_producer_or_model_runtime(self):
        path = (Path(__file__).resolve().parents[1]
                / "scripts/validate_mistral_test_prelabel_freeze.py")
        source = path.read_text(encoding="utf-8"); tree = ast.parse(source)
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)}
        direct_imports = {alias.name for node in ast.walk(tree)
                          if isinstance(node, ast.Import) for alias in node.names}
        self.assertNotIn("scripts.run_mistral_test_prelabel_freeze", imported)
        self.assertTrue({"torch", "transformers", "sklearn"}.isdisjoint(
            imported | direct_imports
        ))
        self.assertIn("PASS_INDEPENDENT_MISTRAL_TEST_PRELABEL_FREEZE", source)

    def test_freeze_requires_exact_direct_input_graph(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_test_prelabel_freeze.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_test_prelabel_freeze.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("MISTRAL_TEST_PRELABEL_INPUT_GRAPH_AMENDMENT", producer)
        self.assertIn("current_manifest_member_paths", validator)
        self.assertIn("NONEXACT_FROZEN_INPUT_GRAPH", validator)

    def test_current_manifest_coverage_rejects_extra_file(self):
        with tempfile.TemporaryDirectory() as folder:
            namespace = Path(folder)
            payload_path = namespace / "payload.bin"
            payload_path.write_bytes(b"payload")
            manifest = namespace / "SHA256_MANIFEST.json"
            value = {"files": [{
                "path": "payload.bin", "size_bytes": payload_path.stat().st_size,
                "sha256": hashlib.sha256(payload_path.read_bytes()).hexdigest(),
            }]}
            manifest.write_text(json.dumps(value), encoding="utf-8")
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            self.assertEqual(
                current_manifest_member_paths(namespace, manifest_sha),
                {manifest.resolve(), payload_path.resolve()},
            )
            (namespace / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "CURRENT_MANIFEST_COVERAGE"):
                current_manifest_member_paths(namespace, manifest_sha)


if __name__ == "__main__":
    unittest.main()
