"""Version 2: explicit fixed-tokenizer cardinality binding; original selected ASTs."""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import sys
import traceback
import types


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--config', required=True, type=Path); parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--producer-inputs', required=True, type=Path); parser.add_argument('--producer-inputs-sha256', required=True); args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding='utf-8')); rec = next(e for e in cfg['controls'] if e['name'] == 'io')
    path = Path(rec['path']); assert hashlib.sha256(path.read_bytes()).hexdigest() == rec['sha256']
    io = types.ModuleType('independent_tokenizer_io'); io.__file__ = str(path); sys.modules[io.__name__] = io; exec(compile(path.read_bytes(), str(path), 'exec'), io.__dict__)
    cfg, out, env, named, state, allowed, result = io.setup(args.config, args.config_sha256, 'validator')
    result['original_physical_root'] = cfg['roots']['original']['physical']
    try:
        assert io.sha(args.producer_inputs) == args.producer_inputs_sha256
        for e in json.loads(args.producer_inputs.read_text(encoding='utf-8'))['files']:
            p = out / e['path']; assert p.parent == out and io.sha(p) == e['sha256'] and p.stat().st_size == e['size_bytes']
        producer = json.loads((out / 'PRODUCER_RESULT.json').read_text(encoding='utf-8'))
        assert producer['status'] == 'PASS_FULL_HISTORICAL_QWEN_TOKENIZER_PENDING_INDEPENDENT'
        original = io.namespace('original_independent_tokenizer_validator'); records = result['ast_nodes']
        io.take(original, named['support'], {'DATASETS', 'RETRIEVERS', 'BRANCH_FIELDS', 'require', 'canonical', 'jsha', 'tsha', 'trace_key'}, records)
        io.take(original, named['independent'], {'FORBIDDEN', 'no_forbidden_fields', 'parsed_answer', 'parsed_query', 'render', 'validate_branch', 'independent_replay_subset', 'validate_generation'}, records)
        tokenizer, pre = io.tokenizer(named, result)
        cardinality = len(tokenizer)
        vocabulary_sha = io.jsha(tokenizer.get_vocab())
        cardinality_calls = 0
        fixture_cardinality_calls = 0
        generated_ids_checked = 0
        vocabulary_rechecks = 0
        negative_checks = []

        def frozen_cardinality(value):
            nonlocal cardinality_calls
            if value is tokenizer:
                cardinality_calls += 1
                return cardinality
            return len(value)

        def recheck_vocabulary():
            nonlocal vocabulary_rechecks
            assert len(tokenizer) == cardinality and io.jsha(tokenizer.get_vocab()) == vocabulary_sha
            vocabulary_rechecks += 1

        assert cardinality == 151665 and 'len' not in original.__dict__
        original.__dict__['len'] = frozen_cardinality
        templates = {'answer': named['answer_template'].read_text(encoding='utf-8'), 'repair_query': named['repair_template'].read_text(encoding='utf-8')}
        def rows(name):
            with named[name].open(encoding='utf-8') as f: return [json.loads(line) for line in f]
        traces = rows('canonical_traces'); replay = rows('replay_traces')
        assert len(traces) == len({original.trace_key(t) for t in traces}) == 13500 and len({(t['dataset'], t['sample_id']) for t in traces}) == 4500
        assert [t['position'] for t in traces] == list(range(13500)) and replay == original.independent_replay_subset(traces)
        replay_keys = {original.trace_key(t) for t in replay}; references = {}; coverage = {}; fields_checked = 0; input_total = output_total = 0
        with (out / 'TOKENIZER_REPLAY_PRIVATE.jsonl').open(encoding='utf-8') as produced:
            for mode, ordered in [('canonical', traces), ('replay', replay)]:
                handles = [named[mode + '_' + role].open(encoding='utf-8') for role in ('branches', 'provenance', 'generations')]
                strata = collections.Counter(); failclosed = collections.Counter()
                try:
                    for i, trace in enumerate(ordered, 1):
                        branch, provenance = [json.loads(next(f)) for f in handles[:2]]; gens = []
                        k = original.trace_key(trace); assert original.trace_key(branch) == original.trace_key(provenance) == k
                        original.validate_branch(branch); original.no_forbidden_fields(provenance)
                        assert provenance['position'] == trace['position'] and provenance['runtime_config_sha256'] == pre['runtime_config_sha256']
                        assert provenance['canonical_row_sha256'] == original.jsha(branch) and provenance['question_sha256'] == original.tsha(branch['question'])
                        for side in ('e0', 'e1'):
                            assert [d['text'] for d in provenance[side]] == branch['evidence0' if side == 'e0' else 'evidence1']
                        for stage in ('a0', 'repair_query', 'a1'):
                            archived = json.loads(next(handles[2])); gens.append(archived)
                            original.validate_generation(archived, trace, stage, provenance['e1' if stage == 'a1' else 'e0'], branch['question'], tokenizer, templates, pre)
                            generated_ids_checked += len(archived['generated_token_ids'])
                            if not negative_checks:
                                before_fixtures = cardinality_calls
                                for fault, expected_error in [('prompt', 'Independent prompt hash'), ('input', 'Independent input token IDs/mask'), ('vocabulary', 'Generated token ID schema')]:
                                    invalid = copy.deepcopy(archived)
                                    if fault == 'prompt': invalid['prompt_sha256'] = '0' * 64
                                    if fault == 'input': invalid['input_token_ids'][0] = -1
                                    if fault == 'vocabulary': invalid['generated_token_ids'] = [cardinality]
                                    try:
                                        original.validate_generation(invalid, trace, stage, provenance['e0'], branch['question'], tokenizer, templates, pre)
                                    except RuntimeError as exc:
                                        assert str(exc) == expected_error
                                        negative_checks.append(dict(fault=fault, expected_rejection=expected_error, rejected=True))
                                    else: raise AssertionError('COUNTERFEIT_RECEIPT_ACCEPTED')
                                fixture_cardinality_calls = cardinality_calls - before_fixtures
                            row = json.loads(next(produced))
                            assert set(row) == {'mode', 'dataset', 'retriever', 'sample_id', 'position', 'stage', 'rebuilt', 'archived_observations', 'bindings'}
                            assert row['mode'] == mode and original.trace_key(row) == k and row['position'] == trace['position'] and row['stage'] == stage
                            assert set(row['rebuilt']) == {'prompt_sha256', 'input_token_ids', 'attention_mask', 'raw_text', 'input_tokens', 'output_tokens', 'native_output_score_steps', 'render', 'parsed_text', 'parser_fallback'}
                            for field, value in row['rebuilt'].items(): assert value == archived[field] and type(value) is type(archived[field]); fields_checked += 1
                            assert row['archived_observations'] == {k: archived[k] for k in ('generated_token_ids', 'qwen_forward_calls')}
                            assert row['bindings'] == {name: original.jsha(value) for name, value in dict(trace=trace, branch=branch, provenance=provenance, generation=archived).items()}
                            input_total += archived['input_tokens']; output_total += archived['output_tokens']
                            if stage != 'repair_query' and archived['parsed_text'] == '': failclosed['empty_' + stage] += 1
                            if stage == 'repair_query' and archived['parser_fallback']: failclosed['repair_parser_fallback'] += 1
                        assert branch['a0'] == gens[0]['parsed_text'] and branch['a1'] == gens[2]['parsed_text']
                        signature = original.jsha(dict(branch=branch, provenance=provenance, generations=gens))
                        if mode == 'canonical' and k in replay_keys: references[k] = signature
                        if mode == 'replay': assert signature == references[k], 'HISTORICAL_FIXED_REPLAY_SIGNATURE_MISMATCH'
                        strata[k[:2]] += 1
                        if i % 1500 == 0:
                            recheck_vocabulary(); print('INDEPENDENT_QWEN_TOKENIZER', mode, i, len(ordered), flush=True)
                    assert all(f.readline() == '' for f in handles), 'EXTRA_ARCHIVED_ROWS'
                finally:
                    for f in handles: f.close()
                recheck_vocabulary()
                assert strata == collections.Counter({(d, r): 1500 if mode == 'canonical' else 20 for d in original.DATASETS for r in original.RETRIEVERS})
                coverage[mode] = dict(traces=len(ordered), generations=3 * len(ordered), strata={d + '/' + r: v for (d, r), v in sorted(strata.items())}, retained_failclosed=dict(failclosed))
            assert produced.readline() == '' and len(references) == 180
        assert cardinality_calls - fixture_cardinality_calls == generated_ids_checked and len(negative_checks) == 3 and vocabulary_rechecks == 11
        result['explicit_cardinality_binding'] = dict(global_name='len', only_specialized_object='the one fixed tokenizer instance', all_other_objects='ordinary builtin len', cardinality=cardinality, vocabulary_sha256=vocabulary_sha, ordinary_cardinality_and_full_vocabulary_rechecks=vocabulary_rechecks, full_ledger_specialized_calls=cardinality_calls-fixture_cardinality_calls, fixture_specialized_calls=fixture_cardinality_calls, tokenizer_mutated=False, selected_original_function_asts_changed=False, original_builtin_binding_changed=True)
        result['negative_checks'] = negative_checks
        assert fields_checked == 410400 and input_total == producer['input_tokens_checked'] and output_total == producer['output_tokens_checked']
        assert not producer['blocked_events'] and not producer['forbidden_calls'] and producer['capability_sockets_closed'] and not producer['torch_cuda_initialized']
        result.update(status='PASS_FULL_HISTORICAL_QWEN_TOKENIZER_ONLY', coverage=coverage, generation_receipts=41040,
            exact_rebuilt_field_comparisons=fields_checked, input_tokens_checked=input_total, output_tokens_checked=output_total,
            original_validate_generation_calls=41040, independent_subset_traces=180, exact_subset_signatures=180, mismatches=0,
            scope='Historical input/decoder validation only; shared fixed tokenizer; explicit stable-cardinality binding; no retrieval or neural replay')
    except Exception as exc: result.update(error=repr(exc), traceback=traceback.format_exc())
    io.finish(result, state, allowed, out, 'INDEPENDENT_RESULT.json')
    print(json.dumps({k: result[k] for k in ('status', 'generation_receipts', 'input_tokens_checked', 'output_tokens_checked') if k in result}, indent=2))
    return 0 if result['status'].startswith('PASS_') else 2


if __name__ == '__main__': raise SystemExit(main())
