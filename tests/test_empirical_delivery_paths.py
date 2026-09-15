"""Boundary tests for the separate delivery adapter, with no scientific inputs."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

from scripts.empirical_delivery_paths import BoundFiles, RootBinding, SourceLoader, bind_support, ORIGINAL_ROOT, SUPPORT_PATHS, relative_identity, windows_identity


class DeliveryPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="delivery_paths_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.physical = self.root / "transport"
        self.physical.mkdir()
        self.file = self.physical / "source.py"
        self.file.write_text("answer = 42\n", encoding="utf-8")
        self.roots = {"original": RootBinding(ORIGINAL_ROOT, self.physical)}
        self.entry = dict(root="original", relative_path="source.py", logical_path=ORIGINAL_ROOT + "/source.py",
                          sha256=hashlib.sha256(self.file.read_bytes()).hexdigest(), size_bytes=self.file.stat().st_size)

    def test_declared_identity_resolves_without_metadata_rewrite(self):
        files = BoundFiles(self.roots, [self.entry])
        self.assertEqual(files.checked(self.entry["logical_path"]), self.file)
        files.verify_exact_fileset()
        self.assertEqual(self.entry["logical_path"], ORIGINAL_ROOT + "/source.py")

    def test_prefix_confusion_and_unknown_physical_file_are_rejected(self):
        files = BoundFiles(self.roots, [self.entry])
        with self.assertRaises(ValueError): files.checked(ORIGINAL_ROOT + "-other/source.py")
        with self.assertRaises(ValueError): files.checked_physical(self.root / "source.py")

    def test_relative_traversal_aliases_and_reserved_names(self):
        for name in ("../escape.py", "x/../escape.py", "./source.py", "source.py ", "x//source.py", "source.py:stream", "NUL", "C:/source.py"):
            with self.subTest(name=name), self.assertRaises(ValueError): relative_identity(name)

    def test_duplicate_case_alias_is_rejected(self):
        alias = dict(self.entry, logical_path=self.entry["logical_path"].upper(), relative_path="SOURCE.PY")
        with self.assertRaises(ValueError): BoundFiles(self.roots, [self.entry, alias])

    def test_absolute_identity_alias_and_relative_root_rejected(self):
        for value in (ORIGINAL_ROOT + "//source.py", ORIGINAL_ROOT + "/NUL/child", ORIGINAL_ROOT + "/./source.py"):
            with self.subTest(value=value), self.assertRaises(ValueError): windows_identity(value)
        with self.assertRaises(ValueError): BoundFiles({"original": RootBinding(ORIGINAL_ROOT, Path("relative"))}, [])

    def test_original_support_pin_checked_before_exec_even_with_matching_transport_hash(self):
        relative = next(iter(SUPPORT_PATHS))
        source = self.physical / relative
        source.parent.mkdir(parents=True)
        sentinel = self.root / "executed.txt"
        source.write_text("from pathlib import Path\nPath(" + repr(str(sentinel)) + ").write_text('bad')\n", encoding="utf-8")
        entry = dict(self.entry, relative_path=relative, logical_path=ORIGINAL_ROOT + "/" + relative,
                     sha256=hashlib.sha256(source.read_bytes()).hexdigest(), size_bytes=source.stat().st_size)
        loader = SourceLoader(BoundFiles(self.roots, [entry]))
        with self.assertRaises(ValueError): loader.load("delivery_forbidden_support", source)
        self.assertFalse(sentinel.exists())
        self.assertNotIn("delivery_forbidden_support", sys.modules)

    def test_overlapping_root_bindings_are_rejected(self):
        with self.assertRaises(ValueError):
            BoundFiles(dict(self.roots, nested=RootBinding(ORIGINAL_ROOT + "/child", self.root / "other")), [])
        with self.assertRaises(ValueError):
            BoundFiles(dict(self.roots, nested=RootBinding("F:/other", self.physical / "child")), [])

    def test_changed_hash_rejected_before_module_side_effect(self):
        sentinel = self.root / "executed.txt"
        self.file.write_text("from pathlib import Path\nPath(" + repr(str(sentinel)) + ").write_text('bad')\n", encoding="utf-8")
        loader = SourceLoader(BoundFiles(self.roots, [self.entry]))
        with self.assertRaises(ValueError): loader.load("delivery_forbidden_side_effect", self.file)
        self.assertFalse(sentinel.exists())

    def test_hardlink_alias_is_rejected(self):
        os.link(self.file, self.physical / "linked.py")
        with self.assertRaises(ValueError): BoundFiles(self.roots, [self.entry]).checked(self.entry["logical_path"])

    def test_unknown_file_breaks_exact_file_set(self):
        (self.physical / "extra.txt").write_text("extra", encoding="utf-8")
        with self.assertRaises(ValueError): BoundFiles(self.roots, [self.entry]).verify_exact_fileset()

    def test_only_explicit_path_and_import_bindings_change(self):
        module = types.ModuleType("invented_support")
        module.ROOT = Path(ORIGINAL_ROOT); module.OUT = Path(ORIGINAL_ROOT) / "out"
        module.import_file = lambda *args: None
        module.science = lambda x: x + 1; module.seed = 17
        science = module.science
        receipt = bind_support(module, self.physical, dict(ROOT="", OUT="out"), lambda *args: None)
        self.assertEqual(module.ROOT, self.physical); self.assertEqual(module.OUT, self.physical / "out")
        self.assertIs(module.science, science); self.assertEqual(module.science(2), 3); self.assertEqual(module.seed, 17)
        self.assertTrue(receipt["unchanged_scientific_function_objects"])

    def test_unexpected_path_or_unowned_module_is_rejected(self):
        module = types.ModuleType("bad_support"); module.ROOT = Path(ORIGINAL_ROOT); module.EXTRA = Path(ORIGINAL_ROOT) / "extra"
        module.import_file = lambda *args: None
        with self.assertRaises(ValueError): bind_support(module, self.physical, dict(ROOT=""), lambda *args: None)
        self.assertEqual(module.ROOT, Path(ORIGINAL_ROOT))
        with self.assertRaises(ValueError): SourceLoader(BoundFiles(self.roots, [self.entry])).load("sys", self.file)


if __name__ == "__main__":
    unittest.main()
