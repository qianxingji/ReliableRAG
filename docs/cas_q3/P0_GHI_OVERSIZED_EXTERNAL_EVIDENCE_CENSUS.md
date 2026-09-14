# P0-G/H/I oversized external-evidence census

Decision: **PASS_BOUNDED_OVERSIZED_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_CANDIDATES**.

**CAS Q3 STATUS: NOT READY.**

On 2026-09-14, a separate read-only streaming pass covered every text file and
ZIP text member that the primary accessible-evidence census skipped only because
it exceeded 5,000,000 bytes. The same three roots and exclusions were used.

All 26 oversized ordinary text files were scanned, covering 518,683,752 bytes.
All 12 oversized text members across the same 39 ZIP archives were streamed,
covering another 970,485,466 uncompressed bytes. No item exceeded the
1,000,000,000-byte stream guard. The pass found zero marker candidates and zero
read or size error.

The scanner reads bounded chunks with overlap so a marker split across two
chunks is detected. It hashes each streamed item but reports a hash only for a
candidate, reports no matched content or ordinary-file path, extracts no archive,
and executes no file. Synthetic tests cover clean large files, a marker across
the chunk boundary, streaming from a ZIP without extraction, the maximum-size
guard and excluded descendants.

This closes only the primary census's oversized-text limitation. It does not
inspect unsupported binary formats, prove absence outside the three roots,
authenticate institutional authority, or replace a retained HBUT record. No
institutional CAS, manuscript-approval or code-release candidate was recovered,
so P0-G, P0-H and P0-I remain open. The pass performed no model forward,
scientific fit, bootstrap recomputation or semantic interpretation and does not
authorize submission or distribution.
