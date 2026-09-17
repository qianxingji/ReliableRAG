"""Independent full-ledger reconciliation of the two C3 census processes."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def require(value: Any, message: str) -> None:
    if not value: raise ValueError(message)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(2 * 1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False); stream.write("\n")


def verify_mode(path: Path) -> tuple[dict[str, Any], dict[tuple[str, str, str, str], dict[str, Any]], collections.Counter]:
    manifest = load(path / "SHA256_MANIFEST.json")
    require([x["path"] for x in manifest["files"]] == ["OBSERVATIONS.jsonl", "DISCREPANCIES.jsonl", "RESULT.json"], "mode manifest schema")
    for entry in manifest["files"]:
        file = path / entry["path"]
        require(file.stat().st_size == entry["size_bytes"] and sha(file) == entry["sha256"], "mode file hash")
    result = load(path / "RESULT.json"); require(result["status"] == "COMPLETE_DIAGNOSTIC_CENSUS_MODE", "complete mode")
    observations = {}; classes = collections.Counter()
    with (path / "OBSERVATIONS.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line); key = (row["pass"], row["dataset"], row["retriever"], row["sample_id"])
            require(key not in observations, "unique observation key")
            observations[key] = row; classes[row["classification"]] += 1
    require(len(observations) == 18180 and classes == collections.Counter({k[15:]: v for k, v in result["counts"].items() if k.startswith("classification_")}), "observation/result reconciliation")
    ledger_counts = collections.Counter()
    with (path / "DISCREPANCIES.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line); require((row["pass"], row["dataset"], row["retriever"], row["sample_id"]) in observations, "discrepancy key")
            ledger_counts[row["kind"]] += 1
    require(ledger_counts["component"] == result["counts"].get("component_ledger_entries", 0) and
            ledger_counts["final_ranking"] == result["counts"].get("final_ranking_ledger_entries", 0) and
            ledger_counts["replacement"] == result["counts"].get("replacement_ledger_entries", 0), "complete discrepancy ledger")
    return result, observations, ledger_counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--single", required=True, type=Path); parser.add_argument("--default", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), "single-use reconciliation output")
    single_result, single, single_ledger = verify_mode(args.single)
    default_result, default, default_ledger = verify_mode(args.default)
    require(set(single) == set(default), "identical two-mode key set")
    mode_differences = collections.Counter(); mode_rows = 0
    replay_matches = {"single": 0, "default": 0}
    for mode, observations in (("single", single), ("default", default)):
        canonical = {k[1:]: row for k, row in observations.items() if k[0] == "canonical"}
        for key, row in observations.items():
            if key[0] != "replay": continue
            parent = canonical[key[1:]]
            for field in ("repair_record_sha256", "repair_query_record_sha256", "repair_query_sha256", "dense_query_vector_bytes_sha256"):
                require(row[field] == parent[field], f"{mode} replay signature/bytes")
            replay_matches[mode] += 1
    for key in sorted(single):
        left, right = single[key], default[key]
        changed = False
        for field in ("recomputed_score_vector_sha256", "component_comparisons", "final_ranking_comparison", "replacement_equal", "classification"):
            if left[field] != right[field]: mode_differences[field] += 1; changed = True
        if changed: mode_rows += 1
    require(replay_matches == {"single": 180, "default": 180}, "all fixed replay signatures")
    output = {"status": "PASS_COMPLETE_INDEPENDENT_CENSUS_RECONCILIATION", "cas_q2_status": "NOT READY",
        "modes": {"single": {"counts": single_result["counts"], "ledger_counts": dict(single_ledger)},
                  "default": {"counts": default_result["counts"], "ledger_counts": dict(default_ledger)}},
        "exact_key_count_per_mode": 18180, "fixed_replay_signatures_and_query_vector_bytes_exact": replay_matches,
        "rows_with_cross_mode_difference": mode_rows, "cross_mode_difference_fields": dict(mode_differences),
        "default_exact_all_saved_fields": default_result["counts"].get("classification_exact", 0) == 18180,
        "single_exact_all_saved_fields": single_result["counts"].get("classification_exact", 0) == 18180,
        "neural_forwards": 0, "scientific_fits": 0, "fresh_gold_values_materialized": 0,
        "interpretation": "Complete arithmetic census only; no original full-validator acceptance."}
    write(args.output, output); print(json.dumps(output, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
