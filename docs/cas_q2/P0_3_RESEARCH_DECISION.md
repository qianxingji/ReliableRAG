# Research Lead decision after the minimal-control audit — 2026-09-11

**CAS Q2 STATUS: NOT READY.**

Decision: **FINAL_CANDIDATE_NOT_CLEARED; NO_CONFIRMATION_EXECUTION_FREEZE**.
The requested final-candidate and confirmation-design step cannot honestly be
certified complete after the observed gate failures. This is a scientific
decision from available results, not a local-data access failure or a request
for another routine approval. The original confirmation draft remains a draft.

## The additional design was executed prospectively

The missing HGB_ONLY_R attribution protocol was committed at `164d5e1` before
its implementation (`11efac4`) and before any of its fits. The single-use
`outputs/cas_q2/hgb_only_attribution_v1` namespace contains 28 base models plus
28 disjoint calibrators: 56 new scientific fit calls. All seven earlier reference
methods were reused without refitting. Primary actions and the predeclared
HGB_GBV_R-stratum-count sensitivity were sealed before held-out metrics.

Independent validation passed: 3,942,077 checks, zero maximum numerical error,
28 models / 19,212 eligible predictions and two 81,000-row aggregate ledgers.
Every context, fit-only transform, fit design/target hash, exact action set,
summary and decision was reconstructed without importing the executor/fitter.
The original ROA namespace and previous controls were authenticated unchanged.
The manifest SHA-256 is
`cec3d2c2f085225c3995792a7839f6acbec6fac8b75edd8463ac18b9e2a75a8e`.

| Seed | HGB_GBV_R Net / Damage | HGB_ONLY_R Net / Damage | GBV_ONLY_R Net / Damage |
|---|---:|---:|---:|
| 20260917 | 291 / 10 | 238 / 26 | 237 / 15 |
| 20260918 | 294 / 6 | 246 / 23 | 241 / 16 |
| 20260919 | 292 / 9 | 241 / 26 | 240 / 14 |
| 20260920 | 290 / 8 | 244 / 22 | 242 / 15 |
| 20260921 | 296 / 7 | 241 / 22 | 238 / 12 |

The fusion has 5/5 Net-higher/Damage-no-higher successes versus each single
signal in the mixed-development repetitions. Median EM differences are
+0.377778 pp versus HGB_ONLY_R and +0.392593 pp versus GBV_ONLY_R.
LODO fusion-minus-HGB_ONLY_R is +0.488889 pp (MuSiQue), **-0.111111 pp
(2Wiki)** and +0.377778 pp (HotpotQA). The 2Wiki difference fails the frozen
-0.10 pp floor. Do not round it up, relax the floor, redraw the split, or treat
the mixed-development repetitions as five independent confirmations.
The exact decision is `TWO_SIGNAL_INCREMENT_NOT_ESTABLISHED`.

This failure does not imply absence of mixed-population complementarity,
equivalence of models, or a statistically established negative transfer effect.
It means that the prespecified conjunction needed for advancement did not hold.

## Scope of the completed work

P0-1 saved-parameter replay is accepted, with historical provenance limitations
specified in P0_1_CLIENT_ACCEPTANCE.md. P0-2 is complete and independently sealed;
the full-stack contribution gate failed. P0-3 has completed a scientific review
and one prospectively justified diagnostic control. It has **not** produced an
accepted final deployment candidate or executable confirmation protocol.
New scientific fits in this takeover total 168; retrieval, generation, base-score
extraction, new confirmation-ID selection and final deployment fits remain zero.

## Next research contract; no automatic model search

The next research task is a focused decision about an empirical-study route,
not another optimizer. It must determine whether a fixed paired-answer,
budget-constrained evaluation of complexity, supervision and population shift
has a meaningful contribution beyond the recent works in
P0_2_CONTRIBUTION_REVIEW.md. It must keep both favorable mixed-data results and
unfavorable LODO results. It must not reframe ordinary logistic stacking as a
new algorithm or claim end-to-end unseen-domain transfer.

A future positive Research Lead decision must specify, before implementation:

1. One clearly stated claim and its population; either evaluate a fixed method
   as an empirical object or give a supported method contribution. Explicitly
   explain any change from the failed robustness-based advancement route.
2. The final top-level recipe, existing upstream model versions and one disjoint
   fit/calibration split. Reuse the saved rules; do not deploy an unreviewed
   ensemble, select a favorable partition, or refit after calibration.
3. Fixed reference policies, including both supervised single-signal controls,
   raw HGB/GbV and ROA-FULL/NOGBV; primary comparison hierarchy and multiplicity.
4. A question-level planning analysis on opened development data that accounts
   for batch top-K reallocation, then a fixed fresh sample size within actual
   availability. Availability alone does not justify 1,500 questions/dataset.
5. Complete pre-outcome analysis, seals, current-method cost accounting and
   claim limits. The cached likelihood matrix is not an exact TrustMargin
   implementation. A 5% switch count is not a 5% inference-cost budget.

Until that design exists, there are no further scientific fits or new outcomes
authorized by these protocol files. Read-only source/claim/cost audits and
technical reproducibility work can proceed under the user's project mandate.

## Remaining concrete gaps and priority

- P0 scientific: a defensible final claim/candidate and a complete frozen
  confirmation design. The two failed advancement decisions must remain visible.
- P0 reproducibility: original per-estimator fit-time training-ID/matrix receipts
  for the seven `outputs/mars_full/models/*.joblib` learned inputs, and an earlier
  independent pin for the complete `outputs/mars_full/manifest.json`, were not
  recovered. Source/ledger reconstruction and zero observed overlap are documented;
  they do not become evidence of unobserved historical execution.
- P0 submission: actual new confirmation, current-method evidence and a claim-
  consistent submission package do not exist. No journal's CAS partition has
  been certified; journal year/ISSN/category and institutional recognition must
  be verified before any Submission Ready label.
- P1: current-method end-to-end costs, error/transfer analysis, full-text nearest-
  work comparison and reproducible public release scope.
- P2: postpone larger models, more feature/seed/budget searches and cosmetic work.
