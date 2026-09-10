# Codex task — DAA-V3 GbV incremental attribution

## Scope

Work locally at `E:\paper\ReliableRAG` on branch:

`v3-risk-constrained-arbitration`

Read first:

- `AGENTS.md`
- `docs/V3_DEVELOPMENT_STATUS.md`
- `docs/V3_ARCHITECTURE_REVIEW_AFTER_DHC.md`
- `docs/V3_RECOVERY_ONLY_ISOLATION_PROTOCOL.md`
- `docs/V3_ARCHITECTURE_REVIEW_AFTER_ROA_ISOLATION.md`
- `docs/V3_GBV_INCREMENTAL_ATTRIBUTION_PROTOCOL.md`
- sealed local `outputs/daa_v3_development/recovery_only_isolation_v1/`.

This is one development-only attribution experiment. Fit exactly one new variant: `ROA-GBVONLY`. No feature/model search and no fresh cohort are authorized.

## Mandatory preflight

Before the first new scientific fit:

1. synchronize the branch by fast-forward only; do not force push or rewrite history;
2. verify the local branch contains the architecture review and attribution protocol;
3. verify recovery-only parent decision exactly `ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE` and dependence label exactly `GBV_AUGMENTED_ONLY`;
4. verify parent hashes:
   - `AUTHOR_REPORT.md` = `4090ec70c4a9154ecfc960c9c2bc26317b585d06cc308ee962a984e8981bbf6d`;
   - `DEVELOPMENT_DECISION.json` = `a38673592d9d0cba7dadf92c66439919d3fbd99949545aa2868ee01c15796acf`;
   - `INDEPENDENT_VALIDATION.json` = `4a809efaf38de9c14e7df696d803a88bf4bab1d1226a688f08813810d90206b7`;
   - `RECOVERY_ONLY_ISOLATION_SEAL.json` = `61f5b0c8103af32ce6bb901fdebfff61f1130deee7f382720feee12caf6cede5`;
5. verify the entire parent recursive manifest and all earlier V3 parent manifests byte-for-byte;
6. confirm ROA-FULL parent outputs will be read-only and zero ROA-FULL refits are planned;
7. confirm no new confirmatory IDs, source Gold, retrieval, generation, repair, likelihood/base-score extraction or feature search has occurred;
8. freeze execution/config and write `INPUT_VERIFICATION.json`, `FEATURE_SCHEMA.json`, and `SPLIT_REUSE_VALIDATION.json` before the first fit.

Any mismatch is a hard stop.

## Exactly one new variant

`ROA-GBVONLY` uses only:

- numeric `gbv_margin`;
- its explicit missingness indicator;
- retriever one-hot BM25/Dense/Hybrid.

Recovery target only:

`R=1 iff a0_em=0 and a1_em=1`.

Do not include any of the ten non-GbV score features, dataset/sample identity, sibling features, raw text, Gold support, correctness, action membership, or Damage target.

## Exact model

Use the same ROA estimator family:

- L2 LogisticRegression;
- C=1.0;
- solver=lbfgs;
- class_weight=None;
- max_iter=5000.

Fit-only preprocessing:

- missing flag;
- median imputation for `gbv_margin`;
- fit-only mean/population-std standardization for `gbv_margin`;
- leave binary indicators unstandardized.

Separate disjoint Platt calibration exactly as parent:

- C=1e6;
- lbfgs;
- class_weight=None;
- max_iter=2000.

Require both recovery classes in every fit and calibration partition. No redraw, rebalance or weighting.

## Exact partition reuse

Reuse the recovery-only isolation split manifest byte-for-byte.

Primary partitions:

- five seeds `20260917` through `20260921` exactly as parent;
- all 25 outer-test partitions and their exact fit/calibration memberships.

LODO:

- seed `20260922`;
- exactly MuSiQue, 2WikiMultiHopQA and HotpotQA held out in turn;
- exact parent two-dataset fit/calibration memberships.

Do not generate a new split namespace.

Expected scientific calls: exactly 28 base-model fits + 28 Platt fits = 56, unless a technical hard stop occurs. Do not refit ROA-FULL.

## Selection and references

For every evaluation partition:

`K = round(0.05 * N_all_trace_rows_in_partition)`

with the same rounding semantics as parent.

Select top K eligible/scorable rows by calibrated ROA-GBVONLY recovery probability, stable tie-break `(dataset,retriever,sample_id)`.

Read sealed ROA-FULL predictions/actions/results as the immutable primary attribution reference. Also report raw GbV, raw HGB, and sealed ROA-NOGBV context at the same K.

No threshold, quota, action-rate, rho, veto, lambda, alpha or policy search.

## Mechanical attribution decision

Apply `docs/V3_GBV_INCREMENTAL_ATTRIBUTION_PROTOCOL.md` literally.

`FULL_increment_success` for one repetition means:

`FULL net > GBVONLY net AND FULL damage <= GBVONLY damage`.

`FULL_INCREMENT_SUPPORTED` requires all six frozen conditions:

1. success >=4/5;
2. median FULL-minus-GBVONLY EM >= +0.20 pp;
3. median FULL-minus-GBVONLY F1 >= +0.15 pp;
4. FULL damage <= GBVONLY in >=4/5;
5. LODO FULL-minus-GBVONLY EM nonnegative in >=2/3;
6. no LODO FULL-minus-GBVONLY EM below -0.10 pp.

If these fail, apply only the already frozen diagnostic logic and return either:

- `GBVONLY_EXPLAINS_MOST_GAIN_REQUIRES_ARCHITECTURE_REVIEW`, or
- `INCREMENTAL_ATTRIBUTION_INCONCLUSIVE`.

Do not reinterpret near misses and do not promote GBVONLY automatically.

## Output namespace

Create only:

`outputs/daa_v3_development/gbv_incremental_attribution_v1/`

At minimum produce:

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
- `SHA256_MANIFEST.json`.

Independent validation must separately reconstruct the GBVONLY features, all reused partitions, model/calibrator predictions, top-K memberships, metrics, subgroup arithmetic, LODO results and six-condition decision logic without importing the primary executor as its oracle.

## Hard stop

After independent validation, seal and recursive manifest, HARD STOP.

Do not add variants, tune features/models, change action rate, refit FULL, fit a final deployable model, select fresh confirmatory IDs, run new retrieval/generation, or make confirmatory claims.

Return the sealed attribution result for architecture review.