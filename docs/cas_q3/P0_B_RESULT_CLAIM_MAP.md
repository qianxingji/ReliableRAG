# P0-B complete result and Claim map

Decision: **PASS_COMPLETE_FROZEN_QWEN_RESULT_CLAIM_MAP.** Independent closure
receipt: `P0_A_P0_B_ASTRA_XHIGH_RECHECK.md`. This map reports and binds the
accepted Qwen result universe. It does not independently revalidate
the statistical implementation (P0-D), authorize manuscript drafting or establish
Submission Ready.

## Authoritative result bindings

- Population: 6,000 question groups and 18,000 traces; 2,000 questions from each
  of HotpotQA, 2WikiMultiHopQA and MuSiQue, crossed with BM25, dense and hybrid
  retrieval.
- Reader: `Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1`,
  the single frozen Qwen condition accepted in
  `../cas_q2/EMPIRICAL_D_ACCEPTANCE.md`.
- Candidate pools: three fixed dataset-specific bounded pools, shared across
  compared policies and retrieval conditions within each dataset: HotpotQA
  19,352, 2WikiMultiHopQA 11,746 and MuSiQue 23,618 documents (54,716 total).
- Global action cap: `K=900`, or 5% of all 18,000 trace rows. Every non-Keep
  policy executes exactly 900 fixed actions.
- Point estimates:
  `outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json`, SHA-256
  `b03ddad8fa35f582a63403c029942104c3f5da1a961110edc2a62f09871f4d3b`.
- Intervals:
  `outputs/cas_q2/empirical_analysis_v1/INTERVALS.json`, SHA-256
  `6d454afeec7c125c0cc4d182556af6db214a867aa4f62f7a6fbd1e6e22b09331`.
- Analysis manifest:
  `outputs/cas_q2/empirical_analysis_v1/SHA256_MANIFEST.json`, SHA-256
  `498b83e75538032de3711bd6ce190eac049631d8393c875744d83aa0318097f6`.
- Research interpretation: `../cas_q2/P0_3_FRESH_RESULT_DECISION.md`.

EM, token F1 and Damage rate are percentages below; deltas and comparison ranges
are percentage points (pp). Recovery, Damage count and Neutral count only
executed switches. Recovery is an executed 0-to-1 normalized-EM change; Damage
is an executed 1-to-0 normalized-EM change; Neutral is any other executed switch
and does not mean unchanged F1. Net is Recovery minus Damage count.
`Damage rate (%) = 100 * Damage count / 18,000`, rather than division by 900 or
the 3,238 originally correct traces. `Delta EM (pp) = 100 * (Recovery - Damage
count) / 18,000`. P0-A's earlier term “Rescue” denotes the same 0-to-1 event and
is standardized here as Recovery. A signal named faithfulness does not imply
that EM/Damage validates a faithfulness improvement.

## Complete nine-policy context

| Policy | Actions | Recovery | Damage count | Neutral | Net | EM (%) | Delta EM (pp) | F1 (%) | Delta F1 (pp) | Damage rate (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Keep | 0 | 0 | 0 | 0 | 0 | 17.9889 | 0.0000 | 22.7207 | 0.0000 | 0.0000 |
| HGB | 900 | 366 | 32 | 502 | 334 | 19.8444 | 1.8556 | 25.1593 | 2.4386 | 0.1778 |
| GbV | 900 | 318 | 25 | 557 | 293 | 19.6167 | 1.6278 | 24.8928 | 2.1722 | 0.1389 |
| ROA-FULL | 900 | 371 | 22 | 507 | 349 | 19.9278 | 1.9389 | 25.2988 | 2.5781 | 0.1222 |
| ROA-NOGBV | 900 | 355 | 38 | 507 | 317 | 19.7500 | 1.7611 | 25.0321 | 2.3115 | 0.2111 |
| HGB_GBV_R | 900 | 352 | 11 | 537 | 341 | 19.8833 | 1.8944 | 25.2780 | 2.5574 | 0.0611 |
| HGB_ONLY_R | 900 | 357 | 26 | 517 | 331 | 19.8278 | 1.8389 | 25.1323 | 2.4117 | 0.1444 |
| GBV_ONLY_R | 900 | 323 | 24 | 553 | 299 | 19.6500 | 1.6611 | 24.9344 | 2.2137 | 0.1333 |
| V2 | 900 | 361 | 28 | 511 | 333 | 19.8389 | 1.8500 | 25.1712 | 2.4506 | 0.1556 |

All eight switching-policy comparisons with Keep are fixed-batch descriptive
point estimates. They were not members of the six-endpoint primary interval
family and cannot be presented as eight confirmatory improvements.

## Complete six-endpoint primary family

The primary analysis uses 20,000 dataset-stratified question-cluster bootstrap
draws and reallocates each policy's global top-K within every draw. The adjusted
percentile range uses quantiles 0.0041666667 and 0.9958333333 for the family of
six endpoints.

| Ordered comparison | Endpoint | Point (pp) | Adjusted range (pp) | Direction | Joint rule |
|---|---|---:|---:|---|---|
| ROA-FULL - HGB_GBV_R | EM | +0.0444 | [-0.1333, +0.2037] | inconclusive | Not met |
| ROA-FULL - HGB_GBV_R | Damage | +0.0611 | [+0.0000, +0.1278] | inconclusive | Not met |
| HGB_GBV_R - HGB_ONLY_R | EM | +0.0556 | [-0.1556, +0.3167] | inconclusive | Not met |
| HGB_GBV_R - HGB_ONLY_R | Damage | -0.0833 | [-0.1833, -0.0056] | favorable reduction | Not met |
| HGB_GBV_R - GBV_ONLY_R | EM | +0.2333 | [+0.0722, +0.4333] | favorable increase | **Met** |
| HGB_GBV_R - GBV_ONLY_R | Damage | -0.0722 | [-0.1444, -0.0278] | favorable reduction | **Met** |

The event-count differences behind the three ordered comparisons are respectively
`(+8 Net,+11 Damage)`, `(+10 Net,-15 Damage)` and `(+42 Net,-13 Damage)`.

## Same-draw fixed-action sensitivity

This sensitivity multiplies the originally frozen action memberships by the same
bootstrap multiplicities. It is secondary and cannot replace the reallocated
primary analysis.

| Ordered comparison | EM adjusted range (pp) | Damage adjusted range (pp) | Joint rule |
|---|---:|---:|---|
| ROA-FULL - HGB_GBV_R | [-0.1333, +0.2278] | [+0.0000, +0.1278] | Not met |
| HGB_GBV_R - HGB_ONLY_R | [-0.2000, +0.3111] | [-0.1722, +0.0000] | Not met |
| HGB_GBV_R - GBV_ONLY_R | [+0.0389, +0.4278] | [-0.1389, -0.0222] | **Met** |

## Claim registry

| ID | Status | Allowed statement | Required evidence/boundary |
|---|---|---|---|
| C1 | Primary, supported | On the fixed 6,000-question Qwen cohort, under the shared candidates and global 5% action cap, HGB_GBV_R improves EM and reduces Damage relative to supervision-matched GBV_ONLY_R. | Both adjusted primary ranges exclude zero in the favorable direction. Name reader, cohort, retrieval conditions and comparator. |
| C2 | Primary, unsupported | HGB_GBV_R jointly improves EM and Damage relative to HGB_ONLY_R. | **Do not assert.** EM crosses zero; fixed-action Damage touches zero. |
| C3 | Primary, unsupported | ROA-FULL improves on HGB_GBV_R. | **Do not assert.** EM crosses zero and Damage is not favorable. ROA advancement remains rejected. |
| C4 | Descriptive | Every switching policy has a positive point EM/F1 delta from Keep. | Report as point estimates only; no new significance language. |
| C5 | Descriptive | Among the eight switching policies that each execute 900 actions, HGB_GBV_R has the lowest observed full-population Damage count/rate and near-top point EM/F1; Keep has zero Damage. | Observed ranking only; no optimality, overall harmlessness or transport claim. |
| C6 | Method boundary | HGB_GBV_R is a two-input supervised empirical policy using existing HGB and adapted GbV signals. | No novel-algorithm, necessity or universal-fusion wording. |
| C7 | Population boundary | Evidence covers the exact named Qwen reader, 6,000 question groups expanded to 18,000 traces by three retrieval conditions, and three fixed dataset-specific bounded candidate pools shared within each dataset. | The 18,000 traces are not independent questions. No reader transfer, full-Wikipedia corpus, unseen-domain, independent-population or reader-agnostic claim. |
| C8 | Statistical boundary | Adjusted ranges quantify resampling variation conditional on fixed models and realized candidate pools. | No model-training uncertainty, exact coverage, equivalence or noninferiority interpretation. |
| C9 | Cost boundary | All policies share already incurred retrieval, generation and scoring work; 900 actions are an allocation count. | No 5%-compute, deployment speedup or standalone-policy latency claim. |

## Frozen secondary and negative evidence

The authoritative JSON locations are:

| Reported object | Sealed JSON location |
|---|---|
| Nine-policy totals | `POINT_ESTIMATES.json: policies.<policy>` |
| Three ordered point comparisons | `POINT_ESTIMATES.json: comparisons[]`, matched by `left/right` |
| Primary intervals | `INTERVALS.json: reallocated.comparisons[].endpoints.<endpoint>` |
| Fixed-action sensitivity | `INTERVALS.json: fixed_action.comparisons[].endpoints.<endpoint>` |
| Dataset/retriever/cross cells | `POINT_ESTIMATES.json: fixed_global_action_breakdowns.dataset / retriever / dataset_x_retriever` |
| Secondary 95% intervals | Each endpoint's `secondary_unadjusted_95_range_pp` |

- Dataset, retriever and dataset-by-retriever tables in `POINT_ESTIMATES.json`
  remain descriptive because actions were allocated globally. No favorable cell
  can be promoted to a confirmatory subgroup.
- The unadjusted 95% ranges in `INTERVALS.json` are secondary. The adjusted
  primary family controls the directional Claim decision.
- Failure to pass C2 or C3 is not evidence of equivalence, noninferiority or zero
  effect.
- Phi V4 failed its frozen semantic gate and Mistral never reached engineering;
  neither contributes a row, replication or robustness result.
- The seven original per-estimator fit-time ID/matrix receipts and an independent
  original-fit witness remain missing historical provenance evidence.
- Canonical C2/C3 accelerator peaks, standalone policy latency, unified
  end-to-end latency and FLOPs remain unmeasured.

**CAS Q3 STATUS: NOT READY.** P0-A through P0-C are closed. P0-D through P0-I
remain mandatory.
