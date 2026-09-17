"""Run/resume paired GbV scoring for accepted Mistral test branches."""

from __future__ import annotations

import argparse
import collections
import gc
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import traceback

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    DurableLedger, read_jsonl, record, recover_or_execute, sha256,
    verify_manifest, write_json_durable,
)
from scripts.mistral_development_scoring_common import (
    DurableStageJournal, write_bytes_once,
)
from scripts.empirical_runtime_io import CPU_TEST_SHA, native_runtime, restore_dataset
from scripts.run_mistral_test_a0_query import (
    DATASETS, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_INPUT_LEDGER_SHA256, EXPECTED_TEST_POOL_MANIFEST_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256, EXPECTED_TEST_TRACE_SHA256,
    acquire_gpu_mutex, validate_selected_manifest, validate_test_binding,
)
from scripts.run_mistral_test_repair import EXPECTED_RETRIEVAL_MANIFEST_SHA256
from src.arbitration.mistral_reader_runtime import object_sha256, require, text_sha256
from src.evaluation.answer_normalization import assess_pair_eligibility
from src.verification.gbv_nli import (
    GBV_MODEL_ID, GBV_MODEL_REVISION, GBVPostAnsweringNLI, format_hypothesis,
    split_passage_to_fit,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
GBV_SOURCE_SHA256 = "a9ca2f6391b91fec2b56c309bdfb2543ff0a6ae9c5f8cfe89ff7e14358c11503"
HISTORICAL_PREFLIGHT_SHA256 = "f29a5ad13c2d8ce6cab3bb6331bd315837c70907fa9d71725339af07baeb5790"
GBV_PACKAGE_ROOT_RELATIVE = Path(
    "outputs/published_baseline_gbv_nli_v1/infrastructure/python_packages"
)
BATCH_SIZE = 8
LOGIT_WIDTH = 2
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60
MIN_DISK_FREE_BYTES = 20 * 1024 ** 3


def validate_hgb_gate(root: Path) -> tuple[Path, Path]:
    namespace = root / "hgb_signal"
    validation = root / "hgb_signal_validation/VALIDATION.json"
    require((namespace / "SHA256_MANIFEST.json").is_file() and validation.is_file(),
            "HGB_ACCEPTANCE_REQUIRED")
    verify_manifest(namespace, sha256(namespace / "SHA256_MANIFEST.json"))
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_FORMULA_MISTRAL_TEST_HGB_SIGNAL"
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value["hgb_feature_rows_sha256"] == sha256(namespace / "HGB_FEATURE_ROWS.jsonl")
            and value["hgb_signal_rows_sha256"] == sha256(namespace / "HGB_SIGNAL_ROWS.jsonl")
            and value["project_gold_values_read"] == 0
            and value["test_gold_values_read"] == 0
            and value["test_outcome_values_read"] == 0
            and value["scientific_fits"] == 0
            and value["test_input_rows_read"] == EXPECTED_TRACES,
            "HGB_VALIDATION_BINDING")
    return namespace, validation


def validate_gbv_assets(original: Path) -> tuple[Path, Path, list[dict]]:
    preflight = original / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/PREFLIGHT_INPUT_VERIFICATION.json"
    source = REPO / "src/verification/gbv_nli.py"
    require(sha256(preflight) == HISTORICAL_PREFLIGHT_SHA256
            and sha256(source) == GBV_SOURCE_SHA256, "GBV_SOURCE_PINS")
    value = json.loads(preflight.read_text(encoding="utf-8"))
    require(value["gbv"]["fingerprint"] == "d3cb8a434c78bb162315f3c5f1dd893b441af71a712958c14854ce32f37a3339"
            and len(value["gbv_local_cache_copies"]) == 7, "GBV_INVENTORY")
    package_root = (original / value["gbv"]["package_root"]).resolve()
    require(value["gbv"]["package_root"] == GBV_PACKAGE_ROOT_RELATIVE.as_posix()
            and package_root.is_dir()
            and len(value["gbv"]["package_files"]) == 17,
            "GBV_SENTENCEPIECE_INVENTORY")
    records = [record(preflight), record(source)]
    for item in value["gbv"]["package_files"]:
        path = (original / item["path"]).resolve()
        require(path.is_relative_to(package_root)
                and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"],
                "GBV_SENTENCEPIECE_ASSET:" + item["path"])
        records.append(record(path))
    provenance = value["gbv"]["provenance"]
    provenance_path = (original / provenance["path"]).resolve()
    require(provenance_path.stat().st_size == provenance["size_bytes"]
            and sha256(provenance_path) == provenance["sha256"],
            "GBV_SENTENCEPIECE_PROVENANCE")
    records.append(record(provenance_path))
    snapshot = None
    for entry in value["gbv_local_cache_copies"]:
        item = entry["copy"]; path = (original / item["path"]).resolve()
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "GBV_ASSET:" + item["path"])
        records.append(record(path)); snapshot = path.parent
    require(snapshot is not None and snapshot.name == GBV_MODEL_REVISION, "GBV_SNAPSHOT")
    return snapshot, package_root, records


def validate_sentencepiece_runtime(package_root: Path) -> dict:
    import sentencepiece
    module_path = Path(sentencepiece.__file__).resolve()
    require(module_path.is_relative_to(package_root)
            and sentencepiece.__version__ == "0.2.1",
            "GBV_SENTENCEPIECE_RUNTIME")
    return {
        "version": sentencepiece.__version__,
        "module_path": str(module_path),
    }


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


def prepare_pairs(scorer, question: str, answer: str,
                  evidence_texts: list[str]) -> tuple[str, list[tuple[str, str]]]:
    hypothesis = format_hypothesis(question, answer)
    require(bool(evidence_texts), "NO_EVIDENCE_PASSAGES")
    pairs = []
    for passage in evidence_texts:
        chunks = split_passage_to_fit(
            scorer.tokenizer, passage, hypothesis,
            max_length=scorer.max_length,
        )
        pairs.extend((chunk, hypothesis) for chunk in chunks)
    require(bool(pairs), "NO_NLI_PAIRS")
    return hypothesis, pairs


def deterministic_nli_error(message: str) -> bool:
    return message == "hypothesis does not fit the NLI context window" or bool(
        re.fullmatch(
            r"single-word premise at position [0-9]+ does not fit the NLI context window",
            message,
        )
    )


def retain_scored_branch(row: dict, state: str, payload: dict) -> None:
    require(payload["status"] == "scored" and math.isfinite(payload["score"]),
            "GBV_RETAIN_SCORED_BRANCH")
    if state == "a0_e0":
        require(row["F0"] is None and row["e0_chunk_count"] == 0,
                "GBV_DUPLICATE_F0")
        row["F0"] = payload["score"]
        row["e0_chunk_count"] = payload["chunk_count"]
    elif state == "a1_e1":
        require(row["F1"] is None and row["e1_chunk_count"] == 0,
                "GBV_DUPLICATE_F1")
        row["F1"] = payload["score"]
        row["e1_chunk_count"] = payload["chunk_count"]
    else:
        raise RuntimeError("GBV_UNKNOWN_BRANCH_STATE")


def expected_token_batches(scorer, pairs: list[tuple[str, str]]) -> list[dict]:
    result = []
    for start in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[start:start + BATCH_SIZE]
        encoded = scorer.tokenizer(
            [value[0] for value in batch], [value[1] for value in batch],
            add_special_tokens=True, truncation=False, padding=True,
            return_tensors="pt",
        )
        require(int(encoded["input_ids"].shape[1]) <= scorer.max_length,
                "OVERLENGTH_EXPECTED_BATCH")
        result.append({name: tensor.tolist() for name, tensor in encoded.items()})
    return result


def softmax_entailment(logits: np.ndarray, entailment_index: int) -> np.ndarray:
    require(logits.ndim == 2 and logits.shape[1] == LOGIT_WIDTH
            and np.isfinite(logits).all(), "GBV_LOGIT_SCHEMA")
    shifted = logits.astype(np.float64) - np.max(logits.astype(np.float64), axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp[:, entailment_index] / np.sum(exp, axis=1)


def validate_branch_payload(payload: dict, *, trace: dict, role: str, state: str,
                            question: str, answer: str, evidence_texts: list[str],
                            expected_pairs: list[tuple[str, str]] | None,
                            expected_tokens: list[dict] | None,
                            stage_output: Path, entailment_index: int) -> None:
    require(payload["position"] == trace["position"] and payload["state"] == state
            and payload["dataset"] == trace["dataset"]
            and payload["retriever"] == trace["retriever"]
            and payload["sample_id"] == trace["sample_id"] and payload["role"] == role
            and payload["question_sha256"] == object_sha256(question)
            and payload["answer_sha256"] == text_sha256(answer)
            and payload["evidence_sha256"] == object_sha256(evidence_texts)
            and payload["premise_count"] == len(evidence_texts), "GBV_BRANCH_IDENTITY")
    if payload["status"] == "unscorable":
        require(expected_pairs is None and expected_tokens is None
                and isinstance(payload["diagnostic"], str) and payload["diagnostic"]
                and payload["hypothesis_sha256"] is None
                and payload["pair_bindings"] == []
                and payload["chunk_count"] == 0 and payload["forwards"] == []
                and payload["score"] is None, "GBV_UNSCORABLE_PAYLOAD")
        return
    require(payload["status"] == "scored" and expected_pairs is not None
            and expected_tokens is not None
            and payload["hypothesis_sha256"] == text_sha256(expected_pairs[0][1])
            and payload["chunk_count"] == len(expected_pairs)
            and payload["pair_bindings"] == [{
                "premise_sha256": text_sha256(premise),
                "hypothesis_sha256": text_sha256(hypothesis),
            } for premise, hypothesis in expected_pairs]
            and len(payload["forwards"]) == len(expected_tokens), "GBV_SCORED_PAYLOAD")
    probabilities = []
    for batch_index, (forward, token_fields) in enumerate(
            zip(payload["forwards"], expected_tokens, strict=True)):
        start = batch_index * BATCH_SIZE; stop = min(start + BATCH_SIZE, len(expected_pairs))
        require(forward["batch_index"] == batch_index
                and forward["pair_indices"] == list(range(start, stop))
                and forward["token_fields"] == token_fields, "GBV_FORWARD_IDENTITY")
        meta = forward["logits"]; path = (stage_output / meta["path"]).resolve()
        rows = stop - start
        require(path.is_relative_to(stage_output)
                and path.stat().st_size == meta["size_bytes"] == rows * LOGIT_WIDTH * 4
                and sha256(path) == meta["sha256"] and meta["dtype"] == "float32"
                and meta["shape"] == [rows, LOGIT_WIDTH]
                and meta["byte_order"] == "little", "GBV_LOGIT_BINDING")
        logits = np.fromfile(path, dtype="<f4").reshape(rows, LOGIT_WIDTH)
        probabilities.extend(softmax_entailment(logits, entailment_index).tolist())
    score = max(probabilities)
    require(math.isfinite(score) and abs(payload["score"] - score) <= 1e-7,
            "GBV_SCORE_RECOMPUTATION")


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
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    original = args.project_root.resolve(); root = args.test_root.resolve()
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve()
            and sys.byteorder == "little", "FIXED_ROOTS_OR_BYTE_ORDER")
    hgb_stage, hgb_validation = validate_hgb_gate(root)
    stage_output = root / "gbv"
    require(not any((stage_output / name).exists() for name in
                    ("STAGE_RECEIPT.json", "STAGE_FAILURE.json", "SHA256_MANIFEST.json")),
            "TERMINAL_STAGE_IMMUTABLE")
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
            "COMMIT_BEFORE_EXECUTION")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    started = time.perf_counter(); scorer = journal = ledger = mutex = prehook = posthook = None
    observed_forwards = 0; observed_pairs = 0; completed_traces = 0
    modes = collections.Counter(); forced = collections.Counter()
    result: dict[str, object] = {
        "status": "FAIL", "cas_q3_status": "NOT READY", "source_commit": commit,
        "stage": "gbv", "project_gold_values_read": 0,
        "test_gold_values_read": 0, "test_outcome_values_read": 0,
        "scientific_fits": 0, "test_input_rows_read": 0,
        "mistral_model_loads": 0, "bge_model_loads": 0,
        "nli_model_loads": 0, "nli_model_unloads": 0,
    }
    try:
        if not args.resume: stage_output.mkdir(parents=True, exist_ok=False)
        import psutil
        require(psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES, "DISK_FREE_ADMISSION")
        snapshot, package_root, asset_records = validate_gbv_assets(original)
        expected_hf_home = original / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/cache/hf"
        expected_hub = expected_hf_home / "hub"
        required_environment = {
            "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false", "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
            "HF_HOME": str(expected_hf_home), "HF_HUB_CACHE": str(expected_hub),
            "PYTHONPATH": str(package_root),
        }
        require(all(os.environ.get(key) == value for key, value in required_environment.items()),
                "GBV_FROZEN_ENVIRONMENT")
        sentencepiece_runtime = validate_sentencepiece_runtime(package_root)
        mutex = acquire_gpu_mutex()
        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        input_manifest = input_freeze / "SHA256_MANIFEST.json"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(sha256(input_manifest) == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
                and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256, "INPUT_FREEZE")
        preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
        pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        retrieval = REPO / "outputs/cas_q2/empirical_retrieval_v1"
        cpu_tests = REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1"
        trace_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
        require(sha256(trace_path) == EXPECTED_TEST_TRACE_SHA256,
                "TEST_TRACE_PIN")
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
            *verify_manifest(hgb_stage, sha256(hgb_stage / "SHA256_MANIFEST.json")),
            hgb_validation,
        ]
        for stage in ("a0_query", "repair", "a1_likelihood"):
            namespace = root / stage
            paths.extend(verify_manifest(
                namespace, sha256(namespace / "SHA256_MANIFEST.json")
            ))
            validation = root / f"{stage}_validation/VALIDATION.json"
            require(validation.is_file(), "PRIOR_VALIDATION_MISSING:" + stage)
            paths.append(validation)
        controls = [
            Path(__file__), REPO / "scripts/validate_mistral_test_gbv.py",
            REPO / "scripts/empirical_runtime_io.py",
            REPO / "scripts/empirical_retrieval_io.py",
            REPO / "scripts/empirical_pool_io.py",
            REPO / "scripts/empirical_runtime_contract.py",
            REPO / "scripts/replay_roa_original.py",
            REPO / "scripts/verify_roa_artifacts.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/mistral_development_scoring_common.py",
            REPO / "scripts/run_mistral_test_a0_query.py",
            REPO / "scripts/run_mistral_test_repair.py",
            REPO / "scripts/validate_mistral_test_a0_query.py",
            REPO / "scripts/empirical_feature_independent.py",
            REPO / "src/evaluation/answer_normalization.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            REPO / "docs/cas_q3/MISTRAL_TEST_GBV_INPUT_GRAPH_AMENDMENT_2026-09-17.md",
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/SHA256_MANIFEST.json",
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/runtime_support.py",
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/native_runtime.py",
            Path(sys.executable),
        ]
        records = [record(path) for path in sorted(
            {Path(path).resolve() for path in [*paths, *controls]}, key=str
        )]
        by_path = {item["path"]: item for item in [*records, *asset_records]}
        require(len(by_path) == len(records) + len(asset_records),
                "UNIQUE_GBV_INPUTS")
        input_records = [by_path[path] for path in sorted(by_path)]
        freeze = {
            "status": "FROZEN_BEFORE_MISTRAL_TEST_GBV", "source_commit": commit,
            "stage": "gbv", "expected_traces": EXPECTED_TRACES,
            "model_id": GBV_MODEL_ID, "model_revision": GBV_MODEL_REVISION,
            "batch_size": BATCH_SIZE, "dtype": "float32", "device": "cuda:0",
            "branch_order": ["a0_e0", "a1_e1"], "inputs": input_records,
            "environment": required_environment, "host": platform.platform(),
            "sentencepiece_runtime": sentencepiece_runtime,
            "python": str(Path(sys.executable).resolve()),
            "test_gold_access": "FORBIDDEN",
            "test_outcome_access": "FORBIDDEN",
            "scientific_fit_access": "FORBIDDEN",
            "scope": "test paired GbV only; Mistral/BGE/Gold/outcome/fit/tuning forbidden",
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                    "RESUME_FREEZE_MISMATCH")
        else:
            write_json_durable(freeze_path, freeze)
        wrapper, native, nodes, boundary = native_runtime(original)
        traces = list(read_jsonl(trace_path))
        test_rows = validate_test_binding(traces, read_jsonl(frozen_ledger))
        result["test_input_rows_read"] = EXPECTED_TRACES
        a0_rows = list(read_jsonl(root / "a0_query/GENERATION_RECEIPTS.jsonl"))
        repair_rows = list(read_jsonl(root / "repair/REPAIR_BINDINGS.jsonl"))
        a1_rows = list(read_jsonl(root / "a1_likelihood/MODEL_RECEIPTS.jsonl"))
        a0_map = {row["payload"]["position"]: row["payload"]
                  for row in a0_rows if row["operation"] == "a0"}
        repair_map = {row["payload"]["position"]: row["payload"] for row in repair_rows}
        a1_map = {row["payload"]["position"]: row["payload"]
                  for row in a1_rows if row["operation"] == "a1"}
        require(len(a0_rows) == 36_000 and len(repair_rows) == EXPECTED_TRACES
                and len(a1_rows) == 90_000
                and len(a0_map) == len(repair_map) == len(a1_map) == EXPECTED_TRACES,
                "BRANCH_SOURCE_COUNTS")
        journal = DurableStageJournal(stage_output / "CALL_JOURNAL.jsonl", resume=args.resume,
                                      allowed_operations={"gbv_branch"})
        ledger = DurableLedger(stage_output / "BRANCH_RECEIPTS.jsonl", resume=args.resume)
        import torch
        require(torch.cuda.is_available(), "GBV_CUDA_REQUIRED")
        device = torch.cuda.get_device_properties(0)
        require(device.name == "NVIDIA GeForce RTX 5060 Ti", "GBV_GPU_IDENTITY")
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False; torch.backends.cudnn.deterministic = True
        torch.cuda.reset_peak_memory_stats(0)
        scorer = GBVPostAnsweringNLI(
            model_id=GBV_MODEL_ID, revision=GBV_MODEL_REVISION,
            device="cuda:0", batch_size=BATCH_SIZE, torch_dtype="float32",
            local_files_only=True,
        )
        result["nli_model_loads"] = 1
        require(scorer.model.__class__.__name__ == "DebertaV2ForSequenceClassification"
                and getattr(scorer.model.config, "_commit_hash", None) == GBV_MODEL_REVISION
                and scorer.entailment_index == 0 and scorer.max_length == 512
                and scorer.resolved_dtype == "torch.float32" and not scorer.model.training,
                "GBV_MODEL_IDENTITY")
        observer = {"active": False, "expected": [], "captured": [], "current": None,
                    "prefix": None}
        def before_forward(_module, _args, kwargs):
            nonlocal observed_forwards, observed_pairs
            require(observer["active"] and observer["current"] is None
                    and torch.is_inference_mode_enabled() and not torch.is_grad_enabled()
                    and not scorer.model.training, "GBV_FORWARD_CONTEXT")
            index = len(observer["captured"])
            require(index < len(observer["expected"]), "GBV_UNEXPECTED_FORWARD")
            actual = {name: tensor.detach().cpu().tolist() for name, tensor in kwargs.items()}
            require(actual == observer["expected"][index], "GBV_FORWARD_TOKEN_BINDING")
            observer["current"] = index; observed_forwards += 1
            observed_pairs += len(actual["input_ids"])
        def after_forward(_module, _args, _kwargs, output):
            index = observer["current"]
            require(observer["active"] and index == len(observer["captured"]),
                    "GBV_FORWARD_OUTPUT_ORDER")
            logits = np.ascontiguousarray(output.logits.detach().float().cpu().numpy(),
                                          dtype="<f4")
            require(logits.ndim == 2 and logits.shape[1] == LOGIT_WIDTH
                    and np.isfinite(logits).all(), "GBV_FORWARD_LOGITS")
            relative = Path("logits") / f"{observer['prefix']}_{index:02d}.f32"
            write_bytes_once(stage_output / relative, logits.tobytes(order="C"))
            meta = record(stage_output / relative); meta["path"] = relative.as_posix()
            meta.update(dtype="float32", shape=list(logits.shape), byte_order="little")
            observer["captured"].append(meta); observer["current"] = None
        prehook = scorer.model.register_forward_pre_hook(before_forward, with_kwargs=True)
        posthook = scorer.model.register_forward_hook(after_forward, with_kwargs=True)

        class NoEmbeddingBackend:
            dimension = 768
            def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")
            def encode_documents(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")

        backend = NoEmbeddingBackend(); current_dataset = None; data = None; gbv_rows = []
        for position, trace in enumerate(traces):
            if trace["dataset"] != current_dataset:
                data = restore_dataset(trace["dataset"], native, backend)
                current_dataset = trace["dataset"]
            question = data["questions"][trace["sample_id"]]
            e0 = wrapper.original_evidence(trace, data, native)
            e1 = reconstruct_e1(native, e0, repair_map[position], data)
            a0, a1 = a0_map[position]["parsed_text"], a1_map[position]["parsed_text"]
            eligibility = assess_pair_eligibility(a0, a1)
            row = {
                "dataset": trace["dataset"], "retriever": trace["retriever"],
                "sample_id": trace["sample_id"], "position": position,
                "role": test_rows[position]["role"], "pair_eligible": eligibility.eligible,
                "eligible": eligibility.eligible, "forced_keep_reason": eligibility.reason,
                "F0": None, "F1": None, "gbv_margin": None,
                "e0_premise_count": len(e0), "e1_premise_count": len(e1),
                "e0_chunk_count": 0, "e1_chunk_count": 0,
                "branch_receipt_sha256": {}, "model_id": GBV_MODEL_ID,
                "model_revision": GBV_MODEL_REVISION,
            }
            if not eligibility.eligible:
                forced[eligibility.reason] += 1; gbv_rows.append(row)
                completed_traces += 1
                if completed_traces % 50 == 0:
                    print(json.dumps({"stage": "gbv", "completed_traces": completed_traces,
                                      "expected_traces": EXPECTED_TRACES}, sort_keys=True),
                          flush=True)
                continue
            branch_payloads = {}
            for state_name, answer, evidence in (("a0_e0", a0, e0), ("a1_e1", a1, e1)):
                evidence_texts = [item.text for item in evidence]
                key = f"gbv:{position:05d}:{state_name}"
                input_value = {
                    "dataset": trace["dataset"], "retriever": trace["retriever"],
                    "sample_id": trace["sample_id"], "position": position,
                    "role": test_rows[position]["role"], "state": state_name,
                    "question": question, "answer": answer, "evidence_texts": evidence_texts,
                }
                pair_error = None
                try:
                    hypothesis, pairs = prepare_pairs(scorer, question, answer, evidence_texts)
                    token_batches = expected_token_batches(scorer, pairs)
                except ValueError as exc:
                    pair_error = str(exc)
                    require(deterministic_nli_error(pair_error), "GBV_UNEXPECTED_PREPARATION_ERROR")
                    hypothesis = None; pairs = token_batches = None
                def execute(state_name=state_name, answer=answer, evidence_texts=evidence_texts,
                            hypothesis=hypothesis, pairs=pairs, token_batches=token_batches,
                            pair_error=pair_error, key=key, trace=trace,
                            position=position, question=question,
                             role=test_rows[position]["role"]):
                    if pair_error is not None:
                        before = observed_forwards
                        try:
                            scorer.score_branch(question, answer, evidence_texts)
                        except ValueError as exc:
                            require(str(exc) == pair_error, "GBV_UNSCORABLE_DIAGNOSTIC")
                        else:
                            raise RuntimeError("GBV_EXPECTED_UNSCORABLE")
                        require(observed_forwards == before, "GBV_UNSCORABLE_FORWARD")
                        return {
                            "status": "unscorable", "dataset": trace["dataset"],
                            "retriever": trace["retriever"], "sample_id": trace["sample_id"],
                            "position": position, "role": role,
                            "state": state_name, "question_sha256": object_sha256(question),
                            "answer_sha256": text_sha256(answer),
                            "evidence_sha256": object_sha256(evidence_texts),
                            "premise_count": len(evidence_texts), "chunk_count": 0,
                            "hypothesis_sha256": None, "pair_bindings": [],
                            "forwards": [], "score": None, "diagnostic": pair_error,
                        }
                    observer.update(active=True, expected=token_batches, captured=[],
                                    current=None, prefix=f"{position:05d}_{state_name}")
                    try:
                        branch_score = scorer.score_branch(question, answer, evidence_texts)
                    finally:
                        observer["active"] = False
                    require(observer["current"] is None
                            and len(observer["captured"]) == len(token_batches),
                            "GBV_FORWARD_COUNT")
                    forwards = []
                    for batch_index, (tokens, meta) in enumerate(
                            zip(token_batches, observer["captured"], strict=True)):
                        start = batch_index * BATCH_SIZE
                        stop = min(start + BATCH_SIZE, len(pairs))
                        forwards.append({
                            "batch_index": batch_index,
                            "pair_indices": list(range(start, stop)),
                            "token_fields": tokens, "logits": meta,
                        })
                    return {
                        "status": "scored", "dataset": trace["dataset"],
                        "retriever": trace["retriever"], "sample_id": trace["sample_id"],
                        "position": position, "role": role,
                        "state": state_name, "question_sha256": object_sha256(question),
                        "answer_sha256": text_sha256(answer),
                        "evidence_sha256": object_sha256(evidence_texts),
                        "premise_count": branch_score.premise_count,
                        "chunk_count": branch_score.chunk_count,
                        "hypothesis_sha256": text_sha256(hypothesis),
                        "pair_bindings": [{
                            "premise_sha256": text_sha256(premise),
                            "hypothesis_sha256": text_sha256(hyp),
                        } for premise, hyp in pairs],
                        "forwards": forwards, "score": float(branch_score.score),
                        "diagnostic": None,
                    }
                saved, mode = recover_or_execute(
                    journal=journal, ledger=ledger, key=key, operation="gbv_branch",
                    input_sha256=object_sha256(input_value), execute=execute,
                )
                validate_branch_payload(
                    saved["payload"], trace=trace, role=test_rows[position]["role"],
                    state=state_name, question=question, answer=answer,
                    evidence_texts=evidence_texts, expected_pairs=pairs,
                    expected_tokens=token_batches, stage_output=stage_output,
                    entailment_index=scorer.entailment_index,
                )
                modes[mode] += 1; branch_payloads[state_name] = saved["payload"]
                row["branch_receipt_sha256"][state_name] = object_sha256(saved)
                if saved["payload"]["status"] == "unscorable":
                    row["eligible"] = False
                    row["forced_keep_reason"] = "nli_unscorable:" + saved["payload"]["diagnostic"]
                    forced["nli_unscorable"] += 1
                    break
                retain_scored_branch(row, state_name, saved["payload"])
            if row["eligible"]:
                require(set(branch_payloads) == {"a0_e0", "a1_e1"}, "GBV_BRANCH_COMPLETENESS")
                row["gbv_margin"] = row["F1"] - row["F0"]
            gbv_rows.append(row); completed_traces += 1
            if completed_traces % 50 == 0:
                print(json.dumps({"stage": "gbv", "completed_traces": completed_traces,
                                  "expected_traces": EXPECTED_TRACES}, sort_keys=True), flush=True)
        require(len(gbv_rows) == completed_traces == EXPECTED_TRACES
                and journal.pending is None, "GBV_COMPLETE")
        gbv_raw = b"".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False).encode("utf-8") + b"\n"
            for row in gbv_rows
        )
        write_bytes_once(stage_output / "GBV_ROWS.jsonl", gbv_raw)
        logical_forwards = sum(len(row["payload"]["forwards"]) for row in ledger.rows)
        logical_pairs = sum(row["payload"]["chunk_count"] for row in ledger.rows
                            if row["payload"]["status"] == "scored")
        completed_branch_operations = len(ledger.rows)
        prehook.remove(); prehook = None; posthook.remove(); posthook = None
        del scorer.model; del scorer.tokenizer; scorer = None
        gc.collect(); torch.cuda.empty_cache()
        allocated_after = int(torch.cuda.memory_allocated(0))
        require(allocated_after < 1024 ** 3, "GBV_NOT_RELEASED")
        result["nli_model_unloads"] = 1
        journal.close(); journal = None; ledger.close(); ledger = None
        for item in input_records: require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started; require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update(
            status="PASS_MISTRAL_TEST_GBV_PENDING_INDEPENDENT",
            completed_traces=EXPECTED_TRACES,
            pair_eligible_traces=sum(row["pair_eligible"] for row in gbv_rows),
            scored_traces=sum(row["eligible"] for row in gbv_rows),
            forced_keep_counts=dict(forced),
            completed_branch_operations=completed_branch_operations,
            logical_nli_forwards=logical_forwards, logical_nli_pairs=logical_pairs,
            observed_nli_forwards_current_process=observed_forwards,
            observed_nli_pairs_current_process=observed_pairs,
            operation_modes=dict(modes), cuda_allocated_after_close_bytes=allocated_after,
            native_ast_nodes=nodes, generation_boundary=boundary,
            elapsed_seconds=elapsed,
            branch_receipts=record(stage_output / "BRANCH_RECEIPTS.jsonl"),
            gbv_rows=record(stage_output / "GBV_ROWS.jsonl"),
            call_journal=record(stage_output / "CALL_JOURNAL.jsonl"),
        )
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output); print(result["status"], flush=True); return 0
    except Exception as exc:
        result.update(status="FAIL_MISTRAL_TEST_GBV",
                      error_type=type(exc).__name__, diagnostic=str(exc),
                      traceback=traceback.format_exc(), completed_traces=completed_traces,
                      observed_nli_forwards_current_process=observed_forwards,
                      observed_nli_pairs_current_process=observed_pairs,
                      operation_modes=dict(modes), elapsed_seconds=time.perf_counter() - started)
        if prehook is not None:
            try: prehook.remove()
            except Exception: pass
        if posthook is not None:
            try: posthook.remove()
            except Exception: pass
        if scorer is not None:
            try:
                del scorer.model; del scorer.tokenizer
            except Exception: pass
        if journal is not None:
            try: journal.close()
            except Exception: pass
        if ledger is not None:
            try: ledger.close()
            except Exception: pass
        if stage_output.is_dir() and not (stage_output / "STAGE_FAILURE.json").exists():
            write_json_durable(stage_output / "STAGE_FAILURE.json", result); seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True); return 2
    finally:
        if mutex is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(mutex)
            except Exception: pass


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
