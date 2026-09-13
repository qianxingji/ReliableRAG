"""Observe unchanged native GbV chunk/token/logit/probability bindings."""
import hashlib


def text_sha(text):return hashlib.sha256(str(text).encode('utf-8')).hexdigest()


class GbVWitness:
    """Repeats native token preparation for binding; adds no NLI forward or cache."""
    def __init__(self, scorer, native):
        self.scorer=scorer;self.native=native;self.active=False;self.forward_count=0
        self.hook=scorer.model.register_forward_hook(self._forward,with_kwargs=True)

    def _forward(self,model,args,kwargs,output):
        import torch
        if not self.active or self.position>=len(self.pairs):raise RuntimeError('Unexpected GbV forward')
        if not torch.is_inference_mode_enabled() or torch.is_grad_enabled() or model.training:raise RuntimeError('GbV inference context')
        pairs=self.pairs[self.position:self.position+self.scorer.batch_size]
        expected=self.scorer.tokenizer([p for p,h in pairs],[h for p,h in pairs],
            add_special_tokens=True,truncation=False,padding=True,return_tensors='pt')
        if set(expected)!=set(kwargs):raise RuntimeError('GbV token field set')
        tokens={name:tensor.detach().cpu().tolist() for name,tensor in kwargs.items()}
        if tokens!={name:tensor.tolist() for name,tensor in expected.items()}:raise RuntimeError('GbV chunk/token batch binding')
        if kwargs['input_ids'].shape[1]>self.scorer.max_length:raise RuntimeError('GbV context bound')
        logits=output.logits.float()
        if tuple(logits.shape)!=(len(pairs),len(model.config.id2label)) or not torch.isfinite(logits).all():raise RuntimeError('GbV logits shape/finite')
        probabilities=torch.softmax(logits,dim=-1)
        if not torch.isfinite(probabilities).all():raise RuntimeError('GbV finite probabilities')
        self.forward_count+=1
        self.records.append(dict(forward_ordinal=self.forward_count,pair_offset=self.position,
            pairs=[dict(premise=p,hypothesis=h) for p,h in pairs],token_fields=tokens,
            logits=logits.detach().cpu().tolist(),probabilities=probabilities.detach().cpu().tolist(),
            entailment_index=self.scorer.entailment_index,max_length=self.scorer.max_length))
        self.position+=len(pairs)
        return None

    def score_branch(self,question,answer,evidence):
        if self.active:raise RuntimeError('Nested GbV request')
        evidence=[str(p) for p in evidence];hypothesis=self.native.format_hypothesis(question,answer)
        self.pairs=[];chunk_counts=[]
        for premise in evidence:
            chunks=self.native.split_passage_to_fit(self.scorer.tokenizer,premise,hypothesis,
                max_length=self.scorer.max_length,overlap_words=self.native.GBV_WORD_OVERLAP)
            self.pairs.extend((chunk,hypothesis) for chunk in chunks);chunk_counts.append(len(chunks))
        self.position=0;self.records=[];self.active=True
        try:result=self.scorer.score_branch(question,answer,evidence)
        finally:self.active=False
        if self.position!=len(self.pairs) or result.premise_count!=len(evidence) or result.chunk_count!=len(self.pairs):
            raise RuntimeError('GbV complete chunk accounting')
        values=[p[self.scorer.entailment_index] for r in self.records for p in r['probabilities']]
        if not values or result.score!=max(values):raise RuntimeError('GbV native maximum differs from witnesses')
        return result,dict(question_sha256=text_sha(question),answer_sha256=text_sha(answer),
            hypothesis_sha256=text_sha(hypothesis),premise_sha256=[text_sha(p) for p in evidence],
            premise_chunk_counts=chunk_counts,batches=list(self.records),native_score=result.score,
            premise_count=result.premise_count,chunk_count=result.chunk_count)

    def close(self):self.hook.remove()
