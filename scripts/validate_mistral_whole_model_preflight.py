"""Validate saved Mistral whole-model witnesses without loading the model."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys


REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
ASSET_MANIFEST_SHA256 = "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
TOKENIZER_REPORT_SHA256 = "47f3f2f04ed324e7be8051a594224bfdca8fc244133c14d5aeef028db24d1b5a"
GIB = 1024 ** 3
EXPECTED_LINEAR4BIT_MODULES = {
    f"model.layers.{layer}.{branch}.{projection}"
    for layer in range(32)
    for branch, projections in (
        ("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")),
        ("mlp", ("gate_proj", "up_proj", "down_proj")),
    )
    for projection in projections
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ids_sha256(values) -> str:
    import numpy as np

    return hashlib.sha256(np.asarray(values, dtype="<i4").tobytes()).hexdigest()


def array_sha256(values) -> str:
    import numpy as np

    return hashlib.sha256(np.ascontiguousarray(values, dtype="<f4").tobytes()).hexdigest()


def require(condition: bool, label: str, checks: list[str]) -> None:
    if not condition:
        raise RuntimeError(label)
    checks.append(label)


def render(tokenizer, template: str, *, question: str, evidence: str) -> str:
    user = template.format(question=question, evidence=evidence)
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )


def stable_log_probabilities(logits, targets):
    import numpy as np

    values = []
    for row, target in zip(logits.astype(np.float64), targets, strict=True):
        maximum = float(row.max())
        logsumexp = maximum + math.log(float(np.exp(row - maximum).sum()))
        values.append(float(row[int(target)] - logsumexp))
    return np.asarray(values, dtype=np.float64)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-report", required=True, type=Path)
    parser.add_argument("--producer-script", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--tokenizer-report", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--answer-prompt", required=True, type=Path)
    parser.add_argument("--repair-prompt", required=True, type=Path)
    parser.add_argument("--attempt-log", required=True, type=Path)
    parser.add_argument("--witness", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report_path = args.producer_report.resolve()
    script_path = args.producer_script.resolve()
    protocol = args.protocol.resolve()
    tokenizer_report = args.tokenizer_report.resolve()
    asset = args.asset.resolve()
    overlay = args.overlay.resolve()
    answer_prompt_path = args.answer_prompt.resolve()
    repair_prompt_path = args.repair_prompt.resolve()
    attempt_log = args.attempt_log.resolve()
    witness_path = args.witness.resolve()
    output = args.output.resolve()
    checks: list[str] = []

    for path, label in (
        (report_path, "PRODUCER_REPORT_EXISTS"),
        (script_path, "PRODUCER_SCRIPT_EXISTS"),
        (protocol, "PROTOCOL_EXISTS"),
        (tokenizer_report, "TOKENIZER_REPORT_EXISTS"),
        (witness_path, "WITNESS_EXISTS"),
        (attempt_log, "ATTEMPT_LOG_EXISTS"),
    ):
        require(path.is_file(), label, checks)
    require(not output.exists(), "OUTPUT_ABSENT", checks)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(report["status"] == "PASS_BOUNDED_MISTRAL_NF4_WHOLE_MODEL_PREFLIGHT",
            "PRODUCER_STATUS", checks)
    require(report["cas_q3_status"] == "NOT READY", "NOT_READY_PRESERVED", checks)
    require(report["revision"] == REVISION, "EXACT_REVISION", checks)
    require(sha256(script_path) == report["script_sha256"], "PRODUCER_SCRIPT_HASH", checks)
    require(sha256(protocol) == report["protocol_sha256"], "PROTOCOL_HASH", checks)
    require(sha256(tokenizer_report) == report["tokenizer_report_sha256"] ==
            TOKENIZER_REPORT_SHA256, "TOKENIZER_REPORT_HASH", checks)
    require(sha256(asset / "ASSET_MANIFEST.json") == report["asset_manifest_sha256"] ==
            ASSET_MANIFEST_SHA256, "ASSET_MANIFEST_HASH", checks)
    require(report["model_loads"] == 1, "ONE_MODEL_LOAD", checks)
    require(report["generation_calls"] == 3, "THREE_GENERATION_CALLS", checks)
    require(report["teacher_forced_calls"] == 2, "TWO_TEACHER_CALLS", checks)
    for field in ("project_rows_read", "scientific_fits", "gold_labels_read"):
        require(report[field] == 0, "ZERO_" + field.upper(), checks)

    attempts = [json.loads(line) for line in attempt_log.read_text(encoding="utf-8").splitlines() if line]
    require([row["event"] for row in attempts] == [
        "whole_model_preflight_started", "whole_model_preflight_completed"
    ], "ATTEMPT_EVENT_SEQUENCE", checks)
    require(attempts[1]["report_sha256"] == sha256(report_path),
            "ATTEMPT_REPORT_HASH", checks)
    require(attempts[1]["witness_sha256"] == sha256(witness_path),
            "ATTEMPT_WITNESS_HASH", checks)
    require(all(row["project_rows_read"] == row["gold_labels_read"] ==
                row["scientific_fits"] == 0 for row in attempts),
            "ATTEMPT_ZERO_SCIENTIFIC_ACCESS", checks)

    witness = report["witness"]
    require(witness["sha256"] == sha256(witness_path), "WITNESS_HASH", checks)
    require(witness["bytes"] == witness_path.stat().st_size, "WITNESS_BYTES", checks)
    require(witness["bytes"] <= witness["max_bytes"] == 8 * 1024 * 1024,
            "WITNESS_SIZE_LIMIT", checks)
    import numpy as np
    with np.load(witness_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    require(sorted(arrays) == witness["array_names"], "WITNESS_ARRAY_SET", checks)
    for name, value in arrays.items():
        require(value.dtype in (np.dtype("int32"), np.dtype("float32")),
                "WITNESS_DTYPE:" + name, checks)
        require(bool(np.isfinite(value).all()), "WITNESS_FINITE:" + name, checks)

    answer = report["answer_fixture"]
    require(arrays["answer_scores_f32"].shape ==
            (answer["generated_token_count"], 32768), "ANSWER_SCORE_SHAPE", checks)
    require(np.array_equal(arrays["answer_scores_f32"].argmax(axis=1).astype(np.int32),
                           arrays["answer_generated_ids_i32"]),
            "ANSWER_GREEDY_RECONSTRUCTION", checks)
    require(arrays["answer_generated_ids_i32"].tolist() == answer["generated_ids"],
            "ANSWER_IDS", checks)
    require(ids_sha256(arrays["answer_prompt_ids_i32"]) ==
            answer["prompt_ids_sha256_int32_le"], "ANSWER_PROMPT_HASH", checks)
    require(ids_sha256(arrays["answer_generated_ids_i32"]) ==
            answer["generated_ids_sha256_int32_le"], "ANSWER_IDS_HASH", checks)
    require(array_sha256(arrays["answer_scores_f32"]) ==
            answer["scores_sha256_float32_le"], "ANSWER_SCORES_HASH", checks)

    repair = report["repair_fixture"]
    require(arrays["repair_scores_f32"].shape ==
            (repair["generated_token_count"], 32768), "REPAIR_SCORE_SHAPE", checks)
    require(np.array_equal(arrays["repair_scores_f32"].argmax(axis=1).astype(np.int32),
                           arrays["repair_generated_ids_i32"]),
            "REPAIR_GREEDY_RECONSTRUCTION", checks)
    require(arrays["repair_generated_ids_i32"].tolist() == repair["generated_ids"],
            "REPAIR_IDS", checks)
    require(ids_sha256(arrays["repair_prompt_ids_i32"]) ==
            repair["prompt_ids_sha256_int32_le"], "REPAIR_PROMPT_HASH", checks)
    require(array_sha256(arrays["repair_scores_f32"]) ==
            repair["scores_sha256_float32_le"], "REPAIR_SCORES_HASH", checks)

    likelihood = report["likelihood_fixture"]
    require(arrays["likelihood_logits_f32"].shape ==
            (likelihood["target_token_count"], 32768), "LIKELIHOOD_LOGIT_SHAPE", checks)
    require(arrays["likelihood_target_ids_i32"].tolist() == likelihood["target_ids"],
            "LIKELIHOOD_TARGET_IDS", checks)
    require(ids_sha256(arrays["likelihood_prompt_ids_i32"]) ==
            likelihood["prompt_ids_sha256_int32_le"], "LIKELIHOOD_PROMPT_HASH", checks)
    require(ids_sha256(arrays["likelihood_target_ids_i32"]) ==
            likelihood["target_ids_sha256_int32_le"], "LIKELIHOOD_TARGET_HASH", checks)
    require(array_sha256(arrays["likelihood_logits_f32"]) ==
            likelihood["logits_sha256_float32_le"], "LIKELIHOOD_LOGITS_HASH", checks)
    independently_recomputed = stable_log_probabilities(
        arrays["likelihood_logits_f32"], arrays["likelihood_target_ids_i32"]
    )
    saved_values = arrays["likelihood_chosen_log_probabilities_f32"].astype(np.float64)
    report_values = np.asarray(likelihood["chosen_log_probabilities"], dtype=np.float64)
    require(np.allclose(independently_recomputed, saved_values, rtol=0, atol=1e-5),
            "INDEPENDENT_LOG_PROBABILITY_ARITHMETIC", checks)
    require(np.array_equal(saved_values.astype(np.float32), report_values.astype(np.float32)),
            "REPORT_LOG_PROBABILITIES", checks)

    resolved_sys_path = [Path(entry).resolve() for entry in sys.path if entry]
    require(overlay in resolved_sys_path, "OVERLAY_ON_SYS_PATH", checks)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        asset, use_fast=True, legacy=False, local_files_only=True, trust_remote_code=False
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    answer_template = answer_prompt_path.read_text(encoding="utf-8")
    repair_template = repair_prompt_path.read_text(encoding="utf-8")
    answer_prompt = render(
        tokenizer, answer_template,
        question="What is the capital of France?",
        evidence="[Evidence 1 | id=invented-answer | title=Geography]\nParis is the capital of France.",
    )
    replay_answer_prompt_ids = np.asarray(
        tokenizer(answer_prompt, add_special_tokens=False)["input_ids"], dtype=np.int32
    )
    require(np.array_equal(replay_answer_prompt_ids, arrays["answer_prompt_ids_i32"]),
            "ANSWER_PROMPT_RETOKENIZATION", checks)
    decoded_answer = tokenizer.decode(
        arrays["answer_generated_ids_i32"].tolist(), skip_special_tokens=True
    ).strip()
    require(decoded_answer == answer["decoded"], "ANSWER_DECODE", checks)
    require(decoded_answer.strip().rstrip(".").strip().casefold() == "paris",
            "ANSWER_SEMANTIC_PREDICATE", checks)
    repair_prompt = render(
        tokenizer, repair_template,
        question="In which country is Ada's birth city located?",
        evidence="[Evidence 1 | id=invented-repair | title=Biography]\nAda was born in Northport.",
    )
    replay_repair_prompt_ids = np.asarray(
        tokenizer(repair_prompt, add_special_tokens=False)["input_ids"], dtype=np.int32
    )
    require(np.array_equal(replay_repair_prompt_ids, arrays["repair_prompt_ids_i32"]),
            "REPAIR_PROMPT_RETOKENIZATION", checks)
    decoded_repair = tokenizer.decode(
        arrays["repair_generated_ids_i32"].tolist(), skip_special_tokens=True
    ).strip()
    require(decoded_repair == repair["decoded"], "REPAIR_DECODE", checks)
    missing = re.search(r"(?im)^\s*Missing fact:\s*(.+?)\s*$", decoded_repair)
    query = re.search(r"(?im)^\s*Search query:\s*(.+?)\s*$", decoded_repair)
    require(missing is not None and missing.group(1).strip() == repair["missing_fact"],
            "REPAIR_MISSING_FACT", checks)
    require(query is not None and query.group(1).strip() == repair["search_query"],
            "REPAIR_SEARCH_QUERY", checks)
    prompt_ids = tokenizer(answer_prompt, add_special_tokens=False)["input_ids"]
    full_ids = tokenizer(answer_prompt + "Paris", add_special_tokens=False)["input_ids"]
    require(full_ids[:len(prompt_ids)] == prompt_ids, "LIKELIHOOD_PREFIX_ALIGNMENT", checks)
    require(np.array_equal(np.asarray(prompt_ids, dtype=np.int32),
                           arrays["likelihood_prompt_ids_i32"]),
            "LIKELIHOOD_PROMPT_RETOKENIZATION", checks)
    require(np.array_equal(np.asarray(full_ids[len(prompt_ids):], dtype=np.int32),
                           arrays["likelihood_target_ids_i32"]),
            "LIKELIHOOD_TARGET_RETOKENIZATION", checks)

    quantization = report["quantization"]
    require(quantization["load_in_4bit"] is True, "LOAD_IN_4BIT", checks)
    require(quantization["quant_type"] == "nf4", "NF4", checks)
    require(quantization["double_quant"] is True, "DOUBLE_QUANT", checks)
    require(quantization["compute_dtype"] == "bfloat16", "BF16_COMPUTE", checks)
    require(quantization["attention_implementation"] == "eager", "EAGER_ATTENTION", checks)
    require(quantization["linear4bit_module_count"] == 224, "LINEAR4BIT_COUNT", checks)
    require(set(quantization["linear4bit_module_names"]) == EXPECTED_LINEAR4BIT_MODULES,
            "LINEAR4BIT_NAME_SET", checks)
    require(quantization["ordinary_linear_module_names"] == ["lm_head"],
            "ONLY_LM_HEAD_ORDINARY", checks)
    require(quantization["parameter_devices"] == ["cuda:0"], "PARAMETERS_CUDA0", checks)
    require(all(value in (0, "cuda", "cuda:0")
                for value in quantization["hf_device_map"].values()),
            "NO_OFFLOAD", checks)

    resources = report["resources"]
    require(resources["gpu_total_bytes"] >= 15 * GIB, "GPU_TOTAL_ADMISSION", checks)
    require(resources["gpu_free_before_bytes"] >= 12 * GIB, "GPU_FREE_ADMISSION", checks)
    require(resources["gpu_peak_reserved_bytes"] <= 12 * GIB, "GPU_PEAK_LIMIT", checks)
    require(resources["ram_available_before_bytes"] >= 8 * GIB, "RAM_ADMISSION", checks)
    require(resources["minimum_sampled_ram_available_bytes"] >= 4 * GIB,
            "RAM_DURING_LIMIT", checks)
    require(resources["process_peak_working_set_bytes"] <= 20 * GIB,
            "PROCESS_PEAK_LIMIT", checks)
    require(resources["disk_free_before_bytes"] >= 30 * GIB, "DISK_ADMISSION", checks)
    require(resources["wall_seconds"] <= 20 * 60, "WALL_LIMIT", checks)

    validation = {
        "schema_version": 1,
        "status": "PASS_INDEPENDENT_MISTRAL_WHOLE_MODEL_WITNESS_VALIDATION",
        "cas_q3_status": "NOT READY",
        "producer_report_sha256": sha256(report_path),
        "producer_script_sha256": sha256(script_path),
        "protocol_sha256": sha256(protocol),
        "witness_sha256": sha256(witness_path),
        "attempt_log_sha256": sha256(attempt_log),
        "validator_script_sha256": sha256(Path(__file__).resolve()),
        "checks": len(checks),
        "check_labels": checks,
        "independent_likelihood_log_probabilities_float64": independently_recomputed.tolist(),
        "model_loads": 0,
        "reader_generations": 0,
        "neural_forwards": 0,
        "project_rows_read": 0,
        "scientific_fits": 0,
        "gold_labels_read": 0,
        "scope_limit": "Saved invented witnesses and resource/module receipts only; the validator does not reload the model or establish full-workload or scientific validity.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(validation, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": validation["status"], "checks": len(checks),
                      "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
