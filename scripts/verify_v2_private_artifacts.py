#!/usr/bin/env python3
"""Verify historical private estimator artifacts before any prospective V2 run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument(
        "--requirements",
        type=Path,
        default=Path("docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    specification = json.loads(args.requirements.read_text(encoding="utf-8"))
    checks = []
    all_passed = True
    for expected in specification["required_historical_files"]:
        path = args.historical_root / expected["path"]
        exists = path.is_file()
        actual_size = path.stat().st_size if exists else None
        actual_hash = sha256(path) if exists else None
        passed = (
            exists
            and actual_size == int(expected["size_bytes"])
            and actual_hash == expected["sha256"]
        )
        all_passed &= passed
        checks.append(
            {
                "path": expected["path"],
                "exists": exists,
                "expected_size_bytes": int(expected["size_bytes"]),
                "actual_size_bytes": actual_size,
                "expected_sha256": expected["sha256"],
                "actual_sha256": actual_hash,
                "passed": passed,
            }
        )

    result = {
        "status": "PASS" if all_passed else "FAIL",
        "historical_root": str(args.historical_root.resolve()),
        "requirements_sha256": sha256(args.requirements),
        "checks": checks,
        "required_base_score_fields": specification["required_base_score_fields"],
        "fresh_label_access_authorized": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    if not all_passed:
        raise SystemExit("historical private-artifact verification failed")


if __name__ == "__main__":
    main()
