# Mistral test answer-semantics implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

The label-blind test answer-semantics producer and its independent validator are
implemented. They have not been run on the formal test chain. The producer is
blocked until the test `a0_query`, repair, `a1_likelihood`, witness replay and
all corresponding independent validations are accepted. Those test stages are
themselves blocked on completion and acceptance of the development chain.

## Frozen operation

The producer accepts exactly 18,000 sealed test identities and the accepted
`a0` and `a1` text receipts. In canonical HotpotQA, 2WikiMultihopQA and MuSiQue
order, it encodes the two answers for every trace with the pinned document-mode
BGE encoder. The fixed accounting is:

- 18,000 answer pairs and 36,000 answer vectors;
- batch size 16, exactly 750 batches per dataset and 2,250 batches overall;
- 768 float32 values per answer, explicitly serialized as little-endian bytes;
- 110,592,000 raw vector bytes;
- one observed BGE forward per batch and one model load/unload for the stage.

Each durable batch binds its answer hashes, test identity, tokenizer fields,
vector file and pairwise dot product. The execution freeze recursively binds
the accepted prior-stage files and validations, the test trace and input freeze,
the BGE assets, control sources and test protocol. Mistral and NLI loads, Gold,
outcomes, fitting and tuning are forbidden and have explicit zero counters.

The separate validator imports neither the producer, the scoring journal nor
any model class. It loads only the pinned BGE tokenizer, reconstructs all
2,250 batch inputs from the original sealed receipts, verifies all raw vector
files and norms, and recomputes all 18,000 answer-pair dot products. A
prospective amendment also requires exact equality between the producer freeze
and the independently reconstructed direct path set before tokenizer
construction. Its expected terminal status is
`PASS_INDEPENDENT_TOKENIZER_ONLY_MISTRAL_TEST_ANSWER_SEMANTICS`.

Six contract tests cover the exact accounting, little-endian vector and
dot-product checks, witness/forbidden-access gates, validator independence,
exact input-graph closure and unexpected-file rejection. The complete Mistral
engineering suite passes 180 tests. The formal stage was not executed while
implementing or testing this code.

## Remaining gates and risks

- **P0:** finish and independently accept development acquisition, scoring,
  outcomes and the equal-budget 84-fit tuning chain; preserve all failures.
- **P1:** execute the frozen test chain once, then implement and accept test HGB,
  GbV and common prelabel scoring before sealing actions.
- **P2:** open numeric test outcomes only after action-ledger acceptance; update
  the manuscript and public bundle only from independently accepted results.

The main rejection risk remains that fusion may not improve both accuracy and
damage over the stronger `HGB_ONLY_R` control. Other material risks are rare
damage events, one repair operator, known benchmark identities, transferred HGB
provenance and the cost of public neural reproduction. This implementation
closes an engineering gap only; it supplies no new scientific result.
