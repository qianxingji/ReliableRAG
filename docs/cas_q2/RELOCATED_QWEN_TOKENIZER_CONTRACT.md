# Full historical Qwen prompt/tokenizer/decoder replay

Research Lead design, 2026-09-11. CAS Q2 STATUS: NOT READY.

## Prospective scope

The restored historical runtime contains 13,500 canonical traces (4,500 question
groups; nine strata of 1,500) and the original fixed 180 replay traces (20 per
stratum). Replay all three generation receipts per trace: a0, repair_query, a1.
There are 40,500 canonical and 540 replay receipts. Do not sample, regenerate,
inspect answer quality, read Gold, or choose new IDs. The original live empirical
C3 process and all its inputs remain outside this CPU-only gate.

Before decoding any of these ledgers, freeze exact source/config/input records,
controller bytes, commands, environment and accepted dependency authorities.
Use the accepted static graph aa5c3da7ed764405e92602b64303984931a798abf2aee3e64c5d56ae34e892ea
and restoration 54b44ed473665264a366ee0bb24e5a205b43c0bb012799fdd654592c620a4ff6.
Read scientific files only from E:/paper/ReliableRAG-static-roots-v1/original;
write only into a new task output namespace. No new files inside restored roots.
The historical RUNTIME_CONFIG_FREEZE.json remains pinned to
9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9.

## Computation and independent acceptance

Use the existing new neural environment, with its unchanged 33 main packages.
Load the exact Qwen/Qwen2.5-3B-Instruct tokenizer at revision
aa8e72537993ba99e69dfaafa59ed015b17504d1, local_files_only=True and
trust_remote_code=False. Explicitly bind the physical restored snapshot path;
retain model ID, revision and original logical path in the receipt. This path
argument is an IO adaptation, not an unchanged invocation of the old CLI.
Keep the historical pad/EOS behavior, left padding and chat-template hash.
Only non-weight tokenizer/configuration assets may be opened by child processes.

The producer compiles the original RankedDocument, EvidenceRender,
render_phase10_evidence, supporting constants/FrozenProtocol, and answer parser
from authenticated original source ASTs without changing their bodies. Record
all selected AST hashes. Rebuild ordered evidence from archived branch provenance
and bind it to the canonical branch text. With the original prompt templates,
apply the tokenizer chat template, tokenize without truncation (CPU tensors as
in the original generation prefix), and decode archived generated IDs. No model
is constructed. Save complete rebuilt input IDs, masks, prompt hash, raw text,
parsed text/fallback, rendering and token counts for every receipt, plus identity
and hashes binding the exact historical trace/branch/provenance/generation rows.
The repair parser uses the original sealed independent parser unchanged.
Archived generated IDs and forward-call counters are observations, not newly
generated predictions or recomputed neural counters. Label them accordingly.

A separate process must not import the producer or its native renderer. It
compiles the original independent_validate.py functions validate_generation,
render, parsed_answer, parsed_query, no_forbidden_fields, validate_branch and
independent_replay_subset with their original support functions/constants.
Its orchestration authenticates all inputs again, recreates the exact original
180-trace subset, and invokes validate_generation on every archived receipt
using a separately constructed tokenizer. Compare every producer output field
exactly to the corresponding archived receipt and all identity/source bindings.
Verify canonical/replay row order, exact coverage, end-of-file, per-stratum counts,
branch/evidence bindings, parsed-answer bindings and replay subset signatures.
No tolerance is needed: token IDs, masks, strings, hashes, counts and flags must
match exactly. No mismatches may be hidden; retain partial rows and failure logs.

The original validation functions are selected unchanged; the entire historical
validator is not run. Retrieval ranking/embedding calculations, old whole-parent
checks and original writes are outside this gate, supported separately by prior
accepted seals. Both processes share the same fixed tokenizer implementation;
this is separate orchestration and original independent validation, not a second
independent implementation of Qwen's tokenizer.

## Isolation, preservation and failure rule

One CPU thread; CUDA_VISIBLE_DEVICES=-1 and no CUDA initialization. Deny model
weight/estimator deserialization, fits, generation, neural forwards, raw dataset
or current empirical ledger access, external writes and network/process use.
Retain only the previously accepted narrow OS bootstrap (authenticated platform
cmd /c ver and stock NUL) and authenticated urllib3 IPv6 capability bind; require
that socket closed, with no connect/listen/data transfer. No SentencePiece or
PyArrow target injection is needed for Qwen. Record actual package/module roots.
The prior Windows hidden-process decoding/fallback explanation remains applicable;
do not rewrite platform metadata to force identity.

Hash every used original/restored input and all 21,267 installed environment and
target files before/after. Keep frozen implementations and accepted outputs
unchanged. Diagnose failures, then freeze a versioned correction before retry;
never modify original sources, hashes, expected outputs or matching rules.

Passing establishes the full historical Qwen input/decoder binding in the restored
roots and new environment. It does not reproduce Qwen/BGE/NLI neural forwards,
load BGE/NLI tokenizers, close their target-package bindings, retrain estimators,
prove full relocated C4/D execution or another-host/OS reproduction, or establish
fresh empirical quality or novelty. Seven historical training receipts remain
missing. P0: original C3 completion/replay/acceptance, actual C4, cost/D, claim
review. P1: remaining neural/predecessor bindings and complete delivery replay.
P2: no extra model/feature/seed/budget search; journal/CAS-year convention remains
user-undecided and does not block these experiments.
