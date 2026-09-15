"""Source-only historical estimator assembly and exact fit-input receipts."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import site
import sys
import types


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def jsha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def module(name,path):
    m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m


def setup(config,pin,role):
    assert sha(config)==pin;cfg=load(config);out=config.parent.resolve();env=Path(cfg['environment']).resolve()
    assert Path(sys.prefix).resolve()==env and site.ENABLE_USER_SITE is False and sys.flags.isolated and sys.dont_write_bytecode
    assert os.environ['CUDA_VISIBLE_DEVICES']=='-1' and os.environ['OMP_NUM_THREADS']=='1'
    controls={e['name']:e for e in cfg['controls']}
    for e in controls.values():assert sha(Path(e['path']))==e['sha256'] and Path(e['path']).stat().st_size==e['size_bytes']
    inputs={k:Path(e['path']) for k,e in cfg['named_inputs'].items()}
    for k,p in inputs.items():assert sha(p)==cfg['named_inputs'][k]['sha256'] and p.stat().st_size==cfg['named_inputs'][k]['size_bytes']
    guard=module('historical_final_fit_guard',Path(controls['guard']['path']))
    state,bootstrap,allowed=guard.install(env,out,list(inputs.values())+[Path(e['path']) for e in controls.values()]+[config],role)
    result=dict(status='FAIL',role=role,config_sha256=pin,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        selected_ast_nodes=[],fresh_gold_values=0,historical_test_gold_values=0,neural_forwards=0,
        original_fit_time_receipts_recovered=False,original_full_cli_replayed=False)
    result['platform_bootstrap']=bootstrap()
    return cfg,out,inputs,state,result


def assemble(named,records):
    import numpy as np
    from dataclasses import dataclass
    from typing import Any
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    for name in ('src','src.mars'):
        m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
    def take(name,path,names,extra=None):
        m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
        m.__dict__.update(np=np,dataclass=dataclass,Any=Any,StandardScaler=StandardScaler,
            HistGradientBoostingClassifier=HistGradientBoostingClassifier,LogisticRegression=LogisticRegression,make_pipeline=make_pipeline)
        if extra:m.__dict__.update(extra)
        nodes=[]
        for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
            n=getattr(node,'name',None)
            if isinstance(node,ast.Assign) and len(node.targets)==1:n=getattr(node.targets[0],'id',None)
            if n in names:
                nodes.append(node);records.append(dict(path=str(path),name=n,ast_sha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()))
        assert len(nodes)==len(names)
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        tree=ast.fix_missing_locations(ast.Module(body=[future]+nodes,type_ignores=[]))
        exec(compile(tree,str(path),'exec'),m.__dict__);return m
    sym=take('src.mars.state_symmetric',named['symmetric_source'],{'PHI_NAMES','DELTA_NAMES','INTERACTION_BASES','SYMMETRIC_FEATURE_NAMES',
        'NO_CROSS_FEATURE_NAMES','matrix','SymmetricSelector','fit_symmetric_selector'})
    full=take('src.mars.full_experiment',named['full_source'],{'_key','ORDINARY_NAMES','_ordinary_matrix','OrdinarySelector','_fit_ordinary','MODEL_SPECS','_fit_model'},
        {k:getattr(sym,k) for k in ('DELTA_NAMES','NO_CROSS_FEATURE_NAMES','SYMMETRIC_FEATURE_NAMES','fit_symmetric_selector')})
    return sym,full


def training_rows(named,full):
    pairs=[json.loads(x) for x in named['pairs'].read_text(encoding='utf-8').splitlines()]
    labels=[json.loads(x) for x in named['labels'].read_text(encoding='utf-8').splitlines()]
    assert len(pairs)==1539 and len(labels)==7200
    assert len({full._key(x) for x in pairs})==1539 and len({full._key(x) for x in labels})==7200
    by={full._key(x):x for x in labels};assert all(full._key(x) in by for x in pairs)
    selected=[x for x in pairs if by[full._key(x)]['preference_label'] in (0,1)]
    targets=[int(by[full._key(x)]['preference_label']) for x in selected]
    assert len(selected)==601 and len({(x['dataset'],x['sample_id']) for x in selected})==518
    assert len({(x['dataset'],x['sample_id']) for x in labels})==4800 and set(targets)=={0,1}
    return pairs,selected,targets


def finish(out,name,result,state):
    result.update(fit_calls=state['fit_calls'],nested_fit_calls=state['nested_fit_calls'],model_load_calls=state['model_load_calls'],
        blocked_events=state['blocked'],forbidden_calls=state['forbidden_calls'],opened_paths=sorted(state['opened']),
        bootstrap_events=state['bootstrap_events'],optional_import_refusals=state['optional_import_refusals'],
        finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if state['blocked'] or state['forbidden_calls']:result['status']='FAIL_BOUNDARY'
    result['core_packages']={k:dict(path=str(Path(sys.modules[k].__file__).resolve()),version=sys.modules[k].__version__)
        for k in ('numpy','scipy','sklearn','joblib')}
    write(out/name,result)

