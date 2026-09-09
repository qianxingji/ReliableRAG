# Codex task — DAA-V2 candidate-pool freeze only

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` and the scientific protocol on branch `v2-arbitration-high-standard`.

The 4,500-question fresh cohort has already been selected and sealed. This task is limited to **building, validating, and sealing the shared label-free candidate pools and selected runtime projections** for the three datasets.

Do **not** run BM25, Dense, Hybrid/RRF, or repair retrieval. Do **not** build dense embeddings or retrieval indexes. Do **not** generate original answers, repair queries, or repaired answers. Do **not** run reader likelihood scoring, HGB scoring, DAA-V2 scoring, or GbV scoring. Do **not** select or seal arbitration actions. Do **not** load/map fresh Gold, correctness, supporting facts, aliases, EM/F1, recovery/damage, or outcome values.

Stop immediately after candidate-pool freeze integrity is independently validated and sealed.

## Read first

Read and obey:

- `AGENTS.md`
- `docs/V2_DEVELOPMENT_DECISION.md`
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`
- `docs/V2_PROTOCOL_AMENDMENT_HOTPOT_FULL_VALIDATION.md`
- `docs/V2_PROTOCOL_AMENDMENT_CANDIDATE_POOL_1500.md`
- `docs/V2_SAMPLE_SIZE_PLAN.md`
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`
- `docs/CODEX_TASK_DAA_V2_FRESH_COHORT_FREEZE.md`

Treat all historical experiment namespaces, both availability-audit namespaces, and `outputs/daa_v2_fresh_v1/cohort_freeze/` as immutable inputs.

## Accepted cohort-freeze anchors

Before reading benchmark runtime content, verify all of the following from the preserved cohort-freeze artifacts:

- cohort freeze status: `PASS`;
- branch: `v2-arbitration-high-standard`;
- selected total: `4500`;
- selected count per dataset: exactly `1500` each;
- selected/forbidden overlap: `0`;
- deterministic reselection exact match: `true`;
- selected ID ledger SHA-256: `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`;
- selection manifest SHA-256: `52ec0c3634441f8c6952dd0af2d981cfa1d31b6199f6a5d87fa1aed87310f003`;
- independent selection validation SHA-256: `7fed4ebc7f79e05be95ada10fc8a12a0788e78d2f981fa362f42199afcc683a9`;
- cohort freeze file SHA-256: `0e02d187a379a730f70b24ef33033dbbe93e72c1860fb9b2f20b42b744e7f7f4`;
- forbidden union SHA-256: `4faff825a33d512538b753c4687441aea9f388d493618fe5dfa134518185202b`;
- source ID ledger SHA-256 values:
  - HotpotQA: `51e70aeed94a1e4939b41ece4c80d03e571aab410fc5cf6324f503624c076d21`;
  - 2WikiMultiHopQA: `e90e093a710788607bbb40a5c4dae4d0cf320e1b3e22800642deebd0610342ff`;
  - MuSiQue: `780de0e3028e0da1bad567922aef7a36d500c600d6b31a09c414087c78fd3292`;
- pre-task counters: model/generation/retrieval/fresh-label = zero;
- candidate pool, retrieval index, generation, likelihood scoring, V2/HGB/GbV scoring, action selection, Gold mapping, and evaluation all not started.

If any anchor differs, STOP without constructing a pool.

## Frozen contributor rule

The contributor rule is prospectively fixed by `docs/V2_PROTOCOL_AMENDMENT_CANDIDATE_POOL_1500.md`.

For each dataset, the candidate-pool contributors are **exactly the already frozen 1,500 evaluation IDs from that dataset**.

No extra corpus-only contributor rows may be added. No selected evaluation row may be dropped. No alternate contributor seed or subset is permitted.

Thus create three identifier-only contributor ledgers as deterministic projections of the frozen 4,500-ID cohort:

- `hotpotqa_contributors.jsonl` — 1,500 rows;
- `2wikimultihopqa_contributors.jsonl` — 1,500 rows;
- `musique_contributors.jsonl` — 1,500 rows.

Each row must contain exactly:

```json
{"dataset":"...","sample_id":"..."}
```

The union of these three contributor ledgers must equal `selected_fresh_ids.jsonl` exactly as a set.

## Source/runtime inputs

Use the already accepted source bytes/projections and their recorded hashes. Do not substitute a new benchmark mirror/source merely because it is convenient.

### HotpotQA

Use the pinned complete `hotpotqa/hotpot_qa`, config `distractor`, split `validation` source established by the successful Hotpot-full audit:

- revision: `1908d6afbbead072334abe2965f91bd2709910ab`;
- accepted raw/cache artifact SHA-256: `c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6`;
- accepted complete runtime projection SHA-256: `c763594e68feec3c5f1ff6d682a761e43c3004ecc0304cfb5a1034d11e7d2503`.

Prefer projecting the selected 1,500 rows from the already validated full runtime projection rather than reopening raw benchmark fields unnecessarily.

### 2WikiMultiHopQA

Use the accepted corrected `dev.json` source:

- raw-source SHA-256: `79f77ae104088ea8e25b1a65dbece768d45771194663bc5660ec9a98070dadf5`.

Reuse the validated Phase10 source-projection guard to emit selected runtime-only rows.

### MuSiQue

Use the accepted train source used in the availability/cohort protocol:

- raw-source SHA-256: `83a75b1e11e4e9bb8f8308e72ac40ca617ae4431b3a0d955b61cab259248490a`.

Reuse the validated Phase10 source-projection guard to emit selected runtime-only rows.

Do not switch MuSiQue back to dev.

## Gold-free runtime projection contract

For each selected row, materialize only runtime-visible fields required to bind the question and build the pooled corpus. Preserve the existing private pipeline's canonical field names and structure.

Allowed semantic content:

- dataset;
- sample/question ID;
- question text;
- ordered context/passage titles;
- ordered context/passage text/sentences/paragraph text;
- non-Gold structural indices required to preserve deterministic order.

Forbidden content includes, but is not limited to:

- answer;
- answer aliases / answer IDs;
- supporting facts / supporting flags;
- evidence/evidence IDs when they encode Gold support;
- decomposition annotations;
- `is_supporting`;
- correctness labels;
- EM/F1;
- recovery/damage/net labels;
- Gold-aware retrieval or oracle fields.

The projector must fail closed on prohibited emitted fields. Do not merely delete them after writing a broad raw projection.

Write selected runtime projections under a new namespace:

`outputs/daa_v2_fresh_v1/pool_freeze/runtime_projection/`

These files contain private benchmark text and must be classified private/not-for-publication.

## Reuse the accepted pooled-corpus implementation

Locate the exact validated Phase10 source-projection and candidate-corpus construction implementation from the accepted private project/provenance.

The accepted Phase10 evidence previously recorded implementation hashes for source projection/corpus construction. Resolve the actual accepted files from the existing manifests and verify them before execution. If the accepted implementation cannot be provenance-verified, STOP rather than writing a new approximate builder.

Do not modify the historical accepted implementation in place.

If a thin new V2 wrapper is needed only to feed the frozen 1,500 contributor IDs into that accepted implementation, keep it in the new `pool_freeze` namespace or a clearly named V2 script and hash it. The wrapper must not alter corpus semantics.

## Frozen candidate-pool semantics

For each dataset independently:

1. use exactly the 1,500 selected contributor rows;
2. pool all allowed context/passages from those rows;
3. apply the accepted canonical rendering and deduplication behavior;
4. deduplicate using the accepted normalized title plus passage/sentence-content rule;
5. preserve deterministic document identifiers/order according to the accepted implementation;
6. produce exactly one shared candidate pool for that dataset;
7. do not compute BM25 statistics, dense embeddings, nearest-neighbor indexes, RRF rankings, or retrieval results in this task.

The same frozen dataset pool will later be consumed by BM25, Dense, Hybrid/RRF, and the fixed repair retrieval. No arbitration method receives a different pool.

Do not assume or hard-code the final document counts. Measure them from the deterministic build.

## Output namespace

Create only:

`outputs/daa_v2_fresh_v1/pool_freeze/`

Suggested structure:

```text
pool_freeze/
  contributors/
    hotpotqa_contributors.jsonl
    2wikimultihopqa_contributors.jsonl
    musique_contributors.jsonl
  runtime_projection/
    hotpotqa_selected_runtime.jsonl
    2wikimultihopqa_selected_runtime.jsonl
    musique_selected_runtime.jsonl
  pools/
    hotpotqa_documents.jsonl
    2wikimultihopqa_documents.jsonl
    musique_documents.jsonl
  manifests/
    hotpotqa_pool_manifest.json
    2wikimultihopqa_pool_manifest.json
    musique_pool_manifest.json
  independent_validation.json
  CANDIDATE_POOL_FREEZE.json
  SHA256_MANIFEST.json
```

Equivalent deterministic paths are acceptable if documented, but do not write into historical/audit/cohort-freeze namespaces.

## Required per-dataset pool manifest

For each dataset record at least:

- dataset;
- contributor_count = `1500`;
- contributor ID-ledger SHA-256;
- selected cohort parent SHA-256;
- raw/cache source digest reference;
- selected runtime-projection SHA-256;
- source-projection implementation path/hash;
- corpus-construction implementation path/hash;
- canonicalization/dedup rule/version/hash;
- passage/document count before deduplication;
- duplicate count removed;
- final document count;
- unique document-ID count;
- duplicate document-ID count = `0`;
- exact final pool SHA-256;
- final pool byte size;
- prohibited-field scan status = PASS;
- Gold/outcome values materialized = `0`;
- retrieval/index/model/generation/scoring calls = `0`.

## Double-build reproducibility requirement

Build the three candidate pools twice from the same frozen inputs using a clean second output location or a temporary deterministic rebuild namespace.

Require for every dataset:

- identical contributor hashes;
- identical selected runtime-projection hashes;
- identical pre-dedup counts;
- identical dedup counts;
- identical final document counts;
- identical final pool SHA-256;
- identical canonical document-ID sequence.

The second build is only a reproducibility check. Retain the first accepted pool as the canonical pool and record the second-build fingerprints in the independent validation. Do not choose whichever build is more favorable.

## Independent validation

Independently validate the candidate-pool freeze without trusting only the construction script's own manifests.

At minimum independently verify:

- parent cohort freeze hash and status;
- contributor ledgers contain exactly 1,500 IDs per dataset and union to exactly the 4,500 selected IDs;
- zero contributor ID lies outside the frozen selected cohort;
- selected runtime projection contains exactly the selected IDs;
- prohibited emitted field names are absent;
- no Gold/outcome values are intentionally materialized by the validator;
- pool document IDs are unique;
- pool manifests' counts/hashes match independently recomputed values;
- clean second build exactly reproduces all pool fingerprints;
- no retrieval/index/generation/model/scoring outputs exist in the authorized namespace;
- all historical protected namespaces and cohort-freeze inputs remain unchanged.

Write:

`outputs/daa_v2_fresh_v1/pool_freeze/independent_validation.json`

Status must be PASS before sealing.

## Candidate-pool freeze seal

Write:

`outputs/daa_v2_fresh_v1/pool_freeze/CANDIDATE_POOL_FREEZE.json`

It must contain at least:

- status = PASS only if all independent checks pass;
- UTC creation timestamp;
- branch, Git commit and tree;
- protocol snapshot hash;
- parent `COHORT_FREEZE.json` SHA-256 = `0e02d187a379a730f70b24ef33033dbbe93e72c1860fb9b2f20b42b744e7f7f4`;
- parent selected ID ledger SHA-256 = `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`;
- contributor rule = exactly 1,500 frozen evaluation IDs per dataset, no additional corpus-only rows;
- contributor count and hash per dataset;
- runtime projection hash per dataset;
- final document count and pool SHA-256 per dataset;
- accepted implementation hashes;
- independent validation SHA-256;
- `candidate_pool_construction_started = true`;
- `candidate_pool_construction_completed = true`;
- `retrieval_index_construction_started = false`;
- `retrieval_calls = 0`;
- `model_calls = 0`;
- `generation_calls = 0`;
- `likelihood_scoring_started = false`;
- `v2_hgb_gbv_scoring_started = false`;
- `action_selection_or_sealing_started = false`;
- `fresh_labels_accessed = 0`;
- `gold_mapping_started = false`;
- `evaluation_started = false`;
- explicit hard stop.

## Hash manifest and preservation audit

Create a SHA-256 manifest covering every regular file created under `pool_freeze/`, excluding the manifest itself.

Classify private runtime projections and candidate-pool text as private benchmark-derived material not for public redistribution.

Verify that:

- historical experiment namespaces are byte-identical to their pre-task anchors;
- both availability-audit namespaces are unchanged;
- `cohort_freeze/` is unchanged;
- no raw source cache/model binary has been copied into the pool-freeze namespace unless explicitly necessary and authorized; prefer path/hash references.

## Final report to author

Return only control/provenance facts, not benchmark text:

1. task status PASS/FAIL;
2. contributor counts and hashes per dataset;
3. selected runtime-projection hashes per dataset;
4. pre-dedup, removed-duplicate, and final document counts per dataset;
5. final candidate-pool SHA-256 per dataset;
6. source-projection and corpus-builder implementation hashes;
7. clean second-build exact-reproduction PASS/FAIL;
8. prohibited-field/Gold-materialization checks;
9. independent validation SHA-256;
10. candidate-pool freeze seal SHA-256;
11. pool-freeze hash-manifest SHA-256;
12. confirmation that retrieval/indexing, generation, likelihood scoring, V2/HGB/GbV scoring, action selection, Gold mapping, and evaluation did not start.

Do not include question text, context text, answers, aliases, supporting facts, or predictions in the author-facing report.

## HARD STOP

STOP after `CANDIDATE_POOL_FREEZE.json`, independent validation, and the SHA-256 manifest are complete and PASS.

A PASS here authorizes **only the existence of frozen shared candidate pools**. It does not authorize retrieval, index construction, generation, scoring, action sealing, Gold mapping, or evaluation. A new explicit author instruction is required for the next stage.
