# Mistral test witness replay implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `PASS_LABEL_BLIND_TEST_WITNESS_ENGINEERING_NOT_EXECUTED`.
This is a replay executor and no-model vector-audit milestone. It contains no
formal test replay, outcome or performance result.

## Frozen witness set

`scripts/run_mistral_test_witness_replay.py` requires independently accepted
test `a0_query`, repair and `a1_likelihood` stages. It selects the first and last
canonical position in every dataset-by-retriever cell. The nine cells produce
exactly 18 unique positions.

At each position it replays `a0`, repair query, `a1`, `L00`, `L01`, `L10` and
`L11`. Each replay receipt must equal its accepted canonical receipt exactly.
The executor saves the full first generated-token or first target-token logit
vector as raw little-endian FP32. The fixed evidence volume is:

- 126 replay operations;
- 126 vectors;
- 32,768 FP32 values per vector;
- 131,072 bytes per vector;
- 16,515,072 raw vector bytes in total.

Every predecessor namespace member, validation, source trace, label-blind pool,
input freeze, exact reader asset, prompt, implementation and protocol is bound
before execution and checked again after execution. BGE, NLI, Gold, fitting and
tuning are forbidden. The shared GPU mutex prevents overlap with acquisition.

## Independent validation

`scripts/validate_mistral_test_witness_replay.py` imports neither the producer
nor the neural reader. It reconstructs the 18 positions, evidence branches,
canonical operations and likelihood first-target token with the pinned
tokenizer. It hashes every vector and independently computes float64 log-softmax
over all 32,768 FP32 values. Agreement with the canonical selected-token log
probability must be within `2e-4`. A prospective amendment additionally requires
exact equality between the frozen direct input graph and an independently
reconstructed set before tokenizer construction. Its expected terminal status is
`PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_WITNESS_REPLAY`.

Seven invented-only tests cover exact counts, test-only first/last selection,
durable vector identity, all three accepted predecessor gates and validator
independence, exact input-graph closure and unexpected-file rejection. All seven
pass. The complete Mistral suite passes 178/178.

No source smoke can honestly claim canonical replay before the three accepted
test predecessors exist. No formal witness namespace was created.

## Remaining evidence and risks

- P0: finish and independently accept the complete development chain.
- P1: implement test neural scoring, then execute the frozen test chain once
  only after all predecessor gates pass.
- P2: update the manuscript, supplement and public reproduction package only
  from independently accepted results.

The main rejection risks remain an uncertain fusion increment over
`HGB_ONLY_R`, rare Damage, one repair operator, known benchmark identities and
the cost of end-to-end public neural reproduction.
