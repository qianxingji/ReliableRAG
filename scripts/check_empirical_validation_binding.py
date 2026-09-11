"""Invented-only equivalence and finalization checks for the C3 execution adapter."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import site
import sys
import time
import traceback
import types


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--config-sha256',required=True)
    args=parser.parse_args();data=args.config.read_bytes()
    assert hashlib.sha256(data).hexdigest()==args.config_sha256
    cfg=json.loads(data);out=args.config.parent.resolve();repo=Path(cfg['engineering_root']).resolve();root=Path(cfg['project_root']).resolve()
    assert Path(sys.prefix).resolve()==root/'.venv' and sys.flags.isolated and sys.dont_write_bytecode and site.ENABLE_USER_SITE is False
    assert os.environ['CUDA_VISIBLE_DEVICES']=='-1' and os.environ['OMP_NUM_THREADS']=='1'
    controls={e['name']:e for e in cfg['controls']}
    for e in cfg['controls']+cfg['inputs']:
        p=Path(e['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'] and p.stat().st_size==e['size_bytes']
    sys.path.insert(0,str(repo))
    from scripts import validate_roa_empirical_runtime as native
    from scripts.empirical_runtime_guard import guard
    from scripts.empirical_retrieval_io import configure_environment, boundary_record
    from scripts.empirical_pool_io import verify_namespace
    from scripts.empirical_validation_length import FixedTokenizerLength, canonical_hash, CARDINALITY
    from scripts.empirical_validation_binding import ValidationBindings, helper_asts
    from scripts.validate_roa_empirical_runtime_bound import profile_execution
    configure_environment(out);platform.uname()._asdict()
    events=[];profile_execution(events)
    from transformers import AutoTokenizer
    boundary=guard(root,out,[Path(e['path']) for e in cfg['controls']+cfg['inputs']]+[args.config],gpu_only=True,tokenizer_only=True)
    result=dict(status='FAIL',scope='INVENTED_ONLY_NO_CURRENT_RUNTIME_VALIDATION',source_commit=cfg['source_commit'],
        config_sha256=args.config_sha256,current_runtime_payloads_read=0,fresh_gold_values=0,neural_forwards=0,scientific_fits=0)
    try:
        helper=root/'outputs/daa_v2_fresh_v1/runtime_branch_freeze/independent_validate.py'
        assert helper_asts(helper)==cfg['original_helper_asts']
        tokenizer=AutoTokenizer.from_pretrained(cfg['tokenizer_snapshot'],local_files_only=True,trust_remote_code=False)
        baseline=FixedTokenizerLength(cfg['tokenizer_source']);baseline.bind(tokenizer)
        functions=native.load_independent_functions(root)
        evidence=[dict(rank=i,document_id='invented-'+str(i),title='Invented title '+str(i),text='The blue marker is in the invented box.') for i in range(1,6)]
        question='Where is the invented blue marker?'
        templates=dict(answer='Answer the invented question: {question}\n{evidence}',repair_query='Provide Search Query: for {question}\n{evidence}')
        config=dict(runtime_config_sha256='f'*64)
        trace=dict(dataset='invented',retriever='bm25',sample_id='fixture',position=0)
        rendered=functions['render'](evidence)
        cases=[]
        for stage,text in [('a0',''),('a1','Answer: blue'),('repair_query','Search Query: blue marker')]:
            prompt=tokenizer.apply_chat_template([dict(role='user',content=templates['repair_query' if stage=='repair_query' else 'answer'].format(question=question,evidence=rendered['text']))],tokenize=False,add_generation_prompt=True)
            tokens=tokenizer([prompt],truncation=False);ids=tokenizer.encode(text,add_special_tokens=False)+[tokenizer.eos_token_id]
            raw=tokenizer.batch_decode([ids],skip_special_tokens=True)[0].strip()
            parsed,fallback=functions['parsed_query'](raw,question) if stage=='repair_query' else (functions['parsed_answer'](raw),None)
            count=0
            for token in ids:
                if token==tokenizer.pad_token_id:break
                count+=1
            receipt=dict(trace,stage=stage,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),input_token_ids=tokens['input_ids'][0],
                attention_mask=tokens['attention_mask'][0],generated_token_ids=ids,raw_text=raw,input_tokens=sum(tokens['attention_mask'][0]),
                output_tokens=count,native_output_score_steps=len(ids),render=rendered,parsed_text=parsed,parser_fallback=fallback,
                logical_generation_calls=1,qwen_forward_calls=len(ids),runtime_config_sha256=config['runtime_config_sha256'])
            cases.append((stage,receipt))

        def invocation(function,stage,receipt,active_tokenizer=tokenizer):
            try:
                value=function(receipt,trace,stage,evidence,question,active_tokenizer,templates,config)
                return dict(status='PASS',return_value=value)
            except Exception as exc:
                return dict(status='REJECTED',error_type=type(exc).__name__,reason=str(exc))

        equivalence=[]
        for stage,receipt in cases:
            plain=native.load_independent_functions(root)['validate_generation']
            active=native.load_independent_functions(root)['validate_generation'];length=FixedTokenizerLength(cfg['tokenizer_source'])
            bound=length.wrap_generation(active)
            left=invocation(plain,stage,receipt);right=invocation(bound,stage,receipt)
            assert left==right==dict(status='PASS',return_value=None)
            length.finish(1);equivalence.append(dict(case=stage,ordinary=left,bound=right))
        original=cases[0][1]
        faults={
            'prompt':lambda r:r.update(prompt_sha256='0'*64),
            'input_ids':lambda r:r['input_token_ids'].__setitem__(0,r['input_token_ids'][0]+1),
            'attention_mask':lambda r:r['attention_mask'].__setitem__(0,0),
            'out_of_vocabulary':lambda r:r.update(generated_token_ids=[CARDINALITY]),
            'negative_generated_id':lambda r:r.update(generated_token_ids=[-1]),
            'bool_generated_id':lambda r:r.update(generated_token_ids=[True]),
            'empty_generated_ids':lambda r:r.update(generated_token_ids=[]),
            'over_budget':lambda r:r.update(generated_token_ids=[tokenizer.eos_token_id]*49),
            'wrong_stop':lambda r:r.update(generated_token_ids=[0]),
            'wrong_decode':lambda r:r.update(raw_text='invented corruption'),
            'wrong_counters':lambda r:r.update(logical_generation_calls=2),
            'wrong_render':lambda r:r['render'].update(text='invented corruption'),
            'wrong_config':lambda r:r.update(runtime_config_sha256='0'*64)}
        for label,change in faults.items():
            bad=copy.deepcopy(original);change(bad)
            plain=native.load_independent_functions(root)['validate_generation']
            length=FixedTokenizerLength(cfg['tokenizer_source']);bound=length.wrap_generation(native.load_independent_functions(root)['validate_generation'])
            left=invocation(plain,'a0',bad);right=invocation(bound,'a0',bad)
            assert left==right and left['status']=='REJECTED',label
            equivalence.append(dict(case=label,ordinary=left,bound=right))
        ordinary=[]
        length=FixedTokenizerLength(cfg['tokenizer_source']);length.bind(tokenizer)
        for value in ([],[1,2],(),('one',),{},dict(one=1),'blue',b'blue'):
            assert length(value)==len(value);ordinary.append(dict(type=type(value).__name__,length=len(value)))
        try:length(7)
        except TypeError:ordinary.append(dict(type='int',ordinary_typeerror=True))
        else:raise AssertionError('NON_LENGTH_OBJECT_ACCEPTED')
        clone=copy.deepcopy(tokenizer)
        try:length.bind(clone)
        except RuntimeError as exc:assert str(exc)=='TOKENIZER_INSTANCE_CHANGED'
        else:raise AssertionError('REPLACEMENT_TOKENIZER_ACCEPTED')
        mutated=FixedTokenizerLength(cfg['tokenizer_source']);mutated.bind(clone)
        assert clone.add_tokens(['__invented_c3_binding_mutation_20260911__'])==1
        try:mutated.recheck()
        except RuntimeError as exc:assert str(exc)=='TOKENIZER_CARDINALITY_CHANGED'
        else:raise AssertionError('MUTATED_VOCABULARY_ACCEPTED')
        baseline.recheck()
        del clone

        # Exercise the real hooks around invented output files and unchanged helper/writer/seal functions.
        success=out/'invented_finalization';success.mkdir()
        control_bytes=b'{"scope":"invented control"}\n'
        frozen=dict(tokenizer_source=cfg['tokenizer_source'],original_helper_asts=cfg['original_helper_asts'],freeze_sha256=args.config_sha256,
            embedded_controls=[dict(filename='INVENTED_CONTROL.json',sha256=hashlib.sha256(control_bytes).hexdigest(),size_bytes=len(control_bytes))])
        def fake_native(folder):
            return types.SimpleNamespace(OUT=folder,load_independent_functions=native.load_independent_functions,write_json=native.write_json,seal=native.seal)
        fake=fake_native(success);bindings=ValidationBindings(fake,frozen,{'INVENTED_CONTROL.json':control_bytes},expected_generations=1500,forbidden_events=events);bindings.install()
        actual=fake.load_independent_functions(root)['validate_generation'];started=time.perf_counter()
        for _ in range(500):
            for stage,receipt in cases:
                assert invocation(actual,stage,receipt)==dict(status='PASS',return_value=None)
        elapsed=time.perf_counter()-started
        report=dict(status='PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY',fixture_only=True)
        fake.write_json(success/'INDEPENDENT_VALIDATION.json',report)
        assert report['status']=='PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY'
        assert report['execution_binding']['fixed_length']['complete_vocabulary_rechecks']==3
        original_report_hash=hashlib.sha256((success/'INDEPENDENT_VALIDATION.json').read_bytes()).hexdigest()
        try:fake.write_json(success/'INDEPENDENT_VALIDATION.json',dict(status='FAIL',fixture_only=True))
        except RuntimeError as exc:assert str(exc)=='FIRST_INDEPENDENT_RESULT_ONLY'
        else:raise AssertionError('RESULT_OVERWRITE_ACCEPTED')
        fake.write_json(success/'SEAL.json',dict(status='INVENTED_ONLY',independent_sha256=original_report_hash))
        fake.seal(success)
        manifest=success/'SHA256_MANIFEST.json';manifest_hash=hashlib.sha256(manifest.read_bytes()).hexdigest()
        namespace=verify_namespace(success,manifest_hash)
        assert (success/'validation_execution/INVENTED_CONTROL.json').read_bytes()==control_bytes
        try:bindings.seal_with_controls(success)
        except RuntimeError as exc:assert str(exc)=='NO_EXECUTION_CONTROL_OVERWRITE'
        else:raise AssertionError('CONTROL_OVERWRITE_ACCEPTED')
        assert hashlib.sha256((success/'INDEPENDENT_VALIDATION.json').read_bytes()).hexdigest()==original_report_hash
        failed=out/'invented_original_failure';failed.mkdir();fake=fake_native(failed)
        failed_bindings=ValidationBindings(fake,frozen,{'INVENTED_CONTROL.json':control_bytes},expected_generations=1);failed_bindings.install()
        original_failure=dict(status='FAIL',fixture_only=True,diagnostic='INVENTED_ORIGINAL_FAILURE')
        fake.write_json(failed/'INDEPENDENT_VALIDATION.json',original_failure)
        assert original_failure['status']=='FAIL' and original_failure['diagnostic']=='INVENTED_ORIGINAL_FAILURE'
        assert original_failure['execution_binding']['status']=='ORIGINAL_VALIDATION_FAILED_NOT_UPGRADED'
        mismatch=out/'invented_binding_failure';mismatch.mkdir();fake=fake_native(mismatch)
        mismatch_bindings=ValidationBindings(fake,frozen,{'INVENTED_CONTROL.json':control_bytes},expected_generations=1);mismatch_bindings.install()
        incomplete=dict(status='PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY',fixture_only=True)
        fake.write_json(mismatch/'INDEPENDENT_VALIDATION.json',incomplete)
        assert incomplete['status']=='FAIL' and incomplete['execution_binding_error']=='ONE_COMPLETE_ORIGINAL_HELPER_LOAD'
        import torch
        assert not torch.cuda.is_initialized() and not events and not boundary['denied']
        baseline.recheck()
        result.update(status='PASS_C3_VALIDATION_BINDING_INVENTED_ONLY',equivalence_cases=equivalence,
            ordinary_len_cases=ordinary,replacement_tokenizer_rejected=True,cloned_vocabulary_mutation_rejected=True,
            original_primary_tokenizer_unchanged=True,periodic_fixture_generations=1500,periodic_fixture_elapsed_seconds=elapsed,
            periodic_fixture_binding=report['execution_binding'],original_helper_asts=cfg['original_helper_asts'],
            finalization_namespace_manifest_sha256=manifest_hash,finalization_namespace_files=len(namespace)-1,
            original_failure_not_upgraded=True,binding_failure_forces_fail_before_first_write=True,
            result_and_control_overwrites_rejected=True,original_finalization_functions_used=True,
            torch_cuda_initialized=False,actual_environment_prefix=sys.prefix)
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    result.update(execution_boundary=boundary_record(boundary),forbidden_execution_events=events)
    native.write_json(out/'FIXTURE_RESULT.json',result)
    print(json.dumps({k:result[k] for k in ('status','periodic_fixture_generations','periodic_fixture_elapsed_seconds','error_type','error') if k in result},indent=2))
    return 0 if result['status']=='PASS_C3_VALIDATION_BINDING_INVENTED_ONLY' else 2


if __name__=='__main__':
    raise SystemExit(main())
