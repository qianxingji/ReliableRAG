# P0-I compiled-artifact acceptance

Signed date: 2026-09-13 (Asia/Shanghai). Reviewer: client-side Research Project
Lead.

**DECISION: PASS_COMPILED_DRAFT_MECHANICAL_AND_VISUAL_CHECKS_WITH_DISCLOSED_NOTICES**

**CAS Q3 STATUS: NOT READY.** This accepts the anonymous compiled draft as a
reviewable artifact. It does not certify target-journal PDF compliance, CAS Q3
eligibility, author declarations, licensing or final Submission Ready.

## Build and artifacts

The manuscript was compiled with MiKTeX pdfTeX 1.40.28 / LaTeX2e 2025-11-01.
The main build used `pdflatex`, `bibtex`, then two further `pdflatex` passes.
The supplement used two `pdflatex` passes.

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/manuscript.pdf` | 11 | `c9150d15ae9023160c07437735333754a897a3331450d1e57388eed7703aa641` |
| `output/pdf/supplement.pdf` | 3 | `fcf134c7695f9c706db376996856240e4980332ef5b4843a7d2095f6c4788d61` |

Both are PDF 1.5, letter size. The exact engine, page, font, PDF and log results
are machine-recorded in `paper/COMPILE_RECEIPT.json`.

## Mechanical and visual review

The main and supplement logs have zero fatal errors, undefined
citations/references and overfull/underfull boxes. All 11 main pages and all 3
supplement pages were rendered and inspected. Tables, figures, references,
equations and page boundaries were legible; no clipping, overlap, blank page or
missing text was observed.

After the executable-resolution repair, all 14 pages were rendered again at
108 dpi. Every page PNG was byte-identical to the page inspected independently
by the Astra xhigh reviewer before the repair, confirming that the rebuild
changed no visible page content.

The supplement log retains one nonfatal `longtable` infinite-glue page-split
notice. Its rendered table is complete. The main PDF has two unembedded
Base-14 fonts, Helvetica and Helvetica-Bold, originating in the two vector
figures. The main PDF also contains one embedded Type 3 font (`F127`); other
TeX Computer Modern fonts are embedded. The supplement has no unembedded or
Type 3 fonts. These are disclosed formatting issues to resolve against the
selected journal's PDF profile. MiKTeX reports that this installation has not
yet checked for updates outside the LaTeX logs.

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
formatting. The Astra xhigh compiled-artifact rebind and post-repair engineering
addendum are complete and retain these external blockers.
