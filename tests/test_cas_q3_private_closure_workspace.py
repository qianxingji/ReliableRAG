"""Tests for idempotent preparation of the ignored external-closure workspace."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_cas_q3_private_closure_workspace import prepare


class PrivateClosureWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.specs = (
            (Path("templates/owner.json"), Path("private/owner.local.json")),
            (Path("templates/cas.json"), Path("private/cas.local.json")),
            (Path("templates/release.json"), Path("private/release.local.json")),
        )
        for index, (template, _) in enumerate(self.specs):
            path = self.root / template
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"schema_version": 1, "slot": index}) + "\n", encoding="utf-8")
        self.evidence = (Path("evidence/cas"), Path("evidence/release"))

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_creates_exact_template_copies_and_empty_directories(self):
        result = prepare(self.root, input_specs=self.specs, evidence_directories=self.evidence)
        self.assertEqual(result["decision"], "PASS_PRIVATE_CLOSURE_WORKSPACE_PREPARED_WITHOUT_OVERWRITE")
        self.assertTrue(all(item["status"] == "CREATED_FROM_TEMPLATE" for item in result["inputs"]))
        self.assertTrue(all(item["matches_empty_template"] for item in result["inputs"]))
        for template, local in self.specs:
            self.assertEqual((self.root / template).read_bytes(), (self.root / local).read_bytes())
        for directory in self.evidence:
            self.assertTrue((self.root / directory).is_dir())
        self.assertFalse(result["existing_private_bytes_overwritten"])
        self.assertFalse(result["submission_authorized"])

    def test_second_run_is_idempotent(self):
        prepare(self.root, input_specs=self.specs, evidence_directories=self.evidence)
        result = prepare(self.root, input_specs=self.specs, evidence_directories=self.evidence)
        self.assertTrue(all(item["status"] == "PRESERVED_EXISTING" for item in result["inputs"]))
        self.assertTrue(all(item["status"] == "PRESERVED_EXISTING" for item in result["evidence_directories"]))

    def test_existing_private_input_is_preserved_byte_for_byte(self):
        local = self.root / self.specs[0][1]
        local.parent.mkdir(parents=True, exist_ok=True)
        private_bytes = b'{"private":"DO_NOT_OVERWRITE_7QX"}\n'
        local.write_bytes(private_bytes)
        result = prepare(self.root, input_specs=self.specs, evidence_directories=self.evidence)
        self.assertEqual(local.read_bytes(), private_bytes)
        self.assertEqual(result["inputs"][0]["status"], "PRESERVED_EXISTING")
        self.assertFalse(result["inputs"][0]["matches_empty_template"])
        self.assertNotIn("DO_NOT_OVERWRITE_7QX", json.dumps(result))

    def test_file_collision_at_evidence_directory_is_rejected(self):
        collision = self.root / self.evidence[0]
        collision.parent.mkdir(parents=True, exist_ok=True)
        collision.write_text("collision", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "directory is unsafe"):
            prepare(self.root, input_specs=self.specs, evidence_directories=self.evidence)
        self.assertFalse((self.root / self.specs[0][1]).exists())

    def test_missing_template_is_rejected_before_any_workspace_mutation(self):
        (self.root / self.specs[-1][0]).unlink()
        with self.assertRaisesRegex(ValueError, "canonical template is missing"):
            prepare(self.root, input_specs=self.specs, evidence_directories=self.evidence)
        self.assertTrue(all(not (self.root / local).exists() for _, local in self.specs))
        self.assertTrue(all(not (self.root / directory).exists() for directory in self.evidence))


if __name__ == "__main__":
    unittest.main()
