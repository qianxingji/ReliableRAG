# Research Lead reader and repair execution contract

Effective 2026-09-11, before any new reader generation. CAS Q2 STATUS: NOT READY.

This engineering stage implements the fixed reader/repair part of section C in
EMPIRICAL_REPLICATION_PROTOCOL_V1.md. It may run only after C2 original retrieval
passes independent acceptance and its manifest is pinned in the new executable
freeze. This document alone is not an executable input freeze.

For all 18,000 original traces, in the sealed original top5 ledger order, generate
a0 from E0, one repair query from question/E0 (without a0), and a1 from repaired
E1. Use the authenticated native runtime assembly: exact Qwen2.5-3B-Instruct
revision aa8e72537993ba99e69dfaafa59ed015b17504d1 and BGE revision
a5beb1e3e68b9ab74eb54cfd186867f64f240e1a; original BF16/deterministic settings,
seed 20260828, prompt bytes, tokenizer chat template, inherited generation config,
greedy decoding, answer cap 48 and repair-query cap 64. Preserve original
16,000-character evidence rendering, tokenization, stop tokens and raw parsers.

Reuse the original restricted generation assembly, whose generation prefix is
AST-identical to its original reader and omits only unused post-generation
mean/min log-probability diagnostics. Do not introduce a replacement generator
or describe a new equivalent implementation as the original. Neither likelihood
features nor selectors are available in this stage.

Restore the sealed BM25 structures and document embedding matrices; never rebuild
them. Bind E0 to the exact saved top5 IDs/scores. Use the same retriever for one
repair ranking at depth 50, with original dense/RRF component behavior. The native
repair operator inserts the first candidate absent from all five E0 documents,
keeps original ranks 1..4, and replaces rank 5. No per-policy acquisition and no
post-hoc selection of repair queries. Retain native query-parser fallback and
empty parsed answers. A technical generation/repair failure aborts and preserves
completed durable receipts; it does not authorize dropping or replacing a trace.

Before benchmark generation, freeze all source/config/model/tokenizer hashes,
environment versions, accepted C1/C2 bindings, 18,000 complete trace records and
the replay subset below. Run invented-only renderer/parser/repair/receipt tests
and a guarded joint Qwen/BGE GPU preflight. That preflight loads the two pinned
models concurrently and runs exactly two identical invented answer generations;
record their forwards/tokens separately, require exact token replay, and use no
benchmark text. Do not change dtype/model/config after a failure without a new
prospective engineering/scientific review as appropriate.

Canonical namespace: outputs/cas_q2/empirical_runtime_v1. Write durable append-only
generation receipts (prompt hash, input/mask/generated token IDs, raw/parsed text,
rendering, token counts and actual forward counts), repair rankings/components/
query vectors, complete branch evidence provenance and method-independent a0/a1
branch rows. Exactly 54,000 canonical generation calls and 18,000 repair retrieval
calls are planned, including 12,000 single-query BGE repair forwards and zero
document-embedding forwards. No outcome/scoring/action fields are allowed.

Preserve the original bounded numerical runtime replay rule: in each of the nine
dataset/retriever strata, rank all 2,000 traces by ascending SHA256 UTF-8
`daa-v2-runtime-replay-v1|<dataset>|<retriever>|<sample_id>`, then sample_id, and
take the first 20. Retain their canonical execution order (180 traces). Bind this
subset before any reader generation. After canonical completion, replay those
180 traces once in a separate subdirectory. Require byte-identical scientific
rows, token receipts, repair bindings and evidence provenance. Keep every failure;
no favorable replay-subset redraw. Report the 540 additional generation calls and
180 repair retrieval calls separately from canonical inference cost. This is
bounded replay, not a second full 18,000-trace reader reproduction.

A separate validator imports no native runtime builder/reader and performs no
model forwards. It may load the pinned tokenizer only. For every trace independently
reconstruct E0/E1 evidence, context rendering, prompt and input token IDs, token
decoding, original parser behavior, full repair ranking and replacement from saved
matrices, all transition bindings and exact a0/a1 branch rows. Verify actual
generation/repair counters, complete trace coverage, every file/source hash and
the fixed replay membership and byte matches. Do not infer correctness from
generated text or open answers to judge output quality at this stage.

Apply read/write/import/network guards with only the two pinned model caches,
accepted safe runtime/pool/retrieval data and exact frozen source controls allowed.
Raw benchmark and all Gold/outcome files remain inaccessible. Redirect temporary
library caches into the new namespace and preserve Python-audit scope limitations.
The client Lead accepts only candidate-pair acquisition after these checks pass;
supervised scoring, common eligibility, exact top-K actions, prelabel acceptance
and outcome analysis remain separate required stages.
