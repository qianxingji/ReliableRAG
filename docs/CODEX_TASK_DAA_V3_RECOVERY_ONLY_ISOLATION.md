# Codex task — DAA-V3 recovery-only arbitration isolation

## Scope

Work against the full private repository at `E:\paper\ReliableRAG` on branch:

`v3-risk-constrained-arbitration`

Read first:

- `AGENTS.md`
- `docs/V3_DEVELOPMENT_STATUS.md`
- `docs/V3_ARCHITECTURE_REVIEW_AFTER_DHC.md`
- `docs/V3_RECOVERY_ONLY_ISOLATION_PROTOCOL.md`
- sealed local DHC namespace `outputs/daa_v3_development/dual_head_constrained_v1/`

This is a development-only parsimony/baseline-dependence experiment. Test exactly two recovery-only variants: ROA-FULL and ROA-NOGBV.

Do not select a fresh cohort, do not fit a Damage head, do not use MILP, and do not add any feature/model/action-rate search.

## Mandatory preflight

Before any scientific fit:

1. verify local/remote branch is a descendant of the R1 dual-head protocol commits and contains the new architecture review and recovery-only protocol;
2. verify DHC `AUTHOR_REPORT.md` SHA-256 `184cb2491837ac6fac7f2373af840ab7c907f6ef402083e18e0ba98e4f84f015`;
3. verify DHC `INDEPENDENT_VALIDATION.json` SHA-256 `16c3aa52dd9de337afe57d388fd8bc8da6d086fac1f645f7a1f85a41c9039d8b`;
4. verify DHC `DUAL_HEAD_DEVELOPMENT_SEAL.json` SHA-256 `59f6da26ba30ca751ccea010de1d67728fee4dd53a143d1b00ff169ae231d266`;
5. verify DHC decision exactly `INCONCLUSIVE_DUAL_HEAD_STAGE` and hard-stop status;
6. verify all earlier V3 parent manifests byte-for-byte;
7. confirm no new confirmatory IDs, retrieval, generation, repair, likelihood or base-score extraction has started;
8. write `INPUT_VERIFICATION.json`, feature schema, split receipt, and executable/config freeze before the first scientific fit.

Any mismatch is a hard stop.

## Population

Use only the already opened development cohort:

- 4,500 question groups;
- 13,500 retriever traces;
- 3,202 frozen eligible/scorable traces;
- group key `dataset:sample_id`.

## Targets and variants

Target for both variants:

`R=1` iff `a0_em=0 and a1_em=1`, else 0.

### ROA-FULL

Use exactly the DHC recovery-head feature family:

- 11 numeric fields: `state_symmetric_hgb`, `state_symmetric_logistic`, `no_cross_state`, `no_B`, `no_evidence_change`, `no_answer_form`, `ordinary_compact_logistic`, `B_rule`, `higher_own_likelihood`, `likelihood_margin`, `gbv_margin`;
- one missingness flag per numeric field;
- retriever one-hot BM25/Dense/Hybrid.

### ROA-NOGBV

Same as ROA-FULL except remove `gbv_margin` and its missingness flag.

No third variant is allowed.

## Model and preprocessing

For each variant use:

- L2 logistic regression;
- `C=1.0`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=5000`.

Fit-only preprocessing:

- create missing flags;
- median impute from fit groups only;
- standardize continuous features from fit groups only;
- leave binary indicators unstandardized.

Use separate disjoint Platt calibration exactly as in the DHC recovery-head pipeline:

- `C=1e6`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=2000`.

Require both classes in fit and calibration. Do not redraw or rebalance.

Record all model/calibration calls.

## Primary repeated development

Reuse exactly DHC repetition seeds:

- 20260917
- 20260918
- 20260919
- 20260920
- 20260921

Reuse the exact DHC outer-fold and outer-final fit/calibration hash formulas. Do not invent new split namespaces.

For each outer fold and each ROA variant:

1. fit/calibrate using outer-training groups only;
2. score untouched outer-test groups;
3. set `K=round(0.05*N_all_trace_rows_in_outer_test)`;
4. select top calibrated recovery probability among eligible/scorable rows up to K, stable tie-break `(dataset,retriever,sample_id)`;
5. compute raw HGB, GbV, and optional frozen V2 rankings at exactly K actions;
6. save predictions, action memberships and metrics.

No outer-test label may influence fitting, calibration or ranking.

## Mandatory LODO

Reuse exact DHC LODO seed and final fit/calibration split namespace:

`20260922`.

No rho selection or inner policy selection is needed.

Run exactly:

- HotpotQA + 2Wiki -> MuSiQue;
- HotpotQA + MuSiQue -> 2Wiki;
- 2Wiki + MuSiQue -> HotpotQA.

Fit/calibrate each ROA variant only on the two training datasets and evaluate once on the held-out dataset at fixed 5% action cap. Compare with same-action-count HGB and GbV.

## Mechanical decisions

Apply `docs/V3_RECOVERY_ONLY_ISOLATION_PROTOCOL.md` literally.

Architecture outcome must be exactly one of:

- `ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE`
- `ROA_FULL_INCONCLUSIVE`
- `ROA_FULL_REJECTED`

If and only if ROA-FULL is supported, also assign exactly one dependence label:

- `BASELINE_INDEPENDENCE_SUPPORTED`
- `GBV_AUGMENTED_ONLY`

Do not reinterpret a near miss.

## Required outputs

Create only under:

`outputs/daa_v3_development/recovery_only_isolation_v1/`

At minimum:

- `INPUT_VERIFICATION.json`
- `FEATURE_SCHEMA.json`
- `SPLIT_MANIFEST.json`
- `MODEL_FIT_MANIFEST.json`
- `OUTER_PREDICTIONS_PRIVATE.jsonl`
- `OUTER_ACTIONS_PRIVATE.jsonl`
- `OUTER_RESULTS.json`
- `DATASET_RETRIEVER_BREAKDOWN.json`
- `LODO_TRANSPORT.json`
- `DEVELOPMENT_DECISION.json`
- `AUTHOR_REPORT.md`
- `INDEPENDENT_VALIDATION.json`
- `RECOVERY_ONLY_ISOLATION_SEAL.json`
- `SHA256_MANIFEST.json`

Independent validation must independently reconstruct feature allowlists/values, DHC-reused group splits, model predictions, top-K memberships, all metrics, all three LODO results, and decision-rule booleans without importing the primary executor as its oracle.

## Hard stop

After independent validation, seal and recursive manifest, HARD STOP.

Do not fit a final full-development ROA model and do not select fresh confirmatory IDs. Those require a separate finalization protocol only if ROA-FULL is supported.
