# DAA-V2 development decision

Status: **development-only; not a fresh confirmatory result and not the final pre-label freeze**.

## 1. What the frozen historical ledger establishes

The historical 9,000-trace cohort is reclassified as V2 development evidence. Re-ranking the already-frozen state-symmetrized HGB score under a single global action budget yields a materially stronger operating point than the historical retriever-specific HGB thresholds.

At 370 actions, global HGB ranking produced 191 recoveries, 7 damages, and 184 net corrections. The exact historical Conservative dataset x retriever budgets, when imposed on HGB ranking, produced 173 recoveries, 17 damages, and 156 net corrections. These two diagnostics indicate that the HGB advantage has two components: stronger within-stratum ranking and better system-level allocation of actions across retrieval regimes. Neither result is prospective evidence.

The 370-action global point is positive in every dataset and retriever. In particular, Hybrid receives 107 actions and 52 net corrections under global HGB ranking rather than being nearly frozen.

## 2. Nested development validation of a damage-aware meta correction

A three-state meta model predicts recovery, damage, or neutral transition behavior from frozen label-free selector scores. Outer GroupKFold splits evaluate the candidate; inner GroupKFold predictions choose the damage penalty and fusion weight. All retriever traces from a question remain in the same fold.

Across ten grouped nested seeds (20260909--20260918):

| Budget | Candidate V2 net, median [min,max] | Raw HGB net, median [min,max] | Candidate damage, median [min,max] | Raw HGB damage, median [min,max] | Stability |
|---|---:|---:|---:|---:|---|
| 370 | 185 [181,189] | 182 [178,187] | 5 [3,6] | 7 [6,10] | V2 net better in 9/10, tied in 1/10; damage lower in 10/10 |
| 450 | 209 [206,217] | 200 [197,204] | 7.5 [6,9] | 10.5 [9,14] | V2 net better in 10/10; damage lower in 10/10 |

At 450 actions, the mean nested V2 net is 209.6 versus 200.6 for raw HGB, and mean damage is 7.4 versus 10.9. The repeated folds are sensitivity checks on one historical cohort, not independent replications.

## 3. Provisional architecture decision

The V2 method should **retain state-symmetrized HGB as the ranking backbone** and add a lightweight damage-aware correction rather than replacing HGB with a larger opaque model.

The current candidate is:

1. label-free frozen score features at runtime;
2. a three-state development model for recovery / damage / neutral behavior;
3. expected utility `p(recovery) - lambda * p(damage)`;
4. quantile-normalized fusion with the HGB backbone;
5. a single global action budget so the policy can allocate actions across retrievers.

Raw HGB must remain a mandatory ablation and fallback. The meta correction is adopted only if repeated grouped development validation continues to improve net correction and damage without relying on dataset identity.

## 4. Complexity guardrail

An exploratory dataset-identity feature improved historical development results, but it is **rejected from the primary V2 feature set** because it risks benchmark-specific coding and weakens transfer claims.

A reduced HGB + Logistic meta feature set is simpler and still improves raw HGB, but the current broader score ensemble has the strongest repeated development point estimates. Before the final freeze, the feature set should be reduced if a simpler subset preserves most of the gain. Complexity itself is not a contribution.

## 5. Primary budget decision

The preferred prospective primary action rate is **5.0%**. On a 9,000-trace reference cohort this corresponds to 450 actions. The reason is methodological rather than cosmetic: 5% is scale-free, deployment-interpretable, and the repeated nested development study shows a more stable net/damage improvement than the historical 370-action count.

The final confirmatory protocol should therefore match V2 and GbV at the same 5.0% total action budget. A secondary analysis should exactly match dataset x retriever budgets to isolate within-stratum ranking quality.

## 6. What is still required before final freeze

- Obtain or regenerate the per-trace GbV score ledger under the pinned published-baseline implementation so development comparisons can be evaluated at the same 5.0% budget.
- Finalize the smallest defensible V2 meta-feature set.
- Freeze train/calibration/fresh-ID splits, model artifacts, lambda, action budget, tie-breaking, comparator revision, statistical code, and hashes before fresh-label access.
- Run a genuinely new fresh confirmatory evaluation once. Historical results in this document may not be relabeled as confirmatory superiority.

## 7. High-standard success criterion retained

The fresh study targets a positive V2-minus-GbV EM difference at identical action volume, no increase in harmful adoption, a preferred point advantage of at least +0.60 EM percentage points, and a preferred 95% cluster-bootstrap lower bound of at least +0.30 points. These are targets, not guaranteed outcomes.
