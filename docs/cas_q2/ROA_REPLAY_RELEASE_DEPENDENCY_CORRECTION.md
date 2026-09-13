# Replay release v1 dependency omission and prospective v2 correction

2026-09-11. CAS Q2 STATUS: NOT READY.

The first new dependency package was built from source ec1e2ef. Its 2,820 copied
files / 340,622,741 bytes and archive round-trip checks passed, but independent
comparison against the accepted primary replay's 2,601 parent records found one
omission: `outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/v2_actions.jsonl`,
3,924,936 bytes, original SHA-256
`2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`.

The old controls' `parents()` authenticates four direct score/action/outcome
sources after traversing parent manifests and freeze metadata. Three sources
were also present in the metadata traversal; V2 actions were not. The v1
packager failed to include this separate direct-input step. Its internal
`PASS_REPLAY_DEPENDENCY_PACKAGE_ONLY` therefore overstates dependency closure;
the Research Lead rejects v1 for replay use. This is a packaging defect, not a
changed original artifact or a scientific replay failure. No v1 relocation or
numerical run was started.

Keep all original package bytes, including its misleading internal status, under
`roa_replay_release_v1`. Its manifest SHA-256 is
`d079da6c2c4b4090df7083b06bdc35ebeeca4bfa51d8b74a8418c11d1405f54f`.
Do not edit the frozen v1 implementation or replace the archive. Record this
superseding rejection separately.

Before any v2 packaging: implement a new version which retains the original
five-namespace traversal and additionally authenticates all four direct inputs
using their original controls-source literal digests. Require every accepted
primary replay parent record to be present with the same path, digest and size;
the primary and independent original parent receipts must match. Bind that
receipt externally, copy it into the private release, and test that omission
or disagreement prevents acceptance. Existing archive/restore/path-guard code
remains unchanged. Repeat only the packaging operation into a new v2 namespace.

All original replay parameters, scientific rules and planned relocation gates
stay unchanged. Run primary and independent relocation once after v2 dependency
coverage passes. Total scientific fits remain 178; no fresh Gold was read.
