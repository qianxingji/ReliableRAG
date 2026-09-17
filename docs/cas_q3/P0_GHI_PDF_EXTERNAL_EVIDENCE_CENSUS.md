# P0-G/H/I PDF external-evidence census

Decision: **PASS_BOUNDED_PDF_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES**.

**CAS Q3 STATUS: NOT READY.**

On 2026-09-14, a read-only Poppler `pdftotext -layout` pass covered PDFs in
the original workspace, preserved private historical root and old repository
ZIP. It extracted every PDF within the 20,000,000-byte item guard.

The pass processed all 100 ordinary PDFs, covering 20,267,890 PDF bytes, and
all 138 PDF members across the same 39 ZIP archives, covering 22,448,146 PDF
bytes. It searched 3,448,238 extracted text bytes and returned zero marker
candidate, zero skip and zero extraction or archive error.

The 238 occurrences reduce to 35 unique PDF hashes. Every unique PDF has at
least 20 non-whitespace bytes in its extracted text layer; none is a text-empty
or low-text document. All 35 unique PDFs also pass a `pdfdetach -list`
attachment inventory with zero embedded attachment. Thirty unique PDFs were
first encountered as ZIP members, so they were materialized individually in
the system temporary directory for attachment inspection and immediately
deleted. No archive tree or persistent extracted member was created.

Ordinary PDF paths, ZIP member names and extracted text are not serialized in
the receipt. Candidate and extraction-error records would contain content
hashes without matched text. ZIP members are passed to `pdftotext` through
standard input; no scanned file is executed. Synthetic tests cover ordinary
PDFs, candidate privacy, ZIP-member handling, attachment-count privacy and
fail-closed size limits.

This is a text-layer census with a complete embedded-attachment inventory. It
does not perform OCR on page images, inspect text that may exist only inside an
image, cover other binary formats or prove absence outside the three roots. It
authenticates neither authorship nor institutional authority.
No institutional CAS, manuscript-approval or code-release candidate was
recovered, so P0-G, P0-H and P0-I remain open. The pass performs no model
forward, scientific fit, bootstrap recomputation or scientific-payload
interpretation and does not authorize submission or distribution.
