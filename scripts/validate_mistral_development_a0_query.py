"""Independent no-model validator for formal Mistral development a0/query."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import types


EXPECTED_TRACES = 13_500
EXPECTED_OPERATIONS = 27_000
REPO = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition: raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def object_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""): digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict]:
    result = []
    with path.open("rb") as handle:
        for raw in handle:
            require(raw.endswith(b"\n"), "PARTIAL_JSONL")
            row = json.loads(raw); require(raw == canonical(row) + b"\n", "NONCANONICAL_JSONL")
            result.append(row)
    return result


def _import_file(name: str, path: Path):
    module = types.ModuleType(name); module.__file__ = str(path); module.__package__ = ""
    sys.modules[name] = module
    payload = path.read_bytes()
    exec(compile(payload.decode("utf-8-sig"), str(path), "exec"), module.__dict__)
    return module


def load_original_native(original: Path):
    frozen = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    support = _import_file("independent_runtime_support", frozen / "runtime_support.py")
    # native_runtime imports the literal module name.
    sys.modules["runtime_support"] = support
    require(support.ROOT == original, "ORIGINAL_RUNTIME_ROOT")
    retrieval = _import_file(
        "independent_retrieval_support",
        original / "outputs/daa_v2_fresh_v1/retrieval_freeze/retrieval_support.py",
    )
    sys.modules["retrieval_support"] = retrieval
    loader = _import_file("independent_mistral_native_runtime", frozen / "native_runtime.py")
    loader.import_file = _import_file
    native, _nodes, _boundary = loader.accepted()
    return loader, native


def parse_answer(raw: str) -> str:
    match = re.search(r"(?im)^\s*final\s+answer\s*:\s*(.*?)\s*$", raw)
    return (match.group(1) if match else raw).strip()


def parse_query(raw: str, question: str) -> tuple[str, bool]:
    matches = [value.strip() for value in re.findall(
        r"(?im)^\s*search\s+query\s*:\s*(.*?)\s*$", raw
    ) if value.strip()]
    if matches: return matches[0], False
    fallback = next((line.strip() for line in reversed(raw.splitlines()) if line.strip()), question)
    return (fallback or question), True


def render_evidence(evidence: list[dict]) -> tuple[str, dict]:
    require(len(evidence) == 5, "EVIDENCE_COUNT")
    headers = [f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n" for row in evidence]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = 16_000 - sum(len(a) + len(b) for a, b in zip(separators, headers, strict=True))
    chunks, flags = [], []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip(); included = body[:remaining]; remaining -= len(included)
        chunks.append(separator + header + included); flags.append(len(included) < len(body))
    text = "".join(chunks)
    return text, {
        "context_budget_characters": 16_000, "rendered_context_characters": len(text),
        "context_truncated": any(flags), "per_document_truncated": flags,
        "ordered_passed_document_ids": [row["document_id"] for row in evidence],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--namespace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original, namespace, output = args.project_root.resolve(), args.namespace.resolve(), args.output.resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve(), "FIXED_PROJECT_ROOT")
    require(not output.exists(), "OUTPUT_EXISTS")
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(receipt["status"].endswith("PENDING_INDEPENDENT") and receipt["completed_traces"] == EXPECTED_TRACES,
            "PRODUCER_STATUS")
    rows = read_rows(namespace / "GENERATION_RECEIPTS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(rows) == EXPECTED_OPERATIONS and len(events) >= EXPECTED_OPERATIONS * 2, "ROW_COUNTS")
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_ROWS")
    completed = {}; pending = None
    for event in events:
        if event["event"] == "intent":
            require(pending is None, "OVERLAPPING_INTENT"); pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None and event["operation_key"] == pending["operation_key"], "RESUME_EVENT")
        else:
            require(event["event"] == "result" and pending is not None
                    and event["operation_key"] == pending["operation_key"], "RESULT_EVENT")
            require(event["result_sha256"] == object_sha(row_map[event["operation_key"]]), "RESULT_HASH")
            completed[event["operation_key"]] = event; pending = None
    require(pending is None and set(completed) == set(row_map), "COMPLETE_EVENTS")
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    members = set()
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members, "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"], "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")
    freeze = json.loads((namespace.parent / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == receipt["source_commit"] and freeze["expected_operations"] == EXPECTED_OPERATIONS,
            "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"], "FROZEN_INPUT")

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        args.asset.resolve(), use_fast=True, local_files_only=True,
        trust_remote_code=False, legacy=False,
    )
    tokenizer.pad_token = tokenizer.eos_token; tokenizer.padding_side = "left"
    answer_template = (original / "prompts/baseline_v1.txt").read_text(encoding="utf-8")
    repair_template = (original / "prompts/repair_missing_v1.txt").read_text(encoding="utf-8")
    runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    traces = read_rows(runtime_root / "trace_manifest.jsonl")
    frozen_rows = [row for row in read_rows(REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl")
                   if row.get("cohort") == "development"]
    require(len(traces) == len(frozen_rows) == EXPECTED_TRACES, "SOURCE_COUNTS")
    loader, native = load_original_native(original)
    class NoEmbeddingBackend:
        dimension = 768
        def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")
        def encode_documents(self, *_args, **_kwargs): raise RuntimeError("DOCUMENT_EMBEDDING_FORBIDDEN")
    backend = NoEmbeddingBackend(); current_dataset = None; data = None; checks = 0
    for position, (trace, frozen) in enumerate(zip(traces, frozen_rows, strict=True)):
        require(trace["position"] == frozen["position"] == position, "SOURCE_POSITION")
        dataset, retriever, sample_id = trace["dataset"], trace["retriever"], trace["sample_id"]
        require((dataset, retriever, sample_id) == (frozen["dataset"], frozen["retriever"], frozen["sample_id"]),
                "SOURCE_IDENTITY")
        if dataset != current_dataset:
            data = loader.restore_dataset(dataset, native, backend); current_dataset = dataset
        question = data["questions"][sample_id]
        e0 = loader.original_evidence(trace, data, native)
        private_e0 = [item.as_private_dict() for item in e0]
        for offset, operation in enumerate(("a0", "repair_query")):
            row = rows[2 * position + offset]; payload = row["payload"]
            key = f"{position:05d}:{operation}"
            require(row["sequence"] == 2 * position + offset and row["operation_key"] == key
                    and row["operation"] == operation and payload["stage"] == operation, "ROW_ORDER")
            require(payload["dataset"] == dataset and payload["retriever"] == retriever
                    and payload["sample_id"] == sample_id and payload["position"] == position
                    and payload["role"] == frozen["role"], "ROW_IDENTITY")
            require(payload["question_sha256"] == object_sha(question)
                    and payload["evidence_sha256"] == object_sha(private_e0), "SOURCE_HASHES")
            context, render = render_evidence(private_e0)
            template = repair_template if operation == "repair_query" else answer_template
            user = template.format(question=question, evidence=context)
            prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True,
            )
            ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
            expected = frozen["repair_query" if operation == "repair_query" else "answer"]
            require(payload["render"] == render and payload["prompt_sha256"] == hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "PROMPT_RENDER")
            require(payload["input_tokens"] == len(ids) == expected["input_tokens"]
                    and payload["input_token_ids_sha256"] == object_sha(ids) == expected["input_token_ids_sha256"],
                    "PROMPT_IDS")
            input_value = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                           "position": position, "role": frozen["role"], "operation": operation,
                           "question": question, "evidence": private_e0}
            require(row["input_sha256"] == object_sha(input_value), "OPERATION_INPUT_HASH")
            raw = tokenizer.decode(payload["generated_token_ids"], skip_special_tokens=True).strip()
            require(raw == payload["raw_text"] and hashlib.sha256(raw.encode("utf-8")).hexdigest() == payload["raw_text_sha256"],
                    "RAW_DECODE")
            parsed, fallback = (parse_query(raw, question) if operation == "repair_query"
                                else (parse_answer(raw), None))
            require(parsed == payload["parsed_text"] and fallback == payload["parser_fallback"], "PARSER")
            require(payload["output_tokens"] == len(payload["generated_token_ids"]) == len(payload["chosen_log_probabilities"]),
                    "OUTPUT_LENGTHS")
            require(all(math.isfinite(value) for value in payload["chosen_log_probabilities"]), "FINITE_VALUES")
            require(payload["compact_schema"] == "generation-v1-reconstruct-input-from-bound-evidence", "COMPACT_SCHEMA")
            checks += 28
    require(receipt["project_gold_values_read"] == receipt["scientific_fits"] == receipt["test_rows_read"] == 0,
            "ZERO_FORBIDDEN_ACCESS")
    result = {
        "status": "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "generation_receipts_sha256": sha256(namespace / "GENERATION_RECEIPTS.jsonl"),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "model_loads": 0, "model_forwards": 0, "gold_values_read": 0,
        "scientific_fits": 0, "test_rows_read": 0,
        "source_prompts_reconstructed": EXPECTED_OPERATIONS,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
