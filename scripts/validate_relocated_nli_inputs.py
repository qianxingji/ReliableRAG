"""Separate complete preparation checks with the frozen independent chunker."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
import traceback
import types


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);parser.add_argument('--config-sha256',required=True)
    parser.add_argument('--producer-inputs',type=Path,required=True);parser.add_argument('--producer-inputs-sha256',required=True);args=parser.parse_args()
    cfg=json.loads(args.config.read_text(encoding='utf-8'));rec=next(e for e in cfg['controls'] if e['name']=='io');path=Path(rec['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['sha256']
    io=types.ModuleType('independent_nli_transport');io.__file__=str(path);sys.modules[io.__name__]=io;exec(compile(path.read_bytes(),str(path),'exec'),io.__dict__)
    cfg,out,env,named,state,allowed,result=io.setup(args.config,args.config_sha256,'validator')
    nli=io.load_module('nli_input_helpers',Path(next(e for e in cfg['controls'] if e['name']=='nli_io')['path']))
    try:
        assert io.sha(args.producer_inputs)==args.producer_inputs_sha256
        for e in json.loads(args.producer_inputs.read_text())['files']:
            p=out/e['path'];assert p.parent==out and io.sha(p)==e['sha256'] and p.stat().st_size==e['size_bytes']
        producer=json.loads((out/'PRODUCER_RESULT.json').read_text());assert producer['status']=='PASS_FULL_HISTORICAL_NLI_PREPARATION_PENDING_INDEPENDENT'
        independent=nli.independent_sources(named,io,result['ast_nodes'])
        eligibility=io.load_module('original_nli_eligibility',named['eligibility'])
        tokenizer,config=nli.factory(cfg,named,io,result)
        assert independent.positive_index(config.id2label)==0
        fixture=nli.fixtures(tokenizer,independent.hypothesis,independent.chunks,independent.positive_index,independent.length)
        assert fixture==producer['fixtures'];result['fixtures']=fixture
        vocab=io.jsha(tokenizer.get_vocab());assert vocab==producer['tokenizer_vocabulary_sha256']
        provenance,execution=nli.archive_metadata(named,io)
        keys=set();questions=set();strata=collections.Counter();counts=collections.Counter();pairs=batches=input_tokens=token_values=0;historical_checks=0
        with named['branches'].open(encoding='utf-8') as branches,named['gbv_scores'].open(encoding='utf-8') as scores,(out/'NLI_PREPARATION_PRIVATE.jsonl').open(encoding='utf-8') as witnesses:
            for position,line in enumerate(branches):
                branch=json.loads(line);archived=json.loads(next(scores));witness=json.loads(next(witnesses));nli.source_pair(branch,archived)
                k=nli.key(branch);assert k not in keys and nli.key(witness)==k;keys.add(k);questions.add((k[0],k[2]));strata[k[:2]]+=1
                assert witness['position']==position and set(witness)=={'position','dataset','retriever','sample_id','eligible','forced_keep_reason','e0_premise_count','e1_premise_count','e0_chunk_count','e1_chunk_count','new_preparation','bindings'}
                assert witness['bindings']==dict(branch_sha256=io.jsha(branch),archived_score_row_sha256=io.jsha(archived))
                eligible=eligibility.assess_pair_eligibility(branch['a0'],branch['a1']);scorable=eligible.eligible;reason=eligible.reason
                rebuilt_counts=dict(e0_premise_count=5,e1_premise_count=5,e0_chunk_count=0,e1_chunk_count=0);prepared=None
                if scorable:
                    prepared={}
                    try:
                        for side,answer,field in [('e0','a0','evidence0'),('e1','a1','evidence1')]:
                            claim=independent.hypothesis(branch['question'],branch[answer])
                            parts=[independent.chunks(tokenizer,text,claim,max_length=512,overlap=20) for text in branch[field]]
                            flat=[(part,claim) for passage in parts for part in passage];batch_rows=[]
                            for offset in range(0,len(flat),8):
                                block=flat[offset:offset+8]
                                encoded=dict(tokenizer([x[0] for x in block],[x[1] for x in block],truncation=False,padding=True))
                                assert set(encoded)==set(tokenizer.model_input_names)
                                widths={len(ids) for ids in encoded['input_ids']};assert len(widths)==1 and 0<next(iter(widths))<=512
                                assert all(len(array)==len(block) and all(len(row)==next(iter(widths)) and all(type(v)is int for v in row) for row in array) for array in encoded.values())
                                assert all(v in (0,1) for row in encoded['attention_mask'] for v in row)
                                token_values+=sum(len(row) for array in encoded.values() for row in array)
                                input_tokens+=sum(sum(mask) for mask in encoded['attention_mask']);pairs+=len(block);batches+=1
                                batch_rows.append(dict(start=offset,size=len(block),tokens=encoded))
                            rebuilt_counts[side+'_chunk_count']=len(flat)
                            prepared[side]=dict(hypothesis=claim,premise_chunks=parts,batches=batch_rows)
                    except ValueError as exc:
                        scorable=False;reason='nli_unscorable:'+str(exc);prepared=None;rebuilt_counts.update(e0_chunk_count=0,e1_chunk_count=0)
                expected=dict(eligible=scorable,forced_keep_reason=reason,**rebuilt_counts)
                for field,value in expected.items():
                    assert value==archived[field] and type(value)is type(archived[field]) and value==witness[field] and type(value)is type(witness[field]);historical_checks+=1
                assert prepared==witness['new_preparation'],'FULL_NEW_INPUT_WITNESS_MISMATCH'
                counts['scored' if scorable else reason]+=1
                if (position+1)%1500==0:print('INDEPENDENT_NLI_INPUT_ROWS',position+1,13500,flush=True)
            assert scores.readline()==witnesses.readline()==''
        assert len(keys)==13500 and len(questions)==4500 and strata==collections.Counter({(d,r):1500 for d in ('hotpotqa','2wikimultihopqa','musique') for r in ('bm25','dense','hybrid')})
        assert dict(counts)==provenance['counts']==producer['counts'] and historical_checks==81000
        assert pairs==producer['prepared_chunk_pairs']==execution['call_counters']['gbv_nli_pairs']==32174
        assert batches==producer['prepared_batches']==execution['call_counters']['gbv_nli_forward_calls']==6404
        assert input_tokens==producer['input_tokens'] and io.jsha(tokenizer.get_vocab())==vocab
        assert not producer['blocked_events'] and not producer['forbidden_calls'] and producer['capability_sockets_closed'] and not producer['torch_cuda_initialized']
        result.update(status='PASS_HISTORICAL_NLI_COUNTS_AND_NEW_INPUT_WITNESSES_ONLY',traces=13500,question_groups=4500,counts=dict(counts),
            strata={d+'/'+r:n for (d,r),n in sorted(strata.items())},historical_count_comparisons=historical_checks,
            new_prepared_branches=6404,original_premises=32020,prepared_chunk_pairs=pairs,prepared_batches=batches,input_tokens=input_tokens,
            exact_new_token_mask_type_scalar_comparisons=token_values,tokenizer_vocabulary_sha256=vocab,tokenizer_vocabulary_unchanged=True,
            historical_token_ids_available=False,old_neural_scores_replayed=False,new_witnesses_not_historical=True)
        result['binary_ownership']=nli.binary_ownership(cfg,io,allowed)
    except Exception as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    io.finish(result,state,allowed,out,'INDEPENDENT_RESULT.json')
    print(json.dumps({k:result[k] for k in ('status','traces','prepared_chunk_pairs','prepared_batches','input_tokens') if k in result},indent=2))
    return 0 if result['status'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
