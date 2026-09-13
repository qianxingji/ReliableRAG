# D executable specification before Gold mapping or analysis

CAS Q2 STATUS: NOT READY. Effective 2026-09-11. This specification implements
section D of EMPIRICAL_REPLICATION_PROTOCOL_V1.md. It fixes serialization,
iteration order and validation before implementation and before fresh outcomes.
It changes no model, cohort, seed, endpoint, budget, interval or scientific claim.

## Prerequisites and separated processes

Require the complete accepted C4 prelabel namespace, its independent report,
seal and exact predecessor manifests. An individual scoring-stage PASS or CPU
engineering acceptance is insufficient. Before a process starts, authenticate
every relevant source/input and committed code; use exclusive new namespaces:
empirical_outcome_mapping_v1, empirical_outcome_validation_v1,
empirical_analysis_v1 and empirical_analysis_validation_v1. Keep failed or
partial namespaces. Never alter old frozen sources to pass a new check.

The mapping process can read only accepted cohort IDs, canonical a0/a1 strings,
the authenticated original metric/reference-reader definitions and the three
original raw reference sources. It cannot decode policy scores/actions/models.
An input authentication step may hash their bytes without materializing their
contents. Read selected answer references only; do not expose supporting facts,
decomposition or unselected references as Python strings. Preserve the original
source-answer-only rule for HotpotQA/2Wiki and answer-plus-original-aliases rule
for MuSiQue. Original JSON selected-span readers and Parquet selected-scalar
semantics remain explicit shared dependencies. Parquet decompression can span
unselected rows; this is not claimed to avoid physical decoding of those pages.

Use the authenticated original normalized EM/token-F1 evaluator for a0/a1.
Write exactly the seven-field numeric rows: dataset, retriever, sample_id,
a0_em, a1_em, a0_f1, a1_f1. Preserve all 18,000 rows and 6,000 three-retriever
question groups. Write a reference-set binding hash, source/reference-policy
records and actual access counts; do not write reference strings or leak them
through diagnostics. No quality metric is computed by the mapper.

A separate method-blind outcome validator re-reads only the same 6,000 selected
references, reproduces normalized EM/F1 independently and checks complete schema,
IDs, sibling coverage, reference binding and all 72,000 scalar metric values.
EM is exact; F1 uses the existing 1e-15 outcome-check tolerance. State shared
source-reader dependencies. Seal numeric outcomes only after complete validation.
Analysis processes cannot read raw references or canonical question/answer text;
they read only the accepted numeric outcomes, frozen prelabel scores/actions,
their identity/eligibility metadata and authentication records. No model loading,
fitting, inference, action amendment, network or subprocess occurs after guards.

## Point estimates and fixed reporting universe

Order all trace keys lexicographically by (dataset,retriever,sample_id). Order
question groups lexicographically by (dataset,sample_id). All nine policy names
are fixed: Keep, HGB, GbV, ROA-FULL, ROA-NOGBV, HGB_GBV_R, HGB_ONLY_R,
GBV_ONLY_R, V2. Check each sealed action exactly against the common eligibility
mask, descending saved score and canonical tie order at K=900. This check must
not amend actions or create a policy-specific mask.

For every policy report absolute EM and token-F1, delta from Keep, number of
replacements, Recovery (selected 0->1), Damage (selected 1->0), Neutral (selected
0->0 or 1->1), Net=Recovery-Damage and Damage-rate with all traces as denominator.
Also retain the complete 2x2 EM transition table under realized policy outputs,
including kept rows, so neutral switches and kept answers cannot be confused.
Use math.fsum in canonical order for F1 totals. Repeat these point summaries
for each dataset, retriever and dataset-by-retriever cell using the same globally
sealed actions; no cell-specific ranking or budget. Empty cells are invalid in
the actual balanced experiment.

Primary ordered pairs remain (ROA-FULL,HGB_GBV_R), (HGB_GBV_R,HGB_ONLY_R),
(HGB_GBV_R,GBV_ONLY_R). Endpoint order is (EM difference, Damage-rate difference),
both in percentage points over all 18,000 traces. Positive EM is favorable;
positive Damage is unfavorable. No additional comparison becomes primary.

## Reproducible bootstrap and storage

Instantiate NumPy default_rng(20260926) exactly once. For each of 20,000 draws,
iterate datasets in ascending lexical order: 2wikimultihopqa, hotpotqa, musique.
Within each dataset use rng.choice on its canonically ordered question-group
indices, size=2000, replace=True. Convert sampled indices to integer counts.
All three siblings and all policies receive the same question multiplicities.
Do not use multinomial as a substitute RNG call, reset the generator per policy,
change draw order, refit models or rebuild a realized candidate pool.

Reallocate all scored policies in the resampled whole batch with the accepted
weighted_top_k kernel. Use round(.05*N_all_resampled), including ineligible
copies, canonical score ties and min(K,eligible copies). Duplicate copies at
the budget boundary may be partly selected. Keep selects none. Compute paired
EM/Net and Damage integer event differences before conversion to percentage
points. Fixed-action sensitivity multiplies the original actions by the same
draw counts and is never substituted for the primary reallocated analysis.

Persist all question multiplicities as little-endian uint16 rows in
BOOTSTRAP_QUESTION_WEIGHTS.u16le, with the explicit 6,000-group order and fixed
20,000x6,000 shape in metadata. Each count is checked to be within 0..2000 before
conversion; arithmetic uses int64. Append and flush each row and corresponding
draw receipt, retaining partial bytes on failure. A complete file has exactly
240,000,000 bytes. Draw receipts retain all policy Net/Damage totals, allocation
counts and the three paired integer endpoint differences for both analyses.
These are sufficient to reproduce all specified intervals without raw text.

Use linear percentile quantiles at [0.05/(2*6), 1-0.05/(2*6)] for all six primary
intervals; also report secondary unadjusted [0.025,0.975] ranges and fixed-action
sensitivity on exactly those draws. Preserve all signs and inconclusive ranges.
A zero-touching interval does not exclude zero. A joint favorable EM/Damage claim
requires adjusted EM lower>0 and adjusted Damage upper<0 for that same pair.
No nonsignificant finding is called equivalence or noninferiority.

## Independent analysis gate

The independent validator imports neither analysis executor nor its numerical
aggregation module. Regenerate every question-count draw from the fixed RNG and
group order, verify every stored count and exact file length, explicitly expand
eligible row copies and independently rank/select each policy on every draw.
Check every integer allocation/event count and all paired differences, not a
selected subset. Recompute point estimates/cell summaries, quantiles and all
directional labels separately. Integer/action/EM checks are exact; original F1
arithmetic keeps its 1e-15 bound. Check all inputs unchanged and all 20,000 draws
accounted for before sealing analysis. Shared NumPy RNG/quantile implementation
and fixed-pool/model conditioning must be reported; this is not an exact
finite-sample coverage guarantee or a second independent RNG algorithm.

Test with invented numeric outcomes, ties, duplicate copies, insufficient or
zero eligible rows, three-sibling strata, cache-independent deterministic RNG,
negative findings, zero-touching intervals and deliberate record corruption.
Do not use newly generated answers or fresh Gold as development fixtures.

P0 remains complete fresh evidence and honest contribution assessment. P1 covers
comparison fidelity, complete inference cost, provenance/contamination boundaries
and reproducible release. P2 introduces no further model/feature/seed/budget
search. This protocol and any statistical PASS do not establish Submission Ready.
