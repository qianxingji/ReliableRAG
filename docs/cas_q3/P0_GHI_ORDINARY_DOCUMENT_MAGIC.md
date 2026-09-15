# P0-G/H/I ordinary-file document-magic census

Decision: **PASS_BOUNDED_ORDINARY_DOCUMENT_MAGIC_MATCHES_EXTENSIONS**.

**CAS Q3 STATUS: NOT READY.**

On 2026-09-15, a read-only file-header census covered the same original
workspace, preserved private historical root and old repository ZIP used by the
external-evidence searches. It saw 465,460 ordinary files and read at most
4,096 leading bytes from each, 631,242,643 bytes in total.

Strict signature detection found exactly 39 ZIP containers, all named `.zip`,
and 100 PDFs, all named `.pdf`. Inspection of every ordinary ZIP central
directory found no OOXML Word, spreadsheet or presentation package and no ODF
text, spreadsheet or presentation package. No RTF or OLE compound-file header
was present. There was no document-magic/extension mismatch and no read or ZIP-
classification error.

A deliberately loose `%PDF-` diagnostic found three non-header occurrences in
two `.js` files and one `.ts` file. The strict detector rejected them because
the marker was source-code content rather than the document header. This
preserves the false-positive evidence instead of counting tool source as three
hidden PDFs.

Combined with the separate first-level nested-archive audit, this closes the
common PDF, RTF, OLE, OOXML and ODF wrong-or-missing-extension question for
ordinary files in the three bounded roots. It does not identify arbitrary
unknown binary formats, inspect PDF page images with OCR, or prove absence
outside the roots. It recovers no institutional record, closes no P0 gate and
authorizes neither submission nor distribution. No file was executed, and no
model forward, scientific fit or scientific payload interpretation occurred.
