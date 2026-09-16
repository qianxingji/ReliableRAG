# Mistral development A1/likelihood input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running, before development repair acceptance and
before any `a1_likelihood` namespace existed. It changes no question, trace,
reader, prompt template, generation setting, likelihood cell, repair operation,
action budget, label, endpoint or tuning rule. It only strengthens the
provenance boundary for the not-yet-run `a1_likelihood` stage.

## Gap

The initial implementation authenticated the three historical manifests and
the accepted input, `a0_query` and repair manifests before use, but its own
executable freeze recorded several manifest files without every payload member
they authenticated. The independent validator checked individual frozen rows
but did not reconstruct the complete direct input graph. A payload replacement
between the initial check and final receipt could therefore evade the final
rehash, and an omitted or unexpected frozen path would not necessarily fail
independent validation.

## Prospective correction

Before any A1 generation or likelihood forward, the producer must now:

1. verify and record all 220 payload members plus three manifests in the
   historical runtime, pool and retrieval freezes, permitting only generated
   `__pycache__/*.pyc` extras in those legacy namespaces;
2. verify and record every member of the accepted Mistral input freeze, the
   completed `a0_query` stage and the completed repair stage;
3. record the root-level `a0_query` executable freeze and both independent
   predecessor validation receipts;
4. verify and record the Mistral asset manifest and its 14 selected files;
5. record the A1 producer, independent validator, shared acquisition code,
   predecessor producers, reader adapter, frozen acquisition protocol, this
   amendment, source prompts and required native runtime files; and
6. rehash every recorded input after model unload and before writing a PASS
   receipt.

The independent tokenizer-only validator separately reconstructs the same
complete path set. It requires exact equality with the producer's executable
freeze, rehashes every member, verifies exact recursive manifest coverage,
checks the 15 Mistral asset paths, and binds the producer receipt to the saved
model-receipt and call-journal files. It also checks the exact 13,500 A1
generations, 54,000 four-cell likelihood operations, one model load and one
model unload.

Six focused A1/likelihood tests cover the scientific operation counts, payload
guards, prerequisite gates, validator independence, complete input graph and
rejection of an unexpected current-manifest file. The complete Mistral test
suite passes 156 tests.

No development repair, A1 generation, likelihood forward, Gold access, test
access or scientific fit occurred while making or testing this amendment. The
active `a0_query` executable, its frozen source commit and all 31 frozen inputs
remain unchanged.
