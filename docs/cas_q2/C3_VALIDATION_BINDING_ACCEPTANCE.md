# Client acceptance of the C3 validation execution adapter

CAS Q2 STATUS: NOT READY. Accept the scoped adapter at implementation
`3bc67ae755a6e9bb0afaec6c41952f8d323f4c31` for one complete current C3 independent
validation **after** original canonical generation and the fixed neural replay
finish. This is engineering acceptance; current C3 validation has not executed.

The [binding contract](C3_VALIDATION_BINDING_CONTRACT.md) was frozen in 4edaaad
before implementation. The invented-only gate is sealed at
`360cf355a92a3a5ddabdaed7ccfe9c7b35d14c8e04b2e4d28e8479096aa347de`;
its execution freeze is
`4c706d9cf226ad3127cde9302ee7d6f8e1f71d997437e29078a373e924ad437a`.

Actual checks use the original native environment and authenticated Qwen
tokenizer assets. All 16 original/adapted cases agree: three successful a0/a1/
repair-query receipts and 13 exact original rejection reasons for corrupt
prompt, IDs/mask, generated-token schema/budget/stop, decode, counters, render
and configuration. Nine ordinary-len cases preserve builtin results/TypeError.
A replacement tokenizer is rejected. A separate in-memory clone with one
invented added token fails cardinality verification; the primary tokenizer
and all stored assets remain unchanged.

A run of 1,500 invented generation checks reconciles all 5,500 generated IDs
to specialized length calls and performs three complete vocabulary/cardinality/
template checks. It took 3.184112 seconds on this shared host. This is a small
fixture timing, not the unexecuted full-current validation's duration or a
dedicated performance benchmark. All original per-token checks still run.

The finalization fixture uses the original writer, seal and verify_namespace.
Client review independently verifies that the original result fields retain
their canonical hash, the extra control bytes belong to the final manifest,
existing failures stay failed and result/control overwrites are rejected.
A binding failure forces FAIL before the first result write. All 13 selected
original helper ASTs were independently rehashed. These invented records are
explicitly marked fixture_only and do not satisfy full C3/C4 stage acceptance.

All 56 declared inputs, six controls, 30,823 original environment files and 41
active C3 source/config files remain unchanged. Stderr is empty, the original
guard has no denied events, the separate observer records no model/fit/forward
or CUDA-initialization event, and Torch reports CUDA uninitialized. No current
runtime payload or Gold is decoded. Scientific fits remain 185.

The accepted driver preserves original main/validate_all and scientific helper
bodies, with disclosed loader/length, first-write metadata and final-seal control
bindings. It is not a literal unchanged original CLI. Actual execution must
freeze its command, accepted fixture/client-review pins and the newly completed
canonical/replay manifest hashes. The driver requires those predecessor states,
the accepted adapter source hashes and 54,540 complete generation checks.
Client review must verify the final copied controls, periodic vocabulary checks,
all original result fields and the unchanged C4 predecessor checks before C4.
That full actual integration remains pending; this acceptance does not waive it.

The private client review is C3_VALIDATION_BINDING_CLIENT_REVIEW.json; its hash,
source pins and the private evidence kit are in
[results](C3_VALIDATION_BINDING_RESULTS.json). The earlier source observation
is retained as history. Do not repeat this passed fixture gate or modify any
frozen source to change results. Preserve any future runtime failure separately.

P0: finish original C3 and fixed neural replay, execute/accept the complete bound
validator, then C4/full prelabel and cost/D with contribution review. P1 retains
full BGE/neural-pipeline delivery and training provenance limits. No cleared
novel candidate or fresh quality result exists. P2 adds no search; the CAS year,
institutional recognition rule and journal remain user-undecided.
