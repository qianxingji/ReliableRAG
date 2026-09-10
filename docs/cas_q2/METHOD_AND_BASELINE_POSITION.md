# Method and baseline position — 2026-09-10

This is a Research Lead assessment, not manuscript prose or a claim of novelty
acceptance. It uses the authenticated ROA report, current source and the primary
sources below. No new scientific experiment was run.

## A method issue that claim wording must resolve

ROA ranks predicted Recovery probability. For binary normalized EM transitions,
the expected improvement from switching one answer is:

`E[EM_after - EM_before | x, switch] = P(Recovery | x) - P(Damage | x)`.

Therefore ranking Recovery alone does not generally maximize expected Net or
guarantee low Damage. For example, with one allowed switch, candidate A with
(Recovery, Damage, Neutral)=(0.60,0.39,0.01) ranks above B=(0.50,0.01,0.49) by
Recovery, but their expected gains are 0.21 and 0.49. This is an algebraic
counterexample, not project data or an empirical result.

The defensible current question is whether a simple Recovery score works well
empirically at the fixed budget, given these upstream signals and data. The
observed development Damage advantage supports an empirical observation only.
The inconclusive dual-head stage does not prove that damage estimation is
theoretically unnecessary. Do not claim Bayes optimality, a risk guarantee, or
universal superiority of the recovery-only objective.

This issue does not yet justify reopening the rejected risk/MILP searches.
Retain ROA while resolving the already frozen contribution controls. If they
support the full method, explain the empirical regime and its failures. If not,
revisit the contribution before final confirmation; do not rename ordinary
supervised stacking as a new theoretical principle.

## Relevant primary sources and task boundaries

| Work | Supported source-level characterization | Implication for ReliableRAG |
|---|---|---|
| [Generate but Verify](https://aclanthology.org/2025.ijcnlp-long.56/) | Couples answer generation with faithfulness prediction and evaluates faithfulness-aware downstream use. | Keep the current paired adaptation visible and name it as an adaptation. Correctness under normalized EM is not identical to evidence faithfulness. |
| [TrustMargin](https://arxiv.org/abs/2606.08397) | Its indexed arXiv abstract describes training-free selection between Direct and RAG answers using model likelihood margins. Full text was not retrievable in this continuation. | Answer-level arbitration and likelihood-margin selection are prior ideas. Original-versus-repaired RAG pairs differ from Direct-versus-RAG pairs; do not label a changed candidate domain an exact reproduction. |
| [SURE-RAG, v2](https://arxiv.org/abs/2605.03534v2) | Studies support/refutation/insufficiency verification, aggregating claim-evidence relations into a selective answering score; its reported external-task comparison reverses the ranking. | Aggregating verifier signals and adding calibration are not, by themselves, a convincing novelty claim. Evidence sufficiency/abstention and budgeted answer switching require different evaluation. |

These implications are our inferences from the described tasks, not claims made
by the cited authors about ReliableRAG. This is a targeted boundary check, not a
systematic literature review or proof that all competing methods are covered.

## Priority decision

- P0: supervised GbV-only and HGB+GbV controls, already designed. They directly
  test whether the full feature stack adds value beyond labels and verifier input.
- P0: retain raw HGB, the GbV paired adaptation and all negative dependence/LODO
  findings. A favorable external comparison alone does not establish contribution.
- P1: after source access, check whether the cached likelihood quantities permit
  a faithful comparison to the relevant TrustMargin components without new
  generation. Record exact mathematical/candidate-domain differences first;
  do not claim a TrustMargin result from an existing differently defined margin.
- P2: no automatic full reimplementation of unrelated retrieval-generation or
  abstention systems solely to increase the number of baseline names.

The current innovation claim remains **not established**. A supported benchmark
advantage is necessary evidence for this route, but is not by itself a scientific
contribution or a guarantee of CAS Q2 acceptance.
**CAS Q2 STATUS: NOT READY.**
