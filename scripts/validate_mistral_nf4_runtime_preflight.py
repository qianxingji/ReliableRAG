"""Independent replay of the saved bounded NF4 runtime smoke test."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys


EXPECTED_VERSIONS = {
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


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise RuntimeError(message)
    checks.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-report", required=True, type=Path)
    parser.add_argument("--producer-script", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report_path = args.producer_report.resolve()
    script_path = args.producer_script.resolve()
    overlay = args.overlay.resolve()
    wheelhouse = args.wheelhouse.resolve()
    output = args.output.resolve()
    checks: list[str] = []
    require(not output.exists(), "OUTPUT_ABSENT", checks)
    require(report_path.is_file(), "PRODUCER_REPORT_EXISTS", checks)
    require(script_path.is_file(), "PRODUCER_SCRIPT_EXISTS", checks)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(
        report["status"] == "PASS_BOUNDED_NF4_KERNEL_SMOKE_ONLY",
        "PRODUCER_STATUS",
        checks,
    )
    require(report["cas_q3_status"] == "NOT READY", "NOT_READY_PRESERVED", checks)
    for field in (
        "model_loads", "reader_generations", "project_rows_read",
        "scientific_fits", "gold_labels_read",
    ):
        require(report[field] == 0, "ZERO_" + field.upper(), checks)
    require(sha256(script_path) == report["script_sha256"], "PRODUCER_SCRIPT_HASH", checks)
    producer_wheels = {entry["filename"]: entry for entry in report["wheels"]}
    require(set(producer_wheels) == set(EXPECTED_WHEELS), "WHEEL_NAME_SET", checks)
    for filename, expected in EXPECTED_WHEELS.items():
        wheel = wheelhouse / filename
        require(wheel.is_file(), "WHEEL_EXISTS:" + filename, checks)
        actual = sha256(wheel)
        require(actual == expected, "WHEEL_HASH:" + filename, checks)
        require(producer_wheels[filename]["sha256"] == actual,
                "PRODUCER_WHEEL_HASH:" + filename, checks)
        require(
            producer_wheels[filename]["official_pypi_sha256_matched_before_install"] is True,
            "OFFICIAL_PYPI_MATCH:" + filename,
            checks,
        )

    resolved_sys_path = [Path(entry).resolve() for entry in sys.path if entry]
    require(overlay in resolved_sys_path, "OVERLAY_ON_SYS_PATH", checks)
    overlay_index = resolved_sys_path.index(overlay)
    require(
        all(
            overlay_index < index
            for index, entry in enumerate(resolved_sys_path)
            if entry != overlay and entry.name.casefold() == "site-packages"
        ),
        "OVERLAY_FIRST_SITE_PACKAGES",
        checks,
    )

    import accelerate
    import bitsandbytes as bnb
    import torch
    import transformers

    versions = {
        package: importlib.metadata.version(package) for package in EXPECTED_VERSIONS
    }
    require(versions == EXPECTED_VERSIONS, "VERSION_SET", checks)
    require(Path(accelerate.__file__).resolve().is_relative_to(overlay),
            "ACCELERATE_OVERLAY_ORIGIN", checks)
    require(Path(bnb.__file__).resolve().is_relative_to(overlay),
            "BNB_OVERLAY_ORIGIN", checks)
    require(not Path(torch.__file__).resolve().is_relative_to(overlay),
            "TORCH_PRESERVED_ORIGIN", checks)
    require(not Path(transformers.__file__).resolve().is_relative_to(overlay),
            "TRANSFORMERS_PRESERVED_ORIGIN", checks)
    require(torch.cuda.is_available(), "CUDA_AVAILABLE", checks)
    require(torch.version.cuda == "12.8", "CUDA_12_8", checks)
    require(torch.cuda.get_device_capability(0) == (12, 0), "CUDA_SM120", checks)
    require(torch.cuda.is_bf16_supported(), "BF16_SUPPORTED", checks)

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
    require(layer.weight.quant_state is not None, "NF4_QUANT_STATE", checks)
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
    require(first.shape == (3, 64), "OUTPUT_SHAPE", checks)
    require(first.dtype == torch.bfloat16, "OUTPUT_DTYPE", checks)
    require(torch.isfinite(first).all().item(), "OUTPUT_FINITE", checks)
    require(torch.equal(first, second), "REPEAT_EXACT", checks)
    payload = first.float().cpu().numpy().astype("<f4", copy=False).tobytes()
    replay_hash = hashlib.sha256(payload).hexdigest()
    require(
        replay_hash == report["kernel"]["output_sha256_float32_le"],
        "INDEPENDENT_OUTPUT_HASH",
        checks,
    )

    validation = {
        "schema_version": 1,
        "status": "PASS_INDEPENDENT_BOUNDED_NF4_KERNEL_REPLAY",
        "cas_q3_status": "NOT READY",
        "producer_report_sha256": sha256(report_path),
        "producer_script_sha256": sha256(script_path),
        "validator_script_sha256": sha256(Path(__file__).resolve()),
        "checks": len(checks),
        "check_labels": checks,
        "versions": versions,
        "independent_output_sha256_float32_le": replay_hash,
        "model_loads": 0,
        "reader_generations": 0,
        "project_rows_read": 0,
        "scientific_fits": 0,
        "gold_labels_read": 0,
        "scope_limit": (
            "Kernel replay only; Mistral assets, loading, memory fit, semantic "
            "fixtures, throughput and full-workload feasibility remain untested."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(validation, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": validation["status"], "checks": len(checks),
                      "output": str(output), "output_hash": replay_hash}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
