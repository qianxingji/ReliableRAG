# Current method and claim boundary

The current paper object is an empirical audit. The author selected the following
title on 2026-09-16:

**Selecting Between Original and Repaired RAG Answers: A Controlled Study of
Accuracy and Harmful Replacements**

The preceding working title was `Supervision-Matched Selection of Paired RAG
Repairs: An Empirical Study of Accuracy and Damage`.
`Repair or Preserve? A Supervision-Matched Audit of Paired RAG Repair under Harm
and Action Budgets` was the earlier Q2 working title. The title change is
editorial; the scientific claim boundaries and pending acceptance gates remain.

The [P0-A direct-neighbor audit](P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md)
rejects method novelty and accepts the bounded empirical gap. The
[P0-B result/Claim map](P0_B_RESULT_CLAIM_MAP.md) is the numeric reporting
authority. Both are closed by the independent
[Astra xhigh recheck](P0_A_P0_B_ASTRA_XHIGH_RECHECK.md).
The [P0-C method/fairness account](P0_C_METHOD_FAIRNESS_ACCOUNT.md) is the
reviewer-readable execution and supervision authority.
The [P0-D statistical verification](P0_D_STATISTICAL_STATEMENT_VERIFICATION.md)
is the authority for units, interval roles, multiplicity and the joint rule.
The [P0-E disclosure boundary](P0_E_PROVENANCE_CONTAMINATION_ADAPTATION_FAILURE_DISCLOSURES.md)
is mandatory for provenance, contamination, GbV adaptation and failed-reader
reporting.
The [P0-F cost table](P0_F_CLAIM_SCOPED_COST_TABLE.md) is the only allowed
workload/cost authority and prohibits standalone speed or 5%-compute Claims.

For each already generated original/repaired answer pair `(a0, a1)`, a policy
chooses Keep or Repair under a fixed 5% full-batch action allocation. The study
measures full-population normalized EM, token F1, Recovery, Damage, Neutral and
cost. All supervised comparison heads use the same development fit/calibration
roles, candidates, eligibility, action budget and canonical tie rule.

HGB_GBV_R is the focal empirical fusion policy. HGB is an upstream signal and
comparator. Neither is an independently established new algorithm. The strongest
primary attribution comparisons are:

- HGB_GBV_R minus HGB_ONLY_R: the conditional increment from adding GbV to HGB;
- HGB_GBV_R minus GBV_ONLY_R: the conditional increment from adding HGB to GbV.

On the accepted Qwen study, only the second comparison passes the frozen joint
EM/Damage rule. The first does not. ROA-FULL does not improve on HGB_GBV_R under
its advancement rule and remains rejected. The supportable finding is therefore
comparison-dependent signal value and a harm/cost boundary, not universal fusion
superiority or a novel top-level method.

The evidence covers the named Qwen reader, HotpotQA, 2WikiMultiHopQA and MuSiQue,
the fixed BM25/dense/hybrid retrieval conditions, the frozen candidate generation
and scoring implementation, and the selected 6,000-question cohort. It does not
establish broad reader transfer, independent population replication, a formal
risk guarantee, zero-shot system transfer or complete historical training
provenance.

Phi scientific use is closed by
`../cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md`. Mistral
engineering is closed by
`../cas_q2/MISTRAL_EMPIRICAL_EXTENSION_PROTOCOL_GO_STOP_REVIEW.md`. These
failures and unexecuted plans are reported as limitations and do not enter the
Qwen effect estimates.

**CAS Q3 STATUS: NOT READY.**
