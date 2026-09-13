"""V2 entry: original C3 validator plus accepted length and helper-constant bindings."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import site
import sys


def profile_execution(events):
    """Fail closed if the tokenizer-only validation enters model/fit/CUDA code."""
    def observe(frame, event, arg):
        if event != 'call':
            return
        module = frame.f_globals.get('__name__')
        if not isinstance(module, str):
            return
        name = frame.f_code.co_name
        forbidden = ((module.startswith('torch.nn.') and name in {'forward', '_call_impl', '_wrapped_call_impl'}) or
            (module.startswith('torch.cuda') and name == '_lazy_init') or
            (module in {'transformers.modeling_utils', 'transformers.models.auto.auto_factory'} and name == 'from_pretrained') or
            (module.startswith('sklearn.') and name in {'fit', 'fit_transform', 'partial_fit'}))
        if forbidden:
            events.append(dict(module=module, function=name))
            raise RuntimeError('MODEL_FIT_FORWARD_OR_CUDA_FORBIDDEN')
    sys.setprofile(observe)


def prepare(config, pin):
    raw = config.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin, 'V2_BINDING_CONFIG_PIN'
    cfg = json.loads(raw)
    root = Path(cfg['project_root']).resolve()
    repo = Path(cfg['engineering_root']).resolve()
    assert root == Path('E:/paper/ReliableRAG').resolve()
    assert repo == Path('E:/paper/ReliableRAG-cas-q2-p0-1').resolve()
    assert Path(sys.prefix).resolve() == root / '.venv'
    assert sys.flags.isolated and sys.dont_write_bytecode and site.ENABLE_USER_SITE is False
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
    assert all(os.environ[name] == '1' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'))
    payloads = {}
    controls = {}
    for entry in cfg['controls']:
        path = Path(entry['path']); data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256'] and len(data) == entry['size_bytes']
        assert Path(entry['filename']).name == entry['filename'] and entry['filename'] not in payloads
        payloads[entry['filename']] = data; controls[entry['name']] = entry
    assert Path(controls['entry_v2']['path']).resolve() == Path(__file__).resolve()
    v1 = json.loads(payloads[controls['v1_fixture_acceptance']['filename']])
    v1_review = json.loads(payloads[controls['v1_client_acceptance']['filename']])
    v2 = json.loads(payloads[controls['v2_fixture_acceptance']['filename']])
    v2_review = json.loads(payloads[controls['v2_client_acceptance']['filename']])
    assert v1['status'] == 'PASS_C3_VALIDATION_BINDING_INVENTED_ONLY'
    assert v1_review['status'] == 'ACCEPTED_C3_VALIDATION_BINDING_FOR_FULL_CURRENT_VALIDATION'
    assert v2['status'] == 'PASS_C3_VALIDATION_V2_INVENTED_ONLY'
    assert v2_review['status'] == 'ACCEPTED_C3_VALIDATION_V2_FOR_ONE_FULL_RUN'
    for name in ('binding_v2','entry_v2','fixture_v2'):
        assert v2['tested_v2_sources'][name] == controls[name]['sha256']
    assert v2_review['fixture_manifest_sha256'] == controls['v2_fixture_manifest']['sha256']
    relocation = json.loads(payloads[controls['relocation_receipt']['filename']])
    assert relocation['status'] == 'PASS_FAILED_REPORT_PRESERVED_AND_RELOCATED'
    assert relocation['source_absent_after_move'] and relocation['runtime_initial_namespace_restored']
    sys.path.insert(0, str(repo))
    for expected in cfg['original_sources'].values():
        path = Path(expected['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256'] and path.stat().st_size == expected['size_bytes']
    assert cfg['original_sources']['current_validator']['sha256'] == '3eb99ad55f93af8beaa0d316d8892ca8747a627bb80671d358312b758638915a'
    for name, source in (('length_v1','empirical_validation_length.py'),
                         ('binding_v1','empirical_validation_binding.py'),
                         ('entry_v1','validate_roa_empirical_runtime_bound.py'),
                         ('binding_v2','empirical_validation_binding_v2.py')):
        entry = controls[name]; path = repo / 'scripts' / source
        assert Path(entry['path']).resolve() == path.resolve()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    frozen = dict(cfg, freeze_sha256=pin)
    frozen['embedded_controls'] = [{key:entry[key] for key in ('filename','sha256','size_bytes')}
        for entry in cfg['controls']]
    frozen['embedded_controls'].append(dict(filename='EXECUTION_FREEZE.json',
        sha256=pin, size_bytes=len(raw)))
    assert 'EXECUTION_FREEZE.json' not in payloads
    payloads['EXECUTION_FREEZE.json'] = raw
    return root, repo, frozen, payloads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    args = parser.parse_args()
    root, repo, frozen, payloads = prepare(args.config, args.config_sha256)
    events = []; profile_execution(events)
    from scripts import validate_roa_empirical_runtime as native
    from scripts.empirical_validation_binding_v2 import V2ValidationBindings
    assert Path(native.__file__).resolve() == Path(frozen['original_sources']['current_validator']['path']).resolve()
    assert not (native.OUT / 'INDEPENDENT_VALIDATION.json').exists()
    assert not (native.OUT / 'SEAL.json').exists() and not (native.OUT / 'SHA256_MANIFEST.json').exists()
    assert not (native.OUT / 'validation_execution').exists()
    for mode, folder in [('canonical',native.OUT),('replay',native.OUT/'replay')]:
        manifest = folder / 'EXECUTION_MANIFEST.json'
        assert hashlib.sha256(manifest.read_bytes()).hexdigest() == frozen['runtime_execution_manifests'][mode]
        expected = 'GENERATED_PENDING_REPLAY_AND_INDEPENDENT' if mode == 'canonical' else 'PASS_BOUNDED_REPLAY_PENDING_INDEPENDENT'
        assert json.loads((folder/'BUILD_RECEIPT.json').read_text(encoding='utf-8'))['status'] == expected
    binding = V2ValidationBindings(native, frozen, payloads, forbidden_events=events)
    binding.install()
    sys.argv = [str(Path(native.__file__)), '--project-root', str(root),
        '--preparation-manifest-sha256', '7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258']
    return native.main()


if __name__ == '__main__':
    raise SystemExit(main())
