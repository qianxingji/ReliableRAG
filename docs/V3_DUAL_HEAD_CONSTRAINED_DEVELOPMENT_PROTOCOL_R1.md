# DAA-V3 dual-head risk-constrained development protocol R1

## Status and precedence

Development-only protocol. This R1 supersedes `docs/V3_DUAL_HEAD_CONSTRAINED_DEVELOPMENT_PROTOCOL.md` for future execution of the blocked dual-head stage and incorporates `docs/V3_DUAL_HEAD_PROTOCOL_CLARIFICATION_001.md`.

The original protocol, task, readiness receipts, and `PROTOCOL_CLARIFICATION_REQUIRED.md` remain immutable evidence of the pre-fit pause. R1 is written before any dual-head scientific fit, calibration, MILP solve, rho selection, or policy evaluation.

This protocol tests one structural hypothesis only:

> Separately estimated recovery and damage probabilities, combined through an explicit predicted-damage budget, can improve repair selection beyond raw HGB, the rejected simple RG-HGB gate, and GbV.

This is V3 development evidence only. It does not authorize a fresh confirmatory cohort.

## Parent evidence and mandatory preflight

Before any scientific fit, require the blocked readiness evidence to show zero scientific execution and verify all parent namespaces byte-for-byte.

Known anchors include:

- V3 failure-audit seal: `ff2c177bd71e29f1170b4093594194d40d2bc0d89f2eaf1273802c8c07840882`;
- V3 risk-head comparison seal: `1d1c01f1c483db16cdeefb9f846dfb36b4058597a534c34a930a11c60eeea034`;
- RG-HGB amendment execution record: `a91bc244db608e0e78f0c46f91a2f5fb326d3827a2d88bfeff134bfed0bd0978`;
- RG-HGB author report: `bad7f809566f13aa0e0eeb1fb0f3873e707fc2dee9d4f3077a72accbe4a7e6f3`;
- RG-HGB independent validation: `a7345245a1d919d1f86a8067377699974c919a40181d4228f7b0cff89ce46bde`;
- opened numeric outcomes: `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`;
- V2 base-score ledger: `d3842c514224354206846edb7e96b7296765d67050b131b552f469d0c64fa609`;
- GbV score ledger: `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`;
- canonical branches: `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`.

Also locate the sealed local RG-HGB `RISK_GATED_POLICY_SEAL.json` and recursive manifest, require status PASS and decision `REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD`, and verify all three parent manifests in full.

Preserve these blocked dual-head pre-fit artifacts byte-for-byte:

- `outputs/daa_v3_development/dual_head_constrained_v1/INPUT_VERIFICATION.json`;
- `outputs/daa_v3_development/dual_head_constrained_v1/PROTOCOL_READINESS_VALIDATION.json` if materialized there;
- `outputs/daa_v3_development/dual_head_constrained_v1/PROTOCOL_CLARIFICATION_REQUIRED.md`.

The execution branch must be a strict descendant of `e263760591c950bc5f1e73a102edce98559cbc93` and include this R1 protocol plus clarification 001.

## Output namespace

Continue only under:

`outputs/daa_v3_development/dual_head_constrained_v1/`

Do not delete or overwrite the blocked pre-fit receipts. New R1 receipts use distinct filenames where needed.

## Development population

Use only the already opened V3-development cohort:

- 4,500 question groups;
- 13,500 retriever traces;
- 3,202 frozen eligible/scorable traces;
- retrievers BM25, Dense, Hybrid;
- group key `dataset:sample_id`.

Sibling traces from the same question must remain in the same partition. This cohort can never again be described as unseen V3 confirmation.

## Targets

Fit two separate binary targets from normalized EM transitions:

- recovery `R=1` iff `a0_em=0` and `a1_em=1`, else 0;
- damage `D=1` iff `a0_em=1` and `a1_em=0`, else 0.

Do not construct a combined utility label.

## Fixed primary feature block

Numeric inputs exactly:

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

Also include one-hot retriever identity and one explicit missingness flag per numeric input.

Prohibited predictors: dataset identity, sample ID, question/evidence/raw-answer text, sibling features, V2/GbV action membership, correctness, Gold support, and any outcome-derived feature other than the current head's training target. IDs are group/join/tie-break keys only.

## Fixed head family and preprocessing

Recovery and Damage heads use the identical fixed model family:

- L2 logistic regression;
- `C=1.0`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=5000`;
- no hyperparameter search.

For each fit partition only:

1. create missingness flags;
2. median-impute numeric missing values from that fit partition;
3. standardize continuous numeric fields using fit-partition mean/std;
4. leave binary indicators unstandardized.

### Separate Platt calibration

On a calibration partition disjoint from fitting, calibrate each head's base logit with one-dimensional logistic regression:

- `C=1e6`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=2000`.

Use calibrated `pR` and `pD` in the selector. Every required fit and calibration partition must contain both classes for both targets. Otherwise hard stop; no redraw, rebalance, pooling, resampling, or class-weight change.

## Primary end-to-end nested grouped design

Use exactly five repetition seeds:

`20260917, 20260918, 20260919, 20260920, 20260921`.

For each seed assign question groups to five outer folds:

`sha256("v3-dhc-outer-v1|<seed>|<dataset>|<sample_id>") mod 5`.

Within each outer-training pool assign groups to four inner folds:

`sha256("v3-dhc-inner-v1|<seed>|<outer_fold>|<dataset>|<sample_id>") mod 4`.

For inner validation fold `j`, split its remaining inner-training groups into fit/calibration by:

`sha256("v3-dhc-inner-cal-v1|<seed>|<outer_fold>|<j>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

After choosing rho for an outer fold, split all outer-training groups for final outer models by:

`sha256("v3-dhc-outer-cal-v1|<seed>|<outer_fold>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

Outer-test groups may not influence head fitting, calibration, rho selection, optimization inputs, or action membership.

## Fixed action cap

For every evaluation partition:

`K = round(0.05 * N_all_trace_rows_in_partition)`.

The action rate is fixed at 5%. No action-rate search is allowed.

## Fixed predicted-damage budget grid

Exactly:

`rho in {INF, 0.05, 0.03, 0.02, 0.01}`.

`INF` is the unconstrained recovery-head fallback. For finite rho:

`B = rho * K`.

No other risk budget, threshold, veto fraction, lambda, alpha, or feature subset may be tried.

## Constrained selector

For eligible/scorable rows choose binary `x_i` to maximize:

`sum_i pR_i * x_i`

subject to:

- `sum_i x_i <= K`;
- for finite rho, `sum_i pD_i * x_i <= rho*K`;
- `x_i in {0,1}`.

Use only `scipy.optimize.milp` / HiGHS. If an optimal solution is not returned, hard stop; no greedy or heuristic fallback.

### Deterministic two-pass tie resolution

1. solve the primary recovery objective;
2. record optimum `U*`;
3. solve again under all original constraints plus `sum_i pR_i*x_i >= U* - 1e-10`, minimizing stable key rank from `(dataset,retriever,sample_id)`.

Record solver status, objective, selected count, predicted damage sum, budget and slack.

## Inner rho selection

For every rho candidate run the complete fit/calibrate/select pipeline on all four inner validation folds and pool only held-out inner results.

A finite rho is eligible only if:

1. pooled selected action count >= 90% of pooled inner cap;
2. pooled realized damage <= pooled `INF` damage.

`INF` is always eligible.

Among eligible candidates choose lexicographically:

1. maximize pooled net;
2. tie -> lower damage;
3. tie -> higher recovery;
4. tie -> higher action count;
5. tie -> weaker constraint in order `INF > 0.05 > 0.03 > 0.02 > 0.01`.

Apply the selected rho once to the untouched outer-test fold using newly fit/calibrated outer-training-only heads.

## Outer comparators

At exactly the DHC actual action count compute:

1. Recovery-only head: top calibrated `pR`;
2. raw HGB: top frozen HGB score;
3. GbV: top frozen `gbv_margin`.

Cap-based HGB/GbV may be reported as secondary context if DHC underfills. Frozen V2 and rejected RG-HGB are historical secondary development context only and cannot choose rho.

Stable comparator ties use `(dataset,retriever,sample_id)`.

## Primary metrics

For every fold and repetition report:

- action count and retention vs K;
- recovery, damage, neutral, net;
- delta EM pp and delta F1 pp versus Keep;
- DHC minus Recovery-only, HGB and GbV EM/F1;
- selected rho;
- selected predicted-damage sum/mean/slack;
- dataset, retriever, and all nine dataset×retriever cells without subgroup reranking.

Do not treat five repetitions as independent confirmatory experiments.

## Immutable pre-LODO primary receipt

After all five repeated-development repetitions are complete, and before any LODO model fit or held-out transport evaluation, write:

- `PRIMARY_DECISION_PRE_LODO.json`
- `PRIMARY_DECISION_PRE_LODO_SEAL.json`

The receipt must hash-bind the repeated-development outputs and record:

- success counts versus Recovery-only, raw HGB, and GbV;
- median repetition-level DHC-minus-GbV EM and F1;
- finite-rho selections out of 25 outer folds;
- median outer-test action retention;
- support conditions 1–7;
- the three rejection-trigger booleans;
- exactly one pre-LODO status.

Permitted status values:

- `PRIMARY_REJECT_TRIGGERED` if any frozen rejection trigger is true;
- `PRIMARY_SUPPORT_1_TO_7_MET_PENDING_LODO` if no rejection trigger is true and support conditions 1–7 all pass;
- `PRIMARY_INCONCLUSIVE_PENDING_LODO` otherwise.

This receipt is immutable after creation. LODO is then executed regardless of this pre-LODO status unless a technical hard stop occurs.

## Mandatory LODO transport — exact deterministic recipe

LODO uses a separate split namespace; it does not use a primary `outer_fold` token.

Use exactly one LODO seed:

`20260922`.

Canonical held-out tokens exactly:

- `musique`
- `2wikimultihopqa`
- `hotpotqa`

For held-out dataset `H`, the other two datasets are the complete training pool.

### LODO inner folds

Assign each training-pool question group to four inner folds by:

`sha256("v3-dhc-lodo-inner-v1|20260922|<H>|<dataset>|<sample_id>") mod 4`.

For inner validation fold `j`, fit/cal split the remaining three folds by:

`sha256("v3-dhc-lodo-inner-cal-v1|20260922|<H>|<j>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

Require both classes for both targets in every fit/calibration partition or hard stop.

For each rho run the complete inner pipeline, pool the four validation results, and choose rho using the exact same finite-candidate eligibility and lexicographic rule as the primary stage. No held-out-dataset label may influence this choice.

### LODO final heads

After rho selection, split all two-dataset training groups by:

`sha256("v3-dhc-lodo-final-cal-v1|20260922|<H>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

Fit/calibrate both heads only on those two training datasets. For the held-out dataset set:

`K = round(0.05 * N_all_trace_rows_in_heldout_dataset)`.

Apply the selected rho once through the same two-pass MILP selector. Compare against raw HGB and GbV at exactly the DHC actual action count. The held-out token is used only for split-domain separation and reporting, never as a learned feature.

Run exactly these three transports:

- HotpotQA + 2Wiki -> MuSiQue;
- HotpotQA + MuSiQue -> 2Wiki;
- 2Wiki + MuSiQue -> HotpotQA.

Write `LODO_TRANSPORT.json` only after the immutable pre-LODO receipt exists.

## Final development decision

For each repetition define success against comparator X as:

`DHC net > X net AND DHC damage <= X damage`

at the same DHC action count.

Support conditions are:

1. success vs Recovery-only >= 4/5;
2. success vs raw HGB >= 4/5;
3. success vs GbV >= 4/5;
4. median repetition-level DHC-minus-GbV EM >= +0.30 pp;
5. median repetition-level DHC-minus-GbV F1 > 0.00 pp;
6. finite rho selected in >= 15/25 outer folds;
7. median outer-test action retention >= 90% of K;
8. among three LODO DHC-minus-GbV EM point estimates, at least 2/3 are nonnegative and none is below -0.20 pp.

Frozen rejection triggers are:

- success vs raw HGB < 3/5; OR
- success vs GbV < 3/5; OR
- median repetition-level DHC-minus-GbV EM <= 0.

Final `DEVELOPMENT_DECISION.json` is determined in this order:

1. if any rejection trigger is true -> `REJECT_DUAL_HEAD_ARCHITECTURE`, regardless of LODO;
2. else if all support conditions 1–8 are true -> `SUPPORTED_FOR_V3_FINALIZATION`;
3. else -> `INCONCLUSIVE_DUAL_HEAD_STAGE`.

LODO cannot alter primary metrics, conditions 1–7, selected outer rho values, or rejection triggers. It cannot rescue a primary rejection.

These are development engineering criteria, not confirmatory hypothesis tests.

## Independent validation

A second implementation must independently recompute or verify:

- parent hashes and recursive manifests;
- exact feature allowlist/values;
- all primary and LODO group splits;
- class-presence guards;
- fit-only preprocessing;
- saved-model predictions from coefficients/calibrators;
- every inner candidate and rho choice;
- MILP feasibility and selected memberships;
- all primary metrics and subgroup arithmetic;
- the immutable pre-LODO receipt and its hash;
- all three LODO results;
- all eight support booleans, rejection booleans, and final decision.

It may not import the main experiment executor as its oracle.

## Required outputs

At minimum add/preserve:

- existing blocked `INPUT_VERIFICATION.json`;
- `INPUT_VERIFICATION_R1.json`;
- `MODEL_FEATURE_SCHEMA.json`;
- `SPLIT_MANIFEST.json`;
- `MODEL_FIT_MANIFEST.json`;
- `RISK_BUDGET_SPEC.json`;
- `INNER_SELECTIONS.json`;
- `OUTER_PREDICTIONS_PRIVATE.jsonl`;
- `OUTER_ACTIONS_PRIVATE.jsonl`;
- `OUTER_RESULTS.json`;
- `DATASET_RETRIEVER_BREAKDOWN.json`;
- `PRIMARY_DECISION_PRE_LODO.json`;
- `PRIMARY_DECISION_PRE_LODO_SEAL.json`;
- `LODO_SPLIT_MANIFEST.json`;
- `LODO_TRANSPORT.json`;
- `DEVELOPMENT_DECISION.json`;
- `AUTHOR_REPORT.md`;
- `INDEPENDENT_VALIDATION.json`;
- `DUAL_HEAD_DEVELOPMENT_SEAL.json`;
- `SHA256_MANIFEST.json`.

## Prohibitions

Do not add sibling features, dataset ID, new rho values, a new action rate, alternate model families, class weights, calibration methods, greedy optimization, post-hoc thresholds, retrieval/generation/repair/likelihood calls, final full-development V3 fitting, or confirmatory-ID selection.

## Hard stop

After independent validation, development seal, and manifest, HARD STOP. A separate finalization protocol is allowed only if the final mechanical decision is `SUPPORTED_FOR_V3_FINALIZATION`.