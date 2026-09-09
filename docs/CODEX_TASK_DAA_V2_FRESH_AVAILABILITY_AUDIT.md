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

1. Create a new audit-only namespace:
   `outputs/daa_v2_fresh_v1/audit/`
2. Do not modify historical `outputs/mars_full/`, Phase3--Phase10 outputs, or their private controls.
3. Record the current project Git commit/tree state and SHA-256 of every V2 protocol file used.
4. Run:

```powershell
python scripts/verify_v2_private_artifacts.py `
  --historical-root outputs/mars_full `
  --output outputs/daa_v2_fresh_v1/audit/private_artifacts.json
```

Expected status: `PASS`.

If the historical root differs, resolve its accepted location from existing manifests. Never create substitute model binaries. A missing or hash-mismatched required artifact is a hard `FAIL`.

## Stage B — construct identifier-only source inventories

Reuse the validated Phase10/source-projection machinery. Do not deserialize or retain answer, supporting-fact, alias, correctness, or other Gold/evaluation values in this audit namespace.

Every inventory row must contain exactly:

```json
{"dataset":"hotpotqa","sample_id":"..."}
```

Create:

- `hotpot_source_ids.jsonl`
- `2wiki_source_ids.jsonl`
- `musique_train_source_ids.jsonl`

### HotpotQA

Primary source: distractor validation. Audit the current runtime-only validation projection first. If it cannot leave 1,500 unused IDs after exclusions, expand the runtime-only identifier/question/context projection from the official distractor-validation source under the existing field-level guard. Gold/evaluation values remain forbidden.

Do not switch HotpotQA to train data without a prospective protocol amendment.

### 2WikiMultiHopQA

Use the accepted corrected `dev.json`. The audited source contains 12,576 rows. A shortage should first be treated as a possible exclusion/projection problem, not as permission to change the source.

### MuSiQue

Use `musique_ans_v1.0_train.jsonl`. Do not use the heavily consumed 2,417-row answerable-dev split for this 1,500-question target.

Exclude the historical MuSiQue development IDs and every previously evaluated MuSiQue question ID. Verify the raw train-file SHA-256 against the accepted source audit before deriving its ID-only inventory.

## Stage C — construct the strict forbidden-ID union

First create one **ID-only ledger per exclusion category**. At minimum cover:

1. selector training/development/calibration;
2. opened pilots used in selector development;
3. main confirmatory evaluation;
4. operator-transfer evaluation;
5. robustness/stress conditions whose outcomes were inspected;
6. second-reader/reader-transfer analyses whose outcomes were inspected;
7. prior Fresh-ID evaluation questions whose Gold/outcomes were opened;
8. prior Fresh extension corpus contributors, including corpus-only contributors;
9. every additional namespace in which question correctness/outcome was accessed.

Every category ledger must contain exactly `dataset` and `sample_id`.

Build the union with the committed tool, for example:

```powershell
python scripts/build_v2_forbidden_union.py `
  --category "selector_development=outputs/daa_v2_fresh_v1/audit/forbidden/selector_development.jsonl" `
  --category "opened_pilots=outputs/daa_v2_fresh_v1/audit/forbidden/opened_pilots.jsonl" `
  --category "main_confirmatory=outputs/daa_v2_fresh_v1/audit/forbidden/main_confirmatory.jsonl" `
  --category "operator_transfer=outputs/daa_v2_fresh_v1/audit/forbidden/operator_transfer.jsonl" `
  --category "robustness=outputs/daa_v2_fresh_v1/audit/forbidden/robustness.jsonl" `
  --category "reader_transfer=outputs/daa_v2_fresh_v1/audit/forbidden/reader_transfer.jsonl" `
  --category "prior_fresh_eval=outputs/daa_v2_fresh_v1/audit/forbidden/prior_fresh_eval.jsonl" `
  --category "prior_fresh_contributors=outputs/daa_v2_fresh_v1/audit/forbidden/prior_fresh_contributors.jsonl" `
  --category "other_opened_outcomes=outputs/daa_v2_fresh_v1/audit/forbidden/other_opened_outcomes.jsonl" `
  --union-output outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl `
  --coverage-output outputs/daa_v2_fresh_v1/audit/forbidden_coverage.json
```

If the private project contains more relevant historical categories, add them as additional `--category` inputs rather than folding them invisibly into another category.

The coverage manifest must preserve every category hash/count and pairwise overlap. Do not report benchmark text.

## Stage D — audit only; select zero questions

Run:

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

`no_selection.jsonl` must be empty. Do **not** rerun with `--per-dataset 1500` in this task.

## Stage E — execution evidence

Create `outputs/daa_v2_fresh_v1/audit/process_evidence.json` from the actual audit execution trace/logs, with exactly these scientific counters/flags:

```json
{
  "model_calls": 0,
  "generation_calls": 0,
  "retrieval_calls": 0,
  "fresh_labels_accessed": 0,
  "selected_questions": 0,
  "fresh_generation_started": false,
  "prelabel_scoring_started": false
}
```

Do not infer `0` merely because an output file is absent. Support the counters from the executed command allowlist/log, source-projection boundaries, and stage controls.

## Stage F — independent fail-closed finalization

Run the committed finalizer. Replace `<...SHA256...>` with the actual raw-source digests verified during this audit:

```powershell
python scripts/finalize_v2_availability_audit.py `
  --project-root "E:\paper\ReliableRAG" `
  --git-state "<CURRENT_GIT_COMMIT_OR_TREE>" `
  --private-artifacts outputs/daa_v2_fresh_v1/audit/private_artifacts.json `
  --forbidden-union outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl `
  --forbidden-coverage outputs/daa_v2_fresh_v1/audit/forbidden_coverage.json `
  --selector-manifest outputs/daa_v2_fresh_v1/audit/availability_selector_manifest.json `
  --no-selection outputs/daa_v2_fresh_v1/audit/no_selection.jsonl `
  --source "hotpotqa=outputs/daa_v2_fresh_v1/audit/hotpot_source_ids.jsonl" `
  --source "2wikimultihopqa=outputs/daa_v2_fresh_v1/audit/2wiki_source_ids.jsonl" `
  --source "musique=outputs/daa_v2_fresh_v1/audit/musique_train_source_ids.jsonl" `
  --raw-source-hash "hotpotqa=<HOTPOT_RAW_SHA256>" `
  --raw-source-hash "2wikimultihopqa=<2WIKI_RAW_SHA256>" `
  --raw-source-hash "musique=<MUSIQUE_TRAIN_RAW_SHA256>" `
  --process-evidence outputs/daa_v2_fresh_v1/audit/process_evidence.json `
  --output outputs/daa_v2_fresh_v1/audit/V2_AVAILABILITY_AUDIT.json
```

The finalizer independently recomputes source/forbidden overlaps and available counts. `PASS` is permitted only when all three datasets independently retain at least 1,500 unused IDs and every zero-call/no-Gold/no-selection condition passes.

Also create a machine-readable SHA-256 manifest covering all audit files.

## Required final report to the author

Return only audit facts, never benchmark content:

1. historical private-artifact verification PASS/FAIL;
2. source ID count for each dataset;
3. unique forbidden count for each dataset;
4. available unused count for each dataset;
5. whether 1,500 per dataset is feasible;
6. raw-source and ID-inventory hash for each dataset;
7. forbidden-union hash and category-coverage hash;
8. `V2_AVAILABILITY_AUDIT.json` hash;
9. confirmation that model/generation/retrieval calls were zero;
10. confirmation that no fresh Gold/correctness/outcome values were accessed;
11. confirmation that zero fresh questions were selected and no generation began.

## Hard stop

After the audit report is written, **STOP**.

Do not proceed to cohort selection, candidate-pool construction, retrieval, generation, likelihood scoring, V2 fitting/scoring, GbV scoring, pre-label action sealing, Gold mapping, or evaluation without a new explicit author instruction.
