# Current method: verifier-augmented recovery arbitration

2026-09-12 P0-3 execution update: the single invented-only Phi compatibility
preflight and the subsequent value-blind full-input freeze are accepted. The
freeze independently reconstructs 63,000 deterministic prompts for all 31,500
fixed traces; the maximum is 3,682 tokens against the binding 9,472-token
ceiling, with no context truncation. Dynamic repaired-answer prompts must pass
the committed guard before CUDA/model access. Five Phi-matched policy heads
remain planned; the seven historical upstream estimators remain byte-fixed.
The joint Phi/BGE 9,472-token stress witness is independently authenticated;
Astra xhigh accepts one-process, batch-one development execution under the
dynamic guard and fail-closed OOM controls. Its allocated peak is 94.80% of
nominal device memory, so this is a bounded engineering admission rather than
scientific evidence. Development-runtime implementation/execution is authorized
next, while test benchmark execution, scientific fits and test Gold remain
closed. See PHI_BGE_JOINT_PREFLIGHT_ACCEPTANCE.md,
PHI_READER_INPUT_FREEZE_ACCEPTANCE.md and PHI_READER_REPLICATION_PROTOCOL_V1.md.

2026-09-12 fresh empirical result update: the complete 18,000-trace fixed study,
20,000-draw analysis and independent validator are accepted. HGB_GBV_R jointly
improves EM and Damage versus GBV_ONLY_R, but not versus HGB_ONLY_R; ROA-FULL
does not improve on HGB_GBV_R under the primary joint rule. No novel final
candidate is cleared. HGB_GBV_R remains only the prospectively focal empirical
object for a possible independent replication. See P0_3_FRESH_RESULT_DECISION.md.

2026-09-11 fixed empirical replication update: five separate comparison policies
are now fitted on one disjoint 3,600/900-question development fit/calibration
split. HGB_GBV_R is the focal empirical policy under its existing name; it is not
a new algorithm or a passed robustness candidate. See EMPIRICAL_AB_ACCEPTANCE.md.
All 6,000 fresh questions now have guarded runtime projections and three shared
native pools (54,716 documents total), independently accepted in
EMPIRICAL_C1_ACCEPTANCE.md. Original retrieval passed complete independent
saved-array validation (EMPIRICAL_C2_ACCEPTANCE.md). Native reader/repair
generation, fixed replay and complete V3.2 validation are now accepted in
C3_VALIDATION_V3_2_FINAL_ACCEPTANCE.md. C4 scoring, fixed actions, cost,
fresh-outcome mapping and D analysis are now complete and independently
accepted. The historical method/contribution judgments below remain visible.

Current review, 2026-09-11: ROA-FULL remains the historical candidate name, but
its full-stack attribution gate failed against HGB_GBV_R. The latter is not an
accepted replacement candidate: its subsequent HGB-only attribution study also
failed the frozen LODO floor. There is no accepted final deployment candidate.
See P0_2_CONTRIBUTION_REVIEW.md and P0_3_RESEARCH_DECISION.md. The method and
original development evidence described below are preserved historical facts.
Saved-parameter replay is now PASS, not missing; upstream provenance limitations
are recorded in P0_1_CLIENT_ACCEPTANCE.md. CAS Q2 STATUS: NOT READY.

Evidence cutoff: ROA isolation closed 2026-09-10T13:41:54Z.
Protocol commit: `cd06659739810f9d0ff5dcd0e646264a26de3109`.
Binding protocol: [ROA isolation](../V3_RECOVERY_ONLY_ISOLATION_PROTOCOL.md).

## Original method and development findings (historical)

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
| ROA-FULL | Historical candidate; subsequent attribution rule failed |
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
ROA evidence. Saved-parameter replay is accepted with the historical training
provenance limits in P0_1_CLIENT_ACCEPTANCE.md; replay does not resolve these claims.

Research Lead follow-up: [method and baseline position](METHOD_AND_BASELINE_POSITION.md)
explains why ranking Recovery alone does not generally optimize expected Net;
[report recheck](REPORT_RECHECK.md) records paired mean/std and LODO limitations.
These findings do not authorize a new model search.
