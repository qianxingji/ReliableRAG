# Mistral test common-prelabel implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

The common test prelabel producer and its independent validator are implemented
but have not been run. They remain blocked on independent acceptance of the
formal test HGB and paired-GbV stages and every earlier predecessor.

## Frozen operation

For each of the 18,000 authenticated test traces, the producer requires the HGB
row and paired-GbV row to agree on dataset, retriever, sample identity, position,
role and native answer-pair eligibility. It then emits the same common
eligibility mask for all three methods:

- `HGB_GBV_R`: ordered features `[hgb_score, gbv_margin]`;
- `HGB_ONLY_R`: ordered feature `[hgb_score]`;
- `GBV_ONLY_R`: ordered feature `[gbv_margin]`.

A native-ineligible answer pair or either of the two frozen deterministic NLI
context-window failures forces Keep for every method. A valid `F0` may be
retained for audit when `a1/E1` is unscorable, but the GbV margin remains null
and the pair cannot enter any method's action ranking. No method receives a
different eligible population.

The executable freeze recursively binds the authenticated 18,000-row test
trace, candidate pool, retrieval artifacts, native-runtime tests, 31,500-row
input freeze, complete HGB and GbV stage manifests, their independent acceptance
records, code and protocol. The producer loads no neural or HGB model, performs
no fit or tuning, and records zero project-Gold, test-Gold and test-outcome
access.

The validator does not import the producer. It independently checks both source
schemas, all identity and eligibility constraints, recomputes the three feature
vectors and their row hashes, verifies exact stage-manifest coverage and frozen
input hashes, and reconciles every count in the producer receipt. Seven focused
contract tests and the complete 152-test Mistral suite pass. No formal prelabel
namespace or test feature row was produced during implementation.

## Remaining gates and risks

- **P0:** finish and independently accept the full development chain and the
  equal-budget 84-fit development-only selection. If tuning is needed, use only
  the frozen development grid and preserve every failed configuration.
- **P1:** execute the frozen test chain once, accept this prelabel freeze, then
  seal all actions before opening numeric test outcomes.
- **P2:** update the manuscript and public reproduction bundle only from
  independently accepted results.

The principal rejection risk remains whether fusion improves both accuracy and
harmful-replacement rate over `HGB_ONLY_R`. A common mask establishes fairness;
it does not establish an incremental empirical contribution.
