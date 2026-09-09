#!/usr/bin/env python3
"""Select genuinely unused V2 fresh question IDs using identifiers only.

Source and forbidden ledgers are intentionally ID-only. No question text, answers,
gold labels, retrieval outputs, or correctness fields are accepted by this script.
Use --per-dataset 0 for an availability audit without selecting any questions.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ALLOWED_FIELDS = frozenset({"dataset", "sample_id"})
DEFAULT_SEED = "20260910-v2-fresh"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_id_ledger(path: Path) -> list[tuple[str, str]]:
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
                raise RuntimeError(f"{path}:{line_number} has an empty identifier")
            rows.append((dataset, sample_id))
    if len(set(rows)) != len(rows):
        raise RuntimeError(f"duplicate IDs inside {path}")
    return rows


def stable_rank(seed: str, dataset: str, sample_id: str) -> str:
    payload = f"{seed}|{dataset}|{sample_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--forbidden", type=Path, action="append", default=[])
    parser.add_argument("--per-dataset", type=int, required=True)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    parser.add_argument("--selected-output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    args = parser.parse_args()
    if args.per_dataset < 0:
        raise ValueError("--per-dataset must be >= 0")

    source_rows: list[tuple[str, str]] = []
    source_hashes = []
    for path in args.source:
        source_rows.extend(read_id_ledger(path))
        source_hashes.append({"path": str(path), "sha256": sha256(path)})
    if len(set(source_rows)) != len(source_rows):
        raise RuntimeError("duplicate dataset/sample_id pairs across source ledgers")

    forbidden_rows: list[tuple[str, str]] = []
    forbidden_hashes = []
    for path in args.forbidden:
        forbidden_rows.extend(read_id_ledger(path))
        forbidden_hashes.append({"path": str(path), "sha256": sha256(path)})
    forbidden = set(forbidden_rows)

    available: dict[str, list[str]] = defaultdict(list)
    for dataset, sample_id in source_rows:
        if (dataset, sample_id) not in forbidden:
            available[dataset].append(sample_id)

    selected: list[tuple[str, str]] = []
    availability = {}
    for dataset in sorted(available):
        ranked = sorted(
            available[dataset],
            key=lambda sample_id: (stable_rank(args.seed, dataset, sample_id), sample_id),
        )
        availability[dataset] = len(ranked)
        if args.per_dataset > len(ranked):
            raise RuntimeError(
                f"requested {args.per_dataset} fresh IDs for {dataset}, but only {len(ranked)} "
                "remain after excluding all forbidden IDs"
            )
        selected.extend((dataset, sample_id) for sample_id in ranked[: args.per_dataset])

    args.selected_output.parent.mkdir(parents=True, exist_ok=True)
    with args.selected_output.open("w", encoding="utf-8") as handle:
        for dataset, sample_id in selected:
            handle.write(
                json.dumps(
                    {"dataset": dataset, "sample_id": sample_id}, sort_keys=True
                )
                + "\n"
            )

    manifest = {
        "status": "V2_FRESH_ID_AUDIT" if args.per_dataset == 0 else "V2_FRESH_IDS_SELECTED",
        "selection_uses_identifiers_only": True,
        "gold_or_correctness_input": False,
        "seed": args.seed,
        "stable_order": "SHA256(seed|dataset|sample_id), then sample_id",
        "requested_per_dataset": args.per_dataset,
        "source_counts": dict(Counter(dataset for dataset, _ in source_rows)),
        "forbidden_counts": dict(Counter(dataset for dataset, _ in forbidden_rows)),
        "available_after_exclusion": availability,
        "selected_counts": dict(Counter(dataset for dataset, _ in selected)),
        "source_ledgers": source_hashes,
        "forbidden_ledgers": forbidden_hashes,
        "selected_sha256": sha256(args.selected_output),
        "selection_rule_locked_before_generation": True,
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
