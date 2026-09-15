# Phi reader full-input and implementation freeze contract

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

This is the value-blind execution gate required by the accepted Phi compatibility
preflight. It authorizes tokenizer-only inspection of the fixed development and
test questions, original Top-5 evidence and candidate document pools. It
authorizes no model weights, neural forward, generation, likelihood score,
scientific fit, existing reader answer, Gold/reference value, action or outcome.

## Fixed inputs

Development uses the original 13,500 trace manifest and label-free pool/runtime
projection under `outputs/daa_v2_fresh_v1`, restricted to the exact 4,500 IDs and
3,600-fit/900-calibration roles in the accepted fixed panel. Test uses the
accepted 18,000-trace preparation, candidate pools and the already fixed 6,000
IDs. Each trace keeps its three BM25/dense/hybrid siblings and original Top-5
document IDs. The producer must prove exact counts, uniqueness, role membership,
dataset/retriever balance and input hashes before emitting a pass.

Use the pinned Phi tokenizer/chat template, unchanged answer and repair-query
templates, and the exact all-five-header 16,000-character renderer. For every
one of the 31,500 fixed original-evidence traces, render and tokenize both the
answer and repair-query prompt. Save only identifiers, role, document and prompt
hashes, token counts and truncation metadata; never save question, evidence or
token text. Expected prompt tokenizations: 63,000.

## Dynamic repaired-answer boundary

The repaired answer prompt cannot exist before Phi emits its repair query and
the frozen retriever resolves the inserted document. The freeze therefore binds
an admission function into the future runtime: after rendering and tokenizing
each dynamic `a1` prompt, and before moving tensors to CUDA or calling
`model.generate`, require a single row, a matching all-one attention mask and at
most 9,472 input tokens. Apply the same function to `a0` and `repair_query`.
Batch size and concurrent reader instances are one. A 9,473-token prompt, a
second row, a malformed mask or an unknown stage must fail closed and preserve
the single-use namespace. No prompt shortening, document substitution or retry
is authorized after such a failure.

The 9,472-token limit is the largest input actually exercised by the accepted
invented preflight. It is a compatibility ceiling, not proof of spare memory.
The observed preflight allocation was 93.48% of nominal device capacity. The
future runtime must record actual per-call token counts, forwards, generated
tokens and CUDA peaks and must execute sequentially.

## Producer and independent validation

The producer must load the tokenizer only with weight-file reads prohibited and
network disabled. It must use an allowlisted data boundary that excludes every
canonical branch, generation receipt, answer, Gold, training target and outcome
source.
It writes a complete private scalar ledger, input/source freeze, build receipt
and exact recursive manifest in one new namespace.

A separate validator must not import the producer. It reloads the tokenizer,
reconstructs every prompt independently from the same allowed label-free inputs,
compares all 31,500 scalar-ledger rows, recomputes aggregate maxima/counts and
tests the committed admission function at and across each boundary. It must
verify every producer input hash and exact namespace coverage.

Passing both processes authorizes implementation of the single frozen Phi
development generator only. It does not authorize test Gold, outcome analysis,
claim promotion or manuscript drafting. Any discrepancy is preserved and
versioned prospectively.
