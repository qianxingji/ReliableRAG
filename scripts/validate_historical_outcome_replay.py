"""Full fresh reference reread and independent historical metric comparison."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback
import types


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--config-sha256',required=True)
    p.add_argument('--producer-inputs',type=Path,required=True);p.add_argument('--producer-inputs-sha256',required=True);a=p.parse_args()
    assert hashlib.sha256(a.config.read_bytes()).hexdigest()==a.config_sha256
    cfg=json.loads(a.config.read_text());entry=next(e for e in cfg['controls'] if e['name']=='io');path=Path(entry['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    io=types.ModuleType('historical_outcome_independent_io');io.__file__=str(path);sys.modules[io.__name__]=io;exec(compile(path.read_bytes(),str(path),'exec'),io.__dict__)
    cfg,out,named,controls,state,allowed,selected,result=io.setup(a.config,a.config_sha256,'validator')
    try:
        io.require(io.sha(a.producer_inputs)==a.producer_inputs_sha256,'PRODUCER_INPUT_PIN')
        for e in io.load(a.producer_inputs)['files']:
            path=out/e['path'];io.require(path.is_relative_to(out) and io.sha(path)==e['sha256'] and path.stat().st_size==e['size_bytes'],'PRODUCER_ARTIFACT_PIN')
        producer=io.load(out/'PRODUCER_RESULT.json');io.require(producer['status']=='PASS_FULL_HISTORICAL_SOURCE_MAPPING_PENDING_INDEPENDENT','PRODUCER_COMPLETED')
        spec,provenance,serialization,readers,Cursor,metric,projected,independent=io.assemble(cfg,named,result)
        io.require(result['source_ast_nodes']==producer['source_ast_nodes'],'MATCHING_FROZEN_DEFINITIONS')
        pa,pq,observer=io.arrow(cfg,controls,result)
        result['fixtures']=io.fixtures(pa,pq,observer,readers,Cursor,metric,independent,out)
        tracked=observer.ObservedParquet(pq,{sid for ds,sid in selected if ds=='hotpotqa'},{named['source_hotpotqa']})
        references,counts=readers.load_references(spec,selected,Cursor,tracked)
        binding=serialization.jsha([[ds,sid,references[(ds,sid)]] for ds,sid in sorted(references)])
        io.require(binding==provenance['selected_reference_binding_sha256']==producer['selected_reference_binding_sha256'],'INDEPENDENT_REFERENCE_BINDING')
        io.require(counts==provenance['source_counts']==producer['source_counts'],'INDEPENDENT_SOURCE_COUNTS')
        io.require(tracked.identifiers==7405 and tracked.python_answer_scalars==1500 and not tracked.denied,'SELECTED_ARROW_CONVERSIONS')
        print('INDEPENDENT_HISTORICAL_REFERENCE_BINDING_PASS',4500,flush=True)
        fields={'dataset','retriever','sample_id','a0_em','a1_em','a0_f1','a1_f1'}
        def check_row(row,branch,refs):
            io.require(set(row)==fields,'EXACT_NUMERIC_SCHEMA')
            io.require(all(row[k]==branch[k] and type(row[k])is str for k in ('dataset','retriever','sample_id')),'EXACT_ORDERED_IDENTITY')
            errors=[]
            for side in ('a0','a1'):
                em,f1=independent.metrics(branch[side],refs)
                io.require(type(row[side+'_em'])is int and row[side+'_em'] in (0,1) and row[side+'_em']==em,'INDEPENDENT_EM')
                observed=row[side+'_f1'];io.require(type(observed)in (int,float) and math.isfinite(observed) and 0<=observed<=1,'FINITE_F1')
                error=abs(observed-f1);io.require(error<=1e-15,'INDEPENDENT_F1');errors.append(error)
            return max(errors)
        invented=dict(dataset='invented',retriever='bm25',sample_id='fixture',a0='yes',a1='no')
        bad=dict(dataset='invented',retriever='bm25',sample_id='fixture',a0_em=0,a1_em=0,a0_f1=1.,a1_f1=0.)
        try:check_row(bad,invented,['yes'])
        except RuntimeError as exc:io.require(str(exc)=='INDEPENDENT_EM','CORRUPTION_REJECTION_REASON')
        else:raise AssertionError('CORRUPT_NUMERIC_ROW_ACCEPTED')
        result['corrupt_numeric_row_rejected']=True
        seen=set();strata=Counter();maximum=0.;comparisons=0
        with (out/'NUMERIC_OUTCOMES_PRIVATE.jsonl').open(encoding='utf-8') as new,named['archived_outcomes'].open(encoding='utf-8') as old:
            for branch in projected.canonical_answer_rows(named['branches'],Cursor):
                k=(branch['dataset'],branch['retriever'],branch['sample_id']);io.require(k not in seen and (k[0],k[2]) in selected,'UNIQUE_HISTORICAL_BRANCH')
                seen.add(k);strata[k[:2]]+=1;refs=references[(k[0],k[2])]
                for row in (json.loads(next(new)),json.loads(next(old))):maximum=max(maximum,check_row(row,branch,refs));comparisons+=4
                if len(seen)%1500==0:print('INDEPENDENT_HISTORICAL_OUTCOME_ROWS',len(seen),13500,flush=True)
            io.require(new.readline()==old.readline()=='','EXACT_LEDGER_EOF')
        io.require(seen=={(ds,r,sid) for ds,sid in selected for r in ('bm25','dense','hybrid')} and len(seen)==13500,'COMPLETE_HISTORICAL_KEY_SET')
        io.require(strata=={(d,r):1500 for d in ('hotpotqa','2wikimultihopqa','musique') for r in ('bm25','dense','hybrid')} and comparisons==108000,'FULL_METRIC_COVERAGE')
        io.require(io.sha(out/'NUMERIC_OUTCOMES_PRIVATE.jsonl')==io.sha(named['archived_outcomes'])==producer['numeric_ledger_sha256'],'EXACT_ORIGINAL_NEW_LEDGER_BYTES')
        result.update(status='PASS_FULL_HISTORICAL_REFERENCE_AND_OUTCOME_REPLAY',historical_questions=4500,traces=13500,
            new_metric_values_checked=54000,archived_metric_values_checked=54000,total_metric_comparisons=comparisons,max_f1_absolute_error=maximum,
            f1_absolute_bound=1e-15,em_exact=True,ledger_bytes_exact=True,selected_reference_binding_sha256=binding,source_counts=counts,
            arrow_observation=tracked.receipt(),shared_original_reference_reader=True,independent_metric_formulas=True,raw_reference_strings_written=False)
    except Exception as exc:result.update(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    try:io.finish(cfg,out,result,state,allowed,'INDEPENDENT_RESULT.json')
    except Exception as exc:
        result.update(status='FAIL_FINAL_BOUNDARY',finish_error=repr(exc));io.write(out/'INDEPENDENT_FAILURE.json',result)
    print(json.dumps({k:result[k] for k in ('status','traces','total_metric_comparisons','max_f1_absolute_error','error_type','error','finish_error') if k in result},indent=2))
    return 0 if result['status']=='PASS_FULL_HISTORICAL_REFERENCE_AND_OUTCOME_REPLAY' else 2


if __name__=='__main__':raise SystemExit(main())
