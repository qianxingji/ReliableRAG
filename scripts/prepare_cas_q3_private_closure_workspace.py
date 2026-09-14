#!/usr/bin/env python3
"""Prepare ignored P0-G/H/I local inputs without overwriting existing bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
INPUT_SPECS = (
    (
        Path("docs/cas_q3/OWNER_INPUTS_TEMPLATE.json"),
        Path("docs/cas_q3/OWNER_INPUTS.local.json"),
    ),
    (
        Path("docs/cas_q3/INSTITUTIONAL_CAS_RECORD_TEMPLATE.json"),
        Path("docs/cas_q3/INSTITUTIONAL_CAS_RECORD.local.json"),
    ),
    (
        Path("docs/cas_q3/INSTITUTIONAL_RELEASE_RECORD_TEMPLATE.json"),
        Path("docs/cas_q3/INSTITUTIONAL_RELEASE_RECORD.local.json"),
    ),
    (
        Path("docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD_TEMPLATE.json"),
        Path("docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD.local.json"),
    ),
)
EVIDENCE_DIRECTORIES = (
    Path("evidence/private/institutional_cas_record"),
    Path("evidence/private/institutional_release_record"),
    Path("evidence/private/institutional_manuscript_approval"),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(
    root: Path = ROOT,
    *,
    input_specs: Iterable[tuple[Path, Path]] = INPUT_SPECS,
    evidence_directories: Iterable[Path] = EVIDENCE_DIRECTORIES,
) -> dict[str, object]:
    root = root.resolve()
    input_specs = tuple(input_specs)
    evidence_directories = tuple(evidence_directories)
    checked_directories: list[tuple[Path, Path]] = []
    checked_inputs: list[tuple[Path, Path, Path]] = []

    # Validate the complete operation before creating anything.  This keeps a
    # malformed template, path escape, symlink or file collision from leaving a
    # partially prepared private workspace.
    for relative in evidence_directories:
        raw_path = root / relative
        path = raw_path.resolve()
        if not path.is_relative_to(root):
            raise ValueError("private evidence directory escapes workspace")
        if raw_path.is_symlink() or path.exists() and not path.is_dir():
            raise ValueError(f"private evidence directory is unsafe: {relative.as_posix()}")
        checked_directories.append((relative, path))

    for template_relative, local_relative in input_specs:
        raw_template = root / template_relative
        raw_local = root / local_relative
        template = raw_template.resolve()
        local = raw_local.resolve()
        if not template.is_relative_to(root) or not local.is_relative_to(root):
            raise ValueError("private input path escapes workspace")
        if raw_template.is_symlink() or not template.is_file():
            raise ValueError(f"canonical template is missing or unsafe: {template_relative.as_posix()}")
        if raw_local.is_symlink() or local.exists() and not local.is_file():
            raise ValueError(f"private local input is unsafe: {local_relative.as_posix()}")
        checked_inputs.append((template_relative, template, local))

    directories: list[dict[str, object]] = []
    for relative, path in checked_directories:
        existed = path.is_dir()
        path.mkdir(parents=True, exist_ok=True)
        directories.append(
            {
                "path": relative.as_posix() + "/",
                "status": "PRESERVED_EXISTING" if existed else "CREATED_EMPTY",
            }
        )

    inputs: list[dict[str, object]] = []
    for (template_relative, local_relative), (_, template, local) in zip(input_specs, checked_inputs):
        local.parent.mkdir(parents=True, exist_ok=True)
        if local.exists():
            status = "PRESERVED_EXISTING"
        else:
            shutil.copyfile(template, local)
            status = "CREATED_FROM_TEMPLATE"
        inputs.append(
            {
                "path": local_relative.as_posix(),
                "status": status,
                "matches_empty_template": _sha(local) == _sha(template),
            }
        )

    return {
        "schema_version": 1,
        "decision": "PASS_PRIVATE_CLOSURE_WORKSPACE_PREPARED_WITHOUT_OVERWRITE",
        "inputs": inputs,
        "evidence_directories": directories,
        "existing_private_bytes_overwritten": False,
        "private_values_emitted": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    result = prepare()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
