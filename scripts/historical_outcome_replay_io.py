"""Frozen original reference/metric assembly and bounded historical-only IO."""
import ast
from collections import Counter,defaultdict
from collections.abc import Sequence
import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import site
import string
import sys
import types


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def require(value,message):
    if not value:raise RuntimeError(message)
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def module(name,path):
    m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m


def setup(config,pin,role):
    require(sha(config)==pin,'CONFIG_PIN');cfg=load(config);out=config.parent.resolve();env=Path(cfg['environment']).resolve()
    require(Path(sys.prefix).resolve()==env and sys.flags.isolated and sys.dont_write_bytecode and site.ENABLE_USER_SITE is False,'ISOLATED_ENVIRONMENT')
    require(os.environ['CUDA_VISIBLE_DEVICES']=='-1' and os.environ['OMP_NUM_THREADS']=='1','CPU_ONLY_SINGLE_THREAD')
    controls={e['name']:e for e in cfg['controls']}
    for e in controls.values():require(sha(e['path'])==e['sha256'] and Path(e['path']).stat().st_size==e['size_bytes'],'CONTROL_HASH')
    named={k:Path(e['path']).resolve() for k,e in cfg['named_inputs'].items()}
    for k,p in named.items():require(sha(p)==cfg['named_inputs'][k]['sha256'] and p.stat().st_size==cfg['named_inputs'][k]['size_bytes'],'INPUT_HASH')
    guard=module('historical_outcome_boundary',Path(controls['guard']['path']))
    state,bootstrap,allowed=guard.install(env,out,list(named.values())+[Path(e['path']) for e in controls.values()]+[config],
        hash_only=[named['archived_outcomes']] if role=='producer' else [],opaque_code=sha.__code__)
    result=dict(status='FAIL',role=role,config_sha256=pin,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scientific_fits=0,neural_forwards=0,current_empirical_gold_python_values=0,current_empirical_payload_reads=0,source_ast_nodes=[])
    result['platform_bootstrap']=bootstrap()
    selected=set();fresh=set()
    for name,destination,count,per_dataset in (('historical_ids',selected,4500,1500),('current_ids',fresh,6000,2000)):
        rows=[json.loads(x) for x in named[name].read_text(encoding='utf-8').splitlines()]
        require(len(rows)==count,'COHORT_ROW_COUNT')
        for row in rows:
            k=(row['dataset'],row['sample_id']);require(all(type(x)is str for x in k) and k not in destination,'COHORT_ID_SCHEMA');destination.add(k)
        require(Counter(k[0] for k in destination)=={d:per_dataset for d in ('hotpotqa','2wikimultihopqa','musique')},'COHORT_STRATA')
    require(not selected.intersection(fresh),'HISTORICAL_CURRENT_OVERLAP')
    result['id_boundary']=dict(historical_questions=4500,current_questions=6000,overlap=0,verified_before_reference_decode=True)
    print('HISTORICAL_CURRENT_ID_OVERLAP',0,flush=True)
    return cfg,out,named,controls,state,allowed,selected,result


def assemble(cfg,named,result):
    def take(name,path,names,extra=None):
        m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
        m.__dict__.update(json=json,io=io,Path=Path,require=require,sha=sha,hashlib=hashlib,re=re,string=string,Counter=Counter,defaultdict=defaultdict,
            Sequence=Sequence,Phase10FailClosed=RuntimeError,_SPECIAL_ANSWERS={'yes','no','noanswer'},math=math)
        if extra:m.__dict__.update(extra)
        nodes=[]
        for n in ast.parse(path.read_text(encoding='utf-8-sig')).body:
            k=getattr(n,'name',None)
            if isinstance(n,ast.Assign) and len(n.targets)==1:k=getattr(n.targets[0],'id',None)
            if k in names:
                nodes.append(n);result['source_ast_nodes'].append(dict(path=str(path),name=k,ast_sha256=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()))
        require(len(nodes)==len(names),'EXACT_ORIGINAL_AST_SELECTION')
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future]+nodes,type_ignores=[])),str(path),'exec'),m.__dict__);return m
    spec=load(named['mapping_spec']);provenance=load(named['mapping_provenance'])
    require(spec['status']==provenance['status']=='PASS','ORIGINAL_OUTCOME_METADATA')
    require(spec['canonical_branches']['sha256']==sha(named['branches']) and spec['selected_ids']['sha256']==sha(named['historical_ids']),'ORIGINAL_BRANCH_ID_PINS')
    for dataset,e in spec['sources'].items():require(sha(named['source_'+dataset])==e['sha256'] and named['source_'+dataset].stat().st_size==e['size_bytes'],'SOURCE_SPEC_PIN')
    serialization=take('original_outcome_serialization',named['control_source'],{'canonical','jsha'})
    readers=take('original_selected_reference_readers',named['reader_source'],{'read_object','json_references','parquet_references','load_references'},dict(ROOT=Path(cfg['restored_original_root'])))
    cursor=take('original_reference_cursor',named['cursor_source'],{'_JSONByteCursor'})._JSONByteCursor
    metric=take('original_answer_metrics',named['metric_source'],set(spec['metric_ast_hashes']))
    actual={e['name']:e['ast_sha256'] for e in result['source_ast_nodes'] if e['path']==str(named['metric_source'])}
    require(actual==spec['metric_ast_hashes'],'ORIGINAL_METRIC_AST_PINS')
    projected=take('frozen_canonical_answer_projection',named['answer_projection'],{'canonical_answer_rows'})
    independent=take('frozen_independent_metric_formulas',named['independent_metric_source'],{'normalize','metrics'})
    result['original_selected_reference_binding']=provenance['selected_reference_binding_sha256']
    return spec,provenance,serialization,readers,cursor,metric,projected,independent


def arrow(cfg,controls,result):
    target=Path(cfg['arrow_target']).resolve();require(target==Path('E:/paper/ReliableRAG-neural-targets-v1/pyarrow').resolve(),'EXACT_NEW_ARROW_TARGET')
    sys.path.insert(0,str(target))
    import pyarrow as pa
    import pyarrow.parquet as pq
    require(pa.__version__=='20.0.0' and Path(pa.__file__).resolve().is_relative_to(target),'ACTUAL_NEW_ARROW_IMPORT')
    paths={name:str(Path(sys.modules[name].__file__).resolve()) for name in ('pyarrow','pyarrow.lib','pyarrow._parquet','pyarrow.parquet')}
    require(all(Path(p).is_relative_to(target) for p in paths.values()),'ARROW_MODULE_TARGET_OWNERSHIP')
    result['arrow']=dict(version=pa.__version__,module_paths=paths)
    observer=module('historical_selected_arrow_observer',Path(controls['arrow_observer']['path']))
    return pa,pq,observer


def fixtures(pa,pq,observer,readers,Cursor,metric,independent,out):
    checks=[]
    for lines in (False,True):
        values=[{'answer':{'malformed':'must be skipped'},'_id':'unselected'}, {'answer':'The blue','answer_aliases':['blue'],'_id':'keep'}]
        data=('\n'.join(json.dumps(x) for x in values) if lines else json.dumps(values)).encode()
        refs,counts=readers.json_references(lambda:io.BytesIO(data),{'keep'},id_field='_id',json_lines=lines,aliases=True,Cursor=Cursor)
        require(refs=={'keep':['The blue','blue']} and counts['unselected_reference_python_values_materialized']==0,'INVENTED_JSON_SELECTION')
        try:readers.json_references(lambda:io.BytesIO(data),{'missing'},id_field='_id',json_lines=lines,aliases=True,Cursor=Cursor)
        except RuntimeError as exc:require(str(exc)=='SOURCE_SELECTED_ID_COVERAGE','MISSING_ID_REASON')
        else:raise AssertionError('MISSING_ID_ACCEPTED')
        checks.append(dict(case='jsonl_selection' if lines else 'json_selection',passed=True,missing_id_rejected=True))
    fixture=out/('PARQUET_FIXTURE_'+result_role(out)+'.parquet')
    table=pa.table({'id':['keep','unselected'],'answer':['The blue',None],'question':['unused','unused'],'supporting_facts':['unused','unused']})
    with fixture.open('xb') as f:pq.write_table(table,f,row_group_size=2)
    tracked=observer.ObservedParquet(pq,{'keep'},{fixture})
    refs,counts=readers.parquet_references(fixture,{'keep'},tracked)
    require(refs=={'keep':['The blue']} and tracked.python_answer_scalars==1,'INVENTED_PARQUET_SELECTION')
    with fixture.open('rb') as f:
        pf=tracked.ParquetFile(f);pf.read_row_group(0,columns=['id'],use_threads=False,use_pandas_metadata=False).column('id').to_pylist()
        answers=pf.read_row_group(0,columns=['answer'],use_threads=False,use_pandas_metadata=False).column('answer')
        for label,call in [('unselected_scalar',lambda:answers[1]),('whole_answer_column',lambda:answers.to_pylist()),
            ('forbidden_column',lambda:pf.read_row_group(0,columns=['question'],use_threads=False,use_pandas_metadata=False))]:
            try:call()
            except RuntimeError:checks.append(dict(case=label,rejected=True))
            else:raise AssertionError('FORBIDDEN_ARROW_FIXTURE_ACCEPTED')
    bad=observer.ObservedParquet(pq,{'unselected'},{fixture})
    try:readers.parquet_references(fixture,{'unselected'},bad)
    except RuntimeError as exc:require(str(exc)=='PARQUET_ANSWER_SHAPE','INVALID_SELECTED_REASON')
    else:raise AssertionError('INVALID_SELECTED_ANSWER_ACCEPTED')
    checks.append(dict(case='invalid_selected_answer',rejected=True))
    for answer,refs in [('blue',['The blue','red']),('yes',['no']),('', ['']),('the blue blue',['blue'])]:
        expected=independent.metrics(answer,refs)
        require((int(metric.exact_match(answer,refs)),float(metric.token_f1(answer,refs)))==expected,'INVENTED_METRIC_AGREEMENT')
    checks.append(dict(case='four_metric_cases',passed=True))
    return checks


def result_role(out):
    # Separate producer/validator fixture paths without mutable global state.
    return 'validator' if (out/'PRODUCER_RESULT.json').exists() else 'producer'


def finish(cfg,out,result,state,allowed,filename):
    import psutil
    expected={Path(e['path']).resolve():e for e in cfg['arrow_binary_files']};binary=[]
    for p in sorted({Path(m.path).resolve() for m in psutil.Process().memory_maps(grouped=False) if m.path and Path(m.path).suffix.lower() in {'.pyd','.dll','.exe'}}):
        require(allowed(p),'BINARY_OUTSIDE_ALLOWED_ROOTS')
        if p.is_relative_to(Path(cfg['arrow_target']).resolve()):
            require(p in expected and sha(p)==expected[p]['sha256'] and p.stat().st_size==expected[p]['size_bytes'],'MAPPED_ARROW_BINARY_PIN')
            binary.append(expected[p])
    require(any(Path(e['path']).name=='_parquet.cp310-win_amd64.pyd' for e in binary),'ACTUAL_PARQUET_BINARY')
    result.update(arrow_mapped_binaries=binary,blocked_events=state['blocked'],forbidden_calls=state['forbidden_calls'],opened_paths=sorted(state['opened']),
        model_load_calls=state['model_load_calls'],bootstrap_events=state['bootstrap_events'],finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    require(not any(n.split('.')[0] in {'torch','transformers','pandas','sklearn','joblib','datasets'} for n in sys.modules),'FORBIDDEN_PACKAGE_LOADED')
    if state['blocked'] or state['forbidden_calls']:result['status']='FAIL_BOUNDARY'
    write(out/filename,result)
