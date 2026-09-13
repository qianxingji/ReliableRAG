# Research Plan

> Current roadmap: [CAS Q2 current task](cas_q2/CURRENT_TASK.md) and
> [current method](cas_q2/CURRENT_METHOD.md), effective 2026-09-10.
> The sections below preserve the original research hypotheses. Completed
> experiments and subsequent decisions take precedence; do not restart them.

## Working Title
Runtime Paired Evidence Interventions for Reliable RAG under Retrieval-State Lock-In

## Problem
Standard RAG systems may repeatedly retrieve a coherent but misleading evidence neighborhood. Answer self-consistency can therefore be misleading: a model may produce the same wrong answer repeatedly because all generations are conditioned on the same faulty retrieval state.

The project studies whether runtime interventions on retrieved evidence can diagnose and repair these failures.

## Initial RAG State
For question q:

E00 = R(q)
a00 = G(q, E00)

## Paired Evidence Interventions
We consider two binary interventions:
- A = targeted evidence addition
- D = dominant-state evidence masking

This produces:
- E00 = E
- E10 = E + A
- E01 = E - D
- E11 = E - D + A

Generate a_ij = G(q, E_ij), for i,j in {0,1}.

## Hypotheses
H1. Observed intervention responses provide more reliable failure diagnosis than static prediction from the original query, evidence and answer alone.

H2. Gap-targeted evidence addition recovers missing supporting facts more effectively than generic query rewriting or random evidence expansion.

H3. Dominant-state masking repairs retrieval lock-in more effectively than random deletion or score-based evidence deletion.

H4. Evidence-certified arbitration over intervention branches produces better selective reliability than majority voting or answer self-consistency.

## Innovation 1: Runtime Paired Evidence Interventions
Instead of predicting one corrective action from the original RAG trace, execute minimal counterfactual interventions and observe the reader response.

## Innovation 2: Oracle-Free Evidence Intervention Operators
Addition: identify low-coverage reasoning facets and retrieve targeted evidence.
Deletion: identify dominant retrieval clusters or anchors and temporarily mask them.

## Innovation 3: Intervention-Aware Evidence Arbitration
Use evidence support, coverage, contradiction and actual intervention response to select a candidate answer or abstain.

## Main Datasets
- HotpotQA
- 2WikiMultiHopQA
- MuSiQue

## Failure Conditions
Natural retrieval errors plus controlled stress tests:
1. Missing evidence
2. Distracting evidence
3. Mixed missing + distracting evidence
4. Retrieval-state lock-in

## Main Ablations
### Innovation 1
- Full intervention
- Static selection
- Add-only
- Delete-only
- No-joint
- Random branch

### Innovation 2: Addition
- Gap-targeted Add
- Generic Rewrite
- Multi-query
- Random Add
- No disjoint constraint

### Innovation 2: Deletion
- Dominant-state masking
- Random delete
- Lowest-score delete
- Highest-score delete
- MMR

### Innovation 3
- Full arbitration
- Majority vote
- Support-only
- No coverage
- No interaction term
- No abstention
- Self-consistency

## Metrics
Answer: EM, F1
Retrieval: Recall@K, Supporting Fact Recall@K
Reliability: Selective Accuracy, Risk-Coverage, AURC, ECE, Brier Score
Custom: Intervention Recovery Rate, Unnecessary Intervention Rate
Efficiency: retrieval calls, generation calls, runtime, token usage, peak GPU memory

## Critical Scientific Constraint
The runtime system must never access gold supporting facts. Gold evidence can only be used for evaluation, controlled dataset construction, and oracle experiments.
