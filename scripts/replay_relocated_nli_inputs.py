"""Full original NLI chunk preparation; new token witnesses, no probabilities."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
import traceback
import types


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--config',type=Path,required=True); parser.add_argument('--config-sha256',required=True); args=parser.parse_args()
    cfg=json.loads(args.config.read_text(encoding='utf-8')); rec=next(e for e in cfg['controls'] if e['name']=='io'); path=Path(rec['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['sha256']
    io=types.ModuleType('nli_transport');io.__file__=str(path);sys.modules[io.__name__]=io;exec(compile(path.read_bytes(),str(path),'exec'),io.__dict__)
    cfg,out,env,named,state,allowed,result=io.setup(args.config,args.config_sha256,'producer')
    nli=io.load_module('nli_input_helpers',Path(next(e for e in cfg['controls'] if e['name']=='nli_io')['path']))
    mismatches=[]
    try:
        native=nli.native_sources(named,io,result['ast_nodes'])
        independent=nli.independent_sources(named,io,result['ast_nodes'])
        eligibility=io.load_module('original_nli_eligibility',named['eligibility'])
        tokenizer,config=nli.factory(cfg,named,io,result)
        assert native.effective_model_max_length(tokenizer,config)==512 and native.resolve_entailment_index(config.id2label)==0
        native_fixture=nli.fixtures(tokenizer,native.format_hypothesis,native.split_passage_to_fit,native.resolve_entailment_index,native.pair_token_length)
        independent_fixture=nli.fixtures(tokenizer,independent.hypothesis,independent.chunks,independent.positive_index,independent.length)
        assert native_fixture==independent_fixture
        result['fixtures']=native_fixture
        vocabulary_sha=io.jsha(tokenizer.get_vocab()); provenance,execution=nli.archive_metadata(named,io)
        counters=collections.Counter();strata=collections.Counter();keys=set();questions=set();pairs=batches=input_tokens=0
        with named['branches'].open(encoding='utf-8') as branches, named['gbv_scores'].open(encoding='utf-8') as scores, (out/'NLI_PREPARATION_PRIVATE.jsonl').open('x',encoding='utf-8',newline='\n') as output:
            for position,line in enumerate(branches):
                branch=json.loads(line);archived=json.loads(next(scores));nli.source_pair(branch,archived)
                k=nli.key(branch);assert k not in keys;keys.add(k);questions.add((k[0],k[2]));strata[k[:2]]+=1
                eligible=eligibility.assess_pair_eligibility(branch['a0'],branch['a1'])
                counts=dict(e0_premise_count=5,e1_premise_count=5,e0_chunk_count=0,e1_chunk_count=0)
                prepared=None;reason=eligible.reason;scorable=eligible.eligible
                if scorable:
                    prepared={}
                    try:
                        for side,answer,field in [('e0','a0','evidence0'),('e1','a1','evidence1')]:
                            claim=native.format_hypothesis(branch['question'],branch[answer])
                            by_premise=[native.split_passage_to_fit(tokenizer,text,claim,max_length=512,overlap_words=20) for text in branch[field]]
                            ordered=[(text,claim) for chunks in by_premise for text in chunks];batch_rows=[]
                            for start in range(0,len(ordered),8):
                                block=ordered[start:start+8]
                                encoded=tokenizer([x[0] for x in block],[x[1] for x in block],truncation=False,padding=True,return_tensors='pt')
                                assert encoded['input_ids'].shape[1]<=512
                                values={name:value.tolist() for name,value in encoded.items()}
                                batch_rows.append(dict(start=start,size=len(block),tokens=values))
                                pairs+=len(block);batches+=1;input_tokens+=int(encoded['attention_mask'].sum().item())
                            counts[side+'_chunk_count']=len(ordered)
                            prepared[side]=dict(hypothesis=claim,premise_chunks=by_premise,batches=batch_rows)
                    except ValueError as exc:
                        reason='nli_unscorable:'+str(exc);scorable=False;prepared=None
                        counts.update(e0_chunk_count=0,e1_chunk_count=0)
                counters['scored' if scorable else reason]+=1
                wanted=dict(eligible=scorable,forced_keep_reason=reason,**counts)
                failures=[name for name,value in wanted.items() if value!=archived[name] or type(value) is not type(archived[name])]
                if failures:mismatches.append(dict(position=position,key=k,fields=failures,rebuilt=wanted))
                row=dict(position=position,dataset=k[0],retriever=k[1],sample_id=k[2],**wanted,new_preparation=prepared,
                    bindings=dict(branch_sha256=io.jsha(branch),archived_score_row_sha256=io.jsha(archived)))
                output.write(json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n');output.flush()
                if (position+1)%1500==0:print('NLI_PREPARATION_ROWS',position+1,13500,flush=True)
            assert scores.readline()==''
        assert len(keys)==13500 and len(questions)==4500 and strata==collections.Counter({(d,r):1500 for d in ('hotpotqa','2wikimultihopqa','musique') for r in ('bm25','dense','hybrid')})
        assert dict(counters)==provenance['counts'] and not mismatches
        assert pairs==execution['call_counters']['gbv_nli_pairs']==32174 and batches==execution['call_counters']['gbv_nli_forward_calls']==6404
        assert io.jsha(tokenizer.get_vocab())==vocabulary_sha
        result.update(status='PASS_FULL_HISTORICAL_NLI_PREPARATION_PENDING_INDEPENDENT',traces=13500,question_groups=4500,counts=dict(counters),
            new_prepared_branches=6404,original_premises=32020,prepared_chunk_pairs=pairs,prepared_batches=batches,input_tokens=input_tokens,
            historical_count_comparisons=81000,tokenizer_vocabulary_sha256=vocabulary_sha,tokenizer_vocabulary_unchanged=True,
            historical_token_ids_available=False,old_neural_scores_replayed=False,new_witnesses_not_historical=True,mismatches=0)
        result['binary_ownership']=nli.binary_ownership(cfg,io,allowed)
    except Exception as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    io.write(out/'MISMATCHES_PRIVATE.json',mismatches);io.finish(result,state,allowed,out,'PRODUCER_RESULT.json')
    print(json.dumps({k:result[k] for k in ('status','traces','prepared_chunk_pairs','prepared_batches','input_tokens') if k in result},indent=2))
    return 0 if result['status'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
