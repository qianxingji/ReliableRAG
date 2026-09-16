"""Acquire and authenticate the exact nonduplicated Mistral reader snapshot."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback


REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
EXCLUDED_DUPLICATE = "consolidated.safetensors"
FILES = (
    ".gitattributes",
    "README.md",
    "config.json",
    "generation_config.json",
    "model-00001-of-00003.safetensors",
    "model-00002-of-00003.safetensors",
    "model-00003-of-00003.safetensors",
    "model.safetensors.index.json",
    "params.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer.model.v3",
    "tokenizer_config.json",
)
EXPECTED_TOTAL_BYTES = 14_499_392_853
EXPECTED_LFS_SHA256 = {
    "model-00001-of-00003.safetensors":
        "ce6fb6f6f4d0183f4813cbf4ece24109da629a08d4210da46f77e1d8b0bd5c19",
    "model-00002-of-00003.safetensors":
        "8c0e72f148366b6a3709e002a98706a33d31aec8515090c856c95b2044f92ae0",
    "model-00003-of-00003.safetensors":
        "905dd405363e43d95779c1c1155a2dbfd36155914ae95dbd934e12e490cfb4ca",
    "tokenizer.model":
        "37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()


def lfs_value(sibling, name: str):
    value = getattr(sibling, "lfs", None)
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def main() -> int:
    from huggingface_hub import HfApi, snapshot_download

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir", required=True, type=Path)
    parser.add_argument("--attempt-log", required=True, type=Path)
    parser.add_argument("--max-workers", type=int, default=2)
    args = parser.parse_args()
    asset_dir = args.asset_dir.resolve()
    attempt_log = args.attempt_log.resolve()
    require(args.max_workers in (1, 2), "MAX_WORKERS")
    require(not (asset_dir / "ASSET_MANIFEST.json").exists(), "ALREADY_COMPLETE")
    asset_dir.mkdir(parents=True, exist_ok=True)
    attempt = {
        "event": "asset_acquisition_started",
        "started_utc": now(),
        "repo_id": REPO_ID,
        "revision": REVISION,
        "asset_dir": str(asset_dir),
        "python": sys.version,
        "max_workers": args.max_workers,
        "selected_files": list(FILES),
        "excluded_duplicate": EXCLUDED_DUPLICATE,
    }
    append_event(attempt_log, attempt)
    try:
        info = HfApi().model_info(
            repo_id=REPO_ID, revision=REVISION, files_metadata=True
        )
        require(info.sha == REVISION, "REVISION_RESOLUTION")
        require(info.private is False, "MODEL_PRIVATE")
        require(not info.gated, "MODEL_GATED")
        require(info.card_data is not None, "MODEL_CARD_DATA")
        require(info.card_data.get("license") == "apache-2.0", "MODEL_LICENSE")
        remote = {sibling.rfilename: sibling for sibling in info.siblings}
        require(set(FILES) <= set(remote), "REMOTE_SELECTED_FILE_SET")
        require(EXCLUDED_DUPLICATE in remote, "REMOTE_DUPLICATE_PRESENT")
        require(len(remote) == 15, "REMOTE_FILE_COUNT")
        require(
            sum(remote[name].size for name in FILES) == EXPECTED_TOTAL_BYTES,
            "REMOTE_SELECTED_BYTES",
        )
        for name, expected in EXPECTED_LFS_SHA256.items():
            require(lfs_value(remote[name], "sha256") == expected, "REMOTE_LFS_HASH:" + name)

        snapshot = Path(snapshot_download(
            repo_id=REPO_ID,
            revision=REVISION,
            local_dir=asset_dir,
            allow_patterns=list(FILES),
            max_workers=args.max_workers,
        )).resolve()
        require(snapshot == asset_dir, "SNAPSHOT_DESTINATION")
        present = {
            path.relative_to(asset_dir).as_posix()
            for path in asset_dir.rglob("*")
            if path.is_file() and ".cache" not in path.relative_to(asset_dir).parts
        }
        require(present == set(FILES), "LOCAL_SELECTED_FILE_SET")
        require(not (asset_dir / EXCLUDED_DUPLICATE).exists(), "DUPLICATE_DOWNLOADED")
        records = []
        for name in FILES:
            path = asset_dir / name
            sibling = remote[name]
            require(path.stat().st_size == sibling.size, "LOCAL_SIZE:" + name)
            digest = sha256(path)
            lfs_sha = lfs_value(sibling, "sha256")
            blob_id = getattr(sibling, "blob_id", None)
            if lfs_sha is not None:
                require(digest == lfs_sha, "LOCAL_LFS_HASH:" + name)
            elif blob_id is not None:
                require(git_blob_sha1(path) == blob_id, "LOCAL_GIT_BLOB:" + name)
            records.append({
                "path": name,
                "size_bytes": path.stat().st_size,
                "sha256": digest,
                "remote_lfs_sha256": lfs_sha,
                "remote_git_blob_sha1": blob_id,
            })
        require(sum(record["size_bytes"] for record in records) == EXPECTED_TOTAL_BYTES,
                "LOCAL_SELECTED_BYTES")
        index = json.loads((asset_dir / "model.safetensors.index.json").read_text())
        shards = set(index["weight_map"].values())
        expected_shards = {
            "model-00001-of-00003.safetensors",
            "model-00002-of-00003.safetensors",
            "model-00003-of-00003.safetensors",
        }
        require(shards == expected_shards, "INDEX_SHARD_SET")
        config = json.loads((asset_dir / "config.json").read_text())
        require(config["model_type"] == "mistral", "MODEL_TYPE")
        require(config["architectures"] == ["MistralForCausalLM"], "ARCHITECTURE")
        manifest = {
            "schema_version": 1,
            "status": "PASS_EXACT_MISTRAL_ASSET_ACQUISITION",
            "repo_id": REPO_ID,
            "requested_revision": REVISION,
            "resolved_revision": info.sha,
            "license": info.card_data.get("license"),
            "private": info.private,
            "gated": info.gated,
            "selected_files": records,
            "selected_file_count": len(records),
            "selected_total_bytes": sum(record["size_bytes"] for record in records),
            "excluded_duplicate": {
                "path": EXCLUDED_DUPLICATE,
                "size_bytes": remote[EXCLUDED_DUPLICATE].size,
                "lfs_sha256": lfs_value(remote[EXCLUDED_DUPLICATE], "sha256"),
                "reason": "Duplicate full-precision serialization; Transformers sharded weights selected.",
            },
            "weight_index_entries": len(index["weight_map"]),
            "weight_shards": sorted(shards),
            "model_type": config["model_type"],
            "architectures": config["architectures"],
            "completed_utc": now(),
            "model_loads": 0,
            "reader_generations": 0,
            "project_rows_read": 0,
            "scientific_fits": 0,
            "gold_labels_read": 0,
            "cas_q3_status": "NOT READY",
        }
        manifest_path = asset_dir / "ASSET_MANIFEST.json"
        with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        append_event(attempt_log, {
            "event": "asset_acquisition_completed",
            "completed_utc": now(),
            "manifest": str(manifest_path),
            "manifest_sha256": sha256(manifest_path),
            "selected_total_bytes": manifest["selected_total_bytes"],
        })
        print(json.dumps({
            "status": manifest["status"],
            "manifest": str(manifest_path),
            "manifest_sha256": sha256(manifest_path),
            "selected_total_bytes": manifest["selected_total_bytes"],
        }))
        return 0
    except Exception as exc:
        append_event(attempt_log, {
            "event": "asset_acquisition_failed",
            "failed_utc": now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })
        raise


if __name__ == "__main__":
    raise SystemExit(main())
