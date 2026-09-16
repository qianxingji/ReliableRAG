# Mistral development witness-replay input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running, before repair or `a1_likelihood`
acceptance and before any witness-replay namespace existed. It changes none of
the 18 frozen witness positions, seven operations per position, reader,
generation setting, likelihood definition, tolerance, label, endpoint or tuning
rule. It strengthens only the provenance boundary of the not-yet-run replay.

## Gap

The initial replay implementation authenticated predecessor manifests but
recorded only those manifest files in its executable freeze. It also did not
require the independent validator to reconstruct the complete input path set or
bind the producer receipt to both saved ledgers. A predecessor payload or
control-file replacement after the initial check could therefore evade the
final rehash, and a missing or unexpected frozen input might not fail the
independent replay audit.

## Prospective correction

Before any witness forward, the producer must now:

1. verify and record all 220 payload members plus three manifests in the
   historical runtime, pool and retrieval freezes, while allowing only
   generated `__pycache__/*.pyc` extras in those legacy namespaces;
2. verify and record every member of the Mistral input freeze and the completed
   `a0_query`, repair and `a1_likelihood` stages;
3. record the root A0 executable freeze and all three independent predecessor
   validation receipts;
4. verify and record the Mistral asset manifest and its 14 selected files;
5. record the replay producer and validator, shared acquisition code, all
   predecessor producers and validators, reader adapter, protocol, prospective
   input-graph amendments, source prompts and required native runtime files;
   and
6. rehash every recorded input after model unload and before the PASS receipt.

The independent tokenizer-only validator reconstructs the identical path set
without importing the replay producer or reader adapter. It requires exact path
equality, validates exact recursive manifest coverage and all 15 Mistral asset
paths, and binds the stage receipt to `WITNESS_RECEIPTS.jsonl` and
`CALL_JOURNAL.jsonl`. It retains the existing independent reconstruction of all
126 canonical operations, raw FP32 vectors, selected-token identities and
log-softmax values.

Six focused witness tests cover operation/vector counts, durable vector
identity, predecessor gates, validator independence, exact input-graph
requirements and rejection of an unexpected current-manifest file. The
complete Mistral suite passes 158 tests.

No witness replay, additional reader forward, Gold access, test access or
scientific fit occurred while making or testing this amendment. The active
`a0_query` executable, source commit and all 31 frozen inputs remain unchanged.
