"""Exact, hash-bound correction for the sealed base CUDA metadata alias.

This module never rewrites a receipt.  It accepts only the one prospectively
reviewed representation found in the sealed base stage: model metadata records
the constructor's generic ``torch.device("cuda")`` string while the pre-forward
counter records every actual input tensor on ``cuda:0``.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.empirical_neural_checks import Checks
from scripts.empirical_pool_io import load


BASE_MANIFEST_SHA256 = "6cbc051be274617e26f548f4b51b5a6ec3cddeb5e1caf6761f00fa8301913cab"
BASE_RECEIPT_SHA256 = "6a8fba007045a2eba50db74ca14e6bc216cc337681836240d4e9c9da58ba1989"
BASE_SOURCE_COMMIT = "842f2c2f20294a997bd7bcc73bae3cc5ae249be0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(2 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_device_alias(metadata, actual, *, calls, rows, tokens, audit=None):
    """Require the exact reviewed metadata/tensor observation without mutation."""
    a = audit if audit is not None else Checks()
    a.exact(metadata["device"], "cuda", "generic constructor CUDA metadata")
    a.exact(actual, {
        "attempted_forward_calls": calls,
        "attempted_input_rows": rows,
        "attempted_input_tokens_including_padding": tokens,
        "devices": ["cuda:0"],
    }, "actual single-device forward counter")
    return a


def validate_frozen_base_device_alias(base: Path, audit=None):
    """Bind the exception to one immutable base manifest and receipt."""
    a = audit if audit is not None else Checks()
    base = Path(base).resolve()
    manifest_path, receipt_path = base / "SHA256_MANIFEST.json", base / "BUILD_RECEIPT.json"
    a.exact(sha256(manifest_path), BASE_MANIFEST_SHA256, "exact reviewed base manifest")
    a.exact(sha256(receipt_path), BASE_RECEIPT_SHA256, "exact reviewed base receipt")
    manifest = load(manifest_path)
    receipt_entry = [entry for entry in manifest["files"] if entry["path"] == "BUILD_RECEIPT.json"]
    a.require(len(receipt_entry) == 1, "one base receipt manifest entry")
    a.exact(receipt_entry[0], {
        "path": "BUILD_RECEIPT.json",
        "sha256": BASE_RECEIPT_SHA256,
        "size_bytes": receipt_path.stat().st_size,
    }, "manifest-bound base receipt")
    receipt = load(receipt_path)
    a.exact(receipt["source_commit"], BASE_SOURCE_COMMIT, "reviewed base source commit")
    a.exact(receipt["status"], "COMPLETED_NATIVE_BASE_PENDING_INDEPENDENT",
            "completed sealed base status")
    before = a.count
    exact_device_alias(receipt["bge"]["metadata"], receipt["bge"]["actual"],
                       calls=2250, rows=36000, tokens=342496, audit=a)
    exact_device_alias(receipt["qwen"]["metadata"], receipt["qwen"]["actual"],
                       calls=16932, rows=16932, tokens=16458213, audit=a)
    return {
        "status": "PASS_EXACT_BASE_DEVICE_ALIAS_CORRIGENDUM_V2",
        "base_manifest_sha256": BASE_MANIFEST_SHA256,
        "base_receipt_sha256": BASE_RECEIPT_SHA256,
        "source_commit": BASE_SOURCE_COMMIT,
        "checks": a.count - before + 6,
        "metadata_device": "cuda",
        "observed_forward_device": "cuda:0",
        "receipt_mutated": False,
        "generic_cuda_alias_acceptance": False,
    }
