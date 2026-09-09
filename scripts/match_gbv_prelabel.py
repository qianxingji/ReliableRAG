#!/usr/bin/env python3
"""Seal Generate-but-Verify comparison actions before fresh labels are opened.

Three frozen GbV operating points are produced:
1. primary same-total-budget ranking comparator;
2. secondary exact dataset x retriever budget-matched ranking comparator;
3. historical-development-selected GbV thresholds transferred unchanged to fresh data.

All three use only the paired GbV margin and stable identifiers. No fresh labels enter.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

GBV_DEV_THRESHOLDS = {
    "bm25": 0.0473407506942749,
    "dense": 0.01295558363199234,
    "hybrid": 0.4287375956773758,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def key(row: dict) -> tuple[str, str, str]:
    return (str(row["dataset"]), str(row["retriever"]), str(row["sample_id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2-actions", type=Path, required=True)
    parser.add_argument("--gbv-scores", type=Path, required=True)
    parser.add_argument("--actions-output", type=Path, required=True)
    parser.add_argument("--seal-output", type=Path, required=True)
    args = parser.parse_args()

    v2_rows = read_jsonl(args.v2_actions)
    gbv_rows = read_jsonl(args.gbv_scores)
    v2_by_key = {key(row): row for row in v2_rows}
    gbv_by_key = {key(row): row for row in gbv_rows}
    if len(v2_by_key) != len(v2_rows) or len(gbv_by_key) != len(gbv_rows):
        raise RuntimeError("duplicate keys in V2 or GbV ledger")
    if set(v2_by_key) != set(gbv_by_key):
        missing_v2 = len(set(gbv_by_key) - set(v2_by_key))
        missing_gbv = len(set(v2_by_key) - set(gbv_by_key))
        raise RuntimeError(
            f"V2/GbV key mismatch: missing_v2={missing_v2}, missing_gbv={missing_gbv}"
        )

    v2_replace = {k for k, row in v2_by_key.items() if row["action"] == "REPLACE"}
    v2_strata = Counter((k[0], k[1]) for k in v2_replace)

    eligible = []
    for k, row in gbv_by_key.items():
        margin = row.get("gbv_margin")
        if margin is None or row.get("eligible") is False:
            continue
        retriever = k[1].lower()
        if retriever not in GBV_DEV_THRESHOLDS:
            raise RuntimeError(f"unknown retriever for frozen GbV threshold: {retriever}")
        eligible.append((k, float(margin)))
    eligible.sort(key=lambda item: (-item[1], item[0]))
    if len(eligible) < len(v2_replace):
        raise RuntimeError("not enough eligible GbV rows to match V2 total action budget")

    gbv_global = {k for k, _ in eligible[: len(v2_replace)]}

    eligible_by_stratum: dict[tuple[str, str], list[tuple[tuple[str, str, str], float]]] = defaultdict(list)
    for k, margin in eligible:
        eligible_by_stratum[(k[0], k[1])].append((k, margin))

    gbv_stratum = set()
    for stratum, budget in sorted(v2_strata.items()):
        candidates = eligible_by_stratum[stratum]
        if len(candidates) < budget:
            raise RuntimeError(
                f"GbV eligible count {len(candidates)} is below V2 budget {budget} for {stratum}"
            )
        gbv_stratum.update(k for k, _ in candidates[:budget])

    gbv_dev_selected = {
        k
        for k, margin in eligible
        if margin >= GBV_DEV_THRESHOLDS[k[1].lower()]
    }

    args.actions_output.parent.mkdir(parents=True, exist_ok=True)
    with args.actions_output.open("w", encoding="utf-8") as handle:
        for k in sorted(v2_by_key):
            margin = gbv_by_key[k].get("gbv_margin")
            record = {
                "dataset": k[0],
                "retriever": k[1],
                "sample_id": k[2],
                "gbv_margin": None if margin is None else float(margin),
                "gbv_global_matched": "REPLACE" if k in gbv_global else "KEEP",
                "gbv_stratum_matched": "REPLACE" if k in gbv_stratum else "KEEP",
                "gbv_dev_selected": "REPLACE" if k in gbv_dev_selected else "KEEP",
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    global_strata = Counter((k[0], k[1]) for k in gbv_global)
    stratum_strata = Counter((k[0], k[1]) for k in gbv_stratum)
    dev_strata = Counter((k[0], k[1]) for k in gbv_dev_selected)
    seal = {
        "status": "GBV_PRELABEL_MATCHED_ACTION_SEAL",
        "saved_utc": datetime.now(timezone.utc).isoformat(),
        "trace_count": len(v2_rows),
        "v2_replace_count": len(v2_replace),
        "gbv_global_replace_count": len(gbv_global),
        "gbv_stratum_replace_count": len(gbv_stratum),
        "gbv_dev_selected_replace_count": len(gbv_dev_selected),
        "v2_actions_sha256": sha256(args.v2_actions),
        "gbv_score_ledger_sha256": sha256(args.gbv_scores),
        "gbv_actions_sha256": sha256(args.actions_output),
        "v2_stratum_budgets": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(v2_strata.items())
        },
        "gbv_global_stratum_counts": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(global_strata.items())
        },
        "gbv_exact_stratum_counts": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(stratum_strata.items())
        },
        "gbv_dev_selected_stratum_counts": {
            f"{dataset}:{retriever}": count
            for (dataset, retriever), count in sorted(dev_strata.items())
        },
        "gbv_dev_selected_thresholds": GBV_DEV_THRESHOLDS,
        "gbv_dev_threshold_source": (
            "Historical 7,200-trace development selection from the frozen published-baseline handoff; "
            "transferred unchanged and never recalibrated on fresh labels."
        ),
        "gold_or_outcome_input": False,
        "tie_break": "descending GbV margin; then dataset, retriever, sample_id lexical order",
    }
    args.seal_output.parent.mkdir(parents=True, exist_ok=True)
    args.seal_output.write_text(json.dumps(seal, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
