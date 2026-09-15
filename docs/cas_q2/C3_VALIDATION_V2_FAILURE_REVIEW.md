# C3 V2 numeric conflict: Research Lead audit

2026-09-12 Asia/Shanghai. **CAS Q2 STATUS: NOT READY.**
This is the bounded Astra xhigh anomaly audit required by MODEL_ROUTING.md.

## Authentic result and first conflict

V2 ran once from commit `4815f514705865573542133efb937b7dc1f53eb9`.
The original validator returned FAIL with `Independent repair component ranks/scores`.
Its complete task failure manifest is
`2642f6f0e1df4f0987e5ab43f4c7e470f479e09dc1fe23062ea36f131d20fa88`;
execution freeze:
`0037d2dcb763b03053c9b8b081880314c0d7c0b0673ba3450de74a1293cdd2de`.
The failed standard report is 17,144 bytes, SHA-256
`1979588de22cc5b450acdffb0f2231500fb70e61e2e9e612d776f91574f7c36b`.
Its content exactly agrees with the final sealed stdout record. Stderr is empty.

The helper-constant correction worked: all original helper global dependencies
resolved. Before stopping, 6,008 canonical traces had completed every check;
the next trace had completed a0 and repair-query validation. This totals 18,026
successful generation checks, 287,962 generated IDs and 13 vocabulary checks.
No generation check failed. The first failing trace is zero-based position
6008, ordinal 6009, in 2Wiki hybrid retrieval. These are partial-validation
counts, not completion of canonical or replay validation.

A separate bounded read-only observer authenticated the failure and examined
positions 6007 and 6008. They have exactly the same saved query vector and query
hash. Position 6007's dense Top-50 agrees exactly. At position 6008 the BM25
Top-100 agrees exactly, and every dense Top-100 document ID and rank agrees.
Only dense rank 95 differs:

| Quantity | Value |
| --- | --- |
| Saved float32 score, represented in JSON | 0.504033088684082 |
| One-thread independent recomputation | 0.5040332078933716 |
| Absolute difference | 1.1920928955078125e-7 |
| float32 ULP difference | 2 |
| Corresponding document index in frozen matrix | 5872 |
| Frozen matrix shape | 11746 x 768 |

The first diagnostic manifest is
`df5f4b5c82364a85193a1f045f72f9124548af07949a526a1d8225b2af44bb95`.
It uses original BM25/helper ASTs and the saved dense matrix/vector. Its field
named native_component_exact reuses the same dense product; it is not a second
encoder or a complete independent producer implementation.

## Controlled numerical observation and limits

Two new isolated arithmetic-only processes used the same original NumPy 2.2.6
and authenticated OpenBLAS 0.3.29 DLL, reporting SkylakeX/pthreads. The explicit
single-thread mode reproduces V2's score. Removing thread overrides reports the
current native default of 12 BLAS threads and exactly reproduces all 100 saved
dense component entries at the failing position. All 16 tested query-vector
address offsets in each mode give that mode's same full score-vector hash.
The NumPy/threadpool package inputs comprise 1,544 files and remain unchanged.
Both completed processes have empty stderr and no denied access.

This establishes thread-dependent arithmetic for the observed input. It does
not establish the original acquisition's actual BLAS thread count, which was
not saved in its receipts, or complete integrity under 12 threads. It also does
not establish that every future score difference leaves ranking, fusion or
replacement unchanged. Neither vector normalization nor expected scores/hashes
were modified; no tolerance was introduced.

The arithmetic observation manifest is
`fb03e5f5152fb309245402fe1b6676ec828cf76d51b8d89929387713f1fe3966`.
An earlier observer failed after computation while hashing NumPy's packaged
pickle fixtures through an unrecognized opaque-hash function. It wrote no
numeric result. Its failure manifest remains
`33c6560786748bfd3690446b30ebb945ba3e7423ef894319cffe459dfdf77951`.
The versioned observer uses the existing authenticated digest boundary for
opaque package hashing; it never deserializes those fixture files.

## Client decision

The client audit rehashed the complete V2 attempt, all 14 original runtime
files, 41 frozen C3 sources/configs, 25 execution controls and all 30,823 original
environment files. It also verified V1's separate failure seal and every bounded
diagnostic manifest. The audit record SHA-256 is
`c0772bc1838e4134b017598ee20174612b6e3c4262897ff02aa7f0f070e2f98b`.
The V2 failed report stays at the standard runtime path; no new successful seal
exists. All fits remain 185; this stage used zero Gold, model forwards or fits.

Accept the failure's authenticity and the bounded thread-dependence finding.
Keep V2 FAIL. Do not rerun either full validator or either neural acquisition.
The [prospective complete repair census](C3_REPAIR_ARITHMETIC_CENSUS_CONTRACT.md)
is the next authorized work under Sol High: compare both fixed modes across
all 18,180 saved repairs and every component/final/replacement field, preserving
all discrepancies. Astra xhigh then reviews the complete evidence before any
new V3 execution-environment design. No V3 or C4 launch is authorized by this
bounded observation.

Leading rejection risks are incomplete fresh empirical integrity/results and
unestablished contribution. Missing evidence includes full C3 acceptance, actual
C4/prelabel/cost/D results, historical BLAS/fit-time records and complete neural
delivery. HGB_GBV_R remains a fixed comparison policy, not an accepted novelty
claim. P0 is the full census, integrity decision and frozen empirical completion;
P1 is provenance/full delivery; P2 is no additional model/feature/seed/budget search.
