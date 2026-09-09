# DAA-V2 high-standard experiment freeze draft

This branch is reserved for a prospective V2 post-repair arbitration experiment. No fresh-test labels may be used for model, feature, budget, threshold, or hyperparameter selection.

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
- No post-label change to score definition, feature schema, action budget, tie-breaking, or comparator implementation.

## High-standard success targets

Development targets, not guarantees:

- recovery >= 200 at the matched primary budget;
- damage <= 10;
- net correction >= 190;
- V2-minus-GbV EM point estimate >= +0.60 percentage points;
- preferred V2-minus-GbV 95% CI lower bound >= +0.30 percentage points;
- damage no greater than GbV, ideally at least 25% lower;
- positive V2-minus-GbV point estimate on all three datasets;
- positive net correction on BM25, Dense, and Hybrid;
- favorable recovery-damage behavior across most predeclared action budgets, not only one threshold.

## Candidate V2 family

The provisional V2 architecture is **HGB backbone + three-state damage-aware meta correction**. The meta model predicts recovery, damage, or neutral transition behavior from label-free frozen selector signals. Its decision utility is

`U = p(recovery) - lambda * p(damage)`.

The utility is quantile-normalized and fused with the state-symmetrized HGB ranking. Raw global HGB remains a mandatory ablation and fallback. A meta correction is retained only if grouped nested development validation improves matched-budget net correction and/or reduces damage without dataset-ID features.

A four-state 00/01/10/11 model is not the primary candidate because the historical scorable set contains too few answer-different both-correct cases for a stable 11 class. Dataset identity is excluded from the primary feature set even though exploratory development showed gains, because benchmark-specific coding would weaken transfer claims.

Optional paired NLI verification signals may be added only if they are computed label-free and improve grouped development validation before final freeze. Complexity itself is not a contribution.

## Budget policy

The preferred prospective primary action rate is **5.0% of retriever-conditioned traces**. On the historical 9,000-trace reference cohort this is 450 actions. This replaces the arbitrary reuse of the historical 370-action count with a scale-free deployment budget.

The 5.0% rate is a development-selected protocol choice and must be frozen before fresh-label access. V2 and GbV will receive the same total number of actions under the primary comparison. Secondary analyses will include exact dataset x retriever budget matching and a predeclared multi-budget curve to test whether any advantage is confined to one operating point.

## Integrity

Before fresh-label access, save hashes for:

- source code and environment;
- train/calibration/fresh split IDs;
- model artifacts;
- feature schema;
- comparator configuration and model revision;
- action-budget rule;
- scoring and tie-breaking rule;
- statistical-analysis script and bootstrap seed.

After fresh labels are opened, only the predeclared evaluation script may join labels to already-frozen scores/actions.
