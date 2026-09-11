"""Full original selected-source mapping into a new historical numeric ledger."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import types


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--config-sha256',required=True);a=p.parse_args()
    assert hashlib.sha256(a.config.read_bytes()).hexdigest()==a.config_sha256
    cfg=json.loads(a.config.read_text());entry=next(e for e in cfg['controls'] if e['name']=='io');path=Path(entry['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    io=types.ModuleType('historical_outcome_producer_io');io.__file__=str(path);sys.modules[io.__name__]=io;exec(compile(path.read_bytes(),str(path),'exec'),io.__dict__)
    cfg,out,named,controls,state,allowed,selected,result=io.setup(a.config,a.config_sha256,'producer')
    try:
        spec,provenance,serialization,readers,Cursor,metric,projected,independent=io.assemble(cfg,named,result)
        pa,pq,observer=io.arrow(cfg,controls,result)
        result['fixtures']=io.fixtures(pa,pq,observer,readers,Cursor,metric,independent,out)
        wanted={sid for ds,sid in selected if ds=='hotpotqa'}
        tracked=observer.ObservedParquet(pq,wanted,{named['source_hotpotqa']})
        references,counts=readers.load_references(spec,selected,Cursor,tracked)
        binding=serialization.jsha([[ds,sid,references[(ds,sid)]] for ds,sid in sorted(references)])
        io.require(binding==provenance['selected_reference_binding_sha256'],'ORIGINAL_REFERENCE_BINDING')
        io.require(counts==provenance['source_counts'],'ORIGINAL_READER_COUNTS')
        io.require(tracked.identifiers==7405 and tracked.python_answer_scalars==1500 and not tracked.denied,'EXACT_SELECTED_ARROW_CONVERSION')
        print('HISTORICAL_REFERENCE_BINDING_PASS',4500,flush=True)
        seen=set();strata=Counter();questions=Counter();destination=out/'NUMERIC_OUTCOMES_PRIVATE.jsonl'
        with destination.open('xb') as f:
            for row in projected.canonical_answer_rows(named['branches'],Cursor):
                k=(row['dataset'],row['retriever'],row['sample_id']);q=(k[0],k[2])
                io.require(k not in seen and q in selected and k[1] in ('bm25','dense','hybrid'),'HISTORICAL_BRANCH_IDENTITY')
                seen.add(k);strata[k[:2]]+=1;questions[q]+=1
                values=dict(dataset=k[0],retriever=k[1],sample_id=k[2])
                for side in ('a0','a1'):
                    values[side+'_em']=int(metric.exact_match(row[side],references[q]))
                    values[side+'_f1']=float(metric.token_f1(row[side],references[q]))
                f.write(serialization.canonical(values)+b'\n')
                if len(seen)%1500==0:print('HISTORICAL_OUTCOME_ROWS',len(seen),13500,flush=True)
            f.flush();os.fsync(f.fileno())
        io.require(len(seen)==13500 and set(questions)==selected and set(questions.values())=={3},'COMPLETE_HISTORICAL_UNIVERSE')
        io.require(strata=={(d,r):1500 for d in ('hotpotqa','2wikimultihopqa','musique') for r in ('bm25','dense','hybrid')},'NINE_COMPLETE_STRATA')
        io.require(io.sha(destination)==io.sha(named['archived_outcomes'])=='2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576','EXACT_ORIGINAL_OUTCOME_BYTES')
        result.update(status='PASS_FULL_HISTORICAL_SOURCE_MAPPING_PENDING_INDEPENDENT',historical_questions=4500,traces=13500,
            metric_values=54000,source_counts=counts,selected_reference_binding_sha256=binding,numeric_ledger_sha256=io.sha(destination),
            raw_reference_strings_written=False,archived_numeric_values_used_to_construct_outputs=False,arrow_observation=tracked.receipt())
    except Exception as exc:result.update(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    try:io.finish(cfg,out,result,state,allowed,'PRODUCER_RESULT.json')
    except Exception as exc:
        result.update(status='FAIL_FINAL_BOUNDARY',finish_error=repr(exc));io.write(out/'PRODUCER_FAILURE.json',result)
    print(json.dumps({k:result[k] for k in ('status','traces','metric_values','error_type','error','finish_error') if k in result},indent=2))
    return 0 if result['status']=='PASS_FULL_HISTORICAL_SOURCE_MAPPING_PENDING_INDEPENDENT' else 2


if __name__=='__main__':raise SystemExit(main())
