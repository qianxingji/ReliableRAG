# Client acceptance: full historical Qwen input/decoder replay

CAS Q2 STATUS: NOT READY. The v2 full run passes this bounded gate.

The [prospective contract](RELOCATED_QWEN_TOKENIZER_CONTRACT.md) was committed
before implementation. The [lifecycle](QWEN_TOKENIZER_GUARD_LIFECYCLE_REFINEMENT.md)
and [cardinality](QWEN_TOKENIZER_CARDINALITY_REFINEMENT.md) corrections were
separately designed, diagnosed and frozen before the new full run. Implementation
commit: `40fbf7b5dedc4b94a01fd66acf87f21492f3fd19`. Acceptance manifest:
`15872f7255fee6d06a480628d47404cd799d07a44ddf3e988d9f4a87d9ce3b12`.

## Actual full checks

- All 13,500 historical canonical traces / 4,500 question groups / nine strata,
  and all 180 originally fixed replay traces. Total: 41,040 generation receipts.
- Every prompt hash, input ID list, attention mask, decoder output, parser result,
  rendering, count and fallback field matches: 410,400 exact field comparisons,
  including 39,750,420 input tokens and 627,012 archived output tokens.
- The separate process invokes the original selected validate_generation function
  for every receipt, independently reconstructs the 180-trace subset and matches
  all 180 branch/provenance/generation signatures. Retrieval is not rerun here.
- Three in-memory counterfeit receipts are rejected for the original specific
  reasons: wrong prompt hash, changed input token and out-of-vocabulary output.
- All 21 original/restored used files, 21,267 environment/target files and
  12 controls remain unchanged. Both child stderr logs are empty; no
  unexpected audit/profile events, CUDA initialization, model load, forward,
  fit or Gold read occurred. Core packages load from the new environment.
- Client review recomputed the 11 producer and 16 independent selected AST hashes.
  The complete v2 producer replay file is byte-identical to the retained v1 file.

## Explicit execution bindings and preserved failure

Original RankedDocument/EvidenceRender/render_phase10_evidence and parsing
definitions supply the producer path. The other process uses the original
independent renderer/parser/checks. Source bodies and archived expected values
are unchanged; the physical snapshot argument is explicitly relocated. Both
processes use the same Qwen2TokenizerFast implementation and fixed revision.

The independent namespace has one disclosed global specialization: len returns
the initially measured 151,665 only for its fixed tokenizer object and delegates
all other objects to Python's ordinary len. It records 627,012 full-ledger calls
and one separate counterfeit call. Eleven subsequent full vocabulary-hash and
ordinary tokenizer-length checks match. This changes the original global built-in
binding; it is not a literal unchanged old CLI or independent tokenizer implementation.
The measured original repeated length call costs about 47-54 ms; the sealed
diagnostic supports the correction without changing any token validity criterion.

The v1 producer completed exact reconstruction, then its profiling callback
raised during interpreter finalization. The original independent attempt was
intentionally stopped after exact process verification, following the frozen
correction decision. Its failure manifest remains
`93818637823edc99772009be61920c3a091e62ab3ae684cbca47e10290aae50a`.
It is not an independently accepted full run. Two failed diagnostic attempts and
the successful four-case lifecycle diagnostic are retained with all stderr and
commands. The v2 full run uses the narrow None-module-name guard correction.

## Evidence and remaining work

The [results/private kit hash](RELOCATED_QWEN_TOKENIZER_RESULTS.json) identify the
full v2 rows, v1 failure/rows, diagnostics, commands, freezes and source controls.
No private payload is uploaded. Exact restored scientific inputs, pretrained
assets and the new package environment remain external dependencies supplied by
the already accepted static and package archives. Do not rerun accepted gates or
alter their sealed namespaces merely to refresh a report.

This closes historical Qwen input/decoder binding in the restored roots and new
environment. Generated IDs and forward counters are archived observations; no
new predictions or neural forwards are produced. BGE/NLI tokenizer/target-package
bindings, complete neural execution and C4/D predecessor execution remain pending.
There is no claim of full pipeline, another-host/OS reproduction or new contribution.

Main rejection risks: no cleared novel candidate, incomplete fresh empirical
results and seven missing historical fit-time ID/matrix receipts. Both earlier
advancement failures remain unchanged; HGB is an input/comparator.

P0: original C3 completion, fixed replay and acceptance, actual C4/full prelabel,
then cost/D and result/claim review. Fresh Gold remains closed until C4 acceptance.
P1: remaining BGE/NLI/target-package and predecessor bindings, completed-stage
closure, full relocated neural/pipeline validation. P2: no model/feature/seed/budget
search; CAS year/institutional category/target journal remain user-undecided.
