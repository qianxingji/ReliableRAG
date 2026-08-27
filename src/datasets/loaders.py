"""Load and normalize the official HotpotQA and 2WikiMultiHopQA JSON files."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .schema import (
    Document,
    EvaluationOnlyAnnotations,
    GoldSupportingFact,
    NormalizedExample,
)

HOTPOTQA = "hotpotqa"
TWOWIKI = "2wikimultihopqa"


class DatasetFormatError(ValueError):
    """Raised when a source row does not match the documented public format."""


def _require_string(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DatasetFormatError(f"Expected non-empty string field {key!r}")
    return value


def _normalize_documents(raw_context: Any) -> tuple[Document, ...]:
    if not isinstance(raw_context, Sequence) or isinstance(raw_context, (str, bytes)):
        raise DatasetFormatError("Expected 'context' to be a sequence of paragraphs")

    documents: list[Document] = []
    for paragraph_index, paragraph in enumerate(raw_context):
        if (
            not isinstance(paragraph, Sequence)
            or isinstance(paragraph, (str, bytes))
            or len(paragraph) != 2
        ):
            raise DatasetFormatError(
                f"Context paragraph {paragraph_index} must be [title, sentences]"
            )
        title, raw_sentences = paragraph
        if not isinstance(title, str):
            raise DatasetFormatError(
                f"Context paragraph {paragraph_index} has a non-string title"
            )
        if not isinstance(raw_sentences, Sequence) or isinstance(
            raw_sentences, (str, bytes)
        ):
            raise DatasetFormatError(
                f"Context paragraph {paragraph_index} sentences must be a sequence"
            )
        if not all(isinstance(sentence, str) for sentence in raw_sentences):
            raise DatasetFormatError(
                f"Context paragraph {paragraph_index} contains a non-string sentence"
            )
        documents.append(Document(title=title, sentences=tuple(raw_sentences)))
    return tuple(documents)


def _normalize_supporting_facts(raw_facts: Any) -> tuple[GoldSupportingFact, ...]:
    if raw_facts is None:
        return ()
    if not isinstance(raw_facts, Sequence) or isinstance(raw_facts, (str, bytes)):
        raise DatasetFormatError("Expected 'supporting_facts' to be a sequence")

    facts: list[GoldSupportingFact] = []
    for fact_index, fact in enumerate(raw_facts):
        if (
            not isinstance(fact, Sequence)
            or isinstance(fact, (str, bytes))
            or len(fact) != 2
        ):
            raise DatasetFormatError(
                f"Supporting fact {fact_index} must be [title, sentence_index]"
            )
        title, sentence_index = fact
        if not isinstance(title, str) or not isinstance(sentence_index, int):
            raise DatasetFormatError(
                f"Supporting fact {fact_index} has invalid title or sentence index"
            )
        if sentence_index < 0:
            raise DatasetFormatError(
                f"Supporting fact {fact_index} has a negative sentence index"
            )
        facts.append(
            GoldSupportingFact(title=title, sentence_index=sentence_index)
        )
    return tuple(facts)


def normalize_hotpotqa(record: Mapping[str, Any], split: str) -> NormalizedExample:
    """Normalize one official HotpotQA row."""

    return NormalizedExample(
        id=_require_string(record, "_id"),
        dataset=HOTPOTQA,
        split=split,
        question=_require_string(record, "question"),
        answer=_require_string(record, "answer"),
        documents=_normalize_documents(record.get("context")),
        evaluation_only=EvaluationOnlyAnnotations(
            gold_supporting_facts=_normalize_supporting_facts(
                record.get("supporting_facts")
            ),
            source_fields={
                key: record[key] for key in ("type", "level") if key in record
            },
        ),
    )


def normalize_2wiki(record: Mapping[str, Any], split: str) -> NormalizedExample:
    """Normalize one official 2WikiMultiHopQA row."""

    evaluation_field_names = (
        "type",
        "evidences",
        "evidences_id",
        "answer_id",
        "entity_ids",
    )
    return NormalizedExample(
        id=_require_string(record, "_id"),
        dataset=TWOWIKI,
        split=split,
        question=_require_string(record, "question"),
        answer=_require_string(record, "answer"),
        documents=_normalize_documents(record.get("context")),
        evaluation_only=EvaluationOnlyAnnotations(
            gold_supporting_facts=_normalize_supporting_facts(
                record.get("supporting_facts")
            ),
            source_fields={
                key: record[key]
                for key in evaluation_field_names
                if key in record
            },
        ),
    )


def _load_raw_records(path: str | Path, limit: int | None) -> list[Mapping[str, Any]]:
    source_path = Path(path)
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")

    with source_path.open("r", encoding="utf-8-sig") as source_file:
        data = json.load(source_file)
    if not isinstance(data, list):
        raise DatasetFormatError(f"Expected a top-level JSON list in {source_path}")

    selected = data if limit is None else data[:limit]
    if not all(isinstance(record, Mapping) for record in selected):
        raise DatasetFormatError(f"Expected every row in {source_path} to be an object")
    return selected


def inspect_raw_fields(path: str | Path) -> tuple[str, ...]:
    """Return sorted field names from the first raw row for validation reports."""

    records = _load_raw_records(path, limit=1)
    return tuple(sorted(records[0].keys())) if records else ()


def load_hotpotqa(
    path: str | Path, *, split: str = "dev_distractor", limit: int | None = None
) -> list[NormalizedExample]:
    """Load normalized examples from an official HotpotQA JSON file."""

    return [
        normalize_hotpotqa(record, split)
        for record in _load_raw_records(path, limit)
    ]


def load_2wiki(
    path: str | Path, *, split: str = "dev", limit: int | None = None
) -> list[NormalizedExample]:
    """Load normalized examples from an official 2WikiMultiHopQA JSON file."""

    return [
        normalize_2wiki(record, split) for record in _load_raw_records(path, limit)
    ]

