# DAA-V3 architecture review after dual-head constrained development

## Status

Development-stage design decision written after the sealed DHC-V3 R1 experiment and before any new V3 finalization, new confirmatory cohort selection, or further architecture search.

The DHC-V3 R1 mechanical result is preserved exactly as:

`INCONCLUSIVE_DUAL_HEAD_STAGE`

This document does not relabel that result as support.

## Accepted DHC evidence

The completed end-to-end nested development experiment showed:

- DHC versus same-action-count GbV: success in 5/5 repetitions;
- DHC versus same-action-count raw HGB: success in 5/5 repetitions;
- median DHC minus GbV EM difference: approximately +0.444444 pp;
- median DHC minus GbV F1 difference: approximately +0.481476 pp;
- DHC action retention median: 100%;
- LODO DHC minus GbV EM was positive on MuSiQue, 2Wiki and HotpotQA;
- however, DHC versus the recovery-only head succeeded in only 1/5 repetitions;
- a finite damage-budget rho was selected in only 5/25 outer folds, and all three LODO transports selected `INF`.

Thus support conditions for the dual-head architecture failed because the explicit damage constraint did not establish enough incremental policy value beyond the recovery-only head and was usually inactive.

## Scientific interpretation

The key positive result is not that the dual-head constraint is validated. It is that the independently fitted recovery head itself appears to be the dominant source of the large improvement over GbV and HGB.

In most repeated-development folds DHC selected `rho=INF`, making DHC identical to recovery-only selection. In the few finite-rho folds the damage head sometimes reduced damage, but not consistently enough to justify the extra constrained architecture under the predeclared rule.

Therefore:

1. do not widen the rho grid;
2. do not lower the finite-rho support threshold;
3. do not reinterpret the DHC result as positive;
4. do not select a final DHC deployment rho;
5. do not move to a fresh confirmatory cohort yet.

## Next bounded architecture question

The next question is narrower and more important:

> Does a simple trace-level recovery estimator, without the damage head or MILP constraint, robustly account for the observed gain over GbV; and does that gain remain when the GbV margin is removed from the estimator input?

This isolates two reviewer-critical issues:

- **parsimony**: whether the recovery head alone is sufficient;
- **baseline dependence**: whether the method merely learns on top of the GbV score that it later compares against.

## Candidate for the next stage

Use the neutral working name **Recovery-Only Arbitration (ROA)** for development only.

Primary variant:

- `ROA-FULL`: the exact recovery-head feature family used in DHC, including `gbv_margin`.

Mandatory independence ablation:

- `ROA-NOGBV`: identical model, preprocessing and splits, but with `gbv_margin` and only its corresponding missingness indicator removed.

No other feature subset or model family is authorized in the next stage.

The next experiment must reuse the already frozen DHC grouped split namespaces rather than choosing new favorable seeds. It must use a fixed 5% action cap and must not tune thresholds, risk budgets, class weights, or action rates.

## Evidence boundary

All existing 4,500-question evidence is V3 development only. Even if ROA is strongly supported, a new untouched cohort is still mandatory for any final superiority claim.

If ROA-FULL is supported but ROA-NOGBV is not, the future method must be described transparently as a verifier-augmented arbitration method rather than an independent replacement for GbV.

If ROA-NOGBV also preserves the gain, the final method may make a stronger baseline-independent methodological claim.
