"""Recheck the pinned author's aggregate tables; do not reconstruct predictions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics

AUTHOR_SHA256 = "4090ec70c4a9154ecfc960c9c2bc26317b585d06cc308ee962a984e8981bbf6d"
METHODS = ("GbV", "HGB", "ROA-FULL", "ROA-NOGBV", "V2")
SEEDS = tuple(str(n) for n in range(20260917, 20260922))
HELD_OUT = ("musique", "2wikimultihopqa", "hotpotqa")


def summarize(report: Path) -> dict:
    data = report.read_bytes()
    if hashlib.sha256(data).hexdigest() != AUTHOR_SHA256:
        raise ValueError("author report does not match pinned artifact")
    rows = {}
    for line in data.decode("utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 9 or cells[0] not in SEEDS + HELD_OUT:
            continue
        row = dict(zip(("context", "method", "actions", "r", "d", "neutral", "net", "em_pp", "f1_pp"), cells))
        key = row["context"], row["method"]
        if key in rows:
            raise ValueError("duplicate report row")
        for field in ("actions", "r", "d", "neutral", "net"):
            row[field] = int(row[field])
        for field in ("em_pp", "f1_pp"):
            row[field] = float(row[field])
        denominator = 13500 if row["context"] in SEEDS else 4500
        if row["actions"] != row["r"] + row["d"] + row["neutral"] or row["net"] != row["r"] - row["d"]:
            raise ValueError("reported count arithmetic mismatch")
        if abs(100 * row["net"] / denominator - row["em_pp"]) > 1e-8:
            raise ValueError("reported delta EM arithmetic mismatch")
        rows[key] = row
    if set(rows) != {(context, method) for context in SEEDS + HELD_OUT for method in METHODS}:
        raise ValueError("incomplete report grid")
    for context in SEEDS + HELD_OUT:
        if len({rows[context, method]["actions"] for method in METHODS}) != 1:
            raise ValueError("reported action budgets differ")

    def stats(values: list) -> dict:
        return {"mean": statistics.mean(values), "sample_std": statistics.stdev(values)}

    metrics = ("r", "d", "net", "em_pp", "f1_pp")
    summary = {method: {k: stats([rows[seed, method][k] for seed in SEEDS]) for k in metrics}
               for method in METHODS}
    comparisons = {method: {k: stats([rows[seed, "ROA-FULL"][k] - rows[seed, method][k]
                                     for seed in SEEDS]) for k in metrics}
                   for method in ("GbV", "HGB", "ROA-NOGBV")}
    return {"source_sha256": AUTHOR_SHA256, "report_rows_checked": len(rows),
            "scope": "REPORTED_AGGREGATE_ARITHMETIC_ONLY", "numeric_replay_status": "NOT_RUN",
            "uncertainty_scope": "same-cohort partition sensitivity; not a confidence interval",
            "cas_q2_status": "NOT READY", "scientific_fit_calls": 0,
            "primary_mean_sample_std": summary, "full_minus_comparator": comparisons,
            "lodo_reported_rows": [rows[context, method] for context in HELD_OUT for method in METHODS]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(summarize(args.report), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
