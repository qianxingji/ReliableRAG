from __future__ import annotations

import json
from pathlib import Path

FRESH_BRANCH_FIELDS = frozenset(
    {
        "dataset",
        "retriever",
        "sample_id",
        "question",
        "a0",
        "a1",
        "evidence0",
        "evidence1",
    }
)


def trace_key(row: dict) -> tuple[str, str, str]:
    return (str(row["dataset"]), str(row["retriever"]), str(row["sample_id"]))


def read_fresh_branches(path: Path) -> list[dict]:
    """Read the strict gold-free canonical branch ledger used by both V2 and GbV."""
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            extra = set(row) - FRESH_BRANCH_FIELDS
            missing = FRESH_BRANCH_FIELDS - set(row)
            if extra or missing:
                raise RuntimeError(
                    f"fresh branch row {line_number}: extra={sorted(extra)}, missing={sorted(missing)}"
                )
            for field in ("dataset", "retriever", "sample_id", "question", "a0", "a1"):
                if not isinstance(row[field], str):
                    raise RuntimeError(f"row {line_number}: {field} must be str")
            for field in ("evidence0", "evidence1"):
                if not isinstance(row[field], list) or not all(
                    isinstance(value, str) for value in row[field]
                ):
                    raise RuntimeError(f"row {line_number}: {field} must be list[str]")
            rows.append(row)
    keys = [trace_key(row) for row in rows]
    if len(set(keys)) != len(keys):
        raise RuntimeError("duplicate dataset/retriever/sample_id keys in fresh branch ledger")
    return rows
