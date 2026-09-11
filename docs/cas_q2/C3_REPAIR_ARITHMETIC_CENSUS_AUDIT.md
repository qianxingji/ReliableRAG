# C3 complete repair-arithmetic census: client authenticity audit

Research Lead final audit, Astra xhigh, 2026-09-12 Asia/Shanghai.
**CAS Q2 STATUS: NOT READY.** This accepts the completeness and stated scope of
the arithmetic census. It does not convert either failed full validator into a
PASS and does not accept C3.

## Decision

The complete two-process census and independent reconciliation are accepted as
`ACCEPTED_COMPLETE_CENSUS_AND_BOUNDED_THREAD_DEPENDENCE`. The evidence is
sufficient to freeze a prospective V3 execution-environment contract.

One global current-native-default execution, with all three thread overrides
absent and the authenticated NumPy 2.2.6 / OpenBLAS 0.3.29 SkylakeX pthreads
DLL reporting 12 threads at start and end, exactly reconstructs every saved
component entry, final Top-50 entry and replacement in all 18,000 canonical and
180 fixed-replay records. Its complete discrepancy ledger is empty.

This does not establish that acquisition historically used 12 threads. No
acquisition receipt recorded that value. It establishes a complete present-day
reconstruction under one fixed global execution mode. V2 remains a literal
one-thread failure, and its failed report remains unchanged at the standard
runtime path pending the separately frozen V3 preservation procedure.

## Complete observations

| Mode | Traces | Component lists | Component entries | Exact saved rows | Score-only rows | Replacement changes |
|---|---:|---:|---:|---:|---:|---:|
| explicit one thread | 18,180 | 24,240 | 1,818,000 | 17,673 | 507 | 0 |
| current native default, 12 threads | 18,180 | 24,240 | 1,818,000 | 18,180 | 0 | 0 |

The one-thread ledger contains 565 differing dense component entries and 177
differing final-ranking entries. Every difference is numeric only: document
membership, order, ranks and first eligible replacement remain unchanged. The
largest observed component difference is `1.1920928955078125e-07`; the largest
float32 distance is four ULPs. The affected saved rows are concentrated in
2WikiMultihopQA dense/hybrid, with eight canonical and one replay row in MuSiQue;
HotpotQA has no saved-field mismatch.

The two modes produce different full dense score-vector hashes on 7,075 rows.
Only 507 of those differences reach a saved Top-50/Top-100 score. Therefore
7,075 is a cross-mode arithmetic-sensitivity count, not a count of corrupt
saved records. No tolerance or rounded comparison is used for acceptance.

Both modes independently confirm all 180 replay repair-record signatures,
repair-query-record bytes, repair-query hashes and saved float32 vector bytes
against their canonical counterparts. The processes decode only the repair-query
receipt; `a0` and `a1` rows are skipped as bytes. They perform zero model or
encoder forwards, zero fits, zero Gold materializations and zero original
validator invocations.

## Integrity and retained failures

The task rehashes the 15-file current runtime state: fourteen acquisition files
plus the retained V2 failed report. It authenticates the V1 sibling failure,
the complete V2 failure task, the six used retrieval structures/arrays, original
helper ASTs, 1,544 NumPy/threadpool files in each process, and all 30,823 original
environment files before and after. Both audit boundaries report no denied access.

The first census controller failed before starting a child because its pool-path
suffix named the wrong frozen directory. It is preserved under manifest
`9fe18c18f9efa9fa8a7c1323feec3fc218775fdd995d21da72de0fcbbb477ed1`.
The first client auditor then stopped before reading source rows because its
hard-coded task hash contained one extra character; that audit failure is
preserved under manifest
`140454b5f3137e58e870d1404ac03a88750e39f4ad5d1a571f1b84b477658683`.
Neither failure touched source evidence or ran scientific computation.

The accepted census task manifest is
`5fd10e9c1582bfd55e401255399faef635d854f61f5bdd02c15ac545863a2321`.
Its 44,630,010-byte private archive is
`3e2b45fcd0e24b815ff3af893586f0b96806735a59d26f5d1a74683e8cf80953`
and all 22 members were reopened and rehashed. The independent client-audit
manifest is
`8c8d897312cedda7679be5e689a65aa84f62a6c42b8b9b8052246c80ffce6f33`.
Private ledgers and archives remain local and are not uploaded.

## Claim boundary and next gate

Accepted claim: under the one globally fixed current-default 12-thread BLAS
mode, the stored repair arithmetic is completely reproducible from authenticated
inputs and unchanged original pure helpers.

Unaccepted claims: historical 12-thread provenance; complete V2 validation;
checks after canonical position 6008; independent neural regeneration; answer
quality; current Gold evaluation; C3 or C4 acceptance.

P0 is to implement and fixture-test the separately frozen
[V3 contract](C3_VALIDATION_V3_CONTRACT.md), preserve and relocate the V2 failed
report exactly as specified, execute one full unchanged-scientific-check V3
validation, and independently accept it before C4. P1 remains historical
training/backend provenance and full neural delivery. P2 remains no new model,
feature, seed, thread-count, tolerance or budget search. The leading rejection
risk remains absent fresh empirical evidence and an unestablished contribution;
this audit closes only the extent of the C3 arithmetic anomaly.
