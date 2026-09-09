# DAA-V2 development decision

Status: **DEVELOPMENT CLOSED. Prospective fresh execution is blocked on the identifier-only availability audit and final pre-label freeze.**

This document records decisions made from the historical 9,000-trace cohort after that cohort was reclassified as V2 development evidence. None of the numerical results below are fresh confirmatory evidence.

## 1. What the frozen historical ledger establishes

Re-ranking the already-frozen state-symmetrized HGB score under a single global action budget yields a materially stronger operating point than the historical retriever-specific HGB thresholds.

At 370 actions, global HGB ranking produced 191 recoveries, 7 damages, and 184 net corrections. The exact historical Conservative dataset x retriever budgets, when imposed on HGB ranking, produced 173 recoveries, 17 damages, and 156 net corrections. These diagnostics indicate that the HGB advantage has two components: stronger within-stratum ranking and better system-level allocation of actions across retrieval regimes. Neither result is prospective evidence.

The 370-action global point is positive in every dataset and retriever. In particular, Hybrid receives 107 actions and 52 net corrections under global HGB ranking rather than being nearly frozen.

## 2. Nested development validation of a damage-aware correction

A three-state meta model predicts recovery, damage, or neutral transition behavior from frozen label-free selector scores. Question ID is the grouping unit, so all retriever traces for one question remain together.

Across ten grouped nested seeds (20260909--20260918):

| Budget | Candidate V2 net, median [min,max] | Raw HGB net, median [min,max] | Candidate damage, median [min,max] | Raw HGB damage, median [min,max] | Stability |
|---|---:|---:|---:|---:|---|
| 370 | 185 [181,189] | 182 [178,187] | 5 [3,6] | 7 [6,10] | V2 net better in 9/10, tied in 1/10; damage lower in 10/10 |
| 450 | 209 [206,217] | 200 [197,204] | 7.5 [6,9] | 10.5 [9,14] | V2 net better in 10/10; damage lower in 10/10 |

At 450 actions, mean nested V2 net is 209.6 versus 200.6 for raw HGB, and mean damage is 7.4 versus 10.9. Repeated folds are sensitivity checks on one historical cohort, not independent replications.

A fixed-parameter stability check was then used to avoid carrying per-fold hyperparameter selection into the prospective method. The retained parameters are:

- damage penalty `lambda = 1.0`;
- meta fusion weight `alpha = 2.0`;
- question-grouped fold count `5`;
- fold seed `20260909`;
- primary action rate `5.0%`.

With the same fixed parameters across repeated grouped partitions, the 450-action development net remained in the 211--216 range and damage remained in the 5--7 range.

## 3. Final development architecture decision

The prospective candidate is **DAA-V2: state-symmetrized HGB backbone + three-state damage-aware meta correction**.

The runtime ranking is built from ten pre-existing, label-free base score fields:

1. `state_symmetric_hgb`;
2. `state_symmetric_logistic`;
3. `no_cross_state`;
4. `no_B`;
5. `no_evidence_change`;
6. `no_answer_form`;
7. `ordinary_compact_logistic`;
8. `B_rule`;
9. `higher_own_likelihood`;
10. `likelihood_margin`.

The meta model predicts recovery / damage / neutral, forms

`U = p(recovery) - p(damage)`,

quantile-normalizes this utility, and fuses it with the quantile-normalized HGB backbone using fixed `alpha = 2.0`.

The retained future predictor is a five-model question-grouped cross-fitted ensemble trained only from the historical developmentized cohort. This avoids refitting one final model and then transferring thresholds to a changed score scale.

Raw global HGB at the identical action budget is a mandatory, pre-sealed key ablation. DAA-V2 is not allowed to replace HGB post hoc if the fresh ablation is unfavorable.

## 4. Complexity and leakage guardrails

Dataset identity is excluded from the prospective feature set even though exploratory historical development showed gains. Encoding benchmark identity in the selector would weaken transfer claims and create an avoidable benchmark-specific shortcut.

The ten-score candidate above is now **frozen for the first prospective fresh run**. It is no longer permissible to reduce, enlarge, or substitute the feature set based on new fresh outputs. A future V3 would require a new development cycle and a new prospective cohort.

GbV NLI scores are **not** input features to DAA-V2 in the prospective run. GbV remains an independent published-method comparator. This prevents the method from absorbing the comparator after its performance became known.

## 5. Primary budget and comparator decisions

The prospective primary action rate is **5.0% of retriever-conditioned traces**. On the historical 9,000-trace reference this corresponds to 450 actions; on a 4,500-question / 13,500-trace fresh cohort it would correspond to 675 actions.

The prospective comparisons are frozen as follows:

- **Primary published-method contrast:** DAA-V2 versus GbV with the exact same total replacement count.
- **Secondary strict fairness contrast:** DAA-V2 versus GbV with exact DAA-V2 action counts inside every dataset x retriever stratum.
- **Secondary published-policy contrast:** DAA-V2 versus GbV using the historical 7,200-development-selected GbV thresholds transferred unchanged.
- **Key method ablation:** DAA-V2 versus raw global HGB at the exact same total action count.

The fixed secondary same-budget operating-rate grid is `1%, 2.5%, 5%, 7.5%, 10%`. The 5% result remains primary; the curve cannot be used to promote a different fresh operating point.

## 6. Development is closed; remaining steps are prospective execution steps

The following are **not further model-development tasks**:

1. Run the identifier-only source/forbidden-ID availability audit. Preferred target: 1,500 genuinely unused evaluation questions per dataset. If any source cannot provide that count under the frozen freshness rule, stop before generation and create a prospective protocol amendment.
2. Verify all historical private model artifacts byte-for-byte against `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`.
3. Freeze selected fresh IDs, source projections, candidate-pool construction, canonical branches, V2 model artifact, V2/HGB scores/actions, GbV scores/actions, and all hashes.
4. Require `seal_v2_gbv_prelabel_gate.py` to return PASS, then stop the gold-free execution.
5. Only under a separate responsible-human authorization, map numeric fresh outcomes and run the already-fixed evaluators exactly once.

The old private GbV score archive is no longer a blocker for the prospective study. The new fresh cohort will be scored label-free from the pinned GbV recipe and model revision before labels are opened.

## 7. Fresh source and sample-size planning boundary

The preferred target is **4,500 unique questions = 1,500 per dataset = 13,500 traces**, subject to identifier-only availability audit.

HotpotQA and 2WikiMultiHopQA should use genuinely unused IDs from their appropriate held-out/runtime sources. Because the previously used MuSiQue answerable-dev source contains only 2,417 rows and has already contributed heavily to prior main/operator/fresh experiments, the prospective MuSiQue evaluation source is genuinely unused IDs from `musique_ans_v1.0_train.jsonl`, excluding the historical MuSiQue development set and every previously evaluated question ID.

This source-split change is intentional and must be disclosed; it must not be hidden as if all three datasets used the same original split as the historical paper.

## 8. High-standard success criteria

Formal primary superiority is the predeclared paired question-cluster EM interval with lower bound above zero for DAA-V2 minus same-total-budget GbV.

The deliberately stronger engineering target additionally requires:

- EM point advantage >= +0.60 percentage points;
- EM 95% lower bound >= +0.30 percentage points;
- F1 point advantage >= +0.50 percentage points;
- F1 95% lower bound > 0;
- V2 damage count <= GbV damage count;
- positive V2-minus-GbV EM point estimate on all three datasets;
- positive V2 net correction for BM25, Dense, and Hybrid.

A >=25% damage reduction and positive V2-minus-GbV retriever-specific EM points are retained as stretch targets. These multi-condition targets are engineering success criteria, not familywise-controlled hypothesis tests.

If any formal or engineering target fails, retain the result. Do not retune, expand the cohort, change the source split, change the budget, or substitute a different selector after fresh labels are opened.
