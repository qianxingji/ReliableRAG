# Research Lead decision after the frozen fresh empirical study

**CAS Q2 STATUS: NOT READY.**

Decision: **ROA-FULL ADVANCEMENT REJECTED; TWO-SIGNAL EMPIRICAL EFFECT PARTLY
SUPPORTED; NO NOVEL FINAL CANDIDATE CLEARED.** The complete fresh study confirms
that a supervision-matched HGB+GbV recovery policy can outperform its GbV-only
counterpart under the fixed batch intervention budget. It does not establish
that ROA-FULL improves on the simpler fusion, or that fusion improves EM over
HGB-only. HGB_GBV_R remains the prospectively focal empirical policy and a
comparison object, not a newly invented algorithm or a post-outcome replacement
candidate.

## Primary results and allowed conclusions

All differences below use the fixed 18,000-trace batch and the prespecified
20,000-draw dataset-stratified question-cluster bootstrap. Ranges are the six-
endpoint Bonferroni-adjusted percentile ranges under draw-level reallocation.

| Primary comparison | EM difference, pp [adjusted range] | Damage-rate difference, pp [adjusted range] | Joint rule |
|---|---:|---:|---|
| ROA-FULL − HGB_GBV_R | +0.0444 [−0.1333, +0.2037] | +0.0611 [+0.0000, +0.1278] | Not met |
| HGB_GBV_R − HGB_ONLY_R | +0.0556 [−0.1556, +0.3167] | −0.0833 [−0.1833, −0.0056] | Not met |
| HGB_GBV_R − GBV_ONLY_R | +0.2333 [+0.0722, +0.4333] | −0.0722 [−0.1444, −0.0278] | Met |

The same-draw fixed-action sensitivity preserves the only joint positive result:
fusion minus GBV-only has EM range `[+0.0389,+0.4278]` and Damage range
`[-0.1389,-0.0222]` pp. It does not rescue either failed joint comparison.

The allowed primary claim is narrow: **on this independently held-out cohort,
with one fixed Qwen reader, three datasets, three retrievers, one shared candidate
pool and a global 5% action budget, the supervision-matched HGB+GbV selector
improves EM and reduces Damage relative to the supervision-matched GbV-only
selector.** This supports complementarity relative to GbV-only in the sampled
population. It does not establish a universal verifier-fusion benefit, unseen-
domain transfer, reader transfer, formal risk control or a novel algorithm.

ROA-FULL has the largest point EM/F1 gain over Keep (`+1.9389/+2.5781` pp), but
it gains only eight more correct answers than HGB_GBV_R and incurs eleven more
Damage events. Its adjusted EM range crosses zero and its Damage difference is
not favorable. A point-estimate ranking cannot override the primary comparison.
Failure to reject also does not prove equivalence.

HGB_GBV_R reduces Damage relative to HGB_ONLY_R in the primary reallocated
analysis, but the EM interval crosses zero and the fixed-action adjusted Damage
range touches zero. The evidence therefore does not satisfy the joint rule for
incremental two-signal benefit over HGB-only. The earlier 2Wiki LODO floor
failure remains visible and prevents a transport or robustness claim.

All eight switching policies improve EM and token-F1 over Keep descriptively,
with overall EM gains from `+1.6278` to `+1.9389` pp. These Keep comparisons did
not belong to the six primary interval family, so the report must present them
as fixed-batch point estimates rather than new significance claims. Dataset and
retriever cells are descriptive under globally allocated actions; no cell may
be promoted as a confirmatory subgroup.

## Contribution and candidate decision

The original complexity claim fails on fresh data consistently with the earlier
development attribution result. ROA-FULL is not advanced. HGB_GBV_R is a simple
two-input calibrated logistic policy using existing HGB and the paired GbV
adaptation. Its positive result against GBV_ONLY_R is scientifically useful, but
ordinary supervised fusion and post-generation arbitration are established
ideas. The current evidence supports a controlled empirical attribution/tradeoff
study, not a method-novelty paper.

No final novel-method candidate is cleared. For any next independent replication,
HGB_GBV_R remains the fixed focal empirical object because it was named before
fresh outcomes and has the lowest observed overall Damage rate (`0.0611` pp)
with near-top EM/F1. This is a study-design choice grounded in its prespecified
role, not a post-hoc claim that it is globally optimal. ROA-FULL remains the
complexity comparator; HGB_ONLY_R, GBV_ONLY_R, raw HGB/GbV, ROA-NOGBV, V2 and
Keep remain required context.

## Next design gate

Do not run another same-reader split merely to seek significance. Before any
new model call or Gold read, freeze one independent replication axis justified
by the empirical claim, preferably a second reader family or a genuinely new
benchmark population. The design must audit local model/data availability,
exclude every opened ID, predeclare one fit/calibration recipe and action budget,
retain all failed/null comparisons, and power the two primary joint comparisons
that remain scientifically informative: fusion versus HGB-only and fusion versus
GbV-only. ROA-FULL versus fusion remains a complexity audit, with no superiority
assumption.

The next protocol must specify the target estimand, reader/population, exact
sample size, multiplicity family, failure handling, cost boundary and stopping
rule before implementation. It must not tune features, model class, score
orientation, budget, seeds or subgroup selection on the current outcomes.

P0: independent-axis availability/provenance audit, literature/Claim boundary,
and a frozen replication protocol or an explicit stop decision if the evidence
cannot support a CAS Q2 empirical contribution. P1: standalone deployment cost,
cross-reader/population robustness, contamination limits and complete public
replay packaging. P2: manuscript drafting and journal targeting only after the
contribution and evidence plan are accepted.
