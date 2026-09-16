"""Validate the saved longest-shape Mistral witness without model loading."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


GIB = 1024 ** 3
PROMPT_TOKENS = 3675
DECODE_STEPS = 64
INPUT_FREEZE_RESULTS_SHA256 = "530df200e9cc295296786042797f576e2017ef76a9d5d7a3c465e73f3c33b9f5"
EXPECTED_LINEAR_NAMES = {
    f"model.layers.{layer}.{branch}.{projection}"
    for layer in range(32)
    for branch, projections in (
        ("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")),
        ("mlp", ("gate_proj", "up_proj", "down_proj")),
    )
    for projection in projections
}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-report", required=True, type=Path)
    parser.add_argument("--producer-script", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--input-freeze-results", required=True, type=Path)
    parser.add_argument("--attempt-log", required=True, type=Path)
    parser.add_argument("--witness", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report_path = args.producer_report.resolve()
    script_path = args.producer_script.resolve()
    protocol = args.protocol.resolve()
    input_results = args.input_freeze_results.resolve()
    attempt_log = args.attempt_log.resolve()
    witness_path = args.witness.resolve()
    output = args.output.resolve()
    checks: list[str] = []
    for path, label in (
        (report_path, "REPORT_EXISTS"), (script_path, "SCRIPT_EXISTS"),
        (protocol, "PROTOCOL_EXISTS"), (input_results, "INPUT_RESULTS_EXISTS"),
        (attempt_log, "ATTEMPT_LOG_EXISTS"), (witness_path, "WITNESS_EXISTS"),
    ):
        require(path.is_file(), label, checks)
    require(not output.exists(), "OUTPUT_ABSENT", checks)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(report["status"] == "PASS_MISTRAL_LONGEST_OBSERVED_SHAPE_RESOURCE_PREFLIGHT",
            "PRODUCER_STATUS", checks)
    require(report["cas_q3_status"] == "NOT READY", "NOT_READY_PRESERVED", checks)
    require(report["model_loads"] == 1 and report["generation_calls"] == 1,
            "ONE_LOAD_ONE_GENERATION", checks)
    require(report["project_content_tokens_read"] == report["gold_reads"] ==
            report["scientific_fits"] == 0, "ZERO_SCIENTIFIC_ACCESS", checks)
    require(sha256(script_path) == report["script_sha256"], "SCRIPT_HASH", checks)
    require(sha256(protocol) == report["protocol_sha256"], "PROTOCOL_HASH", checks)
    require(sha256(input_results) == report["input_freeze_results_sha256"] ==
            INPUT_FREEZE_RESULTS_SHA256, "INPUT_RESULTS_HASH", checks)
    accepted = json.loads(input_results.read_text(encoding="utf-8"))
    require(accepted["maximum_deterministic_input"]["input_tokens"] == PROMPT_TOKENS,
            "ACCEPTED_LENGTH_BINDING", checks)

    attempts = [json.loads(line) for line in attempt_log.read_text(encoding="utf-8").splitlines() if line]
    require([row["event"] for row in attempts] == [
        "longest_shape_preflight_started", "longest_shape_preflight_completed"
    ], "ATTEMPT_EVENT_SEQUENCE", checks)
    require(attempts[1]["report_sha256"] == sha256(report_path),
            "ATTEMPT_REPORT_HASH", checks)
    require(attempts[1]["witness_sha256"] == sha256(witness_path),
            "ATTEMPT_WITNESS_HASH", checks)

    import numpy as np
    with np.load(witness_path, allow_pickle=False) as archive:
        require(set(archive.files) == {
            "prompt_ids_i32", "generated_ids_i32", "generation_scores_f32"
        }, "WITNESS_ARRAY_SET", checks)
        prompt = archive["prompt_ids_i32"]
        generated = archive["generated_ids_i32"]
        scores = archive["generation_scores_f32"]
    require(prompt.dtype == generated.dtype == np.dtype("int32"), "ID_DTYPES", checks)
    require(scores.dtype == np.dtype("float32"), "SCORE_DTYPE", checks)
    require(prompt.shape == (PROMPT_TOKENS,), "PROMPT_SHAPE", checks)
    require(generated.shape == (DECODE_STEPS,), "GENERATED_SHAPE", checks)
    require(scores.shape == (DECODE_STEPS, 32768), "SCORE_SHAPE", checks)
    require(prompt[0] == 1 and prompt[1] == 3 and prompt[-1] == 4,
            "NATIVE_BOUNDARY_TOKENS", checks)
    require(bool(np.all(prompt[2:-1] == 1000)), "INVENTED_MIDDLE_TOKENS", checks)
    require(bool(np.isfinite(scores).all()), "FINITE_SCORES", checks)
    require(np.array_equal(scores.argmax(axis=1).astype(np.int32), generated),
            "INDEPENDENT_GREEDY_ARGMAX", checks)
    shape = report["shape"]
    require(shape["prompt_tokens"] == PROMPT_TOKENS and
            shape["decode_steps"] == DECODE_STEPS, "REPORT_SHAPE", checks)
    require(shape["eos_disabled_for_resource_upper_bound"] is True,
            "EOS_RESOURCE_DISCLOSURE", checks)
    require(ids_sha256(prompt) == shape["prompt_ids_sha256_int32_le"],
            "PROMPT_HASH", checks)
    require(ids_sha256(generated) == shape["generated_ids_sha256_int32_le"],
            "GENERATED_HASH", checks)
    require(array_sha256(scores) == shape["scores_sha256_float32_le"],
            "SCORES_HASH", checks)
    require(report["witness"]["sha256"] == sha256(witness_path),
            "WITNESS_HASH", checks)
    require(report["witness"]["bytes"] == witness_path.stat().st_size and
            report["witness"]["bytes"] <= 12 * 1024 * 1024,
            "WITNESS_SIZE", checks)

    quant = report["quantization"]
    require(quant["linear4bit_module_count"] == 224, "LINEAR4BIT_COUNT", checks)
    require(set(quant["linear4bit_module_names"]) == EXPECTED_LINEAR_NAMES,
            "LINEAR4BIT_NAME_SET", checks)
    require(quant["nf4"] is quant["double_quant"] is True,
            "NF4_DOUBLE_QUANT", checks)
    require(quant["compute_dtype"] == "bfloat16", "BF16_COMPUTE", checks)
    require(quant["parameter_devices"] == ["cuda:0"], "PARAMETERS_CUDA0", checks)
    require(all(value in (0, "cuda", "cuda:0") for value in quant["hf_device_map"].values()),
            "NO_OFFLOAD", checks)
    resources = report["resources"]
    require(resources["gpu_total_bytes"] >= 15 * GIB, "GPU_TOTAL", checks)
    require(resources["gpu_free_before_bytes"] >= 14 * GIB, "GPU_FREE", checks)
    require(resources["gpu_peak_reserved_bytes"] <= 14 * GIB, "GPU_PEAK", checks)
    require(resources["ram_available_before_bytes"] >= 8 * GIB, "RAM_BEFORE", checks)
    require(resources["minimum_sampled_ram_available_bytes"] >= 4 * GIB,
            "RAM_DURING", checks)
    require(resources["process_peak_working_set_bytes"] <= 20 * GIB,
            "PROCESS_PEAK", checks)
    require(resources["disk_free_before_bytes"] >= 30 * GIB, "DISK_FREE", checks)
    require(resources["wall_seconds"] <= 20 * 60, "WALL_LIMIT", checks)

    validation = {
        "schema_version": 1,
        "status": "PASS_INDEPENDENT_MISTRAL_LONGEST_SHAPE_WITNESS_VALIDATION",
        "cas_q3_status": "NOT READY",
        "producer_report_sha256": sha256(report_path),
        "producer_script_sha256": sha256(script_path),
        "protocol_sha256": sha256(protocol),
        "input_freeze_results_sha256": sha256(input_results),
        "witness_sha256": sha256(witness_path),
        "attempt_log_sha256": sha256(attempt_log),
        "validator_script_sha256": sha256(Path(__file__).resolve()),
        "checks": len(checks),
        "check_labels": checks,
        "prompt_tokens": PROMPT_TOKENS,
        "decode_steps": DECODE_STEPS,
        "model_loads": 0,
        "neural_forwards": 0,
        "project_content_tokens_read": 0,
        "gold_reads": 0,
        "scientific_fits": 0,
        "scope_limit": "Saved invented longest-shape witness only; no model reload, project content, production workload or scientific effect.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(validation, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": validation["status"], "checks": len(checks),
                      "prompt_tokens": PROMPT_TOKENS, "decode_steps": DECODE_STEPS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
