# P1 JIIS R4 code-alignment acceptance

Date: 2026-09-16

Project lead decision: **PASS for paper-to-public-code alignment**

CAS Q3 STATUS: **NOT READY**

## Accepted artifact

- Author-designated scientific baseline: `paper/source_reference/JIIS_Manuscript_R3.pdf`
  - SHA-256: `b01683e3431cd01c62739c66cd6045395f30362234c04f3315458602eebf6c2e`
- Current code-aligned manuscript: `output/pdf/JIIS_Manuscript_R4_Code_Aligned.pdf`
  - SHA-256: `8f2ce9928ca381c37926b198859b3a91ae1dbab9f6d0bfa4e61d07b9603e8aba`
  - 21 A4 pages, PDF 1.7, all fonts embedded, zero Type 3 fonts
- Public repository: <https://github.com/qianxingji/ReliableRAG-Code>
  - fixed commit: `a6da7d80aca082301824b320ec4698c0dfac7b12`
  - GitHub Actions run: <https://github.com/qianxingji/ReliableRAG-Code/actions/runs/34993574899> (`success`)

R4 changes only four release-state paragraphs: page 12 data/code availability,
page 17 Appendix D.3, page 19 HGB provenance, and page 21 Appendix J. No
scientific result, table, figure, Claim, or interval changed.

## Verification

- `scripts/verify_jiis_r4_code_alignment.py`: 75 checks passed.
- `scripts/verify_latest_manuscript.py`: 20 checks passed.
- Public unit tests: 7 passed after installing the repository-declared dependencies.
- Public aggregate verifier: 129 reporting checks passed.
- Public repository verifier: 167 checks passed, with zero scientific fits and zero model forwards inside that verifier.
- Visual review: all 21 rendered pages reviewed; pages 12, 17, 19, and 21 reviewed at full size; no clipping, overlap, or overflow observed.

The first local unit-test attempt failed before collection because SciPy was not
installed in the active Python environment. This environment failure was retained
in the task record. After `python -m pip install -e .`, all seven tests passed.

## Remaining rejection risks and missing evidence

1. The public package verifies aggregate reporting and exposes current fitting,
   NLI, HGB, allocation, and analysis code, but excludes the per-question rows,
   fitted paper bundles, action memberships, bootstrap multiplicities, benchmark
   text, model weights, and generated answers. Independent end-to-end regeneration
   and per-question top-K bootstrap reconstruction therefore remain unavailable.
2. Only the `HGB_GBV_R` versus `GBV_ONLY_R` joint comparison passes. The paper
   must retain its comparison-specific empirical Claim and cannot claim a new
   architecture, universal fusion advantage, cross-reader transfer, or deployment
   efficiency.
3. The historical HGB saved computation has exact numerical replay, but original
   fit-time ID/matrix receipts and an independent original-fit witness remain
   unavailable.
4. Final JIIS target-format and submission-package checks, reference/novelty
   re-review, and the required Astra xhigh scientific acceptance have not yet been
   completed against this R4 artifact.

## Ordered work

- **P0:** preserve the accepted experimental and provenance boundary; do not widen Claims.
- **P1:** complete JIIS-specific manuscript audit and address only evidence-backed reviewer issues.
- **P2:** prepare the final submission package and run Astra xhigh Claim-sufficiency and Submission Ready acceptance.

This acceptance closes the paper-to-public-code mismatch. It does not declare the
manuscript Submission Ready.
