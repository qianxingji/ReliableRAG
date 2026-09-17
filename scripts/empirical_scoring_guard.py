"""Explicit file/call boundaries for C4 CPU, neural and tokenizer execution."""
import os
from pathlib import Path
import sys

from scripts.empirical_pool_io import REPO


def guard(root, output, paths, *, mode, fresh_paths=()):
    if mode not in {"cpu_models","neural","tokenizer"}: raise ValueError("Scoring boundary mode")
    root, output = root.resolve(), output.resolve()
    allowed = {Path(p).resolve() for p in paths}
    fresh = {Path(p).resolve() for p in fresh_paths}
    if not fresh <= allowed: raise ValueError("Fresh inputs must be explicitly frozen")
    if mode == "cpu_models" and fresh: raise ValueError("No benchmark text in CPU model preflight")
    receipt = dict(reads=set(),writes=set(),denied=[],call_counts={},mode=mode)
    temp = output / "cache/tmp"
    leaf_imports = {"src.evaluation.answer_normalization","src.evaluation.fresh_schema","src.scoring.reader_likelihood","src.verification.gbv_nli"}
    assembled_imports = {"src.mars.state_symmetric","src.mars.full_experiment","src.arbitration.v2_ensemble"}
    def deny(reason):
        receipt["denied"].append(reason); raise RuntimeError("C4 boundary: "+reason)
    def opaque():
        frame = sys._getframe(2)
        while frame:
            if frame.f_code.co_name == "digest" and Path(frame.f_code.co_filename).resolve() == REPO / "scripts/verify_roa_artifacts.py": return True
            frame = frame.f_back
        return False
    def hook(event,args):
        if event == "import" and (args[0] == "src" or args[0].startswith("src.")):
            if args[0] not in leaf_imports and not (args[0] in assembled_imports and args[0] in sys.modules): deny("unassembled original package import")
        if event in {"subprocess.Popen","os.system","os.posix_spawn","socket.connect","socket.bind","socket.getaddrinfo","urllib.Request"}: deny(event)
        if event in {"os.remove","os.rmdir"}:
            p = Path(os.fsdecode(args[0])).resolve()
            if not p.is_relative_to(temp) or p == temp: deny("delete outside ephemeral temp")
        if event in {"os.link","os.symlink"}: deny("link mutation")
        if event == "os.rename":
            a,b=(Path(os.fsdecode(x)).resolve() for x in args[:2])
            if not (a.is_relative_to(output / "cache") and b.is_relative_to(output / "cache") and a.suffix == ".part" and b.suffix == ".json" and not b.exists()): deny("nonexclusive cache rename")
        if event in {"os.mkdir","os.chmod","os.utime","os.truncate"}:
            if not Path(os.fsdecode(args[0])).resolve().is_relative_to(output): deny("mutation outside output")
        if event != "open" or isinstance(args[0],int): return
        p = Path(os.fsdecode(args[0])).resolve(); opening, flags = args[1:3]
        writing = (isinstance(opening,str) and any(c in opening for c in "wax+")) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if writing:
            if not p.is_relative_to(output): deny("write outside output")
            if flags & os.O_TRUNC and not p.is_relative_to(output / "cache"): deny("artifact overwrite")
            receipt["writes"].add(str(p)); return
        if p.is_relative_to(root / "data/raw"): deny("raw benchmark read")
        if p.suffix in {".safetensors",".bin"} and mode != "neural" and not opaque(): deny("neural weight read")
        if p.suffix in {".joblib",".pkl"} and mode == "tokenizer" and not opaque(): deny("estimator read in tokenizer validator")
        if p.is_relative_to(root) or p.is_relative_to(REPO):
            if not (p in allowed or p.is_relative_to(output) or p.is_relative_to(root / ".venv")): deny("unlisted project input")
        receipt["reads"].add(str(p))
    sys.addaudithook(hook)
    def profile(frame,event,arg):
        if event != "call": return
        name = frame.f_code.co_name
        if name in {"fit","partial_fit","fit_transform","generate"}: deny("forbidden call "+name)
        if name == "forward" and hasattr(frame.f_locals.get("self"),"parameters"):
            if mode != "neural": deny("neural forward in "+mode)
            receipt["call_counts"]["neural_forward"] = receipt["call_counts"].get("neural_forward",0)+1
    sys.setprofile(profile)
    return receipt
