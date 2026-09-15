# P0-I Applied Intelligence modern-template preflight acceptance

Signed date: 2026-09-14 (Asia/Shanghai). Reviewer: client-side Research
Project Lead.

**DECISION: PARTIAL_PASS_APPLIED_INTELLIGENCE_MODERN_SN_JNL_PREFLIGHT_SMALLCONDENSED_EQUIVALENCE_OPEN.**

**CAS Q3 STATUS: NOT READY.** This accepts a modern official Springer Nature
template compilation as a technical preflight. It does not establish that
`sn-jnl` is equivalent to the `smallcondensed` profile named on the Applied
Intelligence journal page, and it does not authorize submission.

## Authenticated template dependency

The builder used the December 2024 Springer Nature LaTeX package downloaded
from the current official author-support resource. The full download SHA-256 is
`812e76dcaa9c28dc1bff1fb6065d51729b67d4ea140552a05088317414a3ecae`.
Within that archive, the used `sn-jnl.cls` hash is
`36d0c3273a59d48dc6a9c7b080dfa1ec50dc10229d8751568d1f2e490ffa5ecc`
and the `sn-basic.bst` hash is
`4b368414cc5593169907933b417aacfdb0ce905866a39bdf55d21aad65e9d46c`.
The local build used MiKTeX pdfTeX 1.40.28 with LaTeX2e 2025-11-01 and the
class-required `sttools/cuted.sty` package.

The official class and bibliography files are external build dependencies and
are not copied into the repository or the authored-source ZIP. Consequently,
the committed authored-source ZIP is flat and reviewable but is not represented
as a standalone source package. A final journal package must use the exact
publisher-approved dependency.

## Conversion and compile result

The transformation changes only class/package syntax, anonymous placeholder
front matter, abstract/keyword syntax, bibliography presentation, five flat
asset paths, standard-list presentation, and two target-layout settings. It retains the complete scientific
prose and numbers and leaves the journal-neutral source byte-identical.

The source uses `sn-jnl` with `pdflatex`, `sn-basic` and `Numbered`. The 155-word
abstract, five keywords and numeric citations are present. Compilation has zero
fatal errors, unresolved citations or references, visible unresolved markers,
overfull boxes, nonembedded fonts and Type 3 fonts. The class produces 14
underfull vertical-box notices; all pages were inspected and no corresponding
visible defect was found.

| Artifact | Pages/members | SHA-256 |
|---|---:|---|
| `output/target_profiles/applied_intelligence_modern_preflight/manuscript_sn_jnl_preflight.pdf` | 12 pages | `e9c114ae496c2bf3c46c970b69adb4950f733e8ae3610934335ad774db935eef` |
| `output/target_profiles/applied_intelligence_modern_preflight/applied_intelligence_authored_source_preflight.zip` | 8 flat authored members | `3f8db53d94fb27a9aa960f2867a31c23a270079659e897dc648d096d5c3120f8` |

## Visual review

All 12 final PDF pages were rendered at 110 dpi and reviewed after replacing
the target-only `enumitem` dependency with standard list commands. The title, anonymous
placeholder front matter, abstract, keywords, body, both figures, all tables,
declarations placeholder and all 22 references are present and legible. No
clipping, overlap, blank or orphan page, missing glyph, unreadable label or
unresolved marker was observed. The bibliography was changed to the class's
small font to eliminate a one-reference orphan page; this is a target-layout
change and does not alter reference content.

## Remaining gates

The Applied Intelligence page inspected on 2026-09-14 still names a Springer
macro package with `smallcondensed`, but its linked legacy archive was not
retrievable. The current official general package uses `sn-jnl`. Exact target
compliance therefore remains open pending a working publisher-supplied package
or journal/editor confirmation. Complete verified author/declaration facts,
release review and corrected archive, institutional CAS record, final source
package, and GPT-6 Astra xhigh fairness/Claim/reviewer audit also remain open.

No scientific payload, Gold answer, model forward, fit or bootstrap draw was
read or executed for this preflight.
