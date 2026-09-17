# Mistral test analysis implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PASS_INVENTED_ONLY_ANALYSIS_ENGINEERING`.

The result-independent Mistral test analysis kernel is implemented in
`scripts/mistral_test_analysis_math.py`. A separate implementation in
`scripts/mistral_test_analysis_independent.py` imports neither the producer nor
`src/evaluation/batch_allocation.py`; it expands resampled trace copies,
independently sorts them and reconstructs every allocation and report field.

The frozen implementation covers:

- the three development-selected primary heads and their three fixed-C
  descriptive counterparts under one common eligibility mask;
- complete-population EM, token F1, Recovery, Damage, Neutral, Net and
  transition counts;
- the two primary comparisons by EM and Damage, forming exactly four adjusted
  endpoints at quantiles 0.00625/0.99375;
- `default_rng(20260930)`, dataset-stratified question-cluster draws, all three
  retriever siblings moving together and global K=900 reallocation on each
  production draw;
- fixed-action and fixed-recipe descriptive sensitivities outside the primary
  family;
- fusion/comparator action-overlap categories overall and in all nine dataset
  by retriever cells;
- durable unsigned-16 question multiplicities and JSONL receipt reconstruction.

The formal single-use wrapper is `scripts/run_mistral_test_analysis.py`; its
independent validator is `scripts/validate_mistral_test_analysis.py`. They require
an independently accepted label-blind action seal and an independently accepted
18,000-row numeric-outcome stage. The producer will durably write all 20,000 by
6,000 unsigned-16 question multiplicities (240,000,000 bytes), every draw
receipt, point estimates and interval reports. The validator independently
regenerates the RNG stream and expands trace copies for every draw; it imports
neither the producer wrapper, producer arithmetic nor weighted top-K kernel.

A prospective input-graph amendment now freezes every member of the accepted
action and numeric-outcome namespaces, both validations, all production and
independent arithmetic/storage sources, Python/NumPy and direct controls. Every
input is rehashed after 20,000 draws, and the independent validator requires
exact path equality before reading actions or outcomes.

## Preserved engineering failure

The first invented-only run executed seven tests and failed one assertion for
the one-eligible-row fixture. The assertion incorrectly required a resampled
draw to select no more copies than the number of unique eligible source rows.
Question-cluster bootstrap sampling is with replacement, so one eligible source
trace can occur multiple times and legitimately fill more than one of the
draw's K slots. Producer and independent explicit-copy outputs already agreed.

The assertion was corrected to require replacements not exceed the unchanged
draw cap, and to require zero replacements when there are zero eligible source
rows. No analysis formula, seed, endpoint, allocation rule or production code
was changed in response. The rerun passed all seven focused tests; the complete
Mistral suite then passed 88 tests.

The analysis core and formal-wrapper checks pass 10/10 focused tests; the complete
Mistral suite passes 191/191 tests. These are synthetic engineering checks. They do
not establish a reader effect, authorize test access or change the submission
decision. Test acquisition, neural scoring, score/action sealing, outcomes and
all 20,000 production draws remain unrun.
