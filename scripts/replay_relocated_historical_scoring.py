"""Full historical feature/estimator replay from authenticated restored inputs."""
import argparse
import ast
from dataclasses import dataclass
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import site
import sys
import traceback
import types


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def source_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')


def key(row):
    return tuple(row[k] for k in ('dataset', 'retriever', 'sample_id'))


def main():
    p = argparse.ArgumentParser(); p.add_argument('--config', required=True, type=Path); p.add_argument('--config-sha256', required=True)
    a = p.parse_args(); assert sha(a.config) == a.config_sha256
    cfg = json.loads(a.config.read_text(encoding='utf-8')); out = a.config.parent.resolve()
    env = Path(cfg['environment']).resolve()
    assert Path(sys.prefix).resolve() == env and site.ENABLE_USER_SITE is False and sys.flags.isolated and sys.dont_write_bytecode
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1' and os.environ['OMP_NUM_THREADS'] == '1'
    controls = {e['name']: e for e in cfg['controls']}
    for e in controls.values(): assert sha(Path(e['path'])) == e['sha256'] and Path(e['path']).stat().st_size == e['size_bytes']
    assert Path(controls['producer']['path']).resolve() == Path(__file__).resolve()
    adapter = source_module('historical_delivery_paths', Path(controls['adapter']['path']))
    guard_module = source_module('historical_replay_guard', Path(controls['guard']['path']))
    roots = {k: Path(v['physical']).resolve() for k, v in cfg['roots'].items()}
    files = adapter.BoundFiles({k: adapter.RootBinding(v['logical'], Path(v['physical'])) for k, v in cfg['roots'].items()}, cfg['files'])
    permitted = [files.checked(e['logical_path']) for e in cfg['files']]
    named = {name: files.checked(record['logical_path']) for name, record in cfg['named_inputs'].items()}
    state, bootstrap, allowed = guard_module.install(env, out, permitted + [Path(e['path']) for e in controls.values()] + [a.config])
    result = dict(status='FAIL', started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), config_sha256=a.config_sha256,
                  cas_q2_status='NOT READY', scientific_fits=0, pretrained_model_loads=0, neural_forwards=0,
                  fresh_empirical_gold_values=0, historical_gold_values=0, historical_neural_replay=False,
                  full_fresh_pipeline_replay=False, original_project_content_reads=0)
    mismatches, checks, max_error = [], 0, 0.0

    def compare(actual, reference, label):
        nonlocal checks, max_error
        if isinstance(reference, dict):
            if not isinstance(actual, dict) or set(actual) != set(reference):
                mismatches.append(dict(field=label, kind='KEY_SET', actual_keys=list(actual) if isinstance(actual, dict) else None, expected_keys=list(reference))); return
            for k in reference: compare(actual[k], reference[k], label + '/' + k)
        elif type(reference) in (float, int) and type(actual) in (float, int):
            checks += 1
            if not math.isfinite(actual) or not math.isfinite(reference): mismatches.append(dict(field=label, kind='NONFINITE')); return
            error = abs(actual - reference); max_error = max(max_error, error)
            if error > 1e-12: mismatches.append(dict(field=label, kind='NUMERIC', actual=actual, expected=reference, error=error))
        elif actual != reference or type(actual) is not type(reference):
            mismatches.append(dict(field=label, kind='EXACT', actual=actual, expected=reference))

    def rows(name):
        path = named[name]; loaded = []
        with path.open(encoding='utf-8') as f:
            for line in f:
                assert line.endswith('\n') and line.strip(); loaded.append(json.loads(line))
        assert len({key(r) for r in loaded}) == len(loaded), 'DUPLICATE_INPUT_KEYS:' + name
        return loaded

    try:
        result['platform_bootstrap'] = bootstrap()
        import numpy as np
        from threadpoolctl import threadpool_limits
        loader = adapter.SourceLoader(files); original = roots['original']
        loader.load('v3_support', named['v3_support'])
        wrapper = loader.load('delivery_historical_native_base', named['native_base'])
        native = wrapper.assemble()
        v2 = types.ModuleType('src.arbitration.v2_ensemble'); v2.__dict__.update(np=np, dataclass=dataclass); sys.modules[v2.__name__] = v2
        v2_nodes = wrapper.take(v2, 'src/arbitration/v2_ensemble.py', {'V2_SCORE_FEATURES', 'V2_LABELS', 'V2_LAMBDA_DAMAGE', 'V2_META_ALPHA',
            'V2_ACTION_RATE', 'V2_GROUP_FOLDS', 'V2_GROUP_SEED', 'V2EnsembleBundle', 'empirical_cdf', 'transition_utility', 'score_unseen', 'action_budget'})
        eligibility = loader.load('src.evaluation.answer_normalization', named['eligibility'])
        schema = loader.load('src.evaluation.fresh_schema', named['schema'])
        golden = json.loads(named['golden_cpu'].read_text(encoding='utf-8'))
        assert native.source_definitions + v2_nodes == golden['native_ast_nodes']
        provenance = json.loads(named['base_provenance'].read_text(encoding='utf-8'))
        assert native.source_definitions == provenance['source_definitions']
        tree = ast.parse(named['scoring_io'].read_text(encoding='utf-8-sig')); nodes = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'saved_models': nodes.append(node)
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'FIELDS': nodes.append(node)
        assert len(nodes) == 2
        bridge = types.ModuleType('delivery_saved_models')
        def load_metadata(path): return json.loads(files.checked_physical(path).read_text(encoding='utf-8'))
        def require(value, message):
            if not value: raise RuntimeError(message)
        bridge.__dict__.update(load=load_metadata, require=require, PANEL=named['panel'].parent)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(named['scoring_io']), 'exec'), bridge.__dict__)
        models, bundle, panel = bridge.saved_models(original, native, v2)
        bundle_checks = types.ModuleType('delivery_bundle_checks'); bundle_checks.__dict__.update(np=np, FEATURES=tuple(v2.V2_SCORE_FEATURES), require=require)
        check_nodes = wrapper.take(bundle_checks, 'outputs/daa_v2_fresh_v1/prelabel_seal_v3/independent_validate.py', {'bundle_check'})
        bundle_checks.bundle_check(bundle)
        assert len(models) == 7 and len(panel) == 5 and len(state['model_load_calls']) == 8
        branches = rows('branches'); sidecar = rows('sidecar'); semantic = rows('semantic'); cells = rows('cells'); pairs = rows('pairs'); scores = rows('scores'); decisions = rows('decisions')
        assert len(branches) == len(sidecar) == len(semantic) == len(scores) == len(decisions) == 13500
        assert len(cells) == len(pairs) == 3202
        universe = {key(b) for b in branches}
        assert len({(k[0], k[2]) for k in universe}) == 4500
        for ds in ('hotpotqa', '2wikimultihopqa', 'musique'):
            for retriever in ('bm25', 'dense', 'hybrid'): assert sum(k[:2] == (ds, retriever) for k in universe) == 1500
        by = {name: {key(r): r for r in values} for name, values in dict(sidecar=sidecar, semantic=semantic, cells=cells, pairs=pairs, scores=scores, decisions=decisions).items()}
        assert all(set(by[name]) == universe for name in ('sidecar', 'semantic', 'scores', 'decisions'))
        assert set(by['cells']) == set(by['pairs'])
        replay = {}; fields = tuple(v2.V2_SCORE_FEATURES); observed_eligible = set(); reasons = {}
        with threadpool_limits(limits=1), (out / 'FEATURE_SCORE_REPLAY_PRIVATE.jsonl').open('x', encoding='utf-8', newline='\n') as partial:
            for i, branch in enumerate(branches, 1):
                k = key(branch); trace = wrapper.restore_trace(branch, by['sidecar'][k])
                trace['answer_semantic_agreement'] = by['semantic'][k]['answer_semantic_agreement']
                decision = eligibility.assess_pair_eligibility(trace['a0'], trace['a1'])
                if decision.eligible:
                    observed_eligible.add(k)
                    pair = native.symmetric.build_pair_record(trace, by['cells'][k]['cells'], schema_version='mars-state-symmetric-v1')
                    compare(pair, by['pairs'][k], str(k) + '/pair')
                    values = wrapper.base_scores(native, models, pair)
                else:
                    pair, values = None, {f: None for f in fields}
                    reasons[decision.reason] = reasons.get(decision.reason, 0) + 1
                compare(values, by['scores'][k]['scores'], str(k) + '/scores')
                replay[k] = dict(dataset=k[0], retriever=k[1], sample_id=k[2], pair=pair, scores=values,
                                 forced_keep_reason=decision.reason, v2_score=None, hgb_action='KEEP', v2_action='KEEP')
                partial.write(json.dumps(replay[k], sort_keys=True, allow_nan=False) + '\n'); partial.flush()
                if i % 1500 == 0: print('HISTORICAL_FEATURE_SCORE_ROWS', i, 13500, flush=True)
            assert observed_eligible == set(by['pairs']) and len(observed_eligible) == 3202
            assert reasons == {'a1_empty': 2, 'normalized_answers_equal': 10296}
            ordered = sorted(observed_eligible)
            x = np.asarray([[replay[k]['scores'][f] for f in fields] for k in ordered], dtype=float)
            fused = v2.score_unseen(bundle, x)
            assert len(fused) == 3202 and np.isfinite(fused).all() and v2.action_budget(13500, bundle.action_rate) == 675
            for k, value in zip(ordered, fused, strict=True):
                replay[k]['v2_score'] = float(value); compare(float(value), by['decisions'][k]['v2_score'], str(k) + '/v2_score')
            hgb_selected = set(sorted(ordered, key=lambda k: (-replay[k]['scores']['state_symmetric_hgb'], k))[:675])
            v2_selected = set(sorted(ordered, key=lambda k: (-replay[k]['v2_score'], k))[:675])
            for k in sorted(replay):
                row = replay[k]; row['hgb_action'] = 'REPLACE' if k in hgb_selected else 'KEEP'; row['v2_action'] = 'REPLACE' if k in v2_selected else 'KEEP'
                compare(row['hgb_action'], by['decisions'][k]['hgb_action'], str(k) + '/hgb_action')
                compare(row['v2_action'], by['decisions'][k]['action'], str(k) + '/v2_action')
                compare(row['forced_keep_reason'], by['decisions'][k]['forced_keep_reason'], str(k) + '/forced_keep_reason')
        with (out / 'HISTORICAL_REPLAY_PRIVATE.jsonl').open('x', encoding='utf-8', newline='\n') as f:
            for k in sorted(replay): f.write(json.dumps(replay[k], sort_keys=True, allow_nan=False) + '\n')
        for e in cfg['files']: files.checked(e['logical_path'])
        modules = {}
        for name, module in list(sys.modules.items()):
            path = getattr(module, '__file__', None)
            if isinstance(path, str) and not path.startswith('<'):
                resolved = Path(path).resolve(); assert allowed(resolved), ('MODULE_OUTSIDE_RESTORED_INPUTS', name, path); modules[name] = str(resolved)
        assert len(state['optional_import_refusals']) == 1 and not state['blocked'] and not state['forbidden_calls']
        assert not any(name == 'pyarrow' or name.startswith(('pyarrow.', 'torch.', 'transformers.')) for name in sys.modules)
        result.update(status='PASS_FULL_RELOCATED_HISTORICAL_SCORING_PENDING_INDEPENDENT' if not mismatches else 'FAIL_HISTORICAL_NUMERICAL_OR_ACTION_MISMATCH',
                      traces=13500, question_groups=4500, eligible_pairs=3202, forced_keep_traces=10298, forced_keep_reasons=reasons,
                      base_score_values=32020, v2_score_values=3202, action_comparisons=27000, numeric_checks=checks, max_numeric_error=max_error,
                      saved_upstream_estimators=7, saved_v2_bundles=1, fixed_panel_heads_metadata=5, used_restored_files_unchanged=len(cfg['files']),
                      source_definitions=native.source_definitions + v2_nodes, bundle_check_ast=check_nodes,
                      saved_models_bridge_ast=[dict(name=getattr(n, 'name', 'FIELDS'), ast_sha256=hashlib.sha256(ast.dump(n, include_attributes=False).encode()).hexdigest()) for n in nodes],
                      bridge_IO_globals=dict(PANEL=str(named['panel'].parent), load='authenticated bound-file JSON metadata read', require='raise on false'),
                      supported_imports=loader.loaded, loaded_python_modules=modules, original_metadata_rewritten=False,
                      replay_sha256=sha(out / 'HISTORICAL_REPLAY_PRIVATE.jsonl'))
    except Exception as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc(), failed_outputs_retained=True)
    finally: sys.setprofile(None)
    write(out / 'MISMATCHES_PRIVATE.json', dict(mismatches=mismatches))
    result.update(mismatch_count=len(mismatches), guard={**state, 'opened': sorted(state['opened'])}, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write(out / 'PRODUCER_RESULT.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in {'guard', 'loaded_python_modules', 'source_definitions', 'supported_imports'}}, indent=2))
    return 0 if result['status'] == 'PASS_FULL_RELOCATED_HISTORICAL_SCORING_PENDING_INDEPENDENT' else 2


if __name__ == '__main__':
    raise SystemExit(main())
