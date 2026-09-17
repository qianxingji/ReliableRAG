import importlib.util
from pathlib import Path
import unittest


def _module():
    path = Path(__file__).resolve().parents[1] / "scripts/census_c3_repair_arithmetic.py"
    spec = importlib.util.spec_from_file_location("c3_census", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class C3CensusHelpersTest(unittest.TestCase):
    def test_ulp_distance_and_canonical_json(self):
        module = _module()
        module.self_test()
        self.assertEqual(module.ulp_distance(-0.5, -0.5, 32), 0)
        self.assertEqual(module.canonical({"z": 1, "a": [2]}), b'{"a":[2],"z":1}')
