# Mistral test HGB input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before any formal test scoring. It
changes no test row, eligibility rule, feature, historical HGB model, score
formula or endpoint. The HGB remains a fixed upstream signal and comparator;
there is no refit or tuning. Neural execution, Gold and outcomes remain
forbidden.

## Gap

The HGB producer already froze the selected test trace/pool sources, complete
retrieval, CPU-test, input-freeze and accepted semantic/acquisition namespaces,
the historical model/method/formula sources and direct controls. The independent
formula validator reverified relevant sources but required only the semantic
validation and its own file to appear in the frozen set. It did not independently
prove exact input-path equality.

## Prospective correction

Before feature reconstruction, the validator now independently reconstructs and
rehashes:

1. the selected test trace and seven pool/runtime acceptance files;
2. every member of retrieval, CPU-test, input-freeze, answer-semantics and the
   three acquisition namespaces plus all four validation receipts;
3. the pinned historical preflight, method, HGB model, answer normalization and
   state-symmetric formula sources; and
4. the producer, independent validator/formulas, runtime/retrieval helpers,
   imported test helpers, canonical reader runtime, original runtime files,
   Python executable, frozen test protocol and this amendment.

Exact equality with the producer freeze is required before HGB inference audit.
The producer now also records its imported validator helper, canonical runtime,
Python executable and this amendment. Existing 48-feature, symmetric
`predict_proba`, output binding and zero-fit checks remain unchanged.

Seven contract tests cover model identity, feature width, independent formulas,
independent symmetric scoring, forbidden-access gates, exact input closure and
unexpected-file rejection. No HGB test score, model fit, neural load/forward,
Gold read or outcome read was produced while making or testing this amendment.
The complete Mistral suite passes 182 tests.
