"""Process-isolated checks of the actual replay IO boundary and record adapter."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.audit_roa_upstream import records


class ReplayBoundaryTests(unittest.TestCase):
    def test_historical_nested_cache_copy_records(self):
        a = dict(path="cache/a", sha256="a" * 64, size_bytes=1)
        b = dict(path="source/a", sha256="a" * 64, size_bytes=1)
        self.assertEqual(list(records([{"copy": a, "original": b}])), [a, b])

    def test_output_allowed_source_write_and_network_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out = root / "new"
            out.mkdir()
            original = root / "original.txt"
            original.write_bytes(b"sealed")
            code = '''import pathlib,socket,sys
from scripts.replay_roa_original import install_boundary
out=pathlib.Path(sys.argv[1]); source=pathlib.Path(sys.argv[2])
access=install_boundary(out)
(out/'result.txt').write_text('result')
for operation in [lambda: source.write_text('changed'), lambda: source.unlink(), lambda: socket.create_connection(('127.0.0.1',1))]:
 try: operation()
 except RuntimeError: pass
 else: raise AssertionError('boundary allowed prohibited operation')
assert source.read_bytes()==b'sealed'
assert len(access['blocked'])==3
'''
            result = subprocess.run([sys.executable, "-B", "-c", code, str(out), str(original)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(original.read_bytes(), b"sealed")
            self.assertEqual((out / "result.txt").read_text(), "result")


if __name__ == "__main__": unittest.main()
