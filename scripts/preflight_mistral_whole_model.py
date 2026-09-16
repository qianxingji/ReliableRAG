"""One bounded NF4 Mistral load with invented-only numerical witnesses."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
import time


REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
ASSET_MANIFEST_SHA256 = "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18"
TOKENIZER_REPORT_SHA256 = "47f3f2f04ed324e7be8051a594224bfdca8fc244133c14d5aeef028db24d1b5a"
SEED = 20260917
GIB = 1024 ** 3
MIN_GPU_TOTAL_BYTES = 15 * GIB
MIN_GPU_FREE_BEFORE_BYTES = 12 * GIB
MAX_GPU_RESERVED_BYTES = 12 * GIB
MIN_RAM_AVAILABLE_BEFORE_BYTES = 8 * GIB
MIN_RAM_AVAILABLE_DURING_BYTES = 4 * GIB
MAX_PROCESS_PEAK_WORKING_SET_BYTES = 20 * GIB
MIN_DISK_FREE_BYTES = 30 * GIB
MAX_WALL_SECONDS = 20 * 60
MAX_WITNESS_BYTES = 8 * 1024 * 1024
ANSWER_PREFLIGHT_MAX_NEW_TOKENS = 8
REPAIR_PREFLIGHT_MAX_NEW_TOKENS = 32
EXPECTED_LINEAR4BIT_MODULES = tuple(
    f"model.layers.{layer}.{branch}.{projection}"
    for layer in range(32)
    for branch, projections in (
        ("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")),
        ("mlp", ("gate_proj", "up_proj", "down_proj")),
    )
    for projection in projections
)
REQUIRED_ENVIRONMENT = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "PYTHONHASHSEED": "0",
    "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ids_sha256(values) -> str:
    import numpy as np

    return hashlib.sha256(np.asarray(values, dtype="<i4").tobytes()).hexdigest()


def array_sha256(value) -> str:
    import numpy as np

    return hashlib.sha256(np.ascontiguousarray(value, dtype="<f4").tobytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def append_event(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


class ResourceMonitor:
    def __init__(self, torch_module, psutil_module) -> None:
        self.torch = torch_module
        self.psutil = psutil_module
        self.stop_event = threading.Event()
        self.minimum_available_ram = self.psutil.virtual_memory().available
        self.minimum_gpu_free, self.gpu_total = self.torch.cuda.mem_get_info(0)
        self.samples = 0
        self.thread = threading.Thread(target=self._run, name="resource-monitor", daemon=True)

    def _run(self) -> None:
        while not self.stop_event.wait(0.05):
            self.minimum_available_ram = min(
                self.minimum_available_ram, self.psutil.virtual_memory().available
            )
            free, total = self.torch.cuda.mem_get_info(0)
            self.minimum_gpu_free = min(self.minimum_gpu_free, free)
            self.gpu_total = total
            self.samples += 1

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=5)


def configure_tokenizer(asset: Path):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        asset,
        use_fast=True,
        legacy=False,
        local_files_only=True,
        trust_remote_code=False,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    require(type(tokenizer).__name__ == "LlamaTokenizerFast", "TOKENIZER_CLASS")
    require(tokenizer.bos_token_id == 1 and tokenizer.eos_token_id == 2,
            "TOKENIZER_SPECIAL_IDS")
    require(tokenizer.pad_token_id == 2, "TOKENIZER_PAD_ID")
    return tokenizer


def render(tokenizer, template: str, *, question: str, evidence: str) -> str:
    user = template.format(question=question, evidence=evidence)
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )


def tokenize_prompt(tokenizer, prompt: str, torch_module) -> dict[str, object]:
    values = tokenizer([prompt], add_special_tokens=False, return_tensors="pt")
    require(int(values["input_ids"].shape[0]) == 1, "BATCH_ONE")
    require(int(values["input_ids"].shape[1]) <= 8192, "PROMPT_GUARD")
    return {name: tensor.to("cuda:0") for name, tensor in values.items()}


def generate(model, tokenizer, prompt: str, max_new_tokens: int, torch_module):
    inputs = tokenize_prompt(tokenizer, prompt, torch_module)
    prompt_width = int(inputs["input_ids"].shape[1])
    with torch_module.inference_mode():
        result = model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
            return_dict_in_generate=True,
            output_scores=True,
        )
    output_ids = result.sequences[0, prompt_width:].detach().cpu().to(torch_module.int32).numpy()
    require(len(result.scores) == len(output_ids), "GENERATION_SCORE_STEP_COUNT")
    scores = torch_module.stack([row[0].float().cpu() for row in result.scores]).numpy()
    require(scores.shape == (len(output_ids), 32768), "GENERATION_SCORE_SHAPE")
    require(bool(torch_module.from_numpy(scores).isfinite().all().item()), "FINITE_GENERATION_SCORES")
    decoded = tokenizer.decode(output_ids.tolist(), skip_special_tokens=True).strip()
    return {
        "prompt_ids": inputs["input_ids"][0].detach().cpu().to(torch_module.int32).numpy(),
        "output_ids": output_ids,
        "scores": scores,
        "decoded": decoded,
    }


def teacher_forced(model, tokenizer, prompt: str, target: str, torch_module):
    prompt_ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    full_ids = list(tokenizer(prompt + target, add_special_tokens=False)["input_ids"])
    require(full_ids[:len(prompt_ids)] == prompt_ids, "LIKELIHOOD_PREFIX_ALIGNMENT")
    target_ids = full_ids[len(prompt_ids):]
    require(bool(target_ids), "LIKELIHOOD_TARGET_NONEMPTY")
    require(len(full_ids) <= 8192, "LIKELIHOOD_TOTAL_GUARD")
    input_ids = torch_module.tensor([full_ids], device="cuda:0", dtype=torch_module.long)
    attention_mask = torch_module.ones_like(input_ids)
    position_ids = attention_mask.long().cumsum(-1) - 1
    with torch_module.inference_mode():
        logits = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            use_cache=False,
        ).logits
    positions = torch_module.arange(
        len(prompt_ids) - 1,
        len(prompt_ids) + len(target_ids) - 1,
        device="cuda:0",
    )
    selected = logits[0, positions, :].float().cpu()
    require(tuple(selected.shape) == (len(target_ids), 32768), "LIKELIHOOD_LOGIT_SHAPE")
    require(bool(torch_module.isfinite(selected).all().item()), "FINITE_LIKELIHOOD_LOGITS")
    targets = torch_module.tensor(target_ids, dtype=torch_module.long)
    chosen = selected.gather(1, targets[:, None]).squeeze(1) - torch_module.logsumexp(selected, dim=-1)
    values = chosen.numpy()
    require(all(math.isfinite(float(value)) for value in values), "FINITE_CHOSEN_LOG_PROBABILITIES")
    import numpy as np
    return {
        "prompt_ids": np.asarray(prompt_ids, dtype="<i4"),
        "target_ids": np.asarray(target_ids, dtype="<i4"),
        "logits": selected.numpy(),
        "chosen_log_probabilities": values,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--tokenizer-report", required=True, type=Path)
    parser.add_argument("--answer-prompt", required=True, type=Path)
    parser.add_argument("--repair-prompt", required=True, type=Path)
    parser.add_argument("--attempt-log", required=True, type=Path)
    parser.add_argument("--witness", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    asset = args.asset.resolve()
    overlay = args.overlay.resolve()
    protocol = args.protocol.resolve()
    tokenizer_report = args.tokenizer_report.resolve()
    answer_prompt_path = args.answer_prompt.resolve()
    repair_prompt_path = args.repair_prompt.resolve()
    attempt_log = args.attempt_log.resolve()
    witness = args.witness.resolve()
    output = args.output.resolve()
    script_path = Path(__file__).resolve()
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    require(not witness.exists(), "WITNESS_ALREADY_EXISTS")
    require(asset.is_dir() and overlay.is_dir(), "RUNTIME_PATHS")
    require(protocol.is_file() and tokenizer_report.is_file(), "PROTOCOL_AND_TOKENIZER_REPORT")
    require(answer_prompt_path.is_file() and repair_prompt_path.is_file(), "PROMPT_PATHS")
    require(sha256(asset / "ASSET_MANIFEST.json") == ASSET_MANIFEST_SHA256,
            "ASSET_MANIFEST_HASH")
    require(sha256(tokenizer_report) == TOKENIZER_REPORT_SHA256, "TOKENIZER_REPORT_HASH")
    require(all(os.environ.get(name) == value for name, value in REQUIRED_ENVIRONMENT.items()),
            "FROZEN_ENVIRONMENT")
    if attempt_log.exists():
        prior = [json.loads(line) for line in attempt_log.read_text(encoding="utf-8").splitlines() if line]
        require(not any(row.get("event") == "whole_model_preflight_started" for row in prior),
                "ONE_ATTEMPT_ONLY")

    started = time.perf_counter()
    model_load_attempted = 0
    model = None
    monitor = None
    append_event(attempt_log, {
        "event": "whole_model_preflight_started",
        "started_utc": utc_now(),
        "repo_id": REPO_ID,
        "revision": REVISION,
        "script_sha256": sha256(script_path),
        "protocol_sha256": sha256(protocol),
        "asset_manifest_sha256": ASSET_MANIFEST_SHA256,
        "tokenizer_report_sha256": TOKENIZER_REPORT_SHA256,
        "project_rows_read": 0,
        "gold_labels_read": 0,
        "scientific_fits": 0,
    })
    try:
        import numpy as np
        import psutil
        import torch
        import bitsandbytes as bnb
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
            "torch": "2.7.1+cu128",
            "transformers": "4.53.2",
            "accelerate": "1.8.1",
            "bitsandbytes": "0.50.2",
            "sentencepiece": "0.2.1",
            "protobuf": "7.36.1",
            "numpy": "2.2.6",
            "psutil": "7.0.0",
        }, "VERSION_SET")
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, "ONE_CUDA_DEVICE")
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
        answer_template = answer_prompt_path.read_text(encoding="utf-8")
        repair_template = repair_prompt_path.read_text(encoding="utf-8")

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
        model.generation_config.temperature = None
        model.generation_config.top_p = None
        model.generation_config.top_k = None

        require(type(model).__name__ == "MistralForCausalLM", "MODEL_CLASS")
        require(model.config.model_type == "mistral", "MODEL_TYPE")
        require(model.config.num_hidden_layers == 32, "LAYER_COUNT")
        require(model.config.vocab_size == 32768, "MODEL_VOCAB")
        require(model.config.max_position_embeddings == 32768, "MODEL_CONTEXT")
        require(getattr(model.config, "_attn_implementation", None) == "eager",
                "EAGER_ATTENTION")
        device_map = dict(getattr(model, "hf_device_map", {}))
        require(bool(device_map), "HF_DEVICE_MAP_PRESENT")
        require(all(value in (0, "cuda", "cuda:0") for value in device_map.values()),
                "NO_CPU_OR_DISK_OFFLOAD")
        linear4 = {name: module for name, module in model.named_modules()
                   if isinstance(module, bnb.nn.Linear4bit)}
        require(set(linear4) == set(EXPECTED_LINEAR4BIT_MODULES), "LINEAR4BIT_MODULE_SET")
        ordinary_linear = [name for name, module in model.named_modules()
                           if isinstance(module, torch.nn.Linear)
                           and not isinstance(module, bnb.nn.Linear4bit)]
        require(ordinary_linear == ["lm_head"], "ONLY_LM_HEAD_ORDINARY_LINEAR")
        for name, module in linear4.items():
            state = module.weight.quant_state
            require(state is not None, "QUANT_STATE:" + name)
            require(state.quant_type == "nf4", "NF4:" + name)
            require(bool(state.nested), "DOUBLE_QUANT:" + name)
            require(module.compute_dtype == torch.bfloat16, "BF16_COMPUTE:" + name)
            require(module.weight.device.type == "cuda", "CUDA_WEIGHT:" + name)
        parameter_devices = sorted({str(parameter.device) for parameter in model.parameters()})
        require(parameter_devices == ["cuda:0"], "ALL_PARAMETERS_CUDA0")
        require(not any(parameter.device.type == "meta" for parameter in model.parameters()),
                "NO_META_PARAMETERS")
        require(model.model.embed_tokens.weight.dtype == torch.bfloat16, "EMBED_BF16")
        require(model.lm_head.weight.dtype == torch.bfloat16, "LM_HEAD_BF16")

        answer_prompt = render(
            tokenizer,
            answer_template,
            question="What is the capital of France?",
            evidence="[Evidence 1 | id=invented-answer | title=Geography]\nParis is the capital of France.",
        )
        answer_first = generate(
            model, tokenizer, answer_prompt, ANSWER_PREFLIGHT_MAX_NEW_TOKENS, torch
        )
        answer_second = generate(
            model, tokenizer, answer_prompt, ANSWER_PREFLIGHT_MAX_NEW_TOKENS, torch
        )
        require(np.array_equal(answer_first["output_ids"], answer_second["output_ids"]),
                "ANSWER_REPEAT_IDS")
        require(np.array_equal(answer_first["scores"], answer_second["scores"]),
                "ANSWER_REPEAT_SCORES")
        normalized_answer = answer_first["decoded"].strip().rstrip(".").strip().casefold()
        require(normalized_answer == "paris", "ANSWER_SEMANTIC_FIXTURE")

        repair_prompt = render(
            tokenizer,
            repair_template,
            question="In which country is Ada's birth city located?",
            evidence="[Evidence 1 | id=invented-repair | title=Biography]\nAda was born in Northport.",
        )
        repair = generate(
            model, tokenizer, repair_prompt, REPAIR_PREFLIGHT_MAX_NEW_TOKENS, torch
        )
        missing = re.search(r"(?im)^\s*Missing fact:\s*(.+?)\s*$", repair["decoded"])
        query = re.search(r"(?im)^\s*Search query:\s*(.+?)\s*$", repair["decoded"])
        require(missing is not None and bool(missing.group(1).strip()), "REPAIR_MISSING_FACT_LINE")
        require(query is not None and bool(query.group(1).strip()), "REPAIR_SEARCH_QUERY_LINE")

        likelihood_first = teacher_forced(model, tokenizer, answer_prompt, "Paris", torch)
        likelihood_second = teacher_forced(model, tokenizer, answer_prompt, "Paris", torch)
        require(np.array_equal(likelihood_first["logits"], likelihood_second["logits"]),
                "LIKELIHOOD_REPEAT_LOGITS")
        require(np.array_equal(likelihood_first["chosen_log_probabilities"],
                               likelihood_second["chosen_log_probabilities"]),
                "LIKELIHOOD_REPEAT_VALUES")
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
        temporary_witness = witness.with_suffix(witness.suffix + ".part")
        arrays = {
            "answer_prompt_ids_i32": answer_first["prompt_ids"],
            "answer_generated_ids_i32": answer_first["output_ids"],
            "answer_scores_f32": answer_first["scores"],
            "repair_prompt_ids_i32": repair["prompt_ids"],
            "repair_generated_ids_i32": repair["output_ids"],
            "repair_scores_f32": repair["scores"],
            "likelihood_prompt_ids_i32": likelihood_first["prompt_ids"],
            "likelihood_target_ids_i32": likelihood_first["target_ids"],
            "likelihood_logits_f32": likelihood_first["logits"],
            "likelihood_chosen_log_probabilities_f32": likelihood_first["chosen_log_probabilities"],
        }
        with temporary_witness.open("xb") as handle:
            np.savez_compressed(handle, **arrays)
        temporary_witness.replace(witness)
        require(witness.stat().st_size <= MAX_WITNESS_BYTES, "WITNESS_SIZE_LIMIT")

        report = {
            "schema_version": 1,
            "status": "PASS_BOUNDED_MISTRAL_NF4_WHOLE_MODEL_PREFLIGHT",
            "scientific_status": "INVENTED_INPUTS_ONLY_NO_PROJECT_DATA_OR_GOLD",
            "cas_q3_status": "NOT READY",
            "repo_id": REPO_ID,
            "revision": REVISION,
            "script_sha256": sha256(script_path),
            "protocol_sha256": sha256(protocol),
            "asset_manifest_sha256": ASSET_MANIFEST_SHA256,
            "tokenizer_report_sha256": TOKENIZER_REPORT_SHA256,
            "versions": versions,
            "environment": REQUIRED_ENVIRONMENT,
            "seed": SEED,
            "quantization": {
                "load_in_4bit": True,
                "quant_type": "nf4",
                "double_quant": True,
                "compute_dtype": "bfloat16",
                "nonquantized_dtype": "bfloat16",
                "attention_implementation": "eager",
                "linear4bit_module_count": len(linear4),
                "linear4bit_module_names": sorted(linear4),
                "ordinary_linear_module_names": ordinary_linear,
                "parameter_devices": parameter_devices,
                "hf_device_map": device_map,
                "model_memory_footprint_bytes": int(model.get_memory_footprint()),
            },
            "answer_fixture": {
                "invented_only": True,
                "prompt_token_count": len(answer_first["prompt_ids"]),
                "prompt_ids_sha256_int32_le": ids_sha256(answer_first["prompt_ids"]),
                "generated_token_count": len(answer_first["output_ids"]),
                "generated_ids": answer_first["output_ids"].tolist(),
                "generated_ids_sha256_int32_le": ids_sha256(answer_first["output_ids"]),
                "scores_sha256_float32_le": array_sha256(answer_first["scores"]),
                "decoded": answer_first["decoded"],
                "normalized_exact_paris": True,
                "repeat_ids_exact": True,
                "repeat_scores_exact": True,
            },
            "repair_fixture": {
                "invented_only": True,
                "prompt_token_count": len(repair["prompt_ids"]),
                "prompt_ids_sha256_int32_le": ids_sha256(repair["prompt_ids"]),
                "generated_token_count": len(repair["output_ids"]),
                "generated_ids": repair["output_ids"].tolist(),
                "generated_ids_sha256_int32_le": ids_sha256(repair["output_ids"]),
                "scores_sha256_float32_le": array_sha256(repair["scores"]),
                "decoded": repair["decoded"],
                "missing_fact": missing.group(1).strip(),
                "search_query": query.group(1).strip(),
            },
            "likelihood_fixture": {
                "invented_only": True,
                "prompt_token_count": len(likelihood_first["prompt_ids"]),
                "prompt_ids_sha256_int32_le": ids_sha256(likelihood_first["prompt_ids"]),
                "target_token_count": len(likelihood_first["target_ids"]),
                "target_ids": likelihood_first["target_ids"].tolist(),
                "target_ids_sha256_int32_le": ids_sha256(likelihood_first["target_ids"]),
                "logits_sha256_float32_le": array_sha256(likelihood_first["logits"]),
                "chosen_log_probabilities": [float(value) for value in likelihood_first["chosen_log_probabilities"]],
                "repeat_logits_exact": True,
                "repeat_values_exact": True,
            },
            "witness": {
                "path": str(witness),
                "bytes": witness.stat().st_size,
                "sha256": sha256(witness),
                "max_bytes": MAX_WITNESS_BYTES,
                "array_names": sorted(arrays),
            },
            "resources": {
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_capability": list(torch.cuda.get_device_capability(0)),
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
            "model_loads": 1,
            "generation_calls": 3,
            "teacher_forced_calls": 2,
            "project_rows_read": 0,
            "scientific_fits": 0,
            "gold_labels_read": 0,
            "claims": [
                "The exact pinned Mistral model loads fully on CUDA 0 as the frozen NF4/double-quant/BF16 configuration without CPU or disk offload.",
                "Short invented answer, repair and likelihood paths execute deterministically and expose independently checkable full-vocabulary witnesses.",
                "This does not establish worst-case length, full-workload throughput, end-to-end integration or scientific effect.",
            ],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        append_event(attempt_log, {
            "event": "whole_model_preflight_completed",
            "completed_utc": utc_now(),
            "status": report["status"],
            "report": str(output),
            "report_sha256": sha256(output),
            "witness": str(witness),
            "witness_sha256": sha256(witness),
            "model_loads": 1,
            "project_rows_read": 0,
            "gold_labels_read": 0,
            "scientific_fits": 0,
        })
        print(json.dumps({
            "status": report["status"],
            "output": str(output),
            "witness": str(witness),
            "gpu_peak_reserved_bytes": peak_reserved,
            "wall_seconds": wall_seconds,
        }))
        return 0
    except BaseException as error:
        if monitor is not None:
            monitor.stop()
        append_event(attempt_log, {
            "event": "whole_model_preflight_failed",
            "failed_utc": utc_now(),
            "error_type": type(error).__name__,
            "error": str(error),
            "model_load_attempted": model_load_attempted,
            "report_exists": output.exists(),
            "witness_exists": witness.exists(),
            "project_rows_read": 0,
            "gold_labels_read": 0,
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
