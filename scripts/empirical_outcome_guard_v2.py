"""Narrow decoded-file permissions layered over immutable D inventory guard.

The broader authenticated predecessor graph may be hashed; it is never an
implicit permission to decode earlier scores/outcomes in a method-blind mapper.
"""
import os
from pathlib import Path
import sys

from scripts.empirical_outcome_guard import guard as original_guard
from scripts.empirical_pool_io import REPO


def guard(root, output, authenticated_paths, *, mode, readable_paths):
    allowed = {Path(p).resolve() for p in authenticated_paths}
    decoded = {Path(p).resolve() for p in readable_paths}
    if not decoded <= allowed:
        raise ValueError("Decoded D inputs must all be authenticated")
    receipt = original_guard(root, output, authenticated_paths, mode=mode)
    root, output = Path(root).resolve(), Path(output).resolve()
    receipt["decoded_input_allowlist"] = sorted(str(p) for p in decoded)
    libraries = (Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
    def opaque():
        frame = sys._getframe(2)
        while frame:
            if frame.f_code.co_name == "digest" and Path(frame.f_code.co_filename).resolve() == REPO / "scripts/verify_roa_artifacts.py":
                return True
            frame = frame.f_back
        return False
    def audit(event, args):
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        opening, flags = args[1:3]
        writing = isinstance(opening, str) and any(c in opening for c in "wax+") or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing or opaque() or path.is_relative_to(output) or any(path.is_relative_to(p) for p in libraries):
            return
        if path not in decoded:
            receipt["denied"].append("UNLISTED_DECODED_INPUT")
            raise RuntimeError("D_BOUNDARY_UNLISTED_DECODED_INPUT")
    sys.addaudithook(audit)
    return receipt
