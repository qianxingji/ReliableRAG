# Mistral test a1/likelihood implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `PASS_LABEL_BLIND_TEST_A1_LIKELIHOOD_ENGINEERING_NOT_EXECUTED`.
This is an executor and tokenizer-only audit milestone. It contains no formal
test generation, likelihood, outcome or performance result.

## Frozen operation

`scripts/run_mistral_test_a1_likelihood.py` requires independently accepted
test `a0_query` and repair stages. The executable freeze binds every member of
both predecessor namespaces, their independent validations, the authenticated
18,000-row test trace, the selected label-blind pool/runtime files, the Mistral
input freeze, exact model assets, prompts, implementation and protocol.

For each test trace it reconstructs `E0` from the sealed five document IDs and
`E1` from the accepted repair's inserted-document ID. It then runs exactly:

- 18,000 `a1` generations from `(question, E1)`;
- 18,000 `L00 = log P(a0 | question, E0)` operations;
- 18,000 `L01 = log P(a0 | question, E1)` operations;
- 18,000 `L10 = log P(a1 | question, E0)` operations;
- 18,000 `L11 = log P(a1 | question, E1)` operations.

The total is 90,000 durable operations. Only the pinned Mistral reader may load.
BGE, NLI, Gold, fitting, hyperparameter tuning and outcome access are forbidden.
The shared GPU mutex prevents overlap with development acquisition.

## Independent validation

`scripts/validate_mistral_test_a1_likelihood.py` imports neither the producer nor
the neural reader. With the pinned tokenizer it reconstructs all generation and
likelihood prompts, input and target token IDs, parsed answers, source hashes,
journal records, operation order and likelihood summary arithmetic. It performs
zero model loads and zero model forwards. A prospective amendment also requires
exact equality between the frozen direct input graph and an independently
reconstructed set before tokenizer construction. Its expected terminal status is
`PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_A1_LIKELIHOOD`.

Seven invented-only tests cover exact operation counts, rank-five evidence
replacement, generation and likelihood payload guards, both predecessor gates,
four-cell semantics, validator independence, exact input-graph closure and
unexpected-file rejection. All seven pass. The complete Mistral suite passes
176/176.

## Preserved smoke attempts

The first read-only source smoke used the neural environment without the pinned
dependency overlay. Tokenizer construction failed with missing
SentencePiece/protobuf before any model, prompt-generation or Gold access. No
namespace or artifact was created.

The corrected smoke prepended
`E:/paper/ReliableRAG-mistral-runtime-v1/site-packages` and the repository to
`PYTHONPATH`. It bound all 18,000 test traces, loaded the exact
`LlamaTokenizerFast`, SentencePiece 0.2.1 and protobuf 7.36.1, and checked one
synthetic rank-five `E1` prompt at the first and last trace of each dataset. Six
checks passed with zero model loads, model forwards and Gold reads. These
synthetic replacements are engineering fixtures and are not test repair output.

## Remaining evidence and risks

- P0: finish and independently accept the complete development chain.
- P1: implement test witness replay and neural scoring, then execute the frozen
  test chain once only after all predecessor gates pass.
- P2: update the manuscript, supplement and public reproduction package only
  from independently accepted results.

The main rejection risks remain an uncertain fusion increment over
`HGB_ONLY_R`, rare Damage, one repair operator, known benchmark identities and
the cost of end-to-end public neural reproduction.
