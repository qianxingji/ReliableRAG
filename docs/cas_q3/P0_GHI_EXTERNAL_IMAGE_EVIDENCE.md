# P0-G/H/I external raster-image evidence audit

Decision: **PASS_BOUNDED_COMMON_RASTER_IMAGE_VISUAL_REVIEW_NO_EXTERNAL_CLOSURE_EVIDENCE**.

**CAS Q3 STATUS: NOT READY.**

On 2026-09-15, a read-only common-raster signature census covered the same
three logical roots used by the external-closure searches: the original
workspace, the preserved private historical root and the old
`ReliableRAG_Codex.zip`. It inspected the leading 64 bytes of all 465,460
ordinary-file paths, all 2,389 direct members of 39 ZIPs and all 301 members of
four first-level nested ZIPs. It recognized PNG, JPEG, GIF, BMP, TIFF, WebP and
HEIF-family signatures independently of suffix.

The census found 104 image occurrences: 83 ordinary files, 21 direct ZIP
members and no nested-ZIP image member. These reduce to 43 unique SHA-256
hashes. Every detected format has an expected suffix, every image-labeled file
has recognized image magic, and there is no read, archive or classification
error. An optimized deterministic rerun produced byte-identical JSON with
SHA-256 `a5f8f68651313ef685462a84fbf18a090f87c8c2a31843b8542cfed0885da5bf`.

The project lead visually reviewed all 43 unique hashes. A contact sheet was
used for 41 images; two legacy 16-bit BMP fixtures that Pillow and OpenCV could
not decode were each opened separately in the native image viewer. The content
breakdown is:

- 14 unique old-manuscript figures across 70 ordinary/ZIP occurrences: study
  charts, workflows and representative cases;
- 29 unique shared-runtime assets across 34 occurrences: `bmp-js` format-test
  fixtures, loading/application icons, OCR-library logos and demo GIFs.

None is an HBUT CAS partition record, manuscript approval, copyright/release
approval, license decision, reviewer-access authorization or persistent-archive
receipt. No candidate is recovered.

The logical original-workspace tree contains one Windows junction. Consequently,
7,796 of the 465,460 ordinary paths resolve outside the three declared physical
roots into a shared local runtime; all 34 runtime-image occurrences and their 29
unique hashes are in that disclosed expansion. The separate
[logical-root reparse disclosure](P0_GHI_LOGICAL_ROOT_REPARSE_DISCLOSURE.md)
explains the effect on the earlier external searches. The expanded scan does not
prove absence elsewhere, and mutable shared-runtime bytes are not treated as
preserved project evidence.

The audit did not perform OCR, interpret scientific payloads, execute any
scanned file, run a model forward or fit a model. It closes no P0 gate and
authorizes neither submission nor distribution.
