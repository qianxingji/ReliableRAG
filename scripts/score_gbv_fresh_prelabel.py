#!/usr/bin/env python3
"""Generate a gold-free GbV score ledger for a prospective fresh cohort."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.answer_normalization import assess_pair_eligibility  # noqa: E402
from src.evaluation.fresh_schema import read_fresh_branches  # noqa: E402
from src.verification.gbv_nli import (  # noqa: E402
    GBV_MODEL_ID,
    GBV_MODEL_REVISION,
    GBVPostAnsweringNLI,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branches", type=Path, required=True)
    parser.add_argument("--scores-output", type=Path, required=True)
    parser.add_argument("--provenance-output", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument(
        "--dtype",
        default="float32",
        choices=["float32", "float16", "bfloat16"],
    )
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    rows = read_fresh_branches(args.branches)
    scorer = GBVPostAnsweringNLI(
        model_id=GBV_MODEL_ID,
        revision=GBV_MODEL_REVISION,
        device=args.device,
        batch_size=args.batch_size,
        torch_dtype=args.dtype,
        local_files_only=args.local_files_only,
    )

    counters = Counter()
    args.scores_output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = args.scores_output.with_suffix(args.scores_output.suffix + ".tmp")
    with temp_output.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(rows, 1):
            eligibility = assess_pair_eligibility(row["a0"], row["a1"])
            record = {
                "dataset": row["dataset"],
                "retriever": row["retriever"],
                "sample_id": row["sample_id"],
                "eligible": eligibility.eligible,
                "forced_keep_reason": eligibility.reason,
                "F0": None,
                "F1": None,
                "gbv_margin": None,
                "e0_premise_count": len(row["evidence0"]),
                "e1_premise_count": len(row["evidence1"]),
                "e0_chunk_count": 0,
                "e1_chunk_count": 0,
                "model_id": GBV_MODEL_ID,
                "model_revision": GBV_MODEL_REVISION,
            }
            if eligibility.eligible:
                try:
                    score0 = scorer.score_branch(
                        row["question"], row["a0"], row["evidence0"]
                    )
                    score1 = scorer.score_branch(
                        row["question"], row["a1"], row["evidence1"]
                    )
                except ValueError as exc:
                    record["eligible"] = False
                    record["forced_keep_reason"] = f"nli_unscorable:{exc}"
                    counters["nli_unscorable"] += 1
                else:
                    record.update(
                        {
                            "F0": score0.score,
                            "F1": score1.score,
                            "gbv_margin": score1.score - score0.score,
                            "e0_chunk_count": score0.chunk_count,
                            "e1_chunk_count": score1.chunk_count,
                        }
                    )
                    counters["scored"] += 1
            else:
                counters[eligibility.reason or "forced_keep"] += 1
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            if index % 100 == 0 or index == len(rows):
                logging.info("GbV scored %d/%d fresh traces", index, len(rows))
    temp_output.replace(args.scores_output)

    import sentencepiece
    import torch
    import transformers

    provenance = {
        "status": "GBV_FRESH_PRELABEL_SCORE_SEAL_INPUT",
        "saved_utc": datetime.now(timezone.utc).isoformat(),
        "trace_count": len(rows),
        "counts": dict(counters),
        "model_id": GBV_MODEL_ID,
        "model_revision": GBV_MODEL_REVISION,
        "revision_note": (
            "Pinned by this study for reproducibility; Filice et al. report the model name, "
            "not this exact Hugging Face commit."
        ),
        "published_recipe": {
            "hypothesis": 'The answer to the question "{q}" is: "{a}"',
            "premise_unit": "each retrieved passage independently",
            "overlength": "20-word-overlap passage chunking; no scientific truncation",
            "aggregation": "maximum entailment probability over passage chunks",
            "pair_margin": "F1-F0",
        },
        "entailment_index": scorer.entailment_index,
        "model_max_length": scorer.max_length,
        "device": args.device,
        "requested_dtype": args.dtype,
        "resolved_dtype": scorer.resolved_dtype,
        "batch_size": args.batch_size,
        "input_sha256": sha256(args.branches),
        "scores_sha256": sha256(args.scores_output),
        "script_sha256": sha256(Path(__file__)),
        "versions": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "sentencepiece": sentencepiece.__version__,
        },
        "gold_or_outcome_input": False,
    }
    if str(args.device).startswith("cuda") and torch.cuda.is_available():
        provenance["cuda_device_name"] = torch.cuda.get_device_name(
            torch.device(args.device)
        )
    args.provenance_output.parent.mkdir(parents=True, exist_ok=True)
    args.provenance_output.write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
