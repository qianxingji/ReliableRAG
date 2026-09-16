"""Independently validate exact Mistral assets without loading model tensors."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct


REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
FILES = {
    ".gitattributes", "README.md", "config.json", "generation_config.json",
    "model-00001-of-00003.safetensors", "model-00002-of-00003.safetensors",
    "model-00003-of-00003.safetensors", "model.safetensors.index.json",
    "params.json", "special_tokens_map.json", "tokenizer.json",
    "tokenizer.model", "tokenizer.model.v3", "tokenizer_config.json",
}
SHARDS = {
    "model-00001-of-00003.safetensors",
    "model-00002-of-00003.safetensors",
    "model-00003-of-00003.safetensors",
}
TOTAL_BYTES = 14_499_392_853
PARAMETERS = 7_248_023_552
TENSOR_BYTES = 14_496_047_104
LFS_SHA256 = {
    "model-00001-of-00003.safetensors":
        "ce6fb6f6f4d0183f4813cbf4ece24109da629a08d4210da46f77e1d8b0bd5c19",
    "model-00002-of-00003.safetensors":
        "8c0e72f148366b6a3709e002a98706a33d31aec8515090c856c95b2044f92ae0",
    "model-00003-of-00003.safetensors":
        "905dd405363e43d95779c1c1155a2dbfd36155914ae95dbd934e12e490cfb4ca",
    "tokenizer.model":
        "37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {path.stat().st_size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, label: str, checks: list[str]) -> None:
    if not condition:
        raise RuntimeError(label)
    checks.append(label)


def lfs_value(sibling, name: str):
    value = getattr(sibling, "lfs", None)
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def read_safetensors_header(path: Path) -> tuple[int, dict]:
    with path.open("rb") as handle:
        prefix = handle.read(8)
        if len(prefix) != 8:
            raise RuntimeError("SAFETENSORS_PREFIX:" + path.name)
        header_bytes = struct.unpack("<Q", prefix)[0]
        if not 2 <= header_bytes <= 16 * 1024 * 1024:
            raise RuntimeError("SAFETENSORS_HEADER_SIZE:" + path.name)
        header = json.loads(handle.read(header_bytes))
    return header_bytes, header


def main() -> int:
    from huggingface_hub import HfApi

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--attempt-log", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    asset_dir = args.asset_dir.resolve()
    manifest_path = args.manifest.resolve()
    attempt_log = args.attempt_log.resolve()
    output = args.output.resolve()
    checks: list[str] = []
    require(not output.exists(), "OUTPUT_ABSENT", checks)
    require(asset_dir.is_dir(), "ASSET_DIR", checks)
    require(manifest_path.is_file(), "MANIFEST_EXISTS", checks)
    require(attempt_log.is_file(), "ATTEMPT_LOG_EXISTS", checks)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest["status"] == "PASS_EXACT_MISTRAL_ASSET_ACQUISITION",
            "MANIFEST_STATUS", checks)
    require(manifest["repo_id"] == REPO_ID, "MANIFEST_REPO", checks)
    require(manifest["requested_revision"] == manifest["resolved_revision"] == REVISION,
            "MANIFEST_REVISION", checks)
    require(manifest["license"] == "apache-2.0", "MANIFEST_LICENSE", checks)
    require(manifest["private"] is False and manifest["gated"] is False,
            "MANIFEST_ACCESS", checks)
    for field in ("model_loads", "reader_generations", "project_rows_read",
                  "scientific_fits", "gold_labels_read"):
        require(manifest[field] == 0, "ZERO_" + field.upper(), checks)
    require(manifest["cas_q3_status"] == "NOT READY", "NOT_READY", checks)

    info = HfApi().model_info(repo_id=REPO_ID, revision=REVISION, files_metadata=True)
    require(info.sha == REVISION, "REMOTE_REVISION", checks)
    require(info.private is False and not info.gated, "REMOTE_ACCESS", checks)
    require(info.card_data is not None and info.card_data.get("license") == "apache-2.0",
            "REMOTE_LICENSE", checks)
    remote = {sibling.rfilename: sibling for sibling in info.siblings}
    require(set(remote) == FILES | {"consolidated.safetensors"},
            "REMOTE_FILE_SET", checks)

    records = {record["path"]: record for record in manifest["selected_files"]}
    require(set(records) == FILES, "MANIFEST_FILE_SET", checks)
    local_files = {
        path.relative_to(asset_dir).as_posix()
        for path in asset_dir.rglob("*")
        if path.is_file()
        and ".cache" not in path.relative_to(asset_dir).parts
        and path.name != "ASSET_MANIFEST.json"
    }
    require(local_files == FILES, "LOCAL_FILE_SET", checks)
    require(not (asset_dir / "consolidated.safetensors").exists(),
            "CONSOLIDATED_EXCLUDED", checks)
    verified = []
    for name in sorted(FILES):
        path = asset_dir / name
        record = records[name]
        sibling = remote[name]
        require(path.stat().st_size == record["size_bytes"] == sibling.size,
                "SIZE:" + name, checks)
        digest = sha256(path)
        require(digest == record["sha256"], "SHA256:" + name, checks)
        remote_lfs = lfs_value(sibling, "sha256")
        remote_blob = getattr(sibling, "blob_id", None)
        require(record["remote_lfs_sha256"] == remote_lfs,
                "REMOTE_LFS_BINDING:" + name, checks)
        require(record["remote_git_blob_sha1"] == remote_blob,
                "REMOTE_BLOB_BINDING:" + name, checks)
        if name in LFS_SHA256:
            require(remote_lfs == digest == LFS_SHA256[name],
                    "LFS_SHA256:" + name, checks)
        else:
            require(remote_lfs is None, "NON_LFS:" + name, checks)
            require(git_blob_sha1(path) == remote_blob, "GIT_BLOB:" + name, checks)
        verified.append({"path": name, "size_bytes": path.stat().st_size,
                         "sha256": digest})
    require(sum(item["size_bytes"] for item in verified) == TOTAL_BYTES,
            "TOTAL_SELECTED_BYTES", checks)

    index = json.loads((asset_dir / "model.safetensors.index.json").read_text())
    weight_map = index["weight_map"]
    require(len(weight_map) == 291, "WEIGHT_INDEX_COUNT", checks)
    require(set(weight_map.values()) == SHARDS, "WEIGHT_INDEX_SHARDS", checks)
    require(index["metadata"]["total_size"] == TENSOR_BYTES,
            "WEIGHT_INDEX_TOTAL_SIZE", checks)
    tensor_names: set[str] = set()
    parameter_count = 0
    tensor_bytes = 0
    dtype_counts = Counter()
    shard_summary = []
    for shard in sorted(SHARDS):
        path = asset_dir / shard
        header_bytes, header = read_safetensors_header(path)
        entries = {name: entry for name, entry in header.items() if name != "__metadata__"}
        expected_names = {name for name, filename in weight_map.items() if filename == shard}
        require(set(entries) == expected_names, "HEADER_INDEX_NAMES:" + shard, checks)
        require(tensor_names.isdisjoint(entries), "UNIQUE_TENSORS:" + shard, checks)
        tensor_names.update(entries)
        ordered_offsets = []
        shard_parameters = 0
        for name, entry in entries.items():
            require(entry["dtype"] == "BF16", "DTYPE:" + name, checks)
            shape = entry["shape"]
            require(all(isinstance(value, int) and value >= 0 for value in shape),
                    "SHAPE:" + name, checks)
            parameters = math.prod(shape)
            start, end = entry["data_offsets"]
            require(0 <= start <= end, "OFFSETS:" + name, checks)
            require(end - start == parameters * 2, "TENSOR_BYTES:" + name, checks)
            ordered_offsets.append((start, end, name))
            parameter_count += parameters
            shard_parameters += parameters
            tensor_bytes += end - start
            dtype_counts[entry["dtype"]] += 1
        ordered_offsets.sort()
        require(ordered_offsets[0][0] == 0, "SHARD_FIRST_OFFSET:" + shard, checks)
        require(all(ordered_offsets[i - 1][1] == ordered_offsets[i][0]
                    for i in range(1, len(ordered_offsets))),
                "SHARD_CONTIGUOUS:" + shard, checks)
        payload_bytes = path.stat().st_size - 8 - header_bytes
        require(ordered_offsets[-1][1] == payload_bytes,
                "SHARD_FINAL_OFFSET:" + shard, checks)
        shard_summary.append({"path": shard, "header_bytes": header_bytes,
                              "tensors": len(entries), "parameters": shard_parameters,
                              "payload_bytes": payload_bytes})
    require(tensor_names == set(weight_map), "ALL_TENSOR_NAMES", checks)
    require(parameter_count == PARAMETERS, "PARAMETER_COUNT", checks)
    require(tensor_bytes == TENSOR_BYTES, "TENSOR_BYTE_COUNT", checks)
    require(dtype_counts == Counter({"BF16": 291}), "DTYPE_COUNTS", checks)

    config = json.loads((asset_dir / "config.json").read_text())
    expected_config = {
        "model_type": "mistral", "architectures": ["MistralForCausalLM"],
        "hidden_size": 4096, "intermediate_size": 14336,
        "num_hidden_layers": 32, "num_attention_heads": 32,
        "num_key_value_heads": 8, "vocab_size": 32768,
        "max_position_embeddings": 32768, "torch_dtype": "bfloat16",
        "bos_token_id": 1, "eos_token_id": 2,
    }
    require(all(config[key] == value for key, value in expected_config.items()),
            "CONFIG_IDENTITY", checks)
    require(sha256(asset_dir / "tokenizer.model") ==
            sha256(asset_dir / "tokenizer.model.v3"),
            "TOKENIZER_MODEL_BYTES_EQUAL", checks)

    attempt_rows = [json.loads(line) for line in attempt_log.read_text(encoding="utf-8").splitlines()
                    if line.strip()]
    attempt_events = Counter(row["event"] for row in attempt_rows)
    require(attempt_events["asset_acquisition_started"] == 2,
            "TWO_RECORDED_STARTS", checks)
    require(attempt_events["asset_acquisition_interrupted_after_no_payload_progress"] == 1,
            "HTTP_FAILURE_PRESERVED", checks)
    require(attempt_events["asset_acquisition_completed"] == 1,
            "ONE_COMPLETION", checks)
    require(attempt_rows[-1]["manifest_sha256"] == sha256(manifest_path),
            "COMPLETION_MANIFEST_HASH", checks)

    result = {
        "schema_version": 1,
        "status": "PASS_INDEPENDENT_EXACT_MISTRAL_ASSET_VALIDATION",
        "cas_q3_status": "NOT READY",
        "repo_id": REPO_ID,
        "revision": REVISION,
        "manifest_sha256": sha256(manifest_path),
        "attempt_log_sha256": sha256(attempt_log),
        "validated_files": verified,
        "selected_file_count": len(verified),
        "selected_total_bytes": sum(item["size_bytes"] for item in verified),
        "weight_tensor_count": len(tensor_names),
        "weight_parameter_count": parameter_count,
        "weight_tensor_bytes": tensor_bytes,
        "weight_dtype_counts": dict(dtype_counts),
        "weight_shards": shard_summary,
        "config_identity": expected_config,
        "attempt_events": dict(attempt_events),
        "checks": len(checks),
        "model_loads": 0,
        "reader_generations": 0,
        "project_rows_read": 0,
        "scientific_fits": 0,
        "gold_labels_read": 0,
        "scope_limit": (
            "Asset and safetensors structure only; tokenizer semantics, model "
            "loading, quantized memory fit, generation and scoring remain untested."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "checks": len(checks),
                      "files": len(verified), "parameters": parameter_count,
                      "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
