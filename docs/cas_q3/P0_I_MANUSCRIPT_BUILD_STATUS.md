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
anonymity. MiKTeX pdfTeX 1.40.28 / LaTeX2e 2025-11-01 compiled the main
manuscript through BibTeX and the supplement. The final artifacts are an
11-page main PDF and a 3-page supplement. Their logs contain no fatal error,
undefined citation/reference or overfull/underfull box. Project-lead review of
all 14 rendered pages found no clipping, overlap or missing content.

The supplement log retains one nonfatal `longtable` infinite-glue page-split
notice; rendered content is complete. The two vector figures use unembedded
PDF Base-14 Helvetica/Helvetica-Bold fonts, and the main PDF contains one
embedded Type 3 font (`F127`). Target-journal PDF-profile and font compliance
therefore remain a journal-selection task. MiKTeX also reports that
the installation has not yet checked for package updates; this notice is
outside the LaTeX logs. Exact hashes, page counts and disclosures are bound in
`paper/COMPILE_RECEIPT.json` and
`docs/cas_q3/P0_I_COMPILED_ARTIFACT_ACCEPTANCE.md`.

The PDF build script resolves TeX executables either from `PATH` or the local
MiKTeX fallback directory as plain executable paths. Both resolution branches
have been exercised successfully in the takeover environment.

Author identities/declarations, project-license selection and the applicable
institutional CAS Q3 journal rule remain owner/institution inputs. The main
scientific rejection risks remain the single accepted reader, lack of a new
algorithm, no joint advantage over HGB-only, missing original fit-time evidence
and unmeasured standalone deployment cost.

**CAS Q3 STATUS: NOT READY.** The source-level audit, compiled-artifact rebind
and post-repair engineering addendum all passed under Astra xhigh within the
stated blockers. Owner inputs, license selection and journal/CAS Q3
certification remain required before Submission Ready.
