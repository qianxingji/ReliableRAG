# P0-G Apache-2.0-aware corrected aggregate V2 acceptance

Signed date: 2026-09-14 (Asia/Shanghai). Reviewer: client-side Research
Project Lead.

**DECISION: PARTIAL_PASS_APACHE2_AWARE_CORRECTED_AGGREGATE_V2_BUILT_AND_VALIDATED_DISTRIBUTION_WITHHELD.**

**CAS Q3 STATUS: NOT READY.** This closes the new-candidate build,
determinism, anonymity, license-scope and aggregate round-trip engineering
work. It does not authorize distribution, establish a persistent archive, or
replace the remaining legal, institutional, third-party and journal gates.

## Preservation and prospective correction

The earlier archive remains an immutable withheld arithmetic witness:

- archive SHA-256:
  `b785890366995c2943007f5635e622814bc7961dc7b3ded4adee0707dfb7ca8d`;
- manifest SHA-256:
  `6c8ca3a4d0a9d70ade6a09b7194337390ee74ab1f46c79d862e918418a341a1c`;
- no member, manifest, status or hash was changed.

The new V2 package was built from a separate source tree. It includes the
corrected non-`-c` DeBERTa training-data caveat and the exact Apache License 2.0
text. It does not relabel the old archive or present a newly written
implementation as an original reproduction artifact.

## New archive and deterministic rebuild

Two new, previously absent external output directories were used:

- `E:/paper/ReliableRAG-cas-q3-aggregate-apache2-candidate-20260914-a`;
- `E:/paper/ReliableRAG-cas-q3-aggregate-apache2-candidate-20260914-b`.

Both contain a byte-identical
`paired_rag_repair_aggregate_apache2_candidate_v2.zip`:

| Field | Value |
|---|---|
| Archive SHA-256 | `4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8` |
| Manifest SHA-256 | `463b26e10ae8724da998033efbea219c26c16be522b52eaaa57cc400f039b4cf` |
| Payload/archive members | 10 / 11 |
| Uncompressed payload bytes | 136,431 |
| Distribution authorized | false |

The package is restricted to the fixed aggregate-reporting allowlist. It
contains no benchmark questions, contexts, Gold strings, generated answers,
per-question outcomes, action memberships, bootstrap multiplicities, model
weights, learned estimators, private archives, local identities, absolute paths
or Git history.

## License boundary

The included `LICENSE` has SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The manifest applies Apache-2.0 only to these project-authored code members:

- `scripts/verify_cas_q3_claim_statistics.py`;
- `scripts/empirical_analysis_math.py`.

The license text, documentation and project-generated aggregates receive
separate redistribution-basis labels. The manifest explicitly states that
non-code members are not relicensed by the project-code license. No benchmark,
model or third-party software payload is included.

## Independent validation

Both external copies independently pass the V2 validator. Each run performs
125 archive, manifest, path, symlink, identity, hash, size, license-scope and
round-trip checks. Extraction into a fresh temporary root and execution of the
packaged standard-library verifier pass all 129 aggregate-reporting checks.

Seven automated tests additionally establish deterministic reconstruction,
code-only license scope, rejection of changed and undeclared members, path
traversal and symlink rejection, and identity/path scanner behavior.

The builder reads the three accepted aggregate JSON inputs needed for the
package. It does not read raw benchmark or answer payloads, per-question
outcomes, action rows or bootstrap multiplicities and performs zero model
forwards and zero scientific fits.

## Remaining P0-G gates

Public distribution remains withheld until all of the following are resolved:

- exact legal copyright holder and year/range;
- institutional NOTICE or release-review decision;
- owner/institutional review of the intended Qwen and DeBERTa release boundary;
- final written authorization of this V2 candidate or a required successor;
- a journal-approved channel for restricted reviewer evidence; and
- an immutable archive DOI or other persistent identifier.

The archive must not be uploaded or published merely because its internal
engineering checks pass.
