# Mistral test a1/likelihood input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before any formal test execution. It
changes no test row, answer, repair, prompt, likelihood cell, model setting,
parser or endpoint. Test Gold, fitting, BGE and NLI remain forbidden.

## Gap

The `a1_likelihood` producer already recorded every member of its accepted a0,
repair and Mistral-input namespaces, both validation receipts, selected test
trace/pool payloads, 14 model assets and direct controls. Its independent
tokenizer-only validator reverified the relevant sources but required only that
its own file appear in the freeze. It did not independently compare the complete
required path set with the producer freeze.

## Prospective correction

Before tokenizer construction, the validator now independently reconstructs and
rehashes:

1. the selected trace and seven selected pool/runtime acceptance files;
2. every member of the Mistral input-freeze, accepted a0 and accepted repair
   namespaces plus both independent validation receipts;
3. the asset manifest and all 14 selected Mistral files; and
4. the producer, validator, acquisition/input-freeze helpers, imported a0 and
   repair producers, a0 validator helper, canonical reader runtime, Python
   executable, prompts, frozen test protocol and this amendment.

Exact path equality is required before the 90,000-operation audit begins. The
producer additionally records the Python executable and this amendment.
Existing exact bindings for all model receipts, journal events and output
summary arithmetic remain unchanged.

Seven invented-only contract tests cover operation counts, rank-five evidence,
generation and likelihood guards, predecessor gates, four-cell semantics,
validator independence, exact input-graph closure and rejection of an
unexpected manifest file. No model load, model forward, test generation, Gold
read, outcome read or scientific fit was performed while making or testing this
amendment. The complete Mistral suite passes 176 tests.
