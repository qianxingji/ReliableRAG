# Accepted empirical shared-inference cost reconciliation

**Decision: ACCEPTED WITH EXPLICIT MEASUREMENT LIMITS.** The single successful
receipt-only cost process and a separate client audit close the frozen C1-C4
shared execution graph. This authorizes D selected-reference mapping. It does
not establish a deployment speedup, answer-quality result, winning policy,
contribution claim or submission readiness.

## Bound result

- Source commit: `1439570d9ae5caf68573aae12346c49cb571dfcb`
- Scientific manifest: `eeffcdc151670acb2985834eb37903d78a7284c4f22bb7a5755b2fc632371819`
- External run manifest: `e19437292802609ea751b3565c31c15cc13f4167b0f8e062e8aefe96757cc612`
- Binding config: `9fa53e64fb6a2cc6776d4737b2742349fbecd1027a6d3ef81cebfa87b5f30e49`
- Cost report: `c36902d3538cda0a90103722ca11ae215aaaec1cf992328b56c1460cd2f4a91a`
- Client audit: `a723d2a948bd9c42c74d47381c4ca485e7a875cbf5b5f2e566a92002999ea42a`

The canonical generation ledger contains 54,000 receipts for 18,000 traces.
It records 51,901,556 prompt tokens, 826,362 generated tokens and the same
number of Qwen score-step forwards. The separate 540-receipt bounded replay
records 518,966 prompt tokens and 8,441 generated tokens/forwards. The cost
producer validates every receipt and token/mask array without materializing
raw or parsed answer strings. The client audit independently scans every scalar
field and aggregate, checks 227 deterministic full-array samples spanning all
27 dataset/retriever/stage cells, binds the accepted C3 counters, and rehashes
all 18,306 executable inputs plus 30,912 environment files.

C2 closes 18,000 logical original retrievals, 12,000 BM25 components, 12,000
dense components, 15,422 embedding forwards and 54,716 embedded document rows.
C3 closes another 18,000 logical repair retrievals, 12,000 BGE query forwards
and no document re-embedding. C4 closes 2,250 answer-embedding forwards,
16,932 likelihood forwards with 136 cache hits, and 8,534 NLI forwards over
42,946 pairs. All nine policies share this acquisition and scoring work. The
900 actions for each non-Keep policy are allocation counts and do not imply a
5% generation or scoring budget.

## Timings and limits

The preserved stage timers are 1,096.562 s for C2, 45,216.887 s for canonical
C3, 5,337.573 s for C4 base scoring, 3,523.022 s for C4 GbV scoring and 157.658 s
for fixed policy allocation. These timers have different start/end boundaries
and include different setup, IO, audit-hook and rehash work, so they cannot be
summed into an end-to-end latency. Saved C4 allocator peaks are 8,153,970,176
bytes for base and 2,956,706,304 bytes for GbV.

The following measurements do not exist and remain explicit limitations:

- canonical C2/C3 CUDA allocator peaks;
- per-generation latency and separately timed policy deployments;
- C2/C3 BGE token totals and generation per-forward input-token touches;
- a uniform end-to-end wall-time boundary or FLOP count.

No standalone HGB-only, GbV-only or ROA deployment cost experiment ran. The C3
synthetic peak cannot replace a canonical peak. C4 cost closure reuses its
independently accepted saved neural witnesses and performs no new forward.

Both failed attempts remain preserved. The first stopped before a scientific
namespace because the prerequisite helper resolved the sealed C4 V1 preflight;
its manifest is `f49f8c76e8e6c9ca8158f9824484a721b80eae4616c5e17cf5e8df3e0dee0120`.
The second stopped before a scientific namespace because one existing C2
preflight metadata file was absent from the authenticated cost graph; its
manifest is `f83b17730a1b2a2eba507075d87f7d04253cb9d787b9e65e3a5336a4686c664f`.
Neither attempt read Gold, fit a model or ran inference.

**CAS Q2 STATUS: NOT READY.** P0 is now the four D processes and real-result
review. P1 remains contribution, robustness, fair comparison and full release
closure justified by those results. P2 remains paper/claim and journal-scope
readiness. The largest rejection risks are still absent fresh outcomes, no
cleared novel contribution, historical fit-time provenance gaps, incomplete
full neural relocation replay, and undecided CAS year/category/target journal.
