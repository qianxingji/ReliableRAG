"""Independent tokenizer/logit validation of Mistral development paired GbV."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_feature_independent import pair_eligibility
from scripts.validate_mistral_development_a0_query import (
    load_original_native, object_sha, read_rows, require, sha256,
)
from src.verification.gbv_nli import (
    GBV_MODEL_ID, GBV_MODEL_REVISION, format_hypothesis, resolve_entailment_index,
    split_passage_to_fit,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_TRACES = 13_500
BATCH_SIZE = 8
LOGIT_WIDTH = 2
GBV_SOURCE_SHA256 = "a9ca2f6391b91fec2b56c309bdfb2543ff0a6ae9c5f8cfe89ff7e14358c11503"
HISTORICAL_PREFLIGHT_SHA256 = "f29a5ad13c2d8ce6cab3bb6331bd315837c70907fa9d71725339af07baeb5790"
GBV_PACKAGE_ROOT_RELATIVE = Path(
    "outputs/published_baseline_gbv_nli_v1/infrastructure/python_packages"
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


def validate_hgb(root: Path) -> Path:
    namespace = root / "hgb_signal"; validate_manifest(namespace)
    validation = root / "hgb_signal_validation/VALIDATION.json"
    value = json.loads(validation.read_text(encoding="utf-8"))
    require(value["status"] == "PASS_INDEPENDENT_FORMULA_MISTRAL_DEVELOPMENT_HGB_SIGNAL"
            and value["producer_receipt_sha256"] == sha256(namespace / "STAGE_RECEIPT.json")
            and value["hgb_feature_rows_sha256"] == sha256(namespace / "HGB_FEATURE_ROWS.jsonl")
            and value["hgb_signal_rows_sha256"] == sha256(namespace / "HGB_SIGNAL_ROWS.jsonl"),
            "HGB_VALIDATION_BINDING")
    return validation


def validate_assets(original: Path) -> tuple[Path, Path]:
    preflight = original / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/PREFLIGHT_INPUT_VERIFICATION.json"
    source = REPO / "src/verification/gbv_nli.py"
    require(sha256(preflight) == HISTORICAL_PREFLIGHT_SHA256
            and sha256(source) == GBV_SOURCE_SHA256, "GBV_SOURCE_PINS")
    value = json.loads(preflight.read_text(encoding="utf-8"))
    require(value["gbv"]["fingerprint"] == "d3cb8a434c78bb162315f3c5f1dd893b441af71a712958c14854ce32f37a3339",
            "GBV_FINGERPRINT")
    require(len(value["gbv_local_cache_copies"]) == 7, "GBV_MODEL_ASSET_COUNT")
    package_root = (original / value["gbv"]["package_root"]).resolve()
    require(value["gbv"]["package_root"] == GBV_PACKAGE_ROOT_RELATIVE.as_posix()
            and package_root.is_dir()
            and len(value["gbv"]["package_files"]) == 17,
            "GBV_SENTENCEPIECE_INVENTORY")
    for item in value["gbv"]["package_files"]:
        path = (original / item["path"]).resolve()
        require(path.is_relative_to(package_root)
                and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"],
                "GBV_SENTENCEPIECE_ASSET:" + item["path"])
    provenance = value["gbv"]["provenance"]
    provenance_path = (original / provenance["path"]).resolve()
    require(provenance_path.stat().st_size == provenance["size_bytes"]
            and sha256(provenance_path) == provenance["sha256"],
            "GBV_SENTENCEPIECE_PROVENANCE")
    snapshot = None
    for entry in value["gbv_local_cache_copies"]:
        item = entry["copy"]; path = (original / item["path"]).resolve()
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "GBV_ASSET:" + item["path"])
        snapshot = path.parent
    require(snapshot is not None and snapshot.name == GBV_MODEL_REVISION, "GBV_SNAPSHOT")
    return snapshot, package_root


def validate_sentencepiece_runtime(package_root: Path) -> dict:
    import sentencepiece
    module_path = Path(sentencepiece.__file__).resolve()
    require(module_path.is_relative_to(package_root)
            and sentencepiece.__version__ == "0.2.1",
            "GBV_SENTENCEPIECE_RUNTIME")
    return {"version": sentencepiece.__version__, "module_path": str(module_path)}


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


def prepare_pairs(tokenizer, question: str, answer: str,
                  evidence_texts: list[str]) -> tuple[str, list[tuple[str, str]]]:
    hypothesis = format_hypothesis(question, answer)
    require(bool(evidence_texts), "NO_EVIDENCE_PASSAGES")
    pairs = []
    for passage in evidence_texts:
        chunks = split_passage_to_fit(
            tokenizer, passage, hypothesis, max_length=512,
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


def token_batches(tokenizer, pairs: list[tuple[str, str]]) -> list[dict]:
    result = []
    for start in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[start:start + BATCH_SIZE]
        encoded = tokenizer(
            [value[0] for value in batch], [value[1] for value in batch],
            add_special_tokens=True, truncation=False, padding=True,
            return_tensors="pt",
        )
        require(int(encoded["input_ids"].shape[1]) <= 512, "OVERLENGTH_TOKEN_BATCH")
        result.append({name: tensor.tolist() for name, tensor in encoded.items()})
    return result


def entailment_probabilities(logits: np.ndarray, entailment_index: int) -> np.ndarray:
    require(logits.ndim == 2 and logits.shape[1] == LOGIT_WIDTH
            and np.isfinite(logits).all(), "GBV_LOGIT_SCHEMA")
    values = logits.astype(np.float64)
    shifted = values - np.max(values, axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials[:, entailment_index] / np.sum(exponentials, axis=1)


def validate_journal(rows: list[dict], events: list[dict]) -> int:
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_BRANCH_ROWS")
    pending = None; completed = {}; recoveries = 0
    for sequence, event in enumerate(events):
        require(event["sequence"] == sequence, "JOURNAL_SEQUENCE")
        key = event["operation_key"]
        if event["event"] == "intent":
            require(pending is None and key not in completed
                    and event["operation"] == "gbv_branch", "JOURNAL_INTENT")
            pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None and key == pending["operation_key"]
                    and event["operation"] == pending["operation"]
                    and event["input_sha256"] == pending["input_sha256"], "JOURNAL_RESUME")
            recoveries += 1
        else:
            require(event["event"] == "result" and pending is not None
                    and key == pending["operation_key"] and key in row_map,
                    "JOURNAL_RESULT")
            row = row_map[key]
            require(event["operation"] == pending["operation"] == row["operation"]
                    and pending["input_sha256"] == row["input_sha256"]
                    and event["result_sha256"] == object_sha(row), "JOURNAL_RESULT_HASH")
            completed[key] = event; pending = None
    require(pending is None and set(completed) == set(row_map), "COMPLETE_JOURNAL")
    return recoveries


def validate_branch(payload: dict, *, trace: dict, role: str, state: str,
                    question: str, answer: str, evidence_texts: list[str],
                    tokenizer, namespace: Path, entailment_index: int):
    require(payload["position"] == trace["position"] and payload["state"] == state
            and payload["dataset"] == trace["dataset"]
            and payload["retriever"] == trace["retriever"]
            and payload["sample_id"] == trace["sample_id"] and payload["role"] == role
            and payload["question_sha256"] == object_sha(question)
            and payload["answer_sha256"] == text_sha(answer)
            and payload["evidence_sha256"] == object_sha(evidence_texts)
            and payload["premise_count"] == len(evidence_texts), "BRANCH_IDENTITY")
    try:
        hypothesis, pairs = prepare_pairs(tokenizer, question, answer, evidence_texts)
        batches = token_batches(tokenizer, pairs); expected_error = None
    except ValueError as exc:
        expected_error = str(exc)
        require(deterministic_nli_error(expected_error), "UNEXPECTED_PREPARATION_ERROR")
        hypothesis = None; pairs = batches = None
    if expected_error is not None:
        require(payload["status"] == "unscorable" and payload["diagnostic"] == expected_error
                and payload["hypothesis_sha256"] is None
                and payload["pair_bindings"] == [] and payload["forwards"] == []
                and payload["chunk_count"] == 0 and payload["score"] is None,
                "UNSCORABLE_BRANCH")
        return None, 0, 0
    require(payload["status"] == "scored" and payload["diagnostic"] is None
            and payload["hypothesis_sha256"] == text_sha(hypothesis)
            and payload["chunk_count"] == len(pairs)
            and payload["pair_bindings"] == [{
                "premise_sha256": text_sha(premise),
                "hypothesis_sha256": text_sha(hyp),
            } for premise, hyp in pairs]
            and len(payload["forwards"]) == len(batches), "SCORED_BRANCH")
    probabilities = []
    for batch_index, (forward, expected_tokens) in enumerate(
            zip(payload["forwards"], batches, strict=True)):
        start = batch_index * BATCH_SIZE; stop = min(start + BATCH_SIZE, len(pairs))
        require(forward["batch_index"] == batch_index
                and forward["pair_indices"] == list(range(start, stop))
                and forward["token_fields"] == expected_tokens, "FORWARD_TOKENS")
        meta = forward["logits"]; path = (namespace / meta["path"]).resolve(); rows = stop - start
        require(path.is_relative_to(namespace)
                and meta["path"] == f"logits/{trace['position']:05d}_{state}_{batch_index:02d}.f32"
                and path.stat().st_size == meta["size_bytes"] == rows * LOGIT_WIDTH * 4
                and sha256(path) == meta["sha256"] and meta["dtype"] == "float32"
                and meta["shape"] == [rows, LOGIT_WIDTH]
                and meta["byte_order"] == sys.byteorder, "LOGIT_BINDING")
        logits = np.fromfile(path, dtype=np.float32).reshape(rows, LOGIT_WIDTH)
        probabilities.extend(entailment_probabilities(logits, entailment_index).tolist())
    score = max(probabilities)
    require(abs(payload["score"] - score) <= 1e-7, "SCORE_RECOMPUTATION")
    return payload["score"], len(batches), len(pairs)


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
    hgb_validation = validate_hgb(root); snapshot, package_root = validate_assets(original)
    require(os.environ.get("PYTHONPATH") == str(package_root),
            "GBV_SENTENCEPIECE_PYTHONPATH")
    sentencepiece_runtime = validate_sentencepiece_runtime(package_root)
    namespace = root / "gbv"; validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "PASS_MISTRAL_DEVELOPMENT_GBV_PENDING_INDEPENDENT"
            and receipt["completed_traces"] == EXPECTED_TRACES
            and receipt["nli_model_loads"] == receipt["nli_model_unloads"] == 1
            and receipt["mistral_model_loads"] == receipt["bge_model_loads"] == 0
            and receipt["gold_values_read"] == receipt["scientific_fits"]
            == receipt["test_rows_read"] == 0, "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"] and freeze["stage"] == "gbv"
            and freeze["expected_traces"] == EXPECTED_TRACES
            and freeze["model_id"] == GBV_MODEL_ID and freeze["model_revision"] == GBV_MODEL_REVISION
            and freeze["batch_size"] == BATCH_SIZE and freeze["dtype"] == "float32"
            and freeze["branch_order"] == ["a0_e0", "a1_e1"]
            and freeze["environment"]["PYTHONPATH"] == str(package_root)
            and freeze["sentencepiece_runtime"] == sentencepiece_runtime,
            "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "FROZEN_INPUT")
    require(len({Path(item["path"]).resolve() for item in freeze["inputs"]})
            == len(freeze["inputs"]), "UNIQUE_FROZEN_INPUTS")
    require(hgb_validation.resolve() in {Path(item["path"]).resolve() for item in freeze["inputs"]},
            "FROZEN_HGB_VALIDATION")
    branch_rows = read_rows(namespace / "BRANCH_RECEIPTS.jsonl")
    gbv_rows = read_rows(namespace / "GBV_ROWS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(gbv_rows) == EXPECTED_TRACES
            and len(branch_rows) == receipt["completed_branch_operations"], "OUTPUT_COUNTS")
    recoveries = validate_journal(branch_rows, events)

    config = json.loads((snapshot / "config.json").read_text(encoding="utf-8"))
    entailment_index = resolve_entailment_index(config["id2label"])
    require(entailment_index == 0, "ENTAILMENT_INDEX")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, use_fast=False, local_files_only=True, trust_remote_code=False,
    )
    runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    traces = read_rows(runtime_root / "trace_manifest.jsonl")
    frozen_rows = [row for row in read_rows(
        REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl"
    ) if row.get("cohort") == "development"]
    a0_rows = read_rows(root / "a0_query/GENERATION_RECEIPTS.jsonl")
    repair_rows = read_rows(root / "repair/REPAIR_BINDINGS.jsonl")
    a1_rows = read_rows(root / "a1_likelihood/MODEL_RECEIPTS.jsonl")
    a0_map = {row["payload"]["position"]: row["payload"]
              for row in a0_rows if row["operation"] == "a0"}
    repair_map = {row["payload"]["position"]: row["payload"] for row in repair_rows}
    a1_map = {row["payload"]["position"]: row["payload"]
              for row in a1_rows if row["operation"] == "a1"}
    require(len(traces) == len(frozen_rows) == len(a0_map) == len(repair_map)
            == len(a1_map) == EXPECTED_TRACES, "SOURCE_COUNTS")
    loader, native = load_original_native(original)

    class NoEmbeddingBackend:
        dimension = 768
        def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")
        def encode_documents(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")

    backend = NoEmbeddingBackend(); current_dataset = None; data = None
    branch_index = 0; logical_forwards = 0; logical_pairs = 0
    forced = {}; scored = 0; pair_eligible_count = 0; checks = 0
    for position, trace in enumerate(traces):
        frozen = frozen_rows[position]
        require(trace["position"] == frozen["position"] == position
                and (trace["dataset"], trace["retriever"], trace["sample_id"])
                == (frozen["dataset"], frozen["retriever"], frozen["sample_id"]),
                "SOURCE_BINDING")
        if trace["dataset"] != current_dataset:
            data = loader.restore_dataset(trace["dataset"], native, backend)
            current_dataset = trace["dataset"]
        question = data["questions"][trace["sample_id"]]
        e0 = loader.original_evidence(trace, data, native)
        e1 = reconstruct_e1(native, e0, repair_map[position], data)
        a0, a1 = a0_map[position]["parsed_text"], a1_map[position]["parsed_text"]
        pair_ok, pair_reason = pair_eligibility(a0, a1)
        expected = {
            "dataset": trace["dataset"], "retriever": trace["retriever"],
            "sample_id": trace["sample_id"], "position": position,
            "role": frozen["role"], "pair_eligible": pair_ok,
            "eligible": pair_ok, "forced_keep_reason": pair_reason,
            "F0": None, "F1": None, "gbv_margin": None,
            "e0_premise_count": len(e0), "e1_premise_count": len(e1),
            "e0_chunk_count": 0, "e1_chunk_count": 0,
            "branch_receipt_sha256": {}, "model_id": GBV_MODEL_ID,
            "model_revision": GBV_MODEL_REVISION,
        }
        if not pair_ok:
            forced[pair_reason] = forced.get(pair_reason, 0) + 1
        else:
            pair_eligible_count += 1; payloads = {}
            for state, answer, evidence in (("a0_e0", a0, e0), ("a1_e1", a1, e1)):
                row = branch_rows[branch_index]
                key = f"gbv:{position:05d}:{state}"
                evidence_texts = [item.text for item in evidence]
                input_value = {
                    "dataset": trace["dataset"], "retriever": trace["retriever"],
                    "sample_id": trace["sample_id"], "position": position,
                    "role": frozen["role"], "state": state, "question": question,
                    "answer": answer, "evidence_texts": evidence_texts,
                }
                require(row["sequence"] == branch_index and row["operation_key"] == key
                        and row["operation"] == "gbv_branch"
                        and row["input_sha256"] == object_sha(input_value), "BRANCH_ROW_IDENTITY")
                score, forwards, pairs = validate_branch(
                    row["payload"], trace=trace, role=frozen["role"], state=state,
                    question=question, answer=answer, evidence_texts=evidence_texts,
                    tokenizer=tokenizer, namespace=namespace,
                    entailment_index=entailment_index,
                )
                expected["branch_receipt_sha256"][state] = object_sha(row)
                payloads[state] = row["payload"]; logical_forwards += forwards
                logical_pairs += pairs; branch_index += 1; checks += 28 + pairs
                if row["payload"]["status"] == "unscorable":
                    expected["eligible"] = False
                    expected["forced_keep_reason"] = "nli_unscorable:" + row["payload"]["diagnostic"]
                    forced["nli_unscorable"] = forced.get("nli_unscorable", 0) + 1
                    break
                if state == "a0_e0":
                    expected["F0"] = score
                    expected["e0_chunk_count"] = row["payload"]["chunk_count"]
                else:
                    expected["F1"] = score
                    expected["e1_chunk_count"] = row["payload"]["chunk_count"]
            if expected["eligible"]:
                require(set(payloads) == {"a0_e0", "a1_e1"}, "COMPLETE_BRANCH_PAIR")
                expected["gbv_margin"] = expected["F1"] - expected["F0"]
                scored += 1
        require(gbv_rows[position] == expected, "GBV_ROW_RECONSTRUCTION")
        checks += 24
    require(branch_index == len(branch_rows)
            and receipt["pair_eligible_traces"] == pair_eligible_count
            and receipt["scored_traces"] == scored
            and receipt["forced_keep_counts"] == forced
            and receipt["logical_nli_forwards"] == logical_forwards
            and receipt["logical_nli_pairs"] == logical_pairs
            and sum(receipt["operation_modes"].values()) == len(branch_rows)
            and 0 <= receipt["observed_nli_forwards_current_process"] <= logical_forwards
            and 0 <= receipt["observed_nli_pairs_current_process"] <= logical_pairs,
            "RECEIPT_RECONCILIATION")
    referenced_logits = {
        (namespace / forward["logits"]["path"]).resolve()
        for row in branch_rows
        for forward in row["payload"]["forwards"]
    }
    logits_root = namespace / "logits"
    actual_logits = ({path.resolve() for path in logits_root.rglob("*") if path.is_file()}
                     if logits_root.is_dir() else set())
    require(actual_logits == referenced_logits
            and all(path.suffix == ".f32" for path in actual_logits),
            "EXACT_LOGIT_COVERAGE")
    def current_record(path: Path) -> dict:
        return {
            "path": str(path.resolve()), "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    require(receipt["branch_receipts"] == current_record(namespace / "BRANCH_RECEIPTS.jsonl")
            and receipt["gbv_rows"] == current_record(namespace / "GBV_ROWS.jsonl")
            and receipt["call_journal"] == current_record(namespace / "CALL_JOURNAL.jsonl"),
            "RECEIPT_FILE_BINDINGS")
    require("transformers.models.deberta_v2.modeling_deberta_v2" not in sys.modules,
            "NLI_MODEL_MODULE_LOADED")
    result = {
        "status": "PASS_INDEPENDENT_TOKENIZER_LOGIT_MISTRAL_DEVELOPMENT_GBV",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "branch_receipts_sha256": sha256(namespace / "BRANCH_RECEIPTS.jsonl"),
        "gbv_rows_sha256": sha256(namespace / "GBV_ROWS.jsonl"),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "traces_validated": EXPECTED_TRACES, "branch_operations": len(branch_rows),
        "logical_nli_forwards": logical_forwards, "logical_nli_pairs": logical_pairs,
        "pair_eligible_traces": pair_eligible_count, "scored_traces": scored,
        "forced_keep_counts": forced, "recovery_events": recoveries,
        "tokenizer_loads": 1, "model_loads": 0, "model_forwards": 0,
        "gold_values_read": 0, "scientific_fits": 0, "test_rows_read": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
