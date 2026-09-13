"""Independent tokenizer/logit validation of the invented-only Phi preflight."""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import subprocess
import sys
from pathlib import Path

from scripts.phi_reader_preflight_common import (
    OUT,
    PHI_MODEL,
    PHI_RELATIVE,
    PHI_REVISION,
    REPO,
    configure_environment,
    digest,
    invented_evidence_rows,
    load,
    object_sha,
    parse_answer,
    parse_query,
    record,
    render_evidence,
    render_generation_evidence,
    require,
    seal,
    text_sha,
    validate_logit_witness,
    verify_namespace,
    write_json,
)


VALIDATION = REPO / "outputs/cas_q2/phi_reader_gpu_preflight_validation_v2"
PRODUCER_COMMIT = "b9680dba8845d7ad077acd884ff8b5166536b009"


class Checks:
    def __init__(self):
        self.count = 0

    def require(self, condition, message):
        self.count += 1
        require(condition, "independent: " + message)

    def exact(self, actual, expected, message):
        self.require(actual == expected, message)


def prepare(tokenizer, template: str, item: dict) -> dict:
    context, context_cut, _ = render_evidence(item["evidence"])
    user = template.format(question=item["question"], evidence=context)
    prompt = tokenizer.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
    prompt_ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    full_ids = list(tokenizer(prompt + item["answer"], add_special_tokens=False)["input_ids"])
    require(full_ids[: len(prompt_ids)] == prompt_ids, "independent prompt/answer alignment")
    answer_ids = full_ids[len(prompt_ids) :]
    require(bool(answer_ids), "independent nonempty answer tokens")
    token_cut = len(prompt_ids) + len(answer_ids) > 8192
    if token_cut:
        prompt_ids = prompt_ids[-(8192 - len(answer_ids)) :]
    evidence_hash = object_sha([{"id": row["document_id"], "content_hash": row["content_hash"]} for row in item["evidence"]])
    payload = {"model_revision": PHI_REVISION, "prompt_sha256": text_sha(prompt), "ordered_evidence_hash": evidence_hash,
        "answer_sha256": text_sha(item["answer"]), "scorer_version": "mars-answer-token-v4-answer-position-only-softmax"}
    return {"prompt_ids": prompt_ids, "answer_ids": answer_ids, "input_ids": prompt_ids + answer_ids,
        "prompt_sha256": text_sha(prompt), "evidence_ids": tuple(row["document_id"] for row in item["evidence"]),
        "evidence_hash": evidence_hash, "answer_sha256": text_sha(item["answer"]), "cache_key": object_sha(payload),
        "truncation": bool(context_cut or token_cut)}


def install_tokenizer_only_boundary(snapshot: Path, output: Path) -> dict:
    receipt = {"weight_reads_denied": 0, "writes_outside_output_denied": 0}

    def hook(event, args):
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request", "subprocess.Popen", "os.system"}:
            raise RuntimeError("independent validator network/process boundary")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing and not path.is_relative_to(output.resolve()):
            receipt["writes_outside_output_denied"] += 1
            raise RuntimeError("independent validator write outside output")
        if not writing and path.is_relative_to(snapshot.resolve()) and path.suffix in {".safetensors", ".bin"}:
            receipt["weight_reads_denied"] += 1
            raise RuntimeError("independent validator weight read")

    sys.addaudithook(hook)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    original = args.project_root.resolve()
    require(not VALIDATION.exists(), "single-use Phi validation namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit validator first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    paths = verify_namespace(OUT)
    receipt = load(OUT / "BUILD_RECEIPT.json")
    require(receipt["status"] == "PASS_PHI_READER_GPU_INVENTED_ONLY" and receipt["source_commit"] == PRODUCER_COMMIT,
        "accepted immutable producer commit")
    VALIDATION.mkdir(parents=True, exist_ok=False)
    configure_environment(VALIDATION)
    # Transformers imports torch lazily, and Python's Windows platform probe may
    # open NUL via a subprocess during that import. Import the library before the
    # tokenizer IO boundary; from_pretrained and every tokenizer file read stay
    # inside it. No model class or weights are loaded.
    from transformers import AutoTokenizer

    boundary = install_tokenizer_only_boundary(original / PHI_RELATIVE, VALIDATION)
    tokenizer = AutoTokenizer.from_pretrained(PHI_MODEL, revision=PHI_REVISION,
        cache_dir=original / "data/models/huggingface", local_files_only=True, trust_remote_code=False)
    answer_template = (original / "prompts/baseline_v1.txt").read_text(encoding="utf-8")
    repair_template = (original / "prompts/repair_missing_v1.txt").read_text(encoding="utf-8")
    generation = load(OUT / "GENERATION_WITNESSES.json")
    likelihood = load(OUT / "LIKELIHOOD_WITNESSES.json")
    checks = Checks()
    checks.exact(generation["invented_evidence_hashes"]["short_rows"], object_sha(invented_evidence_rows()), "short evidence hash")
    checks.exact(generation["invented_evidence_hashes"]["long_rows"], object_sha(invented_evidence_rows(long=True)), "long evidence hash")

    for observation in generation["observations"]:
        evidence = invented_evidence_rows(long=observation["long_evidence"])
        context, context_cut, per_doc = render_generation_evidence(evidence)
        template = answer_template if observation["kind"] == "answer" else repair_template
        user = template.format(question="In the invented toy scene, what color is the paper cog?", evidence=context)
        prompt = tokenizer.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
        # Native generation tokenizes the rendered chat with the tokenizer's
        # default special-token behavior; likelihood preparation is separate.
        input_ids = list(tokenizer(prompt, add_special_tokens=True)["input_ids"])
        capture = observation["capture"]
        checks.exact(capture["prompt_sha256"], text_sha(prompt), "generation prompt hash")
        checks.exact(capture["input_token_ids"], input_ids, "generation prompt tokens")
        checks.exact(capture["attention_mask"], [1] * len(input_ids), "generation mask")
        decoded = tokenizer.batch_decode([capture["generated_token_ids"]], skip_special_tokens=True)[0].strip()
        checks.exact(capture["raw_text"], decoded, "generated token decode")
        checks.exact(observation["result"]["raw_text"], decoded, "result/capture raw text")
        expected_render = {"text": context, "context_truncated": context_cut, "context_budget_characters": 16000,
            "ordered_passed_document_ids": [row["document_id"] for row in evidence], "per_document_truncated": per_doc}
        checks.exact(capture["render"], expected_render, "independent evidence rendering")
        checks.exact(capture["input_tokens"], len(input_ids), "generation input count")
        checks.exact(capture["native_output_score_steps"], len(capture["generated_token_ids"]), "generation score steps")
        if observation["kind"] == "answer":
            checks.exact(observation["result"]["parsed_text"], parse_answer(decoded), "answer parsing")
        else:
            query, fallback = parse_query(decoded, "In the invented toy scene, what color is the paper cog?")
            checks.exact(observation["result"]["search_query"], query, "repair query parsing")
            checks.exact(observation["result"]["parser_fallback"], fallback, "repair fallback")
    checks.exact(generation["observations"][0]["capture"], generation["observations"][1]["capture"], "exact repeated generation")

    short_item = {"question": "In the invented toy scene, what color is the paper cog?", "answer": "silver", "evidence": invented_evidence_rows()}
    long_item = {"question": short_item["question"], "answer": "silver", "evidence": invented_evidence_rows(long=True)}
    prepared_by_key = {}
    for row, item in zip(likelihood["scored"], (short_item, short_item, long_item), strict=True):
        prepared = prepare(tokenizer, answer_template, item)
        expected = dict(prepared)
        expected["evidence_ids"] = list(expected["evidence_ids"])
        checks.exact(row["prepared"], expected, "independent likelihood preparation")
        prepared_by_key[prepared["cache_key"]] = prepared
    checks.exact(likelihood["scored"][1]["result"]["cache_hit"], True, "second short likelihood cache hit")
    checks.exact(likelihood["scored"][1]["result"]["latency_seconds"], 0.0, "cache latency")
    checks.exact(likelihood["scored"][0]["result"]["cache_key"], likelihood["scored"][1]["result"]["cache_key"], "cache key repeat")

    witness_by_key = {}
    for witness in likelihood["forward_witnesses"]:
        validate_logit_witness(witness)
        prepared = prepared_by_key[witness["cache_key"]]
        checks.exact(witness["input_token_ids"], prepared["input_ids"], "witness input IDs")
        checks.exact(witness["answer_token_ids"], prepared["answer_ids"], "witness answer IDs")
        checks.exact(witness["answer_prediction_positions"], list(range(len(prepared["prompt_ids"]) - 1, len(prepared["input_ids"]) - 1)), "answer positions")
        checks.exact(witness["model_revision"], PHI_REVISION, "witness revision")
        values = witness["token_log_probabilities"]
        result = next(row["result"] for row in likelihood["scored"] if row["result"]["cache_key"] == witness["cache_key"] and not row["result"]["cache_hit"])
        checks.require(abs(result["sum_log_probability"] - sum(values)) <= 1e-12, "likelihood sum")
        checks.require(abs(result["mean_log_probability"] - sum(values) / len(values)) <= 1e-12, "likelihood mean")
        checks.exact(result["minimum_log_probability"], min(values), "likelihood minimum")
        witness_by_key[witness["cache_key"]] = witness
    checks.exact(len(witness_by_key), 2, "two unique likelihood forwards")
    checks.exact(len(likelihood["scored"][-1]["prepared"]["input_ids"]), 8192, "long likelihood length")

    availability = load(REPO / "docs/cas_q2/P0_3_READER_AXIS_AVAILABILITY_RESULTS.json")
    shard_pins = availability["reader"]["weight_shards"]
    for row in load(OUT / "EXECUTABLE_FREEZE.json")["inputs"]:
        path = Path(row["path"])
        if path.suffix == ".safetensors":
            checks.exact({"size_bytes": row["size_bytes"], "sha256": row["sha256"]}, shard_pins[path.name], "weight pin from accepted read-only audit")
        else:
            checks.exact(record(path), row, "producer input remains unchanged")
    checks.exact(boundary, {"weight_reads_denied": 0, "writes_outside_output_denied": 0}, "tokenizer-only boundary")
    validator_inputs = [record(path) for path in (
        REPO / "scripts/validate_phi_reader_axis_preflight_v2.py",
        REPO / "scripts/phi_reader_preflight_common.py",
        REPO / "docs/cas_q2/PHI_READER_PREFLIGHT_EXECUTION_CONTRACT.md",
        REPO / "docs/cas_q2/PHI_READER_PREFLIGHT_VALIDATOR_IMPORT_AMENDMENT_V2.md",
    )]
    result = {
        "status": "PASS_INDEPENDENT_PHI_READER_PREFLIGHT",
        "cas_q2_status": "NOT READY",
        "source_commit": commit,
        "producer_source_commit": PRODUCER_COMMIT,
        "producer_manifest_sha256": digest(OUT / "SHA256_MANIFEST.json"),
        "checks": checks.count,
        "generation_observations": 4,
        "likelihood_forwards": 2,
        "likelihood_cache_hits": 1,
        "tokenizer_only": True,
        "model_loads": 0,
        "model_forward_calls": 0,
        "benchmark_rows_read": 0,
        "scientific_fit_calls": 0,
        "gold_reads": 0,
        "boundary": boundary,
        "validator_inputs": validator_inputs,
        "scope": "Invented compatibility only; benchmark implementation/input freeze still required",
        "preserved_predecessor_failure": "outputs/cas_q2/phi_reader_gpu_preflight_validation_v1",
    }
    write_json(VALIDATION / "INDEPENDENT_VALIDATION.json", result)
    seal(VALIDATION)
    print(result["status"], checks.count)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
