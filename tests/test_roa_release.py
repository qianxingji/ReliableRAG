"""Invented byte fixtures for release integrity, failure retention and fallback."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.replay_roa_relocated import FallbackGuard
from scripts.roa_release_io import (archive_check, canonical, extract_bytes, package_bytes,
                                   record, records_index)
from scripts.restore_roa_replay_release import restore


class ReleaseTests(unittest.TestCase):
    def test_binary_roundtrip_and_exclusive_destinations(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / "source"
            data.mkdir()
            (data / "opaque.bin").write_bytes(b'\x00\xff{"answer":"never decode"}\r\n')
            entries = [record(data, data / "opaque.bin")]
            archive = root / "data.zip"
            package_bytes(data, archive, entries)
            before = archive.read_bytes()
            with self.assertRaises(FileExistsError):
                package_bytes(data, archive, entries)
            self.assertEqual(archive.read_bytes(), before)
            extract_bytes(archive, root / "restored", entries)
            self.assertEqual((root / "restored/opaque.bin").read_bytes(), (data / "opaque.bin").read_bytes())
            with self.assertRaises(FileExistsError):
                extract_bytes(archive, root / "restored", entries)

    def test_paths_reject_windows_aliases_traversal_and_ads(self):
        for value in ("../x", "/x", "a//b", "a/./b", "a\\b", "C:/x", "a:b", "NUL.txt", "a. ", "a\x00b", "foo/COM1", "foo."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical(value)
        self.assertEqual(canonical(".venv/Lib/python.dll"), ".venv/Lib/python.dll")

    def test_record_conflicts_and_case_aliases(self):
        a = dict(path="one", size_bytes=0, sha256=hashlib.sha256(b"").hexdigest())
        self.assertEqual(len(records_index([a, dict(a)])), 1)
        for other in (dict(a, path="ONE"), dict(a, size_bytes=1), dict(a, sha256="0")):
            with self.assertRaises(ValueError):
                records_index([a, other])

    def test_changed_source_keeps_failed_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "x").write_bytes(b"before")
            entry = record(root, root / "x")
            (root / "x").write_bytes(b"after!")
            with self.assertRaisesRegex(ValueError, "CHANGED_DURING_COPY"):
                package_bytes(root, root / "partial.zip", [entry])
            self.assertTrue((root / "partial.zip").is_file())
            self.assertGreater((root / "partial.zip").stat().st_size, 0)
            self.assertEqual((root / "x").read_bytes(), b"after!")

    def test_missing_dependency_keeps_partial_and_does_not_fabricate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entry = dict(path="missing", size_bytes=1, sha256=hashlib.sha256(b"x").hexdigest())
            with self.assertRaisesRegex(ValueError, "MISSING_REGULAR_FILE"):
                package_bytes(root, root / "partial.zip", [entry])
            self.assertTrue((root / "partial.zip").exists())
            self.assertFalse((root / "missing").exists())

    def test_corrupt_and_extra_archive_members_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entry = dict(path="x", size_bytes=1, sha256=hashlib.sha256(b"x").hexdigest())
            for n, members in enumerate(([('x', b'y')], [('x', b'x'), ('../outside', b'x')], [('x', b'x'), ('extra', b'x')])):
                archive = root / f"{n}.zip"
                with zipfile.ZipFile(archive, "x") as z:
                    for name, value in members:
                        z.writestr(name, value)
                with self.assertRaises(ValueError):
                    extract_bytes(archive, root / f"dest{n}", [entry])
                self.assertFalse((root / f"dest{n}").exists())

    def test_fallback_guard_blocks_old_data_and_code_but_records_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old, engineering = root / "old", root / "engineering"
            guard = FallbackGuard([old, engineering], old / ".venv")
            for p in (old / "outputs/secret.jsonl", old / "docs/protocol.md", engineering / "scripts/code.py"):
                with self.assertRaisesRegex(RuntimeError, "FALLBACK_FORBIDDEN"):
                    guard.inspect(str(p))
            guard.inspect(old / ".venv/Lib/numpy.py")
            guard.inspect(root / "relocated/data.jsonl")
            guard.inspect(42)
            self.assertEqual(len(guard.blocked), 3)
            self.assertEqual(len(guard.runtime_reads), 1)
            with self.assertRaisesRegex(RuntimeError, "NETWORK_FORBIDDEN"):
                guard.audit("socket.connect", ())

    def test_restore_wrong_external_pin_creates_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "SHA256_MANIFEST.json").write_text('{}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "RELEASE_MANIFEST_PIN"):
                restore(root, "0" * 64, root.parent / (root.name + "-destination"))
            self.assertFalse((root.parent / (root.name + "-destination")).exists())


if __name__ == "__main__":
    unittest.main()
