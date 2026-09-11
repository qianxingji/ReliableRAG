"""C3 variant of the accepted C2 Python guard: Qwen/BGE and tokenizer-only modes."""
import os
from pathlib import Path
import sys
from scripts.empirical_runtime_io import REPO, POOL, RETRIEVAL, PREPARATION


def guard(root, output, paths, *, gpu_only=False, tokenizer_only=False):
    """Python audit guard, not a native-extension or system-wide sandbox."""
    allowed = {Path(p).resolve() for p in paths}
    models = (root / "data/models/huggingface/models--BAAI--bge-base-en-v1.5",
              root / "data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct")
    temp_root = output / "cache/tmp"
    receipt = dict(reads=set(), writes=set(), denied=[], temp_cleanup_events=0)
    def opaque():
        frame = sys._getframe(2)
        while frame:
            if frame.f_code.co_name == "digest" and Path(frame.f_code.co_filename).resolve() == REPO / "scripts/verify_roa_artifacts.py":
                return True
            frame = frame.f_back
        return False
    def deny(message):
        receipt["denied"].append(message)
        raise RuntimeError("C3 boundary: " + message)
    def hook(event, args):
        if event == "import" and (args[0] == "src" or args[0].startswith("src.")):
            deny("original pipeline package import")
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request"}:
            deny(event)
        if event in {"os.remove", "os.rmdir"}:
            path = Path(os.fsdecode(args[0])).resolve()
            if not path.is_relative_to(temp_root) or path == temp_root:
                deny("delete outside ephemeral temp")
            receipt["temp_cleanup_events"] += 1
        if event == "os.link":
            source, dest = (Path(os.fsdecode(x)).resolve() for x in args[:2])
            if not (source.is_relative_to(temp_root) and dest.parent == source.parent and
                    source.name == "probe-source" and dest.name == "probe-link" and source.is_file() and not dest.exists()):
                deny("link outside library probe")
        if event in {"os.rename", "os.symlink"}:
            deny("move or symlink")
        if event in {"os.mkdir", "os.chmod", "os.utime", "os.truncate"}:
            if not Path(os.fsdecode(args[0])).resolve().is_relative_to(output):
                deny("mutation outside output")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output): deny("write outside output")
            if flags & os.O_TRUNC and not path.is_relative_to(output / "cache"): deny("artifact overwrite")
            receipt["writes"].add(str(path)); return
        if path.is_relative_to(root / "data/raw"): deny("raw benchmark read")
        if path.is_relative_to(root / "data/models") and not any(path.is_relative_to(m) for m in models) and not opaque():
            deny("non-Qwen/BGE model read")
        if tokenizer_only and path.suffix in {".safetensors", ".bin", ".joblib", ".pkl"} and not opaque():
            deny("weight deserialization in tokenizer-only validation")
        if gpu_only and any(path.is_relative_to(folder) for folder in (POOL, RETRIEVAL, PREPARATION)) and path.suffix in {".jsonl", ".npy"} and not opaque():
            deny("benchmark text in GPU preflight")
        if path.is_relative_to(root) or path.is_relative_to(REPO):
            if not (path in allowed or path.is_relative_to(output) or path.is_relative_to(root / ".venv") or any(path.is_relative_to(m) for m in models)):
                deny("unlisted project read")
        receipt["reads"].add(str(path))
    sys.addaudithook(hook)
    return receipt

