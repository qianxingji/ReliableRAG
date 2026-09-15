# Research Lead review of the completed controls — 2026-09-11

**CAS Q2 STATUS: NOT READY.** The full stack fails its prospectively frozen
attribution rule. Preserve the ROA-FULL name and original development decision,
but do not advance it to final confirmation or claim feature-stack necessity.
HGB_GBV_R remains a control, not an automatically renamed final method.

## Executed experiment and independent acceptance

Engineering commit: `fc953b2`. Namespace:
`outputs/cas_q2/supervision_matched_controls_v1` in the isolated worktree.
Exactly 56 base fits + 56 disjoint Platt fits, across all 25 primary and 3 LODO
contexts; zero ROA refits, synthetic fits, retrieval, generation or new IDs.
Both control feature recipes and all fitting parameters follow CONTROLS_PROTOCOL.
Every primary action and the secondary allocation actions were sealed before
held-out metric computation. Primary outputs sealed before LODO fits.

Independent validation: PASS, 3,710,044 checks, max numerical error 0 at 1e-10;
56 models, 38,424 model-prediction rows and both 81,000-row aggregate ledgers
reconstructed. Exact action membership, fit-only transforms, training targets,
all fold/repetition/subgroup statistics and the decision verified. The validator
does not import the executor or fitting implementation. Original artifacts were
rechecked unchanged. SHA256_MANIFEST and SEAL preserve the complete execution.

| Seed | ROA-FULL Net / Damage | GBV_ONLY_R Net / Damage | HGB_GBV_R Net / Damage |
|---|---:|---:|---:|
| 20260917 | 302 / 12 | 237 / 15 | 291 / 10 |
| 20260918 | 300 / 12 | 241 / 16 | 294 / 6 |
| 20260919 | 293 / 15 | 240 / 14 | 292 / 9 |
| 20260920 | 297 / 15 | 242 / 15 | 290 / 8 |
| 20260921 | 305 / 11 | 238 / 12 | 296 / 7 |

ROA-FULL satisfies Net-higher/Damage-no-higher in 4/5 repetitions against
GBV_ONLY_R, and 0/5 against HGB_GBV_R. Its median EM differences are +0.437037
and +0.051852 percentage points, respectively. Against the two-input control,
LODO differences are -0.20 pp on MuSiQue and +0.066667 pp on each other dataset.
Both the primary success count and the -0.10 pp LODO floor fail for HGB_GBV_R.
The exact decision is `SIMPLER_CONTROL_COMPETITIVE_REVIEW_CONTRIBUTION`.

The secondary allocation analysis does not rescue the primary failure. Holding
ROA-FULL's per-partition dataset/retriever action counts fixed, HGB_GBV_R nets
are 293, 291, 284, 293, 291, with damages 8, 10, 10, 7, 9. It still damages fewer
answers in every repetition. This is a secondary ranking/allocation diagnostic,
not a replacement primary comparison or an equivalence test.

## Scientific interpretation

The evidence supports a small empirical tradeoff: the full stack obtains a little
more Net on this opened cohort, with consistently more Damage than the two-score
calibrator. It does not establish that every extra feature is useless, that the
methods are equivalent, or that the simple control will generalize better.

The proposed fallback contribution is an empirical investigation of how a
supervised recovery target combines an internal paired-answer score with an
external faithfulness score under a fixed switch budget. A two-input logistic
model itself is not a novel algorithm. A new name, the failed prior risk-head
search, or a better opened-data mean cannot establish a CAS Q2 contribution.

A necessary confound remains: raw HGB is not supervision-matched HGB. Therefore
the current results cannot show that GbV adds information beyond HGB plus the
same recovery labels and retriever indicators. ROA-NOGBV uses ten inputs and
does not close this minimal-control gap. The precise next design is
[HGB_ONLY_PROTOCOL.md](HGB_ONLY_PROTOCOL.md), one added control and no search.

## Related-work boundary update

These are our task-boundary judgments, not claims of comprehensive novelty
clearance. Sources were checked on 2026-09-11.

- [Generate but Verify](https://aclanthology.org/2025.ijcnlp-long.56/) explicitly
  couples answer generation with faithfulness prediction. Our paired-answer
  adaptation must remain labeled an adaptation; EM correctness is a different
  target from faithfulness.
- [TrustMargin](https://arxiv.org/html/2606.08397v1) selects between Direct and
  RAG candidates using question-only, question-plus-context and context-only
  likelihood views. The cached E0/E1 likelihood matrix lacks the first and third
  views, so it cannot provide an exact TrustMargin reproduction. Post-generation
  answer arbitration and likelihood margins are established ideas.
- [Pair-ID](https://arxiv.org/abs/2608.08944) is a recent offline paired-evidence
  response audit. Its abstract explicitly distinguishes that audit from a runtime
  repair policy. The historical paired-intervention framing must be compared
  with this work before any novelty claim; different task scope alone is not
  enough to establish contribution.
- [Doctor-RAG](https://arxiv.org/abs/2604.00865) addresses diagnosed failed agentic
  trajectories with localized repair and prefix reuse. That candidate-generation
  and known-failure setting differs from switching across all current traces.
  A changed task should not be described as its exact reproduction.

## Confirmation preparation actually completed

An ID-only inventory reused authenticated source and exclusion ledgers, adding
all 4,500 newly developmentized ROA questions to the previous 14,100-question
exclusion union. No IDs were selected and no new outcome content was read.

| Dataset | Existing source IDs | Excluded within that source | Remaining |
|---|---:|---:|---:|
| HotpotQA | 7,405 | 5,300 | 2,105 |
| 2WikiMultiHopQA | 12,576 | 5,300 | 7,276 |
| MuSiQue | 19,938 | 2,100 | 17,838 |

This is availability, not a power calculation or a complete audit of every
public split. Final candidate, fit/calibration partition, sample size and full
statistical protocol remain unfrozen. In particular, do not choose 1,500 per
dataset merely because the previous experiment did so.

P0: close the minimal HGB control, contribution and confirmation-design gaps;
retain historical training-receipt limitations. P1: current-method costs, errors,
reader transfer and exact task boundaries against recent work. P2: no additional
feature/model/budget ladder, large models or cosmetic expansion.
