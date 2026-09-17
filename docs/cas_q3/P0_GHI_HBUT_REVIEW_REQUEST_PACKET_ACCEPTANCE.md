# P0-G/H/I HBUT institutional review request packet acceptance

**Decision:** `PASS_DETERMINISTIC_HBUT_REVIEW_REQUEST_PACKET_PREPARED_NOT_SENT`

**CAS Q3 STATUS: NOT READY.**

The existing HBUT verification request is now assembled with the current
anonymous manuscript and supplement, proposed Apache-2.0 license text and
scope, third-party notices, data/code boundary, and project-license decision
packet. This is a fixed institutional-review candidate, not a public release or
submission package.

Two builds from tracked-input commit
`f715faaaf6a66cd5a17e70461d07456030e48519` are byte-identical:

- `E:/paper/ReliableRAG-hbut-institutional-review-request-candidate-20260915-a/hbut_institutional_review_request_candidate.zip`
- `E:/paper/ReliableRAG-hbut-institutional-review-request-candidate-20260915-b/hbut_institutional_review_request_candidate.zip`

The archive SHA-256 is
`42f533f6fba88b3d7367477ed27173ea49692f2eaf3e3abff8e85dbe76f13c5b`;
the embedded manifest SHA-256 is
`d99932cc4a8adf826fc475342ec787f402e2726f0f617d608ebc4989b140a0d5`.
Each archive has 11 allowlisted regular-file members and passes 99 integrity
and boundary checks without extraction.

The packet contains no local owner-input file, institutional response, raw
benchmark text, answers, per-question results, model weights or private
reproduction archive. The manuscript artifacts are anonymous drafts. Any later
institutional manuscript approval must be rebound to the exact final
author-populated artifact and its SHA-256.

## Preserved failure and correction

The first direct validator invocation failed before reading either archive
because its package-style import was unavailable when Python used `scripts/` as
the entrypoint directory. Unit tests had not exposed the CLI path. The verifier
now supports both package import and direct-script import, and a subprocess
regression test covers the actual documented command. The already built ZIP
bytes were not changed or rebuilt after this correction.

## External boundary

The package has not been emailed, uploaded or otherwise sent. No institutional
response has been received. It does not verify the 2025 CAS record, approve the
manuscript, establish a legal copyright holder, approve Apache-2.0 release,
resolve the Qwen/DeBERTa terms, authorize distribution, or close P0-G, P0-H or
P0-I. Those decisions require retained HBUT evidence and later client/Astra
audits.

Local validation passes 151 CAS Q3 tests and the complete repository suite
passes 425 tests with two documented Windows platform skips. The reviewer map
authenticates 208 repository records through 1,574 checks. The fail-closed top
gate verifies 240 repository hashes through 870 checks and remains NOT READY.
