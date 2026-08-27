"""Common, label-safe data structures for multi-hop QA datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Document:
    """A titled document represented as its ordered source sentences."""

    title: str
    sentences: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {"title": self.title, "sentences": list(self.sentences)}


@dataclass(frozen=True, slots=True)
class GoldSupportingFact:
    """A gold sentence reference, usable only through evaluation annotations."""

    title: str
    sentence_index: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {"title": self.title, "sentence_index": self.sentence_index}


@dataclass(frozen=True, slots=True)
class EvaluationOnlyAnnotations:
    """Gold labels and dataset metadata forbidden to runtime retrieval code."""

    gold_supporting_facts: tuple[GoldSupportingFact, ...] = ()
    source_fields: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation with an explicit warning."""

        return {
            "gold_supporting_facts": [
                fact.to_dict() for fact in self.gold_supporting_facts
            ],
            "source_fields": dict(self.source_fields),
        }


@dataclass(frozen=True, slots=True)
class RuntimeExample:
    """The label-free view allowed at runtime for retrieval experiments."""

    id: str
    dataset: str
    split: str
    question: str
    documents: tuple[Document, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable runtime record."""

        return {
            "id": self.id,
            "dataset": self.dataset,
            "split": self.split,
            "question": self.question,
            "documents": [document.to_dict() for document in self.documents],
        }


@dataclass(frozen=True, slots=True)
class NormalizedExample:
    """Common stored schema for HotpotQA and 2WikiMultiHopQA.

    Gold supporting facts are deliberately nested under ``evaluation_only``.
    Runtime components should accept :class:`RuntimeExample`, obtained via
    :meth:`runtime_view`, rather than this label-bearing record.
    """

    id: str
    dataset: str
    split: str
    question: str
    answer: str
    documents: tuple[Document, ...]
    evaluation_only: EvaluationOnlyAnnotations

    def runtime_view(self) -> RuntimeExample:
        """Return a view that cannot expose answers or gold supporting facts."""

        return RuntimeExample(
            id=self.id,
            dataset=self.dataset,
            split=self.split,
            question=self.question,
            documents=self.documents,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the full JSON-serializable stored record."""

        return {
            "id": self.id,
            "dataset": self.dataset,
            "split": self.split,
            "question": self.question,
            "answer": self.answer,
            "documents": [document.to_dict() for document in self.documents],
            "evaluation_only": self.evaluation_only.to_dict(),
        }

