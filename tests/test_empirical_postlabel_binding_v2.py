import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_roa_empirical_postlabel_bound_v2 as binding


class PostlabelBindingV2Tests(unittest.TestCase):
    def test_fixed_map_changes_only_gpu_preflight(self):
        before, after = binding.fixed_stage_maps()
        self.assertEqual(set(before), {"gpu_preflight", "base", "gbv",
                                      "policies", "independent"})
        self.assertEqual(set(before), set(after))
        self.assertTrue(before["gpu_preflight"].endswith(
            "empirical_scoring_gpu_preflight_v1"))
        self.assertTrue(after["gpu_preflight"].endswith(
            "empirical_scoring_gpu_preflight_v2"))
        self.assertEqual({k: v for k, v in before.items()
                          if k != "gpu_preflight"},
                         {k: v for k, v in after.items()
                          if k != "gpu_preflight"})

    def test_entries_are_exact_frozen_processes(self):
        self.assertEqual(binding.ENTRIES, {
            "cost": "scripts.audit_roa_empirical_cost",
            "mapping": "scripts.map_roa_empirical_outcomes",
            "outcome_validation": "scripts.validate_roa_empirical_outcomes",
            "analysis": "scripts.analyze_roa_empirical_results",
            "analysis_validation": "scripts.validate_roa_empirical_analysis",
        })

    def test_record_detects_changed_control(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "control.txt"
            path.write_text("accepted", encoding="utf-8")
            record = binding.record(path)
            self.assertEqual(binding.verify_record(record), path.resolve())
            path.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,
                                        "POSTLABEL_V2_CONTROL_CHANGED"):
                binding.verify_record(record)

    def make_config(self, path, *, entry=None, original_arguments=None):
        before, after = binding.fixed_stage_maps()
        config = {
            "version": 2, "stage": "cost",
            "project_root": str(binding.PROJECT),
            "engineering_root": str(binding.REPO),
            "source_commit": "commit",
            "entry_module": entry or binding.ENTRIES["cost"],
            "original_arguments": original_arguments or [],
            "stage_paths_before": before, "stage_paths_after": after,
            "prelabel_manifest_sha256": binding.PRELABEL_SHA256,
            "v1_manifest_sha256": binding.V1_SHA256,
            "v2_manifest_sha256": binding.V2_SHA256, "controls": []}
        path.write_text(json.dumps(config), encoding="utf-8")
        return config, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_config_hash_is_byte_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            original = ["--project-root", str(binding.PROJECT),
                        "--prelabel-manifest-sha256",
                        binding.PRELABEL_SHA256]
            config, digest = self.make_config(
                path, original_arguments=original)
            with patch.object(binding.subprocess, "check_output",
                              side_effect=["commit\n", ""]):
                _, loaded, controls = binding.parse_binding(
                    ["--config", str(path), "--config-sha256", digest,
                     "--", *original])
            self.assertEqual(loaded, config)
            self.assertEqual(controls, [])
            with self.assertRaisesRegex(RuntimeError,
                                        "POSTLABEL_V2_CONFIG_PIN"):
                binding.parse_binding(
                    ["--config", str(path), "--config-sha256", "0" * 64,
                     "--", *original])

    def test_config_rejects_cross_stage_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            _, digest = self.make_config(
                path, entry="scripts.map_roa_empirical_outcomes")
            with self.assertRaisesRegex(RuntimeError,
                                        "POSTLABEL_V2_FIXED_ENTRY"):
                binding.parse_binding(
                    ["--config", str(path), "--config-sha256", digest, "--"])


if __name__ == "__main__":
    unittest.main()
