"""Frozen control recipe and decision boundary checks; zero fitting calls."""
import ast
import copy
import importlib
from pathlib import Path
import unittest

from scripts.replay_roa_original import load_original
from scripts.run_roa_controls import attribution


class ControlContractTests(unittest.TestCase):
    def test_fitter_changes_only_name_width_and_width_guard(self):
        root=Path(__file__).resolve().parents[1]
        a=ast.parse((root/"src/arbitration/roa_original/learning.py").read_text())
        b=ast.parse((root/"src/arbitration/recovery_controls.py").read_text())
        a.body[0]=b.body[0]
        original=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=="fit_bundle")
        adapted=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=="fit_control")
        original.name="fit_control"
        oi=next(i for i,n in enumerate(original.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="width" for t in n.targets))
        bi=next(i for i,n in enumerate(adapted.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="width" for t in n.targets))
        self.assertEqual(oi,bi)
        original.body[oi:oi+1]=copy.deepcopy(adapted.body[bi:bi+2])
        self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))

    def test_all_missing_and_test_label_scope_fail_before_fit(self):
        load_original("controls");load_original("design")
        fit=importlib.import_module("src.arbitration.recovery_controls").fit_control
        keys=[("hotpotqa","bm25",str(i)) for i in range(6)]
        rows={k:dict(eligible=True,numeric=[None]) for k in keys}
        parts={"fit":set(keys[:2]),"cal":set(keys[2:4]),"test":set(keys[4:])}
        ys={k:dict(a0_em=0,a1_em=i%2) for i,k in enumerate(keys)}
        events=[]
        with self.assertRaisesRegex(RuntimeError,"TRAINING_LABEL_SCOPE"):
            fit(rows,ys,parts,"GBV_ONLY_R","toy",events.append)
        with self.assertRaisesRegex(RuntimeError,"ALL_MISSING_FIT_COLUMN"):
            fit(rows,{k:ys[k] for k in keys[:4]},parts,"GBV_ONLY_R","toy",events.append)
        self.assertEqual(events,[])

    def test_attribution_requires_every_comparator_and_lodo_boundary(self):
        repetitions=[]
        for i in range(5):
            repetitions.append(dict(pooled=dict(methods={"ROA-FULL":dict(net=11,damage=2),"GBV_ONLY_R":dict(net=10 if i<4 else 11,damage=2),"HGB_GBV_R":dict(net=10,damage=2)},
                                                 comparisons={"ROA-FULL":{m:dict(delta_em_pp=.1) for m in ("GBV_ONLY_R","HGB_GBV_R")}})))
        lodo=[dict(heldout=d,summary=dict(comparisons={"ROA-FULL":{m:dict(delta_em_pp=-.1) for m in ("GBV_ONLY_R","HGB_GBV_R")}})) for d in ("hotpotqa","2wikimultihopqa","musique")]
        self.assertEqual(attribution(repetitions,lodo)["decision"],"COMPLEXITY_SUPPORTED_FOR_CONFIRMATION")
        lodo[0]["summary"]["comparisons"]["ROA-FULL"]["HGB_GBV_R"]["delta_em_pp"]=-.10001
        self.assertEqual(attribution(repetitions,lodo)["decision"],"SIMPLER_CONTROL_COMPETITIVE_REVIEW_CONTRIBUTION")


if __name__=="__main__":unittest.main()
