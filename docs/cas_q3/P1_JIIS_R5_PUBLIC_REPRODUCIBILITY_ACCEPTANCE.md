# P1 JIIS R5 public reproducibility acceptance

Date: 2026-09-16

Project lead decision: **PASS for public statistical reconstruction**

CAS Q3 STATUS: **NOT READY**

## Accepted public reproduction

- Repository: <https://github.com/qianxingji/ReliableRAG-Code>
- Frozen commit: `44d22c66c2adbdce8ebc2289844a8b26e6929bd5`
- Successful CI run: <https://github.com/qianxingji/ReliableRAG-Code/actions/runs/35054121085>
- Numeric bundle: `outputs/reproduction_v1/TRACE_NUMERIC.jsonl.gz`
  - 18,000 trace records, 6,000 question groups, three retriever siblings
  - SHA-256: `a930286d62bddf9f4837cb1beb4b863f0f94c1bc697b2311977a9b0eb18f09f7`
  - benchmark sample IDs replaced by dataset-local opaque `qNNNN` ordinals
  - no question, context, reference, generated-answer, or retrieved-passage text
- Exact public reconstruction:
  - all nine-policy point estimates: exact match
  - 20,000 dataset-stratified question-cluster draws: regenerated from seed `20260926`
  - global top-K allocation repeated within each primary draw
  - fixed-action sensitivity reconstructed
  - complete `INTERVALS.json`: exact match
  - scientific fits: 0; model forwards: 0

The one-command workflow is `python scripts/reproduce_all.py`. Eight unit tests,
the full statistical reconstruction, 129 aggregate reporting checks, and 194
repository membership/content/privacy checks pass locally and in GitHub Actions.

## Accepted manuscript

- Current manuscript: `output/pdf/JIIS_Manuscript_R5_Reproducible.pdf`
- SHA-256: `fdb055b765899bc71e3d0258c4e65e3a70a10bccd7bb409e9ac73f32c7f0258b`
- 21 A4 pages; all fonts embedded; zero Type 3 fonts
- 90 paper/code/data/numeric/provenance checks passed
- three consecutive clean PDF builds produced the same SHA-256
- all 21 pages visually reviewed; pages 12, 17, 19, and 21 reviewed at full size
- scientific results, comparisons, intervals, figures, tables, and Claims unchanged

## Remaining boundary and rejection risks

1. The statistical layer is now independently reconstructable from public
   trace-level numeric inputs. Retrieval, candidate generation, neural scoring,
   and paper-head refitting remain outside the public release because benchmark
   text, generated text, model assets, fitted bundles, and development labels are
   not redistributed.
2. Seven historical upstream estimators still lack original fit-time ID/matrix
   receipts and an independent original-fit witness. Exact saved-computation
   replay does not authenticate the original training event.
3. The empirical Claim remains comparison-specific: only `HGB_GBV_R` versus
   `GBV_ONLY_R` passes the joint rule. No architecture novelty, universal fusion,
   cross-reader transfer, or deployment-efficiency Claim is supported.
4. JIIS-specific scientific/editorial review and Astra xhigh final Claim and
   Submission Ready acceptance remain open.

This acceptance closes the earlier inability to reconstruct the selected top-K
bootstrap publicly. It does not declare end-to-end neural reproduction or final
Submission Ready status.
