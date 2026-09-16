"""Run the frozen equal-budget head search on Mistral development rows only."""

from __future__ import annotations

import argparse
import collections
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from threadpoolctl import threadpool_info, threadpool_limits

from scripts.mistral_development_acquisition_common import (
    read_jsonl, record, sha256, verify_manifest, write_json_durable,
)
from scripts.mistral_development_scoring_common import write_bytes_once
from src.arbitration.mistral_reader_runtime import canonical, object_sha256, require
from src.arbitration.reader_development_tuning import (
    BASE_FIXED, C_SEARCH_VALUES, C_TIE_ORDER, FOLD_PREFIX, PLATT_FIXED,
    VARIANT_WIDTHS, candidate_grid, tune_recovery_head,
)


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q3"
METHODS = ("HGB_GBV_R", "HGB_ONLY_R", "GBV_ONLY_R")
EXPECTED_TRACES = 13_500
EXPECTED_FIT_TRACES = 10_800
EXPECTED_CAL_TRACES = 2_700
EXPECTED_SEARCH_FIT_ATTEMPTS = 78
EXPECTED_FIT_ATTEMPTS = 84
EXPECTED_EVENT_ROWS = 168
MAX_STAGE_SECONDS = 60 * 60
IDENTITY_FIELDS = ("dataset", "retriever", "sample_id", "position", "role")
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
PRELABEL_FIELDS = frozenset({
    *IDENTITY_FIELDS, "pair_eligible", "eligible", "forced_keep_reason",
    "hgb_score", "gbv_F0", "gbv_F1", "gbv_margin", "feature_vectors",
    "source_bindings",
})
OUTCOME_FIELDS = frozenset({
    *IDENTITY_FIELDS, "prelabel_row_sha256", "a0_receipt_sha256",
    "a1_receipt_sha256", "a0_em", "a1_em", "a0_f1", "a1_f1",
})


def validate_predecessors(root: Path) -> tuple[Path, Path, Path, Path]:
    prelabel = root / "prelabel"
    prelabel_validation = root / "prelabel_validation/VALIDATION.json"
    outcomes = root / "development_outcomes"
    outcomes_validation = root / "development_outcomes_validation/VALIDATION.json"
    require(prelabel_validation.is_file() and outcomes_validation.is_file(),
            "TUNING_PREDECESSOR_VALIDATIONS_REQUIRED")
    verify_manifest(prelabel, sha256(prelabel / "SHA256_MANIFEST.json"))
    verify_manifest(outcomes, sha256(outcomes / "SHA256_MANIFEST.json"))
    left = json.loads(prelabel_validation.read_text(encoding="utf-8"))
    right = json.loads(outcomes_validation.read_text(encoding="utf-8"))
    require(
        left["status"] == "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_PRELABEL_FREEZE"
        and left["producer_manifest_sha256"]
        == sha256(prelabel / "SHA256_MANIFEST.json")
        and left["producer_receipt_sha256"] == sha256(prelabel / "STAGE_RECEIPT.json")
        and left["prelabel_rows_sha256"] == sha256(prelabel / "PRELABEL_ROWS.jsonl"),
        "TUNING_PRELABEL_ACCEPTANCE",
    )
    require(
        right["status"] == "PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_OUTCOMES"
        and right["producer_manifest_sha256"]
        == sha256(outcomes / "SHA256_MANIFEST.json")
        and right["producer_receipt_sha256"] == sha256(outcomes / "STAGE_RECEIPT.json")
        and right["development_outcomes_sha256"]
        == sha256(outcomes / "DEVELOPMENT_OUTCOMES.jsonl")
        and right["test_rows_read"] == right["scientific_fits"]
        == right["neural_model_loads"] == right["model_forwards"] == 0,
        "TUNING_OUTCOME_ACCEPTANCE",
    )
    return prelabel, prelabel_validation, outcomes, outcomes_validation


def assemble_inputs(prelabel_rows: list[dict], outcome_rows: list[dict]):
    require(len(prelabel_rows) == len(outcome_rows) == EXPECTED_TRACES,
            "TUNING_SOURCE_COUNTS")
    features = {method: {} for method in METHODS}
    outcomes = {}; parts = {"fit": set(), "cal": set()}
    eligible_counts = collections.Counter()
    for position, (prelabel, outcome) in enumerate(zip(
            prelabel_rows, outcome_rows, strict=True)):
        require(set(prelabel) == PRELABEL_FIELDS and set(outcome) == OUTCOME_FIELDS,
                "TUNING_SOURCE_SCHEMA")
        identity = {name: prelabel[name] for name in IDENTITY_FIELDS}
        require(identity["position"] == position
                and all(outcome[name] == value for name, value in identity.items())
                and outcome["prelabel_row_sha256"] == object_sha256(prelabel),
                "TUNING_SOURCE_BINDING")
        key = (identity["dataset"], identity["retriever"], identity["sample_id"])
        require(key not in outcomes and identity["role"] in parts,
                "TUNING_UNIQUE_DEVELOPMENT_KEY")
        require(set(prelabel["feature_vectors"]) == set(METHODS)
                and type(prelabel["eligible"]) is bool,
                "TUNING_FEATURE_VARIANTS")
        outcomes[key] = outcome; parts[identity["role"]].add(key)
        for method in METHODS:
            numeric = prelabel["feature_vectors"][method]
            require(type(numeric) is list and len(numeric) == VARIANT_WIDTHS[method],
                    "TUNING_FEATURE_WIDTH")
            features[method][key] = {
                "eligible": prelabel["eligible"],
                "numeric": numeric,
            }
            if prelabel["eligible"]:
                eligible_counts[(method, identity["role"])] += 1
    require(len(outcomes) == EXPECTED_TRACES
            and len(parts["fit"]) == EXPECTED_FIT_TRACES
            and len(parts["cal"]) == EXPECTED_CAL_TRACES
            and parts["fit"].isdisjoint(parts["cal"]),
            "TUNING_DEVELOPMENT_PARTS")
    groups = collections.defaultdict(set); group_roles = {}
    for role, keys in parts.items():
        for dataset, retriever, sample_id in keys:
            group = (dataset, sample_id); groups[group].add(retriever)
            require(group not in group_roles or group_roles[group] == role,
                    "TUNING_SIBLING_ROLE")
            group_roles[group] = role
    require(len(groups) == 4_500
            and all(value == set(RETRIEVERS) for value in groups.values())
            and all(sum(dataset == name for dataset, _ in groups) == 1_500
                    for name in DATASETS)
            and collections.Counter(group_roles.values()) == {"fit": 3_600, "cal": 900},
            "TUNING_QUESTION_GROUPS")
    require(all(set(value) == set(outcomes) for value in features.values()),
            "TUNING_FEATURE_SCOPE")
    counts = {
        method: {role: eligible_counts[(method, role)] for role in ("fit", "cal")}
        for method in METHODS
    }
    require(len({tuple(value.values()) for value in counts.values()}) == 1,
            "TUNING_COMMON_ELIGIBILITY")
    return features, outcomes, parts, counts


class DurableFitEvents:
    def __init__(self, path: Path) -> None:
        require(not path.exists(), "TUNING_EVENT_JOURNAL_EXISTS")
        self.path = path
        self.rows = []
        self.stream = path.open("xb")

    def __call__(self, event: dict) -> None:
        row = {"sequence": len(self.rows), **event}
        raw = canonical(row) + b"\n"
        self.stream.write(raw); self.stream.flush(); os.fsync(self.stream.fileno())
        self.rows.append(row)

    def close(self) -> None:
        if not self.stream.closed:
            self.stream.close()


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path); item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files,
        "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-name", required=True)
    args = parser.parse_args()
    require(args.output_name and all(part not in args.output_name
                                     for part in ("/", "\\", "..")),
            "SAFE_OUTPUT_NAME")
    original = args.project_root.resolve(); root = (OUTPUT_PARENT / args.output_name).resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve()
            and root.parent == OUTPUT_PARENT.resolve(), "FIXED_ROOTS")
    prelabel, prelabel_validation, outcomes, outcomes_validation = validate_predecessors(root)
    stage_output = root / "tuning"
    require(not stage_output.exists(), "SINGLE_USE_TUNING_NAMESPACE")
    require(not subprocess.check_output(["git", "status", "--porcelain"],
                                        cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     cwd=REPO, text=True).strip()
    stage_output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter(); journal = None
    result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "tuning", "scientific_fit_attempts": 0,
        "scientific_fit_completions": 0, "development_rows_read": 0,
        "development_gold_metric_values_read": 0, "test_rows_read": 0,
        "test_gold_values_read": 0, "neural_model_loads": 0, "model_forwards": 0,
        "action_budget_tuned": False,
    }
    try:
        require(all(name not in sys.modules for name in ("torch", "transformers")),
                "NEURAL_RUNTIME_ALREADY_LOADED")
        input_paths = [
            prelabel / "SHA256_MANIFEST.json", prelabel_validation,
            outcomes / "SHA256_MANIFEST.json", outcomes_validation,
            Path(__file__), REPO / "scripts/validate_mistral_development_tuning.py",
            REPO / "src/arbitration/reader_development_tuning.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "docs/cas_q3/READER_DEVELOPMENT_TUNING_POLICY_2026-09-16.md",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_SCORING_AND_TUNING_PROTOCOL_2026-09-17.md",
            Path(sys.executable),
        ]
        input_records = [record(path) for path in input_paths]
        require(len({item["path"] for item in input_records}) == len(input_records),
                "UNIQUE_TUNING_INPUTS")
        threadpools = threadpool_info()
        packages = {name: importlib.metadata.version(name) for name in
                    ("numpy", "scipy", "scikit-learn", "threadpoolctl")}
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_DEVELOPMENT_TUNING",
            "source_commit": commit, "stage": "tuning", "methods": list(METHODS),
            "variant_widths": VARIANT_WIDTHS, "fold_prefix": FOLD_PREFIX,
            "candidate_grid": list(candidate_grid()),
            "c_search_values": list(C_SEARCH_VALUES),
            "c_tie_order": list(C_TIE_ORDER), "base_fixed": BASE_FIXED,
            "platt_fixed": PLATT_FIXED,
            "expected_search_fit_attempts": EXPECTED_SEARCH_FIT_ATTEMPTS,
            "expected_fixed_reference_fit_attempts": 6,
            "expected_fit_attempts": EXPECTED_FIT_ATTEMPTS,
            "selection_metric": "pooled_eligible_validation_binary_log_loss",
            "target": "a0_em==0 and a1_em==1", "test_access": "FORBIDDEN",
            "action_budget_tuning": "FORBIDDEN", "inputs": input_records,
            "host": platform.platform(), "python": str(Path(sys.executable).resolve()),
            "python_version": sys.version, "packages": packages,
            "threadpool_preflight": threadpools, "thread_limit": 1,
        }
        write_json_durable(stage_output / "EXECUTABLE_FREEZE.json", freeze)

        prelabel_rows = list(read_jsonl(prelabel / "PRELABEL_ROWS.jsonl"))
        outcome_rows = list(read_jsonl(outcomes / "DEVELOPMENT_OUTCOMES.jsonl"))
        features, numeric_outcomes, parts, eligible_counts = assemble_inputs(
            prelabel_rows, outcome_rows,
        )
        result.update(development_rows_read=EXPECTED_TRACES,
                      development_gold_metric_values_read=EXPECTED_TRACES * 4)
        journal = DurableFitEvents(stage_output / "FIT_EVENTS.jsonl")
        models = {}
        with threadpool_limits(limits=1):
            for method in METHODS:
                models[method] = tune_recovery_head(
                    features[method], numeric_outcomes, parts, method, journal,
                )
                result["scientific_fit_attempts"] += models[method]["fit_attempts"]
                result["scientific_fit_completions"] += models[method]["successful_fits"]
        journal.close()
        require(result["scientific_fit_attempts"] == EXPECTED_FIT_ATTEMPTS
                and len(journal.rows) == EXPECTED_EVENT_ROWS,
                "TUNING_WORKLOAD_COUNTS")
        write_bytes_once(stage_output / "TUNING_RESULTS.json",
                         json.dumps(models, sort_keys=True, indent=2,
                                    allow_nan=False).encode("utf-8") + b"\n")
        require(all(name not in sys.modules for name in ("torch", "transformers")),
                "NEURAL_RUNTIME_LOADED")
        for item in input_records:
            require(record(item["path"]) == item, "TUNING_INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "TUNING_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_DEVELOPMENT_TUNING_PENDING_INDEPENDENT",
            methods=list(METHODS), eligible_role_counts=eligible_counts,
            selected_candidates={method: models[method]["selected_candidate_id"]
                                 for method in METHODS},
            fit_event_rows=len(journal.rows),
            tuning_results=record(stage_output / "TUNING_RESULTS.json"),
            fit_events=record(stage_output / "FIT_EVENTS.jsonl"),
            test_rows_read=0, test_gold_values_read=0,
            neural_model_loads=0, model_forwards=0,
            action_budget_tuned=False, elapsed_seconds=elapsed,
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output); print(result["status"], flush=True); return 0
    except Exception as exc:
        if journal is not None:
            journal.close()
            result["scientific_fit_attempts"] = sum(
                row["event"] in {"cv_fit_started", "selected_base_fit_started",
                                 "platt_fit_started", "fixed_base_fit_started",
                                 "fixed_platt_fit_started"}
                for row in journal.rows
            )
            result["scientific_fit_completions"] = sum(
                row["event"] in {"cv_fit_completed", "selected_base_fit_completed",
                                 "platt_fit_completed", "fixed_base_fit_completed",
                                 "fixed_platt_fit_completed"}
                for row in journal.rows
            )
        result.update(
            status="FAIL_MISTRAL_DEVELOPMENT_TUNING",
            error_type=type(exc).__name__, diagnostic=str(exc),
            traceback=traceback.format_exc(), elapsed_seconds=time.perf_counter() - started,
        )
        if not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result); seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True); return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
