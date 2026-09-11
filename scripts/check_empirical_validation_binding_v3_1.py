"""Invented-only regression gate for the prospective C3 V3.1 binding."""
import argparse
import ast
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    args = parser.parse_args()
    raw = args.config.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == args.config_sha256
    cfg = json.loads(raw)
    out = args.config.parent.resolve()
    repo = Path(cfg['engineering_root']).resolve()
    root = Path(cfg['project_root']).resolve()
    assert Path(sys.prefix).resolve() == root / '.venv'
    assert sys.flags.isolated and sys.dont_write_bytecode and site.ENABLE_USER_SITE is False
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
    assert all(name not in os.environ for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'))
    for entry in cfg['controls'] + cfg['inputs']:
        path = Path(entry['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
        assert path.stat().st_size == entry['size_bytes']
    sys.path.insert(0, str(repo))
    from scripts import validate_roa_empirical_runtime as native
    from scripts.empirical_pool_io import verify_namespace
    from scripts.empirical_retrieval_io import boundary_record, configure_environment
    from scripts.empirical_runtime_guard import guard
    from scripts.empirical_validation_binding_v3_1 import (
        EXPECTED_CONSTANTS, V31ValidationBindings, constant_assignments,
        dependency_inventory, source_record, observe_native_default)
    from scripts.validate_roa_empirical_runtime_bound_v3_1 import validate_evidence_pins
    from scripts.validate_roa_empirical_runtime_bound import profile_execution
    configure_environment(out)
    platform.uname()._asdict()
    environment = observe_native_default(cfg, 'start')
    events = []
    profile_execution(events)
    from transformers import AutoTokenizer
    boundary = guard(root, out, [Path(e['path']) for e in cfg['controls'] + cfg['inputs']] + [args.config],
        gpu_only=True, tokenizer_only=True)
    result = dict(status='FAIL', scope='INVENTED_ONLY_NO_CURRENT_RUNTIME_VALIDATION',
        source_commit=cfg['source_commit'], config_sha256=args.config_sha256,
        current_runtime_payloads_read=0, fresh_gold_values=0, neural_forwards=0, scientific_fits=0)
    try:
        helper = root / 'outputs/daa_v2_fresh_v1/runtime_branch_freeze/independent_validate.py'
        support = helper.with_name('runtime_support.py')
        frozen = dict(tokenizer_source=cfg['tokenizer_source'], original_helper_asts=cfg['original_helper_asts'],
            constant_sources=cfg['constant_sources'], constant_assignments=cfg['constant_assignments'],
            freeze_sha256=args.config_sha256, embedded_controls=[], v3_blas=cfg['v3_blas'],
            v3_auxiliary_pools=cfg['v3_auxiliary_pools'],
            census_task_manifest_sha256=cfg['census_task_manifest_sha256'],
            census_client_audit_manifest_sha256=cfg['census_client_audit_manifest_sha256'],
            environment_anomaly_audit_manifest_sha256=cfg['environment_anomaly_audit_manifest_sha256'])

        def fake_native(folder=None, loader=native.load_independent_functions):
            return types.SimpleNamespace(__file__=native.__file__, OUT=folder or out,
                load_independent_functions=loader, write_json=native.write_json, seal=native.seal)

        def invoke(function, *values):
            try:
                return dict(status='PASS', return_value=function(*values))
            except Exception as exc:
                return dict(status='REJECTED', error_type=type(exc).__name__, reason=str(exc))

        # Demonstrate the real V1 defect, then the second missing constant.
        plain = native.load_independent_functions(root)
        valid = dict(dataset='hotpotqa', retriever='bm25', sample_id='invented',
            question='Where is the blue marker?', a0='', a1='',
            evidence0=['invented passage'] * 5, evidence1=['invented repaired passage'] * 5)
        no_constants = invoke(plain['validate_branch'], valid)
        assert no_constants == dict(status='REJECTED', error_type='NameError', reason="name 'DATASETS' is not defined")
        plain = native.load_independent_functions(root)
        plain['validate_branch'].__globals__['DATASETS'] = EXPECTED_CONSTANTS['DATASETS']
        one_constant = invoke(plain['validate_branch'], valid)
        assert one_constant == dict(status='REJECTED', error_type='NameError', reason="name 'RETRIEVERS' is not defined")

        binding = V31ValidationBindings(fake_native(), frozen, {}, environment_start=environment)
        functions = binding.load_functions(root)
        assert binding.helper_scope_receipt['missing_before'] == ['DATASETS', 'RETRIEVERS']
        assert binding.helper_scope_receipt['missing_after'] == []
        assert binding.helper_scope_receipt['affected_helpers_before'] == ['validate_branch']

        # Independently bind the authenticated original assignment ASTs.
        independent = native.load_independent_functions(root)
        independent_scope = independent['validate_branch'].__globals__
        assignments = []
        for node in ast.parse(support.read_text(encoding='utf-8-sig')).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], 'id', None) in EXPECTED_CONSTANTS:
                assignments.append(node)
        assert len(assignments) == 2
        exec(compile(ast.Module(body=assignments, type_ignores=[]), str(support), 'exec'), independent_scope)
        assert {name: tuple(independent_scope[name]) for name in EXPECTED_CONSTANTS} == EXPECTED_CONSTANTS

        strata = []
        for dataset in EXPECTED_CONSTANTS['DATASETS']:
            for retriever in EXPECTED_CONSTANTS['RETRIEVERS']:
                row = copy.deepcopy(valid)
                row.update(dataset=dataset, retriever=retriever, sample_id=f'{dataset}-{retriever}')
                left = invoke(independent['validate_branch'], row)
                right = invoke(functions['validate_branch'], row)
                assert left == right == dict(status='PASS', return_value=None)
                assert row['a0'] == row['a1'] == ''
                strata.append(dict(dataset=dataset, retriever=retriever, result=right))

        branch_faults = {}
        extra = copy.deepcopy(valid); extra['extra'] = 'invented'
        missing = copy.deepcopy(valid); missing.pop('a1')
        wrong_type = copy.deepcopy(valid); wrong_type['question'] = 7
        bad_dataset = copy.deepcopy(valid); bad_dataset['dataset'] = 'invented'
        bad_retriever = copy.deepcopy(valid); bad_retriever['retriever'] = 'invented'
        bad_count = copy.deepcopy(valid); bad_count['evidence0'] = ['invented'] * 4
        bad_passage = copy.deepcopy(valid); bad_passage['evidence1'][2] = {'text': 'invented'}
        faults = dict(extra_field=extra, missing_field=missing, wrong_string_type=wrong_type,
            invalid_dataset=bad_dataset, invalid_retriever=bad_retriever,
            wrong_passage_count=bad_count, wrong_passage_type=bad_passage)
        expected_reasons = dict(extra_field='Canonical exact schema', missing_field='Canonical exact schema',
            wrong_string_type='Canonical string types', invalid_dataset='Canonical stratum',
            invalid_retriever='Canonical stratum', wrong_passage_count='Canonical five text passages',
            wrong_passage_type='Canonical five text passages')
        for label, row in faults.items():
            left = invoke(independent['validate_branch'], row)
            right = invoke(functions['validate_branch'], row)
            assert left == right and left['status'] == 'REJECTED' and left['reason'] == expected_reasons[label]
            branch_faults[label] = right
        nested = {'outer': [{'answer': 'invented forbidden value'}]}
        left = invoke(independent['no_forbidden_fields'], nested)
        right = invoke(functions['no_forbidden_fields'], nested)
        assert left == right and left['reason'] == 'Forbidden Gold/scoring/action field'
        branch_faults['nested_forbidden'] = right

        # Negative authentication/dependency cases.
        changed = copy.deepcopy(frozen)
        changed['constant_assignments']['DATASETS']['value'][0] = 'changed'
        assert invoke(V31ValidationBindings(fake_native(), changed, {}, environment_start=environment).load_functions, root)['reason'] == 'CONSTANT_ASSIGNMENT_AST_AND_VALUES'
        bad_pin = copy.deepcopy(frozen)
        bad_pin['constant_sources']['support']['sha256'] = '0' * 64
        assert invoke(V31ValidationBindings(fake_native(), bad_pin, {}, environment_start=environment).load_functions, root)['reason'] == 'FROZEN_CONSTANT_SOURCE_RECORDS'
        def prebound_loader(value):
            loaded = native.load_independent_functions(value)
            loaded['validate_branch'].__globals__['DATASETS'] = EXPECTED_CONSTANTS['DATASETS']
            return loaded
        assert invoke(V31ValidationBindings(fake_native(loader=prebound_loader), frozen, {}, environment_start=environment).load_functions, root)['reason'] == 'EXACT_PREBIND_MISSING_GLOBALS'
        nested_scope = {}
        exec('def outer():\n    def inner():\n        return INVENTED_MISSING_GLOBAL\n    return inner()\n', nested_scope)
        _, nested_inventory, nested_missing = dependency_inventory({'outer': nested_scope['outer']})
        assert nested_missing == ['INVENTED_MISSING_GLOBAL']
        assert nested_inventory['outer']['missing'] == ['INVENTED_MISSING_GLOBAL']
        controls = {entry['name']: json.loads(Path(entry['path']).read_text(encoding='utf-8'))
                    for entry in cfg['controls'] if entry['name'] in {'census_results', 'census_client_audit'}}
        validate_evidence_pins(cfg, controls['census_results'], controls['census_client_audit'])
        changed_census = copy.deepcopy(cfg); changed_census['census_task_manifest_sha256'] = '0' * 64
        assert invoke(validate_evidence_pins, changed_census, controls['census_results'], controls['census_client_audit'])['reason'] == 'V3_CENSUS_TASK_PIN'
        changed_audit = copy.deepcopy(cfg); changed_audit['census_client_audit_manifest_sha256'] = '0' * 64
        assert invoke(validate_evidence_pins, changed_audit, controls['census_results'], controls['census_client_audit'])['reason'] == 'V3_CENSUS_AUDIT_PIN'
        changed_environment_audit = copy.deepcopy(cfg); changed_environment_audit['environment_anomaly_audit_manifest_sha256'] = '0' * 64
        assert invoke(validate_evidence_pins, changed_environment_audit, controls['census_results'], controls['census_client_audit'])['reason'] == 'V3_1_ENVIRONMENT_AUDIT_PIN'

        # Exercise branch -> generation -> original result/finalization with the real tokenizer.
        tokenizer = AutoTokenizer.from_pretrained(cfg['tokenizer_snapshot'], local_files_only=True, trust_remote_code=False)
        evidence = [dict(rank=i, document_id='invented-' + str(i), title='Invented title ' + str(i),
            text='The blue marker is in the invented box.') for i in range(1, 6)]
        question = valid['question']
        templates = dict(answer='Answer the invented question: {question}\n{evidence}',
            repair_query='Provide Search Query: for {question}\n{evidence}')
        runtime_config = dict(runtime_config_sha256='f' * 64)
        trace = dict(dataset='hotpotqa', retriever='bm25', sample_id='invented', position=0)
        rendered = functions['render'](evidence)
        cases = []
        for stage, text in [('a0', ''), ('repair_query', 'Search Query: blue marker'), ('a1', 'Answer: blue')]:
            user = templates['repair_query' if stage == 'repair_query' else 'answer'].format(question=question, evidence=rendered['text'])
            prompt = tokenizer.apply_chat_template([dict(role='user', content=user)], tokenize=False, add_generation_prompt=True)
            tokens = tokenizer([prompt], truncation=False)
            ids = tokenizer.encode(text, add_special_tokens=False) + [tokenizer.eos_token_id]
            decoded = tokenizer.batch_decode([ids], skip_special_tokens=True)[0].strip()
            parsed, fallback = functions['parsed_query'](decoded, question) if stage == 'repair_query' else (functions['parsed_answer'](decoded), None)
            count = 0
            for token in ids:
                if token == tokenizer.pad_token_id:
                    break
                count += 1
            receipt = dict(trace, stage=stage, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                input_token_ids=tokens['input_ids'][0], attention_mask=tokens['attention_mask'][0], generated_token_ids=ids,
                raw_text=decoded, input_tokens=sum(tokens['attention_mask'][0]), output_tokens=count,
                native_output_score_steps=len(ids), render=rendered, parsed_text=parsed, parser_fallback=fallback,
                logical_generation_calls=1, qwen_forward_calls=len(ids), runtime_config_sha256=runtime_config['runtime_config_sha256'])
            cases.append((stage, receipt))

        success = out / 'invented_finalization'
        success.mkdir()
        control_bytes = b'{"scope":"invented V3.1 control"}\n'
        final_frozen = dict(frozen, embedded_controls=[dict(filename='INVENTED_V3_1_CONTROL.json',
            sha256=hashlib.sha256(control_bytes).hexdigest(), size_bytes=len(control_bytes))])
        final = fake_native(success)
        final_binding = V31ValidationBindings(final, final_frozen, {'INVENTED_V3_1_CONTROL.json': control_bytes},
            expected_generations=3, forbidden_events=events, environment_start=environment)
        final_binding.install()
        final_functions = final.load_independent_functions(root)
        started = time.perf_counter()
        for stage, receipt in cases:
            row = copy.deepcopy(valid)
            assert invoke(final_functions['validate_branch'], row) == dict(status='PASS', return_value=None)
            assert invoke(final_functions['validate_generation'], receipt, trace, stage, evidence, question,
                tokenizer, templates, runtime_config) == dict(status='PASS', return_value=None)
        elapsed = time.perf_counter() - started
        report = dict(status='PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY', fixture_only=True)
        final.write_json(success / 'INDEPENDENT_VALIDATION.json', report)
        assert report['execution_binding']['status'] == 'PASS_COMPLETE_DECLARED_EXECUTION_BINDING_PENDING_FINAL_SEAL'
        assert report['execution_binding']['helper_scope']['status'] == 'PASS_TWO_ORIGINAL_CONSTANTS_BOUND'
        original_report_hash = hashlib.sha256((success / 'INDEPENDENT_VALIDATION.json').read_bytes()).hexdigest()
        try:
            final.write_json(success / 'INDEPENDENT_VALIDATION.json', dict(status='FAIL'))
        except RuntimeError as exc:
            assert str(exc) == 'FIRST_INDEPENDENT_RESULT_ONLY'
        else:
            raise AssertionError('RESULT_OVERWRITE_ACCEPTED')
        final.write_json(success / 'SEAL.json', dict(status='INVENTED_ONLY', independent_sha256=original_report_hash))
        final.seal(success)
        manifest = success / 'SHA256_MANIFEST.json'
        manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
        namespace = verify_namespace(success, manifest_hash)
        try:
            final_binding.seal_with_controls(success)
        except RuntimeError as exc:
            assert str(exc) == 'NO_EXECUTION_CONTROL_OVERWRITE'
        else:
            raise AssertionError('CONTROL_OVERWRITE_ACCEPTED')

        failed = out / 'invented_original_failure'; failed.mkdir()
        failed_native = fake_native(failed)
        failed_binding = V31ValidationBindings(failed_native, final_frozen, {'INVENTED_V3_1_CONTROL.json': control_bytes}, expected_generations=3, environment_start=environment)
        failed_binding.install()
        failed_report = dict(status='FAIL', fixture_only=True, diagnostic='INVENTED_ORIGINAL_FAILURE')
        failed_native.write_json(failed / 'INDEPENDENT_VALIDATION.json', failed_report)
        assert failed_report['status'] == 'FAIL'
        assert failed_report['execution_binding']['status'] == 'ORIGINAL_VALIDATION_FAILED_NOT_UPGRADED'

        incomplete = out / 'invented_binding_failure'; incomplete.mkdir()
        incomplete_native = fake_native(incomplete)
        incomplete_binding = V31ValidationBindings(incomplete_native, final_frozen,
            {'INVENTED_V3_1_CONTROL.json': control_bytes}, expected_generations=3, environment_start=environment)
        incomplete_binding.install()
        incomplete_report = dict(status='PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY', fixture_only=True)
        incomplete_native.write_json(incomplete / 'INDEPENDENT_VALIDATION.json', incomplete_report)
        assert incomplete_report['status'] == 'FAIL'
        assert incomplete_report['execution_binding_error'] == 'ONE_COMPLETE_ORIGINAL_HELPER_LOAD'

        import torch
        assert not torch.cuda.is_initialized() and not events and not boundary['denied']
        fixed = report['execution_binding']['fixed_length']
        assert fixed['successful_generation_checks'] == 3
        assert fixed['specialized_length_calls'] == fixed['generated_ids_checked']
        result.update(status='PASS_C3_VALIDATION_V3_1_INVENTED_ONLY',
            demonstrated_missing_constants=dict(neither=no_constants, datasets_only=one_constant),
            strata=strata, branch_rejection_cases=branch_faults,
            constant_assignment_sources=dict(current=constant_assignments(Path(native.__file__)), historical=constant_assignments(support)),
            independently_executed_assignment_asts=2, nested_code_dependency_detected=True,
            negative_cases=['changed_tuple', 'changed_source_pin', 'prebound_name', 'unresolved_nested_global'],
            composed_generation_checks=3, generated_ids_checked=fixed['generated_ids_checked'],
            complete_vocabulary_rechecks=fixed['complete_vocabulary_rechecks'],
            composed_elapsed_seconds=elapsed, composed_binding=report['execution_binding'],
            finalization_namespace_manifest_sha256=manifest_hash, finalization_namespace_files=len(namespace) - 1,
            original_failure_not_upgraded=True, binding_failure_forces_fail_before_first_write=True,
            result_and_control_overwrites_rejected=True, original_finalization_functions_used=True,
            original_result_fields_preserved_by_canonical_hash=True,
            constant_source_records={name: source_record(value['path']) for name, value in cfg['constant_sources'].items()},
            torch_cuda_initialized=False, actual_environment_prefix=sys.prefix,
            native_default_environment=environment, changed_census_and_audit_pins_rejected=True,
            changed_environment_anomaly_audit_pin_rejected=True)
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
    result.update(execution_boundary=boundary_record(boundary), forbidden_execution_events=events)
    native.write_json(out / 'FIXTURE_RESULT.json', result)
    print(json.dumps({key: result[key] for key in ('status', 'composed_generation_checks', 'generated_ids_checked',
        'complete_vocabulary_rechecks', 'error_type', 'error') if key in result}, indent=2))
    return 0 if result['status'] == 'PASS_C3_VALIDATION_V3_1_INVENTED_ONLY' else 2


if __name__ == '__main__':
    raise SystemExit(main())
