# P0-D statistical statement verification

Decision: **PASS_CAS_Q3_STATISTICAL_STATEMENT_VERIFICATION.** This closes the
reporting-layer statistical gate for the frozen Qwen study. It does not add an
experiment, recompute the sealed bootstrap, cover fitted-model uncertainty, or
authorize manuscript drafting.

## Evidence and verification scope

The new aggregate-only verifier
`../../scripts/verify_cas_q3_claim_statistics.py` (SHA-256
`5cab1545abd0648165aa2102790447165d06b4a6787275639643a12c82ca02d4`)
completed 129 checks and emitted
`P0_D_STATISTICAL_STATEMENT_VERIFICATION.json` (SHA-256
`8e50d910f6b947b42930a0ba4bda07332dddb9dd232e09e41d1bfede7c3472cf`).
It reads only the three sealed aggregate-analysis files and the frozen analysis
source. It does not read per-question outcomes, action ledgers, Gold, reference
strings, answer payloads, bootstrap multiplicities or model artifacts.

The full numerical computation was already independently validated in
`../cas_q2/EMPIRICAL_D_ACCEPTANCE.md`: all 20,000 RNG draws, 180,000 reallocated
policy allocations, 180,000 fixed-action sensitivities, integer event counts,
point/cell reports and six adjusted intervals were checked with explicit-copy
allocation math. P0-D binds planned paper statements to that accepted evidence;
it does not claim a second full bootstrap replay.

## Frozen estimands and units

- The observational unit for point reporting is a question/retriever trace.
  There are 18,000 traces from 6,000 question groups; each group has BM25, dense
  and hybrid siblings.
- Every rate and accuracy uses the full 18,000-trace denominator. The 4,267
  eligible rows and 900 executed actions are not rate denominators.
- Recovery is an executed normalized-EM transition from 0 to 1. Damage is an
  executed transition from 1 to 0. Neutral is every other executed switch.
- `Net = Recovery - Damage count`; `Delta EM (pp) = 100 * Net / 18,000`;
  `Damage rate (%) = 100 * Damage count / 18,000`.
- EM, token F1 and Damage rate are percentages. Their differences and interval
  endpoints are percentage points. Counts must never be labelled percentages.

All nine policy partitions, rate formulas and transition totals match the sealed
point estimates. Keep executes zero actions. Each of the other eight policies
executes exactly 900 actions in the realized batch.

## Bootstrap and multiplicity statement

The primary analysis uses NumPy `default_rng(20260926)` for 20,000
dataset-stratified question-cluster draws. It samples 2,000 question groups with
replacement inside each of the three datasets and assigns each sampled group's
multiplicity to all three retriever siblings. Every draw therefore retains
18,000 trace copies and uses `K=round(0.05*18,000)=900`.

For the primary analysis, each non-Keep policy's frozen score/canonical-key order
is applied to the resampled copy multiplicities and the global top 900 copies are
reallocated. The fixed-action analysis multiplies the originally selected action
memberships by the same draw multiplicities. It is a same-draw secondary
sensitivity and cannot replace the reallocated primary analysis.

The primary family has three ordered comparisons and two endpoints per
comparison, for six endpoints. Its two-sided Bonferroni percentile quantiles are
`0.05/(2*6)=0.004166666666666667` and
`1-0.05/(2*6)=0.9958333333333333`, with NumPy's linear quantile method. The
ordinary `[0.025,0.975]` ranges are secondary and unadjusted.

The directional joint rule passes only when the adjusted EM lower endpoint is
strictly above zero and the adjusted Damage upper endpoint is strictly below
zero. A bound that equals zero is inconclusive. Under this rule:

| Ordered comparison | Reallocated primary joint rule | Fixed-action sensitivity |
|---|---|---|
| ROA-FULL - HGB_GBV_R | Not met | Not met |
| HGB_GBV_R - HGB_ONLY_R | Not met | Not met |
| HGB_GBV_R - GBV_ONLY_R | Met | Met |

## Allowed statistical language

The manuscript may report the single supported joint comparison as conditional
on the fixed reader, fitted heads, bounded candidate pools and realized cohort.
It may state that the other two joint rules were not met and may separately
describe their endpoint directions.

The following interpretations are prohibited:

- equivalence, noninferiority, no effect or proof of absence from a range that
  crosses or touches zero;
- exact finite-sample confidence coverage or a formal risk/safety guarantee;
- coverage of model fitting, calibration, candidate generation, corpus sampling
  or reader/population uncertainty;
- eight confirmatory policy-versus-Keep improvements;
- confirmatory dataset, retriever or dataset-by-retriever subgroup findings;
- treating 18,000 sibling traces as independent questions or treating 20,000
  bootstrap draws as the sample size;
- faithfulness improvement inferred from EM/Damage; or
- selecting the unadjusted or fixed-action range because it is more favorable.

The old Q2 phrase “one shared candidate pool” is not an allowed population
description. The reporting authority is P0-B: three fixed dataset-specific
bounded pools shared within each dataset.

**CAS Q3 STATUS: NOT READY.** P0-D is closed. P0-E through P0-I remain.
