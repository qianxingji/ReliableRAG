# Codex task — DAA-V2 final fresh cohort ID freeze only

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` and the scientific protocol on branch `v2-arbitration-high-standard`.

The Hotpot full-validation availability rerun has passed. This task is limited to **deterministically selecting and sealing the final 4,500 fresh evaluation question IDs**:

- HotpotQA: 1,500;
- 2WikiMultiHopQA: 1,500;
- MuSiQue: 1,500;
- total unique evaluation questions: 4,500.

Do **not** construct retrieval indexes or candidate pools. Do **not** retrieve. Do **not** generate original answers, repair queries, or repaired answers. Do **not** run reader likelihood scoring, HGB/V2 scoring, or GbV scoring. Do **not** load/map fresh Gold, correctness, supporting facts, answer aliases, or outcome values.

Stop immediately after the final ID cohort and its integrity/provenance seals are written and independently validated.

## Read first

Read and obey:

- `AGENTS.md`
- `docs/V2_DEVELOPMENT_DECISION.md`
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`
- `docs/V2_PROTOCOL_AMENDMENT_HOTPOT_FULL_VALIDATION.md`
- `docs/V2_SAMPLE_SIZE_PLAN.md`
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`
- `scripts/select_v2_fresh_ids.py`

Treat all historical experiment namespaces, the first failed availability audit, and the successful Hotpot-full availability audit as immutable inputs.

## Accepted audit anchors

Before selection, verify all of the following from the preserved successful audit:

- availability status: `PASS`;
- integrity validation status: `PASS`;
- final availability audit SHA-256: `d1b7e7638bf59406b703b68b7377bda0c0ddf7d5d552375592819dac179afd03`;
- independent final validation SHA-256: `3948b889fbdaf68025a7d79fe70300d65ac2419b1a9543b1884c5379a4b917bf`;
- forbidden union SHA-256: `4faff825a33d512538b753c4687441aea9f388d493618fe5dfa134518185202b`;
- available IDs after exclusion:
  - HotpotQA: `3605`;
  - 2WikiMultiHopQA: `8776`;
  - MuSiQue: `19338`;
- source ID ledger hashes:
  - HotpotQA full validation: `51e70aeed94a1e4939b41ece4c80d03e571aab410fc5cf6324f503624c076d21`;
  - 2WikiMultiHopQA: `e90e093a710788607bbb40a5c4dae4d0cf320e1b3e22800642deebd0610342ff`;
  - MuSiQue train: `780de0e3028e0da1bad567922aef7a36d500c600d6b31a09c414087c78fd3292`;
- Hotpot full source count = `7405` and shared old/new runtime-projection mismatch count = `0`;
- previous model/generation/retrieval/fresh-label/selection counters before this task = zero.

If any anchor differs, stop without selecting IDs.

## Frozen selection rule

Use the already committed `scripts/select_v2_fresh_ids.py` without changing its ranking rule.

The selection rule is exactly:

`SHA256(seed|dataset|sample_id), then sample_id`

with seed:

`20260910-v2-fresh`

and:

`--per-dataset 1500`

This seed and rule are now frozen. Do not try alternative seeds, dataset orderings, prefixes, stratification schemes, or rejection/resampling rules.

## Input ledgers

Use exactly these ID-only source ledgers:

- HotpotQA: `outputs/daa_v2_fresh_v1/audit_hotpot_full/hotpot_source_ids_full.jsonl`
- 2WikiMultiHopQA: `outputs/daa_v2_fresh_v1/audit/2wiki_source_ids.jsonl`
- MuSiQue: `outputs/daa_v2_fresh_v1/audit/musique_train_source_ids.jsonl`

Use exactly this forbidden union:

- `outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl`

Every source/forbidden row must contain exactly `dataset` and `sample_id`.

Do not expand, reduce, or rewrite the forbidden union in this task.

## Output namespace

Create a new namespace only:

`outputs/daa_v2_fresh_v1/cohort_freeze/`

Do not write into either availability-audit namespace except for read-only verification.

## Stage A — deterministic ID selection

Run the selector with the three exact source ledgers and the exact forbidden union:

```powershell
python scripts/select_v2_fresh_ids.py `
  --source outputs/daa_v2_fresh_v1/audit_hotpot_full/hotpot_source_ids_full.jsonl `
  --source outputs/daa_v2_fresh_v1/audit/2wiki_source_ids.jsonl `
  --source outputs/daa_v2_fresh_v1/audit/musique_train_source_ids.jsonl `
  --forbidden outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl `
  --per-dataset 1500 `
  --seed 20260910-v2-fresh `
  --selected-output outputs/daa_v2_fresh_v1/cohort_freeze/selected_fresh_ids.jsonl `
  --manifest-output outputs/daa_v2_fresh_v1/cohort_freeze/selection_manifest.json
```

No other selector invocation with a positive `--per-dataset` value is authorized.

## Stage B — independent selection validation

Independently validate the saved cohort without relying only on `selection_manifest.json`.

Require all of the following:

- exactly 4,500 rows;
- exactly 4,500 unique `(dataset, sample_id)` pairs;
- exactly 1,500 per dataset;
- zero duplicate IDs;
- every selected ID belongs to its exact frozen source ledger;
- zero selected IDs intersect the frozen forbidden union;
- no dataset aliases outside canonical `hotpotqa`, `2wikimultihopqa`, `musique`;
- recomputing `SHA256(seed|dataset|sample_id)` over every available source-minus-forbidden ID reproduces the exact same first 1,500 IDs for each dataset;
- selected output byte hash matches the manifest;
- source hashes and forbidden-union hash match the accepted audit anchors.

The independent validator must not read benchmark question text or any Gold/evaluation fields.

Write:

`outputs/daa_v2_fresh_v1/cohort_freeze/independent_selection_validation.json`

## Stage C — cohort freeze seal

Write:

`outputs/daa_v2_fresh_v1/cohort_freeze/COHORT_FREEZE.json`

It must contain at least:

- status = `PASS` only if all validation checks pass;
- created UTC timestamp;
- git commit/tree state;
- branch/protocol snapshot hashes;
- selection seed;
- stable-order specification;
- selected total = 4500;
- selected count per dataset = 1500;
- selected ID-ledger SHA-256;
- selection-manifest SHA-256;
- independent-validation SHA-256;
- each source ID-ledger SHA-256;
- frozen forbidden-union SHA-256;
- parent successful availability-audit SHA-256;
- parent independent-validation SHA-256;
- `selection_uses_identifiers_only = true`;
- `gold_or_correctness_input = false`;
- `model_calls = 0`;
- `generation_calls = 0`;
- `retrieval_calls = 0`;
- `fresh_labels_accessed = 0`;
- `fresh_generation_started = false`;
- `prelabel_scoring_started = false`;
- explicit hard stop.

## Stage D — preserve and hash

Create a SHA-256 manifest covering every regular file created in `cohort_freeze/`, excluding the hash manifest itself.

Also verify that the two availability-audit namespaces and all historical protected inputs remain byte-identical to their pre-task anchors.

Do not include benchmark question/context/answer text in any cohort-freeze report.

## Final report to author

Return only identifier/provenance facts:

1. selection status PASS/FAIL;
2. selected count per dataset;
3. total selected count;
4. selected-fresh-ID ledger SHA-256;
5. selection manifest SHA-256;
6. independent selection validation SHA-256;
7. cohort-freeze seal SHA-256;
8. source-ledger hashes and forbidden-union hash;
9. confirmation that deterministic re-selection exactly reproduced all selected IDs;
10. confirmation of zero selected/forbidden overlap;
11. zero model/generation/retrieval/fresh-Gold counters;
12. confirmation that no retrieval index, candidate pool, generation, likelihood scoring, V2/HGB/GbV scoring, action selection, Gold mapping, or evaluation started.

## HARD STOP

STOP after the 4,500-ID cohort freeze and independent validation.

A PASS in this task authorizes **nothing beyond the existence of a sealed ID cohort**. Candidate-pool construction, retrieval, generation, scoring, action sealing, and Gold mapping/evaluation each require a subsequent explicit author instruction.