"""Durable no-model primitives for post-acquisition Mistral development scoring."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any, Iterable

from src.arbitration.mistral_reader_runtime import canonical, require


class DurableStageJournal:
    """Append-only journal whose operation vocabulary is fixed by its caller."""

    def __init__(self, path: str | Path, *, resume: bool,
                 allowed_operations: Iterable[str]) -> None:
        self.path = Path(path)
        self.allowed = frozenset(allowed_operations)
        require(bool(self.allowed) and all(isinstance(value, str) and value for value in self.allowed),
                "STAGE_JOURNAL_ALLOWED_OPERATIONS")
        require(resume or not self.path.exists(), "JOURNAL_EXISTS_WITHOUT_RESUME")
        require(not resume or self.path.is_file(), "RESUME_JOURNAL_MISSING")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, Any]] = []
        if self.path.exists():
            with self.path.open("rb") as handle:
                for raw in handle:
                    require(raw.endswith(b"\n"), "PARTIAL_JOURNAL_LINE")
                    row = json.loads(raw)
                    require(raw == canonical(row) + b"\n", "NONCANONICAL_JOURNAL_ROW")
                    self.rows.append(row)
        self.completed: dict[str, dict[str, Any]] = {}
        self.pending: dict[str, Any] | None = None
        self._validate()
        self.stream = self.path.open("ab")

    def _validate(self) -> None:
        state: dict[str, dict[str, Any]] = {}; active = None
        for sequence, row in enumerate(self.rows):
            require(row.get("sequence") == sequence, "JOURNAL_SEQUENCE")
            event, key = row.get("event"), row.get("operation_key")
            require(isinstance(key, str) and key, "JOURNAL_OPERATION_KEY")
            if event == "intent":
                require(active is None and key not in state, "DUPLICATE_OR_OVERLAPPING_INTENT")
                require(row.get("operation") in self.allowed, "JOURNAL_OPERATION")
                require(re.fullmatch(r"[0-9a-f]{64}", str(row.get("input_sha256", ""))) is not None,
                        "JOURNAL_INPUT_HASH")
                state[key] = {"intent": row, "recoveries": 0}; active = key
            elif event == "resume_pending":
                require(active == key and key in state and "result" not in state[key],
                        "INVALID_PENDING_RESUME")
                require(row.get("operation") == state[key]["intent"]["operation"]
                        and row.get("input_sha256") == state[key]["intent"]["input_sha256"],
                        "RESUME_INPUT")
                state[key]["recoveries"] += 1
            elif event == "result":
                require(active == key and key in state and "result" not in state[key],
                        "INVALID_RESULT")
                require(row.get("operation") == state[key]["intent"]["operation"]
                        and re.fullmatch(r"[0-9a-f]{64}", str(row.get("result_sha256", ""))) is not None,
                        "RESULT_EVENT")
                state[key]["result"] = row; active = None
            else:
                raise RuntimeError("UNKNOWN_JOURNAL_EVENT")
        self.completed = {key: value for key, value in state.items() if "result" in value}
        self.pending = None if active is None else state[active]["intent"]

    def _append(self, row: dict[str, Any]) -> None:
        value = {"sequence": len(self.rows), **row}; raw = canonical(value) + b"\n"
        self.stream.write(raw); self.stream.flush(); os.fsync(self.stream.fileno())
        self.rows.append(value)

    def begin(self, *, operation_key: str, operation: str, input_sha256: str) -> bool:
        require(operation in self.allowed, "UNKNOWN_STAGE_OPERATION")
        require(re.fullmatch(r"[0-9a-f]{64}", input_sha256) is not None, "INVALID_INPUT_HASH")
        if operation_key in self.completed:
            intent = self.completed[operation_key]["intent"]
            require(intent["operation"] == operation and intent["input_sha256"] == input_sha256,
                    "COMPLETED_OPERATION_INPUT_MISMATCH")
            return True
        if self.pending is not None:
            require(self.pending["operation_key"] == operation_key
                    and self.pending["operation"] == operation
                    and self.pending["input_sha256"] == input_sha256, "PENDING_OPERATION_MISMATCH")
            self._append({"event": "resume_pending", "operation_key": operation_key,
                          "operation": operation, "input_sha256": input_sha256})
            return False
        self._append({"event": "intent", "operation_key": operation_key,
                      "operation": operation, "input_sha256": input_sha256})
        self.pending = self.rows[-1]
        return False

    def complete(self, *, operation_key: str, result_sha256: str) -> None:
        require(self.pending is not None and self.pending["operation_key"] == operation_key,
                "RESULT_WITHOUT_MATCHING_INTENT")
        require(re.fullmatch(r"[0-9a-f]{64}", result_sha256) is not None, "INVALID_RESULT_HASH")
        self._append({"event": "result", "operation_key": operation_key,
                      "operation": self.pending["operation"], "result_sha256": result_sha256})
        intent = self.pending
        recoveries = sum(row["event"] == "resume_pending" and row["operation_key"] == operation_key
                         for row in self.rows)
        self.completed[operation_key] = {
            "intent": intent, "result": self.rows[-1], "recoveries": recoveries,
        }
        self.pending = None

    def close(self) -> None:
        if not self.stream.closed: self.stream.close()


def write_bytes_once(path: str | Path, raw: bytes) -> None:
    """Durably create bytes or prove a crash orphan is bit-identical."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == raw, "EXISTING_DURABLE_BYTES_MISMATCH")
        return
    with path.open("xb") as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
