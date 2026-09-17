# One missing attribution control — Research Lead design, 2026-09-11

Status: **FROZEN DEVELOPMENT DESIGN; NOT YET EXECUTED**.
CAS Q2 STATUS: NOT READY. This design follows the completed two-control review;
it does not amend that experiment, its thresholds, failures or output files.

## Why this experiment is necessary

HGB_GBV_R is competitive with ROA-FULL, but the existing study has no HGB-only
control using the same recovery labels and retriever indicators. Raw HGB and
ten-input ROA-NOGBV answer different questions. Exactly one new fit recipe is
needed to assess whether the external verifier adds incremental information to
the minimal supervised internal scorer. This is a bounded attribution test,
not a new architecture or a search for a higher opened-data score.

## Executable scientific contract

- New method name: `HGB_ONLY_R`. Numeric field: `state_symmetric_hgb` only,
  followed by its one missing flag and BM25/Dense/Hybrid indicators: 5 columns.
- Reuse the exact original ROA eligible/scorable universe and all 28 contexts,
  seeds and group memberships. No redraw, new seed, hyperparameter or action rate.
- Use the original ROA fit-only median, population mean/std, zero-variance rule,
  missing flags, fixed logistic and disjoint Platt parameters unchanged. Require
  both recovery classes; reject all-missing fit columns; preserve technical failures.
- One model per context: 28 base fits + 28 calibrations = 56 scientific fit calls.
  Reuse all seven previously sealed reference methods; never refit them.
- The same 5% all-trace cap and canonical tie order apply. Seal all primary
  actions before held-out metrics, and primary outputs before LODO fits. Save
  every coefficient, calibrator, transform, probability, fit call and action.
- Predeclared secondary allocation sensitivity gives HGB_ONLY_R exactly
  HGB_GBV_R's action counts in each dataset/retriever cell of each partition.
  It remains secondary and cannot replace the common-total-cap comparison.
- Output to a new single-use namespace
  `outputs/cas_q2/hgb_only_attribution_v1` in the isolated worktree. Authenticate
  and preserve both ROA and supervision_matched_controls_v1 complete manifests.
  Freeze source commit, executable bytes, protocol, environment and input hashes
  before fitting. No raw text, new retrieval/generation/base extraction, new
  confirmation IDs or final deployment fit. Exact historical replay stays intact.

## Decision fixed before this new control's results

Evaluate HGB_GBV_R against **each** of HGB_ONLY_R and GBV_ONLY_R. Success in a
repetition means strictly greater Net and Damage no higher. Require at least
4/5 successes against each, median EM difference >0 against each, and no LODO
EM difference below -0.10 pp against either. If all hold, label
`TWO_SIGNAL_INCREMENT_SUPPORTED_FOR_DESIGN_REVIEW`; otherwise label
`TWO_SIGNAL_INCREMENT_NOT_ESTABLISHED`.

Also report all five values, means/sample std/medians, every LODO and all fixed
subgroups against raw HGB, raw GbV, ROA-FULL and ROA-NOGBV. The std measures
partition sensitivity, not confirmation uncertainty. Report F1, Recovery,
Damage, Neutral, Net and all action counts. Do not add a favorable selection
criterion after seeing results.

Neither label automatically names a final deployment model or establishes
novelty. Failure ends automatic minimal-fusion development and triggers a new
Research Lead assessment of whether an empirical study has a defensible claim;
it does not authorize another feature, model, threshold, seed or budget search.
Success allows a concrete final-candidate/confirmation design review, including
prior-work differentiation, end-to-end costs and untouched-ID planning.

Independent verification must reconstruct all 28 models and calibrators,
fit-only transforms, training-ID/target/design hashes, probabilities, exact
primary/secondary memberships, metrics and decision without importing the
executor/fitter as its oracle. Tolerance stays 1e-10. Preserve and explain any
technical retry separately; no scientific refits merely to improve a result.
