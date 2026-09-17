"""Byte-bound inputs and fail-closed private namespace IO, with no model code."""
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
DHC = OUT.parent / 'dual_head_constrained_v1'
PRE = ROOT / 'outputs/daa_v2_fresh_v1/prelabel_seal_v3'
SOURCES = {'base': PRE/'scoring/v2_base_scores.jsonl', 'gbv': PRE/'scoring/gbv_scores.jsonl',
           'actions': PRE/'decisions/v2_actions.jsonl',
           'outcomes': ROOT/'outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl'}
DOCS = ['docs/CODEX_TASK_DAA_V3_RECOVERY_ONLY_ISOLATION.md',
        'docs/V3_RECOVERY_ONLY_ISOLATION_PROTOCOL.md', 'docs/V3_ARCHITECTURE_REVIEW_AFTER_DHC.md']
COMMIT = 'cd06659739810f9d0ff5dcd0e646264a26de3109'
MANIFESTS = {
    'failure_audit_v1': 'ca890988ce01be975a0ed8d04ca9ecd8a4f3b2680d8deaa51025097fa62a9cee',
    'risk_head_comparison_v1': '2ca0d4a8bf5c61e7285860617ebe5856f833d916343b6a4a00daedc18503fb7d',
    'risk_gated_policy_v1': '864667f608a402b6fb3df07f1c8d19de73789146237338f691d280b676072b55',
    'dual_head_constrained_v1': '3a5f5cd9dcdc70b22c4a4c46545b9bf080fbe5d14c45e291fa867b489d2bcada'}
ANCHORS = {
    'AUTHOR_REPORT.md': '184cb2491837ac6fac7f2373af840ab7c907f6ef402083e18e0ba98e4f84f015',
    'INDEPENDENT_VALIDATION.json': '16c3aa52dd9de337afe57d388fd8bc8da6d086fac1f645f7a1f85a41c9039d8b',
    'DUAL_HEAD_DEVELOPMENT_SEAL.json': '59f6da26ba30ca751ccea010de1d67728fee4dd53a143d1b00ff169ae231d266'}

def now(): return datetime.now(timezone.utc).isoformat()
def require(ok, message):
    if not ok: raise RuntimeError(message)
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()
def rec(path):
    p = Path(path)
    return dict(path=p.relative_to(ROOT).as_posix(), size_bytes=p.stat().st_size, sha256=sha(p))
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def check(r):
    p = ROOT/r['path']
    require(p.is_file() and p.stat().st_size == r['size_bytes'] and sha(p) == r['sha256'], 'HASH_MISMATCH:'+r['path'])
def dest(name):
    p = (OUT/name).resolve()
    require(p.is_relative_to(OUT), 'WRITE_OUTSIDE_NAMESPACE')
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
def write(name, obj):
    with dest(name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        f.write('\n')
def write_text(name, text):
    with dest(name).open('x', encoding='utf-8', newline='\n') as f: f.write(text)
def write_lines(name, rows):
    with dest(name).open('x', encoding='utf-8', newline='\n') as f:
        for r in rows: f.write(json.dumps(r, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n')
def lines(path):
    with Path(path).open(encoding='utf-8') as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def key(r): return tuple(r[n] for n in ('dataset', 'retriever', 'sample_id'))
def keyed(path):
    rows = {}
    for r in lines(path):
        k = key(r); require(k not in rows, 'DUPLICATE_KEY'); rows[k] = r
    return rows
def keydict(k): return dict(zip(('dataset', 'retriever', 'sample_id'), k))
def kh(keys):
    h = hashlib.sha256()
    for k in sorted(keys): h.update((json.dumps(list(k), ensure_ascii=False, separators=(',', ':'))+'\n').encode('utf-8'))
    return h.hexdigest()
def parents():
    records = {}; manifests = []
    for name, expected in MANIFESTS.items():
        p = OUT.parent/name/'SHA256_MANIFEST.json'
        require(sha(p) == expected, 'PARENT_MANIFEST:'+name)
        rr = load(p)['files']
        require(len(rr) == len({r['path'] for r in rr}), 'PARENT_DUPLICATES')
        require({ROOT/r['path'] for r in rr}|{p} == {q for q in p.parent.rglob('*') if q.is_file()}, 'PARENT_PATH_SET:'+name)
        for r in rr+[rec(p)]: check(r); records[r['path']] = r
        manifests.append(dict(manifest=rec(p), payload_files=len(rr)))
    for name, expected in ANCHORS.items(): require(sha(DHC/name) == expected, 'DHC_ANCHOR:'+name)
    seal = load(DHC/'DUAL_HEAD_DEVELOPMENT_SEAL.json')
    require(seal['status'] == 'PASS' and seal['hard_stop'] is True and seal['decision'] == 'INCONCLUSIVE_DUAL_HEAD_STAGE', 'DHC_TERMINAL')
    require(load(DHC/'DEVELOPMENT_DECISION.json')['decision'] == seal['decision'], 'DHC_DECISION')
    require(load(DHC/'INDEPENDENT_VALIDATION.json')['status'] == 'PASS', 'DHC_INDEPENDENT')
    # Include the original DHC source anchors and bound executable inputs; never execute parent code.
    original = load(DHC/'INPUT_VERIFICATION.json')
    for r in list(original['anchors'].values()) + original['task_and_protocol'] + load(DHC/'EXECUTABLE_CONFIG_FREEZE_R1.json')['files']:
        check(r); records[r['path']] = r
    expected_sources = dict(actions='2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065',
        base='d3842c514224354206846edb7e96b7296765d67050b131b552f469d0c64fa609',
        gbv='c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca',
        outcomes='2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576')
    for name, p in SOURCES.items():
        require(sha(p) == expected_sources[name], 'SOURCE:'+name); records[rec(p)['path']] = rec(p)
    return dict(status='PASS', files=[records[n] for n in sorted(records)], manifests=manifests,
                DHC_decision=seal['decision'], DHC_hard_stop=True, blocked_prefit_receipts_preserved=True)
def frozen():
    r = load(OUT/'EXECUTABLE_CONFIG_FREEZE.json')
    for item in r['files']: check(item)
    return r
def guard(records):
    exact = {(ROOT/r['path']).resolve() for r in records} | set(SOURCES.values()) | {(ROOT/n).resolve() for n in DOCS}
    runtime = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    access = dict(read_paths=set(), write_paths=set(), blocked=[])
    def audit(event, args):
        if event in ('socket.connect', 'socket.bind', 'subprocess.Popen', 'os.system'):
            access['blocked'].append(event); raise RuntimeError('FORBIDDEN:'+event)
        if event != 'open' or isinstance(args[0], int): return
        p = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
        writing = bool((isinstance(mode, str) and any(c in mode for c in 'wax+')) or
                       (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
        ok = p.is_relative_to(OUT) if writing else p in exact or p.is_relative_to(OUT) or any(p.is_relative_to(d) for d in runtime)
        if not ok: access['blocked'].append(str(p)); raise RuntimeError('UNAPPROVED_FILE:'+str(p))
        if p.is_relative_to(ROOT): access['write_paths' if writing else 'read_paths'].add(p.relative_to(ROOT).as_posix())
    sys.addaudithook(audit)
    return access
def guard_receipt(a): return {k: sorted(v) if isinstance(v, set) else v for k, v in a.items()}
