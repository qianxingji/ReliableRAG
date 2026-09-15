"""Observe every reachable HGB state value without fitting or scoring."""
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
    io=types.ModuleType('hgb_diagnostic_io');io.__file__=str(path);sys.modules[io.__name__]=io;exec(compile(path.read_bytes(),str(path),'exec'),io.__dict__)
    cfg,out,named,state,result=io.setup(a.config,a.config_sha256,'validator')
    try:
        import joblib
        import numpy as np
        io.assemble(named,result['selected_ast_nodes'])
        stats={};active=set()
        def encode(value,where):
            stats['visited_values']=stats.get('visited_values',0)+1
            if value is None or type(value) in (str,int,bool):return value
            if type(value) is float:return {'float_hex':value.hex()}
            if type(value) is bytes:return {'bytes_hex':value.hex()}
            if isinstance(value,(type,types.FunctionType,types.BuiltinFunctionType)):
                return dict(global_reference=value.__module__+'.'+value.__qualname__)
            if isinstance(value,np.generic):return dict(numpy_scalar_dtype=str(value.dtype),value=encode(value.item(),where+'/scalar'))
            if isinstance(value,np.dtype):return dict(dtype_str=value.str,descriptor=value.descr,itemsize=value.itemsize)
            if isinstance(value,np.ndarray):
                assert not value.dtype.hasobject,'OBJECT_ARRAY_STATE_UNSUPPORTED'
                stats['arrays']=stats.get('arrays',0)+1
                data=dict(kind='ndarray',shape=list(value.shape),dtype=encode(value.dtype,where+'/dtype'),raw_sha256=hashlib.sha256(value.tobytes(order='C')).hexdigest())
                if value.dtype.names:
                    data['fields']={n:encode(value[n],where+'/fields/'+n) for n in value.dtype.names}
                else:data['values']=[encode(v,where+'/values/'+str(i)) for i,v in enumerate(value.tolist() if value.ndim==1 else value.reshape(-1).tolist())]
                return data
            token=id(value);assert token not in active,('RECURSIVE_STATE_UNRESOLVED',where)
            active.add(token)
            try:
                if isinstance(value,dict):
                    assert all(type(k)is str for k in value),('NONSTRING_STATE_KEY',where)
                    return dict(kind='dict',key_order=list(value),values={k:encode(v,where+'/'+k) for k,v in sorted(value.items())})
                if type(value) in (tuple,list):return dict(kind=type(value).__name__,values=[encode(v,where+'/'+str(i)) for i,v in enumerate(value)])
                typ=type(value);identity=typ.__module__+'.'+typ.__qualname__
                assert typ.__module__.startswith(('src.','sklearn.','numpy.')),('UNSUPPORTED_STATE_OBJECT',identity,where)
                reduction=value.__reduce_ex__(4)
                assert isinstance(reduction,(str,tuple)),('UNSUPPORTED_PICKLE_REDUCTION',identity,where)
                if isinstance(reduction,tuple):
                    assert 2<=len(reduction)<=6
                    reduction=list(reduction)
                    if len(reduction)>3 and reduction[3] is not None:reduction[3]=list(reduction[3])
                    if len(reduction)>4 and reduction[4] is not None:reduction[4]=list(reduction[4])
                    reduction=tuple(reduction)
                stats['objects']=stats.get('objects',0)+1
                return dict(kind='object',class_name=identity,mechanism='__reduce_ex__(4)',state=encode(reduction,where+'/reduction'))
            finally:active.remove(token)
        originals=[]
        for label in ('original_model','new_model'):
            model=joblib.load(named[label]);stats={};observed=encode(model,label)
            io.write(out/(label+'_STATE_PRIVATE.json'),observed);originals.append(observed)
            result[label+'_observation']=dict(sha256=io.sha(named[label]),size_bytes=named[label].stat().st_size,**stats)
        differences=[]
        def compare(a,b,where):
            if type(a)is not type(b):differences.append(dict(path=where,kind='TYPE',original=str(type(a)),new=str(type(b))));return
            if isinstance(a,dict):
                if set(a)!=set(b):differences.append(dict(path=where,kind='KEYS',original=sorted(a),new=sorted(b)));return
                for k in a:compare(a[k],b[k],where+'/'+k)
            elif isinstance(a,(list,tuple)):
                if len(a)!=len(b):differences.append(dict(path=where,kind='LENGTH',original=len(a),new=len(b)));return
                for i,(left,right) in enumerate(zip(a,b)):compare(left,right,where+'/'+str(i))
            elif a!=b:differences.append(dict(path=where,kind='VALUE',original=a,new=b))
        compare(*originals,'state')
        io.write(out/'STATE_DIFFERENCES_PRIVATE.json',differences)
        old=named['original_model'].read_bytes();new=named['new_model'].read_bytes();positions=[i for i,(x,y) in enumerate(zip(old,new)) if x!=y]
        result.update(status='COMPLETE_READ_ONLY_HGB_STATE_DIAGNOSTIC',scientific_fits=0,score_calls=0,model_loads=2,
            state_difference_count=len(differences),state_difference_paths=[x['path'] for x in differences],
            raw_hash_only_difference_count=sum(x['path'].endswith('/raw_sha256') for x in differences),
            differing_byte_positions=len(positions)+abs(len(old)-len(new)),first_differing_byte_positions=positions[:64],
            original_failed_byte_gate_unchanged=True)
        assert len(state['model_load_calls'])==2 and not state['fit_calls'] and not state['nested_fit_calls']
    except Exception as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    io.finish(out,'DIAGNOSTIC_RESULT.json',result,state)
    print(json.dumps({k:result[k] for k in ('status','state_difference_count','raw_hash_only_difference_count','differing_byte_positions','error','state_difference_paths') if k in result},indent=2))
    return 0 if result['status']=='COMPLETE_READ_ONLY_HGB_STATE_DIAGNOSTIC' else 2


if __name__=='__main__':raise SystemExit(main())
