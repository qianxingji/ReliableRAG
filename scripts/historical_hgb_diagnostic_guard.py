"""Read-only HGB state diagnosis; no fit, score or prediction calls."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


def install(environment, output, allowed_files, role):
    environment, output = environment.resolve(), output.resolve()
    base, windows = Path(sys.base_prefix).resolve(), Path(os.environ['SystemRoot']).resolve()
    expected = {p.resolve() for p in allowed_files}
    libraries = (environment, base, windows)
    state = dict(blocked=[], opened=set(), forbidden_calls=[], bootstrap_events=[], optional_import_refusals=[], model_load_calls=[], fit_calls=[], nested_fit_calls=[])
    active_fit = None
    fit_order = ("state_symmetric_logistic", "no_cross_state", "no_B", "no_evidence_change", "no_answer_form", "state_symmetric_hgb", "ordinary_compact_logistic")
    bootstrap_active = True
    fixes = environment / 'Lib/site-packages/sklearn/utils/fixes.py'
    fixes_sha = '5c9908a77a54970344c455b29b2e90ff014ef86f1b71ae9fdc1207f53a3ae5ab'
    sources = {base / 'Lib/platform.py': '95801e4fde8f28a7f41397551eb417d650fa584d780029660610700114efbad0',
               base / 'Lib/subprocess.py': '54356e454227e4085419f455caf5e97e9c4c99995a10ac1e5f685015eff9c038', fixes: fixes_sha}
    for p, sha in sources.items(): assert hashlib.sha256(p.read_bytes()).hexdigest() == sha
    shell = windows / 'System32/cmd.exe'
    assert Path(os.environ['COMSPEC']).resolve() == shell.resolve()

    def platform_query():
        frame = sys._getframe(1)
        while frame:
            if frame.f_code is platform._syscmd_ver.__code__ and Path(frame.f_globals.get('__file__', '')).resolve() == base / 'Lib/platform.py': return True
            frame = frame.f_back
        return False

    def allowed(path):
        return path in expected or path.is_relative_to(output) or any(path.is_relative_to(p) for p in libraries)

    def audit(event, args):
        if bootstrap_active and event in {'open', 'subprocess.Popen'} and platform_query():
            if event == 'subprocess.Popen':
                executable, command, cwd, child_env = args
                if (not any(e['event'] == event for e in state['bootstrap_events'])
                        and (executable is None or Path(executable).resolve() == shell.resolve())
                        and command == os.environ['COMSPEC'] + ' /c "ver"' and cwd is None and child_env is None):
                    state['bootstrap_events'].append(dict(event=event, command=command)); return
            if event == 'open' and not isinstance(args[0], int):
                path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
                if (path == Path(os.devnull).resolve() and mode is None and isinstance(flags, int)
                        and flags & (os.O_WRONLY | os.O_RDWR) == os.O_RDWR and not flags & (os.O_CREAT | os.O_TRUNC)
                        and sys._getframe(1).f_code is subprocess.Popen._get_devnull.__code__
                        and not any(e['event'] == 'nul_capability_open' for e in state['bootstrap_events'])):
                    state['bootstrap_events'].append(dict(event='nul_capability_open', path=str(path))); return
        if event == 'import' and args[0] == 'pyarrow' and not bootstrap_active:
            caller = sys._getframe(1)
            if (not state['optional_import_refusals'] and caller.f_globals.get('__name__') == 'sklearn.utils.fixes'
                    and caller.f_code.co_name == '<module>' and Path(caller.f_globals.get('__file__', '')).resolve() == fixes.resolve()):
                state['optional_import_refusals'].append(dict(module='pyarrow', source_sha256=fixes_sha, action='Absent optional target: ModuleNotFoundError'))
                raise ModuleNotFoundError('PyArrow target absent from historical CPU replay', name='pyarrow')
        if event == 'import' and args[0].split('.')[0] in {'torch', 'transformers', 'datasets', 'sentencepiece', 'pyarrow', 'faiss'}:
            state['blocked'].append(dict(event=event, module=args[0])); raise RuntimeError('NEURAL_OR_RAW_DATA_IMPORT_FORBIDDEN')
        if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.sendto', 'subprocess.Popen', 'os.system', 'urllib.Request'}:
            state['blocked'].append(dict(event=event)); raise RuntimeError('NETWORK_OR_PROCESS_FORBIDDEN')
        if event == 'open' and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if (writing and not path.is_relative_to(output)) or (not writing and not allowed(path)):
                state['blocked'].append(dict(event=event, path=str(path), writing=bool(writing))); raise RuntimeError('UNDECLARED_FILE_ACCESS')
            state['opened'].add(str(path))
        if event in {'os.remove', 'os.rmdir', 'os.mkdir', 'os.rename', 'os.replace', 'os.truncate', 'os.symlink', 'os.link'}:
            for v in args[:2] if event in {'os.rename', 'os.replace', 'os.symlink', 'os.link'} else args[:1]:
                if isinstance(v, (str, bytes, os.PathLike)) and not Path(os.fsdecode(v)).resolve().is_relative_to(output):
                    state['blocked'].append(dict(event=event, path=os.fsdecode(v))); raise RuntimeError('INPUT_OR_ENVIRONMENT_MUTATION_FORBIDDEN')

    forbidden = {'fit', 'fit_transform', 'partial_fit', 'from_pretrained', 'forward', '_ensure_loaded',
                 'scores', 'swapped_scores', 'decision_function', 'predict', 'predict_proba', 'staged_predict', 'staged_predict_proba', 'encode', 'generate', 'generate_answer', 'generate_repair_query', 'score_likelihoods', 'restore_dataset', 'frozen_inputs'}

    def profile(frame, event, arg):
        nonlocal active_fit
        module, name = frame.f_globals.get('__name__'), frame.f_code.co_name
        if module is None: return
        if module == 'src.mars.full_experiment' and name == '_fit_model':
            if event == 'call':
                i = len(state['fit_calls'])
                assert role == 'producer' and active_fit is None and i < 7
                v = frame.f_locals
                assert v['name'] == fit_order[i] and v['seed'] == 20261829 + i and len(v['records']) == len(v['labels']) == 601
                active_fit = i
                row = dict(index=i, name=v['name'], seed=v['seed'], rows=601,
                    records_sha256=hashlib.sha256(json.dumps(v['records'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
                    labels_sha256=hashlib.sha256(json.dumps(v['labels'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
                    source=frame.f_code.co_filename, completed=False)
                state['fit_calls'].append(row)
                with (output / 'FIT_ATTEMPTS_PRIVATE.jsonl').open('a',encoding='utf-8') as f:
                    f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
            elif event == 'return':
                assert active_fit is not None
                state['fit_calls'][active_fit]['completed'] = arg is not None
                active_fit = None
            return
        if event != 'call': return
        if module.startswith('sklearn.') and name in {'fit','fit_transform','partial_fit'}:
            assert role == 'producer' and active_fit is not None, 'UNDECLARED_ESTIMATOR_FIT'
            x,y=frame.f_locals.get('X'),frame.f_locals.get('y')
            def arr(v):
                if v is None:return None
                assert hasattr(v,'tobytes') and hasattr(v,'dtype')
                return dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.tobytes(order='C')).hexdigest())
            state['nested_fit_calls'].append(dict(index=active_fit,module=module,name=name,
                estimator=type(frame.f_locals.get('self')).__name__,X=arr(x),y=arr(y)))
            return
        if module.startswith(('src.', 'sklearn.', 'torch.', 'transformers.', 'accepted_', 'delivery_')) and name in forbidden:
            state['forbidden_calls'].append(dict(module=module,name=name));raise RuntimeError('UNDECLARED_FIT_OR_NEURAL_EXECUTION_FORBIDDEN')
        if module == 'joblib.numpy_pickle' and name == 'load':
            path=Path(frame.f_locals['filename']).resolve()
            assert path.suffix=='.joblib' and (path in expected or path.parent==output/'models')
            state['model_load_calls'].append(str(path))

    def bootstrap():
        nonlocal bootstrap_active
        try: value = platform.uname()._asdict()
        finally: bootstrap_active = False
        assert len(state['bootstrap_events']) == 2
        return value

    sys.addaudithook(audit); sys.setprofile(profile)
    return state, bootstrap, allowed
