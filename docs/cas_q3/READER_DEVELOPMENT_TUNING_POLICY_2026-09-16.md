# Reader development tuning policy

Date: 2026-09-16. **CAS Q3 STATUS: NOT READY.**

The user authorizes tuning when experimental results are unsatisfactory. This
policy incorporates tuning before the new reader's final evaluation. It is a
research-design addendum, not evidence that any fit or reader experiment ran.
The earlier prohibition on test-set tuning remains applicable.

## Scope and fair search budget

The first bounded search covers `HGB_GBV_R`, `HGB_ONLY_R`, and `GBV_ONLY_R`.
Each receives the same eight candidate configurations:

- Base logistic-regression `C`: `0.01`, `0.1`, `1.0`, `10.0`.
- Base `class_weight`: `None` or `balanced`.

The existing `C=1.0, class_weight=None` configuration is included. This range
is chosen before new reader outcomes, not fitted to the observed Qwen test
differences. Feature definitions, recovery target, eligibility, missing-value
handling, solver, convergence tolerances, action allocation and canonical ties
stay fixed within this search. The original implementation also includes
missingness indicators and retriever indicators; these are retained equally.

Reader weights, quantization, prompts, generation settings, retriever settings,
candidate generation and the GbV/NLI scorer are not optimization variables in
this first head-only search. Altering them would require a separate documented
development experiment and regenerate every affected method's shared inputs.
No method gets an extra outcome-driven search after its competitors stop.

## Data roles and selection

Keep the existing development split: 3,600 fit questions and 900 calibration
questions. Three retrieval siblings of a question always stay together.
Within the 3,600 fit questions, use three deterministic dataset-stratified
question-group folds shared by all configurations and methods. Bind fold
membership and the split rule before any fit; do not try alternate splits.
Expected membership is 1,200 validation and 2,400 training questions per fold,
before reader-specific eligibility filtering.

The implemented fold prefix is
`cas-q3-reader-tuning-fold-v1|20260917`. Within each dataset, groups are ordered
by the SHA-256 of the prefix, dataset and sample ID, with the sample ID as a
collision tie-break, then assigned round-robin to folds 0--2. This gives exactly
400 validation questions per dataset and fold. The implementation is
`src/arbitration/reader_development_tuning.py`, SHA-256
`300541e57cbff16bd7bdae9821aa335627bcf4e70bb1fe34586f46ba032002a7`.

Fit imputation, scaling, class weights and the base model using only each
fold's training partition. Validation rows must not contribute to fitted
preprocessing statistics or training class weights. Select each method's configuration by the lowest
pooled held-out binary log loss for the recovery target, using stable raw-logit
arithmetic. Pool all eligible held-out rows, rather than unweighted fold means.
This preserves the existing recovery supervision objective. Recovery, Damage
and Net may be reported as development diagnostics; they are not alternative
selection criteria to adopt after inspecting the search results.

For exactly equal selection losses, prefer `class_weight=None`, then the fixed
`C` order `[1.0, 0.1, 10.0, 0.01]`. A failed or nonconverged fold invalidates
that configuration and remains logged; no extra retry budget, reshuffled fold
or relaxed tolerance is silently substituted. Class-deficient partitions,
nonfinite data or shared preprocessing failures require diagnosis rather than
calling the search a scientific PASS. All-invalid methods stop the search.

After selecting configurations, refit each winner on the full 3,600-question
fit partition. Fit its original Platt calibration once on the separate
900-question calibration partition with the existing fixed parameters.
Calibration outcomes are not reused for hyperparameter selection. Actual
eligible rows, class counts and fitted coefficients are recorded at every fit.

The maximum successful search workload is `3 methods × 8 configurations ×
3 folds = 72` base fits, followed by three selected base refits and three
selected-model Platt fits: **78 search fits**. The prospective fixed-recipe
sensitivity requires one additional fixed base fit and one fixed Platt fit for
each method: six non-search fits. The formal producer therefore performs **84
fit attempts = 78 search + 6 fixed-reference**; its independent validator
repeats the same 84 fits only to audit the result. This accounting was amended
before any project Gold read or scientific fit in
`MISTRAL_FIXED_RECIPE_SENSITIVITY_AMENDMENT_2026-09-17.md`. This is one finite
search, not repeated rounds until the desired result appears. Resource limits
and exact fold identities are bound in the executable reader protocol.

## Evaluation and interpretation

Complete development selection before revealing or analyzing new reader test
performance. Preserve the original fixed-parameter reference and all search
candidates, losses, errors, model receipts and selection decisions. The final
reader protocol must specify before testing whether the selected configuration
or fixed recipe is primary, and which comparisons belong to its multiplicity
family. The earlier four-endpoint proposal is not automatically sufficient if
both recipes are used for confirmatory claims. Do not choose the primary recipe
or expand the search after seeing which test result is more favorable.

The Qwen test results and question identities have already informed project
design. Label new tuning as prospective for the new reader's outputs, not as an
independent, wholly unseen population confirmation. Tuning also changes the
adaptation recipe; cross-reader differences cannot isolate model family alone.
The selected cross-validation score is a development selection score, not an
unbiased performance estimate of the selected model or of training uncertainty.

If final test results are disappointing, retain and report them. A later change
motivated by those results is a new exploratory version; it needs a separately
designed, uncontaminated evaluation for a new confirmatory claim. Do not relabel
the same test set as validation and then report it as held out, append reader
searches until significance, select favorable seeds, or erase failed runs.

Tuning can improve parameter choice; it does not guarantee a gain over HGB-only
or establish algorithmic novelty. Test correctness and scientific authenticity
are never tunable objectives.

## Progress

- P0: this development tuning design, reusable execution core, formal producer
  and independent full-refit validator are implemented. Four core synthetic
  contract tests pass in
  `tests/test_reader_development_tuning.py`, SHA-256
  `ea220853b6b75c006572fa9cc253fa2cc29d9f39dfe8d2f7c7697432e2ff682f`.
  They verify the exact folds, grid/tie rule, finite 28-fit per-method budget,
  fixed-reference identity and rejection of extra roles/outcome scope. Six
  formal tuning contract tests and the complete 81-test Mistral suite also pass.
  No project scientific fit has run.
- P1: once those are ready, run the equal-budget search, freeze selected models,
  and evaluate the fixed reader condition with all outcomes retained.
- P2: update manuscript and public release only from accepted results.

Only synthetic estimator fits were used to test the implementation. No project
development label, new model load, neural forward, scientific fit, bootstrap or
test-outcome read was performed. Existing Qwen/Phi/Mistral evidence and the
latest manuscript remain unchanged. No model/effort switch or independent final
acceptance is certified by this document.
