# Mistral test HGB-signal implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

The test HGB-signal producer and its independent formula validator are
implemented but have not been run. They are blocked on independent acceptance
of the formal test answer-semantics stage, which remains blocked on the complete
accepted development and test acquisition chains.

## Fixed transfer operation

The stage applies the already frozen historical `state_symmetric_hgb` artifact
to all eligible Mistral test answer pairs. It does not fit or tune the HGB. The
artifact SHA-256 remains
`9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e`,
and its ordered feature width remains 48.

For each of the 18,000 test traces, the producer reconstructs original and
repaired evidence from the authenticated test pool and retrieval arrays, binds
the accepted `a0`, repair, `a1`, four likelihood cells and answer-semantic row,
then applies the common fail-closed pair-eligibility rule. Eligible rows receive
the historical state-symmetric HGB score; ineligible rows retain a null score
and an explicit forced-Keep reason. The stage records exactly one logical HGB
score batch and two `predict_proba` calls, one for each symmetric direction.

The execution freeze recursively binds every accepted upstream artifact, the
test trace/input freeze, test pool and retrieval records, historical model and
method files, feature sources, validator and protocol. Neural model loads and
forwards, project/test Gold, test outcomes, fitting and tuning are forbidden and
have explicit counters.

The independent validator does not import the producer. It rebuilds each feature
tree with `scripts/empirical_feature_independent.py`, checks it numerically
against the saved 48-feature record, calls the underlying HGB
`predict_proba` directly on positive and negative matrices, and reconstructs the
state-symmetric score with tolerance `1e-15`. A prospective amendment also
requires exact equality between the frozen direct input graph and an
independently reconstructed set. It performs no fit or neural call.

Seven contract tests cover the model identity, feature width, independent feature
formula, independent HGB scoring, forbidden-access gates, exact input closure
and unexpected-file rejection. The complete Mistral suite passes 182 tests. No
formal test namespace, HGB score or outcome was produced during implementation.

## Remaining gates and risks

- **P0:** finish and independently accept the development chain and the
  equal-budget 84-fit development-only selection.
- **P1:** execute the frozen test acquisition, answer-semantics and HGB stages;
  implement and accept test GbV and common prelabel scoring before any action
  seal.
- **P2:** open numeric test outcomes only after action-ledger acceptance, then
  update the manuscript and public bundle from accepted results.

The main rejection risk remains the incremental fusion effect over this strong
`HGB_ONLY_R` comparator. This stage strengthens fairness and reproducibility but
does not itself establish a fusion advantage or an independent algorithmic
contribution.
