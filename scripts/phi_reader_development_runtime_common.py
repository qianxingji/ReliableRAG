"""Runtime guard and durable-ledger primitives for Phi development generation."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re

from scripts.phi_reader_input_freeze_common import canonical, digest, load, record, require, require_generation_admission, text_sha


def verify_manifest_members(*, namespace: Path, manifest_path: Path, expected_manifest_sha256: str,
                            record_base: Path | None = None, allow_only_extra_pycache: bool = False) -> list[Path]:
    """Return only authenticated manifest members, never discovered extras."""
    namespace, manifest_path = Path(namespace).resolve(), Path(manifest_path).resolve()
    require(manifest_path.parent == namespace and digest(manifest_path) == expected_manifest_sha256, "sealed manifest pin")
    manifest = load(manifest_path); rows_ = manifest["files"]
    members, seen = [], set()
    for row in rows_:
        relative = Path(row["path"])
        path = ((Path(record_base).resolve() / relative) if record_base is not None else (namespace / relative)).resolve()
        require(path.is_relative_to(namespace) and path not in seen, "sealed manifest member path")
        require(record(path)["size_bytes"] == row["size_bytes"] and digest(path) == row["sha256"], "sealed manifest member hash")
        seen.add(path); members.append(path)
    expected = seen | {manifest_path}
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    extras = actual - expected
    if allow_only_extra_pycache:
        require(all("__pycache__" in path.relative_to(namespace).parts and path.suffix == ".pyc" for path in extras),
                "unsealed non-pycache namespace member")
    else:
        require(not extras and actual == expected, "exact sealed namespace coverage")
    require(expected <= actual, "sealed namespace member missing")
    return [manifest_path, *members]


def verify_recorded_tree(root: Path, records: list[dict]) -> list[Path]:
    """Require an accepted record set to be the exact current file tree."""
    root = Path(root).resolve(); expected = {Path(row["path"]).resolve() for row in records}
    actual = {path.resolve() for path in root.rglob("*") if path.is_file()}
    require(actual == expected, "accepted recorded tree members")
    by_path = {Path(row["path"]).resolve(): row for row in records}
    for path in sorted(expected):
        row = by_path[path]
        require(record(path) == {"path": str(path), "size_bytes": row["size_bytes"], "sha256": row["sha256"]},
                "accepted recorded tree hash")
    return sorted(expected)


def verify_selected_manifest_members(*, namespace: Path, manifest_path: Path, expected_manifest_sha256: str,
                                     record_base: Path, required_paths: list[Path]) -> list[Path]:
    """Verify only named safe members of a larger sealed private namespace."""
    namespace, manifest_path, record_base = Path(namespace).resolve(), Path(manifest_path).resolve(), Path(record_base).resolve()
    require(manifest_path.parent == namespace and digest(manifest_path) == expected_manifest_sha256,
            "selected-member manifest pin")
    manifest = load(manifest_path); by_path = {}
    for row in manifest["files"]:
        path = (record_base / row["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in by_path, "selected-member manifest path duplicate")
        by_path[path] = row
    required = {Path(path).resolve() for path in required_paths}
    require(len(required) == len(required_paths) and required <= set(by_path), "selected runtime member missing from manifest")
    for path in sorted(required):
        row = by_path[path]
        require(path.stat().st_size == row["size_bytes"] and digest(path) == row["sha256"],
                "selected runtime member hash")
    return [manifest_path, *sorted(required)]


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
        if kwargs.get("return_tensors") == "pt":
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("ab" if self.path.exists() else "xb")

    def append(self, row: dict) -> None:
        payload = canonical(row) + b"\n"
        self.stream.write(payload); self.stream.flush(); os.fsync(self.stream.fileno()); self.rows.append(row)

    def close(self) -> None:
        if not self.stream.closed:
            self.stream.close()


class DurableCallEvents:
    """Write-ahead intents for every non-repeatable model or retrieval call.

    An intent is durable before the call starts.  Its completion is durable only
    after the corresponding scientific ledger row.  Consequently an unpaired
    intent is an ambiguous call outcome and resume must stop rather than repeat
    the call.
    """

    def __init__(self, path: Path, *, resume: bool):
        self.ledger = DurableJsonl(path, resume=resume)
        try:
            self.completed = self._validate(self.ledger.rows)
        except Exception:
            self.ledger.close()
            raise

    @staticmethod
    def _validate(rows: list[dict]) -> dict[str, dict]:
        completed: dict[str, dict] = {}
        require(len(rows) % 2 == 0, "unpaired durable call intent; resume forbidden")
        for index in range(0, len(rows), 2):
            intent, completion = rows[index:index + 2]
            require(intent.get("event") == "intent" and completion.get("event") == "completion",
                    "call event intent/completion order")
            event_id = intent.get("event_id")
            require(type(event_id) is str and event_id and completion.get("event_id") == event_id,
                    "call event identity")
            require(event_id not in completed, "duplicate completed call event")
            require(intent.get("operation") in {"a0", "repair_query", "repair_retrieval", "a1"},
                    "unknown call operation")
            require(completion.get("operation") == intent["operation"], "call operation completion mismatch")
            require(re.fullmatch(r"[0-9a-f]{64}", str(completion.get("ledger_row_sha256", ""))) is not None,
                    "call completion ledger hash")
            completed[event_id] = {"intent": intent, "completion": completion}
        return completed

    @property
    def rows(self) -> list[dict]:
        return self.ledger.rows

    def intent(self, row: dict) -> None:
        require(len(self.ledger.rows) % 2 == 0, "previous call intent remains unpaired")
        require(row.get("event") == "intent", "durable call intent schema")
        self.ledger.append(row)

    def completion(self, row: dict) -> None:
        require(len(self.ledger.rows) % 2 == 1, "call completion without intent")
        intent = self.ledger.rows[-1]
        require(row.get("event") == "completion" and row.get("event_id") == intent.get("event_id") and
                row.get("operation") == intent.get("operation"), "durable call completion schema")
        self.ledger.append(row)
        self.completed = self._validate(self.ledger.rows)

    def close(self) -> None:
        self.ledger.close()


def event_id(trace: dict, operation: str) -> str:
    require(operation in {"a0", "repair_query", "repair_retrieval", "a1"}, "unknown call operation")
    return f"{int(trace['position']):05d}:{trace['dataset']}:{trace['retriever']}:{trace['sample_id']}:{operation}"


def validate_call_events(events: list[dict], ledgers: dict[str, list[dict]]) -> None:
    """Bind every completed non-repeatable call to exactly one main-ledger row."""
    completed = DurableCallEvents._validate(events)
    expected: dict[str, tuple[str, dict]] = {}
    for row in ledgers["generation_receipts"]:
        expected[event_id(row, row["stage"])] = ("generation_receipts", row)
    for row in ledgers["repair_bindings"]:
        expected[event_id(row, "repair_retrieval")] = ("repair_bindings", row)
    require(set(completed) == set(expected), "call events differ from scientific call ledgers")
    for identifier, (ledger_name, row) in expected.items():
        pair = completed[identifier]
        intent = pair["intent"]
        require(all(intent.get(field) == row[field] for field in ("dataset", "retriever", "sample_id", "position")),
                "call intent trace binding")
        require(intent.get("operation") == (row["stage"] if ledger_name == "generation_receipts" else "repair_retrieval"),
                "call intent operation binding")
        if ledger_name == "generation_receipts":
            require(all(re.fullmatch(r"[0-9a-f]{64}", str(row.get(field, ""))) is not None and
                        intent.get(field) == row[field] for field in ("runtime_config_sha256", "question_sha256", "evidence_sha256")),
                    "generation call intent input binding")
        else:
            require(intent.get("runtime_config_sha256") == row.get("runtime_config_sha256") and
                    intent.get("query_sha256") == row.get("query_sha256") and
                    intent.get("requested_depth") == row.get("requested_depth") == 50,
                    "repair call intent input binding")
        require(pair["completion"].get("ledger") == ledger_name, "call completion ledger name")
        require(pair["completion"]["ledger_row_sha256"] == object_sha(row), "call completion row hash")
    actual_order = [events[index]["event_id"] for index in range(0, len(events), 2)]
    generation = ledgers["generation_receipts"]
    repairs = {(row["dataset"], row["retriever"], row["sample_id"]): row for row in ledgers["repair_bindings"]}
    trace_order = []; seen = set()
    for row in generation:
        key = (row["dataset"], row["retriever"], row["sample_id"])
        if key not in seen:
            seen.add(key); trace_order.append(key)
    generation_map = {(row["dataset"], row["retriever"], row["sample_id"], row["stage"]): row for row in generation}
    expected_order = []
    for key in trace_order:
        for operation in ("a0", "repair_query"):
            row = generation_map.get((*key, operation))
            if row is not None: expected_order.append(event_id(row, operation))
        if key in repairs: expected_order.append(event_id(repairs[key], "repair_retrieval"))
        row = generation_map.get((*key, "a1"))
        if row is not None: expected_order.append(event_id(row, "a1"))
    require(actual_order == expected_order, "durable call event order")


def validate_output_name(name: str) -> str:
    require(type(name) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", name) is not None,
            "output-name must be one safe directory component")
    require(name not in {".", ".."}, "unsafe output-name")
    return name


def object_sha(value: object) -> str:
    import hashlib
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_trace_input_binding(traces: list[dict], frozen_rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    """Bind the old 13,500 trace order to the accepted value-blind Phi freeze."""
    development = [row for row in frozen_rows if row.get("cohort") == "development"]
    require(len(traces) == len(development) == 13_500, "development trace/input count")
    index = {}
    for expected_position, (trace, frozen) in enumerate(zip(traces, development, strict=True)):
        trace_key = (trace["dataset"], trace["retriever"], trace["sample_id"])
        frozen_key = (frozen["dataset"], frozen["retriever"], frozen["sample_id"])
        require(trace_key == frozen_key and trace["position"] == frozen["position"] == expected_position,
                "development trace order differs from accepted input freeze")
        require(object_sha(trace["original_top5_ids"]) == frozen["original_top5_ids_sha256"],
                "development original Top-5 differs from accepted input freeze")
        require(frozen.get("role") in {"fit", "cal"}, "development role")
        require(trace_key not in index, "duplicate development trace")
        index[trace_key] = frozen
    return index


def validate_frozen_generation_capture(capture: dict, frozen: dict, stage: str, admitted_tokens: int) -> None:
    require(stage in {"a0", "repair_query"}, "only deterministic original-evidence stages are frozen")
    witness = frozen["answer" if stage == "a0" else "repair_query"]
    require(capture["prompt_sha256"] == witness["prompt_sha256"], "frozen prompt hash mismatch")
    require(capture["input_tokens"] == witness["input_tokens"] == admitted_tokens,
            "frozen/admitted/native input length mismatch")
    require(object_sha(capture["input_token_ids"]) == witness["input_token_ids_sha256"],
            "frozen input token IDs mismatch")
    render = capture["render"]
    require(render["context_truncated"] == witness["context_truncated"] and
            list(render["per_document_truncated"]) == witness["per_document_truncated"],
            "frozen render metadata mismatch")


def validate_generation_receipt(row: dict, runtime_config_sha256: str) -> None:
    stage = row.get("stage")
    require(stage in {"a0", "repair_query", "a1"} and row.get("reader") == "phi", "Phi generation receipt identity")
    limit = 64 if stage == "repair_query" else 48
    ids, mask, generated = row["input_token_ids"], row["attention_mask"], row["generated_token_ids"]
    require(type(ids) is list and type(mask) is list and len(ids) == len(mask) == row["input_tokens"] == row["guard_input_tokens"],
            "generation receipt input/guard lengths")
    require(0 < len(ids) <= 9_472 and mask == [1] * len(ids), "generation receipt pre-CUDA admission")
    require(type(generated) is list and len(generated) == row["native_output_score_steps"] and
            0 <= row["output_tokens"] <= len(generated) <= limit, "generation receipt output bounds")
    require(row["logical_generation_calls"] == 1 and type(row["phi_forward_calls"]) is int and row["phi_forward_calls"] > 0,
            "generation receipt call counters")
    require(row["runtime_config_sha256"] == runtime_config_sha256 and
            all(re.fullmatch(r"[0-9a-f]{64}", row[field]) is not None
                for field in ("prompt_sha256", "question_sha256", "evidence_sha256")),
            "generation receipt config/prompt/input hashes")
    require(type(row["raw_text"]) is str and type(row["parsed_text"]) is str and
            ((stage == "repair_query") == (type(row["parser_fallback"]) is bool)), "generation receipt parser schema")
    render = row["render"]
    require(render["context_budget_characters"] == 16_000 and len(render["ordered_passed_document_ids"]) == 5 and
            len(set(render["ordered_passed_document_ids"])) == 5 and len(render["per_document_truncated"]) == 5 and
            render["context_truncated"] is any(render["per_document_truncated"]), "generation receipt render schema")


def validate_repair_receipt(row: dict, trace: dict) -> None:
    require(row["position"] == trace["position"] and row["requested_depth"] == 50 and row["repair_retrieval_calls"] == 1 and
            row["replacement_position_zero_based"] == 4 and row["fail_closed_reason"] is None,
            "repair receipt fixed controls")
    ranking = row["ranking"]
    require(len(ranking) == 50 and [item["rank"] for item in ranking] == list(range(1, 51)) and
            len({item["document_id"] for item in ranking}) == 50, "repair depth/rank/uniqueness")
    require(row["e0_ids"] == trace["original_top5_ids"] and len(set(row["e0_ids"])) == 5 and
            row["e1_ids"][:4] == row["e0_ids"][:4] and row["e1_ids"][4] == row["inserted_document_id"] and
            row["replaced_document_id"] == row["e0_ids"][4] and row["inserted_document_id"] not in row["e0_ids"],
            "repair rank-5 replacement")
    inserted = next((item for item in ranking if item["document_id"] == row["inserted_document_id"]), None)
    require(inserted is not None and inserted["rank"] == row["inserted_candidate_rank"], "repair inserted candidate binding")
    expected_components = {"bm25", "dense"} if row["retriever"] == "hybrid" else {row["retriever"]}
    require(set(row["component_rankings"]) == expected_components, "repair same-retriever components")
    require((row["dense_query_vector"] is None) == (row["retriever"] == "bm25") and
            (row["dense_query_vector"] is None or len(row["dense_query_vector"]) == 768), "repair BGE query vector schema")


def validate_completed_trace_rows(traces: list[dict], ledgers: dict[str, list[dict]], runtime_config_sha256: str) -> None:
    """Cross-bind every fully materialized four-ledger trace without a model."""
    trace_map = {(row["dataset"], row["retriever"], row["sample_id"]): row for row in traces}
    generations = {(row["dataset"], row["retriever"], row["sample_id"], row["stage"]): row
                   for row in ledgers["generation_receipts"]}
    repairs = {(row["dataset"], row["retriever"], row["sample_id"]): row for row in ledgers["repair_bindings"]}
    provenances = {(row["dataset"], row["retriever"], row["sample_id"]): row for row in ledgers["branch_provenance"]}
    branches = {(row["dataset"], row["retriever"], row["sample_id"]): row for row in ledgers["canonical_branches"]}
    for key in set(provenances) & set(branches):
        trace, repair, provenance, branch = trace_map[key], repairs[key], provenances[key], branches[key]
        stage_rows = {stage: generations[(*key, stage)] for stage in ("a0", "repair_query", "a1")}
        require(set(branch) == {"dataset", "retriever", "sample_id", "question", "a0", "a1", "evidence0", "evidence1"},
                "completed canonical branch schema")
        validate_repair_receipt(repair, trace)
        for row in stage_rows.values(): validate_generation_receipt(row, runtime_config_sha256)
        require(all(row["position"] == trace["position"] and row["runtime_config_sha256"] == runtime_config_sha256
                    for row in stage_rows.values()), "completed generation trace/config binding")
        require(repair["position"] == provenance["position"] == trace["position"], "completed trace position binding")
        require(provenance["runtime_config_sha256"] == runtime_config_sha256 and
                repair["runtime_config_sha256"] == runtime_config_sha256 and
                provenance["original_top5_row_sha256"] == trace["original_top5_row_sha256"],
                "completed provenance runtime/input binding")
        require(provenance["canonical_row_sha256"] == object_sha(branch) and
                provenance["repair_binding_row_sha256"] == object_sha(repair), "completed row hash binding")
        e0_ids = [row["document_id"] for row in provenance["e0"]]
        e1_ids = [row["document_id"] for row in provenance["e1"]]
        require(e0_ids == trace["original_top5_ids"] == repair["e0_ids"] and e1_ids == repair["e1_ids"],
                "completed evidence identity binding")
        require([row["text"] for row in provenance["e0"]] == branch["evidence0"] and
                [row["text"] for row in provenance["e1"]] == branch["evidence1"], "completed evidence text binding")
        require(stage_rows["a0"]["parsed_text"] == branch["a0"] and stage_rows["a1"]["parsed_text"] == branch["a1"] and
                text_sha(stage_rows["repair_query"]["parsed_text"]) == repair["query_sha256"],
                "completed generation/branch/repair binding")
        require(provenance["question_sha256"] == text_sha(branch["question"]), "completed question hash binding")
        require(all(row["question_sha256"] == provenance["question_sha256"] for row in stage_rows.values()) and
                stage_rows["a0"]["evidence_sha256"] == stage_rows["repair_query"]["evidence_sha256"] == object_sha(provenance["e0"]) and
                stage_rows["a1"]["evidence_sha256"] == object_sha(provenance["e1"]),
                "completed call input witness binding")
        require(list(stage_rows["a0"]["render"]["ordered_passed_document_ids"]) == e0_ids and
                list(stage_rows["repair_query"]["render"]["ordered_passed_document_ids"]) == e0_ids and
                list(stage_rows["a1"]["render"]["ordered_passed_document_ids"]) == e1_ids,
                "completed prompt evidence binding")


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
        # The authenticated runtime durably writes provenance before its public
        # canonical branch row.
        order = [present[name] for name in ("a0", "repair_query", "repair", "a1", "provenance", "branch")]
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
