# DAA-V2 high-standard experiment freeze draft

This branch is reserved for a prospective V2 post-repair arbitration experiment. No fresh-test labels may be used for model, feature, budget, threshold, sample-size, source-split, or hyperparameter selection.

## Scientific objective

Primary objective: at a predeclared matched intervention budget, outperform the published Generate-but-Verify paired NLI comparator on held-out fresh question IDs while not increasing measured harmful adoption.

## Development status

The historical 9,000-trace evaluation is development-only evidence for V2. It must not be reused as the confirmatory superiority test.

A retrospective frozen-ledger diagnostic found that global ranking by the existing state-symmetrized HGB score is materially stronger than the historical retriever-specific operating thresholds. At 370 actions, global HGB ranking yielded 191 recoveries, 7 damages, and 184 net corrections on the historical cohort. Exact Conservative stratum budgets applied to HGB yielded 173 recoveries, 17 damages, and 156 net corrections. These diagnostics are exploratory and must not be presented as fresh confirmatory evidence.

Repeated grouped nested development validation supports a lightweight three-state damage-aware correction on top of HGB. At a 5.0% reference budget (450 of 9,000 traces), the candidate improved net correction over raw HGB in all ten development seeds and lowered damage in all ten. Repeated folds are sensitivity analyses on one historical cohort, not independent replications.

## Prospective design to freeze before fresh-label access

- Train / calibration / fresh confirmatory test must be isolated at question-ID level.
- Candidate answers and repair outputs must be generated without gold labels.
- Primary comparator: published Generate-but-Verify paired NLI adaptation.
- Primary system-level comparison: identical total replacement budget for V2 and GbV.
- Secondary fairness comparison: identical dataset x retriever action budgets.
- Primary metric: paired EM difference V2 minus GbV, clustered by question ID.
- Key secondary metrics: token F1 difference, recovery, damage, net correction, action recovery precision, system damage rate.
- Report 95% question-cluster bootstrap intervals using a predeclared seed and shared bootstrap draws.
- No dataset, retriever, or subgroup may be removed after labels are opened.
- No post-label change to score definition, feature schema, action budget, tie-breaking, comparator implementation, source split, or sample size.

## Fresh cohort size and source plan

The preferred confirmatory target is **4,500 unique fresh questions: 1,500 per dataset and 13,500 retriever-conditioned traces**. This target is motivated by an empirical precision calculation from the historical same-budget Conservative-versus-GbV paired interval; see `docs/V2_SAMPLE_SIZE_PLAN.md`. The calculation is a planning approximation, not a formal power guarantee.

The exact count is not frozen until an identifier-only availability audit passes. If any dataset cannot supply the requested count, the pipeline must stop before generation. A reduced count or alternative source requires an explicit prospective amendment; it must never be chosen after seeing fresh model outputs or labels.

Preferred sources:

- HotpotQA: genuinely unused distractor-validation IDs; expand the runtime-only projection beyond the current 4,000-row materialization if required.
- 2WikiMultiHopQA: genuinely unused corrected `dev.json` IDs.
- MuSiQue: genuinely unused `musique_ans_v1.0_train.jsonl` IDs, excluding the historical 600-question MuSiQue development set. The 2,417-row answerable dev source is too heavily consumed by previous main/operator/fresh contributor allocations for a new 1,500-question strict-fresh evaluation.

Previously label-opened Fresh-ID evaluation questions are forbidden. For the strongest freshness claim, prior corpus-only contributor IDs are also forbidden as new evaluation questions.

## High-standard success targets

The formal primary superiority statement is the predeclared paired EM interval criterion. The stronger conditions below are deliberately demanding engineering success targets rather than familywise-controlled hypothesis tests:

- V2-minus-GbV EM point estimate >= +0.60 percentage points;
- V2-minus-GbV 95% EM CI lower bound >= +0.30 percentage points;
- V2-minus-GbV F1 point estimate >= +0.50 percentage points;
- V2-minus-GbV 95% F1 CI lower bound > 0;
- V2 damage count no greater than GbV, with >=25% reduction retained as a stretch target;
- positive V2-minus-GbV EM point estimate on all three datasets;
- positive V2 net correction on BM25, Dense, and Hybrid;
- favorable recovery-damage behavior across the predeclared multi-budget analysis rather than only one threshold.

Negative, tied, or inconclusive outcomes must be retained.

## Candidate V2 family

The provisional V2 architecture is **HGB backbone + three-state damage-aware meta correction**. The meta model predicts recovery, damage, or neutral transition behavior from label-free frozen selector signals. Its decision utility is

`U = p(recovery) - lambda * p(damage)`.

The fixed candidate uses `lambda = 1.0` and meta fusion weight `alpha = 2.0`, selected from historical development evidence before any new fresh run. The utility is quantile-normalized and fused with the state-symmetrized HGB ranking. Raw global HGB remains a mandatory ablation and fallback comparison, not a post-result replacement for V2.

A four-state 00/01/10/11 model is not the primary candidate because the historical scorable set contains too few answer-different both-correct cases for a stable 11 class. Dataset identity is excluded from the primary feature set even though exploratory development showed gains, because benchmark-specific coding would weaken transfer claims.

No new GbV-derived meta feature is added to the primary V2 after this freeze draft. GbV remains an independent published-method comparator rather than a signal that V2 is allowed to absorb after seeing its fresh performance.

## Budget policy

The preferred prospective primary action rate is **5.0% of retriever-conditioned traces**. On the historical 9,000-trace reference cohort this is 450 actions. This replaces the arbitrary reuse of the historical 370-action count with a scale-free deployment budget.

The 5.0% rate is a development-selected protocol choice and must be frozen before fresh-label access. V2 and GbV receive the same total number of actions under the primary comparison. The secondary comparator exactly matches V2 within every dataset x retriever stratum.

Any multi-budget curve on the fresh cohort must use a budget grid frozen before label access and must be reported as secondary descriptive operating-point evidence; it cannot be used to replace the primary 5.0% result.

## Historical private-artifact integrity

Before any fresh scoring, the historical base estimators and `method_freeze.json` must match the exact file sizes and SHA-256 values in `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`. Missing or mismatched historical models cause a hard stop. They must not be silently retrained to recreate approximately equivalent scores.

V2 and GbV use the same strict canonical branch ledger and the same answer-normalization eligibility rule. Equal normalized answers and empty answers fail closed to KEEP. Method-specific scoring failures are retained as fail-closed events rather than being deleted from analysis.

## Pre-label stop boundary

Before fresh-label access, save hashes for:

- source code and environment;
- source projections and selected fresh IDs;
- candidate-pool fingerprints;
- generated original/repaired branch ledger;
- historical model verification;
- V2 base-score ledger and V2 model artifact;
- V2 sealed actions;
- GbV model/configuration, score ledger, and matched actions;
- action-budget and tie-breaking rules;
- statistical-analysis script and bootstrap seed.

`seal_v2_gbv_prelabel_gate.py` must return PASS. That execution then stops. Fresh Gold/correctness/outcome data require a separate responsible-human authorization and may only be joined by the predeclared post-seal evaluator. No retry, retuning, sample-size expansion, or comparator substitution is allowed after label access.
