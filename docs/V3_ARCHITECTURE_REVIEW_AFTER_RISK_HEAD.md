# DAA-V3 architecture review after bounded risk-head comparison

## Status

This is a **development-stage design decision**, written after the sealed Head-T versus Head-S information test and before any end-to-end V3 policy tuning, final V3 model fit, or new confirmatory cohort selection.

The mechanical result of the bounded risk-head comparison is preserved as:

`INCONCLUSIVE_NEEDS_PROTOCOL_REVIEW`

This document does not relabel that result as support for either head.

## Accepted evidence

The comparison used the already opened V3-development cohort only. The key results were:

- Head T damage AUPRC: `0.2533373479241768`;
- Head S damage AUPRC: `0.2647379846327252`;
- S minus T AUPRC: `+0.011400636708548406`;
- 95% question-cluster bootstrap interval: `[-0.00955093373589463, +0.03379336503775843]`;
- fixed HGB-tail veto: T removed 10 damages and 33 recoveries, S removed 14 damages and 40 recoveries;
- retained net under that diagnostic: T `242`, S `239`;
- leave-one-dataset-out S-minus-T AUPRC: MuSiQue `-0.0034511544566407093`, 2Wiki `+0.03590496918806446`, HotpotQA `+0.03670316470539786`.

The predeclared sibling-support rule did not pass because the pooled bootstrap lower bound crossed zero and the fixed-veto Pareto condition failed. The trace-only-preferred rule also did not pass because the pooled AUPRC point difference favored S.

## Review decision

For the **next policy-development stage only**, use **Head T (trace-only)** as the primary damage-risk input.

This is a parsimony decision, not a claim that T is scientifically superior to S. The reasons are:

1. the incremental sibling block did not satisfy the predeclared evidence threshold required to justify 54 additional features;
2. the fixed veto showed a damage/recovery tradeoff rather than a Pareto gain;
3. S is operationally more expensive in settings where sibling retriever branches are not already available;
4. a simpler primary path makes the next experiment isolate whether explicit risk gating itself adds value over HGB/V2, instead of conflating that question with cross-retriever feature expansion.

Head S remains a **predeclared secondary ablation/sensitivity input**. It may be evaluated only at a policy configuration chosen without using Head-S outcomes. It may not be used to choose the primary V3 configuration unless a future separately frozen protocol explicitly reopens that question.

## Provisional V3 structural hypothesis

The next hypothesis is:

> A separately learned, out-of-fold damage-risk gate can filter a fixed HGB recovery ranking so that selected repairs retain HGB's recovery strength while reducing repair-induced damage.

The structural unit is therefore:

**trace-only calibrated damage-risk gate -> HGB recovery ranking -> fixed action cap**.

This is not yet the final DAA-V3 method. In particular, no veto fraction, risk threshold, action budget other than the already fixed development cap, or final deployment model has been selected by this document.

## What the next experiment must establish

The next stage must use nested question-grouped development validation and a small, predeclared gate-strength grid. It must test whether the risk gate improves policy-level recovery/damage tradeoffs relative to raw HGB and GbV, not merely whether the damage classifier has a favorable AUPRC.

The action rate remains fixed at 5% for this development comparison. No alternative action-rate sweep is allowed.

If the risk-gated HGB policy does not show robust policy-level benefit, the simpler-veto hypothesis is rejected and the project should move to a separately reviewed constrained dual-head design rather than expanding ad hoc thresholds or sibling features.

## Evidence boundary

The entire current cohort is V3 development evidence. It may be used for nested development selection, but it can never again be described as unseen V3 confirmation.

No new confirmatory IDs may be selected until the V3 architecture, feature schema, model-fitting recipe, gate parameter, action rule, comparator hierarchy, and success criteria are fully frozen.
