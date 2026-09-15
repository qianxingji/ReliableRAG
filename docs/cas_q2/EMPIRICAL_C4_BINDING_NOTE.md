# C4 adapter and independent arithmetic implementation note

Effective before any fresh scoring. This refines the already frozen C4 contract
without changing a scientific model, cohort, eligibility rule or action budget.
CAS Q2 STATUS: NOT READY.

The trace adapter accepts only the complete C3 branch/provenance/preparation/
repair schemas. It verifies their exact keys, positions and canonical hashes,
all five ordered evidence texts and metadata, the preserved first four passages
and the inserted fifth passage. It then calls the unchanged historical
restore_trace with an explicitly narrowed metadata projection. Corpus content
hashes are corpus identifiers, not assumed to be hashes of rendered text.
Accepted C3 validation is still required to establish the corpus/ranking origin;
local binding checks cannot independently establish that origin.

The semantic witness calls native encode_documents once per dataset in original
flat a0,a1 order. A forward hook records actual tokens and their text/batch
bindings; it neither changes the neural output nor invokes another forward.
The returned float32 embeddings are retained, and the native paired dot products
must match independent saved-array recomputation. Empty/equal answers remain in
this stage. This is not an independent encoder replay.

Scoring adapters call the original eligibility, four-cell feature builder,
seven saved selectors and V2 score_unseen, plus the previously accepted fixed
five-head arithmetic. GbV's original branch order is a0/E0 then a1/E1. Only
documented deterministic chunk-preparation ValueErrors (hypothesis context
overflow or an individual word that cannot fit) may become an NLI-unscorable
record. Preserve earlier branch witnesses/counters on such a failure. Unknown
ValueErrors, failures during a neural forward, malformed inputs and nonfinite
outputs are technical failures, not additional exclusions. No retry occurs.

Keep both original base scores and GbV receipts even when GbV is deterministically
unscorable. A separate common mask sets every final policy score to null for
that row. All 18,000 rows remain in the denominator; no policy-specific mask,
missing-value substitution for technical failure, threshold or stratum quota
is introduced. Reconciliation verifies native eligibility and reason codes
before applying global K=900. Raw source scores remain available for auditing.

Independent code reconstructs the feature representation from evidence, answer
texts, saved semantic values and likelihood means without importing its builder.
It replays saved linear coefficients/calibration and fixed-reference V2 arithmetic,
and independently reconstructs all nine action sets. The numerical head tolerance
remains 1e-10, with exact masks and actions. Saved HGB estimator probability calls
remain an explicit shared dependency until independent tree traversal is provided.
This note does not establish a tolerance for independent GPU/CPU NLI softmax;
that witness check and the full neural executable freeze remain outstanding.

Tests and CPU integration use invented content only. A passing test or synthetic
saved-model integration is not fresh scoring, a prelabel seal or performance
evidence. Real C4 execution must still wait for C3 acceptance, separate scoring
GPU preflights, full independent integration and immutable executable inputs.
