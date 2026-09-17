# Mistral test common-prelabel input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before formal common-prelabel
execution. It changes no test row, feature, common eligibility rule, method,
action budget or endpoint. Gold, outcomes, model execution, fitting and tuning
remain forbidden.

## Gap

The producer already froze the selected test trace/pool inputs, complete
retrieval, CPU-test and input-freeze namespaces, accepted HGB and GbV namespaces
and validations, and direct controls. The independent validator rehashed every
listed file but required only both validation receipts and its own source to
appear in the freeze. It did not independently prove exact input-path equality.

## Prospective correction

Before reconstructing any common feature row, the validator now independently
reconstructs and rehashes:

1. the selected test trace and seven pool/runtime acceptance files;
2. every member of retrieval, CPU-test and input-freeze;
3. every member of the accepted HGB and GbV namespaces plus both independent
   validation receipts; and
4. the producer, independent validator, imported runtime helpers, canonical
   reader runtime, Python executable, frozen test protocol and this amendment.

Exact equality with the producer freeze is required before the row audit. The
producer now also records its direct CPU-test helper, imported independent
validation helper, Python executable and this amendment. The validator requires
the recorded Python path and exact common-eligibility rule.

Nine contract tests cover feature order, independent row reconstruction, both
NLI-failure positions, native ineligibility, mismatch failure, validator
independence, exact input closure and unexpected-file rejection. No formal test
prelabel namespace, model load, Gold read, outcome read, fit or tuning was
produced while making or testing this amendment.
