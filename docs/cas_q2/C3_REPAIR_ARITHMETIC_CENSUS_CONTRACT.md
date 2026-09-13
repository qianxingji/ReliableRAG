# C3 repair arithmetic census after the V2 failure

Research Lead prospective design, 2026-09-12 Asia/Shanghai.
**CAS Q2 STATUS: NOT READY.** This contract is frozen before census code and
execution. It authorizes a complete diagnostic of saved repair arithmetic,
not a new scientific method or a retry of the full C3 validator.

## Question and fixed scope

The literal V2 validator failed at canonical position 6008. The first observed
difference is one dense component score at rank 95, with identical document
membership/order. The bounded diagnostic found that one-thread NumPy/OpenBLAS
and the current native default of 12 threads produce different float32 products
from identical matrix/vector bytes. The latter exactly matches this saved
component. Original acquisition receipts did not capture actual BLAS threads.
That missing evidence remains missing; a current default is not historical proof.

Determine the complete extent of the discrepancy across all 18,000 canonical
and 180 fixed-replay repair records, including every component entry, final
Top-50 ranking, RRF order and first eligible replacement. Do not infer full
integrity from the first example, sample only favourable rows, or ignore a
discrepancy because its numeric magnitude is small.

Use exactly two separate processes in the original native package environment:

1. V2 controls: OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1.
2. Current native default: remove those three overrides and require the observed
   NumPy OpenBLAS pool to be 12 threads, version 0.3.29, SkylakeX, from the same
   authenticated DLL as the bounded diagnosis. Stop if it differs. Do not search
   more thread counts or select a thread count per dataset/query/score.

Both processes use identical, pinned source and input bytes, offline settings,
no CUDA/model/encoder/fit/Gold access, and no original-output writes. Explicitly
record each process's actual package paths, NumPy version and threadpool state
at start/end. Verify the 30,823 original environment files before/after. Opaque
package hashing must use the authenticated digest boundary; NumPy's shipped
pickle test fixtures must never be deserialized.

## Computation and records

Authenticate all 14 original runtime files against the canonical/replay manifests
and every used retrieval matrix/BM25 structure against original acquisition
inputs. Authenticate the V2 failure task and exact failed report at the standard
path; leave it there. Read no raw benchmark, reference/Gold store, learned-policy
artifact or outcome ledger. Read only the necessary repair-query text from the
existing generation receipts. Do not decode a0/a1 answer strings for this task.

Extract and authenticate the original pure independent helpers, with their
dependencies explicitly bound: bm25_scores, rank_entries, rrf, replacement and
validate_rank. Keep their bodies, dtypes, operation order and every comparison
unchanged. Recompute dense scores as the original matrix @ saved float32 query
vector. Require all JSON vector scalars to round-trip exactly to float32; do not
renormalize, round, cast to float64 for the production product, substitute
recorded component scores or load any encoder. BM25 uses original float64.

For every trace in the exact frozen order, bind dataset/retriever/sample ID,
position and query hash. Check the component depths (50 for single retrievers,
100 for each hybrid component), validate saved schemas, independently reconstruct
final rankings/RRF and replacement, and compare every stored field exactly.
Read the saved original e0/e1/inserted/replaced IDs from repair records; the final
full validator must later verify their question/evidence-text provenance.

Save a per-trace private JSONL observation for both modes, including original
repair/query record hashes, recomputed full score-vector hashes, equality flags,
counts of differing scores, ordered-ID/rank changes, max absolute/ULP differences,
final-ranking changes and any replacement/evidence-ID changes. Save every
differing component/final-ranking entry in a separate complete discrepancy ledger;
no truncation, omission or selective exclusions. Native/default disagreement
is an observation, not a passing row. Classify exact mismatches separately as
score-only, membership/order, final-ranking or replacement changes.

Inspect all 18,180 rows even when exact comparison fails, since the purpose is
an exhaustive discrepancy census. Unexpected exceptions, bad schema, source
mismatch, forbidden access or an unaccounted execution error stop the process
and preserve a new failure. This observer must not write an original PASS or
invoke the original main/validate_all. Record explicit mode completion and
exact stratum counts; totals are 24,240 component lists and 1,818,000 component
entries per mode. All 18,180 final Top-50 lists and replacements are required.

A separate client reconciliation reads both complete result ledgers, verifies
the exact key set and each file hash, compares mode classifications, and records
all mode differences. Establish whether the 12-thread computation is completely
exact to saved records, including both canonical/replay, not just the first
failure. Confirm the 180 fixed replay repair signatures and query/vector bytes
match their canonical counterparts. No threshold, tolerance, expected score or
ranking/hash change is allowed; high-precision arithmetic may be diagnostic
only and must not redefine acceptance.

## Execution controls and next decision

Sol High implements this bounded diagnostic and runs it once in a new isolated
task namespace. Freeze source/commands/environment/inputs before execution;
keep a clean committed engineering checkout. Include all controls, raw logs,
both complete observation/discrepancy ledgers and failures in a private evidence
kit with independent archive verification. Rehash all used original files,
the V1 sibling failure seal, V2 report and environment on completion. Never
repeat canonical or fixed-replay neural generation.

Return to Astra xhigh for the anomaly decision. A successful census is still
not full C3 acceptance. If one global 12-thread computation matches every saved
field exactly, consider a separate prospective V3 execution-environment contract
that discloses historical-thread uncertainty and retains literal V2 failure.
Only that later contract may specify preservation/relocation of the V2 report,
new fixtures and one full unchanged-scientific-check validation. If any saved
ranking/replacement cannot be reproduced exactly, retain the conflict and review
the effect on the scientific protocol before proposing further work. Do not
automatically retry V2/V3, relax tolerance, choose the best mode or begin C4.

P0: full discrepancy census, reviewed integrity decision, complete C3 then
C4/prelabel/cost/D evidence and contribution assessment. P1: historical training
and backend provenance, full neural delivery. P2: no feature/model/seed/budget
search. No current outcome/quality claim is made; fits remain 185.
