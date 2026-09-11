"""Meaningful numerical and forbidden-access tests using invented inputs only."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np
from scripts.empirical_scoring_io import FIELDS, panel_scores
from scripts.empirical_scoring_fixtures import scalar_panel


class ScoringTests(unittest.TestCase):
    def panel(self):
        return {name:dict(numeric_indices=indices,feature_dimension=2*len(indices)+3,
            preprocessing=dict(median=[2.]*len(indices),mean=[1.]*len(indices),std=[2.]*len(indices)),
            coef=[.25]*(2*len(indices))+[.5,1.,1.5],intercept=-.25,platt_slope=.5,platt_intercept=.125)
            for name,indices in FIELDS.items()}

    def test_imputation_flags_and_retriever_columns_against_scalar_formula(self):
        keys=[("hotpotqa",r,"invented") for r in ("bm25","dense","hybrid")]
        data=[[None]+[3.]*10,[2.]*10+[None],[1.]*11]
        panel=self.panel();actual=panel_scores(panel,keys,data)
        for name,model in panel.items():
            for i,key in enumerate(keys):
                expected=scalar_panel(model,key[1],data[i])
                np.testing.assert_allclose([actual[name]["logit_R"][i],actual[name]["pR"][i]],expected,rtol=0,atol=1e-12)

    def test_duplicate_keys_wrong_shape_and_invalid_scale_rejected(self):
        key=("hotpotqa","bm25","toy")
        with self.assertRaises(RuntimeError):panel_scores(self.panel(),[key,key],[[0.]*11]*2)
        with self.assertRaises(RuntimeError):panel_scores(self.panel(),[key],[[0.]*10])
        panel=self.panel();panel["ROA-FULL"]["preprocessing"]["std"][0]=0
        with self.assertRaises(RuntimeError):panel_scores(panel,[key],[[0.]*11])

    def test_real_guard_denies_benchmark_weights_writes_and_fit(self):
        code=r'''
import json,tempfile
from pathlib import Path
from scripts.empirical_scoring_guard import guard
root=Path(tempfile.mkdtemp()).resolve();out=root/'out';out.mkdir()
(root/'data/raw').mkdir(parents=True)
raw=root/'data/raw/raw.jsonl';raw.write_text('invented')
fresh=root/'fresh.jsonl';fresh.write_text('invented')
weight=root/'model.safetensors';weight.write_bytes(b'not a model')
saved=root/'saved.joblib';saved.write_bytes(b'not a pickle')
receipt=guard(root,out,[raw,weight,saved],mode='cpu_models')
assert saved.read_bytes()==b'not a pickle'
def expect_bad(fn):
    try:fn()
    except RuntimeError:return
    raise AssertionError('Expected guarded denial')
expect_bad(raw.read_bytes);expect_bad(fresh.read_bytes);expect_bad(weight.read_bytes)
expect_bad(lambda:(root/'forbidden.txt').write_text('blocked'))
(out/'cache').mkdir();part=out/'cache/a.json.part';target=out/'cache/a.json'
part.write_text('first');part.replace(target)
part.write_text('second');expect_bad(lambda:part.replace(target));assert target.read_text()=='first'
def fit():raise AssertionError('fit body must never execute')
expect_bad(fit)
assert len(receipt['denied'])==6
print(json.dumps({'denials':len(receipt['denied']),'saved_bytes_read':True,'immutable_cache_target':True}))
'''
        run=subprocess.run([sys.executable,"-B","-c",code],cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["denials"],6)


if __name__=="__main__":unittest.main()
