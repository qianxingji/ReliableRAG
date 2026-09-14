# P0-E historical-manifest recovery Astra xhigh authenticity audit

Decision: **PASS_ASTRA_XHIGH_BYTE_AUTHENTICITY_WITH_TIMESTAMP_AND_ORIGINAL_FIT_GAPS_RETAINED**.

**CAS Q3 STATUS: NOT READY.** This independent read-only audit accepts the byte
authenticity of one locally preserved dated/named package copy. It does not
accept the package name, ZIP member time or filesystem time as independent
evidence of historical ordering.

## Independent result

GPT-6 Astra xhigh independently verified the preserved ZIP as 1,993,908 bytes
with 79 unique members. The embedded `mars_full/manifest.json` is 77,147 bytes,
contains 363 path/size/SHA records and is byte-identical to the current
preserved manifest. The internal checksum entry agrees. The bounded scan found
one matching archive among 36 relevant ZIP files, and the Git forensic count
remained 35 unreachable objects.

The audit also reran the generators with receipt writing prohibited and compared
their would-be JSON output with the committed receipts:

- recovery verifier: 30 checks, exit 0;
- reviewer evidence map: 42 repository records, 246 checks, exit 0; and
- submission-readiness gate: 79 repository pins, 205 checks, exit 2 as required
  for the explicit fail-closed `NOT_READY` state.

No Gold, model forward or scientific fit was used. The audit changed no file.

## Accepted wording boundary

The accepted decision is
`PARTIAL_PASS_LOCALLY_PRESERVED_MARS_MANIFEST_BYTE_COPY_RECOVERED_NO_INDEPENDENT_TIMESTAMP_OR_FIT_RECEIPTS`.
The final wording states only that a locally preserved package bearing an
earlier date/name contains a manifest byte copy matching the current file. It
does not claim that the package was independently proved to precede later ROA
work. The recovery verifier explicitly says it did not repeat an exhaustive
historical-content search.

The following remain missing:

- seven original per-estimator fit-time ID receipts;
- seven original per-estimator fit-time matrix receipts;
- an independent original-fit witness;
- independent timestamp certification; and
- evidence excluding unknown unlogged activity or pretraining overlap.

## Audited hashes

| Path | SHA-256 |
|---|---|
| `P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.md` | `991b4aa707b6ed2e75a582e4def7da581525d57b4c44450527c8a87f55d270e1` |
| `P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.json` | `8c8e69d32074509d16906b46b0526f94a456d8d90d53372bf960b931748309ae` |
| `../../scripts/verify_cas_q3_historical_manifest_archive_recovery.py` | `b5ff80d428c5cd73b029f63eaa2e91208075ecd38dbf056a2938d83b447c4718` |
| `P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_VERIFICATION.json` | `eb1630d7d4249f799d1d6dbfbee77f57b0a2646f71221aeaddd4a080630acddc` |
| `REVIEWER_EVIDENCE_MAP.md` | `b7233a4cca854026d7f313664421a9a95c6852c440373bbd4e8e18d8fef94cc8` |
| `REVIEWER_EVIDENCE_MAP.json` | `08d528f04e4c7c4388b6d744f962218840f431dd1cbd2253c8d2c13a83adaf28` |
| `REVIEWER_EVIDENCE_MAP_VERIFICATION.json` | `95434bbfa720c76098adc82e5ae976b2b866b7a6f4b93592bf674c0a38240863` |
| `../../paper/manuscript.tex` | `c8b7c0ca833f1fb5d46a184a1065ea3d7d24daae897942a54c9096eed6c6a3f9` |
| `../../paper/supplement.tex` | `97d2eececeeee84c4d2c5052e1fbd981c41fdda3f9d00ba827c2781f4700a47f` |

This PASS closes only the wording and byte-authenticity review of the recovered
copy. P0-G, P0-H and P0-I remain open.
