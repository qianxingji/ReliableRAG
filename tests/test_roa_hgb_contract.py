"""Supplementary design boundaries; no model fitting."""
import ast
from pathlib import Path
import unittest
from scripts.inventory_roa_confirmation_ids import inventory,DATASETS
from scripts.run_roa_hgb_only import attribution


class HGBContractTests(unittest.TestCase):
    def test_hgb_fitter_only_changes_declared_control_width(self):
        root=Path(__file__).resolve().parents[1]
        a=ast.parse((root/"src/arbitration/recovery_controls.py").read_text())
        b=ast.parse((root/"src/arbitration/recovery_hgb_control.py").read_text())
        a.body[0]=b.body[0]
        fa=next(x for x in a.body if isinstance(x,ast.FunctionDef) and x.name=="fit_control")
        fb=next(x for x in b.body if isinstance(x,ast.FunctionDef) and x.name=="fit_control")
        for i,x in enumerate(fa.body):
            if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="width" for t in x.targets):fa.body[i]=fb.body[i]
        self.assertEqual(ast.dump(a),ast.dump(b))

    def test_inventory_retains_zero_availability_and_requires_three_sources(self):
        sources={d:{(d,"x")} for d in DATASETS}
        result=inventory(sources,{("hotpotqa","x")})
        self.assertEqual(result["hotpotqa"]["available"],0)
        self.assertEqual(result["musique"]["available"],1)
        with self.assertRaises(ValueError):inventory({"hotpotqa":set()},set())

    def test_fusion_needs_both_single_signal_controls(self):
        reps=[dict(pooled=dict(methods={"HGB_GBV_R":dict(net=5,damage=1),"HGB_ONLY_R":dict(net=5,damage=1),"GBV_ONLY_R":dict(net=3,damage=2)},
                                comparisons={"HGB_GBV_R":{m:dict(delta_em_pp=.1) for m in ("HGB_ONLY_R","GBV_ONLY_R")}})) for _ in range(5)]
        lodo=[dict(heldout=d,summary=dict(comparisons={"HGB_GBV_R":{m:dict(delta_em_pp=.1) for m in ("HGB_ONLY_R","GBV_ONLY_R")}})) for d in DATASETS]
        self.assertEqual(attribution(reps,lodo)["decision"],"TWO_SIGNAL_INCREMENT_NOT_ESTABLISHED")
        self.assertEqual(attribution(reps,lodo)["successes"]["HGB_ONLY_R"],0)


if __name__=="__main__":unittest.main()
