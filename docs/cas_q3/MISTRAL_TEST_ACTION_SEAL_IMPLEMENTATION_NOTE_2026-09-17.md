# Mistral test action-seal implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PASS_INVENTED_ONLY_LABEL_BLIND_ACTION_ENGINEERING`.

The pure action-seal core is implemented in
`src/arbitration/reader_test_prediction.py`. It rejects outcome/reference
fields, accepts only `role=test` prelabel rows and the three independently
accepted development tuning records, then applies the stored fit-only
preprocessing, base coefficients and Platt coefficients without fitting.

For each of `HGB_GBV_R`, `HGB_ONLY_R` and `GBV_ONLY_R`, it emits one selected
recipe probability and one fixed-`C=1.0, class_weight=None` probability. All six
policies use the same common eligibility mask. Ineligible rows have null scores,
are forced Keep and remain in the denominator. The public entry point fixes
18,000 traces, 6,000 question groups and global K=900; ties use ascending
`(dataset, retriever, sample_id)` after descending calibrated probability.

`scripts/mistral_test_prediction_independent.py` uses a separate pure-Python
formula with `math.fsum`, repeats preprocessing/base/Platt calculation and sorts
actions directly. It imports neither the producer nor a top-K helper. Producer
and audit probabilities must agree within `1e-12`, while identities, masks,
actions, model hashes and counts must agree exactly.

The formal single-use wrapper is
`scripts/run_mistral_test_action_seal.py`; its independent validator is
`scripts/validate_mistral_test_action_seal.py`. Both verify recursive predecessor
manifests and exact independent-acceptance hashes. Formal execution requires an
accepted development tuning stage with 84 producer fits and 84 audit refits,
plus an independently accepted test prelabel stage with zero Gold/outcome
access. The executor freezes its source commit and inputs, writes canonical
`ACTION_ROWS.jsonl`, a receipt and a complete recursive manifest. The validator
imports neither the wrapper nor the production prediction core.

A prospective input-graph amendment now freezes every member of both accepted
predecessor namespaces rather than their manifests alone, rehashes every input
after writing the action ledger, and requires the independent validator to prove
exact path equality before reconstructing probabilities. It also binds the
Python/NumPy runtime and all direct arithmetic/runtime sources.

## Preserved engineering failure

The first six-test run failed one dependency-isolation assertion. The independent
module did not import the producer; its module docstring merely named the module
that it intentionally avoids. The test originally searched for the bare module
name and therefore treated explanatory prose as an import. The assertion was
narrowed to concrete `from ... import` and `import ...` statements. No
production formula, allocation rule, tolerance or scientific setting changed.

The corrected core suite and formal-wrapper checks pass 10/10 focused tests. The
complete Mistral suite passes 188/188 tests. These checks use invented feature
vectors, fabricated coefficients and temporary invented manifests only. No test
answer, Gold value, outcome, scientific fit, neural forward or formal action
ledger was read or created. The required test acquisition/scoring/prelabel
predecessors are implemented but have not executed or passed their ordered
independent gates, so the formal wrapper cannot yet run.
