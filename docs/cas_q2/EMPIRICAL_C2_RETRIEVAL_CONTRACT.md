# Research Lead C2 original-retrieval execution contract

Effective 2026-09-11, before new retrieval or any new model forward.
CAS Q2 STATUS: NOT READY.

This engineering substage implements only the original-question retrieval part
of section C in EMPIRICAL_REPLICATION_PROTOCOL_V1.md. It follows accepted C1
pool preparation; repair queries, reader generation and downstream scoring have
separate executable freezes before they run. All scientific acquisition parameters
remain those of the authenticated original runtime/retrieval configuration.

Bind the 6,000 selected runtime questions and the three accepted C1 v2 pools by
their manifest SHA-256
4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98.
Use all 54,716 documents in unchanged pool order, without rebuilding or deduping.
Preserve all three retrievers per question: exactly 18,000 original-query traces.

Reuse the authenticated native retrieval ASTs and original router binding,
serialization and index-payload functions. Keep BGE base en v1.5 revision
a5beb1e3e68b9ab74eb54cfd186867f64f240e1a, CUDA BF16, eval/inference-only,
deterministic algorithms, no TF32, CLS normalization, 512-token maximum, native
query prefix, document batches of 16 and separate single-query calls for dense
and hybrid. No CPU/quantized fallback, alternative encoder or approximate index.
BM25 uses k1=1.5, b=.75 and the exact original tokenizer. Keep float64 BM25,
float32 exact full-pool dot products, original pool-order ties and RRF k=60,
component depth 100 with native first-seen ties. Save BM25/dense top100, hybrid
top5 and all original top5 document IDs. Every method later shares these results.

Before GPU use, pin source commit, exact native/support/validator source bytes,
protocols, pool/cohort manifests, model snapshot, prompts/runtime configuration,
package/interpreter versions and environment. Run synthetic arithmetic/schema
tests with invented documents and cached numeric fixtures; no fitting. A separate
guarded GPU compatibility preflight may load only the pinned BGE and perform
exactly two identical invented-query forward passes, requiring identical float32
embeddings. Count those separately from benchmark inference. It must not open
benchmark runtime/pool text. Preserve any failures; do not loosen numerical
settings, hashes, scope guards or deterministic requirements to make them pass.

The canonical single-use namespace is outputs/cas_q2/empirical_retrieval_v1.
After preflight acceptance, construct the three native BM25 structures and
document embedding matrices once; save dense/hybrid query matrices, complete
rankings, top5 ledgers, native AST receipts, actual backend properties and forward
counters. Dense/hybrid vectors for every identical original question must be
exactly equal. Expected canonical counts: 54,716 document rows; 3,422 document
forward batches; 12,000 query rows/forwards; 15,422 total BGE forwards; 18,000
logical original-retrieval calls. Counts are execution checks, not quality gates.

A separate validator imports no native builder/retriever/model. Independently
reconstruct all BM25 lengths, term frequencies, IDFs and postings from sealed
pool text, every BM25/full-pool dense ranking, every RRF fusion and all top5
bindings from saved matrices. Require exact original numeric/ranking equality,
complete 18,000-trace coverage and immutable inputs. This validates saved-array
retrieval arithmetic; it is not a second full neural-encoder replay. The two
invented GPU forwards and the paired query calls check determinism at their
stated scope. Do not claim complete fresh encoder or reader replay from them.

Guard original source/data/model reads and restrict writes to the new namespace
(including explicitly redirected temporary/library caches). Deny raw benchmark
access, non-BGE model loads, original pipeline package imports and network or
child processes during scientific execution. Initialize routine platform/library
metadata before the execution guard where required, with no model forward or
benchmark loading. Retain Python audit scope limitations: native-extension IO
is not a system-wide sandbox claim.

No answers, repairs, likelihood/NLI features, model fitting, policy scores,
switches or Gold outcomes are produced here. No automatic retry or cohort change.
On success the client Lead accepts original retrieval only, then implements the
separately frozen native reader/repair stage. No method contribution or CAS
submission-readiness judgment is implied by retrieval acceptance.
