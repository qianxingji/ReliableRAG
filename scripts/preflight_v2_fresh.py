#!/usr/bin/env python3
"""Structural and leakage preflight for the prospective DAA-V2 fresh cohort.

This gate runs before V2/GbV action sealing and before any fresh correctness labels are
made available to the experimental workspace. It validates selected IDs, the canonical
branch ledger, and the ten-field label-free V2 base-score ledger.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.answer_normalization import assess_pair_eligibility  # noqa: E402
from src.evaluation.fresh_schema import read_fresh_branches, trace_key  # noqa: E402

EXPECTED_RETRIEVERS = ("bm25", "dense", "hybrid")
FORBIDDEN_SCORE_TOKENS = (
    "gold",
    "correct",
    "label",
    "recovery",
    "damage",
    "outcome",
    "target",
    "answer_key",
    "supporting_fact",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_selected(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row) != {"dataset", "sample_id"}:
                raise RuntimeError(
                    f"selected-ID row {line_number} must contain only dataset/sample_id"
                )
            rows.append((str(row["dataset"]), str(row["sample_id"])))
    if len(set(rows)) != len(rows):
        raise RuntimeError("duplicate selected dataset/sample_id pairs")
    return rows


def read_required_scores(path: Path) -> list[str]:
    specification = json.loads(path.read_text(encoding="utf-8"))
    return [str(value) for value in specification["required_base_score_fields"]]


def read_score_ledger(path: Path, required_scores: list[str]) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row) != {"dataset", "retriever", "sample_id", "scores"}:
                raise RuntimeError(
                    f"score row {line_number} must contain exactly dataset/retriever/sample_id/scores"
                )
            if not isinstance(row["scores"], dict):
                raise RuntimeError(f"score row {line_number}: scores must be an object")
            score_names = set(row["scores"])
            if score_names != set(required_scores):
                raise RuntimeError(
                    f"score row {line_number}: expected exactly {sorted(required_scores)}, "
                    f"found {sorted(score_names)}"
                )
            for name, value in row["scores"].items():
                lowered = name.lower()
                if any(token in lowered for token in FORBIDDEN_SCORE_TOKENS):
                    raise RuntimeError(f"forbidden gold/outcome-like score field: {name}")
                if value is not None:
                    numeric = float(value)
                    if not math.isfinite(numeric):
                        raise RuntimeError(
                            f"score row {line_number}: non-finite value for {name}"
                        )
            rows.append(row)
    keys = [
        (str(row["dataset"]), str(row["retriever"]), str(row["sample_id"]))
        for row in rows
    ]
    if len(set(keys)) != len(keys):
        raise RuntimeError("duplicate keys in V2 base-score ledger")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected-ids", type=Path, required=True)
    parser.add_argument("--branches", type=Path, required=True)
    parser.add_argument("--v2-score-ledger", type=Path, required=True)
    parser.add_argument(
        "--private-artifact-spec",
        type=Path,
        default=Path("docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json"),
    )
    parser.add_argument("--private-artifact-verification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    artifact_verification = json.loads(
        args.private_artifact_verification.read_text(encoding="utf-8")
    )
    if artifact_verification.get("status") != "PASS":
        raise RuntimeError("historical private-artifact verification is not PASS")
    if artifact_verification.get("fresh_label_access_authorized") is not False:
        raise RuntimeError("private-artifact verification must predate fresh-label access")

    selected = read_selected(args.selected_ids)
    selected_set = set(selected)
    branches = read_fresh_branches(args.branches)
    required_scores = read_required_scores(args.private_artifact_spec)
    score_rows = read_score_ledger(args.v2_score_ledger, required_scores)

    branch_keys = [trace_key(row) for row in branches]
    score_keys = [
        (str(row["dataset"]), str(row["retriever"]), str(row["sample_id"]))
        for row in score_rows
    ]
    if set(branch_keys) != set(score_keys):
        raise RuntimeError("canonical branch and V2 base-score ledgers have different trace keys")

    by_question: dict[tuple[str, str], list[str]] = defaultdict(list)
    for dataset, retriever, sample_id in branch_keys:
        if (dataset, sample_id) not in selected_set:
            raise RuntimeError(
                f"branch ledger contains unselected question: {(dataset, sample_id)}"
            )
        by_question[(dataset, sample_id)].append(retriever)
    if set(by_question) != selected_set:
        missing = selected_set - set(by_question)
        raise RuntimeError(f"selected questions missing from branch ledger: {len(missing)}")

    for question_key, retrievers in by_question.items():
        if sorted(retrievers) != sorted(EXPECTED_RETRIEVERS):
            raise RuntimeError(
                f"{question_key} must have exactly {EXPECTED_RETRIEVERS}, found {retrievers}"
            )

    score_by_key = {
        (str(row["dataset"]), str(row["retriever"]), str(row["sample_id"])): row
        for row in score_rows
    }
    forced_keep = Counter()
    eligible_scorable = 0
    for branch in branches:
        row_key = trace_key(branch)
        eligibility = assess_pair_eligibility(branch["a0"], branch["a1"])
        scores = score_by_key[row_key]["scores"]
        values = [scores[name] for name in required_scores]
        if eligibility.eligible:
            if any(value is None for value in values):
                forced_keep["eligible_but_missing_base_score"] += 1
            else:
                eligible_scorable += 1
        else:
            forced_keep[eligibility.reason or "ineligible"] += 1

    question_counts = Counter(dataset for dataset, _ in selected)
    trace_counts = Counter(dataset for dataset, _, _ in branch_keys)
    result = {
        "status": "PASS",
        "selected_question_count": len(selected),
        "trace_count": len(branches),
        "question_counts_by_dataset": dict(sorted(question_counts.items())),
        "trace_counts_by_dataset": dict(sorted(trace_counts.items())),
        "expected_retrievers": list(EXPECTED_RETRIEVERS),
        "eligible_scorable_count": eligible_scorable,
        "forced_keep_or_missing_score_counts": dict(sorted(forced_keep.items())),
        "required_base_score_fields": required_scores,
        "hashes": {
            "selected_ids_sha256": sha256(args.selected_ids),
            "branches_sha256": sha256(args.branches),
            "v2_score_ledger_sha256": sha256(args.v2_score_ledger),
            "private_artifact_spec_sha256": sha256(args.private_artifact_spec),
            "private_artifact_verification_sha256": sha256(
                args.private_artifact_verification
            ),
        },
        "gold_or_correctness_input": False,
        "fresh_label_access_authorized": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
