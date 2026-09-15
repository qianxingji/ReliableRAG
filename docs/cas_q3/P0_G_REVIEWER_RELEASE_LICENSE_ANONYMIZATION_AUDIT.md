# P0-G reviewer release, license and anonymization audit

Decision: **PARTIAL_PASS_P0_G_ANONYMOUS_AGGREGATE_CANDIDATE_VALIDATED_RELEASE_WITHHELD.**
The repository contains no tracked raw data or scientific output payloads. The
anonymous aggregate scope is now frozen, assembled from an allowlist and proven
by a deterministic clean round trip. Public distribution remains blocked
because the project has no top-level license and P0-H has not certified a target
journal's data/code policy.

Repository inventory snapshot: branch `work/cas-q2-p0-1`, HEAD
`d3feb08c87d9218e334e820a206f985da8c8b95c` before the initial README/audit
changes. Machine-readable inventory: `P0_G_RELEASE_AUDIT.json`. The later
candidate was built from parent HEAD
`dcb30529a659ec0768400d2f5f0e37c1cf9239e3` plus the reviewed release changes;
its machine-readable receipt is
`P0_G_AGGREGATE_RELEASE_CANDIDATE_RESULTS.json`.

## Passed repository checks

- Git tracks 540 files in the audited snapshot.
- The only seven tracked paths under `data/` and `outputs/` are zero-byte
  `.gitkeep` placeholders. Raw benchmark text, answers, model weights, private
  archives and large scientific outputs are not tracked.
- `.gitignore` excludes raw/processed/index data, CAS Q2 outputs, logs,
  predictions, tables and figures.
- Five platform-specific dependency lock files are tracked under
  `requirements/`, alongside the smaller root requirements files.
- No email address pattern was found in tracked text.
- The refreshed root `README.md` points to the Q3 authority, states the accepted
  Qwen result boundary, distinguishes 6,000 question groups from 18,000 traces,
  lists the principal limitations and supplies an aggregate-only verification
  command.
- The export allowlist is fixed in
  `scripts/package_cas_q3_aggregate_release.py`. It copies nine payload members:
  three reviewer documents, a third-party notice inventory, the reporting
  verifier, the frozen statistical source and three sealed aggregate files.
- Two independent builds produced the same 24,362-byte archive SHA-256
  `b785890366995c2943007f5635e622814bc7961dc7b3ded4adee0707dfb7ca8d`.
  The internal manifest SHA-256 is
  `6c8ca3a4d0a9d70ade6a09b7194337390ee74ab1f46c79d862e918418a341a1c`.
- The independent validator passed 100 package checks, extracted every member
  into a fresh temporary root and reran the aggregate verifier there. The
  verifier passed its 129 reporting checks. Six release tests pass, including
  changed-content, undeclared-member, traversal, symlink and identity/path
  scanner rejection cases.
- The candidate contains no Git metadata, remote, author identity, local path,
  benchmark text, answer, per-question outcome, action, bootstrap multiplicity,
  model asset or private archive. Its stricter anonymous profile is usable for
  either single- or double-blind review once the target policy is confirmed.
- Principal dataset, model and pinned software licenses are inventoried in the
  packaged `THIRD_PARTY_NOTICES.md`. Upstream payloads remain excluded.

These checks reduce accidental disclosure risk. They do not show that the
repository is a complete reproduction package because the accepted scientific
graph deliberately depends on local, private, hash-bound assets.

## Blocking findings

### Project license

No top-level `LICENSE`, `COPYING` or `NOTICE` file exists. Default copyright
restrictions do not give reviewers or downstream users clear permission to use,
modify or redistribute the project code. The project owner must choose and add
the intended project license; this audit will not infer one from dependency or
dataset licenses.

Third-party licenses remain separate. The final release must inventory at least
the three benchmark sources, Qwen, BGE, the DeBERTa verifier, PyTorch,
Transformers, NumPy, SciPy and scikit-learn. A project license cannot override
dataset, model-weight or dependency terms. Model weights and benchmark-derived
text should remain links/hash pins unless their upstream terms and the target
journal permit redistribution.

### Anonymous review mode

The GitHub remote identifies the owner, and the historical evidence tree is a
forensic project record rather than an anonymous artifact. In the audited
snapshot, 104 tracked text files contain 237 Windows absolute-path matches.
Eight tracked files contain 14 occurrences of `qianx`, including preserved audit
receipts and local runbooks. Rewriting those historical records in place would
invalidate their evidence role.

The new candidate satisfies the double-blind content constraint: it is a clean
ZIP with no `.git` directory, GitHub remote, author identity, local username,
task-app path or personal home directory. Identity-bearing historical receipts
are omitted and represented by reviewer-safe boundaries and aggregate hashes.
The canonical private evidence remains unchanged for later confidential or
post-acceptance access.

The anonymous artifact is also acceptable as a content form for single-blind or
open review. P0-H still must confirm whether the journal permits an external
artifact and what data/code statement or repository timing it requires.

### Portable reproduction scope

Many scientific executors and historical validators intentionally bind the
original Windows roots. Those paths authenticate the completed run but do not
form a portable reviewer command. The currently runnable public check is the
aggregate-only P0-D verifier, provided its three sealed aggregates are included.
The full private replay is documented in Q2 runbooks and depends on local
archives, model assets and restored environments that are not published.

The candidate freezes the first of these scopes accurately:

1. **Aggregate verification package:** Q3 authority documents, sealed aggregate
   results, reporting verifier, relevant tests and dependency metadata. This can
   verify arithmetic and Claim mapping but cannot regenerate neural candidates.
2. **Confidential/full private reproduction package:** hash-bound private data,
   models, environments and runbooks supplied only through an allowed access
   channel. This is the only route to the accepted deeper replay scopes.

The confidential/full private scope remains governed by the accepted Q2 static
delivery and offline runbooks. It is not copied or relabelled as public. No
package may be labelled end-to-end reproducible if it contains only the first
scope. The 180-trace neural replay remains a bounded witness rather than a full
18,000-trace independent neural run.

## Required release manifest

The candidate manifest records every member's relative path, byte size,
SHA-256, role, access class, current redistribution basis and whether it contains
benchmark-derived aggregates, benchmark text/answers or identity metadata. The
validator rejects absolute member paths, traversal, undeclared files, symlinks,
duplicates, changed hashes and private payload classes.

The export README supplies the exact portable command and expected 129-check
status, explains that it uses Python 3.10+ standard library only and states the
boundary between aggregate verification and neural reproduction. The command
has run successfully from a fresh extracted root. No another-host or OS claim is
made.

## Closure conditions

Completed P0-G closure conditions:

- aggregate/public scope frozen;
- clean anonymous export assembled only from an allowlist;
- exact manifest, archive hash, deterministic rebuild and round-trip extraction
  checks passed;
- reviewer README command executed in the extracted root; and
- unavailable scientific scopes are labelled unavailable.

P0-G remains open until all of these are true:

- the project owner selects a top-level project license;
- P0-H identifies the target journal and its anonymity/data/code policy;
- the selected license and final journal statement are inserted into a newly
  built candidate, after which the same deterministic and independent checks
  pass again.

No scientific experiment, new model or Gold access is needed to resolve this
gate.

The valid candidate archives are preserved at
`E:/paper/ReliableRAG-cas-q3-aggregate-candidate-20260913-e` and `-f`. Earlier
pre-inventory candidates `-a` and `-b` remain preserved. The first inventory
addition failed before archive creation because URL schemes triggered an
overbroad drive-path pattern; empty destinations `-c` and `-d` and the
[failure record](P0_G_AGGREGATE_RELEASE_CANDIDATE_FAILURE_V1.md) are retained.

**CAS Q3 STATUS: NOT READY.** P0-G has a validated withheld candidate but is
still open for the owner license and final journal policy. P0-H and P0-I are
also open.
