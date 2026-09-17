# DAA-V3 recovery-only arbitration isolation protocol

## Status and objective

Development-only protocol. Written after the sealed DHC-V3 R1 result and before any ROA scientific refit or policy re-evaluation.

This protocol tests whether the recovery head alone explains the observed development gain and whether that gain depends critically on `gbv_margin`.

No fresh confirmatory cohort is authorized.

## Parent evidence

Before any fit, verify the exact local sealed DHC namespace `outputs/daa_v3_development/dual_head_constrained_v1/`, including:

- `AUTHOR_REPORT.md` SHA-256 `184cb2491837ac6fac7f2373af840ab7c907f6ef402083e18e0ba98e4f84f015`;
- `INDEPENDENT_VALIDATION.json` SHA-256 `16c3aa52dd9de337afe57d388fd8bc8da6d086fac1f645f7a1f85a41c9039d8b`;
- `DUAL_HEAD_DEVELOPMENT_SEAL.json` SHA-256 `59f6da26ba30ca751ccea010de1d67728fee4dd53a143d1b00ff169ae231d266`;
- the recursive DHC manifest and all three prior V3 parent manifests must remain unchanged.

Require DHC decision `INCONCLUSIVE_DUAL_HEAD_STAGE` and HARD STOP status.

## Development population

Use only the already opened V3 development cohort:

- 4,500 question groups;
- 13,500 total retriever traces;
- 3,202 frozen eligible/scorable traces;
- group key `dataset:sample_id`.

This cohort can never be described as fresh V3 confirmation.

## Exactly two allowed variants

### ROA-FULL

Use the exact recovery-head feature block from DHC:

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

plus:

- retriever one-hot BM25/Dense/Hybrid;
- one missingness indicator per numeric input.

### ROA-NOGBV

Identical to ROA-FULL except remove:

- `gbv_margin`;
- the `gbv_margin` missingness indicator.

No other feature subset is allowed.

Dataset identity, sample ID, sibling features, raw text, Gold support, correctness, V2/GbV action membership, and outcome-derived predictors are prohibited.

## Fixed model

Both variants use exactly:

- L2 logistic regression;
- `C=1.0`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=5000`.

Target:

`R=1` iff normalized-EM transition is `a0_em=0,a1_em=1`, else 0.

No Damage head is fitted in this protocol.

For each fit partition only:

1. create missingness indicators;
2. median-impute numeric missing values from that fit partition;
3. standardize continuous numeric fields using fit-partition mean/std;
4. keep binary indicators unstandardized.

Separate Platt calibration is allowed only to preserve exact comparability with the DHC recovery-head pipeline:

- calibration partition disjoint from fit;
- `C=1e6`, `lbfgs`, `class_weight=None`, `max_iter=2000`.

Because action selection is top-k within a partition, record and verify that calibration does not change within-partition ranking except ties. If it does, preserve the calibrated ranking as the protocol-defined one and report the event.

## Reuse the exact DHC grouped split namespaces

Do not choose new seeds.

Primary repeated development uses exactly the DHC seeds:

`20260917, 20260918, 20260919, 20260920, 20260921`.

Use the same DHC outer-fold and outer final fit/calibration formulas. No inner rho-selection stage is needed because ROA has no selectable risk parameter.

For each outer fold:

1. fit/calibrate ROA-FULL on outer-training groups only;
2. fit/calibrate ROA-NOGBV on the same outer-training groups only;
3. score the untouched outer-test groups once;
4. select top calibrated recovery probability among eligible/scorable outer-test rows up to the fixed action cap;
5. compute comparators on the same outer-test fold.

Question groups never cross fit/calibration/test.

## Fixed action rule

For each outer-test partition:

`K = round(0.05 * N_all_trace_rows_in_partition)`.

Each ROA variant selects exactly the top `K` eligible/scorable rows if at least `K` eligible rows exist, with stable tie-break `(dataset,retriever,sample_id)`.

No threshold, abstention rule, damage veto, rho, lambda, alpha, action-rate sweep, or quota is allowed.

## Comparators

At exactly K actions compare each ROA variant against:

1. frozen raw HGB ranking;
2. frozen `gbv_margin` ranking;
3. frozen DAA-V2 score ranking as secondary historical development context only.

Do not use comparator outcomes to alter either ROA variant.

## Metrics

For each fold and each repetition report:

- actions;
- recovery;
- damage;
- neutral;
- net;
- delta EM pp versus Keep;
- delta F1 pp versus Keep;
- ROA minus HGB and ROA minus GbV EM/F1;
- dataset, retriever, and all nine dataset×retriever breakdowns without subgroup reranking.

Do not treat repetitions as independent confirmatory samples.

## Fixed LODO transport

Reuse exactly the DHC LODO split namespace and seed `20260922`.

For each held-out dataset:

- fit/calibrate each ROA variant only on the other two datasets using the already frozen DHC LODO final fit/calibration hash rule;
- no rho selection exists;
- evaluate once on the held-out dataset at K = 5% of all held-out trace rows;
- compare to same-action-count HGB and GbV.

Run exactly:

- HotpotQA + 2Wiki -> MuSiQue;
- HotpotQA + MuSiQue -> 2Wiki;
- 2Wiki + MuSiQue -> HotpotQA.

## Predeclared architecture decision

Define repetition-level success versus comparator X as:

`ROA net > X net AND ROA damage <= X damage`.

### ROA-FULL support

Mark `ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE` only if all hold:

1. success versus raw HGB in at least 4/5 repetitions;
2. success versus GbV in at least 4/5 repetitions;
3. median repetition-level ROA-FULL minus GbV EM >= +0.40 pp;
4. median repetition-level ROA-FULL minus GbV F1 >= +0.30 pp;
5. ROA-FULL damage <= GbV damage in at least 4/5 repetitions;
6. all three LODO ROA-FULL minus GbV EM point estimates are nonnegative;
7. no LODO ROA-FULL minus HGB EM point estimate is below -0.10 pp.

Reject ROA-FULL if success versus GbV is below 3/5 or median ROA-FULL minus GbV EM <= 0. Otherwise mark it inconclusive.

### GbV-dependence classification

Only if ROA-FULL is supported, classify independence using ROA-NOGBV.

Mark `BASELINE_INDEPENDENCE_SUPPORTED` only if all hold:

1. ROA-NOGBV success versus GbV in at least 4/5 repetitions;
2. median ROA-NOGBV minus GbV EM >= +0.30 pp;
3. median `ROA-FULL minus ROA-NOGBV` EM is <= +0.10 pp;
4. all three LODO ROA-NOGBV minus GbV EM are >= -0.10 pp;
5. ROA-NOGBV median damage count is no more than ROA-FULL median damage count + 2.

Otherwise, if ROA-FULL is supported, classify `GBV_AUGMENTED_ONLY`.

This classification changes claim framing, not the already observed scientific results.

## Final development labels

Exactly one architecture outcome:

- `ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE`
- `ROA_FULL_INCONCLUSIVE`
- `ROA_FULL_REJECTED`

And, if supported, exactly one dependence label:

- `BASELINE_INDEPENDENCE_SUPPORTED`
- `GBV_AUGMENTED_ONLY`

## Prohibitions

Do not:

- add a third feature variant;
- search features or model families;
- change C, class weights, calibration, action rate, or split seeds;
- use sibling features or dataset ID;
- fit a Damage head;
- use MILP;
- select a new confirmatory cohort;
- regenerate retrieval/generation/repair/likelihood/base scores;
- call this development evidence confirmatory.

## Required outputs

Write only under:

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

Independent validation must reconstruct all splits, feature values, model predictions, action memberships, metrics, LODO results, and mechanical decisions without importing the main executor as its oracle.

## Hard stop

After independent validation, seal and manifest, HARD STOP.

Do not fit a final deployment model or select fresh confirmatory IDs. A separate finalization protocol is required if ROA-FULL is supported.
