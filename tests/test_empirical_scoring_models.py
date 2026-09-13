"""CPU-only config and exclusive snapshot IO tests; no neural constructors called."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.empirical_scoring_models import fixed_configs, nli_copy_plan, stage_nli_cache, NLI_FILES, NLI_REV
from scripts.empirical_scoring_io import record


class ScoringModelIOTests(unittest.TestCase):
    def test_scientific_configs_exact_and_only_paths_are_adapted(self):
        root = Path("E:/paper/ReliableRAG")
        pre = json.loads((root / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/PREFLIGHT_INPUT_VERIFICATION.json").read_text(encoding="utf-8"))
        before = copy.deepcopy(pre)
        out = Path("E:/paper/ReliableRAG-cas-q2-p0-1/outputs/cas_q2/invented-never-created")
        cfg = fixed_configs(root, out, pre)
        self.assertEqual(pre, before)
        self.assertEqual(cfg["reader"]["max_length"], 8192)
        self.assertEqual(cfg["reader"]["model_cache_dir"], str(root / "data/models/huggingface"))
        self.assertEqual(cfg["dense"]["batch_size"], 16)
        for section, field, value in (("dense", "batch_size", 8), ("reader_scorer", "revision", "main")):
            altered = copy.deepcopy(pre)
            target = altered["phase3_config"] if section == "dense" else altered["historical_config"]
            target[section][field] = value
            with self.assertRaises(RuntimeError): fixed_configs(root, out, altered)
        with self.assertRaises(RuntimeError): fixed_configs(root, root / "outputs/new", pre)
        self.assertFalse(out.exists())

    def fixture(self, directory):
        root = Path(directory) / "original"
        out = Path(directory) / "new"
        source = root / "outputs/published_baseline_gbv_nli_v1/infrastructure/model_snapshot"
        source.mkdir(parents=True)
        entries = []
        for name in sorted(NLI_FILES):
            path = source / name
            path.write_bytes(("invented bytes, never a real model: " + name).encode())
            entries.append(dict(record(path), path=path.relative_to(root).as_posix()))
        return root, out, dict(gbv=dict(files=entries))

    def test_new_cache_byte_copies_preserve_originals_and_refuse_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root, out, pre = self.fixture(directory)
            plan = nli_copy_plan(root, out, pre)
            self.assertFalse(out.exists())
            copied = stage_nli_cache(root, out, pre)
            self.assertEqual(len(copied), 7)
            for item in copied:
                self.assertEqual(record(Path(item["source"]["path"])), item["source"])
                self.assertEqual(item["source"]["sha256"], item["copied"]["sha256"])
                self.assertEqual(Path(item["target"]).parent.name, NLI_REV)
            with self.assertRaises(RuntimeError): stage_nli_cache(root, out, pre)

    def test_missing_changed_or_foreign_snapshot_rejected_before_copy(self):
        for mode in ("missing", "hash", "foreign", "duplicate"):
            with tempfile.TemporaryDirectory() as directory:
                root, out, pre = self.fixture(directory)
                if mode == "missing": pre["gbv"]["files"].pop()
                elif mode == "hash": pre["gbv"]["files"][0]["sha256"] = "0" * 64
                elif mode == "foreign": pre["gbv"]["files"][0]["path"] = "outside/config.json"
                else: pre["gbv"]["files"].append(pre["gbv"]["files"][0])
                with self.assertRaises(RuntimeError, msg=mode): stage_nli_cache(root, out, pre)
                self.assertFalse(out.exists(), "Rejected metadata must not create partial cache")


if __name__ == "__main__":
    unittest.main()
