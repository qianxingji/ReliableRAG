# DAA-V3 bounded development protocol — trace-only vs cross-retriever damage head

## Status

Development-only protocol. This protocol is written after the sealed DAA-V2 confirmatory result and the sealed V3 failure audit, but before any V3 model fitting, V3 hyperparameter search, V3 action selection, or new confirmatory cohort selection.

The purpose is deliberately narrow: determine whether cross-retriever sibling signals add reproducible damage-discrimination information beyond a fixed trace-only damage head. This is not the final DAA-V3 architecture and it does not authorize selecting a future confirmatory cohort.

## Immutable parent anchors

Require exact hashes before any fit:

- V3 failure-audit seal: `ff2c177bd71e29f1170b4093594194d40d2bc0d89f2eaf1273802c8c07840882`
- V3 failure-audit independent validation: `c2006500952fbd2be5e7906f901b3ceae26a39641d76494db0ccf0a11ecc070b`
- V3 design candidates: `16b181900f6328cb760b4c5bbc67ff80dd8cff43b658f851a10e5a50c0139423`
- V3 failure-audit manifest: `ca890988ce01be975a0ed8d04ca9ecd8a4f3b2680d8deaa51025097fa62a9cee`
- opened numeric outcomes: `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`
- V2 base-score ledger: `d3842c514224354206846edb7e96b7296765d67050b131b552f469d0c64fa609`
- GbV score ledger: `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`
- V2 action ledger containing the frozen raw-HGB action control: `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- canonical branch ledger: `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`

No parent artifact may be rewritten.

## Development cohort and unit

Primary bounded comparison uses only the already opened 4,500-question V2 fresh cohort, now reclassified as V3 development evidence.

- 4,500 question groups
- 13,500 retriever traces
- exact retrievers: BM25, Dense, Hybrid
- damage-head fitting/evaluation domain: the frozen 3,202 eligible/scorable traces
- group key: `dataset:sample_id`
- target: `damage = 1` iff `a0_em=1` and `a1_em=0`; otherwise `0`

Retriever siblings from the same question must never cross fit/calibration/test partitions.

Historical 9,000-trace evidence may be used only as a supplementary authenticated shift reference. It is not required for the primary sibling-information decision and must not be used to choose hyperparameters.

## Fixed comparison

Exactly two heads are allowed.

### Head T — trace-only damage head

Continuous runtime inputs:

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

- one-hot anchor retriever identity: BM25 / Dense / Hybrid;
- an explicit missingness indicator for every numeric input.

Do not use dataset identity, sample ID, question text, raw evidence text, Gold support, correctness, transition labels other than the training target, V2 action membership, GbV action membership, `v2_score`, or a duplicated `hgb_score` field.

### Head S — trace plus sibling damage head

Head S contains the complete Head T block plus only the following predeclared sibling information from the other two retrievers of the same question:

For each other sibling, in fixed retriever-name order:

- the same 11 numeric score fields listed for Head T;
- one missingness flag per numeric field;
- sibling eligibility flag;
- sibling normalized-answer-change flag;
- normalized `a0` equality between anchor and sibling;
- normalized `a1` equality between anchor and sibling.

Also include:

- normalized `a0` equality between the two non-anchor siblings;
- normalized `a1` equality between the two non-anchor siblings.

Raw answer strings may be read only to compute these equality flags and must not be retained as model features or author-facing examples. Missing sibling scores remain missing and must be represented by explicit missingness indicators; they may not be interpreted as low risk.

No Gold-derived sibling transition state is a feature.

## Fixed preprocessing and model family

Both heads use the identical modeling pipeline so that the only scientific difference is access to sibling information.

For each fit partition only:

1. numeric missingness flags are created first;
2. missing numeric values are imputed with the fit-partition median for that feature;
3. continuous numeric values are standardized with fit-partition mean and standard deviation;
4. categorical retriever indicators remain binary;
5. fit an L2 logistic regression:
   - `C = 1.0`
   - `solver = lbfgs`
   - `class_weight = None`
   - `max_iter = 5000`
   - no hyperparameter search.

Calibration is separate from fitting. On the calibration partition only, fit a one-dimensional Platt calibrator to the base-head logit using logistic regression with:

- `C = 1e6`
- `solver = lbfgs`
- `class_weight = None`
- `max_iter = 2000`.

The calibrated probability is used for Brier/ECE and the fixed tail-veto diagnostic. AUPRC/AUROC may be computed from the calibrated probability; because Platt scaling is monotone, ranking changes should be checked and reported if ties occur.

## Fixed grouped split

Primary OOF comparison uses exactly five outer folds.

Outer fold assignment is deterministic by:

`sha256("v3-risk-head-oof-v1|" + dataset + "|" + sample_id) mod 5`

For each outer fold, all groups not in the outer test fold form the outer training pool. Split that outer training pool into fit and calibration groups by:

`sha256("v3-risk-head-cal-v1|" + dataset + "|" + sample_id) mod 4`

- remainder `0` -> calibration
- remainders `1,2,3` -> fit

The same exact group partitions must be used for Head T and Head S.

Before fitting, require every outer fit, calibration and test partition to contain both damage and non-damage labels. If not, hard stop; do not rebalance or redraw folds.

## Primary information metric

Primary metric:

**OOF damage AUPRC on all 3,202 eligible/scorable traces.**

Compute the Head-S minus Head-T AUPRC difference. Use a question-cluster bootstrap with all sibling traces retained:

- cluster = `dataset:sample_id`
- draws = 5,000
- seed = `20260911`
- percentile 95% interval.

This interval is development evidence, not a confirmatory p-value.

Also report AUROC, Brier score and 10-bin equal-width ECE for both heads, but do not select the preferred head from a post-hoc combination of these metrics.

## Fixed selected-tail diagnostic

Use the already frozen raw-HGB 675-action set as a label-free recovery-ranking control. Do not recompute or change that action set.

Within those 675 actions, use each head's OOF calibrated damage probability to rank risk descending. Veto exactly the highest-risk 25% of the frozen HGB actions:

- veto count = `round(675 * 0.25) = 169`
- no refill
- stable tie-break: `(dataset, retriever, sample_id)`.

For Head T and Head S report:

- damages removed;
- recoveries removed;
- neutral actions removed;
- retained actions;
- retained recovery;
- retained damage;
- retained net;
- damage rate in vetoed vs retained portions.

This 25% veto is a diagnostic retention test only. It is not a final V3 action rate, damage threshold or deployable policy.

## Mandatory dataset-transport diagnostic

Run exactly three leave-one-dataset-out evaluations with the same two head definitions and the same fixed model pipeline:

1. train/calibrate on HotpotQA + 2Wiki, test MuSiQue;
2. train/calibrate on HotpotQA + MuSiQue, test 2Wiki;
3. train/calibrate on 2Wiki + MuSiQue, test HotpotQA.

Within each two-dataset training pool, assign calibration groups using the same `v3-risk-head-cal-v1` hash rule; all other groups are fit groups.

Report damage AUPRC for T and S on each held-out dataset. No dataset-specific model, threshold or feature selection is allowed.

## Predeclared decision rule

The sibling block is marked `SUPPORTED_FOR_NEXT_V3_STAGE` only if all three conditions hold:

1. pooled OOF Head-S minus Head-T damage AUPRC point difference is positive **and** its 95% cluster-bootstrap lower bound is greater than 0;
2. in the fixed 25% HGB-tail veto, Head S is Pareto-non-worse than Head T: it removes at least as many damages and no more recoveries, with at least one of those two quantities strictly better;
3. leave-one-dataset-out Head-S minus Head-T AUPRC is non-negative on at least two of three held-out datasets and is greater than `-0.01` on all three.

Mark `TRACE_ONLY_PREFERRED_FOR_NEXT_V3_STAGE` only if:

- pooled OOF Head-S minus Head-T AUPRC point difference is `<= 0`, and
- Head S does not Pareto-improve the fixed HGB-tail veto.

Otherwise mark `INCONCLUSIVE_NEEDS_PROTOCOL_REVIEW`.

These labels choose only whether sibling information is worth carrying into the next V3 development stage. They do not freeze a final DAA-V3 architecture.

## Prohibitions

This protocol does not authorize:

- any other model family;
- class-weight search;
- feature subset search;
- threshold/risk-budget/action-rate sweep;
- lambda/alpha tuning;
- dual-head constrained optimization;
- choosing a new primary action budget;
- training on future confirmatory IDs;
- new retrieval/generation/repair;
- selecting future confirmatory IDs;
- reporting this opened cohort as V3 fresh confirmation.

## Required outputs

Write only under:

`outputs/daa_v3_development/risk_head_comparison_v1/`

At minimum:

- `INPUT_VERIFICATION.json`
- `FEATURE_SCHEMA.json`
- `SPLIT_MANIFEST.json`
- `OOF_RISK_PREDICTIONS.jsonl`
- `OOF_METRICS.json`
- `TAIL_VETO_DIAGNOSTIC.json`
- `DATASET_TRANSFER.json`
- `DEVELOPMENT_DECISION.json`
- `INDEPENDENT_VALIDATION.json`
- `RISK_HEAD_COMPARISON_SEAL.json`
- `SHA256_MANIFEST.json`

Independent validation must recompute split membership, feature-field allowlists, headline metrics, bootstrap configuration, tail-veto counts and the final decision rule without importing the main analysis code as its oracle.

## Hard stop

After the seal and manifest are written, HARD STOP. Do not fit a final V3 selector, choose a risk threshold, run constrained optimization, or select a new confirmatory cohort. The next stage requires separate review.