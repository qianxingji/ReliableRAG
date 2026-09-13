# P0-I manuscript build status

Status: **ANONYMOUS SOURCE AND COMPILED DRAFT PACKAGE BUILT; PROJECT-LEAD
MECHANICAL AND VISUAL VERIFICATION PASSED.**

The authorized manuscript package now contains:

- a journal-neutral anonymous main LaTeX manuscript;
- a supplementary LaTeX manuscript;
- a 22-record BibTeX bibliography checked against primary publisher/paper pages;
- aggregate-generated study, nine-policy, primary-comparison, sensitivity,
  dataset and retriever tables;
- two deterministic vector PDF figures;
- separate title-page/declarations and cover-letter templates; and
- an aggregate-only asset receipt plus an independent manuscript verifier.

The asset builder pins the accepted SHA-256 values of `POINT_ESTIMATES.json`
and `INTERVALS.json`. It reads no question, answer, Gold string, per-trace
outcome, bootstrap draw or model file. The two figures were rendered with
Poppler at 144 dpi and visually inspected; an initial label-overlap defect in
the recovery/damage figure was corrected before acceptance.

The independent manuscript verifier passes 126 checks, including exact
aggregate-to-table comparisons for all nine overall rows and all 54 dataset and
retriever rows, primary interval cells, bibliography keys, Claim boundaries and
anonymity. The journal-neutral abstract has been compressed from 204 to 142
words while retaining the positive comparison, both negative decisions,
adjusted ranges, within-reader boundary and non-novelty statement. This closes
the inspected 150-word and 250-word candidate limits before target conversion.
MiKTeX pdfTeX 1.40.28 / LaTeX2e 2025-11-01 compiled the main
manuscript through BibTeX and the supplement. The final artifacts are an
11-page main PDF and a 3-page supplement. Their logs contain no fatal error,
undefined citation/reference or overfull/underfull box. Project-lead review of
all 14 rendered pages found no clipping, overlap or missing content.

The [font-embedding corrigendum](P0_I_FONT_EMBEDDING_CORRIGENDUM.md) replaces
the unembedded Base-14 figure fonts with deterministic, hash-pinned,
subset-embedded Bitstream Vera TrueType fonts and replaces the isolated Type 3
item marker. Both compiled PDFs now contain zero nonembedded fonts and zero
Type 3 fonts. All 14 pages were rendered again at 120 dpi and passed visual
review. The supplement log retains one nonfatal `longtable` infinite-glue
page-split notice; its rendered content is complete. Target-journal PDF-profile
compliance remains a journal-selection task. MiKTeX also reports that the
installation has not yet checked for package updates outside the LaTeX logs.
Exact hashes, page counts and disclosures are bound in
`paper/COMPILE_RECEIPT.json`, the historical font-clean compiled-artifact
acceptance and the newer abstract-compression acceptance. The mechanical
verifier no longer asserts that it performed a visual review; the versioned
acceptance record carries that human inspection evidence.

The [length verification](P0_I_MANUSCRIPT_LENGTH_VERIFICATION.json) records a
reproducible Poppler/PDF token proxy: 3,898 tokens before the References heading
and 4,596 in the complete PDF. It is explicitly not a publisher word count. It
shows a JIS-specific below-average-length risk because that journal publishes a
5,000--7,500-word average, but it does not convert an average into a hard
minimum or justify padding the manuscript.

The PDF build script resolves TeX executables either from `PATH` or the local
MiKTeX fallback directory as plain executable paths. Both resolution branches
have been exercised successfully in the takeover environment.

Author identities/declarations, project-license selection and the applicable
institutional CAS Q3 journal rule remain owner/institution inputs. The main
scientific rejection risks remain the single accepted reader, lack of a new
algorithm, no joint advantage over HGB-only, missing original fit-time evidence
and unmeasured standalone deployment cost.

**CAS Q3 STATUS: NOT READY.** The earlier source-level and compiled-artifact
audits remain historical authority for their exact artifacts. The font-clean
rebuild passed project-lead mechanical and visual checks; it requires the
planned final Astra xhigh artifact rebind after journal conversion. Owner
inputs, license selection and journal/CAS Q3 certification also remain required
before Submission Ready.
