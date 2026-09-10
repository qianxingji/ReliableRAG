# Prospective clarification 001: risk-gated policy rejection rule

## Authority and timing

The responsible human explicitly authorized this clarification in the current task conversation before any risk-gated policy evaluation. The existing `risk_gated_policy_v1` namespace contains only the read-only input verification script, its PASS receipt, and the ambiguity/pause note. Policy evaluation calls = 0; q selection has not started. The original pause and input-verification records are retained unchanged. A separate pre-execution record binds this amendment, the revised protocol/task byte hashes, and their local Git commit.

This clarifies only the ambiguous rejection wording. It does not change the support criteria, q grid, action rate, splits, inner selection, comparators, features, models, risk probabilities, outcomes, or any other scientific setting.

## Exact three-state rule

For each repetition and each comparator, define a success iff both:

- `RG-HGB net > comparator net`;
- `RG-HGB damage <= comparator damage`.

Count these successes separately across the five repetitions as integers `success_vs_hgb` and `success_vs_gbv` in 0..5.

- `SUPPORTED_FOR_V3_FINALIZATION` requires `success_vs_hgb >= 4` AND `success_vs_gbv >= 4`, AND all original protocol conditions 3–5: median RG-HGB minus GbV EM >= +0.30 pp; no dataset median below -0.20 pp; q > 0 in at least 15 of 25 outer folds.
- `REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD` requires `success_vs_hgb < 3 OR success_vs_gbv < 3`: either comparator has only zero, one, or two successes.
- All remaining cases are `INCONCLUSIVE_POLICY_STAGE`.

The former phrase “condition 1/2 fails in fewer than 3 of 5 repetitions” is replaced by the explicit success-count rejection rule above. Support and rejection are mutually exclusive. This is a prospective clarification, not an outcome-driven change.

## Execution boundary

Before policy evaluation, update only this document and the corresponding rule passages in `V3_RISK_GATED_POLICY_DEVELOPMENT_PROTOCOL.md` and `CODEX_TASK_DAA_V3_RISK_GATED_POLICY_DEVELOPMENT.md`, commit those three files locally, record their SHA-256 values and commit SHA, and reconfirm zero prior policy evaluations. Do not push or upload.

The original bounded task then remains in force, including fixed q={0,0.05,0.10,0.20,0.30}, action rate 0.05, existing split formulas/seeds, sealed Head-T OOF risks, frozen HGB/GbV rankings, Head-S frozen-q secondary timing, independent validation, seal, manifest, and HARD STOP. No new threshold, success standard, model/feature search, or confirmatory-ID selection is authorized.
