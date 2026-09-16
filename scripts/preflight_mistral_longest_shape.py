"""One NF4 resource preflight at the longest accepted fixed prompt shape."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

from scripts.preflight_mistral_whole_model import (
    EXPECTED_LINEAR4BIT_MODULES,
    REQUIRED_ENVIRONMENT,
    ResourceMonitor,
    append_event,
    array_sha256,
    configure_tokenizer,
    ids_sha256,
    require,
    sha256,
    utc_now,
)


REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
INPUT_FREEZE_RESULTS_SHA256 = "530df200e9cc295296786042797f576e2017ef76a9d5d7a3c465e73f3c33b9f5"
ASSET_MANIFEST_SHA256 = "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
PROMPT_TOKENS = 3675
DECODE_STEPS = 64
MIDDLE_TOKEN_ID = 1000
SEED = 20260917
GIB = 1024 ** 3
MIN_GPU_TOTAL_BYTES = 15 * GIB
MIN_GPU_FREE_BEFORE_BYTES = 14 * GIB
MAX_GPU_RESERVED_BYTES = 14 * GIB
MIN_RAM_AVAILABLE_BEFORE_BYTES = 8 * GIB
MIN_RAM_AVAILABLE_DURING_BYTES = 4 * GIB
MAX_PROCESS_PEAK_WORKING_SET_BYTES = 20 * GIB
MIN_DISK_FREE_BYTES = 30 * GIB
MAX_WALL_SECONDS = 20 * 60
MAX_WITNESS_BYTES = 12 * 1024 * 1024


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--input-freeze-results", required=True, type=Path)
    parser.add_argument("--attempt-log", required=True, type=Path)
    parser.add_argument("--witness", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    asset = args.asset.resolve()
    overlay = args.overlay.resolve()
    protocol = args.protocol.resolve()
    input_results = args.input_freeze_results.resolve()
    attempt_log = args.attempt_log.resolve()
    witness = args.witness.resolve()
    output = args.output.resolve()
    script_path = Path(__file__).resolve()
    require(not output.exists() and not witness.exists(), "OUTPUTS_ABSENT")
    require(asset.is_dir() and overlay.is_dir(), "RUNTIME_ROOTS")
    require(protocol.is_file() and input_results.is_file(), "BOUND_CONTROL_FILES")
    require(sha256(asset / "ASSET_MANIFEST.json") == ASSET_MANIFEST_SHA256,
            "ASSET_MANIFEST_HASH")
    require(sha256(input_results) == INPUT_FREEZE_RESULTS_SHA256,
            "INPUT_FREEZE_RESULTS_HASH")
    frozen_result = json.loads(input_results.read_text(encoding="utf-8"))
    require(frozen_result["status"] == "ACCEPTED_VALUE_BLIND_MISTRAL_INPUT_FREEZE",
            "INPUT_FREEZE_STATUS")
    require(frozen_result["maximum_deterministic_input"]["input_tokens"] == PROMPT_TOKENS,
            "LONGEST_SHAPE_BINDING")
    require(all(os.environ.get(name) == value for name, value in REQUIRED_ENVIRONMENT.items()),
            "FROZEN_ENVIRONMENT")
    if attempt_log.exists():
        prior = [json.loads(line) for line in attempt_log.read_text(encoding="utf-8").splitlines() if line]
        require(not any(row.get("event") == "longest_shape_preflight_started" for row in prior),
                "ONE_ATTEMPT_ONLY")

    append_event(attempt_log, {
        "event": "longest_shape_preflight_started",
        "started_utc": utc_now(),
        "repo_id": REPO_ID,
        "revision": REVISION,
        "prompt_tokens": PROMPT_TOKENS,
        "decode_steps": DECODE_STEPS,
        "script_sha256": sha256(script_path),
        "protocol_sha256": sha256(protocol),
        "input_freeze_results_sha256": INPUT_FREEZE_RESULTS_SHA256,
        "project_content_tokens_read": 0,
        "gold_reads": 0,
        "scientific_fits": 0,
    })
    started = time.perf_counter()
    model = None
    monitor = None
    model_load_attempted = 0
    try:
        import bitsandbytes as bnb
        import numpy as np
        import psutil
        import torch
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig

        resolved_sys_path = [Path(entry).resolve() for entry in sys.path if entry]
        require(overlay in resolved_sys_path, "OVERLAY_ON_SYS_PATH")
        overlay_index = resolved_sys_path.index(overlay)
        require(all(overlay_index < index for index, entry in enumerate(resolved_sys_path)
                    if entry != overlay and entry.name.casefold() == "site-packages"),
                "OVERLAY_FIRST_SITE_PACKAGES")
        versions = {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "accelerate", "bitsandbytes",
                         "sentencepiece", "protobuf", "numpy", "psutil")
        }
        require(versions == {
            "torch": "2.7.1+cu128", "transformers": "4.53.2",
            "accelerate": "1.8.1", "bitsandbytes": "0.50.2",
            "sentencepiece": "0.2.1", "protobuf": "7.36.1",
            "numpy": "2.2.6", "psutil": "7.0.0",
        }, "VERSION_SET")
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1,
                "ONE_CUDA_DEVICE")
        require(torch.cuda.get_device_name(0) == "NVIDIA GeForce RTX 5060 Ti", "GPU_NAME")
        require(torch.cuda.get_device_capability(0) == (12, 0), "GPU_CAPABILITY")
        require(torch.cuda.is_bf16_supported(), "BF16_SUPPORTED")
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(0)
        gpu_free_before, gpu_total = torch.cuda.mem_get_info(0)
        ram_before = psutil.virtual_memory()
        disk_free_before = psutil.disk_usage(str(asset.anchor)).free
        require(gpu_total >= MIN_GPU_TOTAL_BYTES, "GPU_TOTAL_ADMISSION")
        require(gpu_free_before >= MIN_GPU_FREE_BEFORE_BYTES, "GPU_FREE_ADMISSION")
        require(ram_before.available >= MIN_RAM_AVAILABLE_BEFORE_BYTES, "RAM_ADMISSION")
        require(disk_free_before >= MIN_DISK_FREE_BYTES, "DISK_ADMISSION")

        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        np.random.seed(SEED)
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        tokenizer = configure_tokenizer(asset)
        require(tokenizer.convert_tokens_to_ids("[INST]") == 3, "INST_TOKEN")
        require(tokenizer.convert_tokens_to_ids("[/INST]") == 4, "END_INST_TOKEN")

        prompt_ids = np.asarray(
            [1, 3] + [MIDDLE_TOKEN_ID] * (PROMPT_TOKENS - 3) + [4],
            dtype="<i4",
        )
        require(prompt_ids.shape == (PROMPT_TOKENS,), "PROMPT_SHAPE")
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        monitor = ResourceMonitor(torch, psutil)
        monitor.start()
        model_load_attempted = 1
        model = AutoModelForCausalLM.from_pretrained(
            asset,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=True,
            low_cpu_mem_usage=True,
            device_map={"": 0},
            quantization_config=quantization_config,
            torch_dtype=torch.bfloat16,
            attn_implementation="eager",
        )
        model.eval()
        linear4 = {name: module for name, module in model.named_modules()
                   if isinstance(module, bnb.nn.Linear4bit)}
        require(set(linear4) == set(EXPECTED_LINEAR4BIT_MODULES), "LINEAR4BIT_SET")
        require(all(module.weight.quant_state is not None and
                    module.weight.quant_state.quant_type == "nf4" and
                    bool(module.weight.quant_state.nested) and
                    module.compute_dtype == torch.bfloat16
                    for module in linear4.values()), "NF4_DOUBLE_BF16")
        device_map = dict(getattr(model, "hf_device_map", {}))
        require(bool(device_map) and all(value in (0, "cuda", "cuda:0")
                                         for value in device_map.values()),
                "NO_CPU_DISK_OFFLOAD")
        require(sorted({str(parameter.device) for parameter in model.parameters()}) == ["cuda:0"],
                "PARAMETERS_CUDA0")
        input_ids = torch.from_numpy(prompt_ids.astype(np.int64)).unsqueeze(0).to("cuda:0")
        attention_mask = torch.ones_like(input_ids)
        generation_config = copy.deepcopy(model.generation_config)
        generation_config.do_sample = False
        generation_config.eos_token_id = None
        generation_config.pad_token_id = 2
        generation_config.temperature = None
        generation_config.top_p = None
        generation_config.top_k = None
        with torch.inference_mode():
            generated = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                generation_config=generation_config,
                max_new_tokens=DECODE_STEPS,
                use_cache=True,
                return_dict_in_generate=True,
                output_scores=True,
            )
        output_ids = generated.sequences[0, PROMPT_TOKENS:].detach().cpu().to(torch.int32).numpy()
        require(output_ids.shape == (DECODE_STEPS,), "EXACT_DECODE_STEPS")
        require(len(generated.scores) == DECODE_STEPS, "SCORE_STEP_COUNT")
        scores = torch.stack([row[0].float().cpu() for row in generated.scores]).numpy()
        require(scores.shape == (DECODE_STEPS, 32768), "SCORE_SHAPE")
        require(bool(np.isfinite(scores).all()), "FINITE_SCORES")
        require(np.array_equal(scores.argmax(axis=1).astype(np.int32), output_ids),
                "GREEDY_ARGMAX")
        torch.cuda.synchronize(0)
        monitor.stop()
        minimum_available_ram = int(monitor.minimum_available_ram)
        minimum_gpu_free = int(monitor.minimum_gpu_free)
        monitor_samples = int(monitor.samples)
        monitor = None

        wall_seconds = time.perf_counter() - started
        process_memory = psutil.Process().memory_info()
        gpu_free_after, gpu_total_after = torch.cuda.mem_get_info(0)
        peak_allocated = int(torch.cuda.max_memory_allocated(0))
        peak_reserved = int(torch.cuda.max_memory_reserved(0))
        require(gpu_total_after == gpu_total, "GPU_TOTAL_STABLE")
        require(peak_reserved <= MAX_GPU_RESERVED_BYTES, "GPU_PEAK_LIMIT")
        require(minimum_available_ram >= MIN_RAM_AVAILABLE_DURING_BYTES,
                "RAM_DURING_LIMIT")
        require(int(process_memory.peak_wset) <= MAX_PROCESS_PEAK_WORKING_SET_BYTES,
                "PROCESS_PEAK_LIMIT")
        require(wall_seconds <= MAX_WALL_SECONDS, "WALL_LIMIT")

        witness.parent.mkdir(parents=True, exist_ok=True)
        temporary = witness.with_suffix(witness.suffix + ".part")
        with temporary.open("xb") as handle:
            np.savez_compressed(
                handle,
                prompt_ids_i32=prompt_ids,
                generated_ids_i32=output_ids,
                generation_scores_f32=scores,
            )
        temporary.replace(witness)
        require(witness.stat().st_size <= MAX_WITNESS_BYTES, "WITNESS_SIZE_LIMIT")
        report = {
            "schema_version": 1,
            "status": "PASS_MISTRAL_LONGEST_OBSERVED_SHAPE_RESOURCE_PREFLIGHT",
            "scientific_status": "INVENTED_TOKEN_CONTENT_ONLY_NO_PROJECT_CONTENT_OR_GOLD",
            "cas_q3_status": "NOT READY",
            "repo_id": REPO_ID,
            "revision": REVISION,
            "script_sha256": sha256(script_path),
            "protocol_sha256": sha256(protocol),
            "input_freeze_results_sha256": INPUT_FREEZE_RESULTS_SHA256,
            "versions": versions,
            "environment": REQUIRED_ENVIRONMENT,
            "shape": {
                "batch_size": 1,
                "prompt_tokens": PROMPT_TOKENS,
                "decode_steps": DECODE_STEPS,
                "prompt_construction": "[1,3] + [1000] * 3672 + [4]",
                "prompt_ids_sha256_int32_le": ids_sha256(prompt_ids),
                "generated_ids": output_ids.tolist(),
                "generated_ids_sha256_int32_le": ids_sha256(output_ids),
                "scores_sha256_float32_le": array_sha256(scores),
                "eos_disabled_for_resource_upper_bound": True,
                "greedy_argmax_verified": True,
            },
            "quantization": {
                "linear4bit_module_count": len(linear4),
                "linear4bit_module_names": sorted(linear4),
                "nf4": True,
                "double_quant": True,
                "compute_dtype": "bfloat16",
                "parameter_devices": ["cuda:0"],
                "hf_device_map": device_map,
                "model_memory_footprint_bytes": int(model.get_memory_footprint()),
            },
            "resources": {
                "gpu_total_bytes": int(gpu_total),
                "gpu_free_before_bytes": int(gpu_free_before),
                "gpu_free_after_bytes": int(gpu_free_after),
                "gpu_peak_allocated_bytes": peak_allocated,
                "gpu_peak_reserved_bytes": peak_reserved,
                "gpu_peak_reserved_limit_bytes": MAX_GPU_RESERVED_BYTES,
                "ram_total_bytes": int(ram_before.total),
                "ram_available_before_bytes": int(ram_before.available),
                "minimum_sampled_ram_available_bytes": minimum_available_ram,
                "minimum_sampled_ram_available_limit_bytes": MIN_RAM_AVAILABLE_DURING_BYTES,
                "process_peak_working_set_bytes": int(process_memory.peak_wset),
                "process_peak_working_set_limit_bytes": MAX_PROCESS_PEAK_WORKING_SET_BYTES,
                "minimum_sampled_gpu_free_bytes": minimum_gpu_free,
                "resource_monitor_samples": monitor_samples,
                "disk_free_before_bytes": int(disk_free_before),
                "wall_seconds": wall_seconds,
                "wall_limit_seconds": MAX_WALL_SECONDS,
            },
            "witness": {
                "path": str(witness), "bytes": witness.stat().st_size,
                "sha256": sha256(witness), "max_bytes": MAX_WITNESS_BYTES,
            },
            "model_loads": 1,
            "generation_calls": 1,
            "project_content_tokens_read": 0,
            "gold_reads": 0,
            "scientific_fits": 0,
            "scope_limit": "Longest observed fixed prompt shape only; production adapter, dynamic a1, full workload and scientific effect remain open.",
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        append_event(attempt_log, {
            "event": "longest_shape_preflight_completed",
            "completed_utc": utc_now(), "status": report["status"],
            "report_sha256": sha256(output), "witness_sha256": sha256(witness),
            "model_loads": 1, "project_content_tokens_read": 0,
            "gold_reads": 0, "scientific_fits": 0,
        })
        print(json.dumps({"status": report["status"], "prompt_tokens": PROMPT_TOKENS,
                          "decode_steps": DECODE_STEPS,
                          "gpu_peak_reserved_bytes": peak_reserved,
                          "wall_seconds": wall_seconds}))
        return 0
    except BaseException as error:
        if monitor is not None:
            monitor.stop()
        append_event(attempt_log, {
            "event": "longest_shape_preflight_failed", "failed_utc": utc_now(),
            "error_type": type(error).__name__, "error": str(error),
            "model_load_attempted": model_load_attempted,
            "report_exists": output.exists(), "witness_exists": witness.exists(),
            "project_content_tokens_read": 0, "gold_reads": 0,
            "scientific_fits": 0,
        })
        raise
    finally:
        model = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
