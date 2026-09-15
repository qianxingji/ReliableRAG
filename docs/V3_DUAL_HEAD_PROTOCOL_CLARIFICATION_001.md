# DAA-V3 dual-head protocol clarification 001

## Status

Prospective pre-fit clarification. This document resolves two implementation ambiguities found by the protocol-readiness check before any dual-head scientific fitting, calibration, MILP selection, rho selection, policy evaluation, or new confirmatory-ID selection.

The blocked readiness attempt remains immutable. This clarification does not alter the scientific model family, features, rho grid, action rate, repeated-development splits, inner selection rule, comparator hierarchy, support thresholds, rejection thresholds, or interpretation boundary.

## Evidence that this is pre-fit

The accepted readiness receipts record, before this clarification:

- scientific fit calls = 0;
- calibration calls = 0;
- MILP calls = 0;
- rho-selection calls = 0;
- policy-evaluation calls = 0;
- numeric outcome rows were not parsed by the readiness verifier;
- scientific execution started = false;
- no new confirmatory IDs, retrieval, generation, repair, likelihood extraction, or new feature extraction.

The original `PROTOCOL_CLARIFICATION_REQUIRED.md`, `INPUT_VERIFICATION.json`, and `PROTOCOL_READINESS_VALIDATION.json` must be preserved byte-for-byte.

## Clarification A — exact LODO deterministic recipe

LODO is a secondary transport stage and uses a standalone deterministic split namespace. It does **not** reuse or require an `outer_fold` token from the five-repetition development design.

Use exactly one LODO seed:

`20260922`

Canonical held-out dataset tokens are exactly:

- `musique`
- `2wikimultihopqa`
- `hotpotqa`

For each held-out dataset `H`, the two other datasets form the training pool.

### LODO inner folds for rho selection

Assign every question group in the two-dataset training pool to one of four inner folds by:

`sha256("v3-dhc-lodo-inner-v1|20260922|<H>|<dataset>|<sample_id>") mod 4`

For inner validation fold `j in {0,1,2,3}`, all groups with remainder `j` are validation groups. The other three inner folds form the inner-training pool.

Within that inner-training pool, assign fit/calibration groups by:

`sha256("v3-dhc-lodo-inner-cal-v1|20260922|<H>|<j>|<dataset>|<sample_id>") mod 5`

- remainder `0` -> calibration;
- remainders `1,2,3,4` -> fit.

For every inner fold, require both recovery classes and both damage classes in fit and calibration. Otherwise hard stop; do not redraw, merge, rebalance, or change the seed.

For each frozen rho candidate, fit and calibrate both heads only on the corresponding inner fit/calibration groups, solve the frozen constrained selector on the inner validation groups, and pool the four held-out inner results. Choose rho using exactly the already frozen finite-candidate eligibility and lexicographic rule. Held-out-dataset labels are unavailable to this choice.

### LODO final fit/calibration

After rho is chosen from the two training datasets, split all two-dataset training groups for the final LODO heads by:

`sha256("v3-dhc-lodo-final-cal-v1|20260922|<H>|<dataset>|<sample_id>") mod 5`

- remainder `0` -> calibration;
- remainders `1,2,3,4` -> fit.

Require both classes for both targets in final fit and calibration. Fit/calibrate Recovery and Damage heads only on those two training datasets, then apply the already selected rho once to the held-out dataset.

For the held-out dataset:

- `K = round(0.05 * N_all_trace_rows_in_heldout_dataset)`;
- solve the same two-pass `scipy.optimize.milp` selector;
- compare to raw HGB and GbV at exactly the DHC actual selected action count;
- record cap-based comparators only as secondary context if DHC underfills;
- no held-out outcome may influence model fitting, calibration, rho selection, optimization coefficients, or action membership.

The held-out dataset token appears only in deterministic split-domain separation and reporting. It is not a learned predictor.

## Clarification B — immutable pre-LODO receipt and final decision

The phrase "primary development decision before LODO" is replaced by an immutable **pre-LODO primary receipt**, because final `SUPPORTED_FOR_V3_FINALIZATION` depends on condition 8 from LODO.

After all five repeated-development repetitions are complete and before any LODO fitting/evaluation, write:

`PRIMARY_DECISION_PRE_LODO.json`

and seal it with:

`PRIMARY_DECISION_PRE_LODO_SEAL.json`

The receipt must contain, at minimum:

- hashes of all primary repeated-development inputs/outputs;
- success counts versus recovery-only, raw HGB, and GbV;
- median DHC-minus-GbV EM and F1;
- finite-rho outer-fold count;
- median action retention;
- booleans for support conditions 1–7;
- booleans for each of the three frozen rejection triggers;
- a pre-LODO status from exactly the set below.

Permitted pre-LODO statuses:

1. `PRIMARY_REJECT_TRIGGERED`
   - at least one frozen rejection trigger is already true;
2. `PRIMARY_SUPPORT_1_TO_7_MET_PENDING_LODO`
   - no rejection trigger is true and all support conditions 1–7 are true;
3. `PRIMARY_INCONCLUSIVE_PENDING_LODO`
   - no rejection trigger is true but at least one of support conditions 1–7 is false.

This receipt is never overwritten after LODO starts. LODO is run in all three statuses as a fixed secondary transport diagnostic unless a technical hard stop occurs.

After the three LODO evaluations are complete, write the separate final:

`DEVELOPMENT_DECISION.json`

using exactly this order:

1. if any frozen primary rejection trigger is true, final decision = `REJECT_DUAL_HEAD_ARCHITECTURE` regardless of LODO;
2. otherwise, if all support conditions 1–8 are true, final decision = `SUPPORTED_FOR_V3_FINALIZATION`;
3. otherwise, final decision = `INCONCLUSIVE_DUAL_HEAD_STAGE`.

LODO may satisfy or fail condition 8, but it may not alter conditions 1–7, any primary metric, any selected outer rho, or any rejection trigger. LODO therefore cannot rescue a primary rejection.

## Required sequencing

1. preserve the blocked pre-fit namespace and receipts;
2. freeze the corrected R1 protocol/task and execution config;
3. run repeated-development primary stage;
4. write and hash `PRIMARY_DECISION_PRE_LODO.json`;
5. write and hash `PRIMARY_DECISION_PRE_LODO_SEAL.json`;
6. only then run all three exact LODO evaluations;
7. write `LODO_TRANSPORT.json`;
8. write final `DEVELOPMENT_DECISION.json`;
9. run independent validation;
10. write final development seal and recursive manifest;
11. HARD STOP.

## No other authorization

This clarification does not authorize any new rho, model, feature, class weighting, action rate, sibling feature, dataset predictor, retrieval/generation call, final full-development model, or future confirmatory cohort selection.