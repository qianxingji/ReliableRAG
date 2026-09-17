"""Independently reconstruct the Mistral test common prelabel freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_runtime_io import CPU_TEST_SHA
from scripts.validate_mistral_test_a0_query import (
    DATASETS, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_TEST_POOL_MANIFEST_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
    read_rows, require, sha256, validate_selected_manifest,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_RETRIEVAL_MANIFEST_SHA256 = (
    "81b9c7163adf669a828bd2ef772e14fecbda727cf596bced45856a1e699a354d"
)
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


def object_sha(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def finite_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    require(manifest["status"] == "PASS" and manifest["exact_recursive_coverage"] is True,
            "MANIFEST_STATUS")
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members,
                "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def current_manifest_member_paths(
    namespace: Path, expected_manifest_sha256: str,
) -> set[Path]:
    namespace = namespace.resolve(); manifest_path = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest_path) == expected_manifest_sha256,
            "CURRENT_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    for item in value["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members
                and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "CURRENT_MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()},
            "CURRENT_MANIFEST_COVERAGE")
    return {manifest_path.resolve(), *members}


def validate_predecessors(root: Path) -> tuple[Path, Path, Path, Path]:
    hgb = root / "hgb_signal"; hgb_validation = root / "hgb_signal_validation/VALIDATION.json"
    gbv = root / "gbv"; gbv_validation = root / "gbv_validation/VALIDATION.json"
    require(hgb_validation.is_file() and gbv_validation.is_file(),
            "PREDECESSOR_VALIDATIONS_REQUIRED")
    validate_manifest(hgb); validate_manifest(gbv)
    hgb_result = json.loads(hgb_validation.read_text(encoding="utf-8"))
    gbv_result = json.loads(gbv_validation.read_text(encoding="utf-8"))
    require(hgb_result["status"]
            == "PASS_INDEPENDENT_FORMULA_MISTRAL_TEST_HGB_SIGNAL"
            and hgb_result["producer_receipt_sha256"] == sha256(hgb / "STAGE_RECEIPT.json")
            and hgb_result["hgb_signal_rows_sha256"] == sha256(hgb / "HGB_SIGNAL_ROWS.jsonl")
            and hgb_result["project_gold_values_read"] == 0
            and hgb_result["test_gold_values_read"] == 0
            and hgb_result["test_outcome_values_read"] == 0
            and hgb_result["scientific_fits"] == 0
            and hgb_result["test_input_rows_read"] == EXPECTED_TRACES,
            "HGB_ACCEPTANCE")
    require(gbv_result["status"]
            == "PASS_INDEPENDENT_TOKENIZER_LOGIT_MISTRAL_TEST_GBV"
            and gbv_result["producer_receipt_sha256"] == sha256(gbv / "STAGE_RECEIPT.json")
            and gbv_result["gbv_rows_sha256"] == sha256(gbv / "GBV_ROWS.jsonl")
            and gbv_result["project_gold_values_read"] == 0
            and gbv_result["test_gold_values_read"] == 0
            and gbv_result["test_outcome_values_read"] == 0
            and gbv_result["scientific_fits"] == 0
            and gbv_result["test_input_rows_read"] == EXPECTED_TRACES,
            "GBV_ACCEPTANCE")
    return hgb, hgb_validation, gbv, gbv_validation


def reconstruct_prelabel_row(hgb: dict, gbv: dict) -> dict:
    require(set(hgb) == HGB_FIELDS and set(gbv) == GBV_FIELDS,
            "SOURCE_SCHEMA")
    identity = {name: hgb[name] for name in IDENTITY_FIELDS}
    require(all(gbv[name] == value for name, value in identity.items()),
            "SOURCE_IDENTITY")
    require(type(hgb["eligible"]) is bool and type(gbv["pair_eligible"]) is bool
            and type(gbv["eligible"]) is bool
            and hgb["eligible"] is gbv["pair_eligible"], "NATIVE_MASK")
    native = hgb["eligible"]; hgb_score = hgb["hgb_score"]
    if native:
        require(hgb["forced_keep_reason"] is None and finite_number(hgb_score)
                and 0.0 < hgb_score < 1.0, "HGB_VALUE")
    else:
        require(isinstance(hgb["forced_keep_reason"], str)
                and hgb["forced_keep_reason"] and hgb_score is None
                and gbv["eligible"] is False
                and gbv["forced_keep_reason"] == hgb["forced_keep_reason"],
                "NATIVE_KEEP")
    f0, f1, margin = gbv["F0"], gbv["F1"], gbv["gbv_margin"]
    if gbv["eligible"]:
        require(native and gbv["forced_keep_reason"] is None
                and all(finite_number(value) for value in (f0, f1, margin))
                and 0.0 <= f0 <= 1.0 and 0.0 <= f1 <= 1.0
                and margin == f1 - f0
                and gbv["e0_chunk_count"] > 0 and gbv["e1_chunk_count"] > 0
                and set(gbv["branch_receipt_sha256"]) == {"a0_e0", "a1_e1"},
                "COMPLETE_GBV")
        eligible = True; reason = None
    elif native:
        require(isinstance(gbv["forced_keep_reason"], str)
                and gbv["forced_keep_reason"].startswith("nli_unscorable:")
                and margin is None and f1 is None
                and (f0 is None or (finite_number(f0) and 0.0 <= f0 <= 1.0))
                and gbv["e1_chunk_count"] == 0
                and ((f0 is None and gbv["e0_chunk_count"] == 0)
                     or (f0 is not None and gbv["e0_chunk_count"] > 0))
                and set(gbv["branch_receipt_sha256"]) in (
                    {"a0_e0"}, {"a0_e0", "a1_e1"}
                ), "NLI_KEEP")
        eligible = False; reason = gbv["forced_keep_reason"]
    else:
        require(f0 is None and f1 is None and margin is None
                and gbv["e0_chunk_count"] == gbv["e1_chunk_count"] == 0
                and gbv["branch_receipt_sha256"] == {}, "NO_NATIVE_GBV")
        eligible = False; reason = hgb["forced_keep_reason"]
    signals = {"hgb_score": hgb_score, "gbv_F0": f0,
               "gbv_F1": f1, "gbv_margin": margin}
    return {
        **identity, "pair_eligible": native, "eligible": eligible,
        "forced_keep_reason": reason, **signals,
        "feature_vectors": {
            method: [signals[name] for name in fields]
            for method, fields in METHOD_FEATURES.items()
        },
        "source_bindings": {
            "hgb_signal_row_sha256": object_sha(hgb),
            "gbv_row_sha256": object_sha(gbv),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original = args.project_root.resolve()
    root = args.test_root.resolve()
    output = (args.output.resolve() if args.output else
              (root / "prelabel_validation/VALIDATION.json").resolve())
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve()
            and output == (root / "prelabel_validation/VALIDATION.json").resolve()
            and not output.exists(), "FIXED_ROOTS_OR_OUTPUT")
    hgb, hgb_validation, gbv, gbv_validation = validate_predecessors(root)
    namespace = root / "prelabel"; validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "PASS_MISTRAL_TEST_PRELABEL_PENDING_INDEPENDENT"
            and receipt["completed_traces"] == EXPECTED_TRACES
            and receipt["project_gold_values_read"] == 0
            and receipt["test_gold_values_read"] == 0
            and receipt["test_outcome_values_read"] == 0
            and receipt["scientific_fits"] == 0
            and receipt["test_input_rows_read"] == EXPECTED_TRACES
            and receipt["neural_model_loads"] == 0
            and receipt["neural_model_forwards"] == 0
            and receipt["hgb_model_loads"] == 0,
            "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"]
            and freeze["stage"] == "prelabel"
            and freeze["expected_traces"] == EXPECTED_TRACES
            and freeze["method_features"]
            == {key: list(value) for key, value in METHOD_FEATURES.items()}
            and freeze["common_eligibility"]
            == "native_pair_and_finite_hgb_and_complete_gbv_margin"
            and freeze["python"] == str(Path(sys.executable).resolve())
            and freeze["test_gold_access"] == "FORBIDDEN"
            and freeze["test_outcome_access"] == "FORBIDDEN"
            and freeze["scientific_fit_access"] == "FORBIDDEN",
            "EXECUTABLE_FREEZE")
    input_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(len(input_paths) == len(freeze["inputs"]), "UNIQUE_FROZEN_INPUTS")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_INPUT")

    preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
    pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
    retrieval = REPO / "outputs/cas_q2/empirical_retrieval_v1"
    cpu_tests = REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1"
    input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
    pool_relatives = tuple(
        f"{folder}/{dataset}.jsonl"
        for folder in ("pools", "runtime") for dataset in DATASETS
    ) + ("INDEPENDENT_VALIDATION.json",)
    required_inputs = {
        *{path.resolve() for path in validate_selected_manifest(
            preparation, EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
            ("TRACE_MANIFEST_PRIVATE.jsonl",),
        )},
        *{path.resolve() for path in validate_selected_manifest(
            pool_root, EXPECTED_TEST_POOL_MANIFEST_SHA256, pool_relatives,
        )},
        *current_manifest_member_paths(retrieval, EXPECTED_RETRIEVAL_MANIFEST_SHA256),
        *current_manifest_member_paths(cpu_tests, CPU_TEST_SHA),
        *current_manifest_member_paths(
            input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
        ),
        *current_manifest_member_paths(hgb, sha256(hgb / "SHA256_MANIFEST.json")),
        hgb_validation.resolve(),
        *current_manifest_member_paths(gbv, sha256(gbv / "SHA256_MANIFEST.json")),
        gbv_validation.resolve(),
        (REPO / "scripts/run_mistral_test_prelabel_freeze.py").resolve(),
        Path(__file__).resolve(),
        (REPO / "scripts/mistral_development_acquisition_common.py").resolve(),
        (REPO / "scripts/mistral_development_scoring_common.py").resolve(),
        (REPO / "scripts/empirical_runtime_io.py").resolve(),
        (REPO / "scripts/run_mistral_test_a0_query.py").resolve(),
        (REPO / "scripts/run_mistral_test_repair.py").resolve(),
        (REPO / "scripts/validate_mistral_test_a0_query.py").resolve(),
        (REPO / "src/arbitration/mistral_reader_runtime.py").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_PRELABEL_INPUT_GRAPH_AMENDMENT_2026-09-17.md").resolve(),
        Path(sys.executable).resolve(),
    }
    require(required_inputs == input_paths, "NONEXACT_FROZEN_INPUT_GRAPH")

    trace_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
    require(trace_path.resolve() in input_paths, "FROZEN_TEST_TRACE")
    traces = read_rows(trace_path)
    frozen_rows = [row for row in read_rows(
        input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
    ) if row.get("cohort") == "test"]
    hgb_rows = read_rows(hgb / "HGB_SIGNAL_ROWS.jsonl")
    gbv_rows = read_rows(gbv / "GBV_ROWS.jsonl")
    rows = read_rows(namespace / "PRELABEL_ROWS.jsonl")
    require(len(traces) == len(frozen_rows) == len(hgb_rows) == len(gbv_rows)
            == len(rows) == EXPECTED_TRACES, "ROW_COUNTS")
    forced = {}; roles = {}; eligible_roles = {}; pair_eligible = common_eligible = 0
    checks = 0
    for position, (trace, frozen, hgb_row, gbv_row, row) in enumerate(zip(
            traces, frozen_rows, hgb_rows, gbv_rows, rows, strict=True)):
        require(trace["position"] == frozen["position"] == position
                and (trace["dataset"], trace["retriever"], trace["sample_id"], frozen["role"])
                == (hgb_row["dataset"], hgb_row["retriever"],
                    hgb_row["sample_id"], hgb_row["role"])
                and frozen["role"] == "test", "FROZEN_IDENTITY")
        expected = reconstruct_prelabel_row(hgb_row, gbv_row)
        require(row == expected, "PRELABEL_ROW_RECONSTRUCTION")
        roles[row["role"]] = roles.get(row["role"], 0) + 1
        pair_eligible += int(row["pair_eligible"])
        common_eligible += int(row["eligible"])
        if row["eligible"]:
            eligible_roles[row["role"]] = eligible_roles.get(row["role"], 0) + 1
        else:
            reason = row["forced_keep_reason"]
            forced[reason] = forced.get(reason, 0) + 1
        checks += 42
    require(roles == {"test": EXPECTED_TRACES}
            and receipt["role_counts"] == roles
            and receipt["eligible_role_counts"] == eligible_roles
            and receipt["pair_eligible_traces"] == pair_eligible
            and receipt["common_eligible_traces"] == common_eligible
            and receipt["forced_keep_counts"] == forced
            and receipt["methods"] == list(METHOD_FEATURES), "RECEIPT_COUNTS")
    expected_record = {
        "path": str((namespace / "PRELABEL_ROWS.jsonl").resolve()),
        "size_bytes": (namespace / "PRELABEL_ROWS.jsonl").stat().st_size,
        "sha256": sha256(namespace / "PRELABEL_ROWS.jsonl"),
    }
    require(receipt["prelabel_rows"] == expected_record, "PRELABEL_RECEIPT_BINDING")
    require(all(name not in sys.modules for name in ("torch", "transformers", "sklearn")),
            "MODEL_RUNTIME_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_MISTRAL_TEST_PRELABEL_FREEZE",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_manifest_sha256": sha256(namespace / "SHA256_MANIFEST.json"),
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "prelabel_rows_sha256": sha256(namespace / "PRELABEL_ROWS.jsonl"),
        "traces_validated": EXPECTED_TRACES,
        "pair_eligible_traces": pair_eligible,
        "common_eligible_traces": common_eligible,
        "role_counts": roles, "eligible_role_counts": eligible_roles,
        "forced_keep_counts": forced, "methods": list(METHOD_FEATURES),
        "neural_model_loads": 0, "neural_model_forwards": 0,
        "hgb_model_loads": 0, "project_gold_values_read": 0,
        "test_gold_values_read": 0, "test_outcome_values_read": 0,
        "scientific_fits": 0, "test_input_rows_read": EXPECTED_TRACES,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
