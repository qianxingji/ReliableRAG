from pathlib import Path
import types
import unittest

import torch
from scripts.empirical_gbv_witness import GbVWitness
from scripts.empirical_scoring_import_v2 import source_only_import


class ToyPairTokenizer:
    def __call__(self,left,right,**kwargs):
        def ids(a,b):return [1]+[3+len(w)%11 for w in a.split()]+[2]+[3+len(w)%11 for w in b.split()]+[2]
        if isinstance(left,str):return dict(input_ids=ids(left,right))
        rows=[ids(a,b) for a,b in zip(left,right)];width=max(map(len,rows))
        return dict(input_ids=torch.tensor([r+[0]*(width-len(r)) for r in rows]),
                    attention_mask=torch.tensor([[1]*len(r)+[0]*(width-len(r)) for r in rows]))


class ToyNLI(torch.nn.Module):
    def __init__(self):
        super().__init__();self.calls=0;self.bad=False;self.config=types.SimpleNamespace(id2label={0:'entailment',1:'not_entailment'})
    def forward(self,input_ids,attention_mask):
        self.calls+=1;values=input_ids.float().sum(dim=1)*.001
        logits=torch.stack((values,-values),dim=1)
        if self.bad:logits[0,0]=float('nan')
        return types.SimpleNamespace(logits=logits)


class GbVWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.native=source_only_import('invented_native_gbv',Path('E:/paper/ReliableRAG/src/verification/gbv_nli.py'))

    def scorer(self,limit=64):
        scorer=self.native.GBVPostAnsweringNLI.__new__(self.native.GBVPostAnsweringNLI)
        scorer.tokenizer=ToyPairTokenizer();scorer.model=ToyNLI().eval();scorer.torch=torch
        scorer.entailment_index=0;scorer.max_length=limit;scorer.batch_size=8;scorer.device='cpu'
        return scorer

    def test_native_logits_maximum_and_exact_repeated_branches_without_extra_forwards(self):
        scorer=self.scorer();record=GbVWitness(scorer,self.native)
        evidence=['A silver paper cog is invented.']*5
        first,witness=record.score_branch('Color?','silver',evidence)
        second,again=record.score_branch('Color?','silver',evidence)
        self.assertEqual(first,second);self.assertEqual(scorer.model.calls,2)
        self.assertEqual(witness['chunk_count'],5)
        self.assertEqual(witness['batches'][0]['logits'],again['batches'][0]['logits'])
        record.close()

    def test_chunking_retains_all_passages_and_respects_native_limit(self):
        scorer=self.scorer(limit=24);record=GbVWitness(scorer,self.native)
        passages=[' '.join('token'+str(i) for i in range(35)),'short passage']
        result,witness=record.score_branch('Color?','silver',passages)
        self.assertGreater(result.chunk_count,2)
        self.assertEqual(result.chunk_count,sum(witness['premise_chunk_counts']))
        self.assertTrue(all(len(r['token_fields']['input_ids'][0])<=24 for r in witness['batches']))
        self.assertEqual(scorer.model.calls,(result.chunk_count+7)//8)
        record.close()

    def test_impossible_hypothesis_and_nonfinite_logits_fail_closed(self):
        scorer=self.scorer(limit=24);record=GbVWitness(scorer,self.native)
        with self.assertRaises(ValueError):record.score_branch('word '*30,'silver',['toy'])
        self.assertEqual(scorer.model.calls,0)
        scorer.model.bad=True
        with self.assertRaisesRegex(RuntimeError,'logits shape/finite'):record.score_branch('Color?','silver',['toy'])
        record.close()


if __name__=='__main__':unittest.main()
