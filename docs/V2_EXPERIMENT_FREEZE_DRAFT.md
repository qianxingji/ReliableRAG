# DAA-V2 high-standard experiment freeze draft

This branch is reserved for a prospective V2 post-repair arbitration experiment. No fresh-test labels may be used for model, feature, budget, threshold, or hyperparameter selection.

## Scientific objective

Primary objective: at a predeclared matched intervention budget, outperform the published Generate-but-Verify paired NLI comparator on held-out fresh question IDs while not increasing measured harmful adoption.

## Development status

The historical 9,000-trace evaluation is development-only evidence for V2. It must not be reused as the confirmatory superiority test.

A retrospective frozen-ledger diagnostic found that global ranking by the existing state-symmetrized HGB score is materially stronger than the historical retriever-specific operating thresholds. These diagnostics are exploratory and must not be presented as fresh confirmatory evidence.

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

Start from the existing state-symmetrized HGB ranking because the historical frozen ledger indicates it is stronger than the historical logistic operating point. A more complex stacker or dual-head model is accepted only if nested question-grouped development validation improves matched-budget net correction over the raw HGB ranking; complexity is not itself a contribution.

Candidate utility forms may include:

- raw global HGB ranking;
- recovery/damage two-head utility: U = p(recovery) - lambda * p(damage);
- four-state expected utility over 00/01/10/11 transitions;
- optional verification signals such as paired NLI scores, provided they are computed label-free and frozen before fresh evaluation.

Model-family and lambda selection must be completed on development/calibration data only.

## Budget policy

Prefer a predeclared percentage budget for the new confirmatory study rather than inheriting the historical Conservative action count solely because it was used previously. Candidate primary budgets to compare during development include 4.1% and 5.0%; exactly one primary budget must be frozen before fresh-label access.

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
