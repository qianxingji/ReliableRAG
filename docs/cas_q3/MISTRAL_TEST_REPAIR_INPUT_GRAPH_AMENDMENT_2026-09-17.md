# Mistral test repair input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before any formal test acquisition or
repair execution. It changes no trace, repair query, retriever, depth, evidence
replacement, BGE revision or test endpoint. Test Gold, fitting, Mistral and NLI
remain forbidden in this stage.

## Gap

The repair producer already recorded all current members of its retrieval,
preflight, CPU-test, input-freeze and accepted test-a0 namespaces, the selected
trace/pool files and six BGE assets. Its independent no-model validator reloaded
the relevant sources but only required the validator file to appear in the
producer freeze. It did not independently prove that the freeze contained
exactly the required direct path set.

## Prospective correction

Before reconstructing any repair row, the validator now independently rebuilds
and rehashes:

1. the selected trace and seven selected pool/runtime acceptance files;
2. every member of the retrieval, BGE-preflight, CPU-test, Mistral input-freeze
   and accepted test-a0 namespaces;
3. the accepted test-a0 validation and its root executable freeze;
4. all six pinned BGE model files selected by the preflight freeze; and
5. the producer, validator, imported a0 validator/producer, runtime and retrieval
   helpers, canonical reader runtime, original native runtime files, Python
   executable, frozen test protocol and this amendment.

Exact equality with the producer's frozen path set is required before replay.
The producer now directly records the additional imported controls, the Python
executable, the accepted a0 root freeze and this amendment. Existing durable
journal and repair-binding output checks remain unchanged.

Seven invented-only contract tests cover fixed counts, all retrievers,
rank-five and inserted-rank failures, predecessor/component exclusions,
validator independence, exact input-graph closure and rejection of an
unexpected manifest file. No test repair, model load, model forward, Gold read,
outcome read or scientific fit was performed while making or testing this
amendment. The complete Mistral suite passes 174 tests.
