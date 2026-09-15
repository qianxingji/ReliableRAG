# P0-I cross-profile abstract compression and rebuilt-artifact acceptance

Signed date: 2026-09-13 (Asia/Shanghai). Reviewer: client-side Research Project
Lead.

**DECISION: PASS_142_WORD_CROSS_PROFILE_ABSTRACT_AND_REBUILT_DRAFT_WITH_FINAL_ASTRA_AND_EXTERNAL_GATES_OPEN.**

**CAS Q3 STATUS: NOT READY.** This accepts a target-neutral editorial revision
and its rebuilt PDFs. It does not certify a journal's CAS tier, target template,
author declarations, release license or final Submission Ready status.

## Editorial change and Claim preservation

The abstract was reduced from 204 verifier-counted words to 142. It now meets
both inspected candidate ceilings: less than 250 words for Discover Computing
and at most 150 words for Journal of Information Science. No result, table,
figure, experiment, fit, bootstrap draw or sealed aggregate changed.

The compressed abstract retains all material boundaries:

- one Qwen2.5-3B-Instruct reader, 6,000 questions, three datasets, three
  retrieval conditions and nine policies;
- the HGB+GbV_R versus GbV-only_R EM and Damage point differences and both
  adjusted question-cluster bootstrap ranges;
- the non-passing HGB-only_R comparison;
- rejection of ROA-FULL advancement; and
- a bounded within-reader empirical attribution rather than a novel
  architecture, reader-general transfer or deployment-cost Claim.

The static verifier now requires at most 150 words and passes all 126 checks.

## Rebuilt artifacts and mechanical verification

MiKTeX pdfTeX 1.40.28 / LaTeX2e 2025-11-01 produced:

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/manuscript.pdf` | 11 | `dfd1dfe3c1cb53bd1d1972463606f986906c76cff0bc172e98097d2e4d0d2612` |
| `output/pdf/supplement.pdf` | 3 | `bf3a08cf10eb046697cb421e29be9a2f6998ee04238f693f727c548869eff5f7` |

The compiled verifier finds zero fatal errors, undefined references/citations,
overfull/underfull boxes, nonembedded fonts and Type 3 fonts. The supplement
retains the already disclosed nonfatal `longtable` infinite-glue notice. The
verifier now records mechanical facts only and does not manufacture a human
visual-review pass.

## Independent visual and pixel review

Both PDFs were rendered at 120 dpi. All 11 main pages and all three supplement
pages were inspected. No clipping, overlap, blank page, missing glyph,
unresolved marker, unreadable table or unreadable figure label was observed.

Against the preceding committed font-clean PDFs, main pages 1--9 changed at the
pixel level because the shorter abstract reflowed the main text; main pages 10
and 11 are pixel-identical. All three supplement pages are pixel-identical even
though recompilation changed the PDF container bytes. This comparison uses
SHA-256 over Poppler-rendered page PNGs, not a subjective claim of unchanged
source.

## Remaining gates

The existing Astra xhigh source and compiled-artifact audits remain historical
evidence for their exact reviewed artifacts. This editorial rebuild still
requires the planned final Astra xhigh artifact-bound fairness, Claim and
simulated-reviewer audit after the target journal is selected and converted.
P0-G license/release facts, P0-H institutional CAS qualification and P0-I real
author/declaration facts remain open.
