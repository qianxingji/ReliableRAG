"""Authenticated transport and source selection only; shared by both processes."""
import ast
import collections
import dataclasses
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import site
import sys
import types


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def jsha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f: json.dump(value, f, indent=2, allow_nan=False); f.write('\n')


def load_module(name, path):
    module = types.ModuleType(name); module.__file__ = str(path); sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def setup(config, expected, role):
    assert sha(config) == expected
    cfg = json.loads(config.read_text(encoding='utf-8')); out = config.parent.resolve(); env = Path(cfg['environment']).resolve()
    assert Path(sys.prefix).resolve() == env and site.ENABLE_USER_SITE is False and sys.flags.isolated and sys.dont_write_bytecode
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1' and os.environ['OMP_NUM_THREADS'] == '1'
    controls = {e['name']: e for e in cfg['controls']}
    for e in controls.values(): assert sha(Path(e['path'])) == e['sha256'] and Path(e['path']).stat().st_size == e['size_bytes']
    assert Path(sys.argv[0]).resolve() == Path(controls[role]['path']).resolve()
    adapter = load_module('tokenizer_delivery_paths', Path(controls['adapter']['path']))
    guard = load_module('tokenizer_boundary', Path(controls['guard']['path']))
    files = adapter.BoundFiles({k: adapter.RootBinding(v['logical'], Path(v['physical'])) for k, v in cfg['roots'].items()}, cfg['files'])
    permitted = [files.checked(e['logical_path']) for e in cfg['files']]
    named = {name: files.checked(e['logical_path']) for name, e in cfg['named_inputs'].items()}
    state, bootstrap, allowed = guard.install(env, out, permitted + [Path(e['path']) for e in controls.values()] + [config])
    result = dict(status='FAIL', role=role, config_sha256=expected, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  scientific_fits=0, neural_forwards=0, pretrained_model_loads=0, historical_gold_values=0, fresh_gold_values=0,
                  new_generated_predictions=0, original_project_content_reads=0, ast_nodes=[])
    result['platform_bootstrap'] = bootstrap()
    return cfg, out, env, named, state, allowed, result


def take(module, path, names, records):
    tree = ast.parse(path.read_text(encoding='utf-8-sig')); chosen = []
    for node in tree.body:
        name = getattr(node, 'name', None)
        if isinstance(node, ast.Assign) and len(node.targets) == 1: name = getattr(node.targets[0], 'id', None)
        if name in names:
            chosen.append(node); records.append(dict(path=str(path), name=name, ast_sha256=hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()))
    assert len(chosen) == len(names)
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future] + chosen, type_ignores=[])), str(path), 'exec'), module.__dict__)


def namespace(name):
    m = types.ModuleType(name); sys.modules[name] = m
    m.__dict__.update(collections=collections, hashlib=hashlib, json=json, re=re, math=math,
                      dataclass=dataclasses.dataclass, field=dataclasses.field, replace=dataclasses.replace)
    return m


def tokenizer(named, result):
    import torch
    import transformers
    import tokenizers
    from transformers import AutoTokenizer
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized()
    snapshot = named['qwen_tokenizer'].parent
    value = AutoTokenizer.from_pretrained(str(snapshot), revision='aa8e72537993ba99e69dfaafa59ed015b17504d1', local_files_only=True, trust_remote_code=False)
    if value.pad_token_id is None: value.pad_token_id = value.eos_token_id
    value.padding_side = 'left'
    pre = json.loads(named['runtime_config'].read_text(encoding='utf-8'))
    assert sha(named['runtime_config']) == '9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9'
    template_sha = hashlib.sha256(value.chat_template.encode('utf-8')).hexdigest()
    assert template_sha == pre['runtime_config']['tokenizer_chat_template_sha256']
    result['tokenizer'] = dict(model_id='Qwen/Qwen2.5-3B-Instruct', revision='aa8e72537993ba99e69dfaafa59ed015b17504d1', physical_snapshot=str(snapshot),
        logical_tokenizer_path='E:/paper/ReliableRAG/' + named['qwen_tokenizer'].relative_to(Path(result['original_physical_root'])).as_posix(),
        class_name=type(value).__name__, vocab_size=len(value), padding_side=value.padding_side, eos_token_id=value.eos_token_id,
        pad_token_id=value.pad_token_id, chat_template_sha256=template_sha,
        versions=dict(torch=torch.__version__, transformers=transformers.__version__, tokenizers=tokenizers.__version__),
        core_paths={m.__name__:str(Path(m.__file__).resolve()) for m in (torch, transformers, tokenizers)}, local_files_only=True, trust_remote_code=False)
    return value, pre


def finish(result, state, allowed, out, filename):
    import torch
    result['torch_cuda_initialized'] = torch.cuda.is_initialized()
    closed = all(sock.fileno() == -1 for sock in state['capability_sockets'])
    modules = {}
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if isinstance(path, str) and not path.startswith('<'):
            p = Path(path).resolve(); assert allowed(p), ('MODULE_OUTSIDE_ALLOWED_ROOT', name, str(p)); modules[name] = str(p)
    result.update(blocked_events=state['blocked'], forbidden_calls=state['forbidden_calls'], bootstrap_events=state['bootstrap_events'],
        capability_events=state['capability_events'], capability_sockets_closed=closed, opened_paths=sorted(state['opened']),
        loaded_modules=modules, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if state['blocked'] or state['forbidden_calls'] or not closed or result['torch_cuda_initialized']: result['status'] = 'FAIL'
    write(out / filename, result)
