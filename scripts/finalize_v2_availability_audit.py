#!/usr/bin/env python3
"""Finalize the fail-closed DAA-V2 fresh availability audit.

This script converts already-created ID-only manifests into one author-reviewable
PASS/FAIL record. It does not select fresh IDs and performs no retrieval/model call.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

TARGET_PER_DATASET = 1500
REQUIRED_DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
ALLOWED_ID_FIELDS = frozenset({"dataset", "sample_id"})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_ids(path: Path) -> list[tuple[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row) != ALLOWED_ID_FIELDS:
                raise RuntimeError(
                    f"{path}:{line_number} must contain exactly dataset/sample_id"
                )
            rows.append((str(row["dataset"]), str(row["sample_id"])))
    return rows


def parse_source(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("source must be DATASET=PATH")
    dataset, raw_path = value.split("=", 1)
    dataset, raw_path = dataset.strip(), raw_path.strip()
    if dataset not in REQUIRED_DATASETS:
        raise argparse.ArgumentTypeError(f"unexpected dataset: {dataset}")
    return dataset, Path(raw_path)


def parse_raw_hash(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("raw-source-hash must be DATASET=SHA256")
    dataset, digest = value.split("=", 1)
    dataset, digest = dataset.strip(), digest.strip().lower()
    if dataset not in REQUIRED_DATASETS:
        raise argparse.ArgumentTypeError(f"unexpected dataset: {dataset}")
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise argparse.ArgumentTypeError("raw source digest must be a 64-char SHA-256")
    return dataset, digest


def count_by_dataset(rows) -> dict[str, int]:
    return dict(sorted(Counter(dataset for dataset, _ in rows).items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--git-state", required=True)
    parser.add_argument("--private-artifacts", type=Path, required=True)
    parser.add_argument("--forbidden-union", type=Path, required=True)
    parser.add_argument("--forbidden-coverage", type=Path, required=True)
    parser.add_argument("--selector-manifest", type=Path, required=True)
    parser.add_argument("--no-selection", type=Path, required=True)
    parser.add_argument("--source", action="append", type=parse_source, required=True)
    parser.add_argument("--raw-source-hash", action="append", type=parse_raw_hash, required=True)
    parser.add_argument("--process-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    private = load(args.private_artifacts)
    coverage = load(args.forbidden_coverage)
    selector = load(args.selector_manifest)
    process = load(args.process_evidence)

    source_paths = dict(args.source)
    raw_hashes = dict(args.raw_source_hash)
    if set(source_paths) != set(REQUIRED_DATASETS):
        raise RuntimeError("exactly one ID-only source inventory is required for each dataset")
    if set(raw_hashes) != set(REQUIRED_DATASETS):
        raise RuntimeError("exactly one raw source SHA-256 is required for each dataset")

    checks = []

    def check(name: str, condition: bool, detail=None) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    check("private_historical_artifacts_pass", private.get("status") == "PASS")
    check("forbidden_union_builder_pass", coverage.get("status") == "PASS")
    check("forbidden_inputs_identifier_only", coverage.get("identifier_only_inputs") is True)
    check(
        "forbidden_gold_values_materialized_zero",
        int(coverage.get("gold_or_outcome_values_materialized", -1)) == 0,
    )
    check(
        "forbidden_union_hash_matches",
        coverage.get("union_sha256") == sha256(args.forbidden_union),
    )

    no_selection_rows = read_ids(args.no_selection)
    check("audit_selected_zero_questions", len(no_selection_rows) == 0)
    check("selector_requested_zero", int(selector.get("requested_per_dataset", -1)) == 0)
    check(
        "selector_gold_or_correctness_input_false",
        selector.get("gold_or_correctness_input") is False,
    )
    check(
        "selector_uses_identifiers_only",
        selector.get("selection_uses_identifiers_only") is True,
    )

    source_records = {}
    source_sets = {}
    source_counts = {}
    for dataset in REQUIRED_DATASETS:
        path = source_paths[dataset]
        rows = read_ids(path)
        wrong_dataset = sum(row_dataset != dataset for row_dataset, _ in rows)
        duplicates = len(rows) - len(set(rows))
        source_sets[dataset] = set(rows)
        source_counts[dataset] = len(set(rows))
        source_records[dataset] = {
            "path": str(path),
            "row_count": len(rows),
            "unique_count": len(set(rows)),
            "sha256": sha256(path),
            "raw_source_sha256": raw_hashes[dataset],
            "wrong_dataset_rows": wrong_dataset,
            "duplicate_rows": duplicates,
        }
        check(f"{dataset}_source_dataset_pure", wrong_dataset == 0)
        check(f"{dataset}_source_unique", duplicates == 0)

    forbidden_rows = read_ids(args.forbidden_union)
    forbidden_set = set(forbidden_rows)
    forbidden_counts = count_by_dataset(forbidden_set)
    available = {}
    overlap = {}
    for dataset in REQUIRED_DATASETS:
        source = source_sets[dataset]
        blocked = source & forbidden_set
        eligible = source - forbidden_set
        overlap[dataset] = len(blocked)
        available[dataset] = len(eligible)
        check(
            f"{dataset}_available_at_least_{TARGET_PER_DATASET}",
            len(eligible) >= TARGET_PER_DATASET,
            {"available": len(eligible), "target": TARGET_PER_DATASET},
        )

    selector_available = {
        str(k): int(v) for k, v in selector.get("available_after_exclusion", {}).items()
    }
    check(
        "selector_available_counts_match_independent_recount",
        all(selector_available.get(dataset) == available[dataset] for dataset in REQUIRED_DATASETS),
        {"selector": selector_available, "independent": available},
    )
    check(
        "selector_no_selection_hash_matches",
        selector.get("selected_sha256") == sha256(args.no_selection),
    )

    required_process_fields = {
        "model_calls": 0,
        "generation_calls": 0,
        "retrieval_calls": 0,
        "fresh_labels_accessed": 0,
        "selected_questions": 0,
        "fresh_generation_started": False,
        "prelabel_scoring_started": False,
    }
    for field, expected in required_process_fields.items():
        check(
            f"process_{field}",
            process.get(field) == expected,
            {"expected": expected, "actual": process.get(field)},
        )

    passed = all(item["passed"] for item in checks)
    coverage_categories = coverage.get("categories", [])
    if not isinstance(coverage_categories, list):
        coverage_categories = []

    result = {
        "status": "PASS" if passed else "FAIL",
        "schema_version": "daa-v2-fresh-availability-audit-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": args.project_root,
        "git_commit_or_tree_hash": args.git_state,
        "target_unique_questions_per_dataset": TARGET_PER_DATASET,
        "private_artifact_verification_sha256": sha256(args.private_artifacts),
        "source_counts": source_counts,
        "source_ledgers": source_records,
        "raw_source_hashes": raw_hashes,
        "forbidden_counts": forbidden_counts,
        "forbidden_category_coverage": {
            "path": str(args.forbidden_coverage),
            "sha256": sha256(args.forbidden_coverage),
            "category_count": len(coverage_categories),
        },
        "forbidden_ledgers": coverage_categories,
        "forbidden_union": {
            "path": str(args.forbidden_union),
            "sha256": sha256(args.forbidden_union),
            "unique_count": len(forbidden_set),
            "counts_by_dataset": forbidden_counts,
            "coverage_manifest_sha256": sha256(args.forbidden_coverage),
        },
        "overlap_checks": {
            "independently_recounted": True,
            "source_forbidden_overlap_counts": overlap,
        },
        "source_forbidden_overlap_counts": overlap,
        "available_after_exclusion": available,
        "selector_manifest_sha256": sha256(args.selector_manifest),
        "no_selection_sha256": sha256(args.no_selection),
        "process_evidence_sha256": sha256(args.process_evidence),
        "process_evidence": {field: process.get(field) for field in required_process_fields},
        "model_calls": process.get("model_calls"),
        "generation_calls": process.get("generation_calls"),
        "retrieval_calls": process.get("retrieval_calls"),
        "fresh_labels_accessed": process.get("fresh_labels_accessed"),
        "identifier_only_projection_evidence": {
            "source_ledgers_schema_exact": True,
            "forbidden_union_schema_exact": True,
            "gold_or_correctness_values_materialized_by_this_validator": 0,
        },
        "checks": checks,
        "selected_questions": 0,
        "stop_boundary": (
            "STOP after this audit. PASS does not authorize final ID selection, retrieval, "
            "generation, V2/GbV scoring, Gold mapping, or evaluation."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    if not passed:
        raise SystemExit("DAA-V2 availability audit failed; stop before fresh selection/generation")


if __name__ == "__main__":
    main()
