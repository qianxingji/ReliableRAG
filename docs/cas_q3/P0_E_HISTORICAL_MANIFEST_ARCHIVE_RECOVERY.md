# P0-E historical `mars_full` manifest archive recovery

Decision: **PARTIAL_PASS_LOCALLY_PRESERVED_MARS_MANIFEST_BYTE_COPY_RECOVERED_NO_INDEPENDENT_TIMESTAMP_OR_FIT_RECEIPTS**.

**CAS Q3 STATUS: NOT READY.** This read-only forensic audit narrows one historical
provenance gap. It does not authenticate the original estimator-fitting events
or replace the missing fit-time receipts.

## Recovered evidence

The preserved original workspace contains
`E:/paper/ReliableRAG/JKSUCIS_R2_ChatGPT_Web_20260831.zip` (1,993,908 bytes,
SHA-256 `4f9fab4d2bdf0d57dbc807ab9494b3b0868230f8d7ff025950fe8d422b055b5e`).
Among 36 relevant ZIP archives scanned under the original workspace, this is the
only archive containing `evidence/mars_full/manifest.json`.

The embedded member
`JKSUCIS_R2_ChatGPT_Web_20260831/evidence/mars_full/manifest.json` is 77,147
bytes with SHA-256
`5924851c30b18785cb1e2bf6893c74cdc819d3549748760bd44b4ebf7ab4e753`.
It declares phase `mars_rag_full_method_experiment`, code version
`mars-rag-full-v1`, and 363 file records. It is byte-identical to the current
preserved `E:/paper/ReliableRAG/outputs/mars_full/manifest.json`.

The archive's own `MANIFEST_SHA256.txt` lists the same member size and digest.
That is a useful package-integrity check, but both the list and the manifest are
inside the same archive.

## Timestamp and lineage boundary

The manifest member carries ZIP timestamp `2026-08-30 02:12:24`; the archive's
observed filesystem last-write time is `2026-08-31 07:52:46 UTC`. Neither value
is an independent trusted timestamp. No external record was found that pins the
archive name or its SHA-256, and the archive was not recovered from tracked Git
history. The evidence therefore proves that a locally preserved package bearing
an earlier date/name contains a byte copy that matches the current manifest; it
does not independently certify when that copy was created or that it preceded
any later ROA action.

Git history contains no candidate historical `mars_full` manifest or original
fit-receipt path; the only nearby matched path is the later
`docs/cas_q2/ROA_MANIFEST_SPEC.json`. A full unreachable-object scan found 35
objects (19 blobs, four commits and 12 trees) and recovered no original fit
receipt or external archive pin.

## Remaining original-fit gap

Inspection of the archive's seven `evidence/mars_full` JSON members found cohort
IDs and method metadata, but no original per-estimator fit-time ID receipt,
fit-time matrix receipt or independent witness of the original fitting process.
Consequently, all of the following remain missing:

- seven original per-estimator fit-time ID receipts;
- seven original per-estimator fit-time matrix receipts;
- an independent witness of the original historical fit execution;
- independent timestamp certification for the recovered archive; and
- evidence ruling out unknown unlogged activity or model pretraining overlap.

Saved-parameter and historical training replays remain valid only within their
previously accepted scopes. This recovery changes the disclosure from “no
complete-manifest copy recovered outside the current output” to “a locally
preserved dated/named package contains a byte-matched copy, without independent
timestamp certification.” It supplies no new scientific result and involved
zero fits, model forwards or Gold access.

The 30-check machine verifier authenticates the archive hash and size, member
count, embedded bytes, internal checksum line, 363 manifest records, current
byte identity, the bounded ZIP filename scan and Git unreachable-object counts.
It does not independently repeat the earlier exhaustive historical-content
search, prove the absence of every possible receipt or external pin, certify a
timestamp, or authenticate an original training event.

Machine-readable receipt:
`P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.json`.
