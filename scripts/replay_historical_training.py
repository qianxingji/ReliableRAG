"""Re-execute only the seven original final fits, retaining exact byte outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback
import types


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--config-sha256',required=True);a=p.parse_args()
    assert hashlib.sha256(a.config.read_bytes()).hexdigest()==a.config_sha256
    cfg=json.loads(a.config.read_text());entry=next(e for e in cfg['controls'] if e['name']=='io');path=Path(entry['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    io=types.ModuleType('training_replay_io');io.__file__=str(path);sys.modules[io.__name__]=io;exec(compile(path.read_bytes(),str(path),'exec'),io.__dict__)
    cfg,out,named,state,result=io.setup(a.config,a.config_sha256,'producer')
    try:
        import joblib
        import numpy as np
        import yaml
        from threadpoolctl import threadpool_limits
        sym,full=io.assemble(named,result['selected_ast_nodes'])
        original_config=yaml.safe_load(named['config'].read_text(encoding='utf-8'))
        assert original_config['seed']==20260829 and {k:original_config['models'][k] for k in ('logistic_max_iter','hgb_max_iter','hgb_max_leaf_nodes')}==dict(logistic_max_iter=4000,hgb_max_iter=300,hgb_max_leaf_nodes=15)
        manifest=io.load(named['models_manifest']);assert list(full.MODEL_SPECS)==list(manifest)==cfg['model_order']
        pairs,selected,targets=io.training_rows(named,full)
        training=dict(ids=[list(full._key(x)) for x in selected],labels=targets,records_sha256=io.jsha(selected),designs={})
        for name,spec in full.MODEL_SPECS.items():
            names=list(spec[2]);assert names==manifest[name]['feature_names']
            x=full._ordinary_matrix(selected) if spec[0]=='ordinary' else sym.matrix(selected,tuple(names))
            assert x.shape==(601,len(names)) and x.dtype==np.float64 and np.isfinite(x).all()
            training['designs'][name]=dict(feature_names=names,shape=list(x.shape),dtype=str(x.dtype),values=x.tolist(),bytes_sha256=hashlib.sha256(x.tobytes(order='C')).hexdigest())
        io.write(out/'TRAINING_INPUTS_PRIVATE.json',training)
        (out/'models').mkdir();results={}
        with threadpool_limits(limits=1):
            for i,name in enumerate(full.MODEL_SPECS):
                fitted=full._fit_model(name,selected,targets,original_config,int(original_config['seed'])+1000+i)
                destination=out/'models'/(name+'.joblib');joblib.dump(fitted,destination,compress=0)
                score=fitted.scores(pairs);assert score.shape==(1539,) and np.isfinite(score).all()
                results[name]=dict(index=i,seed=20261829+i,original_sha256=io.sha(named['model_'+name]),
                    new_sha256=io.sha(destination),byte_identical=io.sha(destination)==io.sha(named['model_'+name]),scores=score.tolist())
                io.write(out/(name+'_FIT_RESULT.json'),results[name]);print('HISTORICAL_FIT',i+1,7,name,results[name]['byte_identical'],flush=True)
        assert len(state['fit_calls'])==7 and all(x['completed'] for x in state['fit_calls'])
        result.update(status='COMPLETE_SEVEN_FITS_PENDING_INDEPENDENT',scientific_fit_attempts=7,scientific_fit_completions=7,
            training_trace_rows=601,training_questions=518,development_feature_pairs=1539,models=results,
            historical_development_label_records=7200,model_byte_matches=sum(x['byte_identical'] for x in results.values()))
    except Exception as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    io.finish(out,'PRODUCER_RESULT.json',result,state)
    print(json.dumps({k:result[k] for k in ('status','scientific_fit_attempts','scientific_fit_completions','model_byte_matches','error') if k in result},indent=2))
    return 0 if result['status']=='COMPLETE_SEVEN_FITS_PENDING_INDEPENDENT' else 2


if __name__=='__main__':raise SystemExit(main())
