"""Contract tests only: no scientific or synthetic estimator fit calls."""
import ast
from pathlib import Path
import unittest
from src.arbitration.empirical_contract import DATASETS, RETRIEVERS, split_development, select_fresh_ids

ROOT=Path(__file__).resolve().parents[1]


class EmpiricalContractTests(unittest.TestCase):
    def keys(self):return [(d,r,str(i)) for d in DATASETS for i in range(1500) for r in RETRIEVERS]

    def test_probe_overlap_is_explicit_and_fit_cal_siblings_are_disjoint(self):
        parts=split_development(self.keys())
        self.assertEqual(parts,split_development(reversed(self.keys())))
        self.assertEqual(parts["fit"]&parts["cal"],set())
        self.assertEqual(parts["probe"],parts["fit"]|parts["cal"])
        for d in DATASETS:
            self.assertEqual(sum(k[0]==d for k in parts["cal"]),900)
            self.assertEqual(sum(k[0]==d for k in parts["fit"]),3600)
        for d,i in {(k[0],k[2]) for k in parts["cal"]}:
            self.assertTrue({(d,r,i) for r in RETRIEVERS}<=parts["cal"])

    def test_incomplete_or_foreign_sibling_fails_without_redraw(self):
        keys=self.keys()
        with self.assertRaises(ValueError):split_development(keys[:-1])
        keys[-1]=(keys[-1][0],"foreign",keys[-1][2])
        with self.assertRaises(ValueError):split_development(keys)

    def test_exact_fitter_body_except_declared_width_and_probe_role(self):
        def body(path,name):
            node=next(n for n in ast.parse(path.read_text(encoding="utf-8")).body if isinstance(n,ast.FunctionDef) and n.name==name)
            node.name="fit"
            if isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant):node.body.pop(0)
            class Normalize(ast.NodeTransformer):
                def visit_Constant(self,n):
                    if n.value=="probe":n.value="test"
                    return n
                def visit_Assign(self,n):
                    if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="width":n.value=ast.Constant(0)
                    return self.generic_visit(n)
            return ast.dump(Normalize().visit(node),include_attributes=False)
        self.assertEqual(body(ROOT/"src/arbitration/recovery_controls.py","fit_control"),body(ROOT/"src/arbitration/empirical_panel.py","fit_panel"))

    def test_fresh_selection_excludes_history_and_fails_on_short_frame(self):
        sources={d:{(d,str(i)) for i in range(2001)} for d in DATASETS}
        forbidden={(d,"0") for d in DATASETS}
        chosen=select_fresh_ids(sources,forbidden)
        for d in DATASETS:
            self.assertEqual(len(set(chosen[d])),2000)
            self.assertNotIn("0",chosen[d])
        sources[DATASETS[0]].remove((DATASETS[0],"1"))
        with self.assertRaises(ValueError):select_fresh_ids(sources,forbidden)


if __name__=="__main__":unittest.main()
