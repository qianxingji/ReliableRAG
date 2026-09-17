"""Isolated-mode bootstrap for the unchanged C3 V3.1 validation entry."""
import runpy
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
assert repo == Path("E:/paper/ReliableRAG-cas-q2-p0-1").resolve()
assert sys.flags.isolated and sys.dont_write_bytecode
assert str(repo) not in sys.path
sys.path.insert(0, str(repo))
runpy.run_path(str(repo / "scripts/validate_roa_empirical_runtime_bound_v3_1.py"), run_name="__main__")
