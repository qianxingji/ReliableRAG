# Codex task — DAA-V3 dual-head constrained development

## Scope

Work against the full private project at `E:\paper\ReliableRAG` on branch:

`v3-risk-constrained-arbitration`

Read first:

- `AGENTS.md`
- `docs/V3_DEVELOPMENT_STATUS.md`
- `docs/V3_ARCHITECTURE_REVIEW_AFTER_RG_HGB.md`
- `docs/V3_DUAL_HEAD_CONSTRAINED_DEVELOPMENT_PROTOCOL.md`
- `docs/V3_RISK_GATE_REJECTION_RULE_CLARIFICATION_001.md`
- the sealed local namespaces `failure_audit_v1`, `risk_head_comparison_v1`, and `risk_gated_policy_v1`.

This is a development-only end-to-end nested experiment. It must test exactly the dual-head constrained architecture specified in the protocol. It must not expand the model family, feature set, risk-budget grid, or action rate.

## Before any scientific fit

1. Verify the remote/local branch is a strict descendant of `e263760591c950bc5f1e73a102edce98559cbc93`.
2. Verify every parent hash required by the protocol.
3. Locate and verify the local `RISK_GATED_POLICY_SEAL.json` and recursive `SHA256_MANIFEST.json`; record exact hashes and require the mechanical decision `REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD`.
4. Verify the uploaded/audited RG-HGB artifacts against these SHA-256 values:
   - `AMENDMENT_EXECUTION_RECORD.json`: `a91bc244db608e0e78f0c46f91a2f5fb326d3827a2d88bfeff134bfed0bd0978`
   - `AUTHOR_REPORT.md`: `bad7f809566f13aa0e0eeb1fb0f3873e707fc2dee9d4f3077a72accbe4a7e6f3`
   - `INDEPENDENT_VALIDATION.json`: `a7345245a1d919d1f86a8067377699974c919a40181d4228f7b0cff89ce46bde`
5. Confirm no new confirmatory cohort, retrieval, generation, repair, likelihood or feature extraction has started.
6. Write `INPUT_VERIFICATION.json` and a code/config freeze before fitting.

Any mismatch is a hard stop.

## Output namespace

Create only:

`outputs/daa_v3_development/dual_head_constrained_v1/`

All parent namespaces are read-only.

## Exact population and targets

Use only the already opened 4,500-question / 13,500-trace V3-development cohort and the frozen 3,202 eligible/scorable traces.

Group key: `dataset:sample_id`.

Targets:

- Recovery `R=1` iff `a0_em=0` and `a1_em=1`;
- Damage `D=1` iff `a0_em=1` and `a1_em=0`.

Do not create a combined utility label.

## Exact feature block

Use only the 11 numeric trace-level fields plus retriever one-hot and numeric missingness flags declared in `V3_DUAL_HEAD_CONSTRAINED_DEVELOPMENT_PROTOCOL.md`.

No dataset identity, sibling features, sample ID predictor, raw text, Gold support, correctness, V2/GbV action membership, or outcome-derived predictor is allowed.

Save `MODEL_FEATURE_SCHEMA.json` before fitting and fail closed on any unlisted field.

## Exact model pipeline

For both Recovery and Damage heads use:

- L2 logistic regression;
- C=1.0;
- solver=lbfgs;
- class_weight=None;
- max_iter=5000.

For each fit partition, fit-only median imputation and fit-only standardization are mandatory. Binary indicators remain unstandardized.

Use separate Platt calibration for each head on a disjoint calibration partition:

- C=1e6;
- solver=lbfgs;
- class_weight=None;
- max_iter=2000.

Require both classes for both targets in every fit and calibration partition. No redraw, rebalance, resampling or class-weight correction is allowed.

Record every scientific fit and calibration call in `MODEL_FIT_MANIFEST.json`.

## Nested grouped development

Use exactly the five repetition seeds and SHA-256 split formulas in the protocol:

- 20260917
- 20260918
- 20260919
- 20260920
- 20260921

Each repetition has 5 outer folds. Each outer-training pool has 4 inner validation folds. Each inner-training pool has a separate deterministic fit/calibration split. After inner risk-budget selection, fit/calibrate new outer-final Recovery and Damage heads using only outer-training groups, then apply once to outer-test.

No outer-test label may influence head fitting, calibration, risk-budget choice or optimizer inputs for that fold.

Write complete split receipts before model fitting.

## Exact risk-budget candidates

Only:

`rho in {INF, 0.05, 0.03, 0.02, 0.01}`.

Action cap:

`K = round(0.05 * N_all_trace_rows_in_evaluation_partition)`.

No other action rate or risk threshold may be tried.

Write `RISK_BUDGET_SPEC.json` before outcome-based inner selection.

## Exact constrained optimization

For each candidate and held-out evaluation partition solve the binary optimization defined in the protocol:

maximize calibrated recovery probability sum subject to:

- action count <= K;
- for finite rho, calibrated damage-probability sum <= rho*K;
- eligible/scorable rows only.

Use only `scipy.optimize.milp` / HiGHS. No greedy or heuristic fallback.

Perform the protocol's deterministic two-pass optimization and record:

- primary optimum;
- second-pass status;
- selected count;
- predicted damage sum;
- risk-budget slack;
- stable-key tie resolution.

If any required solve is not optimal, STOP rather than changing solver/method.

## Inner rho selection

Run all five candidates through the full nested inner pipeline.

Eligibility and lexicographic selection are exactly as frozen in the protocol:

- finite candidate must retain >=90% of pooled cap;
- finite candidate damage <= INF fallback damage;
- then maximize net;
- tie lower damage;
- tie higher recovery;
- tie higher action count;
- tie weaker constraint (`INF > .05 > .03 > .02 > .01`).

Save every candidate result and selected rho in `INNER_SELECTIONS.json`.

## Outer comparators

On each outer-test fold compare DHC-V3 to:

1. recovery-only head at exactly DHC's actual action count;
2. raw HGB at exactly DHC's actual action count;
3. GbV at exactly DHC's actual action count;
4. cap-based HGB/GbV as secondary context if DHC underfills;
5. frozen V2 and rejected RG-HGB only as historical secondary development context if already authenticated.

No comparator outcome may choose rho.

## Metrics and reporting

For every outer fold and repetition report action count, retention, recovery, damage, neutral, net, delta EM pp, delta F1 pp, predicted risk sum/mean, and DHC-minus-comparator EM/F1.

Also report dataset, retriever and all nine dataset×retriever cells from the already selected outer actions. Do not rerank within subgroups.

Do not treat the five repetitions as independent confirmatory experiments.

## Mandatory leave-one-dataset-out transport

Only after primary repeated-development outputs and the primary development decision are frozen, run the three exact LODO tests specified in the protocol.

For each held-out dataset, all head fitting, calibration and rho selection must use only the other two datasets. Report DHC minus same-action-count GbV and HGB on the held-out dataset.

LODO cannot change the already frozen primary repeated-development outputs.

## Mechanical decision

Apply the protocol literally.

`SUPPORTED_FOR_V3_FINALIZATION` requires all eight support conditions.

`REJECT_DUAL_HEAD_ARCHITECTURE` if:

- success_vs_raw_hgb < 3/5; OR
- success_vs_gbv < 3/5; OR
- median repetition-level DHC-minus-GbV EM <= 0.

Otherwise return `INCONCLUSIVE_DUAL_HEAD_STAGE`.

Do not reinterpret a near miss.

## Independent validation

A second implementation must independently recompute:

- all parent hashes and recursive manifests;
- exact feature allowlist and constructed values;
- every group split;
- class-presence guards;
- saved-model prediction reconstruction;
- all inner candidate results and rho choices;
- MILP feasibility and selected memberships;
- all outer metrics and subgroup arithmetic;
- LODO results;
- every decision-rule boolean.

It may not import the main experiment executor as its oracle.

## Required outputs

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
- `AUTHOR_REPORT.md`
- `INDEPENDENT_VALIDATION.json`
- `DUAL_HEAD_DEVELOPMENT_SEAL.json`
- `SHA256_MANIFEST.json`

## Hard stop

After independent validation, seal and manifest, HARD STOP.

Do not fit a final V3 full-development ensemble, choose a final deployment rho, select new confirmatory IDs, run retrieval/generation, or write a confirmatory claim. Those require a separate finalization protocol only if this stage is supported.
