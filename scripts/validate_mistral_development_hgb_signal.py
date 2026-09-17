"""Independent formula-level validation of the Mistral development HGB signal."""

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
from scripts.validate_mistral_development_a0_query import (
    load_original_native, object_sha, read_rows, require, sha256,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_TRACES = 13_500
HGB_MODEL_SHA256 = "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e"
METHOD_FREEZE_SHA256 = "af69d7b3a974656bf81da0514a32385476421ac5bd0b32a6585d2291f10aa87a"
STATE_SYMMETRIC_SOURCE_SHA256 = "3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717"
ANSWERS_SOURCE_SHA256 = "d6de10b0d44bf32c5aa3727c4d2b4b3dc2556b3e4f791cc1fc4f08ad957dd182"
HISTORICAL_PREFLIGHT_SHA256 = "f29a5ad13c2d8ce6cab3bb6331bd315837c70907fa9d71725339af07baeb5790"
EXPECTED_INPUT_FREEZE_MANIFEST_SHA256 = (
    "588b4d86fb6048ade1bba52731829496772d62fd522a260a7a4c60ec584586ca"
)
EXPECTED_RUNTIME_MANIFEST_SHA256 = (
    "0e831d2807ee48197029f03f8ed1e18381a60bc5fc25327edccc8d8486b6cefb"
)
EXPECTED_POOL_MANIFEST_SHA256 = (
    "f53575bc7b9514f33a235f8380520b99c2faac4cb8b6d78533fc42cb08f377b8"
)
EXPECTED_RETRIEVAL_MANIFEST_SHA256 = (
    "15a18dc5c2a61a83171add05be2cb989813ab023ffea8a035cb1ba42dacdf651"
)


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


def current_manifest_member_paths(
    namespace: Path, expected_manifest_sha256: str,
) -> set[Path]:
    namespace = namespace.resolve(); manifest_path = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest_path) == expected_manifest_sha256,
            "CURRENT_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    if "status" in value:
        require(value["status"] == "PASS", "CURRENT_MANIFEST_STATUS")
    if "exact_recursive_coverage" in value:
        require(value["exact_recursive_coverage"] is True,
                "CURRENT_MANIFEST_EXACT_COVERAGE")
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


def legacy_manifest_member_paths(
    original: Path, namespace: Path, expected_manifest_sha256: str,
) -> set[Path]:
    original = original.resolve(); namespace = namespace.resolve()
    manifest_path = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest_path) == expected_manifest_sha256,
            "LEGACY_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    for item in value["files"]:
        path = (original / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members
                and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "LEGACY_MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    extras = actual - members - {manifest_path.resolve()}
    require(all("__pycache__" in path.parts and path.suffix == ".pyc"
                for path in extras), "LEGACY_MANIFEST_UNEXPECTED_EXTRA")
    return {manifest_path.resolve(), *members}


def validate_semantics(root: Path) -> Path:
    namespace = root / "answer_semantics"; validate_manifest(namespace)
    validation = root / "answer_semantics_validation/VALIDATION.json"
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_TOKENIZER_ONLY_MISTRAL_DEVELOPMENT_ANSWER_SEMANTICS"
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value["batch_receipts_sha256"] == sha256(namespace / "BATCH_RECEIPTS.jsonl")
            and value["semantic_rows_sha256"] == sha256(namespace / "SEMANTIC_ROWS.jsonl")
            and value["call_journal_sha256"] == sha256(namespace / "CALL_JOURNAL.jsonl"),
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
    require([row.document_id for row in e1] == payload["e1_ids"], "E1_BINDING")
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
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original, root, output = (args.project_root.resolve(), args.root.resolve(),
                              args.output.resolve())
    require(original == Path("E:/paper/ReliableRAG").resolve() and not output.exists(),
            "FIXED_ROOT_OR_OUTPUT")
    semantics_validation = validate_semantics(root)
    namespace = root / "hgb_signal"; validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "PASS_MISTRAL_DEVELOPMENT_HGB_SIGNAL_PENDING_INDEPENDENT"
            and receipt["completed_traces"] == EXPECTED_TRACES
            and receipt["hgb_feature_width"] == 48
            and receipt["hgb_score_batches"] == 1
            and receipt["expected_predict_proba_calls"] == 2
            and receipt["hgb_model_loads"] == 1 and receipt["hgb_fit_calls"] == 0
            and receipt["neural_model_loads"] == receipt["neural_model_forwards"] == 0
            and receipt["gold_values_read"] == receipt["scientific_fits"]
            == receipt["test_rows_read"] == 0, "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"]
            and freeze["stage"] == "hgb_signal" and freeze["expected_traces"] == EXPECTED_TRACES
            and freeze["hgb_model_sha256"] == HGB_MODEL_SHA256
            and len(freeze["feature_names"]) == 48, "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "FROZEN_INPUT")
    frozen_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(len(frozen_paths) == len(freeze["inputs"]), "UNIQUE_FROZEN_INPUTS")
    input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
    runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    pool_root = original / "outputs/daa_v2_fresh_v1/pool_freeze"
    retrieval_root = original / "outputs/daa_v2_fresh_v1/retrieval_freeze"
    preflight = original / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/PREFLIGHT_INPUT_VERIFICATION.json"
    require(sha256(preflight) == HISTORICAL_PREFLIGHT_SHA256,
            "HISTORICAL_PREFLIGHT_PIN")
    required_inputs = {
        *legacy_manifest_member_paths(
            original, runtime_root, EXPECTED_RUNTIME_MANIFEST_SHA256,
        ),
        *legacy_manifest_member_paths(
            original, pool_root, EXPECTED_POOL_MANIFEST_SHA256,
        ),
        *legacy_manifest_member_paths(
            original, retrieval_root, EXPECTED_RETRIEVAL_MANIFEST_SHA256,
        ),
        *current_manifest_member_paths(
            input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
        ),
        *current_manifest_member_paths(
            root / "answer_semantics",
            sha256(root / "answer_semantics/SHA256_MANIFEST.json"),
        ),
        *current_manifest_member_paths(
            root / "a0_query", sha256(root / "a0_query/SHA256_MANIFEST.json"),
        ),
        *current_manifest_member_paths(
            root / "repair", sha256(root / "repair/SHA256_MANIFEST.json"),
        ),
        *current_manifest_member_paths(
            root / "a1_likelihood",
            sha256(root / "a1_likelihood/SHA256_MANIFEST.json"),
        ),
        semantics_validation.resolve(), preflight.resolve(),
        (original / "outputs/mars_full/method_freeze.json").resolve(),
        (original / "outputs/mars_full/models/state_symmetric_hgb.joblib").resolve(),
        (original / "src/evaluation/answers.py").resolve(),
        (original / "src/mars/state_symmetric.py").resolve(),
        (REPO / "scripts/run_mistral_development_hgb_signal.py").resolve(),
        Path(__file__).resolve(),
        (REPO / "scripts/mistral_development_acquisition_common.py").resolve(),
        (REPO / "scripts/mistral_development_scoring_common.py").resolve(),
        (REPO / "scripts/run_mistral_development_a0_query.py").resolve(),
        (REPO / "scripts/run_mistral_development_repair.py").resolve(),
        (REPO / "scripts/empirical_feature_independent.py").resolve(),
        (REPO / "src/evaluation/__init__.py").resolve(),
        (REPO / "src/evaluation/answer_normalization.py").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_SCORING_AND_TUNING_PROTOCOL_2026-09-17.md").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_DEVELOPMENT_HGB_INPUT_GRAPH_AMENDMENT_2026-09-17.md").resolve(),
        (runtime_root / "runtime_support.py").resolve(),
        (runtime_root / "native_runtime.py").resolve(),
        (runtime_root / "trace_manifest.jsonl").resolve(),
    }
    require(required_inputs == frozen_paths, "NONEXACT_FROZEN_INPUT_GRAPH")

    feature_rows = read_rows(namespace / "HGB_FEATURE_ROWS.jsonl")
    signal_rows = read_rows(namespace / "HGB_SIGNAL_ROWS.jsonl")
    require(len(signal_rows) == EXPECTED_TRACES
            and len(feature_rows) == receipt["eligible_traces"], "OUTPUT_COUNTS")
    feature_map = {row["position"]: row for row in feature_rows}
    require(len(feature_map) == len(feature_rows), "UNIQUE_FEATURE_POSITIONS")

    runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    traces = read_rows(runtime_root / "trace_manifest.jsonl")
    frozen_rows = [row for row in read_rows(
        REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl"
    ) if row.get("cohort") == "development"]
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
    require(len(a0_map) == len(repair_map) == len(a1_map) == len(semantic_map) == EXPECTED_TRACES
            and all(len(value) == EXPECTED_TRACES for value in cell_maps.values()),
            "PRIOR_COUNTS")
    selector = load_selector_for_independent_scoring(original)
    require(list(selector.feature_names) == freeze["feature_names"], "FEATURE_NAME_FREEZE")
    loader, native = load_original_native(original)

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
                == (frozen["dataset"], frozen["retriever"], frozen["sample_id"]),
                "SOURCE_BINDING")
        if trace["dataset"] != current_dataset:
            data = loader.restore_dataset(trace["dataset"], native, backend)
            current_dataset = trace["dataset"]
        e0 = loader.original_evidence(trace, data, native)
        e1 = reconstruct_e1(native, e0, repair_map[position], data)
        a0, a1 = a0_map[position]["parsed_text"], a1_map[position]["parsed_text"]
        semantic = semantic_map[position]; cells = {cell: cell_maps[cell][position] for cell in cell_maps}
        require(semantic["position"] == position
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
                "sample_id": trace["sample_id"], "split": "development",
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
    expected_feature_record = {
        "path": str((namespace / "HGB_FEATURE_ROWS.jsonl").resolve()),
        "size_bytes": (namespace / "HGB_FEATURE_ROWS.jsonl").stat().st_size,
        "sha256": sha256(namespace / "HGB_FEATURE_ROWS.jsonl"),
    }
    expected_signal_record = {
        "path": str((namespace / "HGB_SIGNAL_ROWS.jsonl").resolve()),
        "size_bytes": (namespace / "HGB_SIGNAL_ROWS.jsonl").stat().st_size,
        "sha256": sha256(namespace / "HGB_SIGNAL_ROWS.jsonl"),
    }
    require(receipt["hgb_feature_rows"] == expected_feature_record
            and receipt["hgb_signal_rows"] == expected_signal_record,
            "PRODUCER_FILE_BINDINGS")
    result = {
        "status": "PASS_INDEPENDENT_FORMULA_MISTRAL_DEVELOPMENT_HGB_SIGNAL",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "hgb_feature_rows_sha256": sha256(namespace / "HGB_FEATURE_ROWS.jsonl"),
        "hgb_signal_rows_sha256": sha256(namespace / "HGB_SIGNAL_ROWS.jsonl"),
        "traces_validated": EXPECTED_TRACES, "eligible_traces": len(eligible_positions),
        "forced_keep_counts": forced, "maximum_numeric_error": maximum_error,
        "hgb_model_loads": 1, "hgb_predict_proba_calls": 2, "hgb_fit_calls": 0,
        "neural_model_loads": 0, "neural_model_forwards": 0,
        "gold_values_read": 0, "scientific_fits": 0, "test_rows_read": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
