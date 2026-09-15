"""Shared non-scientific primitives for the frozen Phi reader preflight."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs/cas_q2/phi_reader_gpu_preflight_v1"
VALIDATION = REPO / "outputs/cas_q2/phi_reader_gpu_preflight_validation_v1"
PHI_MODEL = "microsoft/Phi-3.5-mini-instruct"
PHI_REVISION = "2fe192450127e6a83f7441aef6e3ca586c338b77"
PHI_RELATIVE = Path("data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct/snapshots") / PHI_REVISION
EXPECTED_WEIGHT_BYTES = 7_642_159_104
RUNTIME_SEED = 20260830


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def object_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(8 << 20):
            h.update(block)
    return h.hexdigest()


def record(path: Path) -> dict:
    path = Path(path).resolve()
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest(path)}


def load(path: Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path = Path(path)
    require(not path.exists(), f"refuse overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n")


def seal(output: Path) -> None:
    files = [record(path) for path in sorted(output.rglob("*")) if path.is_file()]
    for row in files:
        row["path"] = Path(row["path"]).relative_to(output).as_posix()
    write_json(output / "SHA256_MANIFEST.json", {
        "status": "PASS",
        "files": files,
        "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def verify_namespace(output: Path) -> list[Path]:
    manifest = load(output / "SHA256_MANIFEST.json")
    expected = {row["path"] for row in manifest["files"]} | {"SHA256_MANIFEST.json"}
    actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
    require(actual == expected, "preflight namespace file set")
    paths = [output / "SHA256_MANIFEST.json"]
    for row in manifest["files"]:
        path = output / row["path"]
        require(record(path)["size_bytes"] == row["size_bytes"] and digest(path) == row["sha256"], "preflight namespace digest")
        paths.append(path)
    return paths


def configure_environment(output: Path) -> dict:
    temp = output / "cache/tmp"
    temp.mkdir(parents=True, exist_ok=True)
    values = {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        "TOKENIZERS_PARALLELISM": "false",
        "PYTHONDONTWRITEBYTECODE": "1",
        "CUDA_CACHE_PATH": str(output / "cache/cuda"),
        "TORCH_HOME": str(output / "cache/torch"),
        "HF_HOME": str(output / "cache/hf"),
        "TMP": str(temp),
        "TEMP": str(temp),
        "TMPDIR": str(temp),
    }
    os.environ.update(values)
    return values


def configure_torch(torch) -> None:
    require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(), "Phi preflight requires CUDA BF16")
    import random
    import numpy as np

    random.seed(RUNTIME_SEED)
    np.random.seed(RUNTIME_SEED)
    torch.manual_seed(RUNTIME_SEED)
    torch.cuda.manual_seed_all(RUNTIME_SEED)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.cuda.init()
    torch.cuda.reset_peak_memory_stats()


def invented_evidence_rows(*, long: bool = False) -> list[dict]:
    rows = []
    for index in range(5):
        if long:
            body = " ".join(f"invented_{index}_{token:05d}" for token in range(1500))
        else:
            body = "In this invented toy scene, the paper cog is silver and rests beside a blue cube."
        rows.append({"rank": index + 1, "document_id": f"invented-doc-{index}", "content_hash": text_sha(body),
            "score": float(5 - index), "title": f"Invented {index}", "text": body})
    return rows


def invented_evidence(native, *, long: bool = False):
    return tuple(native.RankedDocument(row["rank"], row["document_id"], row["content_hash"], row["score"], row["title"], row["text"])
        for row in invented_evidence_rows(long=long))


def compact_evidence(evidence) -> list[dict]:
    return [{
        "rank": int(row.rank),
        "document_id": str(row.document_id),
        "content_hash": str(row.content_hash),
        "score": float(row.score),
        "title": str(row.title),
        "text": str(row.text),
    } for row in evidence]


def render_evidence(evidence: list[dict], budget: int = 16000) -> tuple[str, bool, list[bool]]:
    """Independently reproduce the answer-likelihood scorer's renderer."""
    context = ""
    truncated = False
    per_document = []
    for row in evidence:
        header = f"[Evidence {int(row['rank'])} | id={row['document_id']} | title={row['title']}]\n"
        separator = "\n\n" if context else ""
        available = budget - len(context) - len(separator)
        if available <= len(header):
            truncated = True
            per_document.append(True)
            continue
        body = str(row["text"]).strip()
        included = body[: available - len(header)]
        context += separator + header + included
        cut = len(included) < len(body)
        truncated |= cut
        per_document.append(cut)
    return context, truncated, per_document


def render_generation_evidence(evidence: list[dict], budget: int = 16000) -> tuple[str, bool, list[bool]]:
    """Independently reproduce Phase-10's all-five-headers renderer."""
    require(len(evidence) == 5 and [row["rank"] for row in evidence] == [1, 2, 3, 4, 5], "generation evidence ranks")
    headers = [f"[Evidence {int(row['rank'])} | id={row['document_id']} | title={row['title']}]\n" for row in evidence]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = budget - sum(len(separator) + len(header) for separator, header in zip(separators, headers, strict=True))
    require(remaining >= 0, "generation evidence headers fit budget")
    chunks, flags = [], []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip()
        included = body[:remaining]
        remaining -= len(included)
        chunks.append(separator + header + included)
        flags.append(len(included) < len(body))
    text = "".join(chunks)
    require(len(text) <= budget and all(row["document_id"] in text for row in evidence), "generation evidence identity/budget")
    return text, any(flags), flags


def parse_answer(raw: str) -> str:
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    if not lines:
        return ""
    answer = re.sub(r"^(?:final\s+)?answer\s*:\s*", "", lines[0], flags=re.I)
    answer = re.sub(r"^the answer is\s+", "", answer, flags=re.I)
    return answer.strip()


def parse_query(raw: str, question: str) -> tuple[str, bool]:
    matches = [value.strip() for value in re.findall(r"(?im)^\s*search\s+query\s*:\s*(.*?)\s*$", raw) if value.strip()]
    if matches:
        return matches[0], False
    query = next((line.strip() for line in reversed(raw.splitlines()) if line.strip()), question)
    return (query or question), True


def validate_logit_witness(witness: dict, tolerance: float = 1e-7) -> None:
    chosen = witness["chosen_logits"]
    normalizers = witness["log_normalizers"]
    values = witness["token_log_probabilities"]
    require(len(chosen) == len(normalizers) == len(values) == witness["answer_token_count"], "logit witness lengths")
    for a, b, value in zip(chosen, normalizers, values, strict=True):
        require(all(type(x) in (int, float) and math.isfinite(x) for x in (a, b, value)), "finite logit witness")
        require(abs((a - b) - value) <= tolerance, "independent chosen-logit normalization")
