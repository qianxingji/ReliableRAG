"""Run/resume frozen Mistral test a1 plus four-cell likelihood acquisition."""
from __future__ import annotations

import argparse
import collections
import gc
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    DurableLedger,
    LIKELIHOOD_CELLS,
    compact_generation_receipt,
    compact_likelihood_receipt,
    read_jsonl,
    record,
    recover_or_execute,
    sha256,
    verify_manifest,
    write_json_durable,
)
from scripts.mistral_reader_input_freeze_common import compact_document
from scripts.run_mistral_test_a0_query import (
    DATASETS,
    EXPECTED_ASSET_MANIFEST_SHA256,
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_INPUT_LEDGER_SHA256,
    EXPECTED_TEST_POOL_MANIFEST_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
    EXPECTED_TEST_TRACE_SHA256,
    acquire_gpu_mutex,
    load_test_assets,
    source_pair,
    validate_asset_manifest,
    validate_selected_manifest,
    validate_test_binding,
)
from scripts.validate_mistral_test_a0_query import validate_manifest
from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal,
    MistralNF4Reader,
    object_sha256,
    require,
    text_sha256,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_A1_GENERATIONS = EXPECTED_TRACES
EXPECTED_LIKELIHOODS = EXPECTED_TRACES * 4
EXPECTED_OPERATIONS = EXPECTED_A1_GENERATIONS + EXPECTED_LIKELIHOODS
MIN_DISK_FREE_BYTES = 30 * 1024 ** 3
MAX_STAGE_SECONDS = 7 * 24 * 60 * 60


def reconstruct_e1(
    e0: list[dict], repair_payload: dict, assets: dict[str, dict[str, dict]],
    dataset: str,
) -> list[dict]:
    inserted_id = repair_payload["inserted_document_id"]
    matches = [
        row for row in repair_payload["ranking"]
        if row["document_id"] == inserted_id
    ]
    require(
        len(matches) == 1
        and matches[0]["rank"] == repair_payload["inserted_candidate_rank"],
        "INSERTED_RANK_BINDING",
    )
    documents = assets[dataset]["documents"]
    require(inserted_id in documents, "INSERTED_DOCUMENT_MEMBERSHIP")
    inserted = compact_document(documents[inserted_id], 5)
    e1 = [*e0[:4], inserted]
    require(
        [row["document_id"] for row in e0] == repair_payload["e0_ids"]
        and [row["document_id"] for row in e1] == repair_payload["e1_ids"]
        and repair_payload["replaced_document_id"] == e0[4]["document_id"]
        and inserted_id not in repair_payload["e0_ids"],
        "REPAIR_EVIDENCE_BINDING",
    )
    return e1


def validate_generation_payload(
    payload: dict, *, trace: dict, question: str, private_e1: list[dict],
) -> None:
    require(
        payload["stage"] == "a1"
        and payload["dataset"] == trace["dataset"]
        and payload["retriever"] == trace["retriever"]
        and payload["sample_id"] == trace["sample_id"]
        and payload["position"] == trace["position"]
        and payload["role"] == "test",
        "A1_IDENTITY",
    )
    require(
        payload["question_sha256"] == object_sha256(question)
        and payload["evidence_sha256"] == object_sha256(private_e1),
        "A1_INPUT_HASHES",
    )
    require(
        payload["input_tokens"] <= 8192
        and payload["output_tokens"] == len(payload["generated_token_ids"])
        == len(payload["chosen_log_probabilities"]),
        "A1_TOKEN_COUNTS",
    )
    require(
        all(math.isfinite(value)
            for value in payload["chosen_log_probabilities"])
        and payload["compact_schema"]
        == "generation-v1-reconstruct-input-from-bound-evidence",
        "A1_VALUES",
    )


def validate_likelihood_payload(
    payload: dict, *, trace: dict, cell: str, question: str,
    evidence: list[dict], answer: str,
) -> None:
    require(
        cell in LIKELIHOOD_CELLS and payload["cell"] == cell,
        "LIKELIHOOD_CELL",
    )
    require(
        payload["dataset"] == trace["dataset"]
        and payload["retriever"] == trace["retriever"]
        and payload["sample_id"] == trace["sample_id"]
        and payload["position"] == trace["position"]
        and payload["role"] == "test",
        "LIKELIHOOD_IDENTITY",
    )
    require(
        payload["question_sha256"] == object_sha256(question)
        and payload["evidence_sha256"] == object_sha256(evidence)
        and payload["answer_sha256"] == text_sha256(answer),
        "LIKELIHOOD_INPUT_HASHES",
    )
    values = payload["chosen_log_probabilities"]
    require(
        payload["target_tokens"] == len(values) > 0
        and payload["total_tokens"]
        == payload["prompt_tokens"] + payload["target_tokens"] <= 8192
        and all(math.isfinite(value) for value in values),
        "LIKELIHOOD_VALUES",
    )
    require(
        payload["mean_log_probability"] == float(sum(values) / len(values))
        and payload["minimum_log_probability"] == float(min(values))
        and payload["compact_schema"]
        == "likelihood-v1-reconstruct-prompt-and-target-from-bound-branch",
        "LIKELIHOOD_SUMMARIES",
    )


def seal(stage_output: Path) -> None:
    files = []
    for path in sorted(stage_output.rglob("*")):
        if path.is_file():
            item = record(path)
            item["path"] = path.relative_to(stage_output).as_posix()
            files.append(item)
    write_json_durable(stage_output / "SHA256_MANIFEST.json", {
        "status": "PASS",
        "files": files,
        "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def validate_prior_gates(root: Path) -> tuple[Path, Path, Path, Path]:
    a0_stage = root / "a0_query"
    repair_stage = root / "repair"
    a0_validation = root / "a0_query_validation/VALIDATION.json"
    repair_validation = root / "repair_validation/VALIDATION.json"
    validate_manifest(a0_stage)
    validate_manifest(repair_stage)
    require(a0_validation.is_file() and repair_validation.is_file(),
            "PRIOR_ACCEPTANCE_REQUIRED")
    a0 = json.loads(a0_validation.read_text(encoding="utf-8"))
    repair = json.loads(repair_validation.read_text(encoding="utf-8"))
    require(
        a0.get("status")
        == "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY"
        and a0.get("producer_receipt_sha256")
        == sha256(a0_stage / "STAGE_RECEIPT.json")
        and a0.get("generation_receipts_sha256")
        == sha256(a0_stage / "GENERATION_RECEIPTS.jsonl")
        and a0.get("call_journal_sha256")
        == sha256(a0_stage / "CALL_JOURNAL.jsonl")
        and a0.get("gold_values_read") == 0
        and a0.get("test_gold_values_read") == 0,
        "A0_VALIDATION_BINDING",
    )
    require(
        repair.get("status")
        == "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_REPAIR"
        and repair.get("producer_receipt_sha256")
        == sha256(repair_stage / "STAGE_RECEIPT.json")
        and repair.get("repair_bindings_sha256")
        == sha256(repair_stage / "REPAIR_BINDINGS.jsonl")
        and repair.get("call_journal_sha256")
        == sha256(repair_stage / "CALL_JOURNAL.jsonl")
        and repair.get("gold_values_read") == 0
        and repair.get("test_gold_values_read") == 0,
        "REPAIR_VALIDATION_BINDING",
    )
    return a0_stage, repair_stage, a0_validation, repair_validation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    original, asset, root = (
        args.project_root.resolve(), args.asset.resolve(),
        args.test_root.resolve(),
    )
    require(
        original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve(),
        "FIXED_ROOTS",
    )
    a0_stage, repair_stage, a0_validation, repair_validation = (
        validate_prior_gates(root)
    )
    stage_output = root / "a1_likelihood"
    require(
        not any((stage_output / name).exists() for name in (
            "STAGE_RECEIPT.json", "STAGE_FAILURE.json",
            "SHA256_MANIFEST.json",
        )),
        "TERMINAL_STAGE_IMMUTABLE",
    )
    require(args.resume or not stage_output.exists(), "STAGE_EXISTS_USE_RESUME")
    require(not args.resume or stage_output.is_dir(), "RESUME_STAGE_MISSING")
    require(
        not subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=REPO, text=True,
        ).strip(),
        "COMMIT_BEFORE_EXECUTION",
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True,
    ).strip()
    started = time.perf_counter()
    reader = journal = ledger = mutex = None
    completed = 0
    modes = collections.Counter()
    result: dict[str, object] = {
        "status": "FAIL",
        "cas_q3_status": "NOT READY",
        "source_commit": commit,
        "stage": "a1_likelihood",
        "project_gold_values_read": 0,
        "test_gold_values_read": 0,
        "scientific_fits": 0,
        "test_input_rows_read": 0,
        "bge_model_loads": 0,
        "nli_model_loads": 0,
        "model_loads": 0,
        "model_unloads": 0,
    }
    try:
        if not args.resume:
            stage_output.mkdir(parents=True, exist_ok=False)
        import psutil
        require(psutil.disk_usage("E:\\").free >= MIN_DISK_FREE_BYTES,
                "DISK_FREE_ADMISSION")
        mutex = acquire_gpu_mutex()

        input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
        frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
        require(
            sha256(input_freeze / "SHA256_MANIFEST.json")
            == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
            and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256,
            "INPUT_FREEZE_PIN",
        )
        preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
        pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
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
            *verify_manifest(
                input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
            ),
            *verify_manifest(
                a0_stage, sha256(a0_stage / "SHA256_MANIFEST.json"),
            ),
            a0_validation,
            *verify_manifest(
                repair_stage, sha256(repair_stage / "SHA256_MANIFEST.json"),
            ),
            repair_validation,
            Path(__file__),
            REPO / "scripts/validate_mistral_test_a1_likelihood.py",
            REPO / "scripts/mistral_development_acquisition_common.py",
            REPO / "scripts/mistral_reader_input_freeze_common.py",
            REPO / "scripts/run_mistral_test_a0_query.py",
            REPO / "scripts/run_mistral_test_repair.py",
            REPO / "scripts/validate_mistral_test_a0_query.py",
            REPO / "src/arbitration/mistral_reader_runtime.py",
            REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md",
            original / "prompts/baseline_v1.txt",
            original / "prompts/repair_missing_v1.txt",
        ]
        records = [
            record(path) for path in sorted(
                {Path(path).resolve() for path in paths}, key=str,
            )
        ]
        asset_records = validate_asset_manifest(asset)
        by_path = {item["path"]: item for item in [*records, *asset_records]}
        require(len(by_path) == len(records) + len(asset_records),
                "UNIQUE_A1_INPUTS")
        input_records = [by_path[path] for path in sorted(by_path)]
        freeze = {
            "status": "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_A1_LIKELIHOOD",
            "source_commit": commit,
            "stage": "a1_likelihood",
            "expected_traces": EXPECTED_TRACES,
            "expected_a1_generations": EXPECTED_A1_GENERATIONS,
            "expected_likelihoods": EXPECTED_LIKELIHOODS,
            "expected_operations": EXPECTED_OPERATIONS,
            "test_gold_access": "FORBIDDEN",
            "inputs": input_records,
            "environment": {key: os.environ.get(key) for key in (
                "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
                "HF_HUB_DISABLE_TELEMETRY", "TOKENIZERS_PARALLELISM",
                "PYTHONHASHSEED", "CUBLAS_WORKSPACE_CONFIG",
            )},
            "host": platform.platform(),
            "python": str(Path(sys.executable).resolve()),
            "scope": (
                "test a1 and L00/L01/L10/L11 only; "
                "BGE/NLI/Gold/fit/tuning forbidden"
            ),
        }
        freeze_path = stage_output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            require(
                json.loads(freeze_path.read_text(encoding="utf-8")) == freeze,
                "RESUME_FREEZE_MISMATCH",
            )
        else:
            write_json_durable(freeze_path, freeze)

        traces = list(read_jsonl(trace_path))
        validate_test_binding(traces, read_jsonl(frozen_ledger))
        assets = load_test_assets(pool_root)
        a0_rows = list(read_jsonl(a0_stage / "GENERATION_RECEIPTS.jsonl"))
        a0_map = {
            row["payload"]["position"]: row["payload"]
            for row in a0_rows if row["operation"] == "a0"
        }
        repair_rows = list(read_jsonl(repair_stage / "REPAIR_BINDINGS.jsonl"))
        repair_map = {
            row["payload"]["position"]: row["payload"]
            for row in repair_rows
        }
        require(len(a0_map) == len(repair_map) == EXPECTED_TRACES,
                "PRIOR_ROW_COUNTS")
        result["test_input_rows_read"] = EXPECTED_TRACES
        journal = DurableOperationJournal(
            stage_output / "CALL_JOURNAL.jsonl", resume=args.resume,
        )
        ledger = DurableLedger(
            stage_output / "MODEL_RECEIPTS.jsonl", resume=args.resume,
        )
        require(len(ledger.rows) <= EXPECTED_OPERATIONS,
                "RESUME_LEDGER_COUNT")
        reader = MistralNF4Reader(
            asset=asset,
            answer_prompt=original / "prompts/baseline_v1.txt",
            repair_prompt=original / "prompts/repair_missing_v1.txt",
        )
        reader.load()
        result["model_loads"] = 1

        for trace in traces:
            position = trace["position"]
            dataset, retriever, sample_id = (
                trace["dataset"], trace["retriever"], trace["sample_id"],
            )
            question, private_e0 = source_pair(trace, assets)
            private_e1 = reconstruct_e1(
                private_e0, repair_map[position], assets, dataset,
            )
            a0 = a0_map[position]["parsed_text"]
            a1_key = f"{position:05d}:a1"
            a1_input = {
                "dataset": dataset,
                "retriever": retriever,
                "sample_id": sample_id,
                "position": position,
                "role": "test",
                "operation": "a1",
                "question": question,
                "evidence": private_e1,
            }

            def execute_a1(
                trace=trace, question=question, private_e1=private_e1,
            ):
                generated = reader.generate(
                    stage="a1", question=question, evidence=private_e1,
                )
                payload = compact_generation_receipt(generated.receipt)
                payload.update({
                    "dataset": trace["dataset"],
                    "retriever": trace["retriever"],
                    "sample_id": trace["sample_id"],
                    "position": trace["position"],
                    "role": "test",
                    "question_sha256": object_sha256(question),
                    "evidence_sha256": object_sha256(private_e1),
                })
                validate_generation_payload(
                    payload, trace=trace, question=question,
                    private_e1=private_e1,
                )
                return payload

            a1_row, mode = recover_or_execute(
                journal=journal,
                ledger=ledger,
                key=a1_key,
                operation="a1",
                input_sha256=object_sha256(a1_input),
                execute=execute_a1,
            )
            validate_generation_payload(
                a1_row["payload"], trace=trace, question=question,
                private_e1=private_e1,
            )
            modes[mode] += 1
            a1 = a1_row["payload"]["parsed_text"]
            branches = {
                "L00": (private_e0, a0),
                "L01": (private_e1, a0),
                "L10": (private_e0, a1),
                "L11": (private_e1, a1),
            }
            for cell in LIKELIHOOD_CELLS:
                evidence, answer = branches[cell]
                key = f"{position:05d}:{cell}"
                input_value = {
                    "dataset": dataset,
                    "retriever": retriever,
                    "sample_id": sample_id,
                    "position": position,
                    "role": "test",
                    "operation": "likelihood",
                    "cell": cell,
                    "question": question,
                    "evidence": evidence,
                    "answer": answer,
                }

                def execute_likelihood(
                    cell=cell, evidence=evidence, answer=answer,
                    trace=trace, question=question,
                ):
                    scored = reader.likelihood(
                        question=question, evidence=evidence, answer=answer,
                    )
                    payload = compact_likelihood_receipt(
                        scored.receipt, cell=cell,
                    )
                    payload.update({
                        "dataset": trace["dataset"],
                        "retriever": trace["retriever"],
                        "sample_id": trace["sample_id"],
                        "position": trace["position"],
                        "role": "test",
                        "question_sha256": object_sha256(question),
                        "evidence_sha256": object_sha256(evidence),
                    })
                    validate_likelihood_payload(
                        payload, trace=trace, cell=cell,
                        question=question, evidence=evidence, answer=answer,
                    )
                    return payload

                row, mode = recover_or_execute(
                    journal=journal,
                    ledger=ledger,
                    key=key,
                    operation="likelihood",
                    input_sha256=object_sha256(input_value),
                    execute=execute_likelihood,
                )
                validate_likelihood_payload(
                    row["payload"], trace=trace, cell=cell,
                    question=question, evidence=evidence, answer=answer,
                )
                modes[mode] += 1
            completed += 1
            if completed % 10 == 0:
                print(json.dumps({
                    "stage": "test_a1_likelihood",
                    "completed_traces": completed,
                    "expected_traces": EXPECTED_TRACES,
                }, sort_keys=True), flush=True)

        require(
            completed == EXPECTED_TRACES
            and len(ledger.rows) == EXPECTED_OPERATIONS,
            "COMPLETE_OPERATION_COUNT",
        )
        require(
            journal.pending is None
            and len(journal.completed) == EXPECTED_OPERATIONS,
            "COMPLETE_JOURNAL_COUNT",
        )
        physical_forwards = reader.model_forward_calls
        reader.close()
        reader = None
        result["model_unloads"] = 1
        import torch
        gc.collect()
        torch.cuda.empty_cache()
        allocated_after = int(torch.cuda.memory_allocated(0))
        require(allocated_after < 1024 ** 3, "MISTRAL_NOT_RELEASED")
        journal.close()
        journal = None
        ledger.close()
        ledger = None
        for item in input_records:
            require(record(item["path"]) == item, "INPUT_CHANGED")
        elapsed = time.perf_counter() - started
        require(elapsed <= MAX_STAGE_SECONDS, "STAGE_WALL_LIMIT")
        result.update({
            "status": "PASS_MISTRAL_TEST_A1_LIKELIHOOD_PENDING_INDEPENDENT",
            "completed_traces": completed,
            "logical_operations": EXPECTED_OPERATIONS,
            "a1_generation_operations": EXPECTED_A1_GENERATIONS,
            "likelihood_operations": EXPECTED_LIKELIHOODS,
            "operation_modes": dict(modes),
            "physical_model_forwards": physical_forwards,
            "cuda_allocated_after_close_bytes": allocated_after,
            "elapsed_seconds": elapsed,
            "model_receipts": record(stage_output / "MODEL_RECEIPTS.jsonl"),
            "call_journal": record(stage_output / "CALL_JOURNAL.jsonl"),
        })
        write_json_durable(stage_output / "STAGE_RECEIPT.json", result)
        seal(stage_output)
        print(result["status"], flush=True)
        return 0
    except Exception as exc:
        result.update({
            "status": "FAIL_MISTRAL_TEST_A1_LIKELIHOOD",
            "error_type": type(exc).__name__,
            "diagnostic": str(exc),
            "traceback": traceback.format_exc(),
            "completed_traces": completed,
            "operation_modes": dict(modes),
            "elapsed_seconds": time.perf_counter() - started,
        })
        if reader is not None:
            try:
                reader.close()
            except Exception:
                pass
        if journal is not None:
            try:
                journal.close()
            except Exception:
                pass
        if ledger is not None:
            try:
                ledger.close()
            except Exception:
                pass
        if (stage_output.is_dir()
                and not (stage_output / "STAGE_FAILURE.json").exists()):
            write_json_durable(stage_output / "STAGE_FAILURE.json", result)
            seal(stage_output)
        print(result["status"], result["diagnostic"], flush=True)
        return 2
    finally:
        if mutex is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(mutex)
            except Exception:
                pass


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
