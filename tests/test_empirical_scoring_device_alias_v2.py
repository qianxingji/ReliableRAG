"""Fail-closed tests for the exact sealed-base CUDA alias correction."""
import copy
import hashlib
from pathlib import Path
import unittest

from scripts.empirical_scoring_device_alias_v2 import (
    BASE_MANIFEST_SHA256, BASE_RECEIPT_SHA256, BASE_SOURCE_COMMIT,
    exact_device_alias)
from scripts.run_roa_empirical_scoring_bound_v2 import STAGE_MODULES as V2_STAGES
from scripts.run_roa_empirical_scoring_bound_v3 import STAGE_MODULES as V3_STAGES


META = {"device": "cuda"}
ACTUAL = {
    "attempted_forward_calls": 4,
    "attempted_input_rows": 4,
    "attempted_input_tokens_including_padding": 20,
    "devices": ["cuda:0"],
}


class DeviceAliasV2Tests(unittest.TestCase):
    def test_exact_reviewed_alias_passes_without_mutation(self):
        metadata, actual = copy.deepcopy(META), copy.deepcopy(ACTUAL)
        exact_device_alias(metadata, actual, calls=4, rows=4, tokens=20)
        self.assertEqual(metadata, META)
        self.assertEqual(actual, ACTUAL)

    def test_metadata_variants_fail_closed(self):
        for device in ("cuda:0", "cuda:1", "cpu", "CUDA", "cuda ", None):
            with self.subTest(device=device), self.assertRaises(ValueError):
                exact_device_alias({"device": device}, ACTUAL, calls=4, rows=4, tokens=20)

    def test_observed_device_variants_fail_closed(self):
        for devices in ([], ["cuda"], ["cuda:1"], ["cuda:0", "cuda:1"], ["cpu"]):
            changed = {**ACTUAL, "devices": devices}
            with self.subTest(devices=devices), self.assertRaises(ValueError):
                exact_device_alias(META, changed, calls=4, rows=4, tokens=20)

    def test_counter_variants_fail_closed(self):
        for field in ("attempted_forward_calls", "attempted_input_rows",
                      "attempted_input_tokens_including_padding"):
            changed = {**ACTUAL, field: ACTUAL[field] - 1}
            with self.subTest(field=field), self.assertRaises(ValueError):
                exact_device_alias(META, changed, calls=4, rows=4, tokens=20)

    def test_schema_extensions_fail_closed(self):
        with self.assertRaises(ValueError):
            exact_device_alias(META, {**ACTUAL, "extra": True}, calls=4, rows=4, tokens=20)

    def test_validator_v2_diff_is_exactly_the_reviewed_correction(self):
        root = Path(__file__).resolve().parents[1]
        original = (root / "scripts/validate_roa_empirical_scoring.py").read_text(encoding="utf-8")
        amended = (root / "scripts/validate_roa_empirical_scoring_v2.py").read_text(encoding="utf-8")
        restored = amended.replace(
            '"""Complete independent prelabel acceptance with the frozen base alias correction."""',
            '"""Complete independent prelabel acceptance; tokenizers and saved CPU heads only."""')
        restored = restored.replace(
            "from scripts.empirical_scoring_device_alias_v2 import validate_frozen_base_device_alias\n", "")
        restored = restored.replace(
            '    device_alias = validate_frozen_base_device_alias(STAGES["base"], a)\n', "")
        restored = restored.replace(
            '        batch_size=1, max_length=8192, prompt_masking="answer_tokens_only").items():',
            '        device="cuda:0", batch_size=1, max_length=8192, prompt_masking="answer_tokens_only").items():')
        restored = restored.replace(
            '        pooling="cls", normalize=True, index_backend="numpy_exact").items():',
            '        device="cuda:0", pooling="cls", normalize=True, index_backend="numpy_exact").items():')
        restored = restored.replace(
            '        base_device_alias_corrigendum=device_alias,\n', "")
        self.assertEqual(restored, original)
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),
                         "0f040b1e3ef76484b1bea9edf3235009044bf13655ff5326748a765709bdc91d")

    def test_bound_v3_changes_only_future_independent_entry(self):
        self.assertEqual(V2_STAGES["independent"], "scripts.validate_roa_empirical_scoring")
        self.assertEqual(V3_STAGES["independent"], "scripts.validate_roa_empirical_scoring_v2")
        self.assertEqual({k: v for k, v in V3_STAGES.items() if k != "independent"},
                         {k: v for k, v in V2_STAGES.items() if k != "independent"})
        self.assertEqual(BASE_MANIFEST_SHA256,
                         "6cbc051be274617e26f548f4b51b5a6ec3cddeb5e1caf6761f00fa8301913cab")
        self.assertEqual(BASE_RECEIPT_SHA256,
                         "6a8fba007045a2eba50db74ca14e6bc216cc337681836240d4e9c9da58ba1989")
        self.assertEqual(BASE_SOURCE_COMMIT,
                         "842f2c2f20294a997bd7bcc73bae3cc5ae249be0")


if __name__ == "__main__":
    unittest.main()
