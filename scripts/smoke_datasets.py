"""Download, normalize, and summarize tiny Phase 0 dataset samples."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from src.datasets import (
    NormalizedExample,
    ensure_2wiki_dev,
    ensure_hotpotqa_dev,
    inspect_raw_fields,
    load_2wiki,
    load_hotpotqa,
)

LOGGER = logging.getLogger(__name__)


def _sample_summary(example: NormalizedExample) -> dict[str, Any]:
    return {
        "id": example.id,
        "question": example.question,
        "answer": example.answer,
        "document_count": len(example.documents),
        "gold_supporting_fact_count_evaluation_only": len(
            example.evaluation_only.gold_supporting_facts
        ),
    }


def _dataset_summary(
    name: str,
    source_path: Path,
    examples: list[NormalizedExample],
) -> dict[str, Any]:
    return {
        "dataset": name,
        "source_file": str(source_path),
        "raw_fields_discovered": list(inspect_raw_fields(source_path)),
        "normalized_fields": list(examples[0].to_dict().keys()) if examples else [],
        "loaded_sample_count": len(examples),
        "total_documents_in_sample": sum(
            len(example.documents) for example in examples
        ),
        "total_gold_supporting_facts_evaluation_only": sum(
            len(example.evaluation_only.gold_supporting_facts)
            for example in examples
        ),
        "samples": [_sample_summary(example) for example in examples[:3]],
    }


def run_smoke(data_dir: Path, limit: int) -> dict[str, Any]:
    """Run the end-to-end Phase 0 smoke load for both datasets."""

    hotpot_path = ensure_hotpotqa_dev(data_dir)
    twowiki_path = ensure_2wiki_dev(data_dir)
    hotpot_examples = load_hotpotqa(hotpot_path, limit=limit)
    twowiki_examples = load_2wiki(twowiki_path, limit=limit)

    if len(hotpot_examples) != limit or len(twowiki_examples) != limit:
        raise RuntimeError(
            f"Expected {limit} examples from each dataset; got "
            f"{len(hotpot_examples)} and {len(twowiki_examples)}"
        )

    return {
        "phase": 0,
        "evaluation_only_boundary": (
            "Gold supporting facts are nested under evaluation_only and absent "
            "from RuntimeExample."
        ),
        "datasets": [
            _dataset_summary("HotpotQA", hotpot_path, hotpot_examples),
            _dataset_summary("2WikiMultiHopQA", twowiki_path, twowiki_examples),
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for downloaded public source files (default: data/raw)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of examples to load from each dataset (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit <= 0:
        raise ValueError("--limit must be positive")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    summary = run_smoke(args.data_dir, args.limit)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    LOGGER.info("Phase 0 dataset smoke test completed")


if __name__ == "__main__":
    main()
