"""CPU fake-logit tests exercise the original scoring method and cache behavior."""
import copy
from pathlib import Path
import tempfile
import types
import unittest

import torch
from scripts.empirical_likelihood_witness import LikelihoodWitness
from scripts.empirical_scoring_import_v2 import source_only_import
from scripts.empirical_scoring_fixtures import invented_trace


class ToyTokenizer:
    pad_token_id=0
    def __call__(self,text,**kwargs):return dict(input_ids=[1+ord(c)%30 for c in text])
    def apply_chat_template(self,messages,**kwargs):return '<user>'+messages[0]['content']+'<answer>'


class ToyModel(torch.nn.Module):
    def forward(self,input_ids,attention_mask,position_ids,use_cache):
        vocab=torch.arange(32,dtype=torch.float32)
        logits=(vocab[None,None,:]-.2*input_ids[:,:,None].float()).square()*.002
        return types.SimpleNamespace(logits=logits)


class LikelihoodWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=source_only_import('invented_native_likelihood',Path('E:/paper/ReliableRAG/src/scoring/reader_likelihood.py'))

    def scorer(self,directory):
        native=self.native.ReaderLikelihoodScorer.__new__(self.native.ReaderLikelihoodScorer)
        native.config=dict(batch_size=1,max_length=8192,context_budget_characters=16000)
        native.cache_root=Path(directory);native.answer_template='{question}\n{evidence}'
        native.device=torch.device('cpu');native.tokenizer=ToyTokenizer();native.model=ToyModel().eval();native.resolved_revision='invented'
        for name in ('calls','sequences_scored','cache_hits','wall_seconds','prompt_tokens','answer_tokens','peak_allocated_bytes','peak_reserved_bytes'):
            setattr(native,name,0)
        native.latencies=[]
        return native

    def items(self):
        trace=invented_trace(0,'bm25')
        return [dict(question=trace['question'],answer=trace[a],evidence=trace[e])
                for a,e in (('a0','E0'),('a0','E1'),('a1','E0'),('a1','E1'))]

    def test_exact_native_cell_reductions_cache_hits_and_no_extra_forward(self):
        with tempfile.TemporaryDirectory() as directory:
            scorer=self.scorer(directory);record=LikelihoodWitness(scorer)
            first,requests,witnesses=record.score(self.items())
            self.assertEqual((scorer.calls,scorer.sequences_scored,len(witnesses)),(4,4,4))
            second,cached,repeated=record.score(self.items())
            self.assertEqual((scorer.calls,scorer.cache_hits,repeated),(4,4,[]))
            self.assertTrue(all(r['cache_hit'] for r in cached))
            for result,witness in zip(first,witnesses):
                self.assertEqual(result.sum_log_probability,sum(witness['token_log_probabilities']))
                self.assertEqual(witness['answer_prediction_positions'][0],result.prompt_token_count-1)
            self.assertEqual([r.mean_log_probability for r in first],[r.mean_log_probability for r in second])
            record.close()

    def test_cache_cannot_be_inherited_without_current_run_witness(self):
        with tempfile.TemporaryDirectory() as directory:
            scorer=self.scorer(directory);scorer.score(self.items())
            record=LikelihoodWitness(scorer)
            with self.assertRaisesRegex(RuntimeError,'without current-run witness'):record.score(self.items())
            record.close()

    def test_native_prompt_truncation_and_impossible_answer_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            scorer=self.scorer(directory);scorer.config['max_length']=12
            record=LikelihoodWitness(scorer)
            results,requests,witnesses=record.score(self.items())
            self.assertTrue(all(r.truncation for r in results))
            self.assertTrue(all(len(w['input_token_ids'])==12 for w in witnesses))
            invalid=copy.deepcopy(self.items());invalid[0]['answer']='x'*13
            with self.assertRaisesRegex(RuntimeError,'Answer alone exceeds'):record.score(invalid)
            record.close()


if __name__=='__main__':unittest.main()
