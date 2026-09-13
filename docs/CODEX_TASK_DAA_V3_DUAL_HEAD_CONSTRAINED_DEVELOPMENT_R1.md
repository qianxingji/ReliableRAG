# Codex task — DAA-V3 dual-head constrained development R1

## Scope

Work against the full private project at `E:\paper\ReliableRAG` on branch:

`v3-risk-constrained-arbitration`

This R1 task supersedes `docs/CODEX_TASK_DAA_V3_DUAL_HEAD_CONSTRAINED_DEVELOPMENT.md` for the blocked dual-head attempt. Preserve the original task/protocol and all blocked readiness receipts byte-for-byte.

Read first:

- `AGENTS.md`
- `docs/V3_DEVELOPMENT_STATUS.md`
- `docs/V3_ARCHITECTURE_REVIEW_AFTER_RG_HGB.md`
- `docs/V3_DUAL_HEAD_PROTOCOL_CLARIFICATION_001.md`
- `docs/V3_DUAL_HEAD_CONSTRAINED_DEVELOPMENT_PROTOCOL_R1.md`
- the original blocked dual-head protocol/task for provenance only;
- sealed local namespaces `failure_audit_v1`, `risk_head_comparison_v1`, and `risk_gated_policy_v1`.

This is a development-only end-to-end nested experiment. Do not expand the model family, feature set, rho grid, action rate, split rules, or comparator hierarchy.

## Preserve the blocked pre-fit attempt

Do not delete, replace, rename, or edit:

- `outputs/daa_v3_development/dual_head_constrained_v1/INPUT_VERIFICATION.json`;
- `outputs/daa_v3_development/dual_head_constrained_v1/PROTOCOL_READINESS_VALIDATION.json` if present;
- `outputs/daa_v3_development/dual_head_constrained_v1/PROTOCOL_CLARIFICATION_REQUIRED.md`;
- the pre-fit verifier script and any existing readiness logs.

Before scientific fitting, verify those receipts still show zero fit/calibration/MILP/rho-selection/policy-evaluation calls.

## R1 preflight

1. Verify local/remote branch contains `docs/V3_DUAL_HEAD_PROTOCOL_CLARIFICATION_001.md` and `docs/V3_DUAL_HEAD_CONSTRAINED_DEVELOPMENT_PROTOCOL_R1.md` and is a strict descendant of `e263760591c950bc5f1e73a102edce98559cbc93`.
2. Reverify every parent anchor and full recursive parent manifest required by R1.
3. Require RG-HGB decision `REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD`.
4. Confirm no new confirmatory cohort, retrieval, generation, repair, likelihood extraction, feature search, dual-head fit, MILP policy evaluation, or rho selection has occurred since the blocked receipt.
5. Write `INPUT_VERIFICATION_R1.json`.
6. Freeze all R1 executable/config files and write the exact feature/risk-budget specs before the first scientific fit.

Any mismatch is a hard stop.

## Population and targets

Use only the already opened V3-development cohort:

- 4,500 question groups;
- 13,500 total retriever traces;
- 3,202 frozen eligible/scorable traces;
- group key `dataset:sample_id`.

Targets:

- Recovery `R=1` iff `a0_em=0,a1_em=1`;
- Damage `D=1` iff `a0_em=1,a1_em=0`.

No combined target is allowed.

## Exact features and models

Use exactly the R1 trace-only feature block: 11 numeric scores, retriever one-hot, and numeric missingness flags. No dataset identity or sibling block.

Recovery and Damage heads both use:

- L2 logistic regression;
- `C=1.0`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=5000`.

Use fit-only median imputation and standardization. Use separate disjoint Platt calibration for each head with `C=1e6`, `lbfgs`, `class_weight=None`, `max_iter=2000`.

Every fit/calibration partition must contain both classes for both heads; otherwise hard stop with no redraw or rebalance.

Record every scientific base-head and calibrator fit in `MODEL_FIT_MANIFEST.json`.

## Primary nested repeated development

Use exactly seeds:

`20260917, 20260918, 20260919, 20260920, 20260921`.

Use the exact R1 SHA-256 outer, inner, inner-calibration, and outer-final-calibration formulas. Question siblings never cross partitions.

For each outer fold:

1. run all four inner validation folds;
2. for every frozen rho candidate fit/calibrate both heads from inner-training-only groups and evaluate the constrained selector on inner validation;
3. pool inner held-out results and choose rho by the frozen rule;
4. fit/calibrate new final outer Recovery/Damage heads on outer-training-only groups;
5. apply chosen rho once to outer-test;
6. compute same-actual-action Recovery-only, raw-HGB, and GbV comparators;
7. save all action memberships and solver receipts.

No outer-test label may influence any fitting, calibration, rho selection, predicted probabilities, MILP coefficients, or action membership.

## Fixed risk budgets and optimizer

Only:

`rho in {INF, 0.05, 0.03, 0.02, 0.01}`.

For every evaluation partition:

`K = round(0.05 * N_all_trace_rows_in_partition)`.

Finite risk budget:

`sum pD_i*x_i <= rho*K`.

Maximize `sum pR_i*x_i` subject to action/risk constraints using only `scipy.optimize.milp` / HiGHS. Use the exact R1 two-pass deterministic tie resolution. No heuristic fallback.

## Primary output freeze before LODO

After all five repetitions and all primary subgroup summaries are complete, but before any LODO fit/evaluation, write and seal:

- `PRIMARY_DECISION_PRE_LODO.json`
- `PRIMARY_DECISION_PRE_LODO_SEAL.json`

The pre-LODO receipt must contain and freeze:

- success counts vs Recovery-only, raw HGB, and GbV;
- median DHC-minus-GbV EM/F1;
- finite-rho selection count;
- median action retention;
- support conditions 1–7;
- all three rejection-trigger booleans;
- exactly one of:
  - `PRIMARY_REJECT_TRIGGERED`
  - `PRIMARY_SUPPORT_1_TO_7_MET_PENDING_LODO`
  - `PRIMARY_INCONCLUSIVE_PENDING_LODO`.

Do not create the final `DEVELOPMENT_DECISION.json` yet. Never overwrite the pre-LODO receipt or seal.

## Exact LODO transport

Only after the pre-LODO seal exists, run exactly three transport experiments using R1's standalone LODO namespace.

LODO seed exactly:

`20260922`.

Held-out tokens exactly:

- `musique`
- `2wikimultihopqa`
- `hotpotqa`.

### Training-pool inner split

For held-out `H`, training groups are the other two datasets.

Inner fold:

`sha256("v3-dhc-lodo-inner-v1|20260922|<H>|<dataset>|<sample_id>") mod 4`.

For inner validation fold `j`, fit/cal split the other three inner folds by:

`sha256("v3-dhc-lodo-inner-cal-v1|20260922|<H>|<j>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

Use all five rho candidates and the exact same eligibility/lexicographic rho-selection rule as primary development.

### Final two-dataset model

After rho is selected, split the complete two-dataset training pool by:

`sha256("v3-dhc-lodo-final-cal-v1|20260922|<H>|<dataset>|<sample_id>") mod 5`.

- remainder 0 -> calibration;
- remainders 1,2,3,4 -> fit.

Fit/calibrate both heads only on those two datasets and apply once to held-out `H` with:

`K = round(0.05 * N_all_trace_rows_in_heldout_dataset)`.

No held-out label may influence rho selection, fitting, calibration, MILP inputs, or action membership.

Compare DHC to raw HGB and GbV at exactly DHC's actual action count. Save `LODO_SPLIT_MANIFEST.json` and `LODO_TRANSPORT.json`.

## Final mechanical decision

After all three LODO results are saved, create the separate final `DEVELOPMENT_DECISION.json`.

Support conditions:

1. success vs Recovery-only >=4/5;
2. success vs raw HGB >=4/5;
3. success vs GbV >=4/5;
4. median DHC-minus-GbV EM >= +0.30 pp;
5. median DHC-minus-GbV F1 > 0;
6. finite rho selected >=15/25 outer folds;
7. median action retention >=90%;
8. LODO: at least 2/3 DHC-minus-GbV EM >=0 and none < -0.20 pp.

Frozen rejection triggers:

- success vs raw HGB <3/5; OR
- success vs GbV <3/5; OR
- median DHC-minus-GbV EM <=0.

Decision order:

1. any rejection trigger -> `REJECT_DUAL_HEAD_ARCHITECTURE` regardless of LODO;
2. else all eight support conditions -> `SUPPORTED_FOR_V3_FINALIZATION`;
3. else -> `INCONCLUSIVE_DUAL_HEAD_STAGE`.

LODO must not alter any primary result, condition 1–7, outer rho, or rejection trigger.

## Independent validation

A separate implementation must independently verify/recompute:

- all parent and R1 hashes;
- blocked receipts remain unchanged;
- exact features and partitions;
- class-presence guards;
- saved coefficients/calibrators and predictions;
- all primary inner rho results and chosen rho values;
- all MILP feasibility/memberships;
- all repeated-development metrics and subgroups;
- `PRIMARY_DECISION_PRE_LODO.json` and seal integrity;
- every LODO split, fit/cal partition, rho choice, solver result, and transport metric;
- all eight support conditions, rejection triggers, and final decision.

Do not import the main experiment executor as the validator's oracle.

## Required outputs

At minimum preserve/create:

- blocked pre-fit receipts;
- `INPUT_VERIFICATION_R1.json`
- `MODEL_FEATURE_SCHEMA.json`
- `SPLIT_MANIFEST.json`
- `MODEL_FIT_MANIFEST.json`
- `RISK_BUDGET_SPEC.json`
- `INNER_SELECTIONS.json`
- `OUTER_PREDICTIONS_PRIVATE.jsonl`
- `OUTER_ACTIONS_PRIVATE.jsonl`
- `OUTER_RESULTS.json`
- `DATASET_RETRIEVER_BREAKDOWN.json`
- `PRIMARY_DECISION_PRE_LODO.json`
- `PRIMARY_DECISION_PRE_LODO_SEAL.json`
- `LODO_SPLIT_MANIFEST.json`
- `LODO_TRANSPORT.json`
- `DEVELOPMENT_DECISION.json`
- `AUTHOR_REPORT.md`
- `INDEPENDENT_VALIDATION.json`
- `DUAL_HEAD_DEVELOPMENT_SEAL.json`
- `SHA256_MANIFEST.json`.

## Hard stop

After independent validation, final development seal, and recursive manifest, HARD STOP. Do not expand rho, refit a full-development deployable V3 model, select confirmatory IDs, run new retrieval/generation, or make a V3 confirmatory claim.

Only `SUPPORTED_FOR_V3_FINALIZATION` may authorize a later, separately reviewed finalization protocol.