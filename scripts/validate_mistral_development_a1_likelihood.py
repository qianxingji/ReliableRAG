"""Independent no-model reconstruction of Mistral development a1/likelihoods."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_mistral_development_a0_query import (
    load_original_native, object_sha, parse_answer, read_rows, require, sha256,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_TRACES = 13_500
CELLS = ("L00", "L01", "L10", "L11")
EXPECTED_OPERATIONS = EXPECTED_TRACES * 5
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def evidence_rows(evidence) -> list[dict]:
    return [row.as_private_dict() for row in evidence]


def render_evidence(evidence: list[dict]) -> tuple[str, dict]:
    require(len(evidence) == 5 and [row["rank"] for row in evidence] == [1, 2, 3, 4, 5],
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
    chunks, flags = [], []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip(); included = body[:remaining]
        remaining -= len(included); chunks.append(separator + header + included)
        flags.append(len(included) < len(body))
    rendered = "".join(chunks)
    return rendered, {
        "context_budget_characters": 16_000,
        "rendered_context_characters": len(rendered),
        "context_truncated": any(flags),
        "per_document_truncated": flags,
        "ordered_passed_document_ids": ids,
    }


def render_prompt(tokenizer, template: str, question: str,
                  evidence: list[dict]) -> tuple[str, dict]:
    context, render = render_evidence(evidence)
    user = template.format(question=question, evidence=context)
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}], tokenize=False,
        add_generation_prompt=True,
    )
    require(isinstance(prompt, str) and prompt, "EMPTY_PROMPT")
    return prompt, render


def aligned_ids(tokenizer, prompt: str, answer: str) -> tuple[list[int], list[int]]:
    prompt_ids = [int(value) for value in tokenizer(prompt, add_special_tokens=False)["input_ids"]]
    full_ids = [int(value) for value in tokenizer(prompt + answer, add_special_tokens=False)["input_ids"]]
    require(full_ids[:len(prompt_ids)] == prompt_ids, "PROMPT_TARGET_PREFIX")
    target_ids = full_ids[len(prompt_ids):]
    require(bool(target_ids), "EMPTY_TARGET")
    return prompt_ids, target_ids


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
            "REPAIR_BINDING")
    return e1


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members, "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_journal(rows: list[dict], events: list[dict]) -> int:
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_ROWS")
    pending = None; completed = {}; recoveries = 0
    for event in events:
        if event["event"] == "intent":
            require(pending is None, "OVERLAPPING_INTENT"); pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None and event["operation_key"] == pending["operation_key"]
                    and event["input_sha256"] == pending["input_sha256"], "RESUME_EVENT")
            recoveries += 1
        else:
            require(event["event"] == "result" and pending is not None
                    and event["operation_key"] == pending["operation_key"], "RESULT_EVENT")
            row = row_map[event["operation_key"]]
            require(event["operation"] == pending["operation"] == row["operation"]
                    and event["result_sha256"] == object_sha(row), "RESULT_HASH")
            completed[event["operation_key"]] = event; pending = None
    require(pending is None and set(completed) == set(row_map), "COMPLETE_EVENTS")
    return recoveries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original, asset = args.project_root.resolve(), args.asset.resolve()
    root, output = args.root.resolve(), args.output.resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve() and not output.exists(),
            "FIXED_ROOT_OR_OUTPUT")
    namespace = root / "a1_likelihood"; validate_manifest(namespace)
    a0_stage, repair_stage = root / "a0_query", root / "repair"
    validate_manifest(a0_stage); validate_manifest(repair_stage)
    a0_validation = json.loads((root / "a0_query_validation/VALIDATION.json").read_text(encoding="utf-8"))
    repair_validation = json.loads((root / "repair_validation/VALIDATION.json").read_text(encoding="utf-8"))
    require(a0_validation["status"] == "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY"
            and a0_validation["producer_receipt_sha256"] == sha256(a0_stage / "STAGE_RECEIPT.json")
            and a0_validation["generation_receipts_sha256"] == sha256(a0_stage / "GENERATION_RECEIPTS.jsonl")
            and a0_validation["call_journal_sha256"] == sha256(a0_stage / "CALL_JOURNAL.jsonl"),
            "A0_VALIDATION_BINDING")
    require(repair_validation["status"] == "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_REPAIR"
            and repair_validation["producer_receipt_sha256"] == sha256(repair_stage / "STAGE_RECEIPT.json")
            and repair_validation["repair_bindings_sha256"] == sha256(repair_stage / "REPAIR_BINDINGS.jsonl")
            and repair_validation["call_journal_sha256"] == sha256(repair_stage / "CALL_JOURNAL.jsonl"),
            "REPAIR_VALIDATION_BINDING")
    stage = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(stage["status"] == "PASS_MISTRAL_DEVELOPMENT_A1_LIKELIHOOD_PENDING_INDEPENDENT"
            and stage["completed_traces"] == EXPECTED_TRACES
            and stage["logical_operations"] == EXPECTED_OPERATIONS, "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    require(freeze["source_commit"] == stage["source_commit"]
            and freeze["expected_operations"] == EXPECTED_OPERATIONS, "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"],
                "FROZEN_INPUT")
    rows = read_rows(namespace / "MODEL_RECEIPTS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(rows) == EXPECTED_OPERATIONS, "MODEL_ROW_COUNT")
    recoveries = validate_journal(rows, events)
    a0_rows = read_rows(root / "a0_query/GENERATION_RECEIPTS.jsonl")
    a0_map = {row["payload"]["position"]: row["payload"]
              for row in a0_rows if row["operation"] == "a0"}
    repair_rows = read_rows(root / "repair/REPAIR_BINDINGS.jsonl")
    repair_map = {row["payload"]["position"]: row["payload"] for row in repair_rows}
    require(len(a0_map) == len(repair_map) == EXPECTED_TRACES, "PRIOR_ROW_COUNTS")

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        asset, use_fast=True, local_files_only=True, trust_remote_code=False, legacy=False,
    )
    tokenizer.pad_token = tokenizer.eos_token; tokenizer.padding_side = "left"
    require(tokenizer.is_fast and tokenizer.vocab_size == 32768, "TOKENIZER_IDENTITY")
    answer_template = (original / "prompts/baseline_v1.txt").read_text(encoding="utf-8")
    runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    traces = read_rows(runtime_root / "trace_manifest.jsonl")
    frozen_rows = [row for row in read_rows(
        REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl"
    ) if row.get("cohort") == "development"]
    require(len(traces) == len(frozen_rows) == EXPECTED_TRACES, "SOURCE_COUNTS")
    loader, native = load_original_native(original)

    class NoEmbeddingBackend:
        dimension = 768
        def encode_queries(self, *_args, **_kwargs): raise RuntimeError("BGE_FORBIDDEN")
        def encode_documents(self, *_args, **_kwargs): raise RuntimeError("DOCUMENT_EMBEDDING_FORBIDDEN")

    backend = NoEmbeddingBackend(); current_dataset = None; data = None; checks = 0
    for position, (trace, frozen) in enumerate(zip(traces, frozen_rows, strict=True)):
        require(trace["position"] == frozen["position"] == position, "POSITION")
        dataset, retriever, sample_id = trace["dataset"], trace["retriever"], trace["sample_id"]
        require((dataset, retriever, sample_id)
                == (frozen["dataset"], frozen["retriever"], frozen["sample_id"]), "IDENTITY")
        if dataset != current_dataset:
            data = loader.restore_dataset(dataset, native, backend); current_dataset = dataset
        question = data["questions"][sample_id]
        e0 = loader.original_evidence(trace, data, native)
        e1 = reconstruct_e1(native, e0, repair_map[position], data)
        private_e0, private_e1 = evidence_rows(e0), evidence_rows(e1)
        a0_payload = a0_map[position]
        a0_raw = tokenizer.decode(a0_payload["generated_token_ids"], skip_special_tokens=True).strip()
        a0 = parse_answer(a0_raw)
        require(a0 == a0_payload["parsed_text"], "A0_PARSE")

        a1_row = rows[5 * position]; a1_payload = a1_row["payload"]
        require(a1_row["sequence"] == 5 * position
                and a1_row["operation_key"] == f"{position:05d}:a1"
                and a1_row["operation"] == "a1" and a1_payload["stage"] == "a1", "A1_ORDER")
        require(a1_payload["dataset"] == dataset and a1_payload["retriever"] == retriever
                and a1_payload["sample_id"] == sample_id and a1_payload["position"] == position
                and a1_payload["role"] == frozen["role"], "A1_IDENTITY")
        prompt, render = render_prompt(tokenizer, answer_template, question, private_e1)
        prompt_ids = [int(value) for value in tokenizer(prompt, add_special_tokens=False)["input_ids"]]
        require(len(prompt_ids) <= 8192 and a1_payload["render"] == render
                and a1_payload["prompt_sha256"] == text_sha(prompt)
                and a1_payload["input_tokens"] == len(prompt_ids)
                and a1_payload["input_token_ids_sha256"] == object_sha(prompt_ids), "A1_PROMPT")
        require(a1_payload["question_sha256"] == object_sha(question)
                and a1_payload["evidence_sha256"] == object_sha(private_e1), "A1_SOURCE_HASH")
        a1_raw = tokenizer.decode(a1_payload["generated_token_ids"], skip_special_tokens=True).strip()
        a1 = parse_answer(a1_raw)
        require(a1_raw == a1_payload["raw_text"] and a1 == a1_payload["parsed_text"]
                and text_sha(a1_raw) == a1_payload["raw_text_sha256"]
                and text_sha(a1) == a1_payload["parsed_text_sha256"], "A1_PARSE")
        require(a1_payload["output_tokens"] == len(a1_payload["generated_token_ids"])
                == len(a1_payload["chosen_log_probabilities"])
                and all(math.isfinite(value) for value in a1_payload["chosen_log_probabilities"])
                and a1_payload["reader"] == "mistral_nf4" and a1_payload["revision"] == REVISION
                and a1_payload["compact_schema"] == "generation-v1-reconstruct-input-from-bound-evidence",
                "A1_OUTPUT")
        a1_input = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                    "position": position, "role": frozen["role"], "operation": "a1",
                    "question": question, "evidence": private_e1}
        require(a1_row["input_sha256"] == object_sha(a1_input), "A1_INPUT_HASH")
        branches = {
            "L00": (private_e0, a0), "L01": (private_e1, a0),
            "L10": (private_e0, a1), "L11": (private_e1, a1),
        }
        for offset, cell in enumerate(CELLS, start=1):
            row = rows[5 * position + offset]; payload = row["payload"]
            evidence, answer = branches[cell]
            require(row["sequence"] == 5 * position + offset
                    and row["operation_key"] == f"{position:05d}:{cell}"
                    and row["operation"] == "likelihood" and payload["cell"] == cell,
                    "LIKELIHOOD_ORDER")
            require(payload["dataset"] == dataset and payload["retriever"] == retriever
                    and payload["sample_id"] == sample_id and payload["position"] == position
                    and payload["role"] == frozen["role"], "LIKELIHOOD_IDENTITY")
            likelihood_prompt, likelihood_render = render_prompt(
                tokenizer, answer_template, question, evidence,
            )
            original_prompt_ids, target_ids = aligned_ids(tokenizer, likelihood_prompt, answer)
            require(len(target_ids) < 8192, "TARGET_GUARD")
            keep = 8192 - len(target_ids)
            token_truncated = len(original_prompt_ids) > keep
            kept_prompt_ids = original_prompt_ids[-keep:] if token_truncated else original_prompt_ids
            require(bool(kept_prompt_ids) and len(kept_prompt_ids) + len(target_ids) <= 8192,
                    "LIKELIHOOD_ADMISSION")
            require(payload["render"] == likelihood_render
                    and payload["prompt_sha256"] == text_sha(likelihood_prompt)
                    and payload["prompt_token_ids_sha256"] == object_sha(kept_prompt_ids)
                    and payload["target_token_ids_sha256"] == object_sha(target_ids),
                    "LIKELIHOOD_PROMPT_HASHES")
            require(payload["original_prompt_tokens"] == len(original_prompt_ids)
                    and payload["prompt_tokens"] == len(kept_prompt_ids)
                    and payload["target_tokens"] == len(target_ids)
                    and payload["total_tokens"] == len(kept_prompt_ids) + len(target_ids)
                    and payload["token_truncated"] is token_truncated, "LIKELIHOOD_LENGTHS")
            values = payload["chosen_log_probabilities"]
            require(len(values) == len(target_ids) and all(math.isfinite(value) for value in values)
                    and payload["mean_log_probability"] == float(sum(values) / len(values))
                    and payload["minimum_log_probability"] == float(min(values)),
                    "LIKELIHOOD_VALUES")
            require(payload["question_sha256"] == object_sha(question)
                    and payload["evidence_sha256"] == object_sha(evidence)
                    and payload["answer_sha256"] == text_sha(answer)
                    and payload["reader"] == "mistral_nf4" and payload["revision"] == REVISION
                    and payload["model_forward_calls"] == 1
                    and payload["compact_schema"] == "likelihood-v1-reconstruct-prompt-and-target-from-bound-branch",
                    "LIKELIHOOD_METADATA")
            input_value = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                           "position": position, "role": frozen["role"],
                           "operation": "likelihood", "cell": cell, "question": question,
                           "evidence": evidence, "answer": answer}
            require(row["input_sha256"] == object_sha(input_value), "LIKELIHOOD_INPUT_HASH")
        checks += 112
    require(stage["gold_values_read"] == stage["scientific_fits"] == stage["test_rows_read"] == 0
            and stage["bge_model_loads"] == stage["nli_model_loads"] == 0, "ZERO_FORBIDDEN_ACCESS")
    result = {
        "status": "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_A1_LIKELIHOOD",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "model_receipts_sha256": sha256(namespace / "MODEL_RECEIPTS.jsonl"),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "recovery_events": recoveries, "source_prompts_reconstructed": EXPECTED_OPERATIONS,
        "model_loads": 0, "model_forwards": 0, "gold_values_read": 0,
        "scientific_fits": 0, "test_rows_read": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
