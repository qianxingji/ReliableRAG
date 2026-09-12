"""Runtime guard and durable-ledger primitives for Phi development generation."""
from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.phi_reader_input_freeze_common import canonical, require, require_generation_admission


class GuardedGenerationTokenizer:
    """Observe the exact native generation tensor batch and fail before CUDA."""

    def __init__(self, tokenizer, phase: dict, admissions: list[dict]):
        self._tokenizer = tokenizer
        self._phase = phase
        self._admissions = admissions

    def __getattr__(self, name):
        return getattr(self._tokenizer, name)

    def __call__(self, *args, **kwargs):
        value = self._tokenizer(*args, **kwargs)
        if kwargs.get("return_tensors") == "pt" and self._phase.get("stage") in {"a0", "repair_query", "a1"}:
            width = require_generation_admission(stage=self._phase["stage"], input_ids=value["input_ids"],
                attention_mask=value["attention_mask"])
            self._admissions.append({"stage": self._phase["stage"], "position": self._phase.get("position"), "input_tokens": width})
        return value


class DurableJsonl:
    """Append canonical rows durably while retaining an exact validated prefix."""

    def __init__(self, path: Path, *, resume: bool):
        self.path = Path(path); self.rows = []
        if self.path.exists():
            require(resume, f"existing journal requires resume: {self.path.name}")
            with self.path.open("rb") as stream:
                for raw in stream:
                    require(raw.endswith(b"\n"), f"partial journal line: {self.path.name}")
                    row = json.loads(raw)
                    require(raw == canonical(row) + b"\n", f"noncanonical journal row: {self.path.name}")
                    self.rows.append(row)
        else:
            require(not resume, f"resume journal missing: {self.path.name}")
        self.stream = self.path.open("ab" if resume else "xb")

    def append(self, row: dict) -> None:
        payload = canonical(row) + b"\n"
        self.stream.write(payload); self.stream.flush(); os.fsync(self.stream.fileno()); self.rows.append(row)

    def close(self) -> None:
        if not self.stream.closed:
            self.stream.close()


def validate_resume_prefix(traces: list[dict], ledgers: dict[str, list[dict]]) -> tuple[int, dict | None]:
    """Require complete trace transactions except possibly the final trace."""
    by_name = {name: {} for name in ledgers}
    for name, rows in ledgers.items():
        for row in rows:
            key = (row["dataset"], row["retriever"], row["sample_id"])
            if name == "generation_receipts":
                key = (*key, row["stage"])
            require(key not in by_name[name], f"duplicate {name} row")
            by_name[name][key] = row
    completed = 0; partial = None
    for index, trace in enumerate(traces):
        key = (trace["dataset"], trace["retriever"], trace["sample_id"])
        present = {
            "a0": (*key, "a0") in by_name["generation_receipts"],
            "repair_query": (*key, "repair_query") in by_name["generation_receipts"],
            "repair": key in by_name["repair_bindings"],
            "a1": (*key, "a1") in by_name["generation_receipts"],
            "branch": key in by_name["canonical_branches"],
            "provenance": key in by_name["branch_provenance"],
        }
        order = [present[name] for name in ("a0", "repair_query", "repair", "a1", "branch", "provenance")]
        require(order == sorted(order, reverse=True), "resume stage prefix order")
        if all(order):
            require(partial is None, "completed trace after partial prefix"); completed += 1; continue
        if any(order):
            require(partial is None, "multiple partial trace prefixes"); partial = {"index": index, "key": key, "present": present}
        else:
            require(partial is None or partial["index"] == index - 1, "gap after partial trace")
            break
    expected_counts = {
        "generation_receipts": completed * 3 + (0 if partial is None else sum(partial["present"][s] for s in ("a0", "repair_query", "a1"))),
        "repair_bindings": completed + (0 if partial is None else int(partial["present"]["repair"])),
        "canonical_branches": completed + (0 if partial is None else int(partial["present"]["branch"])),
        "branch_provenance": completed + (0 if partial is None else int(partial["present"]["provenance"])),
    }
    for name, count in expected_counts.items(): require(len(ledgers[name]) == count, f"resume {name} count")
    return completed, partial
