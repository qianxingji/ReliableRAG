# DAA-V3 dual-head risk-constrained development protocol

## Status and objective

Development-only protocol. Written after the sealed RG-HGB development result and before any dual-head fitting, risk-budget selection, final V3 freeze, or new confirmatory cohort selection.

This protocol tests one structural hypothesis only:

> Separately estimated recovery and damage probabilities, combined through an explicit damage-budget constraint, can improve the repair-selection tradeoff beyond raw HGB, the rejected simple RG-HGB gate, and GbV.

This is not confirmatory evidence and does not authorize a new fresh cohort.

## Parent evidence and mandatory preflight

Before any fit, verify the following known anchors exactly:

- amendment execution record uploaded/audited SHA-256: `a91bc244db608e0e78f0c46f91a2f5fb326d3827a2d88bfeff134bfed0bd0978`;
- RG-HGB author report uploaded/audited SHA-256: `bad7f809566f13aa0e0eeb1fb0f3873e707fc2dee9d4f3077a72accbe4a7e6f3`;
- RG-HGB independent validation uploaded/audited SHA-256: `a7345245a1d919d1f86a8067377699974c919a40181d4228f7b0cff89ce46bde`;
- V3 risk-head comparison seal: `1d1c01f1c483db16cdeefb9f846dfb36b4058597a534c34a930a11c60eeea034`;
- V3 failure-audit seal: `ff2c177bd71e29f1170b4093594194d40d2bc0d89f2eaf1273802c8c07840882`;
- opened numeric outcomes: `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`;
- V2 base-score ledger: `d3842c514224354206846edb7e96b7296765d67050b131b552f469d0c64fa609`;
- GbV score ledger: `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`;
- canonical branches: `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`.

Also locate the sealed local `outputs/daa_v3_development/risk_gated_policy_v1/RISK_GATED_POLICY_SEAL.json` and its recursive `SHA256_MANIFEST.json`, record their exact hashes, require status PASS, decision `REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD`, and verify the full parent namespace is unchanged. Any mismatch is a hard stop.

The remote branch must contain prospective clarification commit `e263760591c950bc5f1e73a102edce98559cbc93` or a strict descendant before execution.

## Development population

Use only the already opened V3-development cohort:

- 4,500 question groups;
- 13,500 retriever traces;
- 3,202 frozen eligible/scorable traces;
- retrievers: BM25, Dense, Hybrid;
- group key: `dataset:sample_id`.

All sibling traces from a question must remain in one group partition. This cohort can never again be called fresh V3 confirmation.

## Outcomes

Define two binary targets from the already accepted normalized-EM transitions:

- recovery target `R=1` iff `a0_em=0` and `a1_em=1`; otherwise 0;
- damage target `D=1` iff `a0_em=1` and `a1_em=0`; otherwise 0.

The two labels are fitted separately. No combined scalar target is allowed.

## Fixed primary feature block

Use the exact trace-only Head-T information family. Numeric inputs:

1. `state_symmetric_hgb`
2. `state_symmetric_logistic`
3. `no_cross_state`
4. `no_B`
5. `no_evidence_change`
6. `no_answer_form`
7. `ordinary_compact_logistic`
8. `B_rule`
9. `higher_own_likelihood`
10. `likelihood_margin`
11. `gbv_margin`

Also include:

- one-hot retriever identity: BM25 / Dense / Hybrid;
- one explicit missingness flag per numeric input.

Do not use dataset identity, sample ID, question/evidence/raw answer text, sibling features, V2 action membership, GbV action membership, correctness, Gold support, or transition labels other than the head's own training target.

IDs are group/join/tie-break keys only.

## Fixed head family and preprocessing

Both heads use the same fixed model family:

- L2 logistic regression;
- `C=1.0`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=5000`;
- no hyperparameter search.

For each fit partition only:

1. create numeric missingness flags;
2. impute missing numeric values with the fit-partition median;
3. standardize continuous numeric features using fit-partition mean/std;
4. leave binary indicators unstandardized.

Fit one model to recovery and one independent model to damage.

### Separate calibration

On a calibration partition disjoint from fitting, fit one-dimensional Platt calibration to each head's base logit using:

- logistic regression;
- `C=1e6`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=2000`.

Use calibrated `pR` and `pD` for constrained selection. Require each fit and calibration partition to contain both classes for both targets. Otherwise hard stop; do not redraw or rebalance.

## End-to-end nested grouped design

Use five repetitions with exact seeds:

`20260917, 20260918, 20260919, 20260920, 20260921`.

For each seed assign question groups to five outer folds by:

`sha256("v3-dhc-outer-v1|<seed>|<dataset>|<sample_id>") mod 5`.

Within each outer-training pool assign groups to four inner folds by:

`sha256("v3-dhc-inner-v1|<seed>|<outer_fold>|<dataset>|<sample_id>") mod 4`.

For each inner validation fold, split the remaining inner-training groups into fit/calibration by:

`sha256("v3-dhc-inner-cal-v1|<seed>|<outer_fold>|<inner_fold>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

After choosing the risk budget for an outer fold, split the full outer-training groups for the final outer models by:

`sha256("v3-dhc-outer-cal-v1|<seed>|<outer_fold>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

The untouched outer-test groups may not influence fitting, calibration, inner risk-budget selection, or optimization inputs.

## Fixed action cap

For every evaluation partition:

`K = round(0.05 * N_all_trace_rows_in_partition)`.

The 5% action rate is fixed. No action-rate sweep is allowed.

## Fixed predicted-damage budget grid

Exactly five candidates are allowed:

`rho in {INF, 0.05, 0.03, 0.02, 0.01}`.

`INF` is the unconstrained recovery-head fallback.

For finite `rho`, the expected-damage budget is:

`B = rho * K`.

No other risk budget, threshold, veto fraction, lambda, alpha or feature subset may be tried.

## Constrained selector

On an evaluation partition with calibrated probabilities, choose binary action indicators `x_i` only for eligible/scorable rows by solving:

maximize

`sum_i pR_i * x_i`

subject to

- `sum_i x_i <= K`;
- for finite `rho`: `sum_i pD_i * x_i <= rho * K`;
- `x_i in {0,1}`.

Use `scipy.optimize.milp` / HiGHS only. If the optimizer does not return an optimal solution, hard stop; do not substitute a greedy heuristic.

### Deterministic tie resolution

Use a two-pass optimization:

1. solve the primary recovery objective;
2. record optimum `U*`;
3. solve again with all original constraints plus `sum_i pR_i*x_i >= U* - 1e-10`, minimizing stable key rank based on `(dataset,retriever,sample_id)`.

Record solver status, objective, selected count, predicted damage sum and constraint slack. The independent validator must reproduce feasibility and selected membership without importing the main executor.

## Inner risk-budget selection

For each candidate `rho`, run the complete head fitting/calibration/selection pipeline independently on each of the four inner validation folds and pool the held-out inner results.

Let `INF` be the structural fallback.

A finite candidate is eligible for selection only if:

1. pooled selected action count is at least 90% of the pooled inner action cap;
2. pooled realized damage count is no greater than the pooled `INF` fallback damage count.

`INF` is always eligible.

Choose among eligible candidates lexicographically:

1. maximize pooled net correction;
2. tie -> lower realized damage;
3. tie -> higher recovery;
4. tie -> higher action count;
5. tie -> weaker constraint, ordered `INF > 0.05 > 0.03 > 0.02 > 0.01`.

This rule deliberately prefers the unconstrained fallback when performance is tied, so a nontrivial constraint must earn its complexity.

The chosen `rho` is applied once to the outer-test fold using heads fit/calibrated only from the outer-training groups.

## Outer comparators

For each outer-test fold compute:

1. **DHC-V3 candidate** — constrained dual-head selector at the inner-chosen `rho`;
2. **Recovery-only head** — top calibrated `pR` at exactly the DHC selected action count;
3. **Raw HGB** — top frozen HGB score at exactly the DHC selected action count;
4. **GbV** — top frozen `gbv_margin` at exactly the DHC selected action count;
5. cap-based raw-HGB/GbV results at `K` as transparent secondary context when DHC underfills;
6. frozen V2 and rejected RG-HGB may be reported as secondary historical development references only, never used to choose `rho`.

Stable ranking ties use `(dataset,retriever,sample_id)`.

## Metrics

For every fold and repetition report:

- action count and retention vs K;
- recovery, damage, neutral, net;
- delta EM pp and delta F1 pp versus Keep;
- DHC minus recovery-only, raw-HGB and GbV EM/F1;
- predicted damage sum and mean selected pD;
- dataset, retriever and nine dataset×retriever breakdowns;
- selected `rho`.

Do not pool the five repetitions as independent samples.

## Mandatory leave-one-dataset-out transport diagnostic

After the primary repeated-development outputs and decision file are frozen, run exactly three secondary transport evaluations:

- train/select/calibrate on HotpotQA + 2Wiki, test MuSiQue;
- train/select/calibrate on HotpotQA + MuSiQue, test 2Wiki;
- train/select/calibrate on 2Wiki + MuSiQue, test HotpotQA.

For each held-out dataset, choose `rho` using only the two training datasets under the same grid and intrinsic inner rule, then fit/calibrate both heads only on those two datasets and evaluate once on the held-out dataset.

Report DHC minus same-action-count GbV and HGB. No dataset-specific parameter search is allowed.

## Predeclared development decision

For each repetition define `success_vs_X` as:

`DHC net > X net AND DHC damage <= X damage`

using the same actual DHC action count.

Mark `SUPPORTED_FOR_V3_FINALIZATION` only if all conditions hold:

1. success versus recovery-only head in at least 4/5 repetitions;
2. success versus raw HGB in at least 4/5 repetitions;
3. success versus GbV in at least 4/5 repetitions;
4. median repetition-level DHC-minus-GbV EM >= `+0.30` pp;
5. median repetition-level DHC-minus-GbV F1 > `0.00` pp;
6. a finite `rho` is selected in at least 15/25 outer folds;
7. median outer-test action retention is at least 90% of K;
8. in the three leave-one-dataset-out diagnostics, at least 2/3 DHC-minus-GbV EM point estimates are nonnegative and none is below `-0.20` pp.

Mark `REJECT_DUAL_HEAD_ARCHITECTURE` if any of the following holds:

- success versus raw HGB is fewer than 3/5 repetitions;
- success versus GbV is fewer than 3/5 repetitions;
- median repetition-level DHC-minus-GbV EM <= 0.

Otherwise mark `INCONCLUSIVE_DUAL_HEAD_STAGE`.

Support, reject and inconclusive are mutually interpretable under these explicit rules. These are development engineering criteria, not confirmatory hypothesis tests.

## Prohibitions

Do not:

- add sibling features;
- change model family or class weights;
- search C, solver, calibration method or preprocessing;
- expand the rho grid;
- search action rate;
- use dataset ID as predictor;
- use current outer-test outcomes in fitting/calibration/selection;
- regenerate retrieval, answers, likelihoods or scores;
- select future confirmatory IDs;
- describe this cohort as V3 confirmation.

## Required outputs

Write only under:

`outputs/daa_v3_development/dual_head_constrained_v1/`

At minimum:

- `INPUT_VERIFICATION.json`
- `MODEL_FEATURE_SCHEMA.json`
- `SPLIT_MANIFEST.json`
- `MODEL_FIT_MANIFEST.json`
- `RISK_BUDGET_SPEC.json`
- `INNER_SELECTIONS.json`
- `OUTER_PREDICTIONS_PRIVATE.jsonl`
- `OUTER_ACTIONS_PRIVATE.jsonl`
- `OUTER_RESULTS.json`
- `DATASET_RETRIEVER_BREAKDOWN.json`
- `LODO_TRANSPORT.json`
- `DEVELOPMENT_DECISION.json`
- `INDEPENDENT_VALIDATION.json`
- `DUAL_HEAD_DEVELOPMENT_SEAL.json`
- `SHA256_MANIFEST.json`

Independent validation must independently recompute parent hashes, group splits, feature allowlists, fit/cal/test isolation, probability reconstruction from saved coefficients, candidate feasibility, every inner `rho` choice, optimizer constraints, outer memberships, metrics, LODO results and the final decision rule without importing the main executor as its oracle.

## Hard stop

After validation, seal and manifest, HARD STOP. Do not fit a final full-development V3 ensemble and do not select a new confirmatory cohort. A separate finalization task is required if and only if this stage is supported.
