"""Historical reference replay with the exact new Arrow target; no model or fit."""
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import sys


def install(environment, output, allowed_files, hash_only=(), opaque_code=None):
    environment, output = environment.resolve(), output.resolve()
    base, windows = Path(sys.base_prefix).resolve(), Path(os.environ['SystemRoot']).resolve()
    expected = {p.resolve() for p in allowed_files}
    opaque_only = {p.resolve() for p in hash_only}
    arrow = Path('E:/paper/ReliableRAG-neural-targets-v1/pyarrow').resolve()
    libraries = (environment, base, windows, arrow)
    state = dict(blocked=[], opened=set(), forbidden_calls=[], bootstrap_events=[], optional_import_refusals=[], model_load_calls=[])
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
        if event == 'import' and args[0].split('.')[0] in {'torch', 'transformers', 'datasets', 'sentencepiece', 'faiss', 'sklearn', 'joblib'}:
            state['blocked'].append(dict(event=event, module=args[0])); raise RuntimeError('NEURAL_OR_RAW_DATA_IMPORT_FORBIDDEN')
        if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.sendto', 'subprocess.Popen', 'os.system', 'urllib.Request'}:
            state['blocked'].append(dict(event=event)); raise RuntimeError('NETWORK_OR_PROCESS_FORBIDDEN')
        if event == 'open' and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if not writing and path in opaque_only:
                caller=sys._getframe(1)
                while caller and caller.f_code is not opaque_code:caller=caller.f_back
                if caller is None:
                    state['blocked'].append(dict(event=event,path=str(path),reason='ARCHIVED_NUMERIC_DECODE_IN_PRODUCER'))
                    raise RuntimeError('ARCHIVED_NUMERIC_DECODE_IN_PRODUCER')
            if (writing and not path.is_relative_to(output)) or (not writing and not allowed(path)):
                state['blocked'].append(dict(event=event, path=str(path), writing=bool(writing))); raise RuntimeError('UNDECLARED_FILE_ACCESS')
            state['opened'].add(str(path))
        if event in {'os.remove', 'os.rmdir', 'os.mkdir', 'os.rename', 'os.replace', 'os.truncate', 'os.symlink', 'os.link'}:
            for v in args[:2] if event in {'os.rename', 'os.replace', 'os.symlink', 'os.link'} else args[:1]:
                if isinstance(v, (str, bytes, os.PathLike)) and not Path(os.fsdecode(v)).resolve().is_relative_to(output):
                    state['blocked'].append(dict(event=event, path=os.fsdecode(v))); raise RuntimeError('INPUT_OR_ENVIRONMENT_MUTATION_FORBIDDEN')

    forbidden = {'fit', 'fit_transform', 'partial_fit', 'from_pretrained', 'forward', '_ensure_loaded',
                 'predict', 'predict_proba', 'decision_function', 'encode', 'generate', 'generate_answer', 'generate_repair_query', 'score_likelihoods', 'restore_dataset', 'frozen_inputs'}

    def profile(frame, event, arg):
        if event != 'call': return
        module, name = frame.f_globals.get('__name__'), frame.f_code.co_name
        if module is None: return
        if module.startswith(('src.', 'sklearn.', 'torch.', 'transformers.', 'accepted_', 'delivery_')) and name in forbidden:
            state['forbidden_calls'].append(dict(module=module, name=name)); raise RuntimeError('FIT_OR_NEURAL_EXECUTION_FORBIDDEN')
        if module == 'joblib.numpy_pickle' and name == 'load':
            path = Path(frame.f_locals['filename']).resolve()
            assert path in expected and path.suffix == '.joblib'
            state['model_load_calls'].append(str(path))

    def bootstrap():
        nonlocal bootstrap_active
        try: value = platform.uname()._asdict()
        finally: bootstrap_active = False
        assert len(state['bootstrap_events']) == 2
        return value

    sys.addaudithook(audit); sys.setprofile(profile)
    return state, bootstrap, allowed
