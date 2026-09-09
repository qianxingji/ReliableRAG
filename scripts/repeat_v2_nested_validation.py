#!/usr/bin/env python3
"""Run repeated grouped nested development validation and aggregate stability.

This wrapper intentionally operates only on the historical V2 development cohort. It
must not be pointed at a sealed fresh confirmatory label file before the pre-label
protocol is finalized.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile


def summarize(values: list[float | int]) -> dict[str, float | int]:
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--budgets", default="370,450")
    parser.add_argument("--seed-start", type=int, default=20260909)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    script = Path(__file__).with_name("develop_v2_meta_selector.py")
    budgets = [int(x) for x in args.budgets.split(",") if x.strip()]
    result: dict[str, object] = {
        "status": "REPEATED_NESTED_DEVELOPMENT_VALIDATION_ONLY",
        "seed_start": args.seed_start,
        "runs_per_budget": args.runs,
        "budgets": {},
    }

    with tempfile.TemporaryDirectory(prefix="v2_nested_") as tmp:
        tmpdir = Path(tmp)
        for budget in budgets:
            rows = []
            for offset in range(args.runs):
                seed = args.seed_start + offset
                run_path = tmpdir / f"b{budget}_s{seed}.json"
                command = [
                    sys.executable,
                    str(script),
                    "--decisions",
                    str(args.decisions),
                    "--outcomes",
                    str(args.outcomes),
                    "--output",
                    str(run_path),
                    "--budget",
                    str(budget),
                    "--seed",
                    str(seed),
                ]
                subprocess.run(command, check=True)
                run = json.loads(run_path.read_text(encoding="utf-8"))
                v2 = run["v2_nested_metrics"]
                raw = run["raw_hgb_same_outer_budgets"]
                rows.append(
                    {
                        "seed": seed,
                        "v2": v2,
                        "raw_hgb": raw,
                        "delta_net": v2["net"] - raw["net"],
                        "delta_damage": v2["damage"] - raw["damage"],
                        "delta_recovery": v2["recovery"] - raw["recovery"],
                    }
                )

            result["budgets"][str(budget)] = {
                "runs": rows,
                "v2_net": summarize([x["v2"]["net"] for x in rows]),
                "raw_hgb_net": summarize([x["raw_hgb"]["net"] for x in rows]),
                "v2_damage": summarize([x["v2"]["damage"] for x in rows]),
                "raw_hgb_damage": summarize([x["raw_hgb"]["damage"] for x in rows]),
                "delta_net": summarize([x["delta_net"] for x in rows]),
                "delta_damage": summarize([x["delta_damage"] for x in rows]),
                "v2_net_better_runs": sum(x["delta_net"] > 0 for x in rows),
                "v2_net_tied_runs": sum(x["delta_net"] == 0 for x in rows),
                "v2_damage_lower_runs": sum(x["delta_damage"] < 0 for x in rows),
            }

    result["interpretation"] = (
        "Repeated grouped folds are sensitivity analyses on one historical development cohort; "
        "they are not independent replications and cannot establish prospective superiority."
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
