# Mistral development answer-semantics input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running and before answer-semantics execution. It
changes no answer pair, BGE model or revision, batching order, normalization,
similarity function, label, endpoint or tuning rule. It strengthens only the
source and executable provenance of the not-yet-run stage.

## Gap

The initial answer-semantics implementation authenticated the historical
runtime manifest, Mistral input freeze and accepted answer/witness manifests,
but its executable freeze recorded several manifest files rather than every
payload member. Its independent validator checked two prerequisite paths but
did not reconstruct the complete direct input graph or bind the producer
receipt to all three output ledgers. A payload or control-file replacement
after the initial check could therefore evade the final rehash.

## Prospective correction

Before loading BGE, the producer must now:

1. verify and record all 55 historical runtime payload members and its manifest,
   permitting only generated `__pycache__/*.pyc` extras in that legacy
   namespace;
2. verify and record every member of the accepted Mistral input freeze,
   `a0_query`, `a1_likelihood` and witness-replay stages plus the independent
   witness validation receipt;
3. verify and record the accepted BGE preflight and all six exact BGE snapshot
   files;
4. record the stage producer and independent validator, acquisition and scoring
   common code, imported predecessor/helper code, frozen scoring protocol, this
   amendment and required native runtime files; and
5. rehash every recorded input after BGE unload and before the PASS receipt.

The independent tokenizer-only validator reconstructs the identical path set,
requires exact equality with the executable freeze, validates exact recursive
manifest coverage, independently authenticates all seven BGE provenance paths,
and binds the producer receipt to `BATCH_RECEIPTS.jsonl`,
`SEMANTIC_ROWS.jsonl` and `CALL_JOURNAL.jsonl`.

Six focused answer-semantics tests cover fixed counts, vector normalization and
dot products, prerequisite/forbidden-operation guards, validator independence,
exact input-graph requirements and rejection of an unexpected manifest file.
The complete Mistral suite passes 160 tests.

No answer-semantics BGE load or forward, Gold access, test access or scientific
fit occurred while making or testing this amendment. The active `a0_query`
executable, source commit and all 31 frozen inputs remain unchanged.
