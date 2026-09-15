"""Observe native teacher-forced likelihood forwards without changing their outputs."""
from dataclasses import asdict


class LikelihoodWitness:
    """One native batch-size-1 scorer, empty initial cache, fixed call order.

    Repeats native preparation for token binding before the real score() call.
    Adds no neural forward. The forward hook returns None and never alters logits.
    Sidecar reductions independently check every native aggregate and cache hit.
    """
    def __init__(self, scorer):
        if int(scorer.config["batch_size"]) != 1: raise ValueError("Native likelihood batch size 1 required")
        self.scorer=scorer;self.tokens={};self.active=False;self.forward_count=0
        self.hook=scorer.model.register_forward_hook(self._forward,with_kwargs=True)

    def _forward(self, model, args, kwargs, output):
        import torch
        if not self.active or self.cursor >= len(self.misses): raise RuntimeError("Unexpected likelihood forward")
        if not torch.is_inference_mode_enabled() or torch.is_grad_enabled() or model.training:
            raise RuntimeError("Likelihood inference context")
        prepared=self.misses[self.cursor];self.cursor+=1
        ids=kwargs["input_ids"];mask=kwargs["attention_mask"];position_ids=kwargs["position_ids"]
        if ids.shape[0] != 1 or ids[0].tolist() != prepared["input_ids"]: raise RuntimeError("Likelihood input token binding")
        if mask[0].tolist() != [1]*len(prepared["input_ids"]) or position_ids[0].tolist() != list(range(len(prepared["input_ids"]))):
            raise RuntimeError("Likelihood mask/position binding")
        if kwargs["use_cache"] is not False: raise RuntimeError("Teacher-forced cache configuration")
        prompt=len(prepared["prompt_ids"]);answer=len(prepared["answer_ids"])
        positions=torch.arange(prompt-1,prompt+answer-1,device=ids.device)
        targets=ids[0,prompt:prompt+answer]
        logits=output.logits[0,positions,:].float()
        values=(logits.gather(1,targets[:,None]).squeeze(1)-torch.logsumexp(logits,dim=-1)).cpu().tolist()
        if len(values) != answer: raise RuntimeError("Answer token witness count")
        self.forward_count+=1
        witness=dict(forward_ordinal=self.forward_count,cache_key=prepared["cache_key"],
            prompt_sha256=prepared["prompt_sha256"],answer_sha256=prepared["answer_sha256"],
            evidence_hash=prepared["evidence_hash"],input_token_ids=prepared["input_ids"],
            attention_mask=mask[0].tolist(),position_ids=position_ids[0].tolist(),
            answer_token_ids=prepared["answer_ids"],answer_prediction_positions=positions.tolist(),
            token_log_probabilities=values,prompt_token_count=prompt,answer_token_count=answer,
            truncation=prepared["truncation"],model_revision=self.scorer.resolved_revision)
        previous=self.tokens.get(prepared["cache_key"])
        if previous is not None and previous["token_log_probabilities"] != values:
            raise RuntimeError("Identical likelihood cache key produced different tokens")
        self.tokens[prepared["cache_key"]]=witness;self.records.append(witness)
        return None

    def score(self, items):
        if self.active: raise RuntimeError("Nested likelihood request")
        prepared=[self.scorer._prepare(item) for item in items]
        existing=[self.scorer._cache_path(p["cache_key"]).exists() for p in prepared]
        if any(hit and p["cache_key"] not in self.tokens for p,hit in zip(prepared,existing)):
            raise RuntimeError("Existing likelihood cache without current-run witness")
        self.misses=[p for p,hit in zip(prepared,existing) if not hit]
        self.cursor=0;self.records=[];self.active=True
        before_calls=self.scorer.calls;before_hits=self.scorer.cache_hits
        try:results=self.scorer.score(items)
        finally:self.active=False
        if self.cursor != len(self.misses) or self.scorer.calls-before_calls != len(self.misses):
            raise RuntimeError("Native likelihood forward accounting")
        if self.scorer.cache_hits-before_hits != sum(existing): raise RuntimeError("Native likelihood cache accounting")
        requests=[]
        for index,(p,result,hit) in enumerate(zip(prepared,results,existing,strict=True)):
            witness=self.tokens[p["cache_key"]];values=witness["token_log_probabilities"]
            expected=(sum(values),sum(values)/len(values),min(values))
            actual=(result.sum_log_probability,result.mean_log_probability,result.minimum_log_probability)
            if expected != actual: raise RuntimeError("Native likelihood reduction differs from token witness")
            if result.cache_hit is not hit or result.cache_key != p["cache_key"]: raise RuntimeError("Native cache receipt binding")
            if result.prompt_sha256 != p["prompt_sha256"] or result.answer_sha256 != p["answer_sha256"]:
                raise RuntimeError("Native likelihood prompt/answer binding")
            if result.ordered_evidence_hash != p["evidence_hash"] or result.ordered_evidence_ids != p["evidence_ids"]:
                raise RuntimeError("Native likelihood evidence binding")
            if result.answer_token_count != len(p["answer_ids"]) or result.prompt_token_count != len(p["prompt_ids"]):
                raise RuntimeError("Native likelihood token counts")
            requests.append(dict(cell_position=index,cache_key=p["cache_key"],cache_hit=hit,
                forward_ordinal=witness["forward_ordinal"],native_result=asdict(result)))
        return results,requests,list(self.records)

    def close(self):self.hook.remove()
