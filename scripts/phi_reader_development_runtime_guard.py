"""Fail-closed Python IO boundary for the Phi development runtime."""
from __future__ import annotations

import os
from pathlib import Path
import sys


class DevelopmentRuntimeIOPolicy:
    """Pure path policy, separated from the irreversible audit-hook install."""

    def __init__(self, *, repository: Path, original: Path, output: Path,
                 allowed_reads=(), canonical_reference: Path | None = None):
        self.repository = Path(repository).resolve()
        self.original = Path(original).resolve()
        self.output = Path(output).resolve()
        self.allowed_reads = {Path(path).resolve() for path in allowed_reads}
        self.allowed_read_roots = set()
        if canonical_reference is not None:
            self.allowed_read_roots.add(Path(canonical_reference).resolve())
        self.model_roots = {
            (self.original / "data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct").resolve(),
            (self.original / "data/models/huggingface/models--BAAI--bge-base-en-v1.5").resolve(),
        }
        self.allowed_scan_dirs = set()
        for path in self.allowed_reads:
            parent = path.parent
            while parent != parent.parent:
                self.allowed_scan_dirs.add(parent); parent = parent.parent
        self.temp_root = (self.output / "cache/tmp").resolve()

    @staticmethod
    def _under(path: Path, roots) -> bool:
        return any(path.is_relative_to(root) for root in roots)

    def check_read(self, path: Path) -> None:
        path = Path(path).resolve()
        if path.is_relative_to(self.original / "data/raw"):
            raise RuntimeError(f"raw benchmark/Gold read: {path}")
        if path.is_relative_to(self.original / "data/models") and path not in self.allowed_reads:
            raise RuntimeError(f"unlisted model read: {path}")
        if path.is_relative_to(self.original / "outputs") and path not in self.allowed_reads and not self._under(path, self.allowed_read_roots):
            raise RuntimeError(f"unlisted original output read: {path}")
        if (path.is_relative_to(self.original) and path not in self.allowed_reads and
                not self._under(path, self.allowed_read_roots) and
                not path.is_relative_to(self.original / ".venv")):
            raise RuntimeError(f"unlisted original checkout read: {path}")
        if (path.is_relative_to(self.repository) and not path.is_relative_to(self.output) and
                path not in self.allowed_reads and not self._under(path, self.allowed_read_roots) and
                not path.is_relative_to(self.repository / ".venv")):
            raise RuntimeError(f"unlisted implementation checkout read: {path}")

    def check_scan(self, path: Path) -> None:
        path = Path(path).resolve()
        if path in self.allowed_scan_dirs or path.is_relative_to(self.output) or self._under(path, self.allowed_read_roots):
            return
        if path.is_relative_to(self.original) or path.is_relative_to(self.repository):
            raise RuntimeError(f"unlisted project directory scan: {path}")

    def check_write(self, path: Path, *, truncating: bool = False) -> None:
        path = Path(path).resolve()
        if not path.is_relative_to(self.output):
            raise RuntimeError("write outside selected output namespace")
        if truncating and path.exists() and not path.is_relative_to(self.output / "cache"):
            raise RuntimeError("sealed/runtime artifact overwrite")

    def check_delete(self, path: Path) -> None:
        path = Path(path).resolve()
        if not path.is_relative_to(self.temp_root) or path == self.temp_root:
            raise RuntimeError("delete outside ephemeral temp")


def install(*, repository: Path, original: Path, output: Path, allowed_reads=(),
            canonical_reference: Path | None = None) -> dict:
    policy = DevelopmentRuntimeIOPolicy(repository=repository, original=original, output=output,
        allowed_reads=allowed_reads, canonical_reference=canonical_reference)
    receipt = {"reads": set(), "writes": set(), "denied": [], "temp_cleanup_events": 0}

    def deny(reason: str):
        receipt["denied"].append(reason)
        raise RuntimeError("Phi development IO boundary: " + reason)

    def hook(event, args):
        try:
            if event == "import" and (args[0] == "src" or args[0].startswith("src.")):
                deny("original pipeline package import")
            if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request"}:
                deny(event)
            if event in {"os.remove", "os.rmdir"}:
                policy.check_delete(Path(os.fsdecode(args[0]))); receipt["temp_cleanup_events"] += 1
            if event in {"os.rename", "os.symlink", "os.link"}:
                deny(event)
            if event in {"os.mkdir", "os.chmod", "os.utime", "os.truncate"}:
                path = Path(os.fsdecode(args[0]))
                if event == "os.truncate":
                    policy.check_write(path, truncating=True)
                elif not path.resolve().is_relative_to(policy.output):
                    deny("mutation outside selected output namespace")
            if event in {"os.listdir", "os.scandir"}:
                target = args[0] if args and args[0] is not None else "."
                if not isinstance(target, int): policy.check_scan(Path(os.fsdecode(target)))
            if event != "open" or isinstance(args[0], int):
                return
            path = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if writing:
                policy.check_write(path, truncating=bool(flags & os.O_TRUNC))
                receipt["writes"].add(str(path))
            else:
                policy.check_read(path); receipt["reads"].add(str(path))
        except RuntimeError as exc:
            if str(exc).startswith("Phi development IO boundary:"):
                raise
            deny(str(exc))

    sys.addaudithook(hook)
    return receipt


def compact(receipt: dict) -> dict:
    return {key: sorted(value) if isinstance(value, set) else value for key, value in receipt.items()}
