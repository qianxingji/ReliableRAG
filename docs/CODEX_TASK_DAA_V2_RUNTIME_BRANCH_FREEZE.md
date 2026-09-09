# Codex task — DAA-V2 gold-free runtime branch freeze only

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` and the scientific protocol on branch `v2-arbitration-high-standard`.

The 4,500-question cohort, the three candidate pools, and the original-question BM25/Dense/Hybrid retrieval outputs are already frozen. This task is limited to producing and sealing the **shared completed original/repaired branches** that all later arbitration methods will consume.

Authorized in this task:

1. bind each of the 13,500 frozen `(dataset, retriever, sample_id)` traces to its already sealed original Top-5 evidence;
2. run the exact accepted Phase10 reader/generator configuration to produce the original answer `a0`;
3. run the exact accepted Phase10 missing-information repair-query stage;
4. use the already sealed candidate pools/retrieval structures to execute the accepted repair retrieval rule from that repair query;
5. construct repaired evidence `evidence1` using the accepted Phase10 replacement rule;
6. run the exact accepted reader/generator configuration to produce repaired answer `a1`;
7. save one canonical branch ledger shared by DAA-V2, raw HGB and GbV;
8. independently verify all non-model bindings, perform a predeclared deterministic generation replay subset, hash/seal the runtime branch namespace, then STOP.

Not authorized:

- fresh Gold, answer aliases, supporting-fact labels, correctness, EM, F1, recovery, damage, preference/outcome labels;
- any quality-based filtering or manual sample selection;
- likelihood-feature extraction;
- historical HGB/logistic model scoring;
- DAA-V2 model fitting/scoring;
- GbV NLI scoring;
- arbitration action selection or sealing;
- threshold/budget changes;
- evaluation or result interpretation.

Do not print or summarize fresh answer/query content to the author. Until the pre-label action gate is sealed, author-facing reports must contain only counts, hashes, configuration/provenance and integrity status.

STOP immediately after the runtime branch freeze is independently validated and sealed.

## Read first

Read and obey:

- `AGENTS.md`
- `docs/V2_DEVELOPMENT_DECISION.md`
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`
- `docs/V2_PROTOCOL_AMENDMENT_HOTPOT_FULL_VALIDATION.md`
- `docs/V2_PROTOCOL_AMENDMENT_CANDIDATE_POOL_1500.md`
- `docs/CODEX_TASK_DAA_V2_FRESH_COHORT_FREEZE.md`
- `docs/CODEX_TASK_DAA_V2_CANDIDATE_POOL_FREEZE.md`
- `docs/CODEX_TASK_DAA_V2_RETRIEVAL_FREEZE.md`

Also locate the accepted private Phase10 runtime configuration and implementation used by the historical/fresh pipeline. Authenticate it by SHA/provenance before any model forward. Do not reimplement prompts or generation semantics from memory.

## Immutable parent anchors

Before any runtime generation, verify at minimum:

- selected fresh-ID ledger SHA-256: `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`;
- cohort-freeze SHA-256: `0e02d187a379a730f70b24ef33033dbbe93e72c1860fb9b2f20b42b744e7f7f4`;
- candidate-pool-freeze SHA-256: `bbcf1e6110607fc0cf65cdcc2647385a0d50d8aa0645812d82509a82e8b0cded`;
- candidate-pool independent validation SHA-256: `782b813c68013e1ee61844f29e0f1b9b7ed3b7ceb1adef020604a319b9115834`;
- retrieval-freeze SHA-256: `606d6148af431313c86477d22d9c235a72fc236257c5c120772aa495dca3ddca`;
- retrieval independent validation SHA-256: `f53167f1ae5b8b97928a59aed4017fd8d5a1de5a9b68f4decd7bb27e07f74347`;
- retrieval status and independent validation status: `PASS`;
- original retrieval trace count: `13500`;
- original Top-5 complete count: `13500`;
- retrieval fail-closed events: `0`;
- fresh labels / Gold outcome values materialized before this task: `0`;
- reader generation and repair-query generation before this task: `0`;
- likelihood/HGB/DAA-V2/GbV scoring before this task: not started.

Original Top-5 parent hashes:

- 2WikiMultiHopQA: `08e02105887e99133c11f27986d7bbfa83660a45485194d45c160668dd6c2ea0`;
- HotpotQA: `b242d50fa8d51338a7e4cc1f56e028dde6f5aea5b1bdbf2f202df974b8be0cd3`;
- MuSiQue: `963d9c7e7258be42c7c75c139044747454459685a55052a8470e37a930cebe34`.

Candidate-pool hashes:

- 2WikiMultiHopQA: `80ca0941ed74c27e7451cc8e739ae0141b4985945fed8d9dc6d8597068a1bc66`;
- HotpotQA: `73a271c055f17d8ed4f0b630fd15c7ed08032954a38774533cf25e85f8d7b069`;
- MuSiQue: `f2135cc87bf723126724128e7a221a7d80516972c98338d22b4f3fbd77ab1cf3`.

If any parent anchor differs, STOP before a model forward.

## Stage A — authenticate and freeze the runtime generation configuration

Locate the exact accepted private Phase10 implementation/configuration that determines:

- reader model and exact revision;
- tokenizer/chat template and revision/cache inventory;
- evidence serialization/rendering;
- original-answer prompt;
- missing-information repair-query prompt/logic;
- repair retrieval dispatch by retriever;
- repaired-evidence construction;
- repaired-answer prompt;
- maximum input/evidence budget;
- decoding settings, stop conditions and output parsing;
- dtype/device/batch settings;
- deterministic CUDA/PyTorch settings;
- retry/fail-closed behavior.

The prospective reader must remain:

`Qwen/Qwen2.5-3B-Instruct` at revision
`aa8e72537993ba99e69dfaafa59ed015b17504d1`.

The already frozen runbook constraints remain: deterministic decoding, BF16 CUDA, batch size 1, Top-5 original evidence, 16,000-character evidence budget, and the accepted Phase10 repair behavior.

Do not invent any missing generation parameter. If the exact accepted config/prompt/parser implementation cannot be located and SHA-authenticated, STOP.

Before real generation, write:

`outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json`

containing only configuration/provenance/hashes, not benchmark answer content.

Also record a complete opaque inventory/hash of the Qwen model/tokenizer files actually used.

## Stage B — establish the exact 13,500 trace order

Construct the trace key sequence only from the frozen selected IDs and frozen original retrieval outputs.

Require exactly:

- 4,500 question clusters;
- 13,500 unique `(dataset, retriever, sample_id)` traces;
- 1,500 traces per dataset x retriever stratum;
- retriever set exactly `bm25`, `dense`, `hybrid`;
- original Top-5 evidence for every trace bound byte-for-byte to the retrieval-freeze artifacts;
- no resampling, dropping or reordering based on model output.

Save a trace-key/provenance manifest before model generation.

## Stage C — original answer generation

Using the authenticated accepted runtime only, generate `a0` once for every trace from the frozen question and original Top-5 evidence.

Requirements:

- exact accepted prompt/chat-template/rendering;
- deterministic decoding only;
- no Gold/supporting-fact/answer-alias access;
- no human inspection-based rerun;
- cache every raw generation receipt/token sequence needed for reproducibility;
- parse using only the accepted parser;
- preserve empty/fail-closed outputs exactly rather than repairing them manually.

Do not compute EM/F1 or compare with Gold.

## Stage D — repair-query generation

Run the exact accepted Phase10 repair-query stage on every trace using only the runtime inputs permitted by that implementation.

Do not change the prompt, query length, parser, fallback, or retry rule based on fresh outputs.

Save the repair query privately for subsequent repair retrieval, but do not print sample queries in the author-facing report.

If the accepted Phase10 implementation does not use a separate model forward for repair-query construction, preserve that actual behavior and report the true call counters. Do not force an artificial call count.

## Stage E — repair retrieval and repaired evidence

Reuse the already frozen candidate pools, BM25 structures and dense document embeddings. Do not rebuild pools or document embeddings.

For each trace, run the accepted repair retrieval under the same retriever family as the original trace and apply the frozen repair rule from the accepted Phase10 pipeline.

The historical rule to preserve is the accepted first eligible document in the repair ranking (searched to the accepted depth, historically depth 50) that is outside the original Top-5, replacing original rank 5 while retaining original ranks 1--4. The exact native implementation/tie rules are authoritative; if local accepted code differs from this summary, STOP and report the discrepancy rather than silently choosing one.

Save:

- repair ranking/binding ledger;
- repaired Top-5 evidence binding;
- explicit fail-closed reason for any trace where an accepted replacement cannot be formed.

No retrieval-quality metric or Gold-aware check is permitted.

## Stage F — repaired answer generation

Generate `a1` from the repaired evidence with the exact same authenticated reader model/runtime family and the accepted repaired-answer prompt/parser.

Preserve all empty/fail-closed outputs. Do not rerun individual traces because an answer looks poor.

## Stage G — canonical shared branch ledger

Create exactly one method-independent canonical branch ledger:

`outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl`

with the runtime fields required by the downstream arbitration interface:

- `dataset`
- `retriever`
- `sample_id`
- `question`
- `a0`
- `a1`
- `evidence0`
- `evidence1`

If the accepted downstream schema requires additional **label-free provenance fields**, keep them in a separate sidecar rather than casually expanding the canonical interface.

DAA-V2, raw HGB and GbV must later consume this same canonical branch ledger. No method-specific branch regeneration is allowed.

The canonical ledger must contain exactly 13,500 unique trace rows and no Gold/outcome fields.

## Stage H — independent non-model validation

Use a separate validator that does not import the runtime builder to verify at minimum:

- exact 13,500 trace-key set and sequence;
- original evidence bindings match the sealed retrieval Top-5 parents;
- every repaired evidence row preserves accepted original ranks and uses the exact repair replacement documented by the repair-ranking ledger;
- repair replacement is not already in original Top-5 where replacement is claimed;
- document IDs/text are bound to the sealed candidate pools;
- canonical branch schema is exact;
- no Gold/outcome/evaluation fields are present;
- no trace was dropped or duplicated;
- all parent hashes match;
- all reported call counters reconcile with saved receipts.

This validator must not compute answer quality.

## Stage I — predeclared deterministic generation replay subset

Before any human inspection of fresh answers, deterministically select a replay subset using only trace identifiers:

For each of the 9 dataset x retriever strata, rank traces by

`SHA256("daa-v2-runtime-replay-v1|dataset|retriever|sample_id")`

then `sample_id`, and select the first **20 traces per stratum** (180 traces total).

Replay the complete authorized runtime branch procedure for only these 180 traces using the exact same frozen configuration.

Require exact equality of:

- prompt/input hashes;
- generated token-ID sequences for each model-generated stage;
- parsed `a0`;
- repair query (or deterministic non-model query result if applicable);
- repair retrieval binding;
- repaired Top-5 binding;
- generated token-ID sequence for `a1`;
- parsed `a1`.

If any replay mismatch occurs, preserve it and FAIL the runtime freeze. Do not change CUDA flags, seeds, prompts or parsers and rerun until it matches.

The replay subset is a reproducibility check only; it does not create extra evaluation questions and cannot be used to select/drop traces.

## Stage J — seal and complete-file manifest

Write:

- `RUNTIME_BRANCH_FREEZE.json`
- `independent_validation.json`
- `RUNTIME_HANDOFF.md`
- `SHA256_MANIFEST.json`

inside `outputs/daa_v2_fresh_v1/runtime_branch_freeze/`.

The freeze seal must record at minimum:

- status PASS/FAIL;
- parent cohort/pool/retrieval hashes;
- runtime config hash;
- Qwen model/tokenizer revision and cache fingerprint;
- trace count = 13,500;
- question clusters = 4,500;
- counts per dataset/retriever;
- original-answer generation counters;
- repair-query counters and actual implementation mode;
- repair retrieval counters;
- repaired-answer generation counters;
- fail-closed counts by stage/reason;
- canonical branch ledger SHA-256;
- repair ranking/binding SHA-256;
- deterministic replay subset rule/count/status;
- independent validation SHA-256;
- fresh labels accessed = 0;
- Gold/outcome values materialized = 0;
- likelihood scoring started = false;
- HGB/V2/GbV scoring started = false;
- arbitration action selection/sealing started = false;
- evaluation started = false;
- protected parent namespaces unchanged;
- explicit HARD STOP.

The complete-file manifest must hash every regular file in the runtime branch namespace except itself and classify files containing fresh question/evidence/answer/query content as private benchmark-derived artifacts not for public redistribution.

## Final report to author

Return only configuration/count/hash/integrity facts. Do not quote or summarize any fresh questions, evidence, repair queries, `a0`, or `a1`.

Report:

1. PASS/FAIL;
2. Qwen model/revision/runtime config hash;
3. 13,500 trace / 4,500 question coverage;
4. per-stage actual model/retrieval call counters;
5. fail-closed counts by stage;
6. canonical branch ledger SHA-256;
7. repair-binding ledger SHA-256;
8. replay subset count and exact-match status;
9. independent validation SHA-256;
10. runtime freeze SHA-256;
11. complete-file manifest hash/receipt;
12. confirmation fresh Gold/outcome access remained zero;
13. confirmation likelihood/HGB/DAA-V2/GbV scoring and action selection did not start;
14. confirmation no parent cohort/pool/retrieval artifact changed.

## HARD STOP

STOP after the runtime branch freeze and complete-file manifest.

A PASS authorizes nothing beyond existence of the sealed, shared label-free completed branches. Likelihood/base-feature extraction, DAA-V2 fitting/scoring, raw HGB scoring, GbV scoring, action sealing, Gold mapping and evaluation require a new explicit author instruction.