"""Independent standard-library comparison to all archived historical rows."""
import argparse
import collections
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

GRAPH_PIN = 'aa5c3da7ed764405e92602b64303984931a798abf2aee3e64c5d56ae34e892ea'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def load(path): return json.loads(path.read_text(encoding='utf-8'))
def key(row): return tuple(row[f] for f in ('dataset', 'retriever', 'sample_id'))


def main():
    p = argparse.ArgumentParser(); p.add_argument('--inputs', required=True, type=Path); p.add_argument('--inputs-sha256', required=True)
    a = p.parse_args(); assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    assert sha(a.inputs) == a.inputs_sha256
    inputs = load(a.inputs); out = a.inputs.parent.resolve()
    config_path = Path(inputs['config']['path']); assert sha(config_path) == inputs['config']['sha256']; cfg = load(config_path)
    controls = {e['name']: e for e in cfg['controls']}
    assert Path(controls['validator']['path']).resolve() == Path(__file__).resolve()
    for e in controls.values(): assert sha(Path(e['path'])) == e['sha256'] and Path(e['path']).stat().st_size == e['size_bytes']
    assert sha(Path(controls['graph_manifest']['path'])) == GRAPH_PIN
    graph_seal = load(Path(controls['graph_manifest']['path']))
    g = next(e for e in graph_seal['files'] if e['path'] == 'NODES_PRIVATE.json')
    assert sha(Path(controls['graph_nodes']['path'])) == g['sha256']
    graph = load(Path(controls['graph_nodes']['path'])); nodes = {e['logical_path']: e for e in graph['files']}
    paths = {}
    for name in ('pairs', 'scores', 'decisions', 'decision_seal'):
        e = cfg['named_inputs'][name]; parent = nodes[e['logical_path']]
        assert all(parent[k] == e[k] for k in ('root', 'relative_path', 'logical_path', 'sha256', 'size_bytes'))
        path = Path(cfg['roots'][e['root']]['physical']) / e['relative_path']
        assert sha(path) == e['sha256'] and path.stat().st_size == e['size_bytes']; paths[name] = path
    for e in inputs['producer_files']:
        assert sha(Path(e['path'])) == e['sha256'] and Path(e['path']).stat().st_size == e['size_bytes']
    named = set(paths.values()) | {Path(e['path']) for e in controls.values()} | {config_path, a.inputs}
    libraries = [Path(sys.base_prefix).resolve(), Path(os.environ['SystemRoot']).resolve()]
    blocked, opened = [], set()

    def guard(event, args):
        if event == 'import' and args[0].split('.')[0] in {'numpy', 'scipy', 'sklearn', 'joblib', 'pickle', '_pickle', 'torch', 'transformers', 'datasets', 'pyarrow', 'sentencepiece'}:
            blocked.append(dict(event=event, module=args[0])); raise RuntimeError('SCIENTIFIC_IMPORT_FORBIDDEN')
        if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.sendto', 'subprocess.Popen', 'os.system', 'urllib.Request'}:
            blocked.append(dict(event=event)); raise RuntimeError('NETWORK_OR_PROCESS_FORBIDDEN')
        if event == 'open' and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            permit = path.is_relative_to(out) if writing else (path in named or path.is_relative_to(out) or any(path.is_relative_to(root) for root in libraries))
            if not permit: blocked.append(dict(event=event, path=str(path))); raise RuntimeError('UNDECLARED_FILE_ACCESS')
            opened.add(str(path))
        if event in {'os.remove', 'os.rmdir', 'os.mkdir', 'os.rename', 'os.replace', 'os.truncate', 'os.symlink', 'os.link'}:
            for v in args[:2] if event in {'os.rename', 'os.replace', 'os.symlink', 'os.link'} else args[:1]:
                if isinstance(v, (str, bytes, os.PathLike)) and not Path(os.fsdecode(v)).resolve().is_relative_to(out):
                    blocked.append(dict(event=event, path=os.fsdecode(v))); raise RuntimeError('INPUT_MUTATION_FORBIDDEN')
    sys.addaudithook(guard)
    result = dict(status='FAIL', started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), scientific_fits=0,
                  saved_model_loads=0, neural_forwards=0, gold_values_decoded=0, original_project_content_reads=0)
    mismatches, numeric_checks, exact_checks, max_error = [], 0, 0, 0.0

    def compare(a, b, label):
        nonlocal numeric_checks, exact_checks, max_error
        if isinstance(b, dict):
            assert isinstance(a, dict) and set(a) == set(b), 'EXACT_REFERENCE_SCHEMA:' + label
            for k in b: compare(a[k], b[k], label + '/' + k)
        elif type(a) in (int, float) and type(b) in (int, float):
            numeric_checks += 1; assert math.isfinite(a) and math.isfinite(b)
            error = abs(a-b); max_error = max(max_error, error)
            if error > 1e-12: mismatches.append(dict(field=label, expected=b, actual=a, error=error))
        else:
            exact_checks += 1
            if type(a) is not type(b) or a != b: mismatches.append(dict(field=label, expected=b, actual=a))

    def rows(path):
        answer = {}
        with path.open(encoding='utf-8') as stream:
            for line in stream:
                assert line.endswith('\n') and line.strip(); row = json.loads(line); k = key(row)
                assert k not in answer; answer[k] = row
        return answer

    try:
        producer = load(out / 'PRODUCER_RESULT.json')
        assert producer['status'] == 'PASS_FULL_RELOCATED_HISTORICAL_SCORING_PENDING_INDEPENDENT'
        assert producer['mismatch_count'] == 0 and not producer['guard']['blocked'] and not producer['guard']['forbidden_calls']
        assert len(producer['guard']['model_load_calls']) == 8
        replay = rows(out / 'HISTORICAL_REPLAY_PRIVATE.jsonl')
        pairs, scores, decisions = [rows(paths[name]) for name in ('pairs', 'scores', 'decisions')]
        seal = load(paths['decision_seal'])
        assert len(replay) == len(scores) == len(decisions) == 13500 and len(pairs) == 3202
        assert set(replay) == set(scores) == set(decisions) and set(pairs) <= set(replay)
        assert len({(k[0], k[2]) for k in replay}) == 4500
        assert set(collections.Counter(k[:2] for k in replay).values()) == {1500}
        expected_fields = {'dataset', 'retriever', 'sample_id', 'pair', 'scores', 'forced_keep_reason', 'v2_score', 'hgb_action', 'v2_action'}
        reasons = collections.Counter()
        for k in sorted(replay):
            r, d = replay[k], decisions[k]; assert set(r) == expected_fields
            compare(r['scores'], scores[k]['scores'], str(k) + '/scores')
            compare(r['v2_score'], d['v2_score'], str(k) + '/v2_score')
            compare(r['hgb_action'], d['hgb_action'], str(k) + '/hgb_action')
            compare(r['v2_action'], d['action'], str(k) + '/v2_action')
            compare(r['forced_keep_reason'], d['forced_keep_reason'], str(k) + '/reason')
            if k in pairs:
                assert d['v2_eligible_and_scorable'] is d['hgb_eligible_and_scorable'] is True and r['forced_keep_reason'] is None
                compare(r['pair'], pairs[k], str(k) + '/pair')
                compare(r['scores']['state_symmetric_hgb'], d['hgb_score'], str(k) + '/raw_hgb')
            else:
                assert r['pair'] is None and all(v is None for v in r['scores'].values()) and r['v2_score'] is None
                assert d['v2_eligible_and_scorable'] is d['hgb_eligible_and_scorable'] is False
                reasons[r['forced_keep_reason']] += 1
        assert dict(reasons) == seal['forced_keep_counts'] == {'a1_empty': 2, 'normalized_answers_equal': 10296}
        assert seal['trace_count'] == 13500 and seal['replace_count'] == seal['hgb_replace_count'] == 675 and seal['action_rate'] == .05
        for kind in ('hgb', 'v2'):
            score = lambda k: replay[k]['scores']['state_symmetric_hgb'] if kind == 'hgb' else replay[k]['v2_score']
            chosen = set(sorted(pairs, key=lambda k: (-score(k), k))[:675])
            for k in replay: compare(replay[k][kind + '_action'], 'REPLACE' if k in chosen else 'KEEP', str(k) + '/' + kind + '_independent_top_k')
        for name, path in paths.items(): assert sha(path) == cfg['named_inputs'][name]['sha256']
        for e in inputs['producer_files']: assert sha(Path(e['path'])) == e['sha256']
        assert not blocked
        result.update(status='PASS_FULL_RELOCATED_HISTORICAL_SCORING' if not mismatches else 'FAIL_REFERENCE_COMPARISONS',
                      traces=13500, question_groups=4500, eligible_pairs=3202, forced_keep_traces=10298,
                      base_score_values=32020, v2_score_values=3202, archived_action_comparisons=27000, independent_top_k_comparisons=27000,
                      null_base_score_values=102980, numeric_checks=numeric_checks, exact_checks=exact_checks, max_numeric_error=max_error,
                      full_archived_reference_comparison=True, independent_tree_reimplementation=False, neural_replay=False,
                      current_empirical_pipeline_replay=False, producer_replay_sha256=sha(out / 'HISTORICAL_REPLAY_PRIVATE.jsonl'))
    except Exception as exc: result.update(error=repr(exc), traceback=traceback.format_exc(), failed_outputs_retained=True)
    result.update(mismatch_count=len(mismatches), blocked_events=blocked, opened_paths=sorted(opened), finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    for name, value in [('INDEPENDENT_MISMATCHES_PRIVATE.json', dict(mismatches=mismatches)), ('INDEPENDENT_RESULT.json', result)]:
        with (out / name).open('x', encoding='utf-8', newline='\n') as stream: json.dump(value, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'opened_paths'}, indent=2))
    return 0 if result['status'] == 'PASS_FULL_RELOCATED_HISTORICAL_SCORING' else 2


if __name__ == '__main__': raise SystemExit(main())
