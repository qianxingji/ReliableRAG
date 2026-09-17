# Mistral test a0/query input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before any formal Mistral test
execution. It changes no test row, prompt, evidence order, model setting,
generation rule, output parser or endpoint. It does not authorize test execution
and does not open test Gold.

## Gap

The test `a0_query` producer already recorded the selected label-blind test
trace, six candidate-pool payloads, the complete Mistral input freeze, 14
selected Mistral asset files and its direct code/protocol controls. The
independent tokenizer-only validator reverified these sources, but it only
required its own file to appear in the executable freeze. It did not reconstruct
and compare the complete frozen path set, so a missing or unrelated extra path
would not independently fail the stage.

## Prospective correction

Before tokenizer construction, the independent validator now reconstructs:

1. the pinned preparation manifest and selected test trace;
2. the pinned candidate-pool manifest and all six runtime/document payloads
   actually read by the stage;
3. every member of the exact Mistral input-freeze namespace;
4. the asset manifest and all 14 selected Mistral files; and
5. the producer, validator, acquisition/input-freeze helpers, canonical reader
   runtime, Python executable, two prompt files, frozen test protocol and this
   amendment.

It requires exact set equality with the producer freeze after independently
rehashing every recorded input. The producer additionally freezes the Python
executable and this amendment. Existing exact bindings for the 36,000 generation
receipts and durable journal remain unchanged.

Eight invented-only contract tests cover exact scope, fail-closed identity and
role mutations, ordered evidence, label-blind source pins, shared GPU exclusion,
validator independence, canonical hashing, exact input-graph closure and
rejection of an unexpected manifest file. No model forward, test generation,
Gold value, outcome or scientific fit was used while making or testing this
amendment. The complete Mistral suite passes 172 tests.
