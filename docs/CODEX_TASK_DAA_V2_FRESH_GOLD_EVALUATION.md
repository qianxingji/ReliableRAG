# Codex task — DAA-V2 one-time fresh Gold mapping and confirmatory evaluation

## Scope and authorization boundary

Work against the full private project at `E:\paper\ReliableRAG` on branch `v2-arbitration-high-standard`.

The V3 pre-label execution has completed successfully. DAA-V2, raw HGB, GbV scores and all action policies are sealed before fresh-label access. This task is the **separately authorized post-seal outcome mapping and confirmatory evaluation** described in:

`docs/V2_PROTOCOL_POSTSEAL_GOLD_EVALUATION_AUTHORIZATION.md`

Execution of this task by the responsible human author is the explicit authorization to cross the fresh-Gold boundary once, under the exact constraints below.

This task may:

1. verify the complete pre-label seal and all frozen parents;
2. authenticate the already accepted EM/F1 metric implementation and exact source-specific Gold semantics before decoding selected fresh labels;
3. map Gold for only the frozen 4,500 selected questions into a method-blind 13,500-row numeric outcome ledger;
4. independently validate and seal that outcome ledger;
5. run the already committed primary evaluator exactly once on the sealed outcome ledger;
6. immediately hash/seal the primary evaluation result;
7. run the already frozen secondary 1/2.5/5/7.5/10% budget curve only after the primary result is sealed;
8. independently validate the reported arithmetic/statistical configuration and write the final evaluation seal;
9. report the complete result whether favorable, tied, inconclusive, or unfavorable.

This task may **not** change, refit, regenerate, select, filter, recalibrate, or tune any scientific input or policy after Gold is exposed.

## Read first

Read and obey:

- `AGENTS.md`
- `docs/V2_DEVELOPMENT_DECISION.md`
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`
- `docs/V2_SAMPLE_SIZE_PLAN.md`
- `docs/V2_SECONDARY_BUDGET_GRID.json`
- `docs/V2_PROTOCOL_AMENDMENT_HOTPOT_FULL_VALIDATION.md`
- `docs/V2_PROTOCOL_AMENDMENT_CANDIDATE_POOL_1500.md`
- `docs/V2_PROTOCOL_AMENDMENT_PRELABEL_METADATA_SIDECAR.md`
- `docs/V2_PROTOCOL_AMENDMENT_GBV_LABEL_RESOLVER_FIX.md`
- `docs/V2_PROTOCOL_POSTSEAL_GOLD_EVALUATION_AUTHORIZATION.md`
- `docs/CODEX_TASK_DAA_V2_COMBINED_PRELABEL_SEAL_V3.md`
- `scripts/evaluate_v2_vs_gbv.py`
- `scripts/evaluate_v2_budget_curve.py`

Do not modify either evaluator for this task. If an objectively demonstrated evaluator defect blocks execution, preserve the failure and STOP for review rather than patching after seeing the result.

## Immutable pre-label anchors — verify before any fresh Gold access

Require exact byte hashes:

- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/PRELABEL_SEAL.json`
  - `0d5d593f2d84c5c219ccbddaed257eb3c4e3243478d9cdedda07a2cd3d14e201`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/SHA256_MANIFEST.json`
  - `0a5246a6d270ee01674d099b970a577936bd95d6200a53e1aa3e2ce524857bfd`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/independent_validation.json`
  - `f6fbe43e1c851f21362aa16a70407e65f31c0802577fc7926bad96f5f8898c8d`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/combined_prelabel_gate.json`
  - `bad43503ca58df2f1f8cfd287c6b1f45310c965947c482ce0e16763bc76c7006`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/v2_actions.jsonl`
  - `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/gbv_actions.jsonl`
  - `7dd95ed3bfdec07cacc00321bdacbb68e4fe7e18712861f8371cc0b3507ed07e`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/scoring/gbv_scores.jsonl`
  - `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`
- `outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl`
  - `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`
- selected fresh-ID ledger
  - `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`

Require pre-label facts:

- pre-label seal status = `PASS`;
- combined gate stage = `DAA_V2_GBV_COMBINED_PRELABEL_GATE` and status = `PASS`;
- independent validation status = `PASS`;
- trace count = 13,500;
- question clusters = 4,500;
- V2 eligible/scorable = 3,202;
- DAA-V2 replacement count = 675;
- raw-HGB replacement count = 675;
- GbV global matched replacement count = 675;
- GbV exact-stratum replacement count = 675;
- GbV historical-development-selected replacement count = 1,242;
- GbV entailment index = 0;
- fresh labels accessed = 0;
- Gold mapping started = false;
- evaluation started = false.

The exact DAA-V2/exact-stratum budget vector must remain:

- 2Wiki: BM25 106, Dense 61, Hybrid 45;
- HotpotQA: BM25 110, Dense 75, Hybrid 60;
- MuSiQue: BM25 83, Dense 76, Hybrid 59.

If any anchor differs, STOP before reading any fresh Gold value.

## Output namespace

Create a new post-seal namespace only:

`outputs/daa_v2_fresh_v1/final_evaluation/`

Recommended layout:

- `preflight/`
- `outcomes/`
- `primary/`
- `secondary/`
- `independent/`
- `logs/`

Do not write into or alter any pre-label, runtime, retrieval, pool, cohort, or audit namespace.

## Stage A — pre-Gold metric and source authentication

Before decoding any selected fresh answer label, locate and authenticate the exact historical project functions used for answer normalization, exact match and token F1. Use existing accepted implementation; do not create a new metric based on memory or benchmark folklore.

Establish, using historical/development material only, the exact source-specific handling of:

- canonical answer string;
- accepted answer aliases if and only if the accepted project metric historically used them;
- punctuation/articles/whitespace normalization;
- token F1 aggregation across multiple references if applicable;
- empty answer behavior.

Record source paths, function/AST/file hashes and a small historical/synthetic parity test report under `preflight/`. Do not inspect DAA-V2/GbV fresh outcomes during this stage.

Reverify the already accepted source-provenance records for:

- HotpotQA complete distractor validation;
- corrected 2WikiMultiHopQA development source;
- MuSiQue train source.

The exact selected ID set remains immutable. If metric semantics or source provenance cannot be authenticated unambiguously, STOP before fresh Gold decoding.

## Stage B — create a method-blind Gold/outcome mapper

The mapper must be structurally unable to consult method decisions during outcome construction.

Allowed inputs for the mapping process:

- frozen selected IDs;
- frozen canonical branches;
- the three exact authorized raw source files;
- authenticated metric implementation/configuration;
- read-only provenance/hash controls.

Forbidden mapping-process inputs:

- V2 base scores;
- V2 fused scores;
- raw HGB scores/actions;
- GbV scores/margins/actions;
- any pre-label ranking or policy membership;
- primary/secondary evaluation outputs.

Use a process-local read allowlist/guard or equivalent auditable mechanism to prove this separation.

The mapper may scan raw source files for ID matching, but it must retain/materialize Gold values only for the frozen selected IDs. It must not create a new sample subset based on labels or answer content.

## Stage C — one-time selected-Gold mapping

Cross the Gold boundary only after Stages A/B PASS.

Map exactly 1,500 selected questions from each dataset. Require:

- 4,500 unique `(dataset, sample_id)` Gold question bindings;
- no missing selected ID;
- no extra evaluation ID;
- no duplicate Gold binding;
- source/dataset identity matches the predeclared split/source;
- all three retriever traces for a question use the same frozen Gold reference semantics.

Compute outcome metrics for the immutable canonical `a0` and `a1` branches and write exactly:

`outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl`

Each row must contain exactly:

```json
{"dataset":"...","retriever":"...","sample_id":"...","a0_em":0,"a1_em":0,"a0_f1":0.0,"a1_f1":0.0}
```

Require:

- exactly 13,500 rows;
- exactly 13,500 unique trace keys;
- exactly 4,500 question clusters;
- exactly BM25/Dense/Hybrid for each question;
- each EM value in `{0,1}`;
- each F1 finite and within `[0,1]`;
- no answer string, alias string, question text, evidence, supporting-fact label, method action, score, margin, recovery/damage label or policy name in this numeric ledger.

Immediately write an `OUTCOME_MAPPING_PROVENANCE.json` containing only hashes, counts, metric/source provenance and execution controls. Hash and seal the numeric outcome ledger before any method action file is read by the evaluation process.

## Stage D — independent outcome-ledger validation before analysis

Use a separate validator to confirm schema, key coverage, source binding and metric-range integrity. Where feasible, independently recompute EM/F1 from the same frozen answers and selected Gold with the authenticated metric definitions, still without reading V2/HGB/GbV actions.

Write:

`outputs/daa_v2_fresh_v1/final_evaluation/outcomes/OUTCOME_VALIDATION.json`

Require PASS before policy evaluation.

At this point record `gold_mapping_started=true` and `fresh_labels_accessed=4500 selected question labels` (or an equivalent precise counter); this is expected and must not be confused with pre-label leakage.

## Stage E — run and immediately seal the formal primary evaluator

Only after the outcome ledger and its validation are sealed may the evaluation process read the frozen action files.

Run exactly:

```powershell
python scripts/evaluate_v2_vs_gbv.py `
  --v2-actions outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/v2_actions.jsonl `
  --gbv-actions outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/gbv_actions.jsonl `
  --outcomes outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl `
  --output outputs/daa_v2_fresh_v1/final_evaluation/primary/v2_vs_gbv.json
```

Do not run variants of the evaluator with modified constants.

Immediately after successful creation:

- record SHA-256 of `v2_vs_gbv.json`;
- write `PRIMARY_RESULT_SEAL.json` binding evaluator script SHA, action hashes, outcome hash, bootstrap seed/draws, and result hash;
- do not modify or regenerate the primary result.

The primary interpretation is fixed:

- formal primary published-method contrast = DAA-V2 vs `GbV-global-budget-matched`;
- formal superiority = paired question-cluster bootstrap EM 95% CI lower bound > 0;
- 10,000 bootstrap draws, seed `20260920`;
- all three retriever rows remain inside each `dataset:sample_id` bootstrap cluster.

Do not use secondary results to redefine the primary conclusion.

## Stage F — run the fixed secondary budget grid only after primary seal

Verify `docs/V2_SECONDARY_BUDGET_GRID.json` still specifies exactly:

- primary rate 0.05;
- secondary rates `[0.01, 0.025, 0.05, 0.075, 0.10]`.

Then run exactly:

```powershell
python scripts/evaluate_v2_budget_curve.py `
  --combined-gate outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/combined_prelabel_gate.json `
  --v2-actions outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/v2_actions.jsonl `
  --gbv-scores outputs/daa_v2_fresh_v1/prelabel_seal_v3/scoring/gbv_scores.jsonl `
  --outcomes outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl `
  --grid docs/V2_SECONDARY_BUDGET_GRID.json `
  --output outputs/daa_v2_fresh_v1/final_evaluation/secondary/budget_curve.json
```

This is secondary descriptive evidence. Even if another rate looks better, the 5% result remains the primary confirmatory operating point.

## Stage G — independent result validation

Independently recompute, without importing `evaluate_v2_vs_gbv.py` as the oracle:

- action counts for each policy;
- recovery, damage, net correction;
- selected EM/F1 and deltas from Keep;
- DAA-V2 minus GbV primary EM/F1 point differences;
- per-dataset and per-retriever point differences;
- exact-stratum comparison;
- historical-development-selected GbV comparison;
- DAA-V2 vs raw-HGB key ablation;
- the paired cluster-bootstrap procedure using exactly 4,500 `dataset:sample_id` clusters, 10,000 draws and seed `20260920`;
- every formal/high-standard/stretch boolean in the primary result;
- every fixed budget-curve row and its action budget.

Require numeric equality within deterministic floating-point tolerance and exact equality for counts/booleans. If the validator disagrees, preserve outputs and STOP; do not choose whichever result is more favorable.

Write:

`outputs/daa_v2_fresh_v1/final_evaluation/independent/FINAL_EVALUATION_VALIDATION.json`

## Stage H — final evaluation seal

Write:

`outputs/daa_v2_fresh_v1/final_evaluation/FINAL_EVALUATION_SEAL.json`

Bind at minimum:

- this task/protocol commit hashes;
- all pre-label anchor hashes;
- raw Gold source fingerprints;
- metric implementation hashes;
- selected-ID hash;
- canonical branch hash;
- numeric outcome ledger hash;
- outcome-mapping provenance/validation hashes;
- V2 and GbV action hashes;
- GbV score hash used by the fixed curve;
- primary result hash and primary-result seal hash;
- secondary budget-curve hash;
- independent final validation hash;
- bootstrap constants;
- action budgets;
- one-way post-Gold boundary confirmation;
- explicit statement that no post-Gold tuning/refit/regeneration/cohort change occurred.

Then write a complete recursive SHA-256 manifest for the final-evaluation namespace, excluding only the manifest itself.

## Mandatory author-facing result report

Return the actual results. Do not hide or soften failed targets.

At minimum report:

1. Keep baseline EM/F1;
2. DAA-V2 actions/recovery/damage/net/EM/F1;
3. GbV global matched actions/recovery/damage/net/EM/F1;
4. primary DAA-V2-minus-GbV EM point difference and 95% CI;
5. primary DAA-V2-minus-GbV F1 point difference and 95% CI;
6. formal primary superiority PASS/FAIL;
7. every high-standard engineering target and overall high-standard PASS/FAIL;
8. damage ratio and stretch targets;
9. per-dataset DAA-V2-minus-GbV EM points;
10. per-retriever DAA-V2-minus-GbV EM points and DAA-V2 retriever-specific net corrections;
11. exact-stratum comparison;
12. historical-development-selected GbV comparison;
13. DAA-V2 vs raw-HGB key ablation;
14. all five frozen budget-curve operating points;
15. primary result SHA, outcome ledger SHA, independent validation SHA and final seal SHA.

Do not launch a replacement cohort, alternative selector, threshold search, new reader, source switch, or tuned V2 after seeing these results. Any subsequent experiment must be clearly labeled exploratory/new evidence and cannot replace this confirmatory test.
