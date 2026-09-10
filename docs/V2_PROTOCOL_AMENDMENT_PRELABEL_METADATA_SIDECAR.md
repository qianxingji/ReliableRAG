# DAA-V2 prospective clarification — sealed branch metadata sidecar for historical feature reconstruction

## Status

**Prospective input-contract clarification recorded after the runtime-branch freeze and after a blocked, zero-scoring diagnostic attempt, but before any fresh base-score computation, DAA-V2 fitting on fresh data, HGB/V2/GbV scoring, arbitration action selection, fresh-label access, Gold mapping, or evaluation.**

The blocked diagnostic namespace must remain immutable evidence. This clarification does not retroactively convert that blocked attempt into a successful execution.

## Why this clarification is necessary

The frozen canonical branch ledger intentionally contains the minimum shared branch representation:

- dataset
- retriever
- sample_id
- question
- a0
- a1
- evidence0
- evidence1

Each evidence item is the exact frozen passage text string. The authenticated historical feature/scoring implementation, however, also requires immutable retrieval/evidence metadata including document identity, retrieval score, rank, title, and content hash for evidence-change/state-symmetric features and likelihood prompt rendering.

The blocked input-contract diagnostic established that those values are not uniquely recoverable from the canonical text alone and that replacing them with zeros, fabricated identifiers/titles, or text-derived substitute identities changes the frozen historical method. Therefore the scientifically correct behavior is to restore the already sealed metadata associated with the same frozen branches rather than invent new values or alter the method.

## Authorized sidecar

The only additional fresh-side input authorized for DAA-V2 historical-feature reconstruction is:

`outputs/daa_v2_fresh_v1/runtime_branch_freeze/branch_provenance.jsonl`

Frozen SHA-256:

`4d0ce2c89bb96c33e76d4d1879add655cd79e9c4bd3b9f0545197254ad759b20`

This file was created and sealed as part of the runtime-branch freeze before any V2/HGB/GbV scoring or fresh-label access.

## Authority hierarchy

`canonical_branches.jsonl` remains the **sole authority** for:

- trace membership and order;
- dataset, retriever, sample_id;
- question text;
- a0 and a1;
- evidence0 and evidence1 text strings and their positions.

`branch_provenance.jsonl` is authorized **only** to restore the already frozen metadata attached to those exact canonical evidence items.

The sidecar must never override, replace, edit, normalize, regenerate, reorder, filter, or select any canonical question, answer, evidence text, trace, or branch.

## Allowed metadata fields

Only metadata required by the authenticated historical scoring path may be projected from the sidecar. The allowed semantic set is:

- document_id;
- title;
- rank / evidence position;
- retrieval score;
- content hash or equivalent sealed document-content identity used only for binding/verification;
- branch/evidence-state indicator needed to distinguish evidence0 from evidence1;
- trace identifiers needed for the exact join.

No Gold, answer aliases, supporting-fact labels, correctness, EM, F1, recovery, damage, preference/outcome labels, or any derived evaluation quantity is authorized.

If the sidecar contains additional fields, they are not automatically authorized. Build a narrow metadata-binding projection with an explicit field allowlist before scientific scoring.

## Required canonical-sidecar binding gate

Before any likelihood or base-estimator model call, create a metadata-binding projection and independently verify all of the following:

1. The sidecar SHA-256 exactly matches the frozen hash above.
2. The canonical branch SHA-256 remains `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`.
3. There are exactly 13,500 unique `(dataset, retriever, sample_id)` traces in both inputs.
4. Trace-key sets are exactly equal; no missing or extra trace is tolerated.
5. Every canonical branch has exactly five evidence0 and five evidence1 positions.
6. Sidecar metadata binds one-to-one to every canonical evidence position.
7. Position/rank order exactly agrees with the frozen branch construction.
8. Content hashes and/or deterministic document-text reconstruction prove that the sidecar metadata points to the exact canonical evidence text at each position.
9. Any document ID/title/score/rank ambiguity, mismatch, missing value, duplicate binding, or content-hash mismatch is a hard stop.
10. No default score, fabricated document ID/title, approximate text match, fuzzy join, nearest-neighbor join, or content-derived replacement identity is permitted.
11. The binding procedure does not inspect or compute answer quality or any fresh evaluation quantity.

Write the narrow projection into the new pre-label namespace and hash-seal it before using it for base-feature extraction.

## Scientific interpretation

This clarification does **not** change the candidate pools, retrieval rankings, evidence branches, answers, DAA-V2 architecture, historical estimator binaries, feature definitions, likelihood prompts, action rate, GbV recipe, thresholds, statistical tests, or success criteria.

It narrows the intended meaning of the earlier phrase “consume only the canonical branch ledger” as follows:

> Canonical branch text and trace membership come only from `canonical_branches.jsonl`; the already sealed `branch_provenance.jsonl` may additionally supply hash-bound metadata that the authenticated historical feature/scoring implementation requires and that cannot be reconstructed from canonical text without changing the method.

This is an input-contract correction, not a post-result method change. It is recorded before any fresh scientific score/action result exists.

## Blocked diagnostic preservation

The existing blocked namespace:

`outputs/daa_v2_fresh_v1/prelabel_seal/`

must remain byte-for-byte preserved. It is diagnostic evidence that the canonical-only interpretation failed closed before scientific scoring.

The next authorized execution must use a new namespace such as:

`outputs/daa_v2_fresh_v1/prelabel_seal_v2/`

and may read the blocked namespace only as provenance/control evidence, never as a source of scientific scores or actions.

## Hard boundary

This clarification authorizes only the sidecar metadata restoration needed for the already frozen pre-label scoring pipeline. It does not authorize fresh Gold/correctness/outcome access, method retuning, cohort changes, branch regeneration, action-budget changes, result-based filtering, or evaluation.
