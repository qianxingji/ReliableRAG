# Mistral test GbV input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before formal test GbV execution. It
changes no test row, pair-eligibility rule, NLI model, tokenizer, score formula,
batching rule or endpoint. Gold, outcomes, fitting and tuning remain forbidden.

## Gap

The producer already froze the selected test trace/pool inputs, complete
retrieval, CPU-test, input-freeze, HGB and acquisition namespaces, every upstream
validation receipt, the pinned DeBERTa and SentencePiece assets, runtime sources
and direct controls. The independent tokenizer/logit validator rehashed every
listed file, but it required only the HGB validation receipt and its own source
to appear in the frozen set. It did not independently prove exact input-path
equality.

## Prospective correction

Before tokenizer construction, the validator now independently reconstructs and
rehashes:

1. the selected test trace and seven pool/runtime acceptance files;
2. every member of retrieval, CPU-test, input-freeze, HGB and the three
   acquisition namespaces plus all four validation receipts;
3. the exact historical preflight, 17-file SentencePiece package and provenance,
   seven pinned DeBERTa snapshot assets and GbV formula source; and
4. the producer, independent validator, imported runtime/formula helpers,
   canonical reader runtime, original runtime files, Python executable, frozen
   test protocol and this amendment.

Exact equality with the producer freeze is required before the tokenizer/logit
audit. The validator also requires the full offline environment, CUDA device,
Python executable and SentencePiece runtime recorded by the producer. The
producer now records its directly imported validation/formula helpers, canonical
reader runtime, Python executable and this amendment.

Ten contract tests cover exact model/runtime identity, independent softmax,
error handling, partial-branch retention, raw-logit recomputation, hidden-data
rejection, validator independence, exact input closure and unexpected-file
rejection. No test GbV namespace, NLI forward, Gold read, outcome read, model fit
or tuning was produced while making or testing this amendment.
