"""Independently validate sealed Phi development canonical and replay outputs.

This module intentionally imports none of the producer/runtime helper modules.
"""
from __future__ import annotations

import argparse
import collections
from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import traceback


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q2"
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
STAGES = ("a0", "repair_query", "a1")
LEDGERS = {
    "generation_receipts": "generation_receipts.jsonl",
    "repair_bindings": "repair_bindings.jsonl",
    "branch_provenance": "branch_provenance.jsonl",
    "canonical_branches": "canonical_branches.jsonl",
}
PHI_REVISION = "2fe192450127e6a83f7441aef6e3ca586c338b77"
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
INPUT_FREEZE_MANIFEST_SHA256 = "17cb0c29e4d4a5b98991bbebf1368bdff0ebece6221ca163c73327bcf4bcedd9"
JOINT_PREFLIGHT_MANIFEST_SHA256 = "ecf17a8af6c21fe2887700993bafe53c4aa8ae3c5419112737049db5c91ef2bf"
VALIDATION_CORRIGENDUM_PATH = REPO / "docs/cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_VALIDATION_V4_FAILURE_CORRIGENDUM.md"
WEIGHT_SUFFIXES = {".safetensors", ".bin", ".pt", ".pth", ".ckpt"}
HEX64 = re.compile(r"[0-9a-f]{64}")
COMMIT_HEX40 = re.compile(r"[0-9a-f]{40}")
EXPECTED_RUNTIME_AUDIT_BOUNDARY_START = (
    "after authenticated source records, framework imports/configuration, authenticated native assembly, and cached platform probe; "
    "before CUDA device query, model loads, and runtime trace/dataset semantic reads"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def object_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def record(path: Path) -> dict:
    path = Path(path).resolve()
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest(path)}


def load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def safe_name(name: str) -> str:
    require(type(name) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", name) is not None,
            "namespace name must be one safe directory component")
    require(name not in {".", ".."}, "unsafe namespace name")
    return name


def read_canonical_jsonl(path: Path) -> tuple[list[dict], list[bytes]]:
    result, raw_rows = [], []
    with Path(path).open("rb") as stream:
        for raw in stream:
            require(raw.endswith(b"\n"), f"partial JSONL row: {path.name}")
            row = json.loads(raw)
            require(raw == canonical(row) + b"\n", f"noncanonical JSONL row: {path.name}")
            require(type(row) is dict, f"non-object JSONL row: {path.name}")
            result.append(row); raw_rows.append(raw)
    return result, raw_rows


class CanonicalJsonlStream:
    """Strict one-row lookahead reader; parsed rows are never retained here."""

    def __init__(self, path: Path):
        self.path = Path(path); self.stream = None; self.rows = 0; self.bytes = 0

    def __enter__(self):
        self.stream = self.path.open("rb"); return self

    def __exit__(self, *_args):
        if self.stream is not None: self.stream.close()

    def pop(self) -> tuple[dict, bytes]:
        require(self.stream is not None, "JSONL stream is not open")
        raw = self.stream.readline(); require(raw != b"", f"early JSONL EOF: {self.path.name}")
        require(raw.endswith(b"\n"), f"partial JSONL row: {self.path.name}")
        row = json.loads(raw); require(type(row) is dict and raw == canonical(row) + b"\n",
                                      f"noncanonical JSONL row: {self.path.name}")
        self.rows += 1; self.bytes += len(raw)
        return row, raw

    def finish(self) -> None:
        require(self.stream is not None and self.stream.readline() == b"", f"trailing JSONL row: {self.path.name}")


def verify_exact_seal(namespace: Path) -> tuple[dict, list[Path]]:
    namespace = Path(namespace).resolve(); manifest_path = namespace / "SHA256_MANIFEST.json"
    require(namespace.is_dir() and manifest_path.is_file(), "sealed namespace missing")
    manifest = load(manifest_path)
    require(manifest.get("status") == "PASS" and manifest.get("exact_recursive_coverage") is True and
            manifest.get("excludes_only") == "SHA256_MANIFEST.json", "exact seal schema")
    by_relative = {}
    for row in manifest.get("files", []):
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts and row["path"] not in by_relative,
                "seal member path/duplicate")
        by_relative[row["path"]] = row
    actual = {path.relative_to(namespace).as_posix() for path in namespace.rglob("*") if path.is_file()}
    require(actual == set(by_relative) | {"SHA256_MANIFEST.json"}, "exact namespace member coverage")
    members = [manifest_path]
    for relative, row in by_relative.items():
        path = (namespace / relative).resolve()
        require(path.is_relative_to(namespace) and path.stat().st_size == row["size_bytes"] and digest(path) == row["sha256"],
                "sealed namespace member hash")
        members.append(path)
    return manifest, members


def verify_pinned_seal(namespace: Path, manifest_sha256: str) -> list[Path]:
    require(digest(Path(namespace) / "SHA256_MANIFEST.json") == manifest_sha256, "pinned seal manifest hash")
    return verify_exact_seal(namespace)[1]


def is_weight(path: Path) -> bool:
    return Path(path).suffix.lower() in WEIGHT_SUFFIXES


def verify_runtime_input_records(records: list[dict], joint_records: dict[Path, dict]) -> dict:
    """Rehash all non-weights; bind weight records without opening weight bytes."""
    seen, counts = set(), collections.Counter()
    for row in records:
        path = Path(row["path"]).resolve()
        require(path not in seen and path.is_file(), "runtime input record duplicate/missing")
        lowered_parts = [part.casefold() for part in path.parts]
        require(not any(re.search(r"(^|[^a-z])gold([^a-z]|$)", part) for part in lowered_parts),
                "Gold-bearing runtime input path forbidden")
        if "daa_v2_fresh_v1" in lowered_parts and "runtime_branch_freeze" in lowered_parts:
            require(path.name not in set(LEDGERS.values()) | {"call_events.jsonl"},
                    "historical runtime answer ledger input forbidden")
        seen.add(path)
        require(type(row.get("size_bytes")) is int and HEX64.fullmatch(str(row.get("sha256", ""))), "runtime input record schema")
        if is_weight(path):
            accepted = joint_records.get(path)
            require(accepted is not None and accepted["size_bytes"] == row["size_bytes"] and
                    accepted["sha256"] == row["sha256"] and path.stat().st_size == row["size_bytes"],
                    "weight record differs from accepted joint preflight")
            counts["weight_records_bound_without_byte_read"] += 1
        else:
            require(path.stat().st_size == row["size_bytes"] and digest(path) == row["sha256"], "runtime input changed")
            counts["nonweight_records_rehashed"] += 1
    counts["input_records"] = len(records)
    return dict(counts)


def validate_replay_input_extension(canonical_records: list[dict], replay_records: list[dict],
                                    canonical_members: list[Path]) -> None:
    """Replay adds exactly its sealed canonical reference and changes no core input."""
    def indexed(rows):
        result = {}
        for row in rows:
            path = Path(row["path"]).resolve()
            require(path not in result, "duplicate executable input path")
            result[path] = row
        return result
    core, replay = indexed(canonical_records), indexed(replay_records)
    require(set(core) <= set(replay) and all(replay[path] == row for path, row in core.items()),
            "canonical/replay common executable inputs")
    expected_extra = {Path(path).resolve(): record(path) for path in canonical_members}
    actual_extra = {path: replay[path] for path in set(replay) - set(core)}
    require(actual_extra == expected_extra, "replay-only inputs must equal canonical sealed namespace")


def validate_model_snapshot_records(runtime_records: list[dict], joint_records: dict[Path, dict],
                                    original: Path) -> dict:
    runtime = {Path(row["path"]).resolve(): row for row in runtime_records}
    counts = {}
    roots = {
        "phi": original / f"data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct/snapshots/{PHI_REVISION}",
        "bge": original / f"data/models/huggingface/models--BAAI--bge-base-en-v1.5/snapshots/{BGE_REVISION}",
    }
    for name, root in roots.items():
        root = root.resolve()
        accepted = {path: row for path, row in joint_records.items() if path.is_relative_to(root)}
        frozen = {path: row for path, row in runtime.items() if path.is_relative_to(root)}
        actual = {path.resolve() for path in root.rglob("*") if path.is_file()}
        require(accepted and set(accepted) == set(frozen) == actual and
                all(frozen[path] == accepted[path] for path in accepted), f"{name} exact accepted snapshot records")
        counts[name + "_snapshot_files"] = len(actual)
    return counts


def validate_runtime_config(config: dict) -> None:
    expected = {
        "reader": "microsoft/Phi-3.5-mini-instruct", "reader_revision": PHI_REVISION,
        "bge": "BAAI/bge-base-en-v1.5", "bge_revision": BGE_REVISION,
        "dtype": "torch.bfloat16", "batch_size": 1, "active_reader_instances": 1,
        "answer_max_new_tokens": 48, "repair_query_max_new_tokens": 64,
        "context_budget_characters": 16000, "maximum_generation_input_tokens": 9472,
        "original_evidence_top_k": 5, "original_question_retrieval_calls": 0,
        "repair_candidate_depth": 50, "replacement_position_zero_based": 4,
        "same_retriever_repair": True, "do_sample": False, "runtime_seed": 20260830,
    }
    for key, value in expected.items():
        require(config.get(key) == value, f"runtime config mismatch: {key}")
    require(config.get("reader_model_class") == "Phi3ForCausalLM" and config.get("bge_model_class") == "BertModel",
            "runtime model class")
    require(config.get("versions") == {"torch": "2.7.1+cu128", "transformers": "4.53.2", "numpy": "2.2.6"},
            "runtime library versions")
    for stage, maximum in (("a0", 48), ("repair_query", 64), ("a1", 48)):
        generation = config["effective_generation_configs"][stage]
        require(generation["do_sample"] is False and generation["max_new_tokens"] == maximum and
                generation["use_cache"] is True and generation["return_dict_in_generate"] is True and
                generation["output_scores"] is True and generation.get("temperature") is None and
                generation.get("top_p") is None and generation.get("top_k") is None,
                f"generation config: {stage}")
    require(str(config.get("device", "")).startswith("cuda") and config.get("reader_attention") ==
            config.get("bge_attention") == "sdpa", "runtime CUDA/attention config")


def validate_runtime_audit_boundary(freeze: dict, receipt: dict) -> None:
    require(freeze.get("audit_boundary_start") == receipt.get("audit_boundary_start") ==
            EXPECTED_RUNTIME_AUDIT_BOUNDARY_START, "runtime audit boundary binding")


def validate_runtime_model_load_counts(receipt: dict) -> None:
    require(receipt.get("bge_model_loads") == receipt.get("reader_model_loads") == 1 and
            receipt.get("nli_model_loads") == 0, "runtime model load counts")


def validate_runtime_namespace(namespace: Path, *, mode: str, expected_commit: str,
                               expected_manifest_sha256: str | None = None) -> dict:
    if expected_manifest_sha256 is not None:
        require(HEX64.fullmatch(expected_manifest_sha256) is not None and
                digest(Path(namespace) / "SHA256_MANIFEST.json") == expected_manifest_sha256,
                "runtime namespace manifest pin")
    _manifest, members = verify_exact_seal(namespace)
    receipt = load(namespace / "BUILD_RECEIPT.json"); freeze = load(namespace / "EXECUTABLE_FREEZE.json")
    status = "PASS_PHI_DEVELOPMENT_RUNTIME" if mode == "canonical" else "PASS_PHI_DEVELOPMENT_REPLAY"
    expected = 13_500 if mode == "canonical" else 180
    require(receipt.get("status") == status and receipt.get("mode") == mode and receipt.get("completed_traces") == expected and
            receipt.get("expected_traces") == expected, "runtime receipt status/count")
    require(receipt.get("source_commit") == freeze.get("source_commit") == expected_commit and
            re.fullmatch(r"[0-9a-f]{40}", expected_commit) is not None, "runtime source commit")
    validate_runtime_audit_boundary(freeze, receipt)
    require(freeze.get("mode") == mode and freeze.get("output_name") == namespace.name and
            freeze.get("command_contract", {}).get("output_name") == namespace.name, "runtime freeze namespace/mode")
    command = freeze["command_contract"]
    require(freeze.get("status") == "FROZEN_BEFORE_BENCHMARK_EXECUTION" and command.get("mode") == mode and
            command.get("project_root") == str(Path("E:/paper/ReliableRAG").resolve()) and
            command.get("canonical_output_name") == freeze.get("canonical_output_name") and
            ((mode == "canonical" and freeze.get("canonical_output_name") is None) or
             (mode == "replay" and type(freeze.get("canonical_output_name")) is str)),
            "runtime freeze status/command contract")
    require(freeze.get("call_durability") ==
            "fsync intent; execute one call; fsync main ledger row; fsync completion; unmatched intent forbids resume",
            "runtime call durability contract")
    validate_runtime_config(freeze["runtime_config"])
    config_sha = object_sha(freeze["runtime_config"])
    require(freeze.get("runtime_config_sha256") == receipt.get("runtime_config_sha256") == config_sha,
            "runtime config digest binding")
    require(record(namespace / "EXECUTABLE_FREEZE.json") == receipt.get("executable_freeze"), "receipt executable freeze record")
    artifact_paths = {Path(row["path"]).resolve(): row for row in receipt.get("artifacts", [])}
    required_artifacts = {namespace / filename for filename in (*LEDGERS.values(), "call_events.jsonl")}
    require(set(artifact_paths) == {path.resolve() for path in required_artifacts}, "runtime receipt artifact set")
    for path, row in artifact_paths.items():
        require(record(path) == row, "runtime receipt artifact record")
    require(receipt.get("fresh_gold_values_materialized") == receipt.get("historical_qwen_answer_strings_read") ==
            receipt.get("scientific_fit_calls") == receipt.get("original_question_retrieval_calls") ==
            receipt.get("document_embedding_calls") == receipt.get("bm25_structure_rebuild_calls") == 0,
            "runtime prohibited operation counters")
    require(receipt.get("generation_failure_count") == receipt.get("repair_failure_count") == 0 and
            receipt.get("source_inputs_unchanged") is True, "runtime completion/failure receipt")
    require(receipt.get("automatic_retry_allowed") is False and
            receipt.get("execution_boundary", {}).get("denied") == [], "runtime retry/IO boundary receipt")
    validate_runtime_model_load_counts(receipt)
    require(freeze.get("scope", "").startswith("Phi development generation only"), "runtime freeze scope")
    device = freeze.get("device_at_start")
    require(receipt.get("launch_device") == device and receipt.get("gpu_mutex") == "Local\\ReliableRAG_Phi_Development_Runtime_GPU" and
            type(device.get("start_free_bytes")) is int and type(device.get("start_total_bytes")) is int and
            0 < device["start_free_bytes"] <= device["start_total_bytes"] <= device["nominal_total_bytes"] and
            type(receipt.get("peak_allocated_cuda_bytes")) is int and type(receipt.get("peak_reserved_cuda_bytes")) is int and
            0 <= receipt["peak_allocated_cuda_bytes"] <= receipt["peak_reserved_cuda_bytes"],
            "runtime GPU/device/allocator receipt")
    return {"namespace": namespace.resolve(), "receipt": receipt, "freeze": freeze, "members": members,
            "runtime_config_sha256": config_sha, "expected": expected}


def event_id(row: dict, operation: str) -> str:
    return f"{int(row['position']):05d}:{row['dataset']}:{row['retriever']}:{row['sample_id']}:{operation}"


def validate_event_pair(intent: dict, completion: dict, *, ledger_name: str, row: dict,
                        operation: str) -> None:
    identifier = event_id(row, operation)
    require(intent.get("event") == "intent" and completion.get("event") == "completion" and
            intent.get("event_id") == completion.get("event_id") == identifier and
            intent.get("operation") == completion.get("operation") == operation,
            "call intent/completion pairing")
    require(all(intent.get(field) == row[field] for field in ("dataset", "retriever", "sample_id", "position")),
            "call event trace binding")
    require(completion.get("ledger") == ledger_name and completion.get("ledger_row_sha256") == object_sha(row),
            "call completion row binding")
    fields = (("runtime_config_sha256", "question_sha256", "evidence_sha256") if ledger_name == "generation_receipts"
              else ("runtime_config_sha256", "query_sha256", "requested_depth"))
    require(all(intent.get(field) == row.get(field) for field in fields), "call intent scientific input binding")
    if ledger_name == "repair_bindings": require(row["requested_depth"] == 50, "repair event depth")


def validate_events(events: list[dict], ledgers: dict[str, list[dict]]) -> None:
    require(len(events) % 2 == 0, "unpaired call intent")
    pairs = {}
    for offset in range(0, len(events), 2):
        intent, completion = events[offset:offset + 2]
        require(intent.get("event") == "intent" and completion.get("event") == "completion" and
                intent.get("event_id") == completion.get("event_id") and intent.get("operation") == completion.get("operation"),
                "call intent/completion pairing")
        require(intent["event_id"] not in pairs, "duplicate call event")
        pairs[intent["event_id"]] = (intent, completion)
    expected, order = {}, []
    generations = {(r["dataset"], r["retriever"], r["sample_id"], r["stage"]): r for r in ledgers["generation_receipts"]}
    repairs = {(r["dataset"], r["retriever"], r["sample_id"]): r for r in ledgers["repair_bindings"]}
    seen = set()
    for row in ledgers["generation_receipts"]:
        key = (row["dataset"], row["retriever"], row["sample_id"])
        if key in seen: continue
        seen.add(key)
        for operation in ("a0", "repair_query"):
            item = generations[(*key, operation)]; identifier = event_id(item, operation)
            expected[identifier] = ("generation_receipts", item); order.append(identifier)
        item = repairs[key]; identifier = event_id(item, "repair_retrieval")
        expected[identifier] = ("repair_bindings", item); order.append(identifier)
        item = generations[(*key, "a1")]; identifier = event_id(item, "a1")
        expected[identifier] = ("generation_receipts", item); order.append(identifier)
    require(list(pairs) == order and set(pairs) == set(expected), "call event exact order/set")
    for identifier, (ledger_name, row) in expected.items():
        intent, completion = pairs[identifier]
        operation = row["stage"] if ledger_name == "generation_receipts" else "repair_retrieval"
        validate_event_pair(intent, completion, ledger_name=ledger_name, row=row, operation=operation)


def parse_answer(raw: str) -> str:
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    if not lines: return ""
    answer = re.sub(r"^(?:final\s+)?answer\s*:\s*", "", lines[0], flags=re.I)
    return re.sub(r"^the answer is\s+", "", answer, flags=re.I).strip()


def parse_query(raw: str, question: str) -> tuple[str, bool]:
    matches = [value.strip() for value in re.findall(r"(?im)^\s*search\s+query\s*:\s*(.*?)\s*$", raw) if value.strip()]
    fallback = not matches
    query = matches[0] if matches else next((line.strip() for line in reversed(raw.splitlines()) if line.strip()), question)
    if not query: return question, True
    return query, fallback


def render_evidence(evidence: list[dict], budget: int = 16_000) -> tuple[str, dict]:
    require(len(evidence) == 5 and [row["rank"] for row in evidence] == [1, 2, 3, 4, 5], "evidence exact ranks")
    identifiers = [row["document_id"] for row in evidence]; require(len(set(identifiers)) == 5, "evidence unique IDs")
    headers = [f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n" for row in evidence]
    separators = ["", "\n\n", "\n\n", "\n\n", "\n\n"]
    remaining = budget - sum(len(a) + len(b) for a, b in zip(separators, headers, strict=True))
    require(remaining >= 0, "evidence headers exceed budget")
    chunks, flags = [], []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip(); included = body[:remaining]; remaining -= len(included)
        chunks.append(separator + header + included); flags.append(len(included) < len(body))
    rendered = "".join(chunks)
    require(len(rendered) <= budget and all(identifier in rendered for identifier in identifiers), "evidence render identity")
    return rendered, {"text": rendered, "context_truncated": any(flags), "context_budget_characters": budget,
        "ordered_passed_document_ids": identifiers, "per_document_truncated": flags}


def reconstruct_generation(tokenizer, template: str, question: str, evidence: list[dict]) -> dict:
    rendered, render = render_evidence(evidence)
    user = template.format(question=question, evidence=rendered)
    prompt = tokenizer.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
    encoded = tokenizer([prompt], truncation=False)
    ids = encoded["input_ids"][0] if encoded["input_ids"] and isinstance(encoded["input_ids"][0], list) else encoded["input_ids"]
    ids = list(ids)
    return {"prompt_sha256": text_sha(prompt), "input_token_ids": ids, "input_tokens": len(ids),
            "rendered_context_characters": len(rendered), "render": render}


def validate_generation(row: dict, *, trace: dict, frozen: dict, provenance: dict, branch: dict,
                        tokenizer, templates: dict[str, str], config_sha: str) -> None:
    stage = row.get("stage"); require(stage in STAGES and row.get("reader") == "phi", "generation identity")
    require(all(row.get(field) == trace[field] for field in ("dataset", "retriever", "sample_id", "position")),
            "generation trace binding")
    evidence = provenance["e1"] if stage == "a1" else provenance["e0"]
    question = branch["question"]
    require(row.get("runtime_config_sha256") == config_sha and row.get("question_sha256") == text_sha(question) and
            row.get("evidence_sha256") == object_sha(evidence), "generation config/input hashes")
    rebuilt = reconstruct_generation(tokenizer, templates["repair_query" if stage == "repair_query" else "answer"], question, evidence)
    require(row["prompt_sha256"] == rebuilt["prompt_sha256"] and row["input_token_ids"] == rebuilt["input_token_ids"] and
            row["input_tokens"] == row["guard_input_tokens"] == rebuilt["input_tokens"] and row["attention_mask"] == [1] * rebuilt["input_tokens"],
            "independent prompt/token/admission reconstruction")
    require(row["render"] == rebuilt["render"] and 0 < row["input_tokens"] <= 9472, "independent render/guard reconstruction")
    if stage in {"a0", "repair_query"}:
        witness = frozen["answer" if stage == "a0" else "repair_query"]
        require(row["prompt_sha256"] == witness["prompt_sha256"] and row["input_tokens"] == witness["input_tokens"] and
                object_sha(row["input_token_ids"]) == witness["input_token_ids_sha256"] and
                rebuilt["rendered_context_characters"] == witness["rendered_context_characters"] and
                row["render"]["context_truncated"] == witness["context_truncated"] and
                row["render"]["per_document_truncated"] == witness["per_document_truncated"],
                "accepted input-freeze generation witness")
    generated = row["generated_token_ids"]; maximum = 64 if stage == "repair_query" else 48
    require(type(generated) is list and all(type(value) is int for value in generated) and
            len(generated) == row["native_output_score_steps"] <= maximum, "generated token receipt")
    pad = tokenizer.pad_token_id; output_count = next((i for i, value in enumerate(generated) if value == pad), len(generated))
    require(row["output_tokens"] == output_count and row["logical_generation_calls"] == 1 and
            type(row["phi_forward_calls"]) is int and row["phi_forward_calls"] == row["native_output_score_steps"] > 0,
            "generation counts")
    decoded = tokenizer.batch_decode([generated], skip_special_tokens=True)[0].strip()
    require(row["raw_text"] == decoded, "generated token/raw text binding")
    if stage == "repair_query":
        parsed, fallback = parse_query(decoded, question)
        require(row["parsed_text"] == parsed and row["parser_fallback"] is fallback, "repair-query parser reconstruction")
    else:
        require(row["parsed_text"] == parse_answer(decoded) and row["parser_fallback"] is None, "answer parser reconstruction")


def _same_float(left, right) -> bool:
    return type(left) in {int, float} and type(right) in {int, float} and math.isfinite(float(left)) and float(left) == float(right)


def ordered_scores(scores, document_ids: list[str], depth: int) -> list[dict]:
    import numpy as np
    values = np.asarray(scores)
    require(values.shape == (len(document_ids),) and np.isfinite(values).all(), "finite retrieval score vector")
    order = np.lexsort((np.arange(len(document_ids), dtype=np.int64), -values))[:depth].tolist()
    return [{"document_id": document_ids[index], "rank": rank, "score": float(scores[index])}
            for rank, index in enumerate(order, 1)]


def bm25_scores(query: str, payload: dict):
    import numpy as np
    ids = payload["document_ids"]; scores = np.zeros(len(ids), dtype=np.float64)
    terms = payload.get("_terms_by_name")
    if terms is None:
        terms = {row["term"]: row for row in payload["terms"]}
    lengths = payload["lengths"]; average = payload["average_length"]
    for term in re.findall(r"(?u)\b\w+\b", query.casefold()):
        item = terms.get(term)
        if item is None: continue
        for index, frequency in item["postings"]:
            normalization = frequency + 1.5 * (1.0 - .75 + .75 * lengths[index] / average)
            scores[index] += item["idf"] * (frequency * 2.5 / normalization)
    return scores


def rrf(component_rows: list[list[dict]], depth: int = 50) -> list[dict]:
    scores, first_seen = {}, {}
    for list_index, ranking in enumerate(component_rows):
        for row in ranking:
            document_id = row["document_id"]
            scores[document_id] = scores.get(document_id, 0.0) + 1.0 / (60 + row["rank"])
            first_seen.setdefault(document_id, (list_index, row["rank"]))
    ordered = sorted(scores, key=lambda document_id: (-scores[document_id], first_seen[document_id], document_id))[:depth]
    return [{"document_id": document_id, "rank": rank, "score": scores[document_id]}
            for rank, document_id in enumerate(ordered, 1)]


def compare_ranking(actual: list[dict], expected: list[dict], message: str) -> None:
    require(len(actual) == len(expected), message + " depth")
    for left, right in zip(actual, expected, strict=True):
        require(left["document_id"] == right["document_id"] and left["rank"] == right["rank"] and
                _same_float(left["score"], right["score"]), message)


def validate_repair(row: dict, *, trace: dict, provenance: dict, branch: dict, query: str,
                    retrieval: dict) -> None:
    import numpy as np
    require(type(query) is str and query.strip(), "nonempty repair query")
    require(all(row.get(field) == trace[field] for field in ("dataset", "retriever", "sample_id", "position")),
            "repair trace binding")
    require(row["requested_depth"] == 50 and row["repair_retrieval_calls"] == 1 and
            row["replacement_position_zero_based"] == 4 and row["fail_closed_reason"] is None and
            row["query_sha256"] == text_sha(query), "repair fixed controls/query")
    require(len(row["ranking"]) == 50 and [item["rank"] for item in row["ranking"]] == list(range(1, 51)) and
            len({item["document_id"] for item in row["ranking"]}) == 50, "repair exact depth/ranks")
    e0_ids = trace["original_top5_ids"]
    require(row["e0_ids"] == e0_ids and row["e1_ids"][:4] == e0_ids[:4] and row["replaced_document_id"] == e0_ids[4] and
            row["e1_ids"][4] == row["inserted_document_id"] not in e0_ids, "repair rank-5 replacement")
    dataset = trace["dataset"]; document_ids = retrieval[dataset]["document_ids"]
    components = {}
    if trace["retriever"] in {"bm25", "hybrid"}:
        depth = 100 if trace["retriever"] == "hybrid" else 50
        components["bm25"] = ordered_scores(bm25_scores(query, retrieval[dataset]["bm25"]), document_ids, depth)
    if trace["retriever"] in {"dense", "hybrid"}:
        vector = row["dense_query_vector"]
        require(type(vector) is list and len(vector) == 768 and all(type(x) in {int, float} and math.isfinite(float(x)) for x in vector),
                "saved dense query vector")
        vector_array = np.asarray(vector, dtype=np.float32)
        require(abs(float(np.linalg.norm(vector_array)) - 1.0) <= 1e-3, "saved dense query vector normalization")
        scores = retrieval[dataset]["dense"] @ vector_array
        depth = 100 if trace["retriever"] == "hybrid" else 50
        components["dense"] = ordered_scores(scores, document_ids, depth)
    else:
        require(row["dense_query_vector"] is None, "BM25 must have no dense vector")
    require(set(row["component_rankings"]) == set(components), "same-retriever component set")
    for name in components: compare_ranking(row["component_rankings"][name], components[name], "repair component recomputation")
    expected = rrf([components["bm25"], components["dense"]]) if trace["retriever"] == "hybrid" else components[trace["retriever"]]
    compare_ranking(row["ranking"], expected, "repair final ranking recomputation")
    inserted = next((item for item in expected if item["document_id"] not in set(e0_ids)), None)
    require(inserted is not None and row["inserted_document_id"] == inserted["document_id"] and
            row["inserted_candidate_rank"] == inserted["rank"], "first outside-E0 repair candidate")
    require([item["document_id"] for item in provenance["e0"]] == e0_ids and
            [item["document_id"] for item in provenance["e1"]] == row["e1_ids"], "repair provenance evidence IDs")
    require(branch["evidence0"] == [item["text"] for item in provenance["e0"]] and
            branch["evidence1"] == [item["text"] for item in provenance["e1"]], "branch evidence text")


def validate_ledger_order(selected: list[dict], ledgers: dict[str, list[dict]]) -> None:
    expected_keys = [(row["dataset"], row["retriever"], row["sample_id"], row["position"]) for row in selected]
    require(len(ledgers["generation_receipts"]) == len(selected) * 3 and
            all(len(ledgers[name]) == len(selected) for name in LEDGERS if name != "generation_receipts"),
            "ledger row counts before order validation")
    for name in ("repair_bindings", "branch_provenance", "canonical_branches"):
        actual = [(row["dataset"], row["retriever"], row["sample_id"], row.get("position", position))
                  for position, row in enumerate(ledgers[name])]
        if name == "canonical_branches": actual = [(row["dataset"], row["retriever"], row["sample_id"], selected[i]["position"])
                                                     for i, row in enumerate(ledgers[name])]
        require(actual == expected_keys, f"{name} trace order")
    generation_keys = [(row["dataset"], row["retriever"], row["sample_id"], row["position"], row["stage"])
                       for row in ledgers["generation_receipts"]]
    expected_generation = [(*key, stage) for key in expected_keys for stage in STAGES]
    require(generation_keys == expected_generation, "generation ledger trace/stage order")


def validate_trace_sources(traces: list[dict], replay: list[dict], frozen_rows: list[dict], *,
                           trace_count: int = 13_500, replay_per_cell: int = 20) -> dict:
    development = [row for row in frozen_rows if row.get("cohort") == "development"]
    require(len(traces) == len(development) == trace_count, "development trace count")
    index = {}
    for position, (trace, frozen) in enumerate(zip(traces, development, strict=True)):
        key = (trace["dataset"], trace["retriever"], trace["sample_id"])
        require(key == (frozen["dataset"], frozen["retriever"], frozen["sample_id"]) and
                trace["position"] == frozen["position"] == position and frozen["role"] in {"fit", "cal"} and
                object_sha(trace["original_top5_ids"]) == frozen["original_top5_ids_sha256"] and key not in index,
                "trace/input-freeze sequence binding")
        index[key] = frozen
    roles = {}
    for row in development:
        question_key = (row["dataset"], row["sample_id"])
        require(question_key not in roles or roles[question_key] == row["role"], "development sibling role consistency")
        roles[question_key] = row["role"]
    require(len(roles) == trace_count // 3, "development unique question count")
    if trace_count == 13_500:
        require(collections.Counter(roles.values()) == collections.Counter({"fit": 3_600, "cal": 900}),
                "development role membership/counts")
    require(len(replay) == len(DATASETS) * len(RETRIEVERS) * replay_per_cell and
            all(traces[row["position"]] == row for row in replay), "fixed replay membership/order")
    strata = collections.Counter((row["dataset"], row["retriever"]) for row in replay)
    require(strata == collections.Counter({(dataset, retriever): replay_per_cell for dataset in DATASETS for retriever in RETRIEVERS}),
            "fixed replay strata")
    return index


def validate_receipt_counts(run: dict, ledgers: dict[str, list[dict]], selected: list[dict]) -> None:
    receipt = run["receipt"]; expected = len(selected); counters = receipt["counters"]
    require(len(ledgers["generation_receipts"]) == expected * 3 and
            all(len(ledgers[name]) == expected for name in LEDGERS if name != "generation_receipts"), "ledger row counts")
    require(receipt["guard_admission_count"] == expected * 3 and receipt["guard_admission_max_tokens"] ==
            max(row["guard_input_tokens"] for row in ledgers["generation_receipts"]), "guard admission receipt")
    for stage in STAGES:
        require(counters[stage + "_generation_calls"] == counters[stage + "_generation_completed"] == expected,
                "generation receipt counter")
        require(counters[stage + "_forward_calls"] == sum(row["phi_forward_calls"] for row in ledgers["generation_receipts"] if row["stage"] == stage),
                "stage forward receipt counter")
    require(counters["phi_forward_calls"] == sum(row["phi_forward_calls"] for row in ledgers["generation_receipts"]) and
            counters["repair_retrieval_calls"] == counters["repair_retrieval_completed"] == expected,
            "forward/repair receipt counters")
    for retriever in RETRIEVERS:
        require(counters["repair_" + retriever + "_calls"] == sum(row["retriever"] == retriever for row in selected),
                "same-retriever call counters")
    dense = sum(row["retriever"] in {"dense", "hybrid"} for row in selected)
    require(counters["repair_query_embedding_calls"] == counters["bge_query_forward_calls"] == dense, "BGE query counters")
    require(receipt["stratum_counts"] == {f"{dataset}/{retriever}": sum(row["dataset"] == dataset and row["retriever"] == retriever for row in selected)
                                           for dataset in DATASETS for retriever in RETRIEVERS}, "receipt stratum counts")
    require(receipt["question_clusters"] == len({(row["dataset"], row["sample_id"]) for row in selected}),
            "receipt question cluster count")
    expected_failclosed = {
        "empty_a0_retained": sum(row["stage"] == "a0" and not row["parsed_text"] for row in ledgers["generation_receipts"]),
        "empty_a1_retained": sum(row["stage"] == "a1" and not row["parsed_text"] for row in ledgers["generation_receipts"]),
        "native_repair_parser_fallback_retained": sum(row["stage"] == "repair_query" and row["parser_fallback"]
                                                       for row in ledgers["generation_receipts"]),
    }
    expected_failclosed = {key: value for key, value in expected_failclosed.items() if value}
    require(receipt["fail_closed_counts"] == expected_failclosed, "fail-closed receipt counts")
    if run["freeze"]["mode"] == "canonical":
        require(all(receipt[field] == 0 for field in ("replay_canonical_reference_rows_decoded", "replay_canonical_string_fields_decoded",
                "replay_canonical_answer_fields_decoded", "replay_canonical_reference_raw_lines_scanned",
                "replay_canonical_reference_raw_bytes_scanned")) and receipt["replay_exact_match"] is None,
                "canonical replay counters")
    else:
        require(receipt["replay_canonical_reference_rows_decoded"] == expected * 6 and
                receipt["replay_canonical_answer_fields_decoded"] == expected * 6 and
                receipt["replay_canonical_string_fields_decoded"] > 0 and
                receipt["replay_canonical_reference_raw_lines_scanned"] == 13_500 * 6 and
                receipt["replay_canonical_reference_raw_bytes_scanned"] > 0 and receipt["replay_exact_match"] is True,
                "truthful replay reference counters")


def string_field_count(value: object) -> int:
    if isinstance(value, str): return 1
    if isinstance(value, list): return sum(string_field_count(item) for item in value)
    if isinstance(value, dict): return sum(string_field_count(item) for item in value.values())
    return 0


def answer_string_field_count(ledgers: dict[str, list[dict]]) -> int:
    generation = sum(2 for row in ledgers["generation_receipts"] if row["stage"] in {"a0", "a1"})
    branches = 2 * len(ledgers["canonical_branches"])
    return generation + branches


def verify_replay_bytes(canonical_raw: dict[str, list[bytes]], replay_raw: dict[str, list[bytes]], replay: list[dict], *,
                        canonical_ledgers: dict[str, list[dict]] | None = None) -> None:
    for name in LEDGERS:
        multiplier = 3 if name == "generation_receipts" else 1
        selected = []
        for trace in replay:
            base = trace["position"] * multiplier
            if canonical_raw[name]:
                selected.extend(canonical_raw[name][base:base + multiplier])
            else:
                require(canonical_ledgers is not None, "canonical replay byte source")
                selected.extend(canonical(row) + b"\n" for row in canonical_ledgers[name][base:base + multiplier])
        require(selected == replay_raw[name], f"replay {name} byte identity")


def validate_replay_reference_accounting(receipt: dict, canonical_ledgers: dict[str, list[dict]],
                                         canonical_raw: dict[str, list[bytes]], replay: list[dict], *,
                                         canonical_namespace: Path | None = None) -> None:
    selected_rows = []
    for name in LEDGERS:
        multiplier = 3 if name == "generation_receipts" else 1
        for trace in replay:
            base = trace["position"] * multiplier
            selected_rows.extend(canonical_ledgers[name][base:base + multiplier])
    raw_lines = sum(len(rows) for rows in canonical_ledgers.values())
    raw_bytes = (sum(len(raw) for rows in canonical_raw.values() for raw in rows) if any(canonical_raw.values()) else
                 sum((Path(canonical_namespace) / filename).stat().st_size for filename in LEDGERS.values()))
    require(receipt["replay_canonical_reference_rows_decoded"] == len(selected_rows) == len(replay) * 6 and
            receipt["replay_canonical_string_fields_decoded"] == sum(string_field_count(row) for row in selected_rows) and
            receipt["replay_canonical_answer_fields_decoded"] == len(replay) * 6 and
            receipt["replay_canonical_reference_raw_lines_scanned"] == raw_lines and
            receipt["replay_canonical_reference_raw_bytes_scanned"] == raw_bytes,
            "exact replay canonical-reference accounting")


def load_dataset_assets(original: Path, dataset: str) -> dict:
    import numpy as np
    root = original / "outputs/daa_v2_fresh_v1/retrieval_freeze"
    pool = original / "outputs/daa_v2_fresh_v1/pool_freeze/pools"
    require(dataset in DATASETS, "dataset asset identity")
    bm25 = load(root / "indexes" / dataset / "bm25_structure.json")
    bm25["_terms_by_name"] = {row["term"]: row for row in bm25["terms"]}
    dense = np.load(root / "indexes" / dataset / "document_embeddings.npy", allow_pickle=False)
    require(dense.dtype == np.float32 and dense.shape == (len(bm25["document_ids"]), 768), "serialized dense matrix")
    docs, _ = read_canonical_jsonl(pool / f"{dataset}_documents.jsonl")
    by_id = {row["id"]: row for row in docs}
    require(list(by_id) == bm25["document_ids"], "serialized index/pool document order")
    for row in docs:
        require(row["content_hash"] == object_sha(row["sentences"]) and
                row["id"].startswith(dataset + ":") and row["id"][len(dataset) + 1:] ==
                object_sha({"title": re.sub(r"\s+", " ", row["title"].strip()).casefold(), "content_hash": row["content_hash"]})[:24],
                "pool document content identity")
    runtime_rows, _ = read_canonical_jsonl(original / "outputs/daa_v2_fresh_v1/pool_freeze/runtime_projection" /
                                           f"{dataset}_selected_runtime.jsonl")
    require(len(runtime_rows) == 1500 and
            all(set(row) == {"id", "dataset", "split", "question", "documents"} for row in runtime_rows),
            "label-free runtime projection schema/count")
    original_top5 = {}
    for retriever in RETRIEVERS:
        ranking_rows, _ = read_canonical_jsonl(root / "rankings" / f"{dataset}_{retriever}.jsonl")
        require(len(ranking_rows) == 1500, "original ranking row count")
        for row in ranking_rows:
            top = row["ranking"][:5]
            top_record = {"dataset": dataset, "sample_id": row["sample_id"], "retriever": retriever,
                          "document_ids": [item["document_id"] for item in top]}
            key = (dataset, retriever, row["sample_id"]); require(key not in original_top5, "duplicate original ranking")
            original_top5[key] = (top, object_sha(top_record))
    return {"retrieval": {dataset: {"bm25": bm25, "dense": dense, "document_ids": bm25["document_ids"]}},
        "documents": {dataset: by_id}, "original_top5": original_top5,
        "questions": {dataset: {row["id"]: row["question"] for row in runtime_rows}},
        "pool_hashes": {dataset: digest(pool / f"{dataset}_documents.jsonl")}}


def load_retrieval_assets(original: Path) -> tuple[dict, dict[str, dict], dict, dict, dict]:
    """Compatibility helper for small audits; formal validation loads one dataset at a time."""
    merged = ({}, {}, {}, {}, {})
    for dataset in DATASETS:
        item = load_dataset_assets(original, dataset)
        for target, name in zip(merged, ("retrieval", "documents", "original_top5", "questions", "pool_hashes"), strict=True):
            target.update(item[name])
    return merged


def validate_trace_bundle(*, trace: dict, generations: list[dict], repair: dict, provenance: dict, branch: dict,
                          frozen: dict, tokenizer, templates: dict[str, str], assets: dict, config_sha: str) -> None:
    key = (trace["dataset"], trace["retriever"], trace["sample_id"]); dataset = trace["dataset"]
    require([(row["dataset"], row["retriever"], row["sample_id"], row["position"], row["stage"]) for row in generations] ==
            [(*key, trace["position"], stage) for stage in STAGES], "generation ledger trace/stage order")
    for row, name in ((repair, "repair"), (provenance, "provenance")):
        require((row["dataset"], row["retriever"], row["sample_id"], row["position"]) == (*key, trace["position"]),
                f"{name} ledger trace order")
    require((branch["dataset"], branch["retriever"], branch["sample_id"]) == key and
            set(branch) == {"dataset", "retriever", "sample_id", "question", "a0", "a1", "evidence0", "evidence1"},
            "canonical branch trace/schema")
    require(branch["question"] == assets["questions"][dataset][trace["sample_id"]], "branch/runtime question binding")
    expected_top5, expected_top5_sha = assets["original_top5"][key]
    require(trace["original_top5_ids"] == [row["document_id"] for row in expected_top5] and
            trace["original_top5_row_sha256"] == expected_top5_sha, "trace/original ranking Top-5 binding")
    require(provenance["runtime_config_sha256"] == repair["runtime_config_sha256"] == config_sha and
            provenance["original_top5_row_sha256"] == trace["original_top5_row_sha256"] and
            provenance["canonical_row_sha256"] == object_sha(branch) and
            provenance["repair_binding_row_sha256"] == object_sha(repair), "provenance hash/config bindings")
    require(provenance["pool_sha256"] == repair["pool_sha256"] == assets["pool_hashes"][dataset], "pool hash binding")
    for evidence in provenance["e0"] + provenance["e1"]:
        source = assets["documents"][dataset][evidence["document_id"]]
        require(evidence["content_hash"] == source["content_hash"] and evidence["title"] == source["title"] and
                evidence["text"] == source["title"] + "\n" + "".join(source["sentences"]),
                "provenance/pool document binding")
    compare_ranking([{"document_id": row["document_id"], "rank": row["rank"], "score": row["retrieval_score"]}
                     for row in provenance["e0"]], expected_top5, "provenance original ranking")
    for row in generations:
        validate_generation(row, trace=trace, frozen=frozen, provenance=provenance, branch=branch,
                            tokenizer=tokenizer, templates=templates, config_sha=config_sha)
    require(generations[0]["parsed_text"] == branch["a0"] and generations[2]["parsed_text"] == branch["a1"] and
            provenance["question_sha256"] == text_sha(branch["question"]), "branch generation/question binding")
    validate_repair(repair, trace=trace, provenance=provenance, branch=branch,
                    query=generations[1]["parsed_text"], retrieval=assets["retrieval"])
    inserted_score = next(row["score"] for row in repair["ranking"] if row["document_id"] == repair["inserted_document_id"])
    require(provenance["e1"][:4] == provenance["e0"][:4] and provenance["e1"][4]["rank"] == 5 and
            provenance["e1"][4]["document_id"] == repair["inserted_document_id"] and
            _same_float(provenance["e1"][4]["retrieval_score"], inserted_score), "provenance repaired ranking")


def validate_receipt_stream_summary(run: dict, selected: list[dict], summary: dict) -> None:
    receipt = run["receipt"]; expected = len(selected); counters = receipt["counters"]
    require(summary["ledger_counts"] == {"generation_receipts": expected * 3, "repair_bindings": expected,
            "branch_provenance": expected, "canonical_branches": expected}, "streamed ledger row counts")
    require(receipt["guard_admission_count"] == summary["guard_count"] == expected * 3 and
            receipt["guard_admission_max_tokens"] == summary["guard_max"], "guard admission receipt")
    for stage in STAGES:
        require(counters[stage + "_generation_calls"] == counters[stage + "_generation_completed"] == expected and
                counters[stage + "_forward_calls"] == summary["stage_forwards"][stage], "generation receipt counter")
    require(counters["phi_forward_calls"] == summary["phi_forwards"] and
            counters["repair_retrieval_calls"] == counters["repair_retrieval_completed"] == expected,
            "forward/repair receipt counters")
    for retriever in RETRIEVERS:
        require(counters["repair_" + retriever + "_calls"] == summary["repair_calls"][retriever],
                "same-retriever call counters")
    require(counters["repair_query_embedding_calls"] == counters["bge_query_forward_calls"] == summary["dense_calls"],
            "BGE query counters")
    require(receipt["stratum_counts"] == {f"{dataset}/{retriever}": sum(row["dataset"] == dataset and row["retriever"] == retriever for row in selected)
                                           for dataset in DATASETS for retriever in RETRIEVERS} and
            receipt["question_clusters"] == len({(row["dataset"], row["sample_id"]) for row in selected}),
            "receipt stratum/question counts")
    require(receipt["fail_closed_counts"] == summary["failclosed"], "fail-closed receipt counts")
    if run["freeze"]["mode"] == "canonical":
        require(all(receipt[field] == 0 for field in ("replay_canonical_reference_rows_decoded", "replay_canonical_string_fields_decoded",
                "replay_canonical_answer_fields_decoded", "replay_canonical_reference_raw_lines_scanned",
                "replay_canonical_reference_raw_bytes_scanned")) and receipt["replay_exact_match"] is None,
                "canonical replay counters")
    else:
        require(receipt["replay_exact_match"] is True, "replay exact-match receipt")


def validate_run_streaming(run: dict, *, selected: list[dict], frozen_index: dict, tokenizer,
                           templates: dict[str, str], original: Path, capture_positions: set[int] | None = None,
                           expected_reference: dict[str, dict] | None = None) -> dict:
    capture_positions = capture_positions or set(); captured = {}
    summary = {"ledger_counts": {}, "stage_forwards": collections.Counter(), "phi_forwards": 0,
        "repair_calls": collections.Counter(), "dense_calls": 0, "guard_count": 0, "guard_max": 0,
        "failclosed": collections.Counter(), "string_fields": 0, "answer_string_fields": 0,
        "captured_rows": 0, "captured_string_fields": 0, "captured_answer_fields": 0}
    assets = None; current_dataset = None
    with ExitStack() as stack:
        streams = {name: stack.enter_context(CanonicalJsonlStream(run["namespace"] / filename)) for name, filename in LEDGERS.items()}
        event_stream = stack.enter_context(CanonicalJsonlStream(run["namespace"] / "call_events.jsonl"))
        for trace in selected:
            if trace["dataset"] != current_dataset:
                assets = load_dataset_assets(original, trace["dataset"]); current_dataset = trace["dataset"]
            generation_pairs = [streams["generation_receipts"].pop() for _ in STAGES]
            generations = [pair[0] for pair in generation_pairs]
            repair, repair_raw = streams["repair_bindings"].pop()
            provenance, provenance_raw = streams["branch_provenance"].pop()
            branch, branch_raw = streams["canonical_branches"].pop()
            validate_trace_bundle(trace=trace, generations=generations, repair=repair, provenance=provenance,
                branch=branch, frozen=frozen_index[(trace["dataset"], trace["retriever"], trace["sample_id"])],
                tokenizer=tokenizer, templates=templates, assets=assets, config_sha=run["runtime_config_sha256"])
            operation_rows = (("a0", "generation_receipts", generations[0]),
                              ("repair_query", "generation_receipts", generations[1]),
                              ("repair_retrieval", "repair_bindings", repair),
                              ("a1", "generation_receipts", generations[2]))
            for operation, ledger_name, row in operation_rows:
                intent, _intent_raw = event_stream.pop(); completion, _completion_raw = event_stream.pop()
                validate_event_pair(intent, completion, ledger_name=ledger_name, row=row, operation=operation)
            for row in generations:
                summary["stage_forwards"][row["stage"]] += row["phi_forward_calls"]
                summary["phi_forwards"] += row["phi_forward_calls"]; summary["guard_count"] += 1
                summary["guard_max"] = max(summary["guard_max"], row["guard_input_tokens"])
                if row["stage"] == "a0" and not row["parsed_text"]: summary["failclosed"]["empty_a0_retained"] += 1
                if row["stage"] == "a1" and not row["parsed_text"]: summary["failclosed"]["empty_a1_retained"] += 1
                if row["stage"] == "repair_query" and row["parser_fallback"]: summary["failclosed"]["native_repair_parser_fallback_retained"] += 1
            summary["repair_calls"][trace["retriever"]] += 1
            summary["dense_calls"] += int(trace["retriever"] in {"dense", "hybrid"})
            all_rows = [*generations, repair, provenance, branch]
            summary["string_fields"] += sum(string_field_count(row) for row in all_rows)
            summary["answer_string_fields"] += 6
            raw_by_name = {"generation_receipts": [raw for _row, raw in generation_pairs],
                "repair_bindings": [repair_raw], "branch_provenance": [provenance_raw], "canonical_branches": [branch_raw]}
            key = (trace["dataset"], trace["retriever"], trace["sample_id"])
            if trace["position"] in capture_positions:
                require(key not in captured, "duplicate selected canonical trace")
                captured[key] = raw_by_name
                summary["captured_rows"] += 6
                summary["captured_string_fields"] += sum(string_field_count(row) for row in all_rows)
                summary["captured_answer_fields"] += 6
            if expected_reference is not None:
                for name, values in raw_by_name.items():
                    require(expected_reference.get(key, {}).get(name) == values, f"replay {name} byte identity")
            del generations, generation_pairs, repair, provenance, branch, all_rows, raw_by_name
        for stream in streams.values(): stream.finish()
        event_stream.finish()
        summary["ledger_counts"] = {name: stream.rows for name, stream in streams.items()}
        summary["ledger_raw_lines"] = sum(stream.rows for stream in streams.values())
        summary["ledger_raw_bytes"] = sum(stream.bytes for stream in streams.values())
        summary["event_rows"] = event_stream.rows
    require(summary["event_rows"] == len(selected) * 8, "streamed call-event row count")
    summary["failclosed"] = dict(summary["failclosed"]); summary["captured"] = captured
    validate_receipt_stream_summary(run, selected, summary)
    return summary


def validator_read_allowed(path: Path, *, allowed: set[Path], output: Path,
                           environment_roots: tuple[Path, ...]) -> bool:
    path = Path(path).resolve()
    return path in allowed or path.is_relative_to(output) or any(path.is_relative_to(root) for root in environment_roots)


def install_boundary(*, allowed: set[Path], snapshot: Path, output: Path) -> dict:
    state = {"denied": [], "weight_reads_denied": 0, "outside_reads_denied": 0, "outside_writes_denied": 0,
             "model_weight_bytes_read": 0, "reader_model_loads": 0, "bge_model_loads": 0, "nli_model_loads": 0,
             "model_forward_calls": 0}
    allowed = {Path(path).resolve() for path in allowed}; snapshot = snapshot.resolve(); output = output.resolve()
    require(all(path.is_file() for path in allowed if path.is_relative_to(snapshot)), "tokenizer allowlist member")
    environments = tuple({Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()})
    def audit(event, args):
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request", "subprocess.Popen", "os.system"}:
            state["denied"].append(event); raise RuntimeError("independent development validator network/process boundary")
        if event != "open" or isinstance(args[0], int): return
        path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output):
                state["outside_writes_denied"] += 1; state["denied"].append(str(path)); raise RuntimeError("validator write outside output")
            return
        if is_weight(path):
            state["weight_reads_denied"] += 1; state["denied"].append(str(path)); raise RuntimeError("validator model weight read")
        if validator_read_allowed(path, allowed=allowed, output=output, environment_roots=environments): return
        state["outside_reads_denied"] += 1; state["denied"].append(str(path)); raise RuntimeError(f"validator non-allowlisted read: {path}")
    sys.addaudithook(audit); return state


def configure_validator_environment(output: Path) -> Path:
    """Keep third-party import probes and caches inside the single-use namespace."""
    temp_root = Path(output).resolve() / "cache" / "temp"
    temp_root.mkdir(parents=True, exist_ok=False)
    for key in ("TMP", "TEMP", "TMPDIR"):
        os.environ[key] = str(temp_root)
    tempfile.tempdir = str(temp_root)
    return temp_root


def write_json(path: Path, value: object) -> None:
    with Path(path).open("xb") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n")


def seal_output(output: Path) -> None:
    files = []
    for path in sorted(output.rglob("*")):
        if path.is_file():
            row = record(path); row["path"] = path.relative_to(output).as_posix(); files.append(row)
    write_json(output / "SHA256_MANIFEST.json", {"status": "PASS", "files": files,
        "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--canonical-output-name", required=True)
    parser.add_argument("--replay-output-name", required=True)
    parser.add_argument("--validation-output-name", required=True)
    parser.add_argument("--expected-runtime-commit", required=True)
    parser.add_argument("--expected-validator-commit", required=True)
    parser.add_argument("--canonical-manifest-sha256", required=True)
    parser.add_argument("--replay-manifest-sha256", required=True)
    args = parser.parse_args()
    for value in (args.canonical_output_name, args.replay_output_name, args.validation_output_name): safe_name(value)
    require(len({args.canonical_output_name, args.replay_output_name, args.validation_output_name}) == 3, "namespaces must be distinct")
    original = args.project_root.resolve(); require(original == Path("E:/paper/ReliableRAG").resolve(), "fixed original project root")
    output = (OUTPUT_PARENT / args.validation_output_name).resolve(); require(output.parent == OUTPUT_PARENT.resolve() and not output.exists(), "single-use validation namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit validator before execution")
    validator_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    require(args.expected_validator_commit == validator_commit and COMMIT_HEX40.fullmatch(validator_commit) is not None,
            "validator source commit does not match prospective correction pin")
    for key, value in {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                       "TOKENIZERS_PARALLELISM": "false", "PYTHONDONTWRITEBYTECODE": "1"}.items():
        os.environ[key] = value
    output.mkdir(parents=True, exist_ok=False)
    configure_validator_environment(output)
    result = {"status": "FAIL", "cas_q2_status": "NOT READY", "validator_source_commit": validator_commit,
        "expected_validator_source_commit": args.expected_validator_commit,
        "expected_runtime_source_commit": args.expected_runtime_commit, "gold_reads": 0, "scientific_fit_calls": 0,
        "historical_qwen_answer_strings_read": 0, "reader_model_loads": 0, "bge_model_loads": 0,
        "nli_model_loads": 0, "model_forward_calls": 0, "model_weight_bytes_read": 0, "tokenizer_loads": 0,
        "audit_boundary_start": "after namespace/source authentication and AutoTokenizer module import; before tokenizer from_pretrained and semantic decoding of trace, prompt, input-freeze, and runtime-ledger records"}
    boundary = None
    try:
        canonical_run = validate_runtime_namespace(OUTPUT_PARENT / args.canonical_output_name, mode="canonical",
            expected_commit=args.expected_runtime_commit, expected_manifest_sha256=args.canonical_manifest_sha256)
        replay_run = validate_runtime_namespace(OUTPUT_PARENT / args.replay_output_name, mode="replay",
            expected_commit=args.expected_runtime_commit, expected_manifest_sha256=args.replay_manifest_sha256)
        require(replay_run["freeze"].get("canonical_output_name") == args.canonical_output_name and
                replay_run["runtime_config_sha256"] == canonical_run["runtime_config_sha256"], "replay canonical/config binding")
        input_namespace = REPO / "outputs/cas_q2/phi_reader_input_freeze_v2"
        joint_namespace = REPO / "outputs/cas_q2/phi_bge_joint_gpu_preflight_v2"
        input_members = verify_pinned_seal(input_namespace, INPUT_FREEZE_MANIFEST_SHA256)
        joint_members = verify_pinned_seal(joint_namespace, JOINT_PREFLIGHT_MANIFEST_SHA256)
        joint = load(joint_namespace / "EXECUTABLE_FREEZE.json"); joint_records = {Path(row["path"]).resolve(): row for row in joint["inputs"]}
        input_audit = verify_runtime_input_records(canonical_run["freeze"]["inputs"], joint_records)
        replay_input_audit = verify_runtime_input_records(replay_run["freeze"]["inputs"], joint_records)
        model_snapshot_audit = validate_model_snapshot_records(canonical_run["freeze"]["inputs"], joint_records, original)
        for run in (canonical_run, replay_run):
            predecessors = run["freeze"]["predecessor_manifests"]
            require(predecessors["phi_input_freeze"] == record(input_namespace / "SHA256_MANIFEST.json") and
                    predecessors["phi_joint_preflight"] == record(joint_namespace / "SHA256_MANIFEST.json"),
                    "runtime predecessor manifest binding")
        validate_replay_input_extension(canonical_run["freeze"]["inputs"], replay_run["freeze"]["inputs"],
                                        canonical_run["members"])
        trace_path = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/trace_manifest.jsonl"
        replay_path = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/replay_subset.jsonl"
        prompt_paths = {"answer": original / "prompts/baseline_v1.txt", "repair_query": original / "prompts/repair_missing_v1.txt"}
        snapshot = original / f"data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct/snapshots/{PHI_REVISION}"
        allowed = set(canonical_run["members"] + replay_run["members"] + input_members + joint_members +
                      [Path(row["path"]) for row in canonical_run["freeze"]["inputs"] if not is_weight(Path(row["path"]))] +
                      [trace_path, replay_path, *prompt_paths.values(), Path(__file__),
                       REPO / "docs/cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_VALIDATION_CONTRACT.md",
                       VALIDATION_CORRIGENDUM_PATH])
        validation_input_records = [record(path) for path in sorted(allowed) if Path(path).is_file() and not is_weight(Path(path))]
        # Importing Transformers imports torch, whose Windows platform probe
        # may launch `cmd /c ver`.  Import code before the scientific audit;
        # the tokenizer snapshot load remains inside the boundary.
        from transformers import AutoTokenizer
        boundary = install_boundary(allowed=allowed, snapshot=snapshot, output=output)
        traces, _ = read_canonical_jsonl(trace_path); replay, _ = read_canonical_jsonl(replay_path)
        frozen_rows, _ = read_canonical_jsonl(input_namespace / "INPUT_LENGTHS_PRIVATE.jsonl")
        frozen_index = validate_trace_sources(traces, replay, frozen_rows)
        del frozen_rows
        templates = {name: path.read_text(encoding="utf-8") for name, path in prompt_paths.items()}
        tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False)
        result["tokenizer_loads"] = 1
        require(text_sha(tokenizer.chat_template) == canonical_run["freeze"]["runtime_config"]["tokenizer_chat_template_sha256"] and
                tokenizer.__class__.__name__ == canonical_run["freeze"]["runtime_config"]["tokenizer_class"], "tokenizer identity")
        canonical_summary = validate_run_streaming(canonical_run, selected=traces, frozen_index=frozen_index,
            tokenizer=tokenizer, templates=templates, original=original,
            capture_positions={row["position"] for row in replay})
        replay_summary = validate_run_streaming(replay_run, selected=replay, frozen_index=frozen_index,
            tokenizer=tokenizer, templates=templates, original=original,
            expected_reference=canonical_summary["captured"])
        require(replay_run["receipt"]["replay_canonical_reference_rows_decoded"] == canonical_summary["captured_rows"] == 180 * 6 and
                replay_run["receipt"]["replay_canonical_string_fields_decoded"] == canonical_summary["captured_string_fields"] and
                replay_run["receipt"]["replay_canonical_answer_fields_decoded"] == canonical_summary["captured_answer_fields"] == 180 * 6 and
                replay_run["receipt"]["replay_canonical_reference_raw_lines_scanned"] == canonical_summary["ledger_raw_lines"] == 13_500 * 6 and
                replay_run["receipt"]["replay_canonical_reference_raw_bytes_scanned"] == canonical_summary["ledger_raw_bytes"],
                "exact replay canonical-reference accounting")
        for before in validation_input_records:
            require(record(Path(before["path"])) == before, "validator input changed during validation")
        require(not boundary["denied"] and all(boundary[key] == 0 for key in ("weight_reads_denied", "outside_reads_denied",
                "outside_writes_denied", "model_weight_bytes_read", "reader_model_loads", "bge_model_loads", "nli_model_loads", "model_forward_calls")),
                "validator execution boundary")
        result.update(status="PASS_INDEPENDENT_PHI_DEVELOPMENT_RUNTIME", runtime_source_commit=args.expected_runtime_commit,
            runtime_config_sha256=canonical_run["runtime_config_sha256"], canonical_traces=13_500, replay_traces=180,
            canonical_generation_rows=canonical_summary["ledger_counts"]["generation_receipts"],
            replay_generation_rows=replay_summary["ledger_counts"]["generation_receipts"],
            canonical_repair_rows=canonical_summary["ledger_counts"]["repair_bindings"],
            replay_repair_rows=replay_summary["ledger_counts"]["repair_bindings"],
            prompt_token_reconstructions=13_500 * 3 + 180 * 3, repair_ranking_reconstructions=13_500 + 180,
            canonical_output_string_fields_read=canonical_summary["string_fields"],
            replay_output_string_fields_read=replay_summary["string_fields"],
            canonical_phi_answer_string_fields_read=canonical_summary["answer_string_fields"],
            replay_phi_answer_string_fields_read=replay_summary["answer_string_fields"],
            maximum_resident_runtime_output_traces=180,
            replay_four_ledger_byte_identity=True, canonical_input_record_audit=input_audit,
            replay_input_record_audit=replay_input_audit, model_snapshot_audit=model_snapshot_audit, execution_boundary=boundary,
            dense_vector_provenance_limitation="BGE output identity cannot be recomputed without a prohibited BGE forward; saved vectors are shape/finiteness checked and their complete retrieval consequences are independently recomputed.")
        freeze = {"status": "FROZEN_INDEPENDENT_VALIDATION", "validator_source_commit": validator_commit,
            "expected_validator_source_commit": args.expected_validator_commit,
            "runtime_source_commit": args.expected_runtime_commit, "canonical_output_name": args.canonical_output_name,
            "replay_output_name": args.replay_output_name, "validation_output_name": args.validation_output_name,
            "canonical_manifest_sha256": args.canonical_manifest_sha256,
            "replay_manifest_sha256": args.replay_manifest_sha256,
            "runtime_config_sha256": canonical_run["runtime_config_sha256"],
            "audit_boundary_start": result["audit_boundary_start"],
            "validator_corrigendum": record(VALIDATION_CORRIGENDUM_PATH),
            "inputs": validation_input_records,
            "weight_input_records": [row for row in canonical_run["freeze"]["inputs"] if is_weight(Path(row["path"]))],
            "weight_record_policy": "No weight file opened; records bound to accepted joint-preflight input records and current file sizes.",
            "scope": "Independent result-blind Phi development runtime validation only"}
        write_json(output / "EXECUTABLE_VALIDATION_FREEZE.json", freeze)
        write_json(output / "INDEPENDENT_VALIDATION.json", result)
    except Exception as exc:
        result.update(status="FAIL", error_type=type(exc).__name__, diagnostic=str(exc), traceback=traceback.format_exc(), execution_boundary=boundary)
        write_json(output / "VALIDATION_FAILURE.json", result)
    seal_output(output)
    print(result["status"], result.get("diagnostic", ""), flush=True)
    return 0 if result["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
