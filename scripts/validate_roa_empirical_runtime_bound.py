"""Disclosed binding entry for the original complete C3 independent validator."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import site
import sys


def profile_execution(events):
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
    assert hashlib.sha256(raw).hexdigest() == pin, 'BINDING_CONFIG_PIN'
    cfg = json.loads(raw)
    root = Path(cfg['project_root']).resolve()
    repo = Path(cfg['engineering_root']).resolve()
    assert root == Path('E:/paper/ReliableRAG').resolve() and repo == Path('E:/paper/ReliableRAG-cas-q2-p0-1').resolve()
    assert Path(sys.prefix).resolve() == root / '.venv' and sys.flags.isolated and sys.dont_write_bytecode and site.ENABLE_USER_SITE is False
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1' and all(os.environ[k] == '1' for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'))
    payloads = {}
    controls = {}
    for entry in cfg['controls']:
        path = Path(entry['path']);data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256'] and len(data) == entry['size_bytes']
        assert Path(entry['filename']).name == entry['filename'] and entry['filename'] not in payloads
        payloads[entry['filename']] = data;controls[entry['name']] = entry
    assert Path(controls['entry']['path']).resolve() == Path(__file__).resolve()
    acceptance = json.loads(payloads[controls['fixture_acceptance']['filename']])
    review = json.loads(payloads[controls['client_acceptance']['filename']])
    assert acceptance['status'] == 'PASS_C3_VALIDATION_BINDING_INVENTED_ONLY'
    assert review['status'] == 'ACCEPTED_C3_VALIDATION_BINDING_FOR_FULL_CURRENT_VALIDATION'
    assert review['fixture_acceptance_sha256'] == controls['fixture_acceptance']['sha256']
    for name in ('length', 'bindings', 'entry'):
        assert acceptance['tested_adapter_sources'][name] == controls[name]['sha256']
    sys.path.insert(0, str(repo))
    for name, expected in cfg['original_sources'].items():
        path = Path(expected['path']);assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256']
    assert cfg['original_sources']['current_validator']['sha256'] == '3eb99ad55f93af8beaa0d316d8892ca8747a627bb80671d358312b758638915a'
    for name in ('length', 'bindings'):
        entry = controls[name]
        expected_path = repo / 'scripts' / ('empirical_validation_length.py' if name == 'length' else 'empirical_validation_binding.py')
        assert Path(entry['path']).resolve() == expected_path and hashlib.sha256(expected_path.read_bytes()).hexdigest() == entry['sha256']
    frozen = dict(cfg, freeze_sha256=pin)
    frozen['embedded_controls'] = [{k:e[k] for k in ('filename','sha256','size_bytes')} for e in cfg['controls']]
    frozen['embedded_controls'].append(dict(filename='EXECUTION_FREEZE.json',sha256=pin,size_bytes=len(raw)))
    assert 'EXECUTION_FREEZE.json' not in payloads
    payloads['EXECUTION_FREEZE.json'] = raw
    return root, repo, frozen, payloads


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--config-sha256',required=True)
    args=parser.parse_args()
    root,repo,frozen,payloads=prepare(args.config,args.config_sha256)
    events=[];profile_execution(events)
    from scripts import validate_roa_empirical_runtime as native
    from scripts.empirical_validation_binding import ValidationBindings
    assert Path(native.__file__).resolve()==Path(frozen['original_sources']['current_validator']['path']).resolve()
    assert not (native.OUT/'INDEPENDENT_VALIDATION.json').exists() and not (native.OUT/'SHA256_MANIFEST.json').exists()
    for mode,folder in [('canonical',native.OUT),('replay',native.OUT/'replay')]:
        manifest=folder/'EXECUTION_MANIFEST.json'
        assert hashlib.sha256(manifest.read_bytes()).hexdigest()==frozen['runtime_execution_manifests'][mode]
        expected='GENERATED_PENDING_REPLAY_AND_INDEPENDENT' if mode=='canonical' else 'PASS_BOUNDED_REPLAY_PENDING_INDEPENDENT'
        assert json.loads((folder/'BUILD_RECEIPT.json').read_text(encoding='utf-8'))['status']==expected
    bindings=ValidationBindings(native,frozen,payloads,forbidden_events=events);bindings.install()
    sys.argv=[str(Path(native.__file__)), '--project-root', str(root), '--preparation-manifest-sha256',
        '7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258']
    return native.main()


if __name__=='__main__':
    raise SystemExit(main())
