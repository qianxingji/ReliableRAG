"""Independent tokenizer-only validator for formal Mistral test a0/query."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mistral_development_acquisition_common import (
    read_jsonl,
    sha256,
)
from scripts.mistral_reader_input_freeze_common import compact_document


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_INPUT_FREEZE_MANIFEST_SHA256 = (
    "588b4d86fb6048ade1bba52731829496772d62fd522a260a7a4c60ec584586ca"
)
EXPECTED_INPUT_LEDGER_SHA256 = (
    "538970511fe517a21ef7baee4dc5eb216ce748b2c2222b3960c356a53a12f8ac"
)
EXPECTED_ASSET_MANIFEST_SHA256 = (
    "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
)
EXPECTED_TEST_PREPARATION_MANIFEST_SHA256 = (
    "7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258"
)
EXPECTED_TEST_POOL_MANIFEST_SHA256 = (
    "4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98"
)
EXPECTED_TEST_TRACE_SHA256 = (
    "87d5aff0bc77da76624b541326c523d41b00fa6c84ecefd4d6a050de66b25a29"
)
EXPECTED_TRACES = 18_000
EXPECTED_QUESTIONS = 6_000
EXPECTED_OPERATIONS = 36_000
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")


def require(value, message):
    if not value:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def object_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def read_rows(path: Path) -> list[dict]:
    rows = []
    with path.open("rb") as handle:
        for raw in handle:
            require(raw.endswith(b"\n"), "PARTIAL_JSONL")
            row = json.loads(raw)
            require(raw == canonical(row) + b"\n", "NONCANONICAL_JSONL")
            rows.append(row)
    return rows


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    require(manifest_path.is_file(), "MANIFEST_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("status") == "PASS"
            and manifest.get("exact_recursive_coverage") is True,
            "MANIFEST_STATUS")
    members = set()
    for item in manifest.get("files", []):
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace.resolve()) and path not in members,
                "MANIFEST_PATH")
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_selected_manifest(
    namespace: Path, expected_manifest_sha256: str, relatives: tuple[str, ...],
) -> list[Path]:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest_path) == expected_manifest_sha256,
            "SELECTED_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {item["path"]: item for item in value["files"]}
    require(len(entries) == len(value["files"])
            and set(relatives) <= set(entries), "SELECTED_MANIFEST_MEMBERS")
    paths = []
    for relative in relatives:
        item = entries[relative]
        path = (namespace / relative).resolve()
        require(path.is_relative_to(namespace.resolve()) and path.is_file()
                and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"],
                "SELECTED_MANIFEST_MEMBER:" + relative)
        paths.append(path)
    return [manifest_path.resolve(), *paths]


def current_manifest_member_paths(
    namespace: Path, expected_manifest_sha256: str,
) -> set[Path]:
    namespace = namespace.resolve(); manifest_path = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest_path) == expected_manifest_sha256,
            "CURRENT_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    require(value["status"] == "PASS" and value["exact_recursive_coverage"] is True,
            "CURRENT_MANIFEST_STATUS")
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


def asset_member_paths(asset: Path) -> set[Path]:
    asset = asset.resolve(); manifest_path = asset / "ASSET_MANIFEST.json"
    require(sha256(manifest_path) == EXPECTED_ASSET_MANIFEST_SHA256,
            "ASSET_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    require(value["selected_file_count"] == len(value["selected_files"]) == 14,
            "ASSET_MANIFEST_FILE_COUNT")
    for item in value["selected_files"]:
        path = (asset / item["path"]).resolve()
        require(path.is_relative_to(asset) and path not in members
                and path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "ASSET_MEMBER")
        members.add(path)
    return {manifest_path.resolve(), *members}


def validate_journal(rows: list[dict], events: list[dict]) -> None:
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_ROWS")
    completed = {}
    pending = None
    for event in events:
        if event["event"] == "intent":
            require(pending is None, "OVERLAPPING_INTENT")
            pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None
                    and event["operation_key"] == pending["operation_key"]
                    and event["input_sha256"] == pending["input_sha256"],
                    "RESUME_EVENT")
        else:
            require(event["event"] == "result" and pending is not None
                    and event["operation_key"] == pending["operation_key"],
                    "RESULT_EVENT")
            require(event["result_sha256"]
                    == object_sha(row_map[event["operation_key"]]),
                    "RESULT_HASH")
            completed[event["operation_key"]] = event
            pending = None
    require(pending is None and set(completed) == set(row_map),
            "COMPLETE_EVENTS")


def parse_answer(raw: str) -> str:
    match = re.search(r"(?im)^\s*final\s+answer\s*:\s*(.*?)\s*$", raw)
    return (match.group(1) if match else raw).strip()


def parse_query(raw: str, question: str) -> tuple[str, bool]:
    matches = [value.strip() for value in re.findall(
        r"(?im)^\s*search\s+query\s*:\s*(.*?)\s*$", raw
    ) if value.strip()]
    if matches:
        return matches[0], False
    fallback = next((line.strip() for line in reversed(raw.splitlines())
                     if line.strip()), question)
    return (fallback or question), True


def render_evidence(evidence: list[dict]) -> tuple[str, dict]:
    require(len(evidence) == 5
            and [row["rank"] for row in evidence] == [1, 2, 3, 4, 5],
            "EVIDENCE_SCHEMA")
    ids = [str(row["document_id"]) for row in evidence]
    require(len(set(ids)) == 5, "EVIDENCE_IDS")
    headers = [
        f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n"
        for row in evidence
    ]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = 16_000 - sum(
        len(separator) + len(header)
        for separator, header in zip(separators, headers, strict=True)
    )
    require(remaining >= 0, "EVIDENCE_HEADERS")
    chunks = []
    flags = []
    for separator, header, row in zip(
            separators, headers, evidence, strict=True):
        body = str(row["text"]).strip()
        included = body[:remaining]
        remaining -= len(included)
        chunks.append(separator + header + included)
        flags.append(len(included) < len(body))
    text = "".join(chunks)
    return text, {
        "context_budget_characters": 16_000,
        "rendered_context_characters": len(text),
        "context_truncated": any(flags),
        "per_document_truncated": flags,
        "ordered_passed_document_ids": ids,
    }


def validate_test_binding(traces: list[dict], frozen_rows) -> list[dict]:
    test_rows = [row for row in frozen_rows if row.get("cohort") == "test"]
    require(len(traces) == len(test_rows) == EXPECTED_TRACES,
            "TEST_TRACE_COUNT")
    cells = collections.Counter()
    groups = collections.Counter()
    identities = set()
    for position, (trace, frozen) in enumerate(zip(
            traces, test_rows, strict=True)):
        require(trace["position"] == frozen["position"] == position,
                "TEST_POSITION")
        identity = (trace["dataset"], trace["retriever"], trace["sample_id"])
        require(identity == (frozen["dataset"], frozen["retriever"],
                             frozen["sample_id"])
                and identity not in identities, "TEST_IDENTITY")
        identities.add(identity)
        require(frozen.get("role") == "test", "TEST_ROLE")
        require(object_sha(trace["original_top5_ids"])
                == frozen["original_top5_ids_sha256"],
                "ORIGINAL_TOP5_BINDING")
        cells[(identity[0], identity[1])] += 1
        groups[(identity[0], identity[2])] += 1
    require(all(cells[(dataset, retriever)] == 2_000
                for dataset in DATASETS for retriever in RETRIEVERS),
            "BALANCED_TEST_CELLS")
    require(len(groups) == EXPECTED_QUESTIONS
            and all(value == 3 for value in groups.values()),
            "TEST_QUESTION_SIBLINGS")
    return test_rows


def load_test_assets(pool_root: Path) -> dict[str, dict[str, dict]]:
    result = {}
    for dataset in DATASETS:
        document_rows = read_rows(pool_root / "pools" / f"{dataset}.jsonl")
        runtime_rows = read_rows(pool_root / "runtime" / f"{dataset}.jsonl")
        require(all(set(row) == {"content_hash", "dataset", "id", "sentences",
                                 "title"}
                    and row["dataset"] == dataset for row in document_rows),
                "TEST_DOCUMENT_SCHEMA:" + dataset)
        require(all(set(row) == {"dataset", "documents", "id", "question", "split"}
                    and row["dataset"] == dataset for row in runtime_rows),
                "TEST_RUNTIME_SCHEMA:" + dataset)
        documents = {row["id"]: row for row in document_rows}
        questions = {row["id"]: row["question"] for row in runtime_rows}
        require(len(documents) == len(document_rows)
                and len(questions) == len(runtime_rows),
                "UNIQUE_TEST_ASSET_IDS:" + dataset)
        result[dataset] = {"documents": documents, "questions": questions}
    return result


def source_pair(trace: dict, assets: dict[str, dict[str, dict]]) -> tuple[str, list[dict]]:
    dataset, sample_id = trace["dataset"], trace["sample_id"]
    require(dataset in assets and sample_id in assets[dataset]["questions"],
            "TEST_QUESTION_MEMBERSHIP")
    documents = assets[dataset]["documents"]
    ids = trace["original_top5_ids"]
    require(type(ids) is list and len(ids) == 5 and len(set(ids)) == 5
            and all(document_id in documents for document_id in ids),
            "TEST_EVIDENCE_MEMBERSHIP")
    return (assets[dataset]["questions"][sample_id],
            [compact_document(documents[document_id], rank)
             for rank, document_id in enumerate(ids, 1)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original, asset, root = (args.project_root.resolve(), args.asset.resolve(),
                             args.test_root.resolve())
    output = (args.output.resolve() if args.output else
              (root / "a0_query_validation/VALIDATION.json").resolve())
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve()
            and output
            == (root / "a0_query_validation/VALIDATION.json").resolve()
            and not output.exists(), "FIXED_ROOTS_OR_OUTPUT")
    namespace = root / "a0_query"
    validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    require(receipt.get("status")
            == "PASS_MISTRAL_TEST_A0_QUERY_PENDING_INDEPENDENT"
            and receipt.get("completed_traces") == EXPECTED_TRACES
            and receipt.get("logical_operations") == EXPECTED_OPERATIONS
            and receipt.get("project_gold_values_read") == 0
            and receipt.get("test_gold_values_read") == 0
            and receipt.get("scientific_fits") == 0
            and receipt.get("test_input_rows_read") == EXPECTED_TRACES,
            "PRODUCER_STATUS")
    rows = read_rows(namespace / "GENERATION_RECEIPTS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(rows) == EXPECTED_OPERATIONS
            and len(events) >= EXPECTED_OPERATIONS * 2, "ROW_COUNTS")
    validate_journal(rows, events)
    freeze = json.loads((root / "EXECUTABLE_FREEZE.json").read_text(
        encoding="utf-8"
    ))
    require(freeze.get("source_commit") == receipt.get("source_commit")
            and freeze.get("status")
            == "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_A0_QUERY"
            and freeze.get("expected_traces") == EXPECTED_TRACES
            and freeze.get("expected_operations") == EXPECTED_OPERATIONS
            and freeze.get("test_gold_access") == "FORBIDDEN",
            "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_INPUT")
    input_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(len(input_paths) == len(freeze["inputs"]), "UNIQUE_FROZEN_INPUTS")
    input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
    frozen_ledger = input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"
    require(sha256(input_freeze / "SHA256_MANIFEST.json")
            == EXPECTED_INPUT_FREEZE_MANIFEST_SHA256
            and sha256(frozen_ledger) == EXPECTED_INPUT_LEDGER_SHA256,
            "INPUT_FREEZE_PIN")
    preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
    pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
    trace_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
    require(sha256(trace_path) == EXPECTED_TEST_TRACE_SHA256,
            "TEST_TRACE_PIN")
    preparation_paths = validate_selected_manifest(
        preparation, EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
        ("TRACE_MANIFEST_PRIVATE.jsonl",),
    )
    pool_paths = validate_selected_manifest(
        pool_root, EXPECTED_TEST_POOL_MANIFEST_SHA256,
        tuple(f"{folder}/{dataset}.jsonl"
              for folder in ("pools", "runtime") for dataset in DATASETS),
    )
    required_inputs = {
        *{path.resolve() for path in preparation_paths},
        *{path.resolve() for path in pool_paths},
        *current_manifest_member_paths(
            input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
        ),
        *asset_member_paths(asset),
        (REPO / "scripts/run_mistral_test_a0_query.py").resolve(),
        Path(__file__).resolve(),
        (REPO / "scripts/mistral_development_acquisition_common.py").resolve(),
        (REPO / "scripts/mistral_reader_input_freeze_common.py").resolve(),
        (REPO / "src/arbitration/mistral_reader_runtime.py").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_A0_INPUT_GRAPH_AMENDMENT_2026-09-17.md").resolve(),
        (original / "prompts/baseline_v1.txt").resolve(),
        (original / "prompts/repair_missing_v1.txt").resolve(),
        Path(sys.executable).resolve(),
    }
    require(required_inputs == input_paths, "NONEXACT_FROZEN_INPUT_GRAPH")

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        asset, use_fast=True, local_files_only=True,
        trust_remote_code=False, legacy=False,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    answer_template = (original / "prompts/baseline_v1.txt").read_text(
        encoding="utf-8"
    )
    repair_template = (original / "prompts/repair_missing_v1.txt").read_text(
        encoding="utf-8"
    )
    traces = read_rows(trace_path)
    frozen = validate_test_binding(traces, read_jsonl(frozen_ledger))
    assets = load_test_assets(pool_root)
    checks = 0
    for position, (trace, frozen_row) in enumerate(zip(
            traces, frozen, strict=True)):
        dataset, retriever, sample_id = (
            trace["dataset"], trace["retriever"], trace["sample_id"]
        )
        question, evidence = source_pair(trace, assets)
        for offset, operation in enumerate(("a0", "repair_query")):
            row = rows[2 * position + offset]
            payload = row["payload"]
            key = f"{position:05d}:{operation}"
            require(row["sequence"] == 2 * position + offset
                    and row["operation_key"] == key
                    and row["operation"] == operation
                    and payload["stage"] == operation, "ROW_ORDER")
            require(payload["dataset"] == dataset
                    and payload["retriever"] == retriever
                    and payload["sample_id"] == sample_id
                    and payload["position"] == position
                    and payload["role"] == "test", "ROW_IDENTITY")
            require(payload["question_sha256"] == object_sha(question)
                    and payload["evidence_sha256"] == object_sha(evidence),
                    "SOURCE_HASHES")
            context, render = render_evidence(evidence)
            template = repair_template if operation == "repair_query" else answer_template
            user = template.format(question=question, evidence=context)
            prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": user}], tokenize=False,
                add_generation_prompt=True,
            )
            ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
            expected = frozen_row[
                "repair_query" if operation == "repair_query" else "answer"
            ]
            require(payload["render"] == render
                    and payload["prompt_sha256"]
                    == hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                    == expected["prompt_sha256"]
                    and render["context_truncated"]
                    == expected["context_truncated"]
                    and render["per_document_truncated"]
                    == expected["per_document_truncated"],
                    "PROMPT_RENDER")
            require(payload["input_tokens"] == len(ids)
                    == expected["input_tokens"]
                    and payload["input_token_ids_sha256"] == object_sha(ids)
                    == expected["input_token_ids_sha256"], "PROMPT_IDS")
            input_value = {
                "dataset": dataset, "retriever": retriever,
                "sample_id": sample_id, "position": position, "role": "test",
                "operation": operation, "question": question,
                "evidence": evidence,
            }
            require(row["input_sha256"] == object_sha(input_value),
                    "OPERATION_INPUT_HASH")
            raw = tokenizer.decode(
                payload["generated_token_ids"], skip_special_tokens=True
            ).strip()
            require(raw == payload["raw_text"]
                    and hashlib.sha256(raw.encode("utf-8")).hexdigest()
                    == payload["raw_text_sha256"], "RAW_DECODE")
            parsed, fallback = (
                parse_query(raw, question) if operation == "repair_query"
                else (parse_answer(raw), None)
            )
            require(parsed == payload["parsed_text"]
                    and fallback == payload["parser_fallback"], "PARSER")
            require(payload["output_tokens"]
                    == len(payload["generated_token_ids"])
                    == len(payload["chosen_log_probabilities"])
                    and all(math.isfinite(value)
                            for value in payload["chosen_log_probabilities"]),
                    "OUTPUT_VALUES")
            require(payload["compact_schema"]
                    == "generation-v1-reconstruct-input-from-bound-evidence",
                    "COMPACT_SCHEMA")
            checks += 28
    require(receipt.get("generation_receipts") == {
        "path": str((namespace / "GENERATION_RECEIPTS.jsonl").resolve()),
        "size_bytes": (namespace / "GENERATION_RECEIPTS.jsonl").stat().st_size,
        "sha256": sha256(namespace / "GENERATION_RECEIPTS.jsonl"),
    }, "GENERATION_FILE_BINDING")
    result = {
        "status": "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "generation_receipts_sha256": sha256(
            namespace / "GENERATION_RECEIPTS.jsonl"
        ),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "validated_traces": EXPECTED_TRACES,
        "source_prompts_reconstructed": EXPECTED_OPERATIONS,
        "model_loads": 0, "model_forwards": 0,
        "gold_values_read": 0, "test_gold_values_read": 0,
        "scientific_fits": 0, "test_input_rows_read": EXPECTED_TRACES,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2,
                                  allow_nan=False).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
