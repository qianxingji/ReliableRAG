# DAA-V3 architecture review after recovery-only isolation

## Status

Development-stage design review written after the sealed recovery-only isolation experiment and before any V3 finalization, full-development fit, or new confirmatory-cohort selection.

The recovery-only isolation result is preserved exactly as:

- architecture decision: `ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE`;
- dependence label: `GBV_AUGMENTED_ONLY`.

This document does not reinterpret the opened development cohort as fresh confirmation.

## Accepted parent evidence

The sealed recovery-only experiment used the already opened 4,500-question / 13,500-trace development cohort with 3,202 eligible traces, fixed 5% action cap, fixed L2 logistic recovery estimator, disjoint Platt calibration, five previously frozen grouped repetition seeds, and three previously frozen LODO transports.

Parent artifact anchors reported by the sealed manifest are:

- `AUTHOR_REPORT.md`: `4090ec70c4a9154ecfc960c9c2bc26317b585d06cc308ee962a984e8981bbf6d`;
- `DEVELOPMENT_DECISION.json`: `a38673592d9d0cba7dadf92c66439919d3fbd99949545aa2868ee01c15796acf`;
- `INDEPENDENT_VALIDATION.json`: `4a809efaf38de9c14e7df696d803a88bf4bab1d1226a688f08813810d90206b7`;
- `RECOVERY_ONLY_ISOLATION_SEAL.json`: `61f5b0c8103af32ce6bb901fdebfff61f1130deee7f382720feee12caf6cede5`.

Before any new scientific fit, verify these local files and the complete recovery-only recursive manifest byte-for-byte.

## Scientific interpretation

ROA-FULL is the strongest V3 development candidate so far. Across the five repeated grouped evaluations it achieved success versus both raw HGB and GbV in 5/5 repetitions. Its median difference versus GbV was approximately +0.437037 EM percentage points and +0.469131 F1 percentage points, with damage no higher than GbV in all five repetitions. All three fixed LODO ROA-FULL minus GbV EM point estimates were nonnegative.

However, ROA-NOGBV did not preserve the safety/performance pattern. It achieved 0/5 success versus both HGB and GbV, had median damage 28 versus 12 for ROA-FULL, and failed every predeclared baseline-independence condition. Therefore the future candidate cannot be described as independent of GbV or as a replacement that does not consume the verifier signal.

The scientifically correct working interpretation is:

> ROA-FULL is a verifier-augmented recovery arbitration candidate that appears to improve the decision rule built on top of the GbV verifier signal.

## Remaining attribution gap

The isolation experiment established that removing `gbv_margin` breaks the candidate, but it did not establish that the other ten non-GbV numeric features add material information beyond a supervised model built primarily from `gbv_margin`.

A reviewer can still ask:

> Is ROA-FULL genuinely combining complementary intervention signals, or is most of the gain explained by supervised re-ranking/calibration of the GbV margin itself, possibly with retriever-specific offsets?

This is the last development attribution question that should be answered before final method freeze.

## Authorized next question

Run exactly one new attribution variant:

`ROA-GBVONLY`

It uses only:

- `gbv_margin`;
- its explicit missingness indicator;
- the same BM25/Dense/Hybrid retriever one-hot indicators used by ROA-FULL.

Everything else—target, model family, preprocessing, calibration, partitions, action cap, tie-breaking and comparators—must remain identical to the sealed recovery-only experiment.

ROA-FULL must not be refit, modified or reselected. Reuse its sealed predictions/actions/results as the fixed reference. ROA-NOGBV remains frozen secondary context only.

## Why this is not feature search

This is a single, reviewer-motivated attribution control selected because the preceding predeclared isolation result classified the supported candidate as `GBV_AUGMENTED_ONLY`. No alternative subset is authorized, and the outcome may not be used to open a new feature sweep.

## Decision boundary

If ROA-FULL materially and consistently outperforms ROA-GBVONLY under the prospectively fixed attribution rule, the additional intervention-derived feature block is supported as contributing incremental value beyond a learned GbV-only control.

If ROA-GBVONLY explains most or all of the gain, do not automatically replace ROA-FULL with GBVONLY post hoc. Instead stop for an architecture/novelty review. A simpler GbV-derived model would require its own prospective finalization rationale.

## Hard boundary

Do not yet:

- fit a final full-development V3 model;
- simplify/remove Platt calibration based on these observed results;
- change the 5% action rate;
- add another feature subset or model family;
- select or inspect new confirmatory IDs;
- run new retrieval/generation/repair/likelihood/base-score extraction;
- claim fresh superiority.

Only after the single GbV incremental-attribution experiment is sealed and independently validated may V3 finalization be reviewed.