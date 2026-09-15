"""NLI preparation boundary: add only the pinned new SentencePiece target."""
import hashlib
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys


def install(environment, output, permitted):
    base = Path(sys.base_prefix).resolve()
    windows = Path(os.environ['SystemRoot']).resolve()
    allowed_files = {p.resolve() for p in permitted}
    sentencepiece_target = Path('E:/paper/ReliableRAG-neural-targets-v1/sentencepiece').resolve()
    assert sentencepiece_target.is_dir()
    libraries = (environment.resolve(), sentencepiece_target, base, windows)
    state = dict(blocked=[], opened=set(), forbidden_calls=[], bootstrap_events=[], capability_events=[], capability_sockets=[])
    bootstrap_active = True
    sources = {base / 'Lib/platform.py': '95801e4fde8f28a7f41397551eb417d650fa584d780029660610700114efbad0',
               base / 'Lib/subprocess.py': '54356e454227e4085419f455caf5e97e9c4c99995a10ac1e5f685015eff9c038'}
    connection = environment / 'Lib/site-packages/urllib3/util/connection.py'
    connection_sha = '2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74'
    sources[connection] = connection_sha
    for path, expected in sources.items(): assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    shell = windows / 'System32/cmd.exe'
    assert Path(os.environ['COMSPEC']).resolve() == shell.resolve()

    def platform_query():
        frame = sys._getframe(1)
        while frame:
            if frame.f_code is platform._syscmd_ver.__code__ and Path(frame.f_globals.get('__file__', '')).resolve() == base / 'Lib/platform.py': return True
            frame = frame.f_back
        return False

    def allowed(path):
        return path in allowed_files or path.is_relative_to(output) or any(path.is_relative_to(root) for root in libraries)

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
        if event == 'socket.bind':
            caller = sys._getframe(1); sock, address = args[:2]; function = caller.f_globals.get('_has_ipv6')
            if (not state['capability_events'] and address == ('::1', 0) and sock.family == socket.AF_INET6 and sock.type == socket.SOCK_STREAM
                    and caller.f_globals.get('__name__') == 'urllib3.util.connection'
                    and Path(caller.f_globals.get('__file__', '')).resolve() == connection.resolve()
                    and function is not None and getattr(function, '__code__', None) is caller.f_code and caller.f_code.co_name == '_has_ipv6'):
                state['capability_events'].append(dict(event=event, address=address, source_sha256=connection_sha))
                state['capability_sockets'].append(sock); return
        if event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.sendto', 'subprocess.Popen', 'os.system', 'urllib.Request', 'pickle.find_class'}:
            state['blocked'].append(dict(event=event)); raise RuntimeError('NETWORK_PROCESS_OR_DESERIALIZATION_FORBIDDEN')
        if event == 'open' and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            weight = path.suffix.lower() in {'.safetensors', '.bin', '.pt', '.pth', '.pkl', '.pickle', '.joblib', '.npy', '.arrow', '.parquet'} and not any(path.is_relative_to(root) for root in libraries)
            if weight or (writing and not path.is_relative_to(output)) or (not writing and not allowed(path)):
                state['blocked'].append(dict(event=event, path=str(path), writing=bool(writing))); raise RuntimeError('UNDECLARED_OR_WEIGHT_FILE_ACCESS')
            state['opened'].add(str(path))
        if event in {'os.remove', 'os.rmdir', 'os.mkdir', 'os.rename', 'os.replace', 'os.truncate', 'os.symlink', 'os.link'}:
            for value in args[:2] if event in {'os.rename', 'os.replace', 'os.symlink', 'os.link'} else args[:1]:
                if isinstance(value, (str, bytes, os.PathLike)) and not Path(os.fsdecode(value)).resolve().is_relative_to(output):
                    state['blocked'].append(dict(event=event, path=os.fsdecode(value))); raise RuntimeError('EXTERNAL_MUTATION')

    forbidden = {'fit', 'fit_transform', 'partial_fit', 'forward', 'generate', 'generate_answer', 'generate_repair_query', '_ensure_loaded', '_lazy_init', 'load', 'load_state_dict'}

    def profile(frame, event, arg):
        if event != 'call': return
        module, name = frame.f_globals.get('__name__', '') or '', frame.f_code.co_name
        bad_factory = name == 'from_pretrained' and module.startswith('transformers.') and ('modeling' in module or 'auto_factory' in module)
        if bad_factory or (module.startswith(('src.', 'torch.', 'sklearn.', 'joblib.', 'transformers.')) and name in forbidden):
            state['forbidden_calls'].append(dict(module=module, name=name)); raise RuntimeError('FIT_MODEL_OR_NEURAL_CALL_FORBIDDEN')

    def bootstrap():
        nonlocal bootstrap_active
        try: value = platform.uname()._asdict()
        finally: bootstrap_active = False
        assert len(state['bootstrap_events']) == 2
        return value

    sys.addaudithook(audit); sys.setprofile(profile)
    return state, bootstrap, allowed
