"""Value-blind primitives for the Mistral development/test input freeze."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Sequence


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
VALIDATION = REPO / "outputs/cas_q3/mistral_reader_input_freeze_validation_v1"
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
STAGES = ("a0", "repair_query", "a1")
MAXIMUM_GENERATION_INPUT_TOKENS = 8192
CONTEXT_BUDGET_CHARACTERS = 16000


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def record(path: Path) -> dict[str, object]:
    path = Path(path).resolve()
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest(path)}


def object_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load(path: Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path: Path):
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def write_json(path: Path, value: object) -> None:
    path = Path(path)
    require(not path.exists(), "REFUSE_OVERWRITE:" + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                   allow_nan=False).encode("utf-8") + b"\n"
    )


def seal(output: Path) -> None:
    files = [record(path) for path in sorted(output.rglob("*")) if path.is_file()]
    for item in files:
        item["path"] = Path(str(item["path"])).relative_to(output).as_posix()
    write_json(output / "SHA256_MANIFEST.json", {
        "status": "PASS",
        "files": files,
        "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def render_generation_evidence(
    evidence: Sequence[dict], budget: int = CONTEXT_BUDGET_CHARACTERS,
) -> tuple[str, bool, list[bool]]:
    require(len(evidence) == 5, "EXACT_FIVE_EVIDENCE_ROWS")
    require([row["rank"] for row in evidence] == [1, 2, 3, 4, 5],
            "CANONICAL_EVIDENCE_RANKS")
    require(len({row["document_id"] for row in evidence}) == 5,
            "UNIQUE_EVIDENCE_DOCUMENTS")
    headers = [
        f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n"
        for row in evidence
    ]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = budget - sum(
        len(separator) + len(header)
        for separator, header in zip(separators, headers, strict=True)
    )
    require(remaining >= 0, "EVIDENCE_HEADERS_FIT")
    chunks: list[str] = []
    flags: list[bool] = []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip()
        included = body[:remaining]
        remaining -= len(included)
        chunks.append(separator + header + included)
        flags.append(len(included) < len(body))
    rendered = "".join(chunks)
    require(len(rendered) <= budget, "CONTEXT_BUDGET")
    require(all(row["document_id"] in rendered for row in evidence), "ALL_HEADERS_RETAINED")
    return rendered, any(flags), flags


def prompt_metadata(
    tokenizer, template: str, question: str, evidence: Sequence[dict],
) -> dict[str, object]:
    rendered, truncated, per_document = render_generation_evidence(evidence)
    user = template.format(question=question, evidence=rendered)
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )
    ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    return {
        "prompt_sha256": text_sha(prompt),
        "input_token_ids_sha256": object_sha(ids),
        "input_tokens": len(ids),
        "rendered_context_characters": len(rendered),
        "context_truncated": truncated,
        "per_document_truncated": per_document,
    }


def _shape(value) -> tuple[int, int]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        require(len(shape) == 2, "GENERATION_INPUT_RANK")
        return int(shape[0]), int(shape[1])
    require(isinstance(value, Sequence) and len(value) == 1 and
            isinstance(value[0], Sequence), "SINGLE_GENERATION_INPUT_ROW")
    return 1, len(value[0])


def require_generation_admission(*, stage: str, input_ids, attention_mask) -> int:
    """Reject an unsafe generation input before CUDA/model access."""

    require(stage in STAGES, "UNKNOWN_MISTRAL_GENERATION_STAGE")
    rows_count, width = _shape(input_ids)
    mask_rows, mask_width = _shape(attention_mask)
    require(rows_count == mask_rows == 1 and width == mask_width,
            "SINGLE_ALIGNED_GENERATION_ROW")
    require(0 < width <= MAXIMUM_GENERATION_INPUT_TOKENS,
            "MISTRAL_GENERATION_INPUT_EXCEEDS_GUARD")
    mask = attention_mask[0]
    if hasattr(mask, "tolist"):
        mask = mask.tolist()
    require(list(mask) == [1] * width, "GENERATION_ATTENTION_MASK_ALL_ONE")
    return width


def compact_document(row: dict, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "document_id": row["id"],
        "title": row["title"],
        "text": row["title"] + "\n" + "".join(row["sentences"]),
        "content_hash": row["content_hash"],
    }


def configure_tokenizer_environment(output: Path) -> None:
    cache = output / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.update({
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HF_HOME": str(cache / "hf"),
        "TMP": str(cache / "tmp"),
        "TEMP": str(cache / "tmp"),
        "TMPDIR": str(cache / "tmp"),
    })
