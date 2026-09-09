# Codex task — DAA-V2 fresh availability audit only

## Scope and stop boundary

Work against the full private ReliableRAG project, expected at `E:\paper\ReliableRAG`, while using the scientific protocol from GitHub branch `v2-arbitration-high-standard`.

**This task is limited to Stage 0--1: private-artifact verification and identifier-only fresh-ID availability audit.**

Do **not** select the final fresh cohort. Do **not** run retrieval. Do **not** generate answers or repair queries. Do **not** score V2 or GbV. Do **not** open or map fresh Gold/correctness/outcome values. Stop immediately after producing and validating the audit outputs described below.

## Read before executing

Read and obey:

- `AGENTS.md`;
- `docs/V2_DEVELOPMENT_DECISION.md`;
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`;
- `docs/V2_SAMPLE_SIZE_PLAN.md`;
- `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`;
- `docs/V2_AVAILABILITY_AUDIT_SCHEMA.json`;
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`.

Treat the existing accepted experiment and Phase10 namespaces as immutable inputs.

## Scientific target

Audit whether the project can support the preferred prospective cohort:

- HotpotQA: 1,500 genuinely unused evaluation questions;
- 2WikiMultiHopQA: 1,500 genuinely unused evaluation questions;
- MuSiQue: 1,500 genuinely unused evaluation questions;
- no final IDs selected in this task.

The target is intentionally strict. If any dataset has fewer than 1,500 eligible IDs after the frozen exclusions, report `FAIL` and stop. Do not silently reduce the sample size, reuse opened-label IDs, or substitute a source.

## Stage A — establish immutable private inputs

1. Create a new audit-only namespace, for example:
   `outputs/daa_v2_fresh_v1/audit/`
2. Do not modify historical `outputs/mars_full/`, Phase3--Phase10 outputs, or their private controls.
3. Record the current project Git commit/tree state and the SHA-256 of every V2 protocol file used.
4. Run the historical private-artifact verifier:

```powershell
python scripts/verify_v2_private_artifacts.py `
  --historical-root outputs/mars_full `
  --output outputs/daa_v2_fresh_v1/audit/private_artifacts.json
```

Expected status: `PASS`.

If the historical root differs in the full private project, resolve its actual accepted path from the existing manifests; do not create substitute model binaries. If any required file is missing or hash-mismatched, stop with `FAIL`.

## Stage B — construct identifier-only source inventories

Use the already validated Phase10/source-projection machinery. Do not deserialize or retain answer, supporting-fact, alias, correctness, or other Gold/evaluation values.

Each inventory row must contain exactly:

```json
{"dataset":"hotpotqa","sample_id":"..."}
```

Create source ID inventories for:

### HotpotQA

Primary source: distractor validation.

First audit the currently available runtime-only validation projection. If that projection is too small to leave 1,500 unused IDs after exclusion, expand the **runtime-only identifier/question/context projection** from the official HotpotQA distractor-validation source using the existing field-level source-projection guard. The expansion may expose IDs/runtime fields required to construct an inventory, but Gold/evaluation values remain forbidden and must not be materialized into the audit namespace.

Do not switch HotpotQA to train data merely to satisfy the count without a prospective protocol amendment.

### 2WikiMultiHopQA

Use the corrected `dev.json` source already accepted by the project. The audited raw source contains 12,576 rows, so a count shortage should be treated as a possible exclusion/implementation issue and investigated before any protocol change.

### MuSiQue

Use `musique_ans_v1.0_train.jsonl` for the new primary fresh evaluation inventory. Do not use the already heavily consumed answerable-dev split for the 1,500-question target.

Exclude the historical MuSiQue development IDs and every previously evaluated MuSiQue question ID. Record the raw train-file SHA-256 and verify it against the project's accepted source audit before deriving the ID-only inventory.

## Stage C — construct the union forbidden-ID ledger

Build an ID-only union covering every question that would invalidate the strong fresh claim.

At minimum include IDs from:

1. historical selector training/development/calibration;
2. opened pilots used in selector development;
3. historical main confirmatory evaluation;
4. operator-transfer evaluation;
5. robustness/stress conditions whose outcomes were inspected;
6. second-reader/reader-transfer analyses whose outcomes were inspected;
7. previous Fresh-ID evaluation questions whose Gold/outcomes were opened;
8. previous Fresh extension corpus-contributor IDs, including corpus-only contributors, for the strict primary freshness definition;
9. any additional experimental namespace in which that question's correctness/outcome was accessed.

The union ledger itself must contain only `dataset` and `sample_id`.

Also produce a **forbidden-category coverage manifest** that reports, for each category:

- source namespace/file;
- row count;
- unique question-ID count by dataset;
- SHA-256 of the ID-only projection;
- whether it is included in the final union;
- overlap/duplicate handling.

Do not report raw questions, answers, predictions, passages, or Gold values.

## Stage D — audit only; select zero questions

Run the selector in audit mode:

```powershell
python scripts/select_v2_fresh_ids.py `
  --source outputs/daa_v2_fresh_v1/audit/hotpot_source_ids.jsonl `
  --source outputs/daa_v2_fresh_v1/audit/2wiki_source_ids.jsonl `
  --source outputs/daa_v2_fresh_v1/audit/musique_train_source_ids.jsonl `
  --forbidden outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl `
  --per-dataset 0 `
  --seed 20260910-v2-fresh `
  --selected-output outputs/daa_v2_fresh_v1/audit/no_selection.jsonl `
  --manifest-output outputs/daa_v2_fresh_v1/audit/availability_selector_manifest.json
```

`no_selection.jsonl` must be empty.

Do not rerun with `--per-dataset 1500` in this task.

## Stage E — independent audit validation

Create:

`outputs/daa_v2_fresh_v1/audit/V2_AVAILABILITY_AUDIT.json`

It must conform semantically to `docs/V2_AVAILABILITY_AUDIT_SCHEMA.json` and contain at minimum:

- status PASS/FAIL;
- UTC timestamp;
- project root;
- current Git commit/tree identifier;
- private-artifact verification SHA-256;
- source inventory path/count/SHA for each dataset;
- raw-source hashes;
- forbidden category coverage;
- union forbidden counts by dataset;
- available-after-exclusion count by dataset;
- explicit overlap checks;
- evidence that source/forbidden projections were identifier-only;
- `model_calls = 0`;
- `generation_calls = 0`;
- `retrieval_calls = 0`;
- `fresh_labels_accessed = 0`;
- `selected_questions = 0`;
- mandatory stop boundary.

PASS only when all three datasets have at least 1,500 available IDs and all integrity/leakage checks pass.

Also save a machine-readable hash manifest of all audit outputs.

## Required final report to the author

Return only audit facts, not benchmark content:

1. private historical artifact verification PASS/FAIL;
2. source count for each dataset;
3. unique forbidden count for each dataset;
4. available unused count for each dataset;
5. whether the 1,500-per-dataset target is feasible;
6. source hash and ID-inventory hash for each dataset;
7. union-forbidden hash;
8. `V2_AVAILABILITY_AUDIT.json` hash;
9. confirmation that model/generation/retrieval calls were zero;
10. confirmation that no fresh Gold/correctness/outcome values were accessed;
11. confirmation that no fresh IDs were selected and no fresh generation began.

## Hard stop

After the audit report is written, **STOP**.

Do not proceed to cohort selection, candidate-pool construction, retrieval, generation, likelihood scoring, V2 fitting/scoring, GbV scoring, pre-label action sealing, Gold mapping, or evaluation without a new explicit author instruction.
