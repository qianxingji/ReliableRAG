# Codex task — DAA-V3 bounded risk-gated policy development

## Scope

Work against the full private project at `E:\paper\ReliableRAG` on branch:

`v3-risk-constrained-arbitration`

Read first:

- `AGENTS.md`
- `docs/V3_DEVELOPMENT_STATUS.md`
- `docs/V3_ARCHITECTURE_REVIEW_AFTER_RISK_HEAD.md`
- `docs/V3_RISK_GATED_POLICY_DEVELOPMENT_PROTOCOL.md`
- the sealed local risk-head comparison artifacts under `outputs/daa_v3_development/risk_head_comparison_v1/`

This is a **development-only policy experiment**. The goal is to test whether the already sealed trace-only Head-T damage-risk predictions improve the end-to-end repair-selection tradeoff when used as a hard gate before the frozen HGB recovery ranking.

Do not train or refit a risk head in this task. Do not add features. Do not select a new confirmatory cohort.

## Immutable input verification

Before any policy evaluation, verify exact byte hashes:

- `outputs/daa_v3_development/failure_audit_v1/FAILURE_AUDIT_SEAL.json`
  - `ff2c177bd71e29f1170b4093594194d40d2bc0d89f2eaf1273802c8c07840882`
- `outputs/daa_v3_development/risk_head_comparison_v1/INDEPENDENT_VALIDATION.json`
  - `4340295012574251aee6a3e8b17759d6d838f20667d62835eea8abfd8e52f551`
- `outputs/daa_v3_development/risk_head_comparison_v1/AUTHOR_REPORT.md`
  - `f10b14f7744f9728ce3b32ab9c2c21c85cd4723d2619d477f039a78da2a79c31`
- `outputs/daa_v3_development/risk_head_comparison_v1/RISK_HEAD_COMPARISON_SEAL.json`
  - `1d1c01f1c483db16cdeefb9f846dfb36b4058597a534c34a930a11c60eeea034`
- opened numeric outcomes
  - `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`
- frozen V2 actions/scores
  - `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- frozen GbV scores
  - `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`

Also verify the exact local SHA values for `OOF_RISK_PREDICTIONS.jsonl`, its executable/config freeze, and the recursive risk-head manifest as recorded by the sealed namespace. If any parent differs, STOP.

## Output namespace

Create only:

`outputs/daa_v3_development/risk_gated_policy_v1/`

All previous V2/V3 namespaces are read-only.

## Exact scientific inputs

Use:

1. the already sealed Head-T OOF calibrated damage probability for each eligible/scorable row;
2. frozen `state_symmetric_hgb` as the recovery-ranking score;
3. frozen `gbv_margin` for the GbV comparator;
4. opened numeric V3-development outcomes only for inner policy selection and outer development evaluation;
5. `dataset`, `retriever`, and `sample_id` only as grouping/tie-break keys, never as learned predictors.

No raw question/evidence/answer text is required for the primary experiment.

## Exact policy family

Implement only the RG-HGB family in `docs/V3_RISK_GATED_POLICY_DEVELOPMENT_PROTOCOL.md`.

Allowed veto fractions exactly:

`0.00, 0.05, 0.10, 0.20, 0.30`

Action rate remains exactly `0.05` of all trace rows in each evaluation partition.

For a partition and candidate q:

- sort eligible rows by Head-T risk descending with stable `(dataset,retriever,sample_id)` tie-break;
- veto the first `round(q * eligible_count)` rows;
- rank remaining rows by HGB descending, stable key tie-break;
- select up to `round(0.05 * total_trace_rows_in_partition)`;
- no vetoed row may return;
- no alternative refill rule or threshold is allowed.

Write a machine-readable `POLICY_SPEC.json` before reading outcome labels for any policy-selection step. It must contain the exact grid, tie-break, action cap, inner selection rule, outer split seeds and decision criteria.

## Nested grouped selection

Use exact repetition seeds:

- 20260912
- 20260913
- 20260914
- 20260915
- 20260916

For each seed, use exactly five outer folds and four inner folds with the SHA-256 formulas in the protocol.

Question groups must never cross folds.

For each outer fold:

1. determine q using only outcomes from the outer-training groups through the four inner validation folds;
2. apply the chosen q once to the untouched outer-test groups;
3. compute RG-HGB, raw-HGB, and same-cap GbV results on that outer test fold;
4. do not change q after seeing outer-test results.

Use the exact lexicographic inner rule from the protocol. `q=0` is the fallback and must be retained as an actual candidate.

## Metrics and comparators

For every outer fold and every repetition, report:

- action count;
- recovery;
- damage;
- net;
- delta EM pp;
- delta F1 pp;
- RG-HGB minus HGB EM/F1;
- RG-HGB minus GbV EM/F1;
- dataset and retriever breakdown;
- chosen q.

If V2 score ranking is available from the sealed action ledger and its score field is authenticated, include it only as a secondary development comparator; its absence must not block the primary RG-HGB/HGB/GbV comparison.

Do not run a new bootstrap or significance test unless explicitly defined by the protocol. The five repetitions are robustness summaries over the same development cohort and must not be treated as independent experiments.

## Mechanical development decision

Implement exactly the decision rule from the protocol:

`SUPPORTED_FOR_V3_FINALIZATION` only if all five support conditions pass.

`REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD` if the predeclared rejection rule passes.

Otherwise:

`INCONCLUSIVE_POLICY_STAGE`.

Do not reinterpret the result based on another metric after execution.

## Secondary Head-S sensitivity

Only after the Head-T primary outputs and `DEVELOPMENT_DECISION.json` are written and hash-frozen:

- apply Head S using the exact Head-T-selected q for every outer fold;
- do not let S choose q;
- write `SIBLING_SENSITIVITY.json`;
- do not use this sensitivity to overwrite the primary decision.

## Provisional full-development q*

Only if primary decision is `SUPPORTED_FOR_V3_FINALIZATION`, run the protocol's full-development grouped CV selection to obtain one provisional `q*` using the same grid and lexicographic rule.

If decision is not supported, `q*` must remain null/not-selected.

This task still does not fit the final deployable risk ensemble.

## Independent validator

Build an independent validator that does not import the main policy executor as its oracle. It must recompute:

- parent hashes;
- 5 x 5 outer split membership and all inner split memberships;
- eligible row counts and fold action caps;
- risk-tail veto memberships for every selected q;
- HGB/GbV stable rankings;
- every chosen q from inner outcomes;
- every outer recovery/damage/net and EM/F1 quantity;
- all five decision-rule conditions;
- final mechanical decision;
- Head-S sensitivity uses exactly Head-T q values;
- no new fit, retrieval, generation, confirmatory selection, or parent mutation occurred.

Require PASS.

## Required outputs

At minimum write:

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
- `AUTHOR_REPORT.md`

The author report must show all five repetition results and every failed criterion. Do not hide unfavorable repetitions or subgroup results.

## Hard stop

After independent validation, seal and recursive manifest, HARD STOP.

Do not fit a final V3 ensemble, select new confirmatory IDs, run retrieval/generation, alter the q grid, change action rate, or start a new method based on the result. Further work requires another reviewed task.
