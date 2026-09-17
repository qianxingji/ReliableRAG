"""Freeze common Mistral test features before any test-outcome access."""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_runtime_io import CPU_TEST_SHA
from scripts.mistral_development_acquisition_common import (
    read_jsonl, record, sha256, verify_manifest, write_json_durable,
)
from scripts.mistral_development_scoring_common import write_bytes_once
from scripts.run_mistral_test_a0_query import (
    DATASETS, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_INPUT_LEDGER_SHA256, EXPECTED_TEST_POOL_MANIFEST_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256, EXPECTED_TEST_TRACE_SHA256,
    validate_selected_manifest, validate_test_binding,
)
from scripts.run_mistral_test_repair import EXPECTED_RETRIEVAL_MANIFEST_SHA256
from src.arbitration.mistral_reader_runtime import canonical, object_sha256, require


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
METHOD_FEATURES = {
    "HGB_GBV_R": ("hgb_score", "gbv_margin"),
    "HGB_ONLY_R": ("hgb_score",),
    "GBV_ONLY_R": ("gbv_margin",),
}
IDENTITY_FIELDS = ("dataset", "retriever", "sample_id", "position", "role")
HGB_FIELDS = frozenset({
    *IDENTITY_FIELDS, "eligible", "forced_keep_reason", "bindings",
    "feature_row_sha256", "hgb_score",
})
GBV_FIELDS = frozenset({
    *IDENTITY_FIELDS, "pair_eligible", "eligible", "forced_keep_reason",
    "F0", "F1", "gbv_margin", "e0_premise_count", "e1_premise_count",
    "e0_chunk_count", "e1_chunk_count", "branch_receipt_sha256",
    "model_id", "model_revision",
})
MAX_STAGE_SECONDS = 60 * 60


def finite_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_predecessors(root: Path) -> tuple[Path, Path, Path, Path]:
    hgb = root / "hgb_signal"
    hgb_validation = root / "hgb_signal_validation/VALIDATION.json"
    gbv = root / "gbv"
    gbv_validation = root / "gbv_validation/VALIDATION.json"
    require(all(path.is_file() for path in (
        hgb / "SHA256_MANIFEST.json", hgb_validation,
        gbv / "SHA256_MANIFEST.json", gbv_validation,
    )), "PRELABEL_PREDECESSORS_REQUIRED")
    verify_manifest(hgb, sha256(hgb / "SHA256_MANIFEST.json"))
    verify_manifest(gbv, sha256(gbv / "SHA256_MANIFEST.json"))
    require(json.loads((hgb / "SHA256_MANIFEST.json").read_text(encoding="utf-8"))["status"]
            == "PASS"
            and json.loads((gbv / "SHA256_MANIFEST.json").read_text(encoding="utf-8"))["status"]
            == "PASS", "PREDECESSOR_MANIFEST_STATUS")
    hgb_result = json.loads(hgb_validation.read_text(encoding="utf-8"))
    gbv_result = json.loads(gbv_validation.read_text(encoding="utf-8"))
    require(
        hgb_result["status"] == "PASS_INDEPENDENT_FORMULA_MISTRAL_TEST_HGB_SIGNAL"
        and hgb_result["producer_receipt_sha256"] == sha256(hgb / "STAGE_RECEIPT.json")
        and hgb_result["hgb_signal_rows_sha256"] == sha256(hgb / "HGB_SIGNAL_ROWS.jsonl")
        and hgb_result["project_gold_values_read"] == 0
        and hgb_result["test_gold_values_read"] == 0
        and hgb_result["test_outcome_values_read"] == 0
        and hgb_result["scientific_fits"] == 0
        and hgb_result["test_input_rows_read"] == EXPECTED_TRACES,
        "HGB_ACCEPTANCE_BINDING",
    )
    require(
        gbv_result["status"] == "PASS_INDEPENDENT_TOKENIZER_LOGIT_MISTRAL_TEST_GBV"
        and gbv_result["producer_receipt_sha256"] == sha256(gbv / "STAGE_RECEIPT.json")
        and gbv_result["gbv_rows_sha256"] == sha256(gbv / "GBV_ROWS.jsonl")
        and gbv_result["project_gold_values_read"] == 0
        and gbv_result["test_gold_values_read"] == 0
        and gbv_result["test_outcome_values_read"] == 0
        and gbv_result["scientific_fits"] == 0
        and gbv_result["test_input_rows_read"] == EXPECTED_TRACES,
        "GBV_ACCEPTANCE_BINDING",
    )
    return hgb, hgb_validation, gbv, gbv_validation


def merge_prelabel_row(hgb: dict, gbv: dict) -> dict:
    require(set(hgb) == HGB_FIELDS and set(gbv) == GBV_FIELDS,
            "PRELABEL_SOURCE_SCHEMA")
    identity = {name: hgb[name] for name in IDENTITY_FIELDS}
    require(all(gbv[name] == value for name, value in identity.items()),
            "PRELABEL_SOURCE_IDENTITY")
    require(type(hgb["eligible"]) is bool and type(gbv["pair_eligible"]) is bool
            and type(gbv["eligible"]) is bool
            and hgb["eligible"] is gbv["pair_eligible"],
            "PRELABEL_NATIVE_ELIGIBILITY")
    native_eligible = hgb["eligible"]
    hgb_score = hgb["hgb_score"]
    if native_eligible:
        require(hgb["forced_keep_reason"] is None and finite_number(hgb_score)
                and 0.0 < hgb_score < 1.0, "PRELABEL_HGB_SCORE")
    else:
        require(isinstance(hgb["forced_keep_reason"], str)
                and hgb["forced_keep_reason"]
                and hgb_score is None and gbv["eligible"] is False
                and gbv["forced_keep_reason"] == hgb["forced_keep_reason"],
                "PRELABEL_NATIVE_FORCED_KEEP")

    f0, f1, margin = gbv["F0"], gbv["F1"], gbv["gbv_margin"]
    if gbv["eligible"]:
        require(native_eligible and gbv["forced_keep_reason"] is None
                and all(finite_number(value) for value in (f0, f1, margin))
                and 0.0 <= f0 <= 1.0 and 0.0 <= f1 <= 1.0
                and margin == f1 - f0
                and gbv["e0_chunk_count"] > 0 and gbv["e1_chunk_count"] > 0
                and set(gbv["branch_receipt_sha256"]) == {"a0_e0", "a1_e1"},
                "PRELABEL_COMPLETE_GBV")
        eligible = True
        reason = None
    elif native_eligible:
        require(isinstance(gbv["forced_keep_reason"], str)
                and gbv["forced_keep_reason"].startswith("nli_unscorable:")
                and margin is None and f1 is None
                and (f0 is None or (finite_number(f0) and 0.0 <= f0 <= 1.0))
                and gbv["e1_chunk_count"] == 0
                and ((f0 is None and gbv["e0_chunk_count"] == 0)
                     or (f0 is not None and gbv["e0_chunk_count"] > 0))
                and set(gbv["branch_receipt_sha256"]) in (
                    {"a0_e0"}, {"a0_e0", "a1_e1"}
                ), "PRELABEL_NLI_FORCED_KEEP")
        eligible = False
        reason = gbv["forced_keep_reason"]
    else:
        require(f0 is None and f1 is None and margin is None
                and gbv["e0_chunk_count"] == gbv["e1_chunk_count"] == 0
                and gbv["branch_receipt_sha256"] == {},
                "PRELABEL_NO_NATIVE_GBV_WORK")
        eligible = False
        reason = hgb["forced_keep_reason"]

    signals = {
        "hgb_score": hgb_score,
        "gbv_F0": f0,
        "gbv_F1": f1,
        "gbv_margin": margin,
    }
    return {
        **identity,
        "pair_eligible": native_eligible,
        "eligible": eligible,
        "forced_keep_reason": reason,
        **signals,
        "feature_vectors": {
            method: [signals[name] for name in fields]
            for method, fields in METHOD_FEATURES.items()
        },
        "source_bindings": {
            "hgb_signal_row_sha256": object_sha256(hgb),
            "gbv_row_sha256": object_sha256(gbv),
        },
    }


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path)
            item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files, "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    original = args.project_root.resolve()
    root = args.test_root.resolve()
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve(),
            "FIXED_ROOTS")
    hgb, hgb_validation, gbv, gbv_validation = validate_predecessors(root)
    stage_output = root / "prelabel"
    require(not any((stage_output / name).exists() for name in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json", "SHA256_MANIFEST.json")),
            "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    ).strip(), "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    started = time.perf_counter()
    result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "prelabel", "project_gold_values_read": 0,
        "test_gold_values_read": 0, "test_outcome_values_read": 0,
        "scientific_fits": 0, "test_input_rows_read": 0,
        "neural_model_loads": 0, "neural_model_forwards": 0,
        "hgb_model_loads": 0,
    }
    try:
        if not args.resume:
            stage_output.mkdir(parents=True, exist_ok=False)
        require(all(name not in sys.modules for name in
                    ("torch", "transformers", "sklearn")),
                "MODEL_RUNTIME_ALREADY_LOADED")
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
                and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256,
                "INPUT_FREEZE")
        preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
        pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        retrieval = REPO / "outputs/cas_q2/empirical_retrieval_v1"
        cpu_tests = REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1"
        trace_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
        require(sha256(trace_path) == EXPECTED_TEST_TRACE_SHA256, "TEST_TRACE_PIN")
        pool_relatives = tuple(
            f"{folder}/{dataset}.jsonl"
            for folder in ("pools", "runtime") for dataset in DATASETS
        ) + ("INDEPENDENT_VALIDATION.json",)
        paths = [
            *validate_selected_manifest(
                preparation, EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
                ("TRACE_MANIFEST_PRIVATE.jsonl",),
            ),
            *validate_selected_manifest(
                pool_root, EXPECTED_TEST_POOL_MANIFEST_SHA256, pool_relatives,
            ),
            *verify_manifest(retrieval, EXPECTED_RETRIEVAL_MANIFEST_SHA256),
            *verify_manifest(cpu_tests, CPU_TEST_SHA),
            *verify_manifest(input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256),
            *verify_manifest(hgb, sha256(hgb / "SHA256_MANIFEST.json")),
            hgb_validation,
            *verify_manifest(gbv, sha256(gbv / "SHA256_MANIFEST.json")),
            gbv_validation,
        ]
        controls = [
            Path(__file__),
            REPO / "scripts/validate_mistral_test_prelabel_freeze.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/mistral_development_scoring_common.py",
            REPO / "scripts/empirical_runtime_io.py",
            REPO / "scripts/run_mistral_test_a0_query.py",
            REPO / "scripts/run_mistral_test_repair.py",
            REPO / "scripts/validate_mistral_test_a0_query.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_TEST_PRELABEL_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            Path(sys.executable),
        ]
        input_records = [record(path) for path in sorted(
            {Path(path).resolve() for path in [*paths, *controls]}, key=str
        )]
        require(len({item["path"] for item in input_records}) == len(input_records),
                "UNIQUE_INPUT_RECORDS")
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_TEST_OUTCOME_ACCESS",
            "source_commit": commit, "stage": "prelabel",
            "expected_traces": EXPECTED_TRACES,
            "method_features": {key: list(value) for key, value in METHOD_FEATURES.items()},
            "common_eligibility": "native_pair_and_finite_hgb_and_complete_gbv_margin",
            "inputs": input_records, "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "test_gold_access": "FORBIDDEN",
            "test_outcome_access": "FORBIDDEN",
            "scientific_fit_access": "FORBIDDEN",
            "scope": "test feature rows only; neural models/Gold/outcomes/fit/tuning forbidden",
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                    "RESUME_FREEZE_MISMATCH")
        else:
            write_json_durable(freeze_path, freeze)

        traces = list(read_jsonl(trace_path))
        test_rows = validate_test_binding(traces, read_jsonl(frozen_ledger))
        result["test_input_rows_read"] = EXPECTED_TRACES
        hgb_rows = list(read_jsonl(hgb / "HGB_SIGNAL_ROWS.jsonl"))
        gbv_rows = list(read_jsonl(gbv / "GBV_ROWS.jsonl"))
        require(len(hgb_rows) == len(gbv_rows) == EXPECTED_TRACES,
                "PRELABEL_SOURCE_COUNTS")
        rows = []
        forced = collections.Counter()
        role_counts = collections.Counter()
        eligible_role_counts = collections.Counter()
        for position, (trace, frozen, hgb_row, gbv_row) in enumerate(zip(
                traces, test_rows, hgb_rows, gbv_rows, strict=True)):
            require(trace["position"] == frozen["position"] == position
                    and all(hgb_row[name] == trace[name] for name in
                            ("dataset", "retriever", "sample_id", "position"))
                    and hgb_row["role"] == frozen["role"] == "test",
                    "PRELABEL_FROZEN_IDENTITY")
            row = merge_prelabel_row(hgb_row, gbv_row)
            rows.append(row)
            role_counts[row["role"]] += 1
            if row["eligible"]:
                eligible_role_counts[row["role"]] += 1
            else:
                forced[row["forced_keep_reason"]] += 1
        require(role_counts == {"test": EXPECTED_TRACES}, "PRELABEL_ROLE_COUNTS")
        raw = b"".join(canonical(row) + b"\n" for row in rows)
        write_bytes_once(stage_output / "PRELABEL_ROWS.jsonl", raw)
        for item in input_records:
            require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_TEST_PRELABEL_PENDING_INDEPENDENT",
            completed_traces=EXPECTED_TRACES,
            pair_eligible_traces=sum(row["pair_eligible"] for row in rows),
            common_eligible_traces=sum(row["eligible"] for row in rows),
            role_counts=dict(role_counts),
            eligible_role_counts=dict(eligible_role_counts),
            forced_keep_counts=dict(forced),
            methods=list(METHOD_FEATURES),
            prelabel_rows=record(stage_output / "PRELABEL_ROWS.jsonl"),
            elapsed_seconds=elapsed,
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        result.update(
            status="FAIL_MISTRAL_TEST_PRELABEL",
            error_type=type(exc).__name__, diagnostic=str(exc),
            traceback=traceback.format_exc(), elapsed_seconds=time.perf_counter() - started,
        )
        if stage_output.is_dir() and not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result)
            seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
