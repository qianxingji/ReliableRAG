"""D boundaries separate selected-label mapping from numeric-only analysis."""
import os
from pathlib import Path
import sys

from scripts.empirical_pool_io import REPO


def guard(root, output, paths, *, mode):
    if mode not in {"audit", "mapping", "outcome_validation", "analysis", "analysis_validation"}:
        raise ValueError("Fixed D process mode")
    root, output = Path(root).resolve(), Path(output).resolve()
    allowed = {Path(p).resolve() for p in paths}
    libraries = (Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
    receipt = dict(mode=mode, reads=set(), writes=set(), denied=[], forbidden_calls=0)
    policy = REPO / "outputs/cas_q2/empirical_prelabel_policies_v1"
    runtime = REPO / "outputs/cas_q2/empirical_runtime_v1"
    def opaque():
        frame = sys._getframe(2)
        while frame:
            if frame.f_code.co_name == "digest" and Path(frame.f_code.co_filename).resolve() == REPO / "scripts/verify_roa_artifacts.py":
                return True
            frame = frame.f_back
        return False
    def deny(reason):
        receipt["denied"].append(reason)
        raise RuntimeError("D_BOUNDARY_" + reason)
    def audit(event, args):
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request"}:
            deny("NETWORK_OR_PROCESS")
        if event in {"os.remove", "os.rmdir", "os.link", "os.symlink", "os.rename", "os.truncate"}:
            deny("DELETE_RENAME_LINK_OR_TRUNCATE")
        if event in {"os.mkdir", "os.chmod", "os.utime"}:
            if not Path(os.fsdecode(args[0])).resolve().is_relative_to(output):
                deny("MUTATION_OUTSIDE_OUTPUT")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        opening, flags = args[1:3]
        writing = isinstance(opening, str) and any(c in opening for c in "wax+") or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output) or flags & os.O_TRUNC:
                deny("NONEXCLUSIVE_OR_EXTERNAL_WRITE")
            receipt["writes"].add(str(path))
            return
        if opaque():
            # Authentication is allowed only for explicitly listed files, or
            # original project files during the read-only inventory stage.
            if path in allowed or path.is_relative_to(output) or (mode == "audit" and path.is_relative_to(root)):
                receipt["reads"].add(str(path))
                return
        raw = path.is_relative_to(root / "data/raw") or path.is_relative_to(root / "data/cache/daa_v2_hotpot_full_source")
        if raw and mode not in {"mapping", "outcome_validation"}:
            deny("RAW_REFERENCE_READ_OUTSIDE_MAPPER")
        if path.suffix in {".safetensors", ".joblib", ".pkl"} or path.name == "pytorch_model.bin":
            deny("MODEL_LOADING")
        if mode in {"mapping", "outcome_validation"} and path.is_relative_to(policy):
            deny("POLICY_INPUT_IN_METHOD_BLIND_PROCESS")
        if mode in {"analysis", "analysis_validation"} and path.is_relative_to(runtime) and path.suffix == ".jsonl":
            deny("CANONICAL_TEXT_IN_NUMERIC_ANALYSIS")
        if mode == "audit" and path.suffix in {".jsonl", ".parquet", ".npy", ".u16le"}:
            deny("PRIVATE_PAYLOAD_DECODE_IN_INVENTORY")
        runtime_library = any(path.is_relative_to(p) for p in libraries)
        audit_metadata = mode == "audit" and (path.is_relative_to(root) or path.is_relative_to(REPO)) and path.suffix in {".json", ".py", ".md", ".txt"}
        if not (path in allowed or path.is_relative_to(output) or runtime_library or audit_metadata):
            deny("UNLISTED_INPUT")
        receipt["reads"].add(str(path))
    sys.addaudithook(audit)
    def profile(frame, event, arg):
        if event != "call":
            return
        name = frame.f_code.co_name
        if name in {"fit", "partial_fit", "fit_transform", "generate", "retrieve", "encode_queries"} or (
            name == "forward" and hasattr(frame.f_locals.get("self"), "parameters")):
            receipt["forbidden_calls"] += 1
            deny("MODEL_FIT_INFERENCE_OR_RETRIEVAL")
    sys.setprofile(profile)
    return receipt
