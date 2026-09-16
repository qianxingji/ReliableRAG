"""Independent formula-level validation of the Mistral test HGB signal."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import types

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_feature_independent import (
    check_numeric_tree, feature_pair, pair_eligibility,
)
from scripts.empirical_runtime_io import native_runtime, restore_dataset
from scripts.validate_mistral_test_a0_query import (
    object_sha, read_rows, require, sha256,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
HGB_MODEL_SHA256 = "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e"
METHOD_FREEZE_SHA256 = "af69d7b3a974656bf81da0514a32385476421ac5bd0b32a6585d2291f10aa87a"
STATE_SYMMETRIC_SOURCE_SHA256 = "3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717"
ANSWERS_SOURCE_SHA256 = "d6de10b0d44bf32c5aa3727c4d2b4b3dc2556b3e4f791cc1fc4f08ad957dd182"


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    require(manifest["status"] == "PASS" and manifest["exact_recursive_coverage"] is True,
            "MANIFEST_STATUS")
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members, "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_semantics(root: Path) -> Path:
    namespace = root / "answer_semantics"; validate_manifest(namespace)
    validation = root / "answer_semantics_validation/VALIDATION.json"
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_TOKENIZER_ONLY_MISTRAL_TEST_ANSWER_SEMANTICS"
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value["batch_receipts_sha256"] == sha256(namespace / "BATCH_RECEIPTS.jsonl")
            and value["semantic_rows_sha256"] == sha256(namespace / "SEMANTIC_ROWS.jsonl")
            and value["call_journal_sha256"] == sha256(namespace / "CALL_JOURNAL.jsonl")
            and value["project_gold_values_read"] == 0
            and value["test_gold_values_read"] == 0
            and value["test_outcome_values_read"] == 0
            and value["scientific_fits"] == 0
            and value["test_input_rows_read"] == EXPECTED_TRACES,
            "ANSWER_SEMANTICS_VALIDATION_BINDING")
    return validation


def _exec_module(name: str, path: Path, package: str):
    module = types.ModuleType(name); module.__file__ = str(path); module.__package__ = package
    sys.modules[name] = module
    exec(compile(path.read_text(encoding="utf-8-sig"), str(path), "exec"), module.__dict__)
    return module


def load_selector_for_independent_scoring(original: Path):
    answers_path = original / "src/evaluation/answers.py"
    state_path = original / "src/mars/state_symmetric.py"
    method_path = original / "outputs/mars_full/method_freeze.json"
    model_path = original / "outputs/mars_full/models/state_symmetric_hgb.joblib"
    require(sha256(answers_path) == ANSWERS_SOURCE_SHA256
            and sha256(state_path) == STATE_SYMMETRIC_SOURCE_SHA256
            and sha256(method_path) == METHOD_FREEZE_SHA256
            and sha256(model_path) == HGB_MODEL_SHA256, "HGB_ASSET_PINS")
    answers = _exec_module("mistral_hgb_validation_answers", answers_path, "")
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
    require(selector.family == "hgb" and selector.scaler is None
            and tuple(selector.feature_names) == tuple(manifest["feature_names"])
            and manifest["sha256"] == HGB_MODEL_SHA256, "HGB_MODEL_IDENTITY")
    return selector


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
    require([row.document_id for row in e0] == payload["e0_ids"]
            and [row.document_id for row in e1] == payload["e1_ids"]
            and payload["replaced_document_id"] == e0[4].document_id,
            "E1_BINDING")
    return e1


def independent_scores(selector, pairs: list[dict]) -> np.ndarray:
    x = np.asarray([
        [float(pair["features"][name]) for name in selector.feature_names]
        for pair in pairs
    ], dtype=np.float64)
    require(x.shape == (len(pairs), len(selector.feature_names))
            and np.isfinite(x).all(), "INDEPENDENT_MATRIX")
    positive = np.asarray(selector.model.predict_proba(x)[:, 1], dtype=np.float64)
    negative = np.asarray(selector.model.predict_proba(-x)[:, 1], dtype=np.float64)
    probability = 0.5 * (positive + 1.0 - negative)
    epsilon = np.finfo(np.float64).eps
    probability = np.clip(probability, epsilon, 1.0 - epsilon)
    logits = np.log(probability / (1.0 - probability))
    return 1.0 / (1.0 + np.exp(-logits))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original = args.project_root.resolve()
    root = args.test_root.resolve()
    output = (args.output.resolve() if args.output else
              (root / "hgb_signal_validation/VALIDATION.json").resolve())
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve()
            and output == (root / "hgb_signal_validation/VALIDATION.json").resolve()
            and not output.exists(), "FIXED_ROOTS_OR_OUTPUT")
    semantics_validation = validate_semantics(root)
    namespace = root / "hgb_signal"; validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "PASS_MISTRAL_TEST_HGB_SIGNAL_PENDING_INDEPENDENT"
            and receipt["completed_traces"] == EXPECTED_TRACES
            and receipt["hgb_feature_width"] == 48
            and receipt["hgb_score_batches"] == 1
            and receipt["expected_predict_proba_calls"] == 2
            and receipt["hgb_model_loads"] == 1 and receipt["hgb_fit_calls"] == 0
            and receipt["neural_model_loads"] == receipt["neural_model_forwards"] == 0
            and receipt["project_gold_values_read"] == 0
            and receipt["test_gold_values_read"] == 0
            and receipt["test_outcome_values_read"] == 0
            and receipt["scientific_fits"] == 0
            and receipt["test_input_rows_read"] == EXPECTED_TRACES,
            "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"]
            and freeze["stage"] == "hgb_signal" and freeze["expected_traces"] == EXPECTED_TRACES
            and freeze["hgb_model_sha256"] == HGB_MODEL_SHA256
            and len(freeze["feature_names"]) == 48
            and freeze["test_gold_access"] == "FORBIDDEN"
            and freeze["test_outcome_access"] == "FORBIDDEN"
            and freeze["scientific_fit_access"] == "FORBIDDEN",
            "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "FROZEN_INPUT")
    frozen_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(semantics_validation.resolve() in frozen_paths
            and Path(__file__).resolve() in frozen_paths,
            "FROZEN_SEMANTICS_VALIDATION")

    feature_rows = read_rows(namespace / "HGB_FEATURE_ROWS.jsonl")
    signal_rows = read_rows(namespace / "HGB_SIGNAL_ROWS.jsonl")
    require(len(signal_rows) == EXPECTED_TRACES
            and len(feature_rows) == receipt["eligible_traces"], "OUTPUT_COUNTS")
    feature_map = {row["position"]: row for row in feature_rows}
    require(len(feature_map) == len(feature_rows), "UNIQUE_FEATURE_POSITIONS")

    trace_path = (REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
                  / "TRACE_MANIFEST_PRIVATE.jsonl")
    require(trace_path.resolve() in frozen_paths, "FROZEN_TEST_TRACE")
    traces = read_rows(trace_path)
    frozen_rows = [row for row in read_rows(
        REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl"
    ) if row.get("cohort") == "test"]
    require(len(traces) == len(frozen_rows) == EXPECTED_TRACES, "SOURCE_COUNTS")
    a0_rows = read_rows(root / "a0_query/GENERATION_RECEIPTS.jsonl")
    repair_rows = read_rows(root / "repair/REPAIR_BINDINGS.jsonl")
    a1_rows = read_rows(root / "a1_likelihood/MODEL_RECEIPTS.jsonl")
    semantic_rows = read_rows(root / "answer_semantics/SEMANTIC_ROWS.jsonl")
    a0_map = {row["payload"]["position"]: row["payload"]
              for row in a0_rows if row["operation"] == "a0"}
    repair_map = {row["payload"]["position"]: row["payload"] for row in repair_rows}
    a1_map = {row["payload"]["position"]: row["payload"]
              for row in a1_rows if row["operation"] == "a1"}
    cell_maps = {cell: {row["payload"]["position"]: row["payload"] for row in a1_rows
                        if row["operation"] == cell}
                 for cell in ("L00", "L01", "L10", "L11")}
    semantic_map = {row["position"]: row for row in semantic_rows}
    require(len(a0_rows) == 36_000 and len(repair_rows) == EXPECTED_TRACES
            and len(a1_rows) == 90_000 and len(semantic_rows) == EXPECTED_TRACES
            and len(a0_map) == len(repair_map) == len(a1_map) == len(semantic_map) == EXPECTED_TRACES
            and all(len(value) == EXPECTED_TRACES for value in cell_maps.values()),
            "PRIOR_COUNTS")
    selector = load_selector_for_independent_scoring(original)
    require(list(selector.feature_names) == freeze["feature_names"], "FEATURE_NAME_FREEZE")
    wrapper, native, _nodes, _boundary = native_runtime(original)

    class NoEmbeddingBackend:
        dimension = 768
        def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")
        def encode_documents(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")

    backend = NoEmbeddingBackend(); current_dataset = None; data = None
    independent_pairs = []; eligible_positions = []; forced = {}; checks = 0; maximum_error = 0.0
    for position, trace in enumerate(traces):
        frozen = frozen_rows[position]
        require(trace["position"] == frozen["position"] == position
                and (trace["dataset"], trace["retriever"], trace["sample_id"])
                == (frozen["dataset"], frozen["retriever"], frozen["sample_id"])
                and frozen["role"] == "test",
                "SOURCE_BINDING")
        if trace["dataset"] != current_dataset:
            data = restore_dataset(trace["dataset"], native, backend)
            current_dataset = trace["dataset"]
        e0 = wrapper.original_evidence(trace, data, native)
        e1 = reconstruct_e1(native, e0, repair_map[position], data)
        a0, a1 = a0_map[position]["parsed_text"], a1_map[position]["parsed_text"]
        semantic = semantic_map[position]; cells = {cell: cell_maps[cell][position] for cell in cell_maps}
        require(semantic["position"] == position
                and (semantic["dataset"], semantic["retriever"],
                     semantic["sample_id"], semantic["role"])
                == (trace["dataset"], trace["retriever"],
                    trace["sample_id"], "test")
                and all(payload["position"] == position and payload["cell"] == cell
                        for cell, payload in cells.items()), "PRIOR_ROW_BINDING")
        eligible, reason = pair_eligibility(a0, a1)
        bindings = {
            "a0_receipt_sha256": object_sha(a0_map[position]),
            "repair_receipt_sha256": object_sha(repair_map[position]),
            "a1_receipt_sha256": object_sha(a1_map[position]),
            "likelihood_receipt_sha256": {cell: object_sha(cells[cell]) for cell in cells},
            "answer_semantic_row_sha256": object_sha(semantic),
        }
        signal = signal_rows[position]
        require(signal["position"] == position
                and (signal["dataset"], signal["retriever"], signal["sample_id"], signal["role"])
                == (trace["dataset"], trace["retriever"], trace["sample_id"], frozen["role"])
                and signal["eligible"] is eligible and signal["forced_keep_reason"] == reason
                and signal["bindings"] == bindings, "SIGNAL_IDENTITY")
        require(semantic["a0_sha256"] == text_sha(a0)
                and semantic["a1_sha256"] == text_sha(a1), "ANSWER_SEMANTIC_BINDING")
        if eligible:
            pair_trace = {
                "dataset": trace["dataset"], "retriever": trace["retriever"],
                "sample_id": trace["sample_id"], "split": "test",
                "a0": a0, "a1": a1,
                "E0": [row.as_private_dict() for row in e0],
                "E1": [row.as_private_dict() for row in e1],
                "answer_semantic_agreement": semantic["answer_semantic_agreement"],
            }
            expected_pair = feature_pair(pair_trace, cells)
            feature = feature_map[position]
            count, error = check_numeric_tree(feature["pair"], expected_pair, tolerance=1e-12)
            maximum_error = max(maximum_error, error)
            require(feature == {"position": position, "pair": feature["pair"]}
                    and signal["feature_row_sha256"] == object_sha(feature)
                    and isinstance(signal["hgb_score"], float)
                    and math.isfinite(signal["hgb_score"]), "ELIGIBLE_SIGNAL")
            independent_pairs.append(expected_pair); eligible_positions.append(position)
            checks += count + 24
        else:
            require(position not in feature_map and signal["feature_row_sha256"] is None
                    and signal["hgb_score"] is None, "FORCED_KEEP_SIGNAL")
            forced[reason] = forced.get(reason, 0) + 1; checks += 18
    expected_scores = independent_scores(selector, independent_pairs)
    require(expected_scores.shape == (len(eligible_positions),), "SCORE_COUNT")
    require([row["position"] for row in feature_rows] == eligible_positions,
            "FEATURE_ROW_ORDER")
    for position, expected in zip(eligible_positions, expected_scores, strict=True):
        error = abs(signal_rows[position]["hgb_score"] - float(expected))
        maximum_error = max(maximum_error, error)
        require(error <= 1e-15, "HGB_SCORE_RECONSTRUCTION")
    require(receipt["eligible_traces"] == len(eligible_positions)
            and receipt["forced_keep_counts"] == forced, "RECEIPT_COUNTS")
    require("torch" not in sys.modules and "transformers" not in sys.modules,
            "NEURAL_RUNTIME_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_FORMULA_MISTRAL_TEST_HGB_SIGNAL",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "hgb_feature_rows_sha256": sha256(namespace / "HGB_FEATURE_ROWS.jsonl"),
        "hgb_signal_rows_sha256": sha256(namespace / "HGB_SIGNAL_ROWS.jsonl"),
        "traces_validated": EXPECTED_TRACES, "eligible_traces": len(eligible_positions),
        "forced_keep_counts": forced, "maximum_numeric_error": maximum_error,
        "hgb_model_loads": 1, "hgb_predict_proba_calls": 2, "hgb_fit_calls": 0,
        "neural_model_loads": 0, "neural_model_forwards": 0,
        "project_gold_values_read": 0, "test_gold_values_read": 0,
        "test_outcome_values_read": 0, "scientific_fits": 0,
        "test_input_rows_read": EXPECTED_TRACES,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
