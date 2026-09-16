"""Apply the frozen historical state-symmetric HGB to Mistral development pairs."""

from __future__ import annotations

import argparse
import collections
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import types

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    read_jsonl, record, sha256, validate_development_binding, verify_manifest,
    write_json_durable,
)
from scripts.mistral_development_scoring_common import write_bytes_once
from scripts.run_mistral_development_a0_query import (
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256, EXPECTED_INPUT_LEDGER_SHA256,
    EXPECTED_POOL_MANIFEST_SHA256, EXPECTED_RETRIEVAL_MANIFEST_SHA256,
    EXPECTED_RUNTIME_MANIFEST_SHA256, load_original_native,
)
from scripts.run_mistral_development_repair import legacy_manifest_member_paths
from src.arbitration.mistral_reader_runtime import canonical, object_sha256, require
from src.evaluation.answer_normalization import assess_pair_eligibility


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q3"
EXPECTED_TRACES = 13_500
HGB_MODEL_SHA256 = "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e"
METHOD_FREEZE_SHA256 = "af69d7b3a974656bf81da0514a32385476421ac5bd0b32a6585d2291f10aa87a"
STATE_SYMMETRIC_SOURCE_SHA256 = "3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717"
ANSWERS_SOURCE_SHA256 = "d6de10b0d44bf32c5aa3727c4d2b4b3dc2556b3e4f791cc1fc4f08ad957dd182"
HISTORICAL_PREFLIGHT_SHA256 = "f29a5ad13c2d8ce6cab3bb6331bd315837c70907fa9d71725339af07baeb5790"
MAX_STAGE_SECONDS = 6 * 60 * 60


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_answer_semantics_gate(root: Path) -> tuple[Path, Path]:
    namespace = root / "answer_semantics"
    validation = root / "answer_semantics_validation/VALIDATION.json"
    require((namespace / "SHA256_MANIFEST.json").is_file() and validation.is_file(),
            "ANSWER_SEMANTICS_ACCEPTANCE_REQUIRED")
    verify_manifest(namespace, sha256(namespace / "SHA256_MANIFEST.json"))
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_TOKENIZER_ONLY_MISTRAL_DEVELOPMENT_ANSWER_SEMANTICS"
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value["batch_receipts_sha256"] == sha256(namespace / "BATCH_RECEIPTS.jsonl")
            and value["semantic_rows_sha256"] == sha256(namespace / "SEMANTIC_ROWS.jsonl")
            and value["call_journal_sha256"] == sha256(namespace / "CALL_JOURNAL.jsonl"),
            "ANSWER_SEMANTICS_VALIDATION_BINDING")
    return namespace, validation


def _exec_module(name: str, path: Path, package: str):
    module = types.ModuleType(name); module.__file__ = str(path); module.__package__ = package
    sys.modules[name] = module
    exec(compile(path.read_text(encoding="utf-8-sig"), str(path), "exec"), module.__dict__)
    return module


def load_exact_hgb(original: Path):
    answers_path = original / "src/evaluation/answers.py"
    state_path = original / "src/mars/state_symmetric.py"
    method_path = original / "outputs/mars_full/method_freeze.json"
    model_path = original / "outputs/mars_full/models/state_symmetric_hgb.joblib"
    require(sha256(answers_path) == ANSWERS_SOURCE_SHA256
            and sha256(state_path) == STATE_SYMMETRIC_SOURCE_SHA256
            and sha256(method_path) == METHOD_FREEZE_SHA256
            and sha256(model_path) == HGB_MODEL_SHA256, "HGB_ASSET_PINS")
    answers = _exec_module("mistral_hgb_exact_answers", answers_path, "")
    import src.evaluation as evaluation
    evaluation.normalize_answer = answers.normalize_answer
    mars = types.ModuleType("src.mars"); mars.__path__ = [str(original / "src/mars")]
    sys.modules["src.mars"] = mars
    state = _exec_module("src.mars.state_symmetric", state_path, "src.mars")
    mars.state_symmetric = state
    import joblib
    selector = joblib.load(model_path)
    method = json.loads(method_path.read_text(encoding="utf-8"))
    manifest = method["model_manifest"]["state_symmetric_hgb"]
    require(manifest["sha256"] == HGB_MODEL_SHA256
            and manifest["size_bytes"] == model_path.stat().st_size
            and tuple(manifest["feature_names"]) == tuple(selector.feature_names)
            and selector.family == "hgb" and selector.scaler is None
            and selector.model.__class__.__name__ == "HistGradientBoostingClassifier",
            "HGB_MODEL_IDENTITY")
    return state, selector, method_path, model_path, answers_path, state_path


def reconstruct_e1(native, e0, payload: dict, data: dict):
    inserted_id = payload["inserted_document_id"]
    matches = [row for row in payload["ranking"] if row["document_id"] == inserted_id]
    require(len(matches) == 1 and matches[0]["rank"] == payload["inserted_candidate_rank"],
            "INSERTED_RANK")
    source = data["documents"][inserted_id]
    inserted = native.RankedDocument(
        5, inserted_id, source.content_hash, float(matches[0]["score"]),
        source.title, source.text,
    )
    e1 = tuple((*e0[:4], inserted))
    require([row.document_id for row in e1] == payload["e1_ids"], "E1_BINDING")
    return e1


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path); item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files, "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    require(args.output_name and all(part not in args.output_name for part in ("/", "\\", "..")),
            "SAFE_OUTPUT_NAME")
    original = args.project_root.resolve(); root = (OUTPUT_PARENT / args.output_name).resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve()
            and root.parent == OUTPUT_PARENT.resolve(), "FIXED_ROOTS")
    semantics_stage, semantics_validation = validate_answer_semantics_gate(root)
    stage_output = root / "hgb_signal"
    require(not any((stage_output / name).exists() for name in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json", "SHA256_MANIFEST.json")),
            "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    started = time.perf_counter(); result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "hgb_signal", "gold_values_read": 0, "scientific_fits": 0,
        "test_rows_read": 0, "neural_model_loads": 0, "neural_model_forwards": 0,
        "hgb_model_loads": 0, "hgb_fit_calls": 0,
    }
    try:
        if not args.resume: stage_output.mkdir(parents=True, exist_ok=False)
        require("torch" not in sys.modules and "transformers" not in sys.modules,
                "NEURAL_RUNTIME_ALREADY_LOADED")
        state, selector, method_path, model_path, answers_path, state_path = load_exact_hgb(original)
        result["hgb_model_loads"] = 1
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
                and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256, "INPUT_FREEZE")
        runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
        pool_root = original / "outputs/daa_v2_fresh_v1/pool_freeze"
        retrieval_root = original / "outputs/daa_v2_fresh_v1/retrieval_freeze"
        preflight = original / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/PREFLIGHT_INPUT_VERIFICATION.json"
        require(sha256(preflight) == HISTORICAL_PREFLIGHT_SHA256, "HISTORICAL_PREFLIGHT_PIN")
        paths = [
            *legacy_manifest_member_paths(
                original, runtime_root, EXPECTED_RUNTIME_MANIFEST_SHA256,
            ),
            *legacy_manifest_member_paths(
                original, pool_root, EXPECTED_POOL_MANIFEST_SHA256,
            ),
            *legacy_manifest_member_paths(
                original, retrieval_root, EXPECTED_RETRIEVAL_MANIFEST_SHA256,
            ),
            *verify_manifest(
                input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
            ),
            *verify_manifest(
                semantics_stage, sha256(semantics_stage / "SHA256_MANIFEST.json"),
            ),
            semantics_validation,
            *verify_manifest(
                root / "a0_query", sha256(root / "a0_query/SHA256_MANIFEST.json"),
            ),
            *verify_manifest(
                root / "repair", sha256(root / "repair/SHA256_MANIFEST.json"),
            ),
            *verify_manifest(
                root / "a1_likelihood",
                sha256(root / "a1_likelihood/SHA256_MANIFEST.json"),
            ),
            preflight, method_path, model_path, answers_path, state_path,
        ]
        controls = [
            Path(__file__), REPO / "scripts/validate_mistral_development_hgb_signal.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/mistral_development_scoring_common.py",
            REPO / "scripts/run_mistral_development_a0_query.py",
            REPO / "scripts/run_mistral_development_repair.py",
            REPO / "scripts/empirical_feature_independent.py",
            REPO / "src/evaluation/__init__.py",
            REPO / "src/evaluation/answer_normalization.py",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_SCORING_AND_TUNING_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_HGB_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            runtime_root / "runtime_support.py", runtime_root / "native_runtime.py",
            runtime_root / "trace_manifest.jsonl",
        ]
        input_records = [record(path) for path in sorted(
            {Path(path).resolve() for path in [*paths, *controls]}, key=str
        )]
        require(len({item["path"] for item in input_records}) == len(input_records),
                "UNIQUE_HGB_INPUTS")
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_DEVELOPMENT_HGB_SIGNAL",
            "source_commit": commit, "stage": "hgb_signal",
            "expected_traces": EXPECTED_TRACES,
            "hgb_model_sha256": HGB_MODEL_SHA256,
            "feature_names": list(selector.feature_names), "inputs": input_records,
            "host": platform.platform(), "python": str(Path(sys.executable).resolve()),
            "packages": {name: importlib.metadata.version(name)
                         for name in ("numpy", "scikit-learn", "joblib")},
            "scope": "development pairs only; fixed historical HGB inference; neural/Gold/test/fit forbidden",
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                    "RESUME_FREEZE_MISMATCH")
        else:
            write_json_durable(freeze_path, freeze)

        loader, native, nodes, _boundary = load_original_native(original)
        traces = list(read_jsonl(runtime_root / "trace_manifest.jsonl"))
        development = validate_development_binding(traces, read_jsonl(frozen_ledger))
        a0_rows = list(read_jsonl(root / "a0_query/GENERATION_RECEIPTS.jsonl"))
        repair_rows = list(read_jsonl(root / "repair/REPAIR_BINDINGS.jsonl"))
        a1_rows = list(read_jsonl(root / "a1_likelihood/MODEL_RECEIPTS.jsonl"))
        semantic_rows = list(read_jsonl(semantics_stage / "SEMANTIC_ROWS.jsonl"))
        a0_map = {row["payload"]["position"]: row["payload"]
                  for row in a0_rows if row["operation"] == "a0"}
        repair_map = {row["payload"]["position"]: row["payload"] for row in repair_rows}
        a1_map = {row["payload"]["position"]: row["payload"]
                  for row in a1_rows if row["operation"] == "a1"}
        cell_maps = {cell: {row["payload"]["position"]: row["payload"] for row in a1_rows
                            if row["operation"] == cell}
                     for cell in ("L00", "L01", "L10", "L11")}
        semantic_map = {row["position"]: row for row in semantic_rows}
        require(len(a0_rows) == 27_000 and len(repair_rows) == EXPECTED_TRACES
                and len(a1_rows) == 67_500 and len(semantic_rows) == EXPECTED_TRACES
                and len(a0_map) == len(repair_map) == len(a1_map) == len(semantic_map) == EXPECTED_TRACES
                and all(len(value) == EXPECTED_TRACES for value in cell_maps.values()),
                "PRIOR_ROW_COUNTS")

        class NoEmbeddingBackend:
            dimension = 768
            def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")
            def encode_documents(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")

        backend = NoEmbeddingBackend(); current_dataset = None; data = None
        feature_rows = []; signal_rows = []; pairs = []; eligible_signal_indexes = []
        forced = collections.Counter()
        for position, trace in enumerate(traces):
            require(trace["position"] == position, "TRACE_POSITION")
            if trace["dataset"] != current_dataset:
                data = loader.restore_dataset(trace["dataset"], native, backend)
                current_dataset = trace["dataset"]
            e0 = loader.original_evidence(trace, data, native)
            e1 = reconstruct_e1(native, e0, repair_map[position], data)
            private_e0 = [row.as_private_dict() for row in e0]
            private_e1 = [row.as_private_dict() for row in e1]
            a0, a1 = a0_map[position]["parsed_text"], a1_map[position]["parsed_text"]
            semantic = semantic_map[position]
            require(semantic["position"] == position
                    and (semantic["dataset"], semantic["retriever"], semantic["sample_id"], semantic["role"])
                    == (trace["dataset"], trace["retriever"], trace["sample_id"], development[position]["role"])
                    and semantic["a0_sha256"] == text_sha(a0)
                    and semantic["a1_sha256"] == text_sha(a1), "SEMANTIC_BINDING")
            cells = {cell: cell_maps[cell][position] for cell in cell_maps}
            require(all(payload["position"] == position and payload["cell"] == cell
                        for cell, payload in cells.items()), "LIKELIHOOD_CELL_BINDING")
            eligibility = assess_pair_eligibility(a0, a1)
            bindings = {
                "a0_receipt_sha256": object_sha256(a0_map[position]),
                "repair_receipt_sha256": object_sha256(repair_map[position]),
                "a1_receipt_sha256": object_sha256(a1_map[position]),
                "likelihood_receipt_sha256": {cell: object_sha256(cells[cell]) for cell in cells},
                "answer_semantic_row_sha256": object_sha256(semantic),
            }
            signal = {
                "dataset": trace["dataset"], "retriever": trace["retriever"],
                "sample_id": trace["sample_id"], "position": position,
                "role": development[position]["role"], "eligible": eligibility.eligible,
                "forced_keep_reason": eligibility.reason, "bindings": bindings,
                "feature_row_sha256": None, "hgb_score": None,
            }
            if eligibility.eligible:
                pair_trace = {
                    "dataset": trace["dataset"], "retriever": trace["retriever"],
                    "sample_id": trace["sample_id"], "split": "development",
                    "a0": a0, "a1": a1, "E0": private_e0, "E1": private_e1,
                    "answer_semantic_agreement": semantic["answer_semantic_agreement"],
                }
                pair = state.build_pair_record(
                    pair_trace, cells, schema_version="mars-state-symmetric-v1",
                )
                feature = {"position": position, "pair": pair}
                signal["feature_row_sha256"] = object_sha256(feature)
                feature_rows.append(feature); pairs.append(pair)
                eligible_signal_indexes.append(len(signal_rows))
            else:
                forced[eligibility.reason] += 1
            signal_rows.append(signal)
        require(len(signal_rows) == EXPECTED_TRACES and len(feature_rows) == len(pairs)
                == len(eligible_signal_indexes), "ASSEMBLED_COUNTS")
        scores = np.asarray(selector.scores(pairs), dtype=np.float64)
        require(scores.shape == (len(pairs),) and np.isfinite(scores).all()
                and ((scores > 0.0) & (scores < 1.0)).all(), "HGB_SCORES")
        for index, score in zip(eligible_signal_indexes, scores, strict=True):
            signal_rows[index]["hgb_score"] = float(score)
        feature_raw = b"".join(canonical(row) + b"\n" for row in feature_rows)
        signal_raw = b"".join(canonical(row) + b"\n" for row in signal_rows)
        write_bytes_once(stage_output / "HGB_FEATURE_ROWS.jsonl", feature_raw)
        write_bytes_once(stage_output / "HGB_SIGNAL_ROWS.jsonl", signal_raw)
        require("torch" not in sys.modules and "transformers" not in sys.modules,
                "NEURAL_RUNTIME_LOADED")
        for item in input_records:
            require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_DEVELOPMENT_HGB_SIGNAL_PENDING_INDEPENDENT",
            completed_traces=EXPECTED_TRACES, eligible_traces=len(pairs),
            forced_keep_counts=dict(forced), hgb_feature_width=len(selector.feature_names),
            hgb_score_batches=1, expected_predict_proba_calls=2,
            hgb_feature_rows=record(stage_output / "HGB_FEATURE_ROWS.jsonl"),
            hgb_signal_rows=record(stage_output / "HGB_SIGNAL_ROWS.jsonl"),
            native_ast_nodes=nodes, elapsed_seconds=elapsed,
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output); print(result["status"], flush=True); return 0
    except Exception as exc:
        result.update(status="FAIL_MISTRAL_DEVELOPMENT_HGB_SIGNAL",
                      error_type=type(exc).__name__, diagnostic=str(exc),
                      traceback=traceback.format_exc(), elapsed_seconds=time.perf_counter() - started)
        if stage_output.is_dir() and not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result); seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True); return 2
    finally:
        gc.collect()


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
