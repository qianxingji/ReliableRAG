#!/usr/bin/env python3
"""Create the combined V2/GbV pre-label gate and stop before Gold access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_GBV_DEV_THRESHOLDS = {
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


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, checks: list[dict]) -> None:
    checks.append({"check": message, "passed": bool(condition)})
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-preflight", type=Path, required=True)
    parser.add_argument("--v2-seal", type=Path, required=True)
    parser.add_argument("--gbv-provenance", type=Path, required=True)
    parser.add_argument("--gbv-match-seal", type=Path, required=True)
    parser.add_argument("--v2-actions", type=Path, required=True)
    parser.add_argument("--gbv-scores", type=Path, required=True)
    parser.add_argument("--gbv-actions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    preflight = load(args.fresh_preflight)
    v2 = load(args.v2_seal)
    gbv_prov = load(args.gbv_provenance)
    gbv_match = load(args.gbv_match_seal)
    checks: list[dict] = []

    require(preflight.get("status") == "PASS", "fresh structural/leakage preflight is PASS", checks)
    require(
        preflight.get("fresh_label_access_authorized") is False,
        "fresh preflight explicitly predates label access",
        checks,
    )
    require(v2.get("status") == "V2_PRELABEL_ACTION_SEAL", "V2 action seal status is valid", checks)
    require(v2.get("gold_or_outcome_input") is False, "V2 action seal used no Gold/outcome input", checks)
    require(
        int(v2.get("hgb_replace_count")) == int(v2.get("replace_count")),
        "raw HGB backbone ablation exactly matches V2 total action budget",
        checks,
    )
    require(v2.get("backbone_ablation_predeclared") is True, "raw HGB backbone ablation was predeclared", checks)
    require(
        gbv_prov.get("status") == "GBV_FRESH_PRELABEL_SCORE_SEAL_INPUT",
        "GbV fresh score provenance status is valid",
        checks,
    )
    require(gbv_prov.get("gold_or_outcome_input") is False, "GbV scoring used no Gold/outcome input", checks)
    require(
        gbv_match.get("status") == "GBV_PRELABEL_MATCHED_ACTION_SEAL",
        "GbV matched-action seal status is valid",
        checks,
    )
    require(gbv_match.get("gold_or_outcome_input") is False, "GbV action matching used no Gold/outcome input", checks)
    require(
        gbv_match.get("gbv_dev_selected_thresholds") == EXPECTED_GBV_DEV_THRESHOLDS,
        "GbV historical development thresholds exactly match the frozen published-baseline handoff",
        checks,
    )

    actual_v2_actions_hash = sha256(args.v2_actions)
    actual_gbv_scores_hash = sha256(args.gbv_scores)
    actual_gbv_actions_hash = sha256(args.gbv_actions)
    require(
        v2.get("actions_sha256") == actual_v2_actions_hash,
        "V2/HGB action file matches its seal hash",
        checks,
    )
    require(
        gbv_prov.get("scores_sha256") == actual_gbv_scores_hash,
        "GbV score ledger matches its provenance hash",
        checks,
    )
    require(
        gbv_match.get("gbv_actions_sha256") == actual_gbv_actions_hash,
        "GbV matched action file matches its seal hash",
        checks,
    )
    require(
        gbv_match.get("v2_actions_sha256") == actual_v2_actions_hash,
        "GbV matcher was bound to the exact sealed V2 actions",
        checks,
    )
    require(
        gbv_match.get("gbv_score_ledger_sha256") == actual_gbv_scores_hash,
        "GbV matcher was bound to the exact sealed GbV scores",
        checks,
    )
    require(
        v2.get("branches_sha256") == preflight.get("hashes", {}).get("branches_sha256"),
        "V2 seal uses the exact preflight canonical branch ledger",
        checks,
    )
    require(
        v2.get("score_ledger_sha256") == preflight.get("hashes", {}).get("v2_score_ledger_sha256"),
        "V2 seal uses the exact preflight V2 base-score ledger",
        checks,
    )
    require(
        int(gbv_match.get("v2_replace_count")) == int(v2.get("replace_count")),
        "GbV primary budget exactly matches V2 total replacement count",
        checks,
    )
    require(
        int(gbv_match.get("gbv_global_replace_count")) == int(v2.get("replace_count")),
        "GbV global comparator has exact V2 total budget",
        checks,
    )
    require(
        int(gbv_match.get("gbv_stratum_replace_count")) == int(v2.get("replace_count")),
        "GbV stratum comparator has exact V2 total budget",
        checks,
    )
    require(
        gbv_match.get("gbv_exact_stratum_counts") == gbv_match.get("v2_stratum_budgets"),
        "GbV secondary comparator exactly matches every V2 dataset x retriever budget",
        checks,
    )

    gate = {
        "status": "PASS",
        "stage": "DAA_V2_GBV_COMBINED_PRELABEL_GATE",
        "checks": checks,
        "trace_count": int(v2.get("trace_count")),
        "replace_count": int(v2.get("replace_count")),
        "hgb_replace_count": int(v2.get("hgb_replace_count")),
        "gbv_dev_selected_replace_count": int(gbv_match.get("gbv_dev_selected_replace_count")),
        "action_rate": v2.get("action_rate"),
        "gbv_dev_selected_thresholds": EXPECTED_GBV_DEV_THRESHOLDS,
        "hashes": {
            "fresh_preflight_sha256": sha256(args.fresh_preflight),
            "v2_seal_sha256": sha256(args.v2_seal),
            "gbv_provenance_sha256": sha256(args.gbv_provenance),
            "gbv_match_seal_sha256": sha256(args.gbv_match_seal),
            "v2_actions_sha256": actual_v2_actions_hash,
            "gbv_scores_sha256": actual_gbv_scores_hash,
            "gbv_actions_sha256": actual_gbv_actions_hash,
        },
        "fresh_label_access_authorized": False,
        "post_seal_evaluation_started": False,
        "stop_boundary": (
            "STOP. Do not load fresh Gold/correctness/outcome data in this execution. "
            "A separate responsible-human authorization is required for post-seal mapping/evaluation."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(gate, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
