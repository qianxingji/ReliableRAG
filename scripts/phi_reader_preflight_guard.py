"""Process-local IO boundary for the invented-only Phi GPU preflight."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def install(original: Path, output: Path, allowed_reads=()) -> dict:
    original, output = original.resolve(), output.resolve()
    phi = (original / "data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct").resolve()
    temp = (output / "cache/tmp").resolve()
    allowed = {Path(path).resolve() for path in allowed_reads}
    receipt = {"reads": set(), "writes": set(), "denied": []}

    def deny(reason: str) -> None:
        receipt["denied"].append(reason)
        raise RuntimeError("Phi preflight boundary: " + reason)

    def hook(event, args):
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request"}:
            deny(event)
        if event in {"os.remove", "os.rmdir"}:
            path = Path(os.fsdecode(args[0])).resolve()
            if not path.is_relative_to(output):
                deny("delete outside output")
        if event in {"os.rename", "os.symlink", "os.link"}:
            paths = [Path(os.fsdecode(value)).resolve() for value in args[:2]]
            if any(not path.is_relative_to(output) for path in paths):
                deny("move/link outside output")
        if event in {"os.mkdir", "os.chmod", "os.utime", "os.truncate"}:
            if not Path(os.fsdecode(args[0])).resolve().is_relative_to(output):
                deny("mutation outside output")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output):
                deny("write outside output")
            receipt["writes"].add(str(path))
            return
        if path.is_relative_to(original / "data/raw"):
            deny("raw benchmark read")
        if path.is_relative_to(original / "outputs") and path not in allowed:
            deny("benchmark/output artifact read after boundary")
        if path.is_relative_to(original / "data/models") and not path.is_relative_to(phi):
            deny("non-Phi model read")
        receipt["reads"].add(str(path))

    sys.addaudithook(hook)
    return receipt


def compact(receipt: dict) -> dict:
    return {key: sorted(value) if isinstance(value, set) else value for key, value in receipt.items()}
