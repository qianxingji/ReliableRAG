#!/usr/bin/env python3
"""Verify the manuscript's historical HGB definition against sealed evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def pdf_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return normalized(result.stdout)


def pdf_pages(path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.MULTILINE)
    if match is None:
        raise AssertionError(f"could not read page count: {path}")
    return int(match.group(1))


def reported_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--main-pdf",
        type=Path,
        default=ROOT / "output/pdf/manuscript.pdf",
    )
    parser.add_argument(
        "--supplement-pdf",
        type=Path,
        default=ROOT / "output/pdf/supplement.pdf",
    )
    args = parser.parse_args()

    checks: list[str] = []
    manuscript = (ROOT / "paper/manuscript.tex").read_text(encoding="utf-8")
    supplement = (ROOT / "paper/supplement.tex").read_text(encoding="utf-8")
    manuscript_lower = normalized(manuscript)
    supplement_lower = normalized(supplement)

    contract = (ROOT / "docs/cas_q2/HISTORICAL_TRAINING_REPLAY_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    replay = json.loads(
        (ROOT / "docs/cas_q2/HISTORICAL_TRAINING_REPLAY_RESULTS.json").read_text(
            encoding="utf-8"
        )
    )
    census = json.loads(
        (ROOT / "docs/cas_q3/P0_E_ORIGINAL_FIT_RECEIPT_CENSUS.json").read_text(
            encoding="utf-8"
        )
    )

    require(
        "hgb abbreviates histogram-based gradient boosting" in manuscript_lower,
        "main text expands HGB and identifies gradient boosting",
        checks,
    )
    require(
        "frozen historical pairwise selector" in manuscript_lower,
        "main text identifies HGB as a frozen historical pairwise selector",
        checks,
    )
    require(
        "48 state-symmetric features" in manuscript_lower,
        "main text states the 48-dimensional input",
        checks,
    )
    require(
        "same em status do not enter that fit" in manuscript_lower,
        "main text defines the informative-transition target boundary",
        checks,
    )
    require(
        "a larger hgb score therefore means stronger support for choosing $a_1$"
        in manuscript_lower,
        "main text defines HGB score direction",
        checks,
    )
    require(
        "neither refits the historical hgb estimator" in manuscript_lower,
        "main text separates HGB from current Recovery heads",
        checks,
    )

    required_supplement_terms = {
        "estimator identity": "histgradientboostingclassifier",
        "historical universe": "7,200 labeled traces from 4,800 question groups",
        "historical pair records": "1,539 available pair-feature records",
        "informative fit rows": "601 informative traces from 518 question groups",
        "teacher-forced likelihood cells": "mean teacher-forced token log probability",
        "eight-component branch vector": "eight-component vector",
        "lexical compatibility": "multiset token f1",
        "historical string similarity": "sequencematcher",
        "string-similarity disclosure": "rather than a neural semantic model",
        "five pair contexts": "the five pair-context variables",
        "48-dimensional construction": "eight branch differences and forty difference--context interactions",
        "identity exclusion": "dataset and retriever identities are absent",
        "antisymmetric augmentation": "duplicates each historical example as $(x,y)$ and $(-x,1-y)$",
        "HGB iteration count": "\\texttt{max\\_iter=300}",
        "HGB leaf count": "\\texttt{max\\_leaf\\_nodes=15}",
        "HGB learning rate": "learning rate 0.08",
        "HGB L2": "l2 regularization 1.0",
        "HGB seed": "final-fit seed 20261834",
        "no HGB parameter search": "no feature scaling or hyperparameter search",
        "raw versus calibrated HGB": "hgb-only$_r$ is a separate current l2-logistic recovery head",
        "literal replay boundary": "not the literal historical execution event",
    }
    for label, term in required_supplement_terms.items():
        require(term in supplement_lower, f"supplement defines {label}", checks)

    require(
        replay["status"] == "REVIEWED_LITERAL_BYTE_FAILURE_WITH_EXACT_NUMERICAL_MATCH",
        "sealed replay retains literal-byte failure status",
        checks,
    )
    require(
        replay["model_comparisons"]["state_symmetric_hgb"]["score_checks"] == 1539
        and replay["model_comparisons"]["state_symmetric_hgb"]["max_score_error"] == 0,
        "sealed replay confirms 1,539 exact HGB scores",
        checks,
    )
    require(
        replay["hgb_state_difference"]["original"] == 6
        and replay["hgb_state_difference"]["new"] == 1,
        "sealed replay retains the six-versus-one thread metadata mismatch",
        checks,
    )
    require(
        replay["all_array_buffer_hashes_and_named_fields_equal"] is True,
        "sealed replay confirms learned arrays and named fields",
        checks,
    )
    require(
        replay["historical_fit_time_receipts_still_missing"] == 7
        and census["interpretation"]["independent_original_fit_witness_recovered"] is False,
        "sealed evidence retains missing original-fit receipts and witness",
        checks,
    )

    expected_hashes = {
        "state_symmetric source": "3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717",
        "full_experiment source": "65713509ef6c8d094bb44ad2c47b0238ceade607616d3e729b31c56096326d50",
        "original HGB artifact": "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e",
    }
    for label, value in expected_hashes.items():
        require(value in contract or label == "original HGB artifact", f"contract binds {label}", checks)
        require(value in supplement, f"supplement reports {label} hash", checks)
    require(
        replay["model_comparisons"]["state_symmetric_hgb"]["original_sha256"]
        == expected_hashes["original HGB artifact"],
        "sealed replay binds the reported original HGB hash",
        checks,
    )

    main_pdf = args.main_pdf.resolve()
    supplement_pdf = args.supplement_pdf.resolve()
    require(main_pdf.is_file(), "compiled main PDF exists", checks)
    require(supplement_pdf.is_file(), "compiled supplement PDF exists", checks)
    main_pdf_text = pdf_text(main_pdf)
    supplement_pdf_text = pdf_text(supplement_pdf)
    require(
        "hgb abbreviates histogram-based gradient boosting" in main_pdf_text,
        "compiled main PDF contains the HGB definition",
        checks,
    )
    require(
        "frozen historical hgb score" in supplement_pdf_text,
        "compiled supplement contains the full HGB section",
        checks,
    )
    require(
        "histgradientboostingclassifier" in supplement_pdf_text
        and "sequencematcher" in supplement_pdf_text,
        "compiled supplement retains estimator and feature implementation names",
        checks,
    )
    require(pdf_pages(main_pdf) == 11, "compiled main PDF has 11 pages", checks)
    require(pdf_pages(supplement_pdf) == 4, "compiled supplement PDF has 4 pages", checks)

    result = {
        "schema_version": 1,
        "decision": "PASS_HGB_MANUSCRIPT_DEFINITION_AND_EVIDENCE_BINDING",
        "check_count": len(checks),
        "scientific_fits": 0,
        "model_forwards": 0,
        "main_pdf": {
            "path": reported_path(main_pdf),
            "sha256": sha256(main_pdf),
            "pages": pdf_pages(main_pdf),
        },
        "supplement_pdf": {
            "path": reported_path(supplement_pdf),
            "sha256": sha256(supplement_pdf),
            "pages": pdf_pages(supplement_pdf),
        },
        "checks": checks,
        "remaining_provenance_limit": (
            "The original per-estimator fit-time ID/matrix receipts and an independent "
            "original-fit witness remain unavailable."
        ),
    }
    output = ROOT / "paper/HGB_DEFINITION_VERIFICATION.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
