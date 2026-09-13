# P0-I compiled-artifact acceptance

Signed date: 2026-09-13 (Asia/Shanghai). Reviewer: client-side Research Project
Lead.

**DECISION: PASS_FONT_CLEAN_COMPILED_DRAFT_MECHANICAL_AND_VISUAL_CHECKS_WITH_LONGTABLE_NOTICE**

**CAS Q3 STATUS: NOT READY.** This accepts the anonymous compiled draft as a
reviewable artifact. It does not certify target-journal PDF compliance, CAS Q3
eligibility, author declarations, licensing or final Submission Ready.

## Build and artifacts

The manuscript was compiled with MiKTeX pdfTeX 1.40.28 / LaTeX2e 2025-11-01.
The main build used `pdflatex`, `bibtex`, then two further `pdflatex` passes.
The supplement used two `pdflatex` passes.

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/manuscript.pdf` | 11 | `851eea05278b64793e5814a48de8df6cf2529acdcf27df5072d8ae5f9999e025` |
| `output/pdf/supplement.pdf` | 3 | `b50a3bed4d7165c62f2cfeac06bd934a1b8ea9f997774d35f083ce5c04cd3812` |

Both are PDF 1.5, letter size. The exact engine, page, font, PDF and log results
are machine-recorded in `paper/COMPILE_RECEIPT.json`.

## Mechanical and visual review

The main and supplement logs have zero fatal errors, undefined
citations/references and overfull/underfull boxes. All 11 main pages and all 3
supplement pages were rendered and inspected. Tables, figures, references,
equations and page boundaries were legible; no clipping, overlap, blank page or
missing text was observed.

The font-clean build was rendered at 120 dpi. All 14 pages were inspected with
no clipping, overlap, blank page, missing glyph or unreadable figure label.
Relative to the earlier accepted build, main pages 4 and 7 change only at the
item marker and regenerated figures; the other nine main pages and all three
supplement pages are pixel-identical.

Both compiled PDFs now contain zero nonembedded fonts and zero Type 3 fonts.
The two figures use subset-embedded Bitstream Vera TrueType fonts rendered by
the pinned ReportLab 4.4.9 dependency. The supplement log retains one nonfatal
`longtable` infinite-glue page-split notice, and its rendered table is complete.
MiKTeX reports that this installation has not yet checked for updates outside
the LaTeX logs.

The build script's executable resolver has been tested through both the local
MiKTeX fallback and an explicit `PATH` entry. Both branches completed the full
main/supplement build successfully.

## Scientific boundary and remaining gates

No experiment, fit, model forward, bootstrap or sealed result changed during
compilation and visual repair. The manuscript remains a single-reader,
Qwen-only empirical study. It does not claim a novel top-level algorithm,
joint superiority over HGB-only or ROA advancement.

Remaining P0 blockers are the owner-selected project license and journal release
policy; verified title/ISSN plus the applicable institutional CAS Q3
year/category rule; real author, affiliation, contribution, funding, conflict,
ethics, acknowledgement and writing-assistance declarations; target-specific
formatting. The earlier Astra xhigh compiled-artifact rebind and engineering
addendum remain bound to the pre-font-correction artifact. A fresh final Astra
xhigh artifact rebind remains required after the target-specific conversion.
