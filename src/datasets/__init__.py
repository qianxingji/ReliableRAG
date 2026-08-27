"""Dataset loading and normalization for ReliableRAG."""

from .download import ensure_2wiki_dev, ensure_hotpotqa_dev
from .loaders import (
    HOTPOTQA,
    TWOWIKI,
    DatasetFormatError,
    inspect_raw_fields,
    load_2wiki,
    load_hotpotqa,
    normalize_2wiki,
    normalize_hotpotqa,
)
from .schema import (
    Document,
    EvaluationOnlyAnnotations,
    GoldSupportingFact,
    NormalizedExample,
    RuntimeExample,
)

__all__ = [
    "HOTPOTQA",
    "TWOWIKI",
    "DatasetFormatError",
    "Document",
    "EvaluationOnlyAnnotations",
    "GoldSupportingFact",
    "NormalizedExample",
    "RuntimeExample",
    "ensure_2wiki_dev",
    "ensure_hotpotqa_dev",
    "inspect_raw_fields",
    "load_2wiki",
    "load_hotpotqa",
    "normalize_2wiki",
    "normalize_hotpotqa",
]
