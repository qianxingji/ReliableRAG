"""Independent full membership/design/byte/score validation; no fitting."""
import argparse
import copy
import hashlib
import json
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
    io=types.ModuleType('training_validation_io');io.__file__=str(path);sys.modules[io.__name__]=io;exec(compile(path.read_bytes(),str(path),'exec'),io.__dict__)
    cfg,out,named,state,result=io.setup(a.config,a.config_sha256,'validator')
    try:
        import joblib
        import numpy as np
        from threadpoolctl import threadpool_limits
        assert io.sha(a.producer_inputs)==a.producer_inputs_sha256
        for e in io.load(a.producer_inputs)['files']:
            q=out/e['path'];assert q.is_relative_to(out) and io.sha(q)==e['sha256'] and q.stat().st_size==e['size_bytes']
        producer=io.load(out/'PRODUCER_RESULT.json');assert producer['status']=='COMPLETE_SEVEN_FITS_PENDING_INDEPENDENT'
        sym,full=io.assemble(named,result['selected_ast_nodes']);assert result['selected_ast_nodes']==producer['selected_ast_nodes']
        # Separate join, selection and matrix construction; no producer helper/native matrix call.
        pairs=[json.loads(line) for line in named['pairs'].read_text(encoding='utf-8').splitlines()]
        labels=[json.loads(line) for line in named['labels'].read_text(encoding='utf-8').splitlines()]
        def key(row):return tuple(str(row[k]) for k in ('dataset','split','sample_id','retriever'))
        assert len(pairs)==len({key(x) for x in pairs})==1539 and len(labels)==len({key(x) for x in labels})==7200
        by={key(x):x for x in labels};assert set(key(x) for x in pairs).issubset(by)
        selected=[];targets=[]
        for row in pairs:
            value=by[key(row)]['preference_label']
            if value in (0,1):selected.append(row);targets.append(int(value))
        assert len(selected)==601 and len({(x['dataset'],x['sample_id']) for x in selected})==518
        assert len({(x['dataset'],x['sample_id']) for x in labels})==4800 and set(targets)=={0,1}
        manifest=io.load(named['models_manifest']);assert list(manifest)==list(full.MODEL_SPECS)==cfg['model_order']
        rebuilt=dict(ids=[list(key(x)) for x in selected],labels=targets,records_sha256=io.jsha(selected),designs={})
        for name,meta in manifest.items():
            names=meta['feature_names'];assert names==list(full.MODEL_SPECS[name][2])
            values=[]
            for row in selected:
                source={**row['diagnostics'],**row['invariant_features'],**row['features']} if name=='ordinary_compact_logistic' else row['features']
                values.append([float(source[field]) for field in names])
            array=np.array(values,dtype=np.float64);assert array.shape==(601,len(names)) and np.isfinite(array).all()
            rebuilt['designs'][name]=dict(feature_names=names,shape=list(array.shape),dtype=str(array.dtype),values=values,bytes_sha256=hashlib.sha256(array.tobytes(order='C')).hexdigest())
        witness=io.load(out/'TRAINING_INPUTS_PRIVATE.json')
        def equal_input(candidate):assert candidate==rebuilt,'TRAINING_INPUT_MISMATCH'
        equal_input(witness)
        negative=[]
        bad=copy.deepcopy(witness);bad['ids'][0],bad['ids'][1]=bad['ids'][1],bad['ids'][0]
        for label,b in [('reordered_rows',bad),('changed_design',copy.deepcopy(witness))]:
            if label=='changed_design':b['designs'][cfg['model_order'][0]]['values'][0][0]+=1.0
            try:equal_input(b)
            except AssertionError:negative.append(dict(case=label,rejected=True))
            else:raise AssertionError('COUNTERFEIT_ACCEPTED')
        assert len(producer['fit_calls'])==7 and not producer['blocked_events'] and not producer['forbidden_calls']
        summaries={};mismatches=[];max_error=0.0;checks=0
        with threadpool_limits(limits=1):
            for i,name in enumerate(manifest):
                event=producer['fit_calls'][i]
                assert event['index']==i and event['name']==name and event['seed']==20261829+i and event['rows']==601 and event['completed']
                assert event['records_sha256']==io.jsha(selected) and event['labels_sha256']==io.jsha(targets)
                old=named['model_'+name];new=out/'models'/(name+'.joblib')
                assert io.sha(old)==manifest[name]['sha256']==producer['models'][name]['original_sha256']
                assert io.sha(new)==producer['models'][name]['new_sha256']
                old_model=joblib.load(old);new_model=joblib.load(new)
                old_scores=np.asarray(old_model.scores(pairs),dtype=np.float64);new_scores=np.asarray(new_model.scores(pairs),dtype=np.float64)
                reported=np.asarray(producer['models'][name]['scores'],dtype=np.float64)
                assert old_scores.shape==new_scores.shape==reported.shape==(1539,) and np.isfinite(old_scores).all() and np.isfinite(new_scores).all() and np.isfinite(reported).all()
                error=float(np.max(np.abs(old_scores-new_scores)));report_error=float(np.max(np.abs(new_scores-reported)))
                max_error=max(max_error,error,report_error);checks+=len(old_scores)
                same=io.sha(old)==io.sha(new)
                summaries[name]=dict(original_sha256=io.sha(old),new_sha256=io.sha(new),byte_identical=same,score_checks=1539,max_score_error=error,max_producer_score_error=report_error)
                if not same:mismatches.append(dict(model=name,kind='MODEL_BYTES'))
                if error>1e-12 or report_error>1e-12:mismatches.append(dict(model=name,kind='NUMERIC',error=error,producer_error=report_error))
        first=out/'models'/(cfg['model_order'][0]+'.joblib');original=first.read_bytes();altered=bytes([original[0]^1])+original[1:]
        assert hashlib.sha256(altered).hexdigest()!=io.sha(first);negative.append(dict(case='changed_model_bytes',rejected=True))
        assert not state['fit_calls'] and not state['nested_fit_calls'] and len(state['model_load_calls'])==14
        io.write(out/'MISMATCHES_PRIVATE.json',mismatches)
        result.update(status='PASS_SEVEN_ORIGINAL_FINAL_FITS_BYTES_AND_SCORES' if not mismatches else 'FAIL_SEVEN_MODEL_REPLAY_MISMATCH',
            scientific_fits=0,validated_fit_attempts=7,validated_fit_completions=7,training_trace_rows=601,training_questions=518,
            historical_development_label_records=7200,training_matrices=7,training_matrix_scalar_values=sum(np.prod(d['shape']).item() for d in rebuilt['designs'].values()),
            model_byte_matches=sum(x['byte_identical'] for x in summaries.values()),score_comparisons=checks,
            producer_score_comparisons=checks,max_score_error=max_error,model_results=summaries,negative_checks=negative,mismatches=len(mismatches))
    except Exception as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    io.finish(out,'INDEPENDENT_RESULT.json',result,state)
    print(json.dumps({k:result[k] for k in ('status','model_byte_matches','score_comparisons','max_score_error','error') if k in result},indent=2))
    return 0 if result['status']=='PASS_SEVEN_ORIGINAL_FINAL_FITS_BYTES_AND_SCORES' else 2


if __name__=='__main__':raise SystemExit(main())
