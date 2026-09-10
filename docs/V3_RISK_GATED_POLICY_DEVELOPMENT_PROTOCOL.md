# DAA-V3 bounded risk-gated policy development protocol

## Status

Development-only protocol. Written after `V3_ARCHITECTURE_REVIEW_AFTER_RISK_HEAD.md` and before any policy-level V3 selection on the opened cohort.

This protocol tests one structural hypothesis only: whether a trace-only calibrated damage-risk gate can improve the policy-level recovery/damage tradeoff of the frozen HGB recovery ranking.

It does not authorize a new confirmatory cohort, final V3 fit, paper claim, new retrieval/generation, or an action-rate search.

## Immutable inputs

Require exact hashes before execution:

- V3 failure-audit seal: `ff2c177bd71e29f1170b4093594194d40d2bc0d89f2eaf1273802c8c07840882`
- V3 risk-head independent validation: `4340295012574251aee6a3e8b17759d6d838f20667d62835eea8abfd8e52f551`
- V3 risk-head author report: `f10b14f7744f9728ce3b32ab9c2c21c85cd4723d2619d477f039a78da2a79c31`
- V3 risk-head seal: `1d1c01f1c483db16cdeefb9f846dfb36b4058597a534c34a930a11c60eeea034`
- V3 risk-head OOF predictions: use the exact local SHA recorded in the risk-head seal
- opened numeric outcomes: `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`
- V2 action/score ledger: `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- GbV score ledger: `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`

No parent artifact may be changed.

## Development population

Use only the already opened 4,500-question V3-development cohort.

- 13,500 total retriever traces;
- 3,202 eligible/scorable traces;
- question group key: `dataset:sample_id`;
- all sibling traces from a question must remain in the same policy-development fold;
- Head-T risk values must come from the already sealed out-of-fold calibrated predictions. Do not refit Head T in this task.

## Fixed policy family

Primary candidate family: **Risk-Gated HGB (RG-HGB)**.

For a target evaluation partition:

1. start from all eligible/scorable rows in that partition;
2. rank those rows by the sealed Head-T calibrated damage probability descending, with stable tie-break `(dataset, retriever, sample_id)`;
3. veto the top `q` fraction of eligible rows;
4. among the remaining safe rows, rank by frozen `state_symmetric_hgb` descending, with the same stable key tie-break;
5. select up to the fixed action cap for that partition;
6. no row vetoed by damage risk may be reintroduced to fill the cap;
7. if the safe set contains fewer than the cap, select all safe rows and report the lower action count explicitly.

The action cap is fixed at 5% of all retriever traces in the evaluation partition, using `round(N_trace_partition * 0.05)`.

This is a hard two-stage gate: HGB cannot compensate for being in the vetoed risk tail.

## Bounded gate-strength grid

Exactly five candidate veto fractions are allowed:

`q in {0.00, 0.05, 0.10, 0.20, 0.30}`

`q=0.00` is the raw-HGB structural fallback.

No other threshold, quantile, probability cutoff, risk multiplier, action rate, or feature subset may be tried in this task.

## Nested grouped development design

Use five deterministic repetitions, seeds:

`20260912, 20260913, 20260914, 20260915, 20260916`

For each repetition, assign every question group to one of five outer folds by:

`sha256("v3-rg-outer-v1|<seed>|<dataset>|<sample_id>") mod 5`

Within each outer-training set, assign groups to one of four inner folds by:

`sha256("v3-rg-inner-v1|<seed>|<dataset>|<sample_id>") mod 4`

No group may cross train/validation/test boundaries.

### Inner selection

For each candidate `q`, apply RG-HGB independently to each inner validation fold using only sealed Head-T OOF risks and HGB scores in that fold. Evaluate normalized-EM recovery/damage/net using the already opened development outcomes.

Aggregate the four inner folds.

Choose `q` by the following lexicographic rule:

1. among candidates whose pooled inner damage count is no greater than pooled raw-HGB (`q=0`) damage, maximize pooled net correction;
2. tie: lower damage;
3. tie: higher recovery;
4. tie: smaller `q`.

Because `q=0` is always feasible, the selection rule always has a defined fallback.

The selected `q` is then applied once to the untouched outer test fold. Outer-test outcomes must not influence that repetition/fold's `q`.

## Comparators in every outer test fold

Use the exact same fold-specific action cap for all same-budget comparators:

- raw HGB: top HGB among eligible rows;
- GbV: top `gbv_margin` among eligible rows;
- DAA-V2 score ranking, if the sealed V2 score is present and authenticated, as a secondary development comparator only.

Stable tie-break for all ranking comparators: `(dataset, retriever, sample_id)`.

If RG-HGB selects fewer than the cap because of an insufficient safe set, match GbV and HGB additionally to the actual RG-HGB action count for a transparent same-action sensitivity result; do not hide the cap-based result.

## Per-repetition outputs

Combine the five outer-test folds only within the same repetition. Do not pool the five repetitions as if they were independent samples.

For each repetition report for RG-HGB, raw HGB, GbV, and optional V2:

- action count;
- recovery;
- damage;
- net;
- delta EM pp versus Keep;
- delta F1 pp versus Keep;
- RG-HGB minus comparator EM/F1 points;
- dataset and retriever breakdowns;
- selected `q` in each outer fold.

## Development evidence criteria

Mark the simple risk-gated architecture `SUPPORTED_FOR_V3_FINALIZATION` only if all conditions below hold:

1. RG-HGB has higher net than raw HGB and no more damage than raw HGB in at least 4 of 5 repetitions;
2. RG-HGB has higher net than same-cap GbV and no more damage than GbV in at least 4 of 5 repetitions;
3. the median repetition-level RG-HGB minus GbV EM difference is at least `+0.30` pp;
4. no dataset has a median repetition-level RG-HGB minus GbV EM difference below `-0.20` pp;
5. the selected gate is nontrivial (`q>0`) in at least 15 of the 25 outer folds.

Mark `REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD` if either:

- condition 1 fails in fewer than 3 of 5 repetitions, or
- condition 2 fails in fewer than 3 of 5 repetitions.

Otherwise mark `INCONCLUSIVE_POLICY_STAGE`.

These are development engineering criteria, not confirmatory hypothesis tests.

## Secondary sibling sensitivity

Only after all primary RG-HGB results and the development decision are frozen, run one secondary sensitivity analysis using Head S with the **exact outer-fold q values selected by Head T**. Head S may not choose a new q.

Report whether S changes recovery/damage/net, but do not promote S to the primary architecture from this sensitivity analysis.

## Full-development gate parameter after support

Only if the decision is `SUPPORTED_FOR_V3_FINALIZATION`, choose one provisional deployment `q*` using five-fold grouped cross-validation over the full development cohort with the same candidate grid and lexicographic inner rule. The selection procedure and all fold summaries must be saved.

This `q*` is a development parameter only. A separate final-freeze task must later authenticate/freeze the final risk-model ensemble and action rule before any new confirmatory IDs are selected.

If the architecture is rejected or inconclusive, do not choose `q*`.

## Prohibitions

No new foundation-model calls, retrieval, generation, repair, likelihood extraction, feature engineering, sibling-feature selection, model-family search, class-weight search, action-rate search, post-hoc threshold expansion, or confirmatory-ID selection is allowed.

Do not report any result from this opened cohort as V3 fresh confirmation.

## Required outputs

Write only under:

`outputs/daa_v3_development/risk_gated_policy_v1/`

At minimum:

- `INPUT_VERIFICATION.json`
- `POLICY_SPEC.json`
- `SPLIT_MANIFEST.json`
- `INNER_SELECTIONS.json`
- `OUTER_ACTIONS_PRIVATE.jsonl`
- `OUTER_RESULTS.json`
- `DATASET_RETRIEVER_BREAKDOWN.json`
- `SIBLING_SENSITIVITY.json`
- `DEVELOPMENT_DECISION.json`
- `INDEPENDENT_VALIDATION.json`
- `RISK_GATED_POLICY_SEAL.json`
- `SHA256_MANIFEST.json`

Independent validation must recompute all group splits, q choices, action counts, recovery/damage/net, comparator rankings, decision-rule booleans, and hashes without importing the main policy executor as its oracle.

## Hard stop

After seal and manifest, HARD STOP. Do not fit the final V3 deployable ensemble, select new confirmatory IDs, or perform any new retrieval/generation.
