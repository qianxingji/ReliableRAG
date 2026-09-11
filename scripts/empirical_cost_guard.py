"""Exact read-only cost surface; authenticated payloads are not decode grants."""
import os
from pathlib import Path
import sys

from scripts.empirical_pool_io import REPO


def guard(root, output, authenticated_paths, decoded_paths):
    root, output = Path(root).resolve(), Path(output).resolve()
    allowed = {Path(p).resolve() for p in authenticated_paths}
    decoded = {Path(p).resolve() for p in decoded_paths}
    if not decoded <= allowed:
        raise ValueError("All cost decode inputs must be authenticated")
    libraries = (Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
    receipt = dict(reads=set(), writes=set(), denied=[], forbidden_calls=0)
    def deny(reason):
        receipt["denied"].append(reason)
        raise RuntimeError("COST_BOUNDARY_" + reason)
    def opaque():
        frame = sys._getframe(2)
        while frame:
            if frame.f_code.co_name == "digest" and Path(frame.f_code.co_filename).resolve() == REPO / "scripts/verify_roa_artifacts.py":
                return True
            frame = frame.f_back
        return False
    def audit(event, args):
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request"}:
            deny("NETWORK_OR_SUBPROCESS")
        if event in {"os.remove", "os.rmdir", "os.rename", "os.link", "os.symlink", "os.truncate"}:
            deny("DELETE_RENAME_LINK_OR_TRUNCATE")
        if event in {"os.mkdir", "os.chmod", "os.utime"} and not Path(os.fsdecode(args[0])).resolve().is_relative_to(output):
            deny("EXTERNAL_MUTATION")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = isinstance(mode,str) and any(c in mode for c in "wax+") or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output) or flags & os.O_TRUNC:
                deny("NONEXCLUSIVE_OR_EXTERNAL_WRITE")
            receipt["writes"].add(str(path))
            return
        if opaque() and (path in allowed or path.is_relative_to(output)):
            receipt["reads"].add(str(path))
            return
        if (path.is_relative_to(root / "data/raw") or path.is_relative_to(root / "data/cache/daa_v2_hotpot_full_source") or
            path.suffix in {".safetensors", ".joblib", ".pkl", ".parquet"} or path.name == "pytorch_model.bin"):
            deny("RAW_REFERENCES_OR_MODEL")
        if path not in decoded and not path.is_relative_to(output) and not any(path.is_relative_to(p) for p in libraries):
            deny("UNLISTED_DECODED_INPUT")
        receipt["reads"].add(str(path))
    def profile(frame, event, arg):
        if event == "call" and (frame.f_code.co_name in {"fit", "partial_fit", "fit_transform", "generate", "retrieve", "encode_queries", "encode_documents"} or
            frame.f_code.co_name == "forward" and hasattr(frame.f_locals.get("self"), "parameters")):
            receipt["forbidden_calls"] += 1
            deny("MODEL_FIT_INFERENCE_OR_RETRIEVAL")
    sys.addaudithook(audit)
    sys.setprofile(profile)
    return receipt
