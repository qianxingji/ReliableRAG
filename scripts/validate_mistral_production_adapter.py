"""Independent no-model validation of the invented Mistral adapter gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np


REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
EXPECTED_KEYS = (
    "invented:a0", "invented:repair_query", "invented:a1",
    "invented:L00", "invented:L01", "invented:L10", "invented:L11",
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha(value: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(value, dtype="<f4").tobytes()).hexdigest()


def evidence(city: str, country: str) -> list[dict[str, object]]:
    facts = (
        ("Geography", f"{city} is the capital of {country}."),
        ("Rivers", "Northport is located beside the invented River Azure."),
        ("People", "Ada was born in Northport in this synthetic fixture."),
        ("Institutions", "The Example Institute is in Southville."),
        ("History", "All names in this fixture are invented except the city-country fact."),
    )
    return [
        {"rank": index, "document_id": f"fixture-{index}", "title": title, "text": text,
         "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(), "score": float(6 - index)}
        for index, (title, text) in enumerate(facts, 1)
    ]


def render(evidence_rows: list[dict]) -> tuple[str, dict]:
    headers = [f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n" for row in evidence_rows]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = 16000 - sum(len(a) + len(b) for a, b in zip(separators, headers, strict=True))
    chunks, flags = [], []
    for separator, header, row in zip(separators, headers, evidence_rows, strict=True):
        body = str(row["text"]).strip(); included = body[:remaining]; remaining -= len(included)
        chunks.append(separator + header + included); flags.append(len(included) < len(body))
    value = "".join(chunks)
    return value, {
        "context_budget_characters": 16000, "rendered_context_characters": len(value),
        "context_truncated": any(flags), "per_document_truncated": flags,
        "ordered_passed_document_ids": [row["document_id"] for row in evidence_rows],
    }


def read_jsonl(path: Path) -> list[dict]:
    result = []
    with path.open("rb") as handle:
        for raw in handle:
            require(raw.endswith(b"\n"), "PARTIAL_JSONL")
            row = json.loads(raw); require(raw == canonical(row) + b"\n", "NONCANONICAL_JSONL")
            result.append(row)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--answer-prompt", required=True, type=Path)
    parser.add_argument("--repair-prompt", required=True, type=Path)
    parser.add_argument("--namespace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    asset, namespace, output = args.asset.resolve(), args.namespace.resolve(), args.output.resolve()
    require(not output.exists(), "OUTPUT_EXISTS")
    report_path, witness_path = namespace / "REPORT.json", namespace / "FULL_VOCAB_WITNESS.npz"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(report["status"].endswith("PENDING_INDEPENDENT"), "PRODUCER_STATUS")
    require(report["revision"] == REVISION and report["operation_keys"] == list(EXPECTED_KEYS), "IDENTITY")
    require(report["project_rows_read"] == report["gold_values_read"] == report["scientific_fits"] == 0,
            "ZERO_SCIENTIFIC_ACCESS")
    require(report["witness"]["sha256"] == sha256(witness_path), "WITNESS_HASH")
    receipts = read_jsonl(namespace / "OPERATION_RECEIPTS.jsonl")
    journal = read_jsonl(namespace / "CALL_JOURNAL.jsonl")
    require([row["operation_key"] for row in receipts] == list(EXPECTED_KEYS), "RECEIPT_ORDER")
    require(len(journal) == 14 and [row["event"] for row in journal] == [value for _ in range(7) for value in ("intent", "result")],
            "JOURNAL_EVENT_ORDER")
    receipt_map = {row["operation_key"]: row for row in receipts}
    for index, row in enumerate(receipts):
        intent, result = journal[2 * index:2 * index + 2]
        require(intent["operation_key"] == result["operation_key"] == row["operation_key"], "JOURNAL_KEY")
        require(intent["input_sha256"] == row["input_sha256"], "JOURNAL_INPUT_HASH")
        require(result["result_sha256"] == object_sha(row), "JOURNAL_RESULT_HASH")

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        asset, use_fast=True, local_files_only=True, trust_remote_code=False, legacy=False,
    )
    tokenizer.pad_token = tokenizer.eos_token; tokenizer.padding_side = "left"
    answer_template = args.answer_prompt.read_text(encoding="utf-8")
    repair_template = args.repair_prompt.read_text(encoding="utf-8")
    question = "Which city is identified as the capital in the evidence?"
    e0, e1 = evidence("Paris", "France"), evidence("Lyon", "France")
    checks = 0
    for key, stage, rows in (
        ("invented:a0", "a0", e0), ("invented:repair_query", "repair_query", e0), ("invented:a1", "a1", e1),
    ):
        receipt = receipt_map[key]["receipt"]
        context, render_meta = render(rows)
        template = repair_template if stage == "repair_query" else answer_template
        user = template.format(question=question, evidence=context)
        prompt = tokenizer.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
        ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
        require(receipt["prompt_sha256"] == text_sha(prompt), "PROMPT_HASH:" + key)
        require(receipt["input_token_ids"] == ids and receipt["input_tokens"] == len(ids), "PROMPT_IDS:" + key)
        require(receipt["render"] == render_meta and 0 < len(ids) <= 8192, "RENDER_OR_GUARD:" + key)
        require(receipt["output_tokens"] == len(receipt["generated_token_ids"]) == len(receipt["chosen_log_probabilities"]),
                "GENERATION_LENGTHS:" + key)
        require(all(math.isfinite(value) for value in receipt["chosen_log_probabilities"]), "FINITE_GENERATION:" + key)
        checks += 8

    arrays = np.load(witness_path, allow_pickle=False)
    require(set(arrays.files) == set(report["witness_arrays"]), "WITNESS_ARRAY_NAMES")
    for name in arrays.files:
        value = arrays[name]
        expected = report["witness_arrays"][name]
        require(value.shape == (32768,) and value.dtype == np.dtype("float32") and np.isfinite(value).all(),
                "WITNESS_ARRAY:" + name)
        require(array_sha(value) == expected["sha256_float32_le"], "WITNESS_ARRAY_HASH:" + name)
        checks += 5
    for key in EXPECTED_KEYS[:3]:
        receipt = receipt_map[key]["receipt"]
        logits = arrays[key.replace(":", "_") + "_first_step_logits_f32"]
        token = int(receipt["generated_token_ids"][0])
        actual = float(logits[token] - np.logaddexp.reduce(logits.astype(np.float64)))
        require(int(np.argmax(logits)) == token, "GREEDY_FIRST_TOKEN:" + key)
        require(abs(actual - float(receipt["chosen_log_probabilities"][0])) <= 2e-6, "GENERATION_SOFTMAX:" + key)
        checks += 2

    likelihood_specs = (
        ("invented:L00", e0, report["answer_outputs"]["a0"]),
        ("invented:L01", e1, report["answer_outputs"]["a0"]),
        ("invented:L10", e0, report["answer_outputs"]["a1"]),
        ("invented:L11", e1, report["answer_outputs"]["a1"]),
    )
    for key, rows, answer in likelihood_specs:
        receipt = receipt_map[key]["receipt"]
        context, render_meta = render(rows)
        user = answer_template.format(question=question, evidence=context)
        prompt = tokenizer.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
        prompt_ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
        full_ids = list(tokenizer(prompt + answer, add_special_tokens=False)["input_ids"])
        require(full_ids[:len(prompt_ids)] == prompt_ids, "LIKELIHOOD_ALIGNMENT:" + key)
        target_ids = full_ids[len(prompt_ids):]
        keep = 8192 - len(target_ids); expected_prompt = prompt_ids[-keep:]
        require(receipt["prompt_token_ids"] == expected_prompt and receipt["target_token_ids"] == target_ids,
                "LIKELIHOOD_IDS:" + key)
        values = receipt["chosen_log_probabilities"]
        require(len(values) == len(target_ids) and all(math.isfinite(value) for value in values), "LIKELIHOOD_VALUES:" + key)
        require(abs(sum(values) / len(values) - receipt["mean_log_probability"]) <= 1e-12
                and min(values) == receipt["minimum_log_probability"], "LIKELIHOOD_SUMMARY:" + key)
        logits = arrays[key.replace(":", "_") + "_first_target_logits_f32"]
        actual = float(logits[target_ids[0]] - np.logaddexp.reduce(logits.astype(np.float64)))
        require(abs(actual - float(values[0])) <= 2e-6, "LIKELIHOOD_SOFTMAX:" + key)
        checks += 10
    output.parent.mkdir(parents=True, exist_ok=True)
    value = {
        "status": "PASS_INDEPENDENT_NO_MODEL_MISTRAL_PRODUCTION_ADAPTER_PREFLIGHT",
        "cas_q3_status": "NOT READY", "producer_report_sha256": sha256(report_path),
        "producer_witness_sha256": sha256(witness_path), "checks": checks,
        "model_loads": 0, "model_forwards": 0, "project_rows_read": 0,
        "gold_values_read": 0, "scientific_fits": 0,
    }
    output.write_bytes(json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(value["status"], checks, flush=True)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
