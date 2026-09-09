#!/usr/bin/env python3
"""Reproduce retrospective HGB budget diagnostics from frozen ledgers.

This script performs evaluation-only re-ranking. It does not retrain a selector, alter
historical frozen decisions, or claim prospective superiority. Gold-derived outcome
fields are joined only after the score ledger has been loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.arbitration.v2_policy import (  # noqa: E402
    RankedTrace,
    TransitionOutcome,
    select_global_budget,
    select_stratum_budgets,
    summarize_selection,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def key(row: dict) -> tuple[str, str, str]:
    return (row["sample_id"], row["dataset"], row["retriever"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--budgets",
        default="100,200,300,370,387,407,450,500,750,1000",
        help="comma-separated global budgets",
    )
    args = parser.parse_args()

    outcome_map: dict[tuple[str, str, str], TransitionOutcome] = {}
    for row in read_jsonl(args.outcomes):
        outcome_map[key(row)] = TransitionOutcome(
            a0_em=int(row["a0_em"]),
            a1_em=int(row["a1_em"]),
            a0_f1=float(row["a0_f1"]),
            a1_f1=float(row["a1_f1"]),
        )

    ranked_records: list[RankedTrace] = []
    original_hgb: list[RankedTrace] = []
    conservative_budgets: Counter[tuple[str, str]] = Counter()
    all_strata: set[tuple[str, str]] = set()

    for row in read_jsonl(args.decisions):
        row_key = key(row)
        all_strata.add((row["dataset"], row["retriever"]))
        if row_key not in outcome_map:
            raise RuntimeError(f"decision missing evaluation outcome: {row_key}")
        score = row.get("scores", {}).get("state_symmetric_hgb")
        if score is not None:
            record = RankedTrace(
                sample_id=row["sample_id"],
                dataset=row["dataset"],
                retriever=row["retriever"],
                score=float(score),
            )
            ranked_records.append(record)
            if row["actions"].get("state_symmetric_hgb") == "REPLACE":
                original_hgb.append(record)
        if row["actions"].get("selected_mars") == "REPLACE":
            conservative_budgets[(row["dataset"], row["retriever"])] += 1

    for stratum in all_strata:
        conservative_budgets.setdefault(stratum, 0)

    budgets = [int(value) for value in args.budgets.split(",") if value.strip()]
    budget_rows = []
    for budget in budgets:
        selected = select_global_budget(ranked_records, budget)
        summary = summarize_selection(selected, outcome_map)
        summary["budget"] = budget
        budget_rows.append(summary)

    global_370 = select_global_budget(ranked_records, 370)
    by_dataset: dict[str, list[RankedTrace]] = defaultdict(list)
    by_retriever: dict[str, list[RankedTrace]] = defaultdict(list)
    for row in global_370:
        by_dataset[row.dataset].append(row)
        by_retriever[row.retriever].append(row)

    stratum_matched = select_stratum_budgets(ranked_records, conservative_budgets)

    result = {
        "status": "RETROSPECTIVE_DEVELOPMENT_DIAGNOSTIC_ONLY",
        "source_hashes": {
            "decisions_sha256": sha256(args.decisions),
            "outcomes_sha256": sha256(args.outcomes),
        },
        "scorable_hgb_records": len(ranked_records),
        "historical_hgb_operating_point": summarize_selection(original_hgb, outcome_map),
        "global_budget_sweep": budget_rows,
        "global_370": {
            "overall": summarize_selection(global_370, outcome_map),
            "by_dataset": {
                name: summarize_selection(rows, outcome_map)
                for name, rows in sorted(by_dataset.items())
            },
            "by_retriever": {
                name: summarize_selection(rows, outcome_map)
                for name, rows in sorted(by_retriever.items())
            },
        },
        "conservative_stratum_budgets": {
            f"{dataset}:{retriever}": budget
            for (dataset, retriever), budget in sorted(conservative_budgets.items())
        },
        "hgb_at_conservative_stratum_budgets": summarize_selection(
            stratum_matched, outcome_map
        ),
        "integrity_note": (
            "Scores are frozen non-oracle HGB outputs. Gold-derived EM/F1 fields are joined "
            "only for retrospective evaluation. These results must not be relabeled as a new "
            "prospective confirmatory experiment."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
