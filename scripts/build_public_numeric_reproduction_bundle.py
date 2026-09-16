#!/usr/bin/env python3
"""Build a text-free numeric reproduction bundle for the public repository.

The release preserves the complete trace-level analysis inputs required to
recompute point estimates and the question-cluster bootstrap, while replacing
benchmark sample identifiers with deterministic opaque group identifiers.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.empirical_analysis_math import Panel, point_estimates


ACTIONS = ROOT / "outputs/cas_q2/empirical_prelabel_policies_v1/actions.jsonl"
OUTCOMES = ROOT / "outputs/cas_q2/empirical_outcome_mapping_v1/numeric_outcomes.jsonl"
POINTS = ROOT / "outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json"
INTERVALS = ROOT / "outputs/cas_q2/empirical_analysis_v1/INTERVALS.json"

EXPECTED = {
    ACTIONS: "1c60b684147f2e7426d9998b3f8c325f4ecb3860b92c830c4578bf61746f4b70",
    OUTCOMES: "e8ad8addee644bdd1ef2f620895f1ba1abf32ac0568d514872ed6776e7059408",
    POINTS: "b03ddad8fa35f582a63403c029942104c3f5da1a961110edc2a62f09871f4d3b",
    INTERVALS: "6d454afeec7c125c0cc4d182556af6db214a867aa4f62f7a6fbd1e6e22b09331",
}
DATASETS = ("2wikimultihopqa", "hotpotqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
OPAQUE_ID = re.compile(r"q[0-9]{4}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def rows(path: Path) -> list[dict]:
    result = []
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            require(line.endswith("\n") and bool(line.strip()), f"invalid JSONL record at {path}:{number}")
            result.append(json.loads(line))
    return result


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-repository", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_repository.resolve() / "outputs/reproduction_v1"
    output.mkdir(parents=True, exist_ok=True)

    for path, expected in EXPECTED.items():
        require(path.is_file() and sha256(path) == expected, f"sealed input mismatch: {path}")

    action_rows = rows(ACTIONS)
    outcome_rows = rows(OUTCOMES)
    require(len(action_rows) == len(outcome_rows) == 18000, "expected 18,000 trace rows")
    by_action = {(r["dataset"], r["retriever"], r["sample_id"]): r for r in action_rows}
    by_outcome = {(r["dataset"], r["retriever"], r["sample_id"]): r for r in outcome_rows}
    require(len(by_action) == len(by_outcome) == 18000 and set(by_action) == set(by_outcome), "action/outcome identity mismatch")

    groups = sorted({(dataset, sample_id) for dataset, _, sample_id in by_action})
    require(len(groups) == 6000, "expected 6,000 question groups")
    opaque = {}
    for dataset in DATASETS:
        members = [group for group in groups if group[0] == dataset]
        require(len(members) == 2000, f"expected 2,000 groups for {dataset}")
        for index, group in enumerate(members):
            opaque[group] = f"q{index:04d}"

    release_rows = []
    reconstructed_actions = []
    reconstructed_outcomes = []
    for key in sorted(by_action):
        dataset, retriever, sample_id = key
        action = by_action[key]
        outcome = by_outcome[key]
        require(dataset in DATASETS and retriever in RETRIEVERS, "unexpected dataset/retriever")
        group_id = opaque[(dataset, sample_id)]
        record = {
            "dataset": dataset,
            "retriever": retriever,
            "group_id": group_id,
            "eligible": action["eligible"],
            "forced_keep_reason": action["forced_keep_reason"],
            "scores": action["scores"],
            "actions": action["actions"],
            "a0_em": outcome["a0_em"],
            "a1_em": outcome["a1_em"],
            "a0_f1": outcome["a0_f1"],
            "a1_f1": outcome["a1_f1"],
        }
        release_rows.append(record)
        reconstructed_actions.append({
            "dataset": dataset,
            "retriever": retriever,
            "sample_id": group_id,
            "eligible": action["eligible"],
            "forced_keep_reason": action["forced_keep_reason"],
            "scores": action["scores"],
            "actions": action["actions"],
        })
        reconstructed_outcomes.append({
            "dataset": dataset,
            "retriever": retriever,
            "sample_id": group_id,
            "a0_em": outcome["a0_em"],
            "a1_em": outcome["a1_em"],
            "a0_f1": outcome["a0_f1"],
            "a1_f1": outcome["a1_f1"],
        })

    require(all(OPAQUE_ID.fullmatch(row["group_id"]) for row in release_rows), "opaque ID format mismatch")
    require(len({(r["dataset"], r["group_id"]) for r in release_rows}) == 6000, "opaque group count mismatch")
    require(all(sum(r["dataset"] == d and r["group_id"] == q for r in release_rows) == 3 for d, q in {(r["dataset"], r["group_id"]) for r in release_rows}), "opaque sibling count mismatch")

    panel = Panel(reconstructed_actions, reconstructed_outcomes)
    accepted_points = json.loads(POINTS.read_text(encoding="utf-8"))
    rebuilt_points = json.loads(json.dumps(point_estimates(panel), allow_nan=False))
    require(rebuilt_points == accepted_points, "opaque reconstruction does not reproduce accepted point estimates")

    payload = b"".join(canonical_json(row) for row in release_rows)
    # Dataset IDs, answer text, generated text, references, and contexts are not
    # copied. The only identity is the qNNNN ordinal within a named dataset.
    require(b'"sample_id"' not in payload, "private sample identifier key leaked")
    require(re.search(rb"(?<![0-9a-f])[0-9a-f]{24,32}(?![0-9a-f])", payload) is None, "benchmark-like hexadecimal identifier leaked")
    bundle = output / "TRACE_NUMERIC.jsonl.gz"
    with bundle.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as compressed:
            compressed.write(payload)

    manifest = {
        "schema_version": 1,
        "status": "PUBLIC_TEXT_FREE_NUMERIC_REPRODUCTION_BUNDLE",
        "records": 18000,
        "question_groups": 6000,
        "datasets": list(DATASETS),
        "retrievers": list(RETRIEVERS),
        "identity": "dataset-local opaque qNNNN ordinal preserving canonical tie order",
        "included": [
            "common eligibility and forced-keep reason",
            "eight policy scores and nine realized actions",
            "original/repaired EM and token-F1 numeric outcomes",
            "dataset and retriever labels",
        ],
        "excluded": [
            "benchmark sample identifiers",
            "questions, contexts, references, and annotations",
            "generated answers and retrieved passages",
            "model weights, fitted estimators, and private execution receipts",
        ],
        "source_bindings": {
            "sealed_prelabel_actions_sha256": EXPECTED[ACTIONS],
            "sealed_numeric_outcomes_sha256": EXPECTED[OUTCOMES],
            "accepted_point_estimates_sha256": EXPECTED[POINTS],
            "accepted_intervals_sha256": EXPECTED[INTERVALS],
        },
        "files": [{"path": "TRACE_NUMERIC.jsonl.gz", "size_bytes": bundle.stat().st_size, "sha256": sha256(bundle)}],
        "point_estimate_reconstruction": "PASS_EXACT",
        "bootstrap_seed": 20260926,
        "bootstrap_draws": 20000,
    }
    (output / "MANIFEST.json").write_bytes(canonical_json(manifest))
    print(json.dumps({"status": "PASS_PUBLIC_NUMERIC_BUNDLE_BUILD", "output": str(output), "bundle": manifest["files"][0]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
