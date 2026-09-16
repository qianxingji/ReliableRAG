"""No-model durable primitives for Mistral development acquisition."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Iterable

from src.arbitration.mistral_reader_runtime import (
    DurableOperationJournal,
    canonical,
    frozen_witness_positions,
    object_sha256,
    require,
)


STAGES = ("a0_query", "repair", "a1_likelihood", "witness_replay")
GENERATION_STAGES = frozenset({"a0", "repair_query", "a1"})
LIKELIHOOD_CELLS = ("L00", "L01", "L10", "L11")


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def record(path: str | Path) -> dict[str, object]:
    path = Path(path).resolve()
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def read_jsonl(path: str | Path):
    with Path(path).open("rb") as handle:
        for raw in handle:
            require(raw.endswith(b"\n"), "PARTIAL_JSONL:" + str(path))
            row = json.loads(raw)
            require(raw == canonical(row) + b"\n", "NONCANONICAL_JSONL:" + str(path))
            yield row


def write_json_durable(path: str | Path, value: object) -> None:
    path = Path(path)
    require(not path.exists(), "REFUSE_OVERWRITE:" + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


class DurableLedger:
    """Canonical append-only rows indexed by a unique operation key."""

    def __init__(self, path: str | Path, *, resume: bool) -> None:
        self.path = Path(path)
        require(resume or not self.path.exists(), "LEDGER_EXISTS_WITHOUT_RESUME")
        require(not resume or self.path.is_file(), "RESUME_LEDGER_MISSING")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, Any]] = list(read_jsonl(self.path)) if self.path.exists() else []
        self.by_key: dict[str, dict[str, Any]] = {}
        for sequence, row in enumerate(self.rows):
            require(row.get("sequence") == sequence, "LEDGER_SEQUENCE")
            key = row.get("operation_key")
            require(isinstance(key, str) and key and key not in self.by_key, "LEDGER_OPERATION_KEY")
            self.by_key[key] = row
        self.stream = self.path.open("ab")

    def append(self, row: dict[str, Any]) -> dict[str, Any]:
        key = row.get("operation_key")
        require(isinstance(key, str) and key and key not in self.by_key, "DUPLICATE_LEDGER_KEY")
        value = {"sequence": len(self.rows), **row}
        raw = canonical(value) + b"\n"
        self.stream.write(raw); self.stream.flush(); os.fsync(self.stream.fileno())
        self.rows.append(value); self.by_key[key] = value
        return value

    def close(self) -> None:
        if not self.stream.closed:
            self.stream.close()


def operation_key(position: int, operation: str) -> str:
    require(position >= 0, "NEGATIVE_POSITION")
    require(operation in GENERATION_STAGES or operation in LIKELIHOOD_CELLS
            or operation == "repair_retrieval", "UNKNOWN_OPERATION")
    return f"{position:05d}:{operation}"


def recover_or_execute(
    *,
    journal: DurableOperationJournal,
    ledger: DurableLedger,
    key: str,
    operation: str,
    input_sha256: str,
    execute: Callable[[], dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    """Return a durable row while never regenerating a completed operation.

    If an operation receipt reached the ledger but its journal result did not,
    recovery completes the journal from that durable row.  If only the intent
    exists, the exact deterministic call is reissued and recorded by the
    journal's ``resume_pending`` event.
    """

    saved = ledger.by_key.get(key)
    completed = journal.completed.get(key)
    pending = journal.pending
    if saved is not None:
        require(saved.get("operation") == operation and saved.get("input_sha256") == input_sha256,
                "SAVED_OPERATION_INPUT_MISMATCH")
        saved_sha = object_sha256(saved)
        if completed is not None:
            require(completed["intent"]["operation"] == operation
                    and completed["intent"]["input_sha256"] == input_sha256,
                    "COMPLETED_JOURNAL_INPUT_MISMATCH")
            require(completed["result"]["result_sha256"] == saved_sha, "COMPLETED_RESULT_HASH")
            return saved, "skipped_completed"
        require(pending is not None and pending["operation_key"] == key
                and pending["operation"] == operation and pending["input_sha256"] == input_sha256,
                "LEDGER_ROW_WITHOUT_MATCHING_PENDING_INTENT")
        journal.complete(operation_key=key, result_sha256=saved_sha)
        return saved, "completed_from_durable_row"
    require(completed is None, "COMPLETED_JOURNAL_WITHOUT_LEDGER_ROW")
    skipped = journal.begin(operation_key=key, operation=operation, input_sha256=input_sha256)
    require(not skipped, "UNEXPECTED_COMPLETED_SKIP")
    payload = execute()
    require(isinstance(payload, dict), "EXECUTION_RESULT_NOT_OBJECT")
    durable = ledger.append({
        "operation_key": key, "operation": operation,
        "input_sha256": input_sha256, "payload": payload,
    })
    journal.complete(operation_key=key, result_sha256=object_sha256(durable))
    return durable, "executed" if pending is None else "reissued_pending"


def compact_generation_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Drop reconstructable prompt arrays while retaining exact hashes/counts."""

    require(receipt.get("stage") in GENERATION_STAGES, "GENERATION_STAGE")
    required = {
        "input_token_ids", "attention_mask", "input_token_ids_sha256",
        "input_tokens", "generated_token_ids", "chosen_log_probabilities",
    }
    require(required <= set(receipt), "GENERATION_RECEIPT_FIELDS")
    require(len(receipt["input_token_ids"]) == len(receipt["attention_mask"]) == receipt["input_tokens"],
            "GENERATION_INPUT_LENGTH")
    require(receipt["attention_mask"] == [1] * receipt["input_tokens"], "GENERATION_MASK")
    result = dict(receipt)
    result.pop("input_token_ids"); result.pop("attention_mask")
    result["compact_schema"] = "generation-v1-reconstruct-input-from-bound-evidence"
    return result


def compact_likelihood_receipt(receipt: dict[str, Any], *, cell: str) -> dict[str, Any]:
    require(cell in LIKELIHOOD_CELLS, "LIKELIHOOD_CELL")
    required = {
        "prompt_token_ids", "target_token_ids", "prompt_token_ids_sha256",
        "target_token_ids_sha256", "prompt_tokens", "target_tokens",
        "chosen_log_probabilities", "mean_log_probability", "minimum_log_probability",
    }
    require(required <= set(receipt), "LIKELIHOOD_RECEIPT_FIELDS")
    require(len(receipt["prompt_token_ids"]) == receipt["prompt_tokens"]
            and len(receipt["target_token_ids"]) == receipt["target_tokens"], "LIKELIHOOD_TOKEN_COUNTS")
    require(len(receipt["chosen_log_probabilities"]) == receipt["target_tokens"], "LIKELIHOOD_VALUE_COUNT")
    result = dict(receipt)
    result.pop("prompt_token_ids"); result.pop("target_token_ids")
    result["cell"] = cell
    result["compact_schema"] = "likelihood-v1-reconstruct-prompt-and-target-from-bound-branch"
    return result


def validate_development_binding(traces: list[dict], frozen_rows: Iterable[dict]) -> list[dict]:
    development = [row for row in frozen_rows if row.get("cohort") == "development"]
    require(len(traces) == len(development) == 13_500, "DEVELOPMENT_TRACE_COUNT")
    for position, (trace, frozen) in enumerate(zip(traces, development, strict=True)):
        require(trace["position"] == frozen["position"] == position, "DEVELOPMENT_POSITION")
        require((trace["dataset"], trace["retriever"], trace["sample_id"])
                == (frozen["dataset"], frozen["retriever"], frozen["sample_id"]),
                "DEVELOPMENT_IDENTITY")
        require(frozen.get("role") in {"fit", "cal"}, "DEVELOPMENT_ROLE")
        require(object_sha256(trace["original_top5_ids"]) == frozen["original_top5_ids_sha256"],
                "ORIGINAL_TOP5_BINDING")
    require(frozen_witness_positions(development) == sorted(frozen_witness_positions(development)),
            "WITNESS_POSITION_ORDER")
    return development


def expected_counts(trace_count: int = 13_500) -> dict[str, int]:
    require(trace_count > 0, "TRACE_COUNT")
    return {
        "a0_query_operations": trace_count * 2,
        "repair_operations": trace_count,
        "a1_likelihood_operations": trace_count * 5,
        "generation_calls": trace_count * 3,
        "likelihood_calls": trace_count * 4,
        "total_model_operations": trace_count * 7,
        "total_canonical_operations": trace_count * 8,
        "witness_replay_model_operations": 18 * 7,
    }


def verify_manifest(namespace: str | Path, expected_sha256: str) -> list[Path]:
    namespace = Path(namespace).resolve(); manifest = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest) == expected_sha256, "MANIFEST_PIN")
    value = json.loads(manifest.read_text(encoding="utf-8"))
    paths, seen = [], set()
    for item in value["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in seen, "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "MANIFEST_MEMBER")
        paths.append(path); seen.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == seen | {manifest}, "MANIFEST_EXACT_COVERAGE")
    return paths + [manifest]
