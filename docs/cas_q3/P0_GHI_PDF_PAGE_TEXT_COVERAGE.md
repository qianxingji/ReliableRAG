# P0-G/H/I unique-PDF page-text coverage audit

Decision: **PASS_BOUNDED_UNIQUE_PDF_PAGE_TEXT_COVERAGE_NO_LOW_TEXT_PAGES**.

**CAS Q3 STATUS: NOT READY.**

On 2026-09-15, a read-only page-level follow-up covered the same three external
roots as the preceding text, document and archive censuses. It collected 100
ordinary PDF occurrences, 138 direct ZIP PDF members and 32 PDF members from
all four first-level nested ZIPs. The 270 occurrences reduce to the same 35
unique SHA-256 hashes already observed before nested-archive expansion; the
nested packages therefore add duplicate occurrences, not new PDF content.

`pdfinfo` identified 446 pages across the 35 unique PDFs. A separate
`pdftotext -layout` call inspected every page. All 446 pages contain at least 20
non-whitespace extracted-text bytes: there are zero textless pages and zero low-
text pages. `pdfimages -list` found raster-image objects on 15 unique PDF/page
pairs, but every such page also has the accepted text-layer minimum. There was
no PDF skip, nested-archive skip or parser error, and all temporary files were
removed.

This rules out a wholly textless scanned page among the known PDFs. It does not
OCR text embedded inside raster images on otherwise text-bearing pages, prove
absence outside the three roots, or establish institutional authority. The
earlier full-text marker search remains the evidence for searchable PDF text;
this audit establishes page coverage only. It closes no P0 gate and authorizes
neither submission nor distribution. No scanned file was executed, and no
model forward, scientific fit or scientific payload interpretation occurred.
