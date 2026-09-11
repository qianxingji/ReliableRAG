# C4 protected execution and complete file-level acceptance

CAS Q2 STATUS: NOT READY. This IO/execution contract implements the already
frozen C4 scientific and neural-validation contracts. It changes no model,
sample, feature, seed, score, eligibility rule, budget or statistical endpoint.
It is fixed before new execution code and before any real C4 scoring.

## Order and prerequisites

Use four single-use namespaces: empirical_scoring_gpu_preflight_v1,
empirical_base_scoring_v1, empirical_gbv_scoring_v1 and
empirical_prelabel_policies_v1. Complete independent acceptance belongs in a
fifth namespace, empirical_scoring_validation_v1. Failed directories are retained;
never resume or overwrite them. Missing prerequisites are checked before an
execution directory is created and do not authorize a retry of an actual run.

Require the accepted C3 manifest, candidate-acquisition seal and independent
canonical/180-trace replay PASS before any scoring GPU preflight. This also keeps
the single GPU available for C3's required replay. Bind the accepted CPU
integration and neural-engineering manifests and their unchanged source inputs.
Before each stage: require a clean committed checkout, immutable predecessor
manifests, fixed model/source/config/environment records, and a new executable
freeze. Metadata authentication may hash private files opaquely; GPU preflight
cannot decode any benchmark branch. Actual scoring reads only accepted C3
branches, their provenance/repair/preparation bindings and earlier C4 outputs.
Raw benchmarks, outcomes, training, generation, retrieval, network and subprocess
execution are forbidden after the scientific boundary is installed.

Stage order is invented GPU preflight, base scoring, GbV scoring, fixed policies,
complete independent validation. Neural models load sequentially. Load authentic
SentencePiece package files before Hugging Face imports; set a new HF_HOME and
cache paths first. Copy the seven authenticated GbV snapshot files into that new
cache, preserving model ID and pinned revision. Qwen/BGE use their authenticated
original read-only model cache. All original caches/files remain untouched.

## Invented GPU preflight

No benchmark text is decoded. Use 11 fixed invented answer pairs for semantic
encoding, including an empty pair, an equal pair and a long answer. Encode all
22 texts in original document mode in two batches (16 and 6). Independently
check tokens, bindings and saved-vector dot products.

Score the four likelihood cells of one short invented pair, request those same
four cells once more to test cache hits, then score four cells of a second pair
whose deliberately long question forces native 8,192-token left prompt
truncation. Expected total: 12 cell requests, eight computed sequences, four
cache hits. Keep generation disabled. Independently validate all saved token
and cache observations. The long invented question is only a scoring context
stress fixture, not a new benchmark question or new inference configuration.

Score a short invented pair and a pair with a long premise that requires native
512-token NLI chunking, then a pair whose second hypothesis cannot fit. Retain
the successful first branch of that last pair and its exact deterministic
failure. Expected completed branches: five; the exact number of NLI chunks and
forwards follows the unchanged pinned tokenizer/chunker. Validate all batches
and counters, and the prospective FP32 softmax gate. Do not generate an answer,
fit any model or inspect a real question. Passing this preflight does not prove
all future contexts fit in memory or independently reproduce neural weights.

## Actual acquisition and durable observations

Base scoring reconstructs all 18,000 native traces using the accepted bindings,
then embeds all 36,000 answer strings (2,250 BGE forwards). Persist per-dataset
float32 vectors, semantic binding rows and token batches. Run the unchanged four
likelihood cells only for original native-eligible pairs; compute all original
ten base scores. Keep all 18,000 score rows and every failed/equal/empty pair.

scores.jsonl contains native base records with forward_witnesses represented on
disk by their integer forward ordinals. Full token witnesses are stored once in
likelihood_forwards.jsonl, each bound to trace identity and position. This is a
declared serialization split, not a different scoring return or missing witness.
The downstream policy arithmetic does not consume the token sidecar; complete
independent validation must resolve every reference and reject omissions/extras.

GbV scores.jsonl retains every original paired result. Its completed branch
witness headers store integer batch-forward references; full batches occur once
in nli_forwards.jsonl with trace and branch identity. Exact branch results and
headers are durably written before attempting the next branch. The same principle
applies to likelihood forward observations: flush/fsync each completed witness.
Count top-level model calls and input rows before forwards, including failed
attempts. Unexpected failure aborts with phase/position, actual counters and all
durable partial records retained; it never becomes an additional exclusion.

Persist failures and operational timings separately from predictors. Native
hooks add no neural forward, but their work is included in recorded acquisition
time; no claim of identical historical timer boundaries is permitted.

Fixed-policy execution loads only saved models/parameters and compact complete
base/GbV records. Reconcile one shared mask, preserve raw scores, apply the nine
frozen policies at global K=900 and write every action before any Gold mapping.
No neural weight loading or forward, refit, calibration or model selection occurs.

## Complete independent gate

The independent executable imports neither stage executor nor native witness
builders. Authenticate every predecessor file, expected row set and source
freeze. Reconstruct all C3-to-native evidence bindings separately. Validate all
semantic token/vector rows; stream every likelihood/NLI forward reference in
order, with no gaps, duplicates, unreferenced rows or silently ignored extras;
reproduce all native eligibility/failure reasons and actual counter totals.

Rebuild every feature pair, original base score and fixed-policy score using the
existing independent arithmetic. Retain the stated shared HGB estimator/tokenizer
dependencies and neural-witness limitations. Check exact masks, reason counts,
all 18,000 action rows and each 900-action budget (or min(K,eligible_count)).
Bind a final prelabel seal to all predecessor manifests and the independent
report. Only this complete PASS can precede a separate Gold mapping process;
completion of an individual scoring stage is not that gate.

P0 remains valid complete fresh empirical evidence and contribution assessment,
with historical fit-time provenance limitations and pending CAS qualification.
P1 is baseline/cost/release fidelity. P2 introduces no further search.
