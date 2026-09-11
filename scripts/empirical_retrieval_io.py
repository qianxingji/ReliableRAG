"""Authenticated native retrieval loading and bounded private execution IO."""
import ast
import collections
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import types

from scripts.empirical_pool_io import REPO, DATASETS, load, record, require, checked, verify_namespace
from scripts.replay_roa_original import write_json
from scripts.verify_roa_artifacts import digest

OUT = REPO / "outputs/cas_q2/empirical_retrieval_v1"
GPU_OUT = REPO / "outputs/cas_q2/empirical_retrieval_gpu_preflight_v1"
POOL = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
POOL_SHA = "4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98"
AUDIT = REPO / "outputs/cas_q2/empirical_acquisition_input_audit_v1"
AUDIT_SHA = "6e441f8f9fef2b000ba2b39dcfd7b40f74dd4f779568d885584bb7da10b7d518"
RETRIEVERS = ("bm25", "dense", "hybrid")
REV = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def inputs(root):
    paths = verify_namespace(AUDIT, AUDIT_SHA) + verify_namespace(POOL, POOL_SHA)
    audit = load(AUDIT / "ACQUISITION_INPUT_AUDIT.json")
    require(audit["status"] == "PASS_ACQUISITION_INPUT_INVENTORY_ONLY", "Acquisition inventory status")
    for e in audit["checked_files"]:
        paths.append(checked(Path(e["path"]), e["sha256"], e["size_bytes"]))
    cfg = load(root / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json")
    pre = load(root / "outputs/daa_v2_fresh_v1/retrieval_freeze/PREFLIGHT_INPUT_VERIFICATION.json")
    require(cfg["runtime_config"]["retrieval_config"] == pre["retriever_config"], "Native retrieval configuration mismatch")
    # The independent arithmetic source is separately pinned by the already bound original manifest.
    mp = root / "outputs/daa_v2_fresh_v1/retrieval_freeze/SHA256_MANIFEST.json"
    entry = next(e for e in load(mp)["files"] if e["path"].endswith("retrieval_freeze/independent_validate.py"))
    paths.append(checked(root / entry["path"], entry["sha256"], entry["size_bytes"]))
    return cfg, pre, sorted(set(paths))


def native_retrieval(root):
    folder = root / "outputs/daa_v2_fresh_v1/retrieval_freeze"
    import_file("retrieval_support", folder / "retrieval_support.py")
    wrapper = import_file("empirical_authenticated_retrieval", folder / "native_retrieval.py")
    native, nodes = wrapper.accepted()
    return wrapper, native, nodes


def independent_arithmetic(root):
    """Unchanged AST functions from the original independent validator; no native import."""
    import numpy as np
    path = root / "outputs/daa_v2_fresh_v1/retrieval_freeze/independent_validate.py"
    names = {"tokens", "independent_structure", "bm_scores", "ordered_entries", "independent_rrf",
             "validate_rank", "validate_top", "validate_array"}
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == names, "Independent arithmetic function set")
    module = types.ModuleType("empirical_independent_arithmetic")
    module.__dict__.update(np=np, re=re, math=math, collections=collections, require=require)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), module.__dict__)
    return module


def configure_environment(output):
    temp_root = output / "cache/tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    values = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "TOKENIZERS_PARALLELISM": "false", "PYTHONDONTWRITEBYTECODE": "1",
        "CUDA_CACHE_PATH": str(output / "cache/cuda"), "TORCH_HOME": str(output / "cache/torch"),
        "HF_HOME": str(output / "cache/hf"), "MPLCONFIGDIR": str(output / "cache/mpl"),
        "TMP": str(temp_root), "TEMP": str(temp_root), "TMPDIR": str(temp_root)}
    os.environ.update(values); tempfile.tempdir = str(temp_root)
    return values


def guard(root, output, paths, *, gpu_only=False):
    """Python audit guard, not a native-extension or system-wide sandbox."""
    allowed = {Path(p).resolve() for p in paths}
    bge = root / "data/models/huggingface/models--BAAI--bge-base-en-v1.5"
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
        raise RuntimeError("C2 boundary: " + message)
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
        if path.is_relative_to(root / "data/models") and not path.is_relative_to(bge) and not opaque():
            deny("non-BGE model read")
        if gpu_only and path.is_relative_to(POOL) and path.suffix == ".jsonl" and not opaque():
            deny("benchmark text in GPU preflight")
        if path.is_relative_to(root) or path.is_relative_to(REPO):
            if not (path in allowed or path.is_relative_to(output) or path.is_relative_to(root / ".venv") or path.is_relative_to(bge)):
                deny("unlisted project read")
        receipt["reads"].add(str(path))
    sys.addaudithook(hook)
    return receipt


def boundary_record(value):
    return {k: sorted(v) if isinstance(v, set) else v for k, v in value.items()}


def source_paths():
    return [REPO / p for p in (
        "scripts/empirical_retrieval_io.py", "scripts/preflight_roa_empirical_retrieval_gpu.py",
        "scripts/build_roa_empirical_retrieval.py", "scripts/validate_roa_empirical_retrieval.py",
        "scripts/empirical_pool_io.py", "scripts/replay_roa_original.py", "scripts/verify_roa_artifacts.py",
        "tests/test_empirical_retrieval.py", "docs/cas_q2/EMPIRICAL_REPLICATION_PROTOCOL_V1.md",
        "docs/cas_q2/EMPIRICAL_SAMPLE_SIZE_CORRIGENDUM.md", "docs/cas_q2/EMPIRICAL_C2_RETRIEVAL_CONTRACT.md",
        "docs/cas_q2/EMPIRICAL_C1_ACCEPTANCE.md")]


def seal(output, name="SHA256_MANIFEST.json"):
    write_json(output / name, dict(files=[dict(path=p.relative_to(output).as_posix(), sha256=digest(p), size_bytes=p.stat().st_size)
        for p in sorted(output.rglob("*")) if p.is_file()]))
