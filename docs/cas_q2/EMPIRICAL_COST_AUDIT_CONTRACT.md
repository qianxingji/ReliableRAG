# Prospective accepted-prelabel inference cost reconciliation

CAS Q2 STATUS: NOT READY. Effective 2026-09-11, before cost implementation and
before completion of C3/C4. This implements the cost requirement of the frozen
empirical replication. It changes no running source, model, cohort or analysis.

The audit runs once in empirical_inference_cost_v1 only after the complete C4
independent prelabel seal, including accepted C3 canonical and bounded replay.
Authenticate the entire predecessor graph and committed audit sources before
creating the output. Read only accepted stage metadata and the two generation
receipt ledgers. Hash other graph files opaquely; no raw references, canonical
answer/passages, score/action payloads, models, inference, fitting, retrieval or
network access. A projection of generation receipts decodes only identity,
integer call/token counts and integer-array lengths/mask sums. Skip raw/parsed
answer strings and rendered evidence before string materialization.

Reconcile all 54,000 canonical and 540 replay generation receipts separately.
Require every expected trace to have a0, repair_query and a1 in native order,
unique trace identities/positions, nine complete strata, and exact agreement
with accepted runtime and independent counters. Sum logical generation calls,
Qwen forward calls, native output score steps, prompt input tokens and native
output tokens by stage and dataset/retriever cell. Input token count must match
its mask sum; token/mask lengths and output-step bounds must agree. No estimated
FLOPs, fabricated per-call latency or extrapolation from a partial ledger.

Reconcile C2 logical retrieval counts and actual BGE document/query counters.
Distinguish a hybrid request from its two BM25/dense components: canonical C2
has 18,000 logical retrieval calls and 12,000 of each component. C3 has another
18,000 logical repair retrievals and 12,000 of each component, no document
re-embedding. Its replay costs are additional verification overhead, never
silently charged to or omitted from canonical research execution.

For C4 use the independently accepted complete neural witness summaries and
raw stage counters. Require closure of all 36,000 answer embeddings / 2,250 BGE
forwards, four likelihood requests per native-eligible trace, computed/cache-hit
identity, prompt/answer token totals, NLI attempts/completed branches/pairs and
all actual top-level forwards. Retain work on pairs subsequently forced to Keep
by deterministic NLI preparation failures. State that the cost audit reuses C4's
full witness validation instead of redoing neural computation.

Report a shared execution graph: pool construction, original retrieval,
canonical pair acquisition, all base scoring, GbV scoring and fixed allocation.
All nine policies use the same acquired pair pool. Their logical replacement
counts do not identify standalone compute costs; the panel computed all base
features/heads once. Do not multiply this shared acquisition by nine or claim a
measured HGB-only/GbV-only deployment speedup. Keep's original-answer requirement
does not make this actually executed paired study free of repair computation.

Separate synthetic GPU preflights, the 180-trace replay and independent scoring
validation as measured verification overhead. Preserve each recorded stage
timer, source and boundary without summing them into end-to-end latency. State
that stage timers include portions of IO, authentication, model setup, audit
hooks and fsync instrumentation, with different start/end boundaries. Report
available scoring CUDA allocator peaks by stage only, not total process memory.
The C3 synthetic joint peak is a preflight value; canonical C2/C3 allocator peaks
and per-generation latency were not saved. Mark these missing rather than
altering running/frozen code, rerunning inference, or substituting estimates.

Cache reporting distinguishes cached model weights, reused document vectors,
generation KV cache, the initially empty per-pass likelihood-result cache and
NLI's no-result-cache path. All canonical work, deterministic forced-keeps and
verification overhead remain visible. Historical/development fitting, CPU
engineering tests and later D statistics are separately documented work, not
part of measured inference. No new standalone deployment timing is authorized.

Invented CPU tests must check complete pass accounting, text-skipping projection,
duplicate/missing/out-of-order/invalid counters, cache/branch mismatch rejection
and access boundaries. Actual cost acceptance needs complete original ledgers,
not test PASS. Report source/config hashes, manifest pins, all inputs unchanged,
zero Gold/model calls and explicit missing measurements in the sealed report.

P0 remains complete fresh evidence and contribution review. P1 is honest cost,
comparison fidelity and release quality. P2 adds no experiments or searches.
