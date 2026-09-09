# Codex task — DAA-V2 HotpotQA full-validation availability rerun only

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` and the scientific protocol on branch `v2-arbitration-high-standard`.

This task exists only because the first identifier-only availability audit failed on the 4,000-row local HotpotQA materialization. It is limited to:

1. establishing a complete, provenance-controlled HotpotQA distractor-validation runtime projection;
2. rebuilding the HotpotQA ID-only source inventory;
3. rerunning the identifier-only availability audit with zero selected questions;
4. independently validating the new audit;
5. stopping.

Do **not** select the final fresh cohort. Do **not** run retrieval. Do **not** generate answers or repair queries. Do **not** run reader likelihood scoring, V2 scoring, HGB scoring, or GbV scoring. Do **not** load/map fresh Gold/correctness/outcome values.

## Read first

Read and obey:

- `AGENTS.md`
- `docs/V2_DEVELOPMENT_DECISION.md`
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`
- `docs/V2_PROTOCOL_AMENDMENT_HOTPOT_FULL_VALIDATION.md`
- `docs/V2_SAMPLE_SIZE_PLAN.md`
- `docs/V2_AVAILABILITY_AUDIT_SCHEMA.json`
- `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`

Preserve the prior failed audit and all historical experiment namespaces byte-for-byte.

## Accepted previous-audit anchors

Verify these before doing anything else:

- previous availability audit status: `FAIL`;
- previous Hotpot source unique IDs: `4000`;
- previous Hotpot source/forbidden overlap: `3800`;
- previous Hotpot available IDs: `200`;
- previous forbidden-union unique Hotpot IDs: `5600`;
- previous 2Wiki available IDs: `8776`;
- previous MuSiQue available IDs: `19338`;
- previous union SHA-256: `4faff825a33d512538b753c4687441aea9f388d493618fe5dfa134518185202b`;
- previous Hotpot ID-ledger SHA-256: `50abfc6646469198558f3323ad4b2cd65f9726c047df462882657270a3ae9f90`;
- private-artifact verification status: PASS;
- previous model/generation/retrieval/fresh-label/selection counts: all zero.

If these anchors do not match the preserved audit artifacts, stop.

## Stage A — locate a complete HotpotQA distractor-validation source

Expected complete split: **7,405 unique IDs**.

Use this preference order:

1. Search only known project/cache locations for an existing complete `hotpot_dev_distractor_v1.json` or equivalent accepted cached materialization. Do not perform broad unrelated filesystem crawling.
2. Search the existing Hugging Face cache for `hotpotqa/hotpot_qa`, config `distractor`, split `validation`.
3. If no complete local source exists and network acquisition is allowed in the current environment, acquire `hotpotqa/hotpot_qa` distractor validation from Hugging Face with an explicitly recorded repository/dataset revision and cache path.

The earlier CMU HTTP/HTTPS failures are preserved evidence. Do not overwrite or delete them.

Do not substitute HotpotQA train, fullwiki, BEIR, synthetic data, another benchmark, or a smaller target.

If a complete 7,405-row source cannot be established, write a new FAIL audit supplement and STOP.

## Stage B — source-equivalence validation

Before using the complete source, establish all of the following:

- 7,405 rows and 7,405 unique question IDs;
- duplicate IDs = 0;
- every one of the previous 4,000 Hotpot IDs is contained in the complete source;
- for the shared 4,000 IDs, construct a **label-free runtime projection** containing only the source fields needed by the accepted pipeline: ID, question, and ordered context title/sentence content;
- hash canonical per-ID runtime projections in the old and complete materializations and require exact equality for all 4,000 shared IDs;
- materialize no answer/supporting-fact/correctness/evaluation values into the audit namespace;
- record source transport, source revision when applicable, raw/cache artifact path, file/dataset hashes, row count, ID-set hash, and shared-projection hash.

Write:

`outputs/daa_v2_fresh_v1/audit_hotpot_full/HOTPOT_FULL_SOURCE_EQUIVALENCE.json`

Status must be PASS before continuing.

If equivalence fails, STOP. Do not repair source records manually.

## Stage C — rebuild Hotpot identifier-only source ledger

Write exactly:

`outputs/daa_v2_fresh_v1/audit_hotpot_full/hotpot_source_ids_full.jsonl`

Every row must contain only:

```json
{"dataset":"hotpotqa","sample_id":"..."}
```

Require:

- row count = 7405;
- unique count = 7405;
- duplicate count = 0;
- dataset alias normalized to canonical `hotpotqa`;
- no benchmark content in this ID ledger.

Save its SHA-256.

## Stage D — reuse rather than mutate accepted non-Hotpot inputs

Reuse the accepted 2Wiki and MuSiQue source ID ledgers from the first audit after verifying their hashes:

- 2Wiki: `e90e093a710788607bbb40a5c4dae4d0cf320e1b3e22800642deebd0610342ff`
- MuSiQue: `780de0e3028e0da1bad567922aef7a36d500c600d6b31a09c414087c78fd3292`

Reuse the forbidden union only if its SHA-256 is exactly:

`4faff825a33d512538b753c4687441aea9f388d493618fe5dfa134518185202b`

Do not change exclusion categories to make Hotpot pass.

## Stage E — rerun availability selector in zero-selection mode

Use the complete Hotpot ID ledger plus the unchanged 2Wiki/MuSiQue ledgers and unchanged forbidden union.

Run `scripts/select_v2_fresh_ids.py` with:

- `--per-dataset 0`
- seed `20260910-v2-fresh`

Write outputs under:

`outputs/daa_v2_fresh_v1/audit_hotpot_full/`

The selected ID file must be empty and hash to the SHA-256 of an empty file.

Expected mathematical lower bound before recount:

- full Hotpot source = 7405;
- Hotpot forbidden union = 5600 unique IDs;
- therefore available Hotpot IDs cannot be below 1805 if the complete source and forbidden union are correctly represented.

Still compute the actual source/forbidden intersection. Do not hard-code 1805.

## Stage F — schema-complete finalizer

Use the current branch version of `scripts/finalize_v2_availability_audit.py`, which must emit the required top-level fields directly rather than relying on a reporting wrapper.

Write:

`outputs/daa_v2_fresh_v1/audit_hotpot_full/V2_AVAILABILITY_AUDIT.json`

Require top-level presence of at least:

- status
- source_counts
- source_ledgers
- forbidden_counts
- forbidden_category_coverage
- forbidden_ledgers
- overlap_checks
- available_after_exclusion
- model_calls
- generation_calls
- retrieval_calls
- fresh_labels_accessed
- selected_questions
- stop_boundary

PASS requires all three datasets to have at least 1,500 available IDs and all integrity checks to pass.

## Stage G — independent validation

Independently recount IDs/hashes and validate the final JSON. Do not simply trust the finalizer output.

Write:

- `independent_final_validation.json`
- `AUDIT_REPORT.md`
- an audit output hash manifest

under the same `audit_hotpot_full` namespace.

The independent validator must distinguish:

- **availability status**; and
- **integrity-validation status**.

Do not use one generic PASS field in a way that could be mistaken for availability PASS.

## Zero-call process evidence

The final report must establish:

- model calls = 0
- generation calls = 0
- retrieval calls = 0
- fresh-label accesses = 0
- selected questions = 0
- fresh generation started = false
- pre-label scoring started = false

These must be supported by explicit process/execution evidence, not inferred only from missing output files.

## Final report to author

Return only audit/provenance facts:

1. complete Hotpot source provenance and row count;
2. whether all original 4,000 IDs/runtime projections matched;
3. complete Hotpot ID-ledger SHA-256;
4. actual Hotpot source/forbidden overlap;
5. actual Hotpot available count;
6. 2Wiki available count;
7. MuSiQue available count;
8. availability PASS/FAIL for the 1,500-per-dataset target;
9. final audit SHA-256;
10. independent validation SHA-256;
11. zero-call/zero-selection/zero-Gold evidence;
12. confirmation that no final fresh IDs were selected and no retrieval/generation/scoring began.

## HARD STOP

STOP after the availability rerun and independent validation.

Even an availability PASS does **not** authorize final ID selection, retrieval, generation, V2/HGB/GbV scoring, action sealing, Gold mapping, or evaluation. A new explicit author instruction is required.
