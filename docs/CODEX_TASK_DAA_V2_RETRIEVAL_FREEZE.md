# Codex task — DAA-V2 retrieval/index freeze only

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` and the scientific protocol on branch `v2-arbitration-high-standard`.

The 4,500-question cohort and the three shared candidate pools are already frozen. This task is limited to **building/verifying the frozen retrieval infrastructure and producing the label-free original retrieval rankings for BM25, Dense, and Hybrid/RRF**.

Authorized in this task:

- load the already frozen candidate pools;
- load the already frozen 4,500-question runtime projections;
- build BM25 retrieval structures;
- run the pinned dense embedding model needed to build/query the dense index;
- construct the accepted dense index using the historical implementation;
- run original-question BM25, Dense, and Hybrid/RRF retrieval;
- save deterministic retrieval rankings and the original Top-5 evidence bindings;
- replay/independently validate the retrieval outputs and seal them.

Not authorized in this task:

- Qwen or any reader/generator call;
- original-answer generation;
- missing-information/repair-query generation;
- repair retrieval from a generated repair query;
- repaired-answer generation;
- reader likelihood scoring;
- HGB, DAA-V2, or GbV scoring;
- arbitration action selection/sealing;
- fresh Gold/correctness/supporting facts/aliases/EM/F1/recovery/damage/outcome access;
- evaluation.

STOP after the retrieval freeze is independently validated and sealed.

## Read first

Read and obey:

- `AGENTS.md`
- `docs/V2_DEVELOPMENT_DECISION.md`
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`
- `docs/V2_SAMPLE_SIZE_PLAN.md`
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`
- `docs/V2_PROTOCOL_AMENDMENT_HOTPOT_FULL_VALIDATION.md`
- `docs/V2_PROTOCOL_AMENDMENT_CANDIDATE_POOL_1500.md`
- `docs/CODEX_TASK_DAA_V2_FRESH_COHORT_FREEZE.md`
- `docs/CODEX_TASK_DAA_V2_CANDIDATE_POOL_FREEZE.md`

Treat all historical experiment namespaces, both availability-audit namespaces, `cohort_freeze/`, and `pool_freeze/` as immutable inputs.

## Accepted parent anchors

Before any index/model/retrieval work, verify at minimum:

- cohort-freeze status: `PASS`;
- cohort-freeze SHA-256: `0e02d187a379a730f70b24ef33033dbbe93e72c1860fb9b2f20b42b744e7f7f4`;
- selected ID-ledger SHA-256: `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`;
- candidate-pool-freeze status: `PASS`;
- candidate-pool-freeze SHA-256: `bbcf1e6110607fc0cf65cdcc2647385a0d50d8aa0645812d82509a82e8b0cded`;
- candidate-pool independent validation SHA-256: `782b813c68013e1ee61844f29e0f1b9b7ed3b7ceb1adef020604a319b9115834`;
- exactly 1,500 frozen contributors/evaluation questions per dataset;
- frozen pool document counts:
  - 2WikiMultiHopQA: `9026`;
  - HotpotQA: `14584`;
  - MuSiQue: `19554`;
- frozen pool SHA-256 values:
  - 2WikiMultiHopQA: `80ca0941ed74c27e7451cc8e739ae0141b4985945fed8d9dc6d8597068a1bc66`;
  - HotpotQA: `73a271c055f17d8ed4f0b630fd15c7ed08032954a38774533cf25e85f8d7b069`;
  - MuSiQue: `f2135cc87bf723126724128e7a221a7d80516972c98338d22b4f3fbd77ab1cf3`;
- candidate-pool runtime projection SHA-256 values:
  - 2WikiMultiHopQA: `b67501af86489366f9d61aa4a1ac7d25d5e43a8c1c728a240e93f98d67bbb8d3`;
  - HotpotQA: `d36662b412cb14bbc3590c59fad517e086fb5b0014c87cbca36a9bc263183868`;
  - MuSiQue: `36f13771ac1417f733af96d42fad72e98b381f175446b66ab618cf73c4de83a9`;
- candidate-pool clean second build exact reproduction: `PASS`;
- parent retrieval/index/generation/scoring/Gold counters are zero.

If any anchor differs, STOP.

## Frozen retrieval implementation

Reuse the accepted private retrieval implementation and configuration from the historical/Phase10 experiment. Do not implement a new retriever merely because it is convenient.

The following are fixed scientific requirements:

- retrievers: BM25, Dense, Hybrid/RRF;
- dense model: `BAAI/bge-base-en-v1.5`;
- dense model revision: `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`;
- original evidence delivered downstream: Top-5 ordered passages;
- all three retrievers use the exact same frozen dataset pool for a dataset;
- no Gold/supporting-fact/answer/correctness signal enters indexing or retrieval;
- query is the frozen question text from the selected runtime projection;
- Hybrid/RRF must use the exact accepted historical implementation and parameters.

Before executing, resolve and record the exact accepted values for any implementation-specific settings not enumerated here, including at minimum BM25 tokenization/parameters, dense text rendering/normalization/batching/index type, RRF constant and source-ranking depth, tie-breaking, and document-ID ordering. These values must come from verified historical configuration/source artifacts, not from new tuning.

If an exact accepted setting cannot be established from the private project, STOP and report the unresolved field. Do not guess.

## Dense model and environment provenance

Before any embedding inference:

- verify the exact pinned BGE revision;
- record tokenizer/model file hashes or an immutable cache/model snapshot fingerprint;
- record `transformers`, `torch`, CUDA, FAISS (if used), NumPy, and relevant retrieval-package versions;
- record device and numeric dtype actually used;
- require eval/inference mode and no gradients;
- do not fine-tune the retriever.

A missing pinned model may be acquired only at the exact frozen revision. Record acquisition provenance. Do not silently substitute another BGE/E5 model.

## Output namespace

Create only:

`outputs/daa_v2_fresh_v1/retrieval_freeze/`

Do not mutate `pool_freeze/`, `cohort_freeze/`, audits, historical outputs, or model controls.

Recommended subdirectories:

- `indexes/`
- `rankings/`
- `top5/`
- `manifests/`
- `logs/`

## Stage A — preflight and immutable binding

Create a preflight record binding:

- exact 4,500 selected IDs;
- exact three runtime projections;
- exact three candidate pools;
- exact pool manifests/fingerprints;
- accepted retrieval implementation source hashes;
- resolved retriever configuration;
- pinned BGE revision/environment;
- output namespace state before execution.

Require zero fresh-label/Gold access.

Write:

`outputs/daa_v2_fresh_v1/retrieval_freeze/PREFLIGHT_INPUT_VERIFICATION.json`

## Stage B — build retrieval structures

Build the BM25 and Dense retrieval structures only from the frozen pool documents.

Save enough provenance to bind each index to:

- pool SHA-256;
- canonical document-ID sequence SHA-256;
- retrieval implementation/config hash;
- dense model revision and model/cache fingerprint where applicable.

Do not add documents, remove documents, or re-deduplicate here. The pool contents are immutable.

Hybrid/RRF is a deterministic fusion of the accepted BM25/Dense rankings; do not create a separately tuned hybrid corpus or model.

## Stage C — original-question retrieval

For each of the 4,500 frozen questions, run exactly one accepted original retrieval under each retriever:

- BM25;
- Dense;
- Hybrid/RRF.

Expected trace count:

`4,500 questions x 3 retrievers = 13,500 original-retrieval traces`.

Save a label-free ranking ledger that includes stable identifiers and the ordered retrieved document IDs/scores/ranks needed to reproduce Top-5 and the accepted Hybrid fusion. Do not include benchmark answers, supporting-fact labels, correctness, or outcome fields.

Also save a separate canonical Top-5 binding for each trace. Each trace must contain exactly five ordered document IDs unless the accepted retrieval implementation has a pre-existing fail-closed rule for an impossible pool condition; any such event must be reported and must not be silently dropped.

Do not generate an answer from the Top-5 in this task.

## Stage D — invariants and coverage

Validate at minimum:

- exactly 4,500 unique question clusters;
- exactly 13,500 `(dataset, sample_id, retriever)` traces;
- exactly one BM25, Dense, Hybrid trace per selected question;
- no selected question dropped;
- no unselected question added;
- every retrieved document ID exists in the exact frozen dataset pool;
- no duplicate document IDs within one Top-5;
- Top-5 ordering matches the saved ranking ledger;
- Hybrid rankings are independently recomputable from the saved BM25/Dense rankings and frozen RRF rule;
- all retrieval artifacts are label-free;
- no answer/supporting-fact/alias/correctness/outcome field exists in the retrieval namespace.

## Stage E — reproducibility replay

Without changing the pools, models, config, or selected IDs, replay the retrieval stage independently enough to test determinism.

At minimum require exact byte/hash or exact canonical ranking equivalence for:

- BM25 ranking ledger;
- Dense ranking ledger;
- Hybrid ranking ledger;
- Top-5 bindings;
- trace key sequence.

Do not select between two builds based on retrieval quality. If a deterministic mismatch occurs, STOP and preserve both outputs for diagnosis.

## Stage F — independent validation and retrieval freeze seal

Use an independent validator that does not simply trust the builder receipts.

Write:

- `outputs/daa_v2_fresh_v1/retrieval_freeze/independent_validation.json`
- `outputs/daa_v2_fresh_v1/retrieval_freeze/RETRIEVAL_FREEZE.json`
- `outputs/daa_v2_fresh_v1/retrieval_freeze/SHA256_MANIFEST.json`

`RETRIEVAL_FREEZE.json` must contain at minimum:

- `status = PASS` only when all checks pass;
- parent cohort-freeze and candidate-pool-freeze hashes;
- selected-ID hash;
- candidate-pool hashes/fingerprints;
- exact retriever config and implementation hashes;
- BGE model name/revision/fingerprint;
- index/structure hashes;
- per-dataset and per-retriever trace counts;
- ranking-ledger hashes;
- Top-5 binding hashes;
- reproducibility replay status;
- `fresh_labels_accessed = 0`;
- `gold_outcome_values_materialized = 0`;
- `reader_generation_calls = 0`;
- `repair_query_generation_calls = 0`;
- `repair_retrieval_calls = 0`;
- `likelihood_scoring_started = false`;
- `v2_hgb_gbv_scoring_started = false`;
- `action_selection_or_sealing_started = false`;
- `evaluation_started = false`;
- explicit hard stop.

Dense embedding calls used to build/query the authorized retrieval system are expected and must be counted separately from reader/generator/model-selection calls.

## Scientific interpretation boundary

This retrieval freeze is an upstream shared-input stage. It must not be inspected to choose a different cohort, candidate pool, retriever configuration, model, budget, or method.

Retrieval-quality Gold metrics such as supporting-fact recall are **not** authorized here because they require Gold annotations. They may be computed only later under separately authorized evaluation and must not alter the runtime pipeline.

## Final report to author

Return only label-free execution/provenance facts:

1. retrieval-freeze PASS/FAIL;
2. exact retrieval configuration and BGE revision;
3. dataset pool hashes used;
4. BM25/Dense/Hybrid trace counts;
5. total trace count;
6. Top-5 completeness count/fail-closed events;
7. index/embedding/ranking artifact hashes;
8. exact replay/determinism result;
9. independent-validation SHA-256;
10. retrieval-freeze SHA-256;
11. complete-file manifest SHA-256;
12. zero fresh-Gold, zero reader-generation, zero repair-query, zero repair-retrieval, zero likelihood/V2/HGB/GbV/action/evaluation evidence.

Do not report question text, passage text, answers, supporting facts, or correctness outcomes.

## HARD STOP

STOP after retrieval freeze, independent validation, and complete-file hashing.

A PASS authorizes **nothing beyond the existence of the sealed original retrieval layer**. Reader generation, repair-query generation, repair retrieval, repaired-answer generation, likelihood scoring, DAA-V2/HGB/GbV scoring, action sealing, Gold mapping, and evaluation each require a new explicit author instruction.
