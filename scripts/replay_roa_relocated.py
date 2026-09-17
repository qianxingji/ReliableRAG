"""Apply a location guard around the unchanged original saved-parameter replay."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


class FallbackGuard:
    """Observe Python file-open events; this is not an OS sandbox."""

    def __init__(self, denied: list[Path], runtime: Path):
        self.denied = [p.resolve() for p in denied]
        self.runtime = runtime.resolve()
        self.runtime_reads: set[str] = set()
        self.blocked: set[str] = set()

    def inspect(self, value) -> None:
        if isinstance(value, int):
            return
        p = Path(os.fsdecode(value)).resolve()
        if any(p == root or root in p.parents for root in self.denied):
            if p == self.runtime or self.runtime in p.parents:
                self.runtime_reads.add(str(p))
            else:
                self.blocked.add(str(p))
                raise RuntimeError("ORIGINAL_LOCATION_FALLBACK_FORBIDDEN:" + str(p))

    def audit(self, event, args):
        if event == "open":
            self.inspect(args[0])
        if event in ("socket.connect", "socket.bind"):
            raise RuntimeError("RELOCATION_NETWORK_FORBIDDEN")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("primary", "independent"), required=True)
    parser.add_argument("--deny-root", type=Path, required=True, action="append")
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    for root in args.deny_root:
        for relocated in (source, args.project_root.resolve(), args.output.resolve()):
            if relocated == root.resolve() or root.resolve() in relocated.parents:
                parser.error("Relocated source, data and output must be outside denied roots")
    guard = FallbackGuard(args.deny_root, Path(sys.prefix))
    sys.addaudithook(guard.audit)
    from scripts import replay_roa_original as original
    sys.argv = [str(original.__file__), "--project-root", str(args.project_root),
                "--output", str(args.output), "--mode", args.mode]
    result = original.main()
    original.write_json(args.output / "RELOCATION_ACCESS.json", dict(
        status="PASS_NO_ORIGINAL_DATA_FALLBACK" if not guard.blocked and result == 0 else "FAIL",
        denied_roots=[str(p) for p in guard.denied], runtime_exception=str(guard.runtime),
        runtime_reads=sorted(guard.runtime_reads), blocked=sorted(guard.blocked),
        scope="Python open-event audit; current host/runtime only; numerical code unchanged"))
    return result


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
