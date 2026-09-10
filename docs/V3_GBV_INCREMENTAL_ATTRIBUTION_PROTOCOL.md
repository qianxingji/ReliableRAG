# DAA-V3 GbV incremental-attribution protocol

## Status and objective

Development-only, single-control attribution protocol. Written after recovery-only isolation returned `ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE` with dependence label `GBV_AUGMENTED_ONLY`, and before any execution of `ROA-GBVONLY`, final full-development fit, or new confirmatory-cohort selection.

The only scientific question is:

> Do the ten non-GbV intervention/base-score features in ROA-FULL add material policy value beyond a supervised recovery model built from `gbv_margin` plus the already frozen retriever identity block?

This protocol is not authorization for a feature search or fresh confirmation.

## Mandatory parent verification

Before any new scientific fit, verify the entire sealed local namespace:

`outputs/daa_v3_development/recovery_only_isolation_v1/`

and require:

- architecture decision exactly `ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE`;
- dependence label exactly `GBV_AUGMENTED_ONLY`;
- hard stop true;
- no final full-development model;
- no new confirmatory-ID selection.

Verify these reported parent SHA-256 anchors:

- `AUTHOR_REPORT.md`: `4090ec70c4a9154ecfc960c9c2bc26317b585d06cc308ee962a984e8981bbf6d`;
- `DEVELOPMENT_DECISION.json`: `a38673592d9d0cba7dadf92c66439919d3fbd99949545aa2868ee01c15796acf`;
- `INDEPENDENT_VALIDATION.json`: `4a809efaf38de9c14e7df696d803a88bf4bab1d1226a688f08813810d90206b7`;
- `RECOVERY_ONLY_ISOLATION_SEAL.json`: `61f5b0c8103af32ce6bb901fdebfff61f1130deee7f382720feee12caf6cede5`.

Also verify its recursive manifest and all earlier V3 parent manifests byte-for-byte. Parent ROA-FULL outputs are immutable and must not be regenerated or overwritten.

## Output namespace

Write new artifacts only under:

`outputs/daa_v3_development/gbv_incremental_attribution_v1/`

## Development population

Use only the already opened V3 development cohort:

- 4,500 question groups;
- 13,500 retriever traces;
- 3,202 frozen eligible/scorable traces;
- group key `dataset:sample_id`.

No new source Gold may be read and no new retrieval/generation/repair/likelihood/base-score extraction is allowed.

## Exactly one new learned variant

### ROA-GBVONLY

Target:

`R=1` iff normalized-EM transition is `a0_em=0,a1_em=1`, else 0.

Runtime/model inputs exactly:

1. numeric `gbv_margin`;
2. one explicit `gbv_margin` missingness flag;
3. BM25/Dense/Hybrid retriever one-hot indicators.

No other score or feature is allowed. In particular prohibit all ten non-GbV ROA numeric scores, dataset identity, sample ID, raw text, sibling features, correctness, Gold support, action membership, and damage labels.

This single control intentionally keeps retriever identity because that block is already part of ROA-FULL; therefore FULL minus GBVONLY isolates the incremental contribution of the ten non-GbV numeric feature channels and their missingness indicators.

## Fixed model and preprocessing

Use exactly the ROA-FULL estimator family:

- L2 logistic regression;
- `C=1.0`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=5000`.

For each fit partition only:

- create the missingness flag;
- median-impute `gbv_margin` from the fit partition;
- standardize `gbv_margin` using fit-partition mean and population std;
- leave missingness and retriever one-hot indicators unstandardized.

Use the same disjoint Platt calibration pipeline as ROA-FULL:

- `C=1e6`;
- `solver=lbfgs`;
- `class_weight=None`;
- `max_iter=2000`.

Require both recovery classes in fit and calibration; otherwise hard stop with no redraw, rebalancing or class weighting.

Do not remove calibration in this experiment even if it is monotone/ranking-preserving. That question is outside this attribution protocol.

## Exact partitions

Reuse the sealed recovery-only isolation split manifest exactly. Do not derive new seeds or new hashes.

Primary repeated-development seeds remain exactly:

`20260917, 20260918, 20260919, 20260920, 20260921`.

For all 25 outer-test partitions, use the exact same outer-training fit/calibration memberships used by ROA-FULL.

LODO remains exactly seed `20260922` with the same three fixed two-dataset-training / one-dataset-held-out partitions and final fit/calibration memberships used by ROA-FULL.

Expected new scientific fits: 28 base Recovery fits + 28 Platt calibrators = 56 calls, subject only to technical hard stop. ROA-FULL is reused from the sealed parent and contributes zero new fits.

## Fixed action rule

For each primary outer-test and each LODO held-out dataset:

`K = round(0.05 * N_all_trace_rows_in_partition)`

using the same Python rounding semantics as the parent experiment.

ROA-GBVONLY selects the top K eligible/scorable rows by calibrated recovery probability with stable tie-break:

`(dataset,retriever,sample_id)`.

No threshold, quota, action-rate search, damage veto, rho, lambda or alpha is allowed.

## Fixed reference methods

Primary attribution reference:

- sealed ROA-FULL actions/results from `recovery_only_isolation_v1`.

Mandatory context:

- raw GbV at K;
- raw HGB at K;
- sealed ROA-NOGBV as secondary attribution context.

Do not refit or alter any reference method.

## Metrics

For every outer fold, pooled repetition and LODO report for ROA-GBVONLY:

- actions;
- recovery;
- damage;
- neutral;
- net;
- delta EM pp versus Keep;
- delta F1 pp versus Keep;
- differences versus ROA-FULL, raw GbV and raw HGB;
- dataset, retriever and all nine dataset×retriever cells without subgroup reranking.

For FULL minus GBVONLY always report both point differences and exact recovery/damage/net accounting. Do not hide unfavorable repetitions or subgroups.

## Prospective incremental-value decision

Define repetition-level `FULL_increment_success` as:

`ROA-FULL net > ROA-GBVONLY net AND ROA-FULL damage <= ROA-GBVONLY damage`.

Mark `FULL_INCREMENT_SUPPORTED` only if all conditions hold:

1. `FULL_increment_success >= 4/5` repetitions;
2. median repetition-level `ROA-FULL minus ROA-GBVONLY` EM >= `+0.20 pp`;
3. median repetition-level `ROA-FULL minus ROA-GBVONLY` F1 >= `+0.15 pp`;
4. ROA-FULL damage <= ROA-GBVONLY damage in at least 4/5 repetitions;
5. among three LODO FULL-minus-GBVONLY EM point estimates, at least 2/3 are nonnegative;
6. no LODO FULL-minus-GBVONLY EM point estimate is below `-0.10 pp`.

These are development engineering criteria, not confirmatory significance tests.

### Attribution-failure diagnostic

If `FULL_INCREMENT_SUPPORTED` is false, compute but do not use to select a replacement method:

- GBVONLY success versus raw GbV under the same `net higher AND damage no higher` rule;
- median GBVONLY-minus-raw-GbV EM/F1;
- GBVONLY LODO contrasts versus raw GbV.

If FULL increment is unsupported and GBVONLY itself shows success versus raw GbV in >=4/5 repetitions with median GBVONLY-minus-GbV EM >= +0.30 pp, label:

`GBVONLY_EXPLAINS_MOST_GAIN_REQUIRES_ARCHITECTURE_REVIEW`.

This label does **not** authorize replacing ROA-FULL with GBVONLY.

Otherwise, when FULL increment is unsupported, label:

`INCREMENTAL_ATTRIBUTION_INCONCLUSIVE`.

If all six FULL increment conditions pass, final label is:

`FULL_INCREMENT_SUPPORTED`.

Exactly one final label is allowed.

## Independent validation

A separate implementation must independently verify/recompute:

- parent hashes/manifests remain unchanged;
- exact GBVONLY feature schema;
- exact reuse of all 25 primary and 3 LODO partitions;
- fit-only preprocessing and class guards;
- all 56 newly recorded fit/calibration calls;
- saved model/calibrator predictions;
- top-K action memberships;
- primary and LODO metrics/subgroups;
- all six incremental-value conditions;
- diagnostic label logic;
- final decision.

It may not import the primary executor as its oracle.

## Required outputs

At minimum:

- `INPUT_VERIFICATION.json`
- `FEATURE_SCHEMA.json`
- `SPLIT_REUSE_VALIDATION.json`
- `MODEL_FIT_MANIFEST.json`
- `PREDICTIONS_PRIVATE.jsonl`
- `ACTIONS_PRIVATE.jsonl`
- `OUTER_RESULTS.json`
- `DATASET_RETRIEVER_BREAKDOWN.json`
- `LODO_TRANSPORT.json`
- `INCREMENTAL_VALUE_DECISION.json`
- `AUTHOR_REPORT.md`
- `INDEPENDENT_VALIDATION.json`
- `GBV_INCREMENTAL_ATTRIBUTION_SEAL.json`
- `SHA256_MANIFEST.json`

## Hard stop

After independent validation, seal and recursive manifest, HARD STOP.

Do not:

- add another attribution variant;
- search feature subsets or model families;
- change model hyperparameters or calibration;
- change action rate;
- refit ROA-FULL;
- fit a final deployment model;
- select new confirmatory IDs;
- run new retrieval/generation;
- make a fresh superiority claim.

A separate finalization review is mandatory after this attribution result.