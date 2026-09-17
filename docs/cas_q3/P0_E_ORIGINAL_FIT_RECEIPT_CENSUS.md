# P0-E bounded original-fit receipt census

**Decision:** `PASS_BOUNDED_ACCESSIBLE_HISTORICAL_RECEIPT_CENSUS_NO_RECOVERY`

**CAS Q3 STATUS: NOT READY.**

On 2026-09-14, a new read-only census searched four accessible historical
roots: the preserved original workspace and the `original`, `engineering` and
`task` namespaces under the accepted static-root restoration. It also inspected
ZIP central directories under those roots and top-level ZIP files in
`E:/paper`. The scan excluded dependency/model-cache/data directories, never
deserialized a model and interpreted no benchmark answer or Gold value.

The census covered 55,373 ordinary files, 1,770 bounded metadata-text
candidates and 37 ZIP archives with zero scan errors. Exact-size hashing found
14 copies of the seven original model hashes: one complete seven-model set in
the preserved original workspace and the byte-identical seven-model copy in the
later static-delivery `original` namespace. No third independent model copy was
found.

Neither ordinary candidate metadata nor candidate ZIP members contained both a
seven-model identity and a fit-time/receipt/ID/matrix hash marker. The scan
therefore recovered zero original per-estimator fit-time ID receipts, zero
original per-estimator fit-time matrix receipts and zero independent original-fit
witnesses. The 2026-09-10 recovery-only fit manifest remains takeover-period
evidence and is not relabeled as an original training record.

This is a bounded negative result. It does not prove absence from devices,
accounts or archives outside the scanned roots, and filesystem or ZIP timestamps
are not treated as independent chronological certification. The missing seven
original receipt pairs and independent witness remain a disclosed provenance
limitation; P0-1/P0-E authenticity is not upgraded or closed by this census.
