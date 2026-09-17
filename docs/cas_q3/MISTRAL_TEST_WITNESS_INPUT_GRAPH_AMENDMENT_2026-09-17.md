# Mistral test witness input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before any formal test execution. It
changes no witness position, replay operation, vector format, model setting,
token choice, numerical tolerance or endpoint. Test Gold, fitting, BGE and NLI
remain forbidden.

## Gap

The witness producer already recorded every member of its accepted a0, repair,
a1/likelihood and Mistral-input namespaces, their validation receipts, selected
test sources, 14 Mistral assets and direct controls. Its independent
tokenizer/vector validator reverified those sources but required only its own
file to appear in the producer freeze. It did not compare the complete required
path set independently.

## Prospective correction

Before tokenizer construction or vector audit, the validator now independently
reconstructs and rehashes:

1. the selected test trace and seven selected pool/runtime acceptance files;
2. every member of the input-freeze and three accepted predecessor namespaces,
   plus all three independent validation receipts;
3. the asset manifest and all 14 selected Mistral files; and
4. the producer, validator, acquisition/input-freeze helpers, imported a0 and a1
   producers, a0 validator helper, canonical reader runtime, Python executable,
   prompts, frozen test protocol and this amendment.

The reconstructed set must equal the producer freeze exactly. The producer now
also freezes the imported validator helper, Python executable and this
amendment. Exact canonical-receipt replay, durable journal validation, raw-vector
hashes and independent float64 log-softmax checks remain unchanged.

Seven invented-only contract tests cover counts, witness selection, durable
vector identity, all predecessor gates, validator independence, exact input
closure and unexpected-file rejection. No test replay, model load, model
forward, Gold read, outcome read or scientific fit was performed while making
or testing this amendment. The complete Mistral suite passes 178 tests.
