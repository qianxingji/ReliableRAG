# P0-I Discover Computing provisional technical preflight acceptance

Decision: **PASS_DISCOVER_COMPUTING_PROVISIONAL_TECHNICAL_PREFLIGHT_EXTERNAL_GATES_OPEN.**

**CAS Q3 STATUS: NOT READY.** Discover Computing remains a provisional
editorial-fit lead. Neither the responsible owner nor the institution has
selected it or certified its CAS Q3 status.

## Accepted technical scope

On 2026-09-14, the current official journal and Springer Nature author pages
were rechecked. Discover Computing accepts Research articles, requires an
abstract of fewer than 250 words, accepts a LaTeX ZIP that compiles with
`pdflatex`, specifies at least 12 pt text, uses numeric references, and requires
a funding statement and data-availability statement. The journal uses
single-anonymous review. Springer Nature recommends its current LaTeX template
and states that Snapp compiles source files with `pdflatex`.

The deterministic builder produced a provisional technical profile from the
accepted journal-neutral manuscript by changing only the document-class size
from 11 pt to 12 pt and flattening five figure/table paths. It changed no
scientific prose or numbers and did not modify `paper/manuscript.tex`. The
resulting source ZIP has eight top-level members and no nested paths. It
compiles locally to a 12-page PDF with 18 font rows, zero nonembedded fonts and
zero Type 3 fonts. The 142-word abstract remains below the journal ceiling.

All 12 rendered pages were inspected at 90 dpi. No clipping, overlap, blank
page, missing glyph, unresolved reference, unreadable table or unreadable
figure was observed. This visual acceptance is separate from the automated
receipt.

## Boundary of acceptance

This is a generic 12 pt `article` technical dry run. The Springer Nature
template has not been applied, the final journal has not been selected, and the
output is not authorized for submission or distribution. The anonymous author
line is also incompatible with a completed single-anonymous submission until
the responsible-author facts are supplied.

P0-I remains open for real authorship and declarations, the mandatory funding
statement, the cover letter, final journal template/profile conversion, and a
fresh GPT-6 Astra xhigh artifact and Claim audit. P0-G remains open for project
license and release policy. P0-H remains open for the institution-recognized CAS
edition/category rule, current-title continuity, APC acceptance and final
journal choice.

No benchmark question, answer, outcome, model weight or scientific fit was read
or executed for this preflight.
