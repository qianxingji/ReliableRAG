# Mistral test repair implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `PASS_LABEL_BLIND_TEST_REPAIR_ENGINEERING_NOT_EXECUTED`.
This is an executor and replay-audit milestone. It contains no generated test
answer, repair result, outcome or performance claim.

## Frozen operation

`scripts/run_mistral_test_repair.py` requires the accepted test `a0_query`
producer and independent validation before it can create a stage namespace. It
binds the 18,000-row test trace, selected candidate-pool members, Mistral input
ledger, complete accepted retrieval namespace, original native runtime fixture,
BGE synthetic GPU preflight and six BGE model files.

The repair rule is unchanged from development and the earlier controlled study:

- call the same trace retriever with the generated repair query and depth 50;
- preserve evidence ranks 1--4;
- replace rank 5 with the first eligible returned document outside the original
  top five;
- retain the full 50-row ranking, component rankings, inserted rank and a
  768-dimensional dense query vector when dense scoring is used;
- fail closed on any missing, duplicate, nonfinite or identity-inconsistent
  value.

There are exactly 18,000 repair calls. BM25 traces make no BGE query forward;
dense and hybrid traces make one each, for exactly 12,000 BGE forwards. Frozen
document embeddings and BM25 structures are reused. Document re-embedding,
Mistral, NLI, Gold access and model fitting are forbidden. The stage uses the
same GPU mutex as all other acquisition components.

## Independent validation

`scripts/validate_mistral_test_repair.py` imports neither the repair producer nor
a neural model. For every row it reconstructs original evidence, rebuilds the
native repair query object from the accepted `a0_query` receipt, injects the
saved dense query vector, reruns the frozen BM25/dense/hybrid arithmetic and
requires exact ranking, component, inserted-document and replacement agreement.
Its expected terminal status is
`PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_REPAIR`.

Five invented-only tests cover exact counts, all three retrievers, changed-rank
failure, predecessor and component exclusions, and validator independence. All
five pass. The full Mistral suite passes 118/118.

A separate real label-blind source smoke loaded the accepted retrieval arrays
without a model, restored all three test datasets and verified original evidence
for the first and last trace in each dataset. It made zero model forwards and
zero Gold or outcome reads. No formal repair namespace was created.

## Remaining evidence and risks

- P0: finish and independently accept the full development chain.
- P1: implement test `a1_likelihood`, witness replay and neural scoring, then
  execute the one-time test chain only after all predecessor gates pass.
- P2: update manuscript, supplement and the public reproduction package only
  from independently accepted results.

The main rejection risks remain an uncertain fusion increment over
`HGB_ONLY_R`, rare Damage, one repair operator, known benchmark identities and
end-to-end neural reproduction cost.
