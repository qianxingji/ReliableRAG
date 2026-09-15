# DAA-V3 architecture review after risk-gated HGB development

## Status

Development-stage design decision. This document is written after the sealed RG-HGB development experiment and before any dual-head end-to-end fitting, risk-budget selection, final V3 freeze, or new confirmatory cohort selection.

The previous simple risk-gated architecture is preserved as mechanically rejected:

`REJECT_SIMPLE_RISK_GATE_MOVE_TO_DUAL_HEAD`

This result is development evidence only. It is not V3 confirmation.

## Accepted RG-HGB evidence

The completed development experiment used the already opened 4,500-question / 13,500-trace cohort, with 3,202 eligible/scorable traces. The protocol clarification was recorded before any policy evaluation or q-selection call.

Key repeated-development results:

- RG-HGB versus raw HGB: success in 5/5 repetitions under the fixed criterion `higher net and no more damage`;
- RG-HGB versus same-cap GbV: success in 0/5 repetitions;
- median RG-HGB minus GbV EM difference: `+0.20` percentage points;
- nontrivial gate selected in 23/25 outer folds;
- dataset median RG-HGB minus GbV EM remained nonnegative for 2Wiki, HotpotQA and MuSiQue;
- the simple architecture therefore failed predeclared conditions 2 and 3 and was rejected.

The experiment shows that explicit damage gating can improve the frozen HGB policy, but the simple `damage veto -> HGB ranking` structure does not reduce damage enough to satisfy the stronger GbV comparison.

## Design decision

Do **not** expand the old q-grid, action-rate grid, feature set, sibling block, or HGB threshold after seeing the RG-HGB results.

Proceed to one bounded **Dual-Head Risk-Constrained Arbitration** development experiment.

The next structural hypothesis is:

> Estimate recovery and damage separately on the same trace-only pre-label information, then maximize predicted recovery subject to an explicit predicted-damage budget and action cap, rather than using a compensatory scalar utility or a fixed global veto fraction.

This changes the selection problem itself. High predicted recovery may not erase the damage constraint.

## Primary feature decision

Use the trace-only feature family as the primary V3 feature set.

The sibling-augmented Head S remains a prior secondary ablation result only. Its pooled AUPRC increment was positive but inconclusive, and its fixed veto did not Pareto-improve Head T. No sibling feature is added in the primary dual-head experiment.

Retriever identity may remain as a one-hot predictor because it is a runtime-known system state and prior development showed materially different behavior across BM25, Dense and Hybrid. Dataset identity, sample ID, question text, raw evidence text, Gold support, correctness and outcome-derived features remain prohibited.

## Required methodological correction

The RG-HGB stage used previously sealed OOF risk scores whose training/calibration partitions differed from the policy outer folds. That was acceptable for the bounded fixed-score diagnostic, but it is insufficient for selecting a final architecture.

The dual-head stage must therefore be **end-to-end nested and question-grouped**:

1. outer-test question groups are excluded from all head fitting, calibration and risk-budget selection for that outer fold;
2. inner validation chooses only among one predeclared risk-budget grid;
3. after the risk budget is chosen, both heads are fitted/calibrated only from the outer-training groups and applied once to outer-test;
4. no future confirmatory IDs may be selected until this development stage is sealed and reviewed.

## Decision boundary

If the dual-head constrained policy satisfies its predeclared repeated-development and transport criteria, it may proceed to a separate V3 finalization/freeze task.

If it fails clearly, do not widen the risk-budget grid or add sibling features post hoc. The project must either accept the negative result or reopen the architecture only through a new explicit development protocol.
