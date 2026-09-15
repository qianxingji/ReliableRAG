# Client acceptance: historical NLI preparation and target binding

CAS Q2 STATUS: NOT READY. The completed run passes only the bounded input gate.

The [prospective contract](RELOCATED_NLI_INPUT_CONTRACT.md) was frozen in
a999bd5 and 3303840 before implementation commit `be3aea2b0d348163bf9cb030bceea33da49f911d`.
Acceptance manifest: `8abd5abcbef882a841c9656989d4b54b92a0c4b9526db6599a4321826c9dc9db`. Client review rechecked every sealed file,
17 selected source AST records, loaded SentencePiece binary ownership and both
processes' complete warning logs. No accepted experiment was rerun for reporting.

## Actual checks

- All 13,500 historical traces / 4,500 question groups / nine 1,500-row strata.
  The 3,202 eligible pairs, 10,296 normalized-equal pairs and two empty-a1 pairs
  are retained. All 81,000 historical eligibility/reason/count comparisons match.
- Both branches of all eligible pairs: 6,404 preparations, 32,020 original
  premises and 32,174 split pairs in 6,404 batches. The last two totals exactly
  match the archived execution's observed pair and forward-call counters.
  The new input processes themselves perform zero neural forwards.
- New witnesses contain 4,844,364 unpadded input tokens. The separate process
  reconstructs every hypothesis, chunk, batch and input array, comparing
  22,799,715 token/mask/type scalar values exactly. It uses the frozen independent
  chunk routine with complete word coverage and plain-list batch encoding;
  the producer uses original native helpers and CPU tokenizer tensors.
- Four invented fixtures pass separately in both processes: short premise,
  overlength premise, impossible hypothesis and malformed entailment labels.
  All valid prepared batches fit 512 tokens without truncation. The deliberate
  length probe emits the original 818 > 512 warning once per process; both raw
  stderr files and authenticated warning-source records are retained. There
  are no other stderr messages or unexpected audit/profile events.
- Both processes load DebertaV2Tokenizer (slow), SentencePiece 0.2.1,
  Transformers 4.53.2 and Torch 2.7.1+cu128 from the accepted new installation.
  The actual mapped SentencePiece native binary belongs to its separate new
  target and hashes to `b458ad3635e7a0262c5b0955d873cc6b4c35b2b5303c69367c59ce93d50af6d9`. The complete vocabulary hash
  `ab56a3b798f9e22958e07b304f35e8091bb2e00958713e41dda1baf8148f9014`
  remains unchanged. Entailment index is 0; the model revision stays fixed.
- All 13 used original/restored inputs, 21,267 environment/target files and
  11 controls remain unchanged. Zero pretrained model loads, fits, CUDA
  initialization, neural forwards, new predictions or historical/fresh Gold
  reads occur. Child processes observe no original-project content reads.

## Scope of acceptance

The archived ledger contains counts and scores, but no original input token
arrays, per-premise chunk strings or logits. The full new witnesses establish
preparation consistency; they cannot be called original token or probability
replay. Archived F0/F1/margin fields are decoded solely to bind their complete
historical row hashes and are neither used nor recomputed. Both processes use
the same fixed tokenizer implementation, with independently selected preparation
source and orchestration. Explicit relocated factory/target paths are disclosed;
this is not an unchanged full original scorer CLI or another-host reproduction.

The [results/private evidence kit](RELOCATED_NLI_INPUT_RESULTS.json) identify all
new rows, sealed controls, commands, logs and client review. The input assets and
package environment are supplied by already accepted external static/package
archives. No private payload is uploaded. Do not modify sealed namespaces or
repeat the accepted Qwen, NLI preparation, CPU replay or static delivery gates.

The original C3 process continues unchanged and unaccepted until canonical
completion, fixed replay and independent validation. Actual NLI probabilities,
BGE execution binding, C4/D predecessor binding and full relocated neural
pipeline execution remain pending. Seven original fit-time ID/matrix receipts
are still missing; newly created replay receipts cannot replace them.

Main rejection risks remain no cleared novel candidate, incomplete fresh
results and provenance limits. Both historical advancement failures remain.
P0: original C3/replay/acceptance, actual C4/full prelabel, then cost/D and
contribution review. P1: remaining BGE/predecessor bindings, training provenance
and full relocated neural execution. P2: no additional model/feature/seed/budget
search; CAS year, institutional category and journal remain user-undecided.
