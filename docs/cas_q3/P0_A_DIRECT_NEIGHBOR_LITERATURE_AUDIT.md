# P0-A direct-neighbor literature and contribution audit

Audit date: 2026-09-13 (Asia/Shanghai)

Decision: **PASS FOR BOUNDED EMPIRICAL POSITIONING; METHOD-NOVELTY CLAIM
REJECTED.** Independent closure receipt:
`P0_A_P0_B_ASTRA_XHIGH_RECHECK.md`.

This audit closes P0-A after independent Astra xhigh recheck. It does not certify
journal fit, acceptance probability or manuscript readiness. The search covered
the final empirical question and its nearest task families using primary paper
pages from ACL Anthology, OpenReview and arXiv. The relevant cutoff is the audit
date; later work requires an update before submission.

## Final empirical question

Given an already generated original/repaired RAG answer pair from one fixed
reader, can a supervision-matched selector combine an internal paired-answer
score (HGB) and an adapted external faithfulness score (GbV) to improve exact
match while reducing damage to originally correct answers, relative to each
single-signal supervised selector, under one global 5% action allocation?

This is an empirical attribution and harm-accounting question. HGB_GBV_R is a
two-input calibrated logistic policy, HGB is an upstream score, and GbV is an
adapted published verifier. None is a new top-level algorithm.

## Direct-neighbor matrix

| Work | Closest overlap | Material boundary for this study | Audit consequence |
|---|---|---|---|
| [Generate but Verify](https://aclanthology.org/2025.ijcnlp-long.56/) | Couples answer generation with explicit faithfulness prediction and fallback/corrective use. | Its principal object is Answering with Faithfulness and faithfulness precision/recall. This study adapts its signal to an already generated answer pair and evaluates EM Recovery/Damage under matched supervision. | GbV must be described as an adaptation. No claim that generation-plus-verification or corrective use is new. |
| [TrustMargin](https://arxiv.org/abs/2606.08397) | Post-generation answer-level arbitration between two candidates from the same frozen model using likelihood views. | It selects Direct versus RAG without training; this study selects original versus evidence-repaired RAG answers with supervised calibration and a fixed batch action cap. | Post-generation arbitration and likelihood-margin selection are established. TrustMargin is a mandatory conceptual comparator even though the cached score matrix cannot reproduce all of its required views. |
| [Predicting the Benefit of Retrieval Augmentation in Open-Domain QA, v3 (2026-08-19)](https://arxiv.org/html/2604.07985v3) ([version record](https://arxiv.org/abs/2604.07985v3)) | Supervised post-generation prediction of RAG benefit over a no-RAG response. Section 4.3.1 uses the difference between NLI entailment scores for two answers; §4.3.2 Bert-Gen-2A reads both RAG and no-RAG answers; §7 evaluates predicted-gain-driven Selective RAG. | This study instead holds fixed original-RAG/repaired-RAG candidates, uses matched single- and two-signal training recipes, allocates exactly 900 actions globally, reports full-population correctness and Damage, and retains failed comparisons. | Two-candidate input, post-generation choice, NLI-score difference, supervised benefit prediction and predicted-gain selection are established. The paper cannot claim novelty for any of them and has not shown numeric superiority to Bert-Gen-2A. |
| [D2R-RAG](https://arxiv.org/abs/2606.29377) | Diagnoses RAG failures and selects corrective actions under explicit latency and VRAM budgets. | It chooses among adaptive repair operations using observable signals; this study audits keep/repair selection after both candidates already exist and its 5% cap is an action allocation, not a compute budget. | “Budget-aware RAG repair” and “resource-aware repair” are unavailable novelty claims. The acquisition-cost limitation must be prominent. |
| [When Should LLMs Search?](https://arxiv.org/abs/2607.05752) | Uses paired no-search/forced-search outcomes as counterfactual supervision for an instance-level action router. | It routes SEARCH/NO SEARCH before the searched answer exists; this study selects between already generated original/repaired outputs. | Outcome-derived supervision for intervention routing is established. Do not claim counterfactual-supervision novelty. |
| [Pair-ID](https://arxiv.org/abs/2608.08944) | Holds query, retrieval state and reader fixed while measuring paired response to evidence interventions. | Pair-ID is an offline failure audit over evidence addition/deletion, not a runtime selector; this study evaluates a selector on a separately frozen Qwen cohort. | Paired-evidence intervention and reader-conditional response are established. The runtime-policy distinction is real but insufficient for a method-novelty claim. |
| [Doctor-RAG](https://arxiv.org/abs/2604.00865) | Diagnoses failures and performs localized repair with prefix reuse on multi-hop agentic RAG. | It operates on known failed trajectories and repairs the earliest failed step; this study allocates keep/repair actions across all fixed traces. | Diagnosis-guided selective repair and efficiency framing are established; the task/population boundary must be explicit. |
| [CRAG](https://arxiv.org/abs/2401.15884) | Evaluates retrieval quality and triggers different corrective retrieval actions. | CRAG changes evidence and regeneration before the final answer; this study chooses between two already acquired answers. | Corrective RAG is established. Do not present a generic corrective pipeline contribution. |
| [Self-RAG](https://openreview.net/forum?id=hSyW5go0v8) | Learns retrieval and critique tokens and uses reflection scores to control generation. | Self-RAG trains the generator and interleaves retrieval, critique and generation; this study freezes the reader and fits only a selector. | Adaptive retrieval/critique is established; the present work is a controlled downstream audit. |
| [Adaptive-RAG](https://aclanthology.org/2024.naacl-long.389/) | Trains a classifier to route questions among no-, single- and multi-step retrieval strategies. | It routes by question complexity before candidate generation; this study ranks already generated paired interventions. | Learned instance routing is established. |
| [Self-Knowledge Guided Retrieval Augmentation](https://aclanthology.org/2023.findings-emnlp.691/) | Learns when retrieval helps because retrieved knowledge can harm an original response. | It chooses whether to retrieve; this study exposes Recovery and Damage after a specific repair candidate has been generated. | “Avoiding retrieval harm by selective use” is established. |
| [Verify-and-Edit](https://aclanthology.org/2023.acl-long.320/) | Uses verification, retrieval and post-editing to correct low-consistency reasoning chains. | It changes reasoning and regenerates an answer; this study performs no further edit after the fixed repaired candidate. | Verification-triggered answer repair is established. |
| [Detrimental Contexts in Open-Domain QA](https://aclanthology.org/2023.findings-emnlp.776/) and [The Distracting Effect](https://aclanthology.org/2025.acl-long.892/) | Show that retrieved passages can reduce reader accuracy and study harmful/distracting context. | They study context-level harm and filtering/training; this study measures answer-level Damage from executing a fixed repair. | Retrieval harm is established motivation, not a new discovery. |

## Contribution decision

The literature does not support any of these claims:

- a new selector architecture, verifier-fusion method or risk-control method;
- the first post-generation RAG arbitration or keep/repair policy;
- the first supervised predictor of intervention benefit;
- the first budget-aware, selective or corrective RAG framework;
- a deployment-cost saving from a 5% action allocation;
- universal complementarity of internal and external verification signals.

The defensible contribution is a **controlled empirical result and boundary**:

1. supervision-matched single-signal and two-signal selectors are evaluated on
   the same fixed answer pairs, eligibility rule, development recipe and global
   action count;
2. full-population Recovery, Damage, Neutral, EM and token F1 prevent a favorable
   average from hiding damage to originally correct answers;
3. the frozen Qwen study supports HGB_GBV_R over GBV_ONLY_R on the joint EM/Damage
   rule, while transparently failing the same rule against HGB_ONLY_R and
   rejecting ROA-FULL complexity;
4. the two signal increments have comparison-dependent evidence: adding HGB to
   GbV passes the joint EM/Damage rule, whereas adding GbV to HGB does not. In
   the latter comparison, the reallocated primary Damage endpoint is favorable,
   EM is inconclusive, and the fixed-action Damage upper bound touches zero.

These comparisons do not establish a joint gain from adding the external GbV
verifier to HGB, do not show that GbV is useless, and do not test an interaction,
causal mechanism or difference between the two incremental effects.

This gap is potentially publishable as a Q3 empirical paper because the matched
controls, global allocation and negative result make the attribution more
informative than another point-estimate selector leaderboard. It remains narrow:
one reader, three fixed dataset-specific bounded candidate pools shared across
policies and retrieval conditions within each dataset, one realized
candidate-generation pipeline, and no independent population replication. A
reviewer may reasonably judge the effect too small or
the distinction from supervised gain prediction and budgeted repair too slight.

## Required positioning language

Use “we conduct,” “we test,” “we find” and “under the evaluated setting.” Do not
use “we propose a novel framework,” “state of the art,” “risk guarantee,”
“generalizable,” “cost-efficient” or “reader-agnostic.” The primary positive
sentence must name Qwen, the three datasets/retrievers, the fixed candidate pools,
the global 5% action allocation and GBV_ONLY_R. The adjacent sentence must state
that the joint rule did not pass against HGB_ONLY_R.

**CAS Q3 STATUS: NOT READY.** P0-A and P0-B are closed by the independent Astra
xhigh recheck. P0-C is closed; P0-D through P0-I, especially target-journal fit
and final independent Claim review, remain.
