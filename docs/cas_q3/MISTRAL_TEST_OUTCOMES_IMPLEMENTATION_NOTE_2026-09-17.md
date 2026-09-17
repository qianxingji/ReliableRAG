# Mistral test numeric-outcome implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `PASS_INVENTED_ONLY_NUMERIC_OUTCOME_ENGINEERING_NO_TEST_GOLD_ACCESS`.
This note records an engineering milestone, not a scientific result. No test
reference, answer metric, transition count or performance result was opened.

## Implemented contract

`scripts/run_mistral_test_outcomes.py` is a single-use, fail-closed producer.
Before creating a Gold-access marker it requires:

1. the 18,000-row action-seal receipt with status
   `PASS_MISTRAL_TEST_ACTION_SEAL_PENDING_INDEPENDENT`;
2. the independent action acceptance with status
   `PASS_INDEPENDENT_MISTRAL_TEST_ACTION_SEAL`, bound to the action manifest,
   receipt and row hashes;
3. accepted test `a0_query` and `a1_likelihood` answer receipts, bound to their
   independent validations and canonical answer-row hashes;
4. a clean committed execution tree and the authenticated original Gold reader,
   metric definitions, Python, NumPy and PyArrow identities.

After those gates pass, the producer selects exactly 6,000 balanced question
identities from the sealed action population, reads only their authenticated
references, and emits exactly 18,000 canonical rows. Each row contains only
`dataset`, `retriever`, `sample_id`, `a0_em`, `a1_em`, `a0_f1` and `a1_f1`.
There are 72,000 numeric metric values. Raw reference strings are forbidden in
output artifacts. If a failure occurs after Gold access starts, the failure
receipt preserves the exception type and code locations while withholding the
exception text to prevent accidental reference leakage.

`scripts/validate_mistral_test_outcomes.py` imports neither the producer nor a
model runtime. It independently revalidates the action and answer gates,
rereads the exact authenticated test references, recomputes normalized EM and
token F1 with `scripts.empirical_outcome_independent`, verifies all identities
and reconciles source-reader and transition counts. Its expected terminal status
is `PASS_INDEPENDENT_MISTRAL_TEST_OUTCOMES`.

A prospective input-graph amendment now freezes every member of the action, a0
and a1 namespaces, all three validations, the complete authenticated original
Gold/metric/PyArrow path set and direct controls. Every input is rehashed after
outcome writing, and the independent validator must prove exact path equality
before reference materialization.

## Verification and execution state

Eleven focused invented-only tests cover the exact 18,000/6,000/2,000 population,
sibling balance, duplicate and missing-row rejection, metric edge cases, answer
receipt selection, the seven-field numeric schema, action-before-Gold ordering,
failure-text withholding, validator independence, exact input closure and
unexpected-file rejection. All eleven pass. The full Mistral suite passes
190/190.

The formal output namespace does not exist. The required test acquisition,
answer-source validation, neural scoring, prelabel and action stages are
implemented but have not executed or passed their ordered gates. Consequently
no test Gold access or numeric-outcome execution is authorized yet.

## Remaining evidence and risks

- P0: finish and independently accept the complete development chain; preserve
  all failed runs, seeds and raw receipts.
- P1: implement and run the frozen test acquisition and scoring chain, then run
  the action, numeric-outcome and analysis stages once.
- P2: update the manuscript, supplement and clean public repository only after
  independently accepted numeric results exist.

The main rejection risks remain a weak or absent increment over `HGB_ONLY_R`,
rare Damage events, one repair operator, known benchmark identities and the
cost of public end-to-end neural reproduction.
