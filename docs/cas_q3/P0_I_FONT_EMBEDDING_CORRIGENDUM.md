# P0-I font-embedding engineering corrigendum

Date: 2026-09-13 (Asia/Shanghai).

Decision: **PASS FONT-CLEAN JOURNAL-NEUTRAL REBUILD; FINAL TARGET AND ASTRA
REBIND STILL PENDING.**

**CAS Q3 STATUS: NOT READY.** This corrigendum removes two disclosed PDF
engineering defects. It does not alter a scientific result, close the target
journal gate, provide author facts, or replace the required final GPT-6 Astra
xhigh artifact-bound audit.

## Change and dependency boundary

The prior deterministic vector writer used unembedded Base-14 Helvetica and
Helvetica-Bold. It now uses ReportLab 4.4.9 in invariant mode and its bundled
Bitstream Vera regular/bold TrueType fonts. The builder pins both font-file
hashes and records them in `paper/ASSET_RECEIPT.json`; `paper/requirements.txt`
pins the renderer version. Used font subsets are embedded in each vector
figure. The main manuscript's first-level item markers now use the already
embedded Computer Modern math minus, eliminating the isolated Type 3 marker on
page 4.

The generator was executed twice from the same sources. Both figure PDFs and
the complete asset receipt were byte-identical across the two builds. The
accepted aggregate input hashes, six generated table hashes, all numbers,
policy order, source cardinalities, model-forward count and fit count remained
unchanged.

## Mechanical and visual evidence

- `paper/figures/paired_pipeline.pdf`: all fonts subset-embedded TrueType;
- `paper/figures/recovery_damage.pdf`: all fonts subset-embedded TrueType;
- `output/pdf/manuscript.pdf`: 11 pages, zero nonembedded fonts, zero Type 3
  fonts, no unresolved citation/reference and no box warning;
- `output/pdf/supplement.pdf`: 3 pages, zero nonembedded fonts, zero Type 3
  fonts, retaining the previously disclosed nonfatal `longtable` page-split
  notice;
- all 14 pages were rendered at 120 dpi and reviewed by the project lead with
  no clipping, overlap, missing glyph or unreadable label;
- against the prior accepted compiled PDFs, nine of eleven main pages and all
  three supplement pages are pixel-identical. Main pages 4 and 7 differ only
  where the item marker and the two regenerated figures occur.

`scripts/verify_cas_q3_compiled_pdfs.py` now fails if either compiled PDF
contains any nonembedded or Type 3 font. The static manuscript verifier remains
the numeric, citation and Claim guard.

## Remaining authority

The previous Astra xhigh compiled rebind remains evidence for the pre-correction
artifact. This engineering-only rebuild requires a fresh artifact-bound Astra
xhigh rebind after the final journal template, authorship and declaration
surfaces are fixed. Until P0-G/H/I and that final audit close, the correct
status remains NOT READY.
