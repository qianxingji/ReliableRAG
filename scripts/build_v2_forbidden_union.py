#!/usr/bin/env python3
"""Build the strict DAA-V2 forbidden evaluation-ID union from ID-only ledgers.

Each input ledger must contain exactly {dataset, sample_id}. The script never accepts
benchmark text, predictions, labels, or outcomes. Category provenance, hashes, counts,
and overlaps are recorded so omissions can be audited before fresh selection.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ALLOWED_FIELDS = frozenset({"dataset", "sample_id"})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_ids(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row) != ALLOWED_FIELDS:
                raise RuntimeError(
                    f"{path}:{line_number} must contain exactly {sorted(ALLOWED_FIELDS)}; "
                    f"found {sorted(row)}"
                )
            dataset = str(row["dataset"])
            sample_id = str(row["sample_id"])
            if not dataset or not sample_id:
                raise RuntimeError(f"{path}:{line_number} contains an empty identifier")
            rows.append((dataset, sample_id))
    return rows


def parse_category(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("category must be NAME=PATH")
    name, raw_path = value.split("=", 1)
    name = name.strip()
    raw_path = raw_path.strip()
    if not name or not raw_path:
        raise argparse.ArgumentTypeError("category must be NAME=PATH with non-empty values")
    return name, Path(raw_path)


def counts(rows) -> dict[str, int]:
    return dict(sorted(Counter(dataset for dataset, _ in rows).items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--category",
        action="append",
        type=parse_category,
        required=True,
        help="repeat NAME=PATH for every frozen exclusion category",
    )
    parser.add_argument("--union-output", type=Path, required=True)
    parser.add_argument("--coverage-output", type=Path, required=True)
    args = parser.parse_args()

    names = [name for name, _ in args.category]
    if len(set(names)) != len(names):
        raise RuntimeError("forbidden category names must be unique")

    category_sets: dict[str, set[tuple[str, str]]] = {}
    category_records = []
    for name, path in args.category:
        rows = read_ids(path)
        unique = set(rows)
        category_sets[name] = unique
        category_records.append(
            {
                "name": name,
                "path": str(path),
                "sha256": sha256(path),
                "row_count": len(rows),
                "unique_id_count": len(unique),
                "duplicate_rows_inside_ledger": len(rows) - len(unique),
                "counts_by_dataset": counts(unique),
                "included_in_union": True,
            }
        )

    union: set[tuple[str, str]] = set()
    for values in category_sets.values():
        union.update(values)

    pairwise_overlaps = []
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1 :]:
            overlap = category_sets[left_name] & category_sets[right_name]
            if overlap:
                pairwise_overlaps.append(
                    {
                        "left": left_name,
                        "right": right_name,
                        "overlap_unique_id_count": len(overlap),
                        "counts_by_dataset": counts(overlap),
                    }
                )

    args.union_output.parent.mkdir(parents=True, exist_ok=True)
    with args.union_output.open("w", encoding="utf-8") as handle:
        for dataset, sample_id in sorted(union):
            handle.write(
                json.dumps(
                    {"dataset": dataset, "sample_id": sample_id},
                    sort_keys=True,
                )
                + "\n"
            )

    coverage = {
        "status": "PASS",
        "schema_version": "daa-v2-forbidden-union-v1",
        "identifier_only_inputs": True,
        "gold_or_outcome_values_materialized": 0,
        "category_count": len(category_records),
        "categories": category_records,
        "pairwise_overlaps": pairwise_overlaps,
        "union_unique_id_count": len(union),
        "union_counts_by_dataset": counts(union),
        "union_output": str(args.union_output),
        "union_sha256": sha256(args.union_output),
    }
    args.coverage_output.parent.mkdir(parents=True, exist_ok=True)
    args.coverage_output.write_text(
        json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
