# P0-C reviewer-readable method and fairness account

Decision: **PASS_REVIEWER_READABLE_METHOD_AND_FAIRNESS_ACCOUNT.** This account
describes the frozen Qwen experiment. It does not supply a new algorithm Claim,
close statistical verification, or authorize manuscript work.

## Study object and population

The unit presented to a policy is one fixed pair of answers `(a0,a1)` for a
question/retriever trace. The policy either keeps `a0` or replaces it with `a1`.
The study contains 6,000 question groups and 18,000 traces: 2,000 questions from
each of HotpotQA, 2WikiMultiHopQA and MuSiQue, each crossed with BM25, BGE dense
and hybrid RRF retrieval. All three retriever siblings of a question remain
together in sampling and statistical resampling.

The selected cohort has zero dataset/ID overlap with the known 18,600-question
exclusion union. It is a deterministic hash-ordered sample from the available
benchmark frames, not a probability sample or a semantic-decontamination proof.

## Shared candidate acquisition

One dataset-specific deduplicated corpus is built from the selected benchmark
contexts without reading answers, supporting facts or decomposition. The fixed
pools contain 19,352 HotpotQA, 11,746 2Wiki and 23,618 MuSiQue documents (54,716
total). These are bounded benchmark-derived pools, not full Wikipedia.

For each question and retrieval condition, the frozen reader/repair pipeline is:

1. retrieve the original top five documents `E0`;
2. generate `a0` from the question and `E0`;
3. generate one repair query from the question and `E0`, without `a0`;
4. rank to depth 50 with the same retriever, insert the first document absent
   from all five `E0` documents, retain original ranks 1--4 and replace rank 5
   to create `E1`;
5. generate `a1` from the question and `E1`.

All policies receive these same acquired pairs. No policy has its own retrieval,
repair or generation run. The reader is
`Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1`;
the dense encoder is
`BAAI/bge-base-en-v1.5@a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`.
The run uses frozen prompts and chat template, greedy decoding, seed 20260828,
48 answer tokens, 64 repair-query tokens and a 16,000-character evidence budget.
The accepted canonical acquisition contains 18,000 pairs and 54,000 generation
calls; a prospectively selected 180-trace replay matches exactly.

## Label-free scores available to policies

The historical 11 numeric inputs are:

1. `state_symmetric_hgb`;
2. `state_symmetric_logistic`;
3. `no_cross_state`;
4. `no_B`;
5. `no_evidence_change`;
6. `no_answer_form`;
7. `ordinary_compact_logistic`;
8. `B_rule`;
9. `higher_own_likelihood`;
10. `likelihood_margin`;
11. `gbv_margin`.

The first seven are outputs of seven byte-fixed historical upstream learned
estimators. `B_rule`, `higher_own_likelihood` and `likelihood_margin` are fixed
rule inputs. `gbv_margin=F1-F0` is the paired adaptation of Generate but Verify:
`F0` and `F1` are maximum DeBERTa entailment probabilities over chunks for the
two branches. The pinned verifier revision is
`5a4338ab2151dc8db04ad53b42b6153382bf4f99`; it uses FP32, 512 tokens, 20-word
chunk overlap and entailment label index 0.

Base scoring also uses the fixed BGE answer-pair semantic path and four Qwen
teacher-forced likelihood cells `L00,L01,L10,L11`, with answer-token-only
likelihood and an 8,192-token scoring limit. These calculations happen before
outcomes are available.

## Five supervision-matched heads

All five heads use the same 4,500 opened development questions and 13,500 traces.
Within each dataset, a frozen hash order assigns 1,200 questions to fitting and
300 to disjoint calibration: 3,600 fit and 900 calibration questions overall,
with all three retriever siblings kept together. There is no performance-based
split choice and no internal held-out Claim.

| Policy | Numeric inputs | Numeric missing flags | Retriever indicators | Final width |
|---|---|---:|---:|---:|
| ROA-FULL | inputs 1--11 | 11 | 3 | 25 |
| ROA-NOGBV | inputs 1--10 | 10 | 3 | 23 |
| HGB_GBV_R | inputs 1 and 11 | 2 | 3 | 7 |
| HGB_ONLY_R | input 1 | 1 | 3 | 5 |
| GBV_ONLY_R | input 11 | 1 | 3 | 5 |

For every head, the binary target is Recovery: normalized EM changes from
`a0=0` to `a1=1`. Numeric medians, means and population standard deviations are
fit only; zero standard deviation becomes one. Missingness indicators and the
three BM25/dense/hybrid indicators are unscaled. The base model is L2 logistic
regression (`C=1`, `lbfgs`, no class weights, `max_iter=5000`, `tol=1e-4`). A
separate Platt logistic model (`C=1e6`, `lbfgs`, `max_iter=2000`, `tol=1e-4`)
uses calibration logits only. No dataset ID, sample ID, answer text, Gold value
or future action is a predictor. The five base/Platt bundles required exactly ten
scientific fit calls and were never refit after fresh results.

## Comparators and supervision disclosure

The complete panel is Keep; raw HGB; raw paired GbV; ROA-FULL; ROA-NOGBV;
HGB_GBV_R; HGB_ONLY_R; GBV_ONLY_R; and sealed V2. The five named heads above are
supervision matched. Raw HGB, raw GbV and historical V2 have different upstream
training or rule dependencies and provide context, not matched attribution for
the two-signal Claim. HGB is an upstream score and comparator, not the top-level
model. HGB_GBV_R is an ordinary two-input empirical policy, not a novel method.

## Common eligibility and action fairness

All 18,000 traces remain in the evaluation denominator. Exactly 4,267 traces
share one common eligibility mask. Another 13,732 have equal normalized answer
pairs and one has an empty original answer; they are forced Keep for every
policy. There are no policy-specific deletions.

Each of the eight switching policies receives the same global cap
`K=round(0.05*18000)=900`. Eligible traces are ranked by the policy's frozen
score, descending, then by the stable `(dataset,retriever,sample_id)` key. Keep
selects zero actions. There is no threshold, dataset quota, retriever quota,
budget search or post-outcome action change. Five percent is an action-allocation
fraction after both candidates and all scores already exist; it is not a 5%
retrieval, generation, latency or compute budget.

## Gold firewall and evaluation order

Candidate acquisition, label-free scoring, common eligibility and all nine
policies' complete action memberships were independently checked and sealed
before outcome mapping. Only then did a separate mapper read the 6,000 selected
reference sets (6,863 reference strings) and 36,000 fixed `a0/a1` answers. It
emitted 18,000 numeric rows with only IDs and `a0_em,a1_em,a0_f1,a1_f1`; no
reference string entered the analysis artifact. A method-blind validator
independently recomputed all 72,000 scalar outcomes. The later analysis read
accepted numeric outcomes and frozen actions, performed no fit, retrieval,
generation or model forward, and could not amend an action.

## Fairness and reproducibility limits

- The comparison among the five supervised heads is supervision matched; raw
  HGB, raw GbV and V2 are not substitutes for those attribution controls.
- Intervals condition on fixed fitted heads and the realized candidate pools.
- The seven upstream learned estimators' saved bytes and reconstructed historical
  membership are authenticated, but their original per-estimator fit-time
  ID/matrix receipts and an independent original-fit witness are missing.
- The Qwen/BGE generation replay covers 180 of 18,000 traces; downstream saved
  neural witnesses are completely checked, but this is not another independent
  full neural-forward run.
- One reader, bounded benchmark pools and fixed retrieval conditions do not prove
  reader transfer, unseen-domain transfer or deployment generality.

Primary evidence: `../cas_q2/EMPIRICAL_REPLICATION_PROTOCOL_V1.md`,
`../cas_q2/EMPIRICAL_AB_ACCEPTANCE.md`,
`../cas_q2/EMPIRICAL_C3_EXECUTION_ACCEPTANCE.md`,
`../cas_q2/C3_VALIDATION_V3_2_FINAL_ACCEPTANCE.md`,
`../cas_q2/C4_COMPLETE_PRELABEL_ACCEPTANCE.md`,
`../cas_q2/C4_POLICIES_ACCEPTANCE.md` and
`../cas_q2/EMPIRICAL_OUTCOME_ACCEPTANCE.md`.

**CAS Q3 STATUS: NOT READY.** P0-C is closed. P0-D through P0-I remain.
