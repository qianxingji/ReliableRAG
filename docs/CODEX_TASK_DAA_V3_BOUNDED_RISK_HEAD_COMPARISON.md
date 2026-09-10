# Codex task — DAA-V3 bounded damage-head comparison

## Scope

Work against the full private project at `E:\paper\ReliableRAG` on branch:

`v3-risk-constrained-arbitration`

Read first:

- `AGENTS.md`
- `docs/V3_DEVELOPMENT_STATUS.md`
- `docs/V3_BOUNDED_RISK_HEAD_COMPARISON_PROTOCOL.md`
- `outputs/daa_v3_development/failure_audit_v1/V3_DESIGN_CANDIDATES.md`

This is a **development-only information test**. The task must compare exactly two fixed damage heads under the frozen protocol: trace-only Head T versus the identical head augmented with cross-retriever sibling information, Head S.

Do not implement a final V3 policy, do not tune thresholds/action rates, do not select confirmatory IDs, and do not rerun retrieval or generation.

## Parent verification

Before any fit, verify byte hashes:

- `outputs/daa_v3_development/failure_audit_v1/FAILURE_AUDIT_SEAL.json`
  - `ff2c177bd71e29f1170b4093594194d40d2bc0d89f2eaf1273802c8c07840882`
- `outputs/daa_v3_development/failure_audit_v1/INDEPENDENT_VALIDATION.json`
  - `c2006500952fbd2be5e7906f901b3ceae26a39641d76494db0ccf0a11ecc070b`
- `outputs/daa_v3_development/failure_audit_v1/V3_DESIGN_CANDIDATES.md`
  - `16b181900f6328cb760b4c5bbc67ff80dd8cff43b658f851a10e5a50c0139423`
- `outputs/daa_v3_development/failure_audit_v1/SHA256_MANIFEST.json`
  - `ca890988ce01be975a0ed8d04ca9ecd8a4f3b2680d8deaa51025097fa62a9cee`
- opened V3-development outcomes
  - `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`
- V2 base scores
  - `d3842c514224354206846edb7e96b7296765d67050b131b552f469d0c64fa609`
- GbV scores
  - `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`
- V2/raw-HGB actions
  - `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- canonical branches
  - `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`

Require parent status PASS, `cohort_role=V3_DEVELOPMENT_ONLY`, no previous V3 training/hyperparameter search, and no new confirmatory selection. Any mismatch is a hard stop.

## Output namespace

Create only:

`outputs/daa_v3_development/risk_head_comparison_v1/`

Do not mutate any V2 or failure-audit parent namespace.

## Stage A — build the exact development table

Join by `(dataset, retriever, sample_id)` only.

Primary modeling domain is the frozen 3,202 eligible/scorable traces from the opened 4,500-question V3 development cohort.

Target:

- `damage=1` iff `a0_em=1` and `a1_em=0`
- otherwise `damage=0`.

The target may be used only for V3 development fit/evaluation in this task.

For every question require exactly one BM25, one Dense and one Hybrid sibling in the canonical branch ledger. Sibling groups must remain together in every split.

Write `INPUT_VERIFICATION.json` and `FEATURE_SCHEMA.json` before fitting. The feature schema must exactly mirror the protocol; no extra exploratory feature may be added.

## Stage B — exact features

### Head T

Use exactly:

- ten frozen V2 base-score fields;
- `gbv_margin`;
- anchor retriever one-hot;
- one missingness indicator for each numeric score.

No dataset ID, sample ID predictor, question/evidence text, Gold/support labels, V2/GbV action membership, `v2_score`, duplicate `hgb_score`, or outcome-derived feature.

### Head S

Use the complete Head-T block plus only the protocol-authorized information from the other two retrievers:

- their same eleven score fields;
- score missingness indicators;
- sibling eligibility;
- sibling normalized-answer-change;
- anchor-vs-sibling normalized a0 equality;
- anchor-vs-sibling normalized a1 equality;
- non-anchor sibling-pair normalized a0 equality;
- non-anchor sibling-pair normalized a1 equality.

Use raw answers only transiently to compute normalized equality flags with the already accepted normalizer. Do not persist raw answer strings in the model matrix or author report.

Missing scores must remain distinguishable through missingness flags; never map missing to a special low-risk constant.

## Stage C — deterministic group splits

Use exactly the hash rules in `V3_BOUNDED_RISK_HEAD_COMPARISON_PROTOCOL.md`.

Write `SPLIT_MANIFEST.json` containing for each outer fold:

- question-group counts;
- trace counts;
- fit/calibration/test counts;
- damage/non-damage counts;
- dataset/retriever composition;
- deterministic group-sequence hashes.

Require both classes in fit, calibration and test for all five outer folds. Do not redraw or rebalance folds.

## Stage D — fit Head T and Head S

For each outer fold and each head, independently fit the exact fixed pipeline:

- missing flags first;
- fit-partition median imputation;
- fit-partition standardization;
- L2 logistic regression `C=1.0`, `solver=lbfgs`, `class_weight=None`, `max_iter=5000`;
- separate Platt calibration on the calibration partition using one-dimensional logistic regression `C=1e6`, `solver=lbfgs`, `class_weight=None`, `max_iter=2000`.

No alternate classifier, no class weighting, no regularization sweep, no feature selection, no random seed sweep.

Generate exactly one OOF calibrated probability per eligible/scorable trace for each head and write:

`OOF_RISK_PREDICTIONS.jsonl`

This ledger may contain identifiers, target label, T probability and S probability for development audit only. Do not call it confirmatory evidence.

## Stage E — pooled OOF metrics

Compute exactly:

- damage AUPRC — primary information metric;
- AUROC;
- Brier score;
- equal-width 10-bin ECE.

Compute Head-S minus Head-T AUPRC cluster bootstrap:

- cluster: `dataset:sample_id`
- all retriever rows retained
- 5,000 draws
- seed `20260911`
- percentile 95% CI.

Write `OOF_METRICS.json`.

Do not add alternative bootstrap seeds or confidence-interval definitions after seeing the result.

## Stage F — fixed HGB-tail veto diagnostic

Read the frozen raw-HGB 675-action membership from the accepted V2 action ledger. Do not reconstruct a new HGB budget or ranking.

For T and S separately:

- rank only those 675 actions by OOF calibrated damage probability descending;
- tie-break `(dataset, retriever,sample_id)`;
- veto exactly 169 highest-risk actions;
- no refill.

Write `TAIL_VETO_DIAGNOSTIC.json` with the exact counts required by the protocol. This is not a final V3 policy.

## Stage G — three fixed leave-one-dataset-out transport tests

Run exactly:

- train/calibrate HotpotQA + 2Wiki -> test MuSiQue;
- train/calibrate HotpotQA + MuSiQue -> test 2Wiki;
- train/calibrate 2Wiki + MuSiQue -> test HotpotQA.

Use the same fixed feature definitions/model pipeline. Calibration groups are selected only by the frozen calibration hash rule. No dataset-specific tuning.

Write `DATASET_TRANSFER.json` with T/S damage AUPRC, AUROC, Brier and ECE for each held-out dataset, plus AUPRC deltas.

## Stage H — apply the decision rule mechanically

Create `DEVELOPMENT_DECISION.json` using only the predeclared rule in the protocol.

Allowed final values:

- `SUPPORTED_FOR_NEXT_V3_STAGE`
- `TRACE_ONLY_PREFERRED_FOR_NEXT_V3_STAGE`
- `INCONCLUSIVE_NEEDS_PROTOCOL_REVIEW`

Do not invent a fourth outcome and do not override the mechanical result because another metric looks attractive.

The decision applies only to whether sibling information should be retained in the next development stage. It does not choose a V3 action budget, risk threshold, final model or future cohort.

## Stage I — independent validation

Create a separate independent validator that does not import the main training/evaluation module as its metric/decision oracle.

Independently verify at minimum:

- all parent hashes and non-mutation;
- exact 4,500 question / 13,500 trace structure and 3,202 modeling rows;
- exact feature allowlists and absence of dataset/Gold/action-membership predictors;
- exact deterministic split membership;
- no sibling leakage across splits;
- model constants;
- one OOF prediction per modeling row per head;
- primary AUPRC/AUROC/Brier/ECE values within `1e-10` where deterministic arithmetic permits;
- 5,000-draw bootstrap seed and CI;
- 169-action fixed veto and transition counts;
- three fixed held-out-dataset tests;
- exact mechanical development decision;
- no confirmatory-ID selection, retrieval or generation.

Write `INDEPENDENT_VALIDATION.json` and require PASS.

## Stage J — seal and stop

Write `RISK_HEAD_COMPARISON_SEAL.json` binding all parent and output hashes, exact code/config hashes, model versions, and the final development-only decision.

Then write recursive `SHA256_MANIFEST.json`, excluding only itself.

HARD STOP.

Do not proceed to:

- final V3 architecture selection;
- risk threshold/action-budget choice;
- constrained dual-head optimization;
- new cohort selection;
- any new retrieval/generation;
- any claim that this opened cohort is V3 confirmation.

## Author-facing report

Return aggregate metrics, decision-rule components, hashes, integrity status and limitations only. Do not print question/evidence/raw answer examples.
