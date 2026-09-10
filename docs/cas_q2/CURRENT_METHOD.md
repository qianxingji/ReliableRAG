# Current method: verifier-augmented recovery arbitration

Evidence cutoff: ROA isolation closed 2026-09-10T13:41:54Z.
Protocol commit: `cd06659739810f9d0ff5dcd0e646264a26de3109`.
Binding protocol: [ROA isolation](../V3_RECOVERY_ONLY_ISOLATION_PROTOCOL.md).

## What is established

ROA-FULL is supported for final-candidate consideration, not yet a final
deployment model. It predicts normalized-EM Recovery (a0 incorrect, a1 correct)
from frozen label-free scores for an already generated original/repaired pair.
It selects top recovery probability at a 5% trace-level action cap.

Exact numeric inputs:
`state_symmetric_hgb`, `state_symmetric_logistic`, `no_cross_state`,
`no_B`, `no_evidence_change`, `no_answer_form`,
`ordinary_compact_logistic`, `B_rule`, `higher_own_likelihood`,
`likelihood_margin`, `gbv_margin`.
Add 11 missing flags and 3 retriever indicators: 25 columns.

The predictor is fixed L2 logistic regression, C=1, lbfgs, class_weight=None,
max_iter=5000, followed by disjoint Platt calibration (C=1e6, max_iter=2000).
Fit-only imputation/scaling; no outcome, sample ID or dataset ID predictors.
HGB is an upstream feature and a mandatory comparator, not ROA's top-level model.

Keep equal/empty/unscorable pairs. The batch cap is
`round(0.05 * all_trace_rows_in_partition)`, Python ties-to-even, and ties use
(dataset,retriever,sample_id). This is a batch allocation rule, not an online
threshold or formal risk guarantee. Fold caps can sum to 675 or 676.

## Roles and preserved decisions

| Object | Role and status |
|---|---|
| V2 | HGB plus damage-aware meta correction; completed confirmation, primary superiority failed |
| Raw HGB | Strong internal ranking comparator |
| GbV paired adaptation | Published verifier component adapted to answer pairs; primary external comparator |
| RG-HGB | Rejected simple gate |
| DHC-V3 | Dual-head development inconclusive; added constraint necessity not established |
| ROA-FULL | Current candidate, development support only |
| ROA-NOGBV | Required dependence ablation; baseline independence not supported |

ROA uses 4,500 already opened question groups, 13,500 traces, 3,202 eligible rows.
Five repetitions and three LODO transports reuse that development cohort.
FULL succeeded versus both HGB and GbV in 5/5 repetitions under the frozen
net-higher/damage-not-higher rule. Median FULL-minus-GbV EM/F1 differences:
+0.437037 / +0.469131 percentage points. Dependence label: GBV_AUGMENTED_ONLY.

V2 primary EM difference versus same-total-budget GbV was +0.214815 pp,
95% question-cluster CI [-0.066667,+0.496296], with 23 vs 15 damage events.
These failed/inconclusive findings remain unchanged.

## Unproven claims

No fresh V3 superiority, independent replacement of GbV, hard risk guarantee,
cross-state feature necessity, full-corpus generality or broad reader transfer
has been established for ROA. Old-method ablations/transfer/cost results are not
ROA evidence. The private runtime/model/outcome bytes must be authenticated and
replayed before the current implementation can be accepted as reproducible.

Research Lead follow-up: [method and baseline position](METHOD_AND_BASELINE_POSITION.md)
explains why ranking Recovery alone does not generally optimize expected Net;
[report recheck](REPORT_RECHECK.md) records paired mean/std and LODO limitations.
These findings do not authorize a new model search.
