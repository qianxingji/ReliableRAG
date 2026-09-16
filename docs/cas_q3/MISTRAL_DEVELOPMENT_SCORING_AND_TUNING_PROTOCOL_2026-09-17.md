# Mistral development scoring and tuning protocol

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `PROSPECTIVELY_AMENDED_BEFORE_DEVELOPMENT_GOLD_OR_SCIENTIFIC_FIT`. This
protocol fixes the development-only scoring, outcome opening and bounded head
search for the exact Mistral reader condition. The pipeline executors and
independent validators are implemented, but this is not evidence that scoring,
Gold evaluation, scientific fitting or testing has run. The fixed-reference
fit amendment is recorded in
`MISTRAL_FIXED_RECIPE_SENSITIVITY_AMENDMENT_2026-09-17.md`.

## Scientific purpose and fixed condition

The additional reader tests whether the observed trade-off between Recovery and
harmful replacement changes under one different reader/deployment condition. It
does not establish a new algorithm. The condition remains
`mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`,
whole-model NF4 with double quantization and BF16 compute. Reader weights,
prompts, generation, likelihood, repair and retrieval settings are fixed and are
not tuning variables.

All stages below require independent acceptance of the complete development
`a0_query`, `repair`, `a1_likelihood` and 18-position witness replay chain. They
use exactly 4,500 development questions / 13,500 retriever traces: 3,600 fit
questions and 900 calibration questions. Test inputs and test outcomes remain
closed.

## Ordered stages

1. **Answer semantics.** With Mistral absent, load only the pinned
   `BAAI/bge-base-en-v1.5@a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`
   BF16 backend. In native document mode, encode `a0` and `a1` for every trace
   and save both 768-dimensional float32 vectors plus their dot-product semantic
   agreement. This is 27,000 answer rows and, at batch size 16 within each
   dataset, exactly 1,689 BGE forwards. Close BGE before any other neural model.
2. **Fixed HGB signal.** Reconstruct the accepted state-symmetric pair features
   from E0/E1, the four Mistral likelihood cells and the sealed answer-semantic
   agreement. Apply the already authenticated historical
   `state_symmetric_hgb` estimator without fitting or modification. Retain its
   raw recovery score for every normalization-eligible pair. This HGB estimator
   is an upstream transferred signal; it is not the new reader-specific
   `HGB_ONLY_R` head.
3. **Paired GbV.** With BGE and Mistral absent, load only the pinned
   `MoritzLaurer/deberta-v3-large-zeroshot-v2.0@5a4338ab2151dc8db04ad53b42b6153382bf4f99`
   FP32 NLI scorer. Score `(question, a0, E0)` and `(question, a1, E1)` in the
   original branch order and retain `F1-F0`. Native normalized-equal/empty pairs
   make no NLI call. The only accepted further exclusion is the already defined
   deterministic NLI context failure, retained with its completed prior branch.
   Close NLI before any fitting.
4. **Prelabel freeze.** Form one common eligibility mask for all three fitted
   methods: native answer-pair eligibility, finite HGB score and complete GbV
   margin. Save aligned rows for `HGB_GBV_R=[HGB,GbV]`,
   `HGB_ONLY_R=[HGB]` and `GBV_ONLY_R=[GbV]`. The same trace must be eligible or
   forced Keep for all three methods. Seal this stage before reading any Gold
   value.
5. **Development outcomes.** Only after the prelabel freeze, open development
   Gold answers from the authenticated benchmark sources. Recompute a0/a1
   normalized EM and token F1 with the accepted evaluation code. Bind every
   outcome to dataset, retriever, sample ID, acquisition receipt hashes and the
   pre-existing fit/cal role. No test row or test Gold value may be opened.
6. **Equal-budget tuning.** Invoke the implemented
   `src/arbitration/reader_development_tuning.py` once for each of the three
   methods. Each receives the same eight `C × class_weight` candidates and the
   same three deterministic question-group folds. Selection uses pooled held-out
   recovery-target log loss on fit folds only. Refit the selected base head on
   all fit questions, then fit its fixed Platt layer once on calibration rows.
   The search workload is 72 cross-validation fits, three selected refits and
   three selected-model Platt fits: 78 fits. Separately fit the prospectively
   fixed `C=1.0, class_weight=None` base and Platt reference once per method on
   the same fit/cal partitions: six non-search fits. The producer therefore has
   exactly 84 fit attempts and 168 start/terminal journal rows. Failures remain
   in the event journal. The independent validator repeats all 84 fits as audit
   refits; those repeats are validation work and never enter model selection.

Every producer has an independent validator that reconstructs identities,
features, masks, counts, hashes and numerical formulas without importing that
producer. Neural stages retain token/vector/logit witnesses and exact forward
counts. Each stage is sealed before the next begins; later output cannot replace
earlier rows.

## Primary recipe and test lock

The development-selected configuration is the primary Mistral recipe. The
prospectively fixed `C=1.0, class_weight=None` recipe remains a labelled
secondary sensitivity analysis and cannot replace the primary result after test
inspection. The test action budget is fixed at 900 of all 18,000 traces (5%),
with forced-Keep rows counted in the denominator and the canonical ordering of
descending calibrated recovery probability followed by dataset, retriever and
sample ID.

Before any Mistral test answer or outcome is opened, freeze the three selected
parameter sets, preprocessing arrays, base/Platt coefficients, common
eligibility rule, exact test-acquisition executors, action allocation and
multiplicity family. The primary family has four endpoints:

- `HGB_GBV_R - HGB_ONLY_R`: EM and Damage;
- `HGB_GBV_R - GBV_ONLY_R`: EM and Damage.

Use dataset-stratified, question-cluster bootstrap with global top-K
reallocation on each of 20,000 draws and simultaneous quantiles
0.00625/0.99375. Report Recovery, Damage, Neutral, EM, token F1, eligibility,
actual class counts, selected parameters and action-overlap decomposition for
all nine dataset × retriever cells. The fixed-recipe sensitivity is descriptive
and outside this four-endpoint confirmatory family.

## Failure, tuning and interpretation rules

- No test-set tuning, reader switching, prompt change, extra seed, alternative
  split, action-budget selection or second search round is allowed after seeing
  results.
- Empty answers, nonfinite values, missing classes, nonconvergence, unexpected
  model calls, source mutation or independent-validator rejection fail closed.
- A disappointing development result may select another member of the already
  fixed eight-candidate grid. It cannot expand that grid.
- A disappointing test result is retained and reported. Any later change is a
  new exploratory version requiring new uncontaminated evaluation evidence.
- Cross-reader differences jointly reflect model family, parameter scale and
  NF4 deployment; they are not causal effects of model size or architecture.

Main rejection risks remain a small or uncertain increment over the strong
`HGB_ONLY_R` control, one repair operator, reuse of previously viewed question
identities, rare Damage, transferred HGB provenance and public end-to-end neural
reproduction cost. This protocol can measure those limits; it cannot guarantee
a favorable result.
