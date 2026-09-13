# P0-G reviewer release, license and anonymization audit

Decision: **REVISE_P0_G_RELEASE_NOT_READY.** The repository contains no tracked
raw data or scientific output payloads, and its root README has been updated to
the Q3 authority. A reviewer release cannot yet be certified because the project
has no top-level license, no frozen export scope and no journal-specific
anonymization mode.

Snapshot: branch `work/cas-q2-p0-1`, HEAD
`d3feb08c87d9218e334e820a206f985da8c8b95c` before the README/audit changes in
this review. Machine-readable inventory:
`P0_G_RELEASE_AUDIT.json`.

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

### Double-blind anonymity

The GitHub remote identifies the owner, and the historical evidence tree is a
forensic project record rather than an anonymous artifact. In the audited
snapshot, 104 tracked text files contain 237 Windows absolute-path matches.
Eight tracked files contain 14 occurrences of `qianx`, including preserved audit
receipts and local runbooks. Rewriting those historical records in place would
invalidate their evidence role.

If the target journal uses double-blind review, the submission artifact must be
a clean export with no `.git` directory, GitHub remote, author identity, local
username, task-app path or personal home directory. Identity-bearing historical
receipts should be omitted from the anonymous package and represented by
reviewer-safe summaries plus cryptographic hashes. The canonical private
evidence must remain unchanged for later confidential or post-acceptance access.

If the target journal is single blind or open review, a clean portable export is
still required, but identity redaction may not be necessary. P0-H must decide
which mode applies before P0-G can close.

### Portable reproduction scope

Many scientific executors and historical validators intentionally bind the
original Windows roots. Those paths authenticate the completed run but do not
form a portable reviewer command. The currently runnable public check is the
aggregate-only P0-D verifier, provided its three sealed aggregates are included.
The full private replay is documented in Q2 runbooks and depends on local
archives, model assets and restored environments that are not published.

The final package must state one of these scopes accurately:

1. **Aggregate verification package:** Q3 authority documents, sealed aggregate
   results, reporting verifier, relevant tests and dependency metadata. This can
   verify arithmetic and Claim mapping but cannot regenerate neural candidates.
2. **Confidential/full private reproduction package:** hash-bound private data,
   models, environments and runbooks supplied only through an allowed access
   channel. This is the only route to the accepted deeper replay scopes.

No package may be labelled end-to-end reproducible if it contains only the first
scope. The 180-trace neural replay remains a bounded witness rather than a full
18,000-trace independent neural run.

## Required release manifest

Before closure, create one immutable manifest for the chosen reviewer export
that records, for every member, its relative path, byte size, SHA-256, role,
public/private status, license/redistribution basis and whether it contains
benchmark-derived content or identity-bearing metadata. The validator must
reject absolute member paths, traversal, undeclared files, symlinks, duplicates,
changed hashes and private payload classes in a public export.

The export README must contain exact commands, expected receipt hashes, tested
Python/platform constraints, expected skips, resource limits and the boundary
between aggregate verification and neural reproduction. It must use portable
relative paths. It must not claim another-host or OS reproduction without an
actual run.

## Closure conditions

P0-G remains open until all of these are true:

- the project owner selects a top-level project license;
- P0-H identifies the target journal and its anonymity/data/code policy;
- the aggregate/public and any confidential scopes are frozen;
- a clean export is assembled from an allowlist and independently scanned;
- the manifest, archive hash and round-trip extraction check pass; and
- the README commands execute in the declared environment with all unavailable
  scopes labelled unavailable rather than silently skipped.

No scientific experiment, new model or Gold access is needed to resolve this
gate.

**CAS Q3 STATUS: NOT READY.** P0-G is open. P0-H and P0-I are also open.
