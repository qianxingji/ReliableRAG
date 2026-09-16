"""Bounded NF4 runtime smoke test; never loads a reader or project data."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys


EXPECTED = {
    "torch": "2.7.1+cu128",
    "transformers": "4.53.2",
    "bitsandbytes": "0.50.2",
    "accelerate": "1.8.1",
}
EXPECTED_WHEELS = {
    "accelerate-1.8.1-py3-none-any.whl":
        "c47b8994498875a2b1286e945bd4d20e476956056c7941d512334f4eb44ff991",
    "bitsandbytes-0.50.2-py3-none-win_amd64.whl":
        "c697963c8fda3dcd0d7ebd9b5211ae4067feef7cd06e0350d4e816a434fe683d",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    overlay = args.overlay.resolve()
    wheelhouse = args.wheelhouse.resolve()
    output = args.output.resolve()
    require(overlay.is_dir(), "OVERLAY_MISSING")
    require(wheelhouse.is_dir(), "WHEELHOUSE_MISSING")
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")

    # The script directory normally remains sys.path[0]. Require the isolated
    # overlay to precede every site-packages directory instead.
    resolved_sys_path = [Path(entry).resolve() for entry in sys.path if entry]
    require(overlay in resolved_sys_path, "OVERLAY_NOT_ON_SYS_PATH")
    overlay_index = resolved_sys_path.index(overlay)
    require(
        all(
            overlay_index < index
            for index, entry in enumerate(resolved_sys_path)
            if entry != overlay and entry.name.casefold() == "site-packages"
        ),
        "OVERLAY_NOT_FIRST_SITE_PACKAGES",
    )
    wheels = []
    for filename, expected_digest in EXPECTED_WHEELS.items():
        path = wheelhouse / filename
        require(path.is_file(), "WHEEL_MISSING:" + filename)
        actual_digest = sha256(path)
        require(actual_digest == expected_digest, "WHEEL_HASH:" + filename)
        wheels.append({
            "filename": filename,
            "bytes": path.stat().st_size,
            "sha256": actual_digest,
            "official_pypi_sha256_matched_before_install": True,
        })

    import accelerate
    import bitsandbytes as bnb
    import numpy as np
    import torch
    import transformers

    versions = {
        package: importlib.metadata.version(package) for package in EXPECTED
    }
    require(versions == EXPECTED, "VERSION_SET")
    require(Path(accelerate.__file__).resolve().is_relative_to(overlay), "ACCELERATE_ORIGIN")
    require(Path(bnb.__file__).resolve().is_relative_to(overlay), "BNB_ORIGIN")
    require(not Path(torch.__file__).resolve().is_relative_to(overlay), "TORCH_ORIGIN")
    require(not Path(transformers.__file__).resolve().is_relative_to(overlay), "TRANSFORMERS_ORIGIN")
    require(torch.cuda.is_available(), "CUDA_UNAVAILABLE")
    require(torch.version.cuda == "12.8", "CUDA_RUNTIME")
    require(torch.cuda.device_count() == 1, "CUDA_DEVICE_COUNT")
    require(torch.cuda.get_device_capability(0) == (12, 0), "CUDA_CAPABILITY")
    require(torch.cuda.is_bf16_supported(), "BF16_UNSUPPORTED")

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(0)
    free_before, total = torch.cuda.mem_get_info(0)
    input_width, output_width = 128, 64
    layer = bnb.nn.Linear4bit(
        input_width,
        output_width,
        bias=False,
        compute_dtype=torch.bfloat16,
        compress_statistics=True,
        quant_type="nf4",
    )
    weight = (
        torch.arange(output_width * input_width, dtype=torch.float32)
        .reshape(output_width, input_width)
        .remainder(257)
        .sub(128)
        .div(512)
    )
    with torch.no_grad():
        layer.weight.copy_(weight)
    layer = layer.to("cuda:0")
    require(layer.weight.quant_state is not None, "NF4_QUANT_STATE_MISSING")
    values = (
        torch.arange(3 * input_width, device="cuda:0", dtype=torch.float32)
        .reshape(3, input_width)
        .remainder(61)
        .sub(30)
        .div(64)
        .to(torch.bfloat16)
    )
    with torch.inference_mode():
        first = layer(values)
        second = layer(values)
    torch.cuda.synchronize(0)
    require(first.shape == (3, output_width), "OUTPUT_SHAPE")
    require(first.dtype == torch.bfloat16, "OUTPUT_DTYPE")
    require(torch.isfinite(first).all().item(), "NONFINITE_OUTPUT")
    require(torch.equal(first, second), "REPEATED_FORWARD_MISMATCH")
    output_bytes = first.float().cpu().numpy().astype("<f4", copy=False).tobytes()
    free_after, total_after = torch.cuda.mem_get_info(0)
    require(total_after == total, "GPU_TOTAL_CHANGED")

    report = {
        "schema_version": 1,
        "status": "PASS_BOUNDED_NF4_KERNEL_SMOKE_ONLY",
        "scientific_status": "NO_READER_MODEL_OR_PROJECT_DATA_EXECUTED",
        "cas_q3_status": "NOT READY",
        "script_sha256": sha256(Path(__file__).resolve()),
        "python": sys.version,
        "python_executable": str(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "versions": versions,
        "origins": {
            "accelerate": str(Path(accelerate.__file__).resolve()),
            "bitsandbytes": str(Path(bnb.__file__).resolve()),
            "torch": str(Path(torch.__file__).resolve()),
            "transformers": str(Path(transformers.__file__).resolve()),
        },
        "wheels": wheels,
        "cuda": {
            "runtime": torch.version.cuda,
            "device": torch.cuda.get_device_name(0),
            "capability": list(torch.cuda.get_device_capability(0)),
            "bf16_supported": torch.cuda.is_bf16_supported(),
            "total_bytes": total,
            "free_before_bytes": free_before,
            "free_after_bytes": free_after,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(0),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(0),
        },
        "kernel": {
            "layer": "bitsandbytes.nn.Linear4bit",
            "quant_type": "nf4",
            "double_quant": True,
            "compute_dtype": "bfloat16",
            "input_shape": [3, input_width],
            "output_shape": list(first.shape),
            "output_dtype": str(first.dtype),
            "output_sha256_float32_le": hashlib.sha256(output_bytes).hexdigest(),
            "repeat_exact": True,
            "finite": True,
        },
        "model_loads": 0,
        "reader_generations": 0,
        "project_rows_read": 0,
        "scientific_fits": 0,
        "gold_labels_read": 0,
        "claims": [
            "The pinned Windows CUDA 12.8 NF4 kernel executes on this sm120 GPU.",
            "This does not prove Mistral model loading, memory fit, semantic correctness, throughput, or replay acceptance.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "output": str(output),
                      "output_hash": report["kernel"]["output_sha256_float32_le"],
                      "peak_reserved_bytes": report["cuda"]["peak_reserved_bytes"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
