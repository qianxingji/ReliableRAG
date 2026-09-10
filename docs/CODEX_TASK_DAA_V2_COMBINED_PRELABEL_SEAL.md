# Codex task — DAA-V2 combined pre-label scoring and action seal

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` and the scientific protocol on branch `v2-arbitration-high-standard`.

The 4,500-question cohort, candidate pools, original retrieval outputs, and shared 13,500-trace original/repaired runtime branches are already frozen. This task is the **last fresh-label-free execution before outcome mapping**.

It is limited to:

1. re-verifying all frozen parents and historical selector artifacts;
2. fitting the already frozen DAA-V2 cross-fitted meta ensemble from historical development evidence only;
3. extracting the ten frozen label-free base scores on the 13,500 fresh branches using the authenticated historical feature/scoring implementation;
4. running the fresh structural/leakage preflight;
5. sealing DAA-V2 and raw-HGB actions at the frozen 5% action rate;
6. independently computing the published GbV paired-adaptation NLI scores on the same canonical branches;
7. sealing GbV same-total-budget, exact-stratum-budget, and historical-development-threshold actions;
8. independently validating all score/action ledgers and hashes;
9. creating the combined pre-label gate;
10. hashing/sealing the complete namespace and **stopping before any fresh Gold/outcome access**.

No fresh Gold, correctness, answer aliases, supporting-fact labels, EM, F1, recovery, damage, preference labels, or outcome values may be loaded, mapped, inferred, displayed, or used anywhere in this task.

Do not change the fresh cohort, candidate pools, retrieval outputs, runtime branches, DAA-V2 architecture, feature list, lambda, alpha, group seed/folds, action rate, GbV model recipe, thresholds, action budgets, eligibility rule, or tie-breaks.

Do not report or inspect answer quality. Author-facing output before the combined gate must contain only counts, hashes, frozen configuration/provenance, integrity status, and action counts—not example questions, answers, evidence, NLI scores, or per-trace rankings.

## Read first

Read and obey:

- `AGENTS.md`
- `docs/V2_DEVELOPMENT_DECISION.md`
- `docs/V2_EXPERIMENT_FREEZE_DRAFT.md`
- `docs/V2_FRESH_EXECUTION_RUNBOOK.md`
- `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`
- `docs/V2_SAMPLE_SIZE_PLAN.md`
- `docs/V2_PROTOCOL_AMENDMENT_HOTPOT_FULL_VALIDATION.md`
- `docs/V2_PROTOCOL_AMENDMENT_CANDIDATE_POOL_1500.md`
- `docs/CODEX_TASK_DAA_V2_FRESH_COHORT_FREEZE.md`
- `docs/CODEX_TASK_DAA_V2_CANDIDATE_POOL_FREEZE.md`
- `docs/CODEX_TASK_DAA_V2_RETRIEVAL_FREEZE.md`
- `docs/CODEX_TASK_DAA_V2_RUNTIME_BRANCH_FREEZE.md`
- `scripts/verify_v2_private_artifacts.py`
- `scripts/fit_v2_ensemble.py`
- `scripts/preflight_v2_fresh.py`
- `scripts/score_v2_prelabel.py`
- `scripts/score_gbv_fresh_prelabel.py`
- `scripts/match_gbv_prelabel.py`
- `scripts/seal_v2_gbv_prelabel_gate.py`
- `src/arbitration/v2_ensemble.py`
- `src/evaluation/answer_normalization.py`
- `src/evaluation/fresh_schema.py`
- `src/verification/gbv_nli.py`

## Immutable parent anchors

Before any new score/model forward, verify at minimum:

- selected fresh-ID ledger SHA-256: `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`;
- cohort-freeze SHA-256: `0e02d187a379a730f70b24ef33033dbbe93e72c1860fb9b2f20b42b744e7f7f4`;
- candidate-pool-freeze SHA-256: `bbcf1e6110607fc0cf65cdcc2647385a0d50d8aa0645812d82509a82e8b0cded`;
- candidate-pool independent validation SHA-256: `782b813c68013e1ee61844f29e0f1b9b7ed3b7ceb1adef020604a319b9115834`;
- retrieval-freeze SHA-256: `606d6148af431313c86477d22d9c235a72fc236257c5c120772aa495dca3ddca`;
- retrieval independent validation SHA-256: `f53167f1ae5b8b97928a59aed4017fd8d5a1de5a9b68f4decd7bb27e07f74347`;
- runtime-config-freeze SHA-256: `9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9`;
- canonical branch ledger SHA-256: `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`;
- repair binding ledger SHA-256: `efe03e0da6c522e8f635b3071f5b7f8cc03a05b8a132745d6f2c8554440aab4a`;
- runtime independent validation SHA-256: `d401ffdfd835b8ece9d13b040d81bccdcc3e245a5f6b67cb167bf630ef56d1f1`;
- runtime-branch-freeze SHA-256: `af0bbbbd96d9629155dac1adf35e68c78e7e74dfca49b8c31fa2ed93d62a7b09`;
- runtime trace count: `13500`;
- question clusters: `4500`;
- exact 1,500 traces in each of the nine dataset × retriever strata;
- runtime 180-trace deterministic replay: exact match;
- runtime fresh Gold/outcome access: `0`;
- likelihood/HGB/DAA-V2/GbV scoring before this task: not started;
- arbitration action selection/sealing before this task: not started.

Re-hash protected parent namespaces. Any mismatch is a hard stop.

## Frozen DAA-V2 specification

The primary candidate remains exactly:

- backbone score: `state_symmetric_hgb`;
- three meta states: recovery / damage / neutral;
- utility: `p(recovery) - p(damage)`;
- `lambda_damage = 1.0`;
- `meta_alpha = 2.0`;
- grouped cross-fitting: 5 folds;
- group seed: the committed `V2_GROUP_SEED` in `src/arbitration/v2_ensemble.py`;
- no dataset-ID feature;
- exact ten score features from `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`;
- action rate: `0.05`;
- 13,500 traces therefore imply a primary total replacement budget of exactly **675**;
- raw HGB must be sealed at exactly the same total budget as the mandatory backbone ablation.

Do not tune or reselect any of these values.

## Output namespace

Create only:

`outputs/daa_v2_fresh_v1/prelabel_seal/`

Do not mutate any prior audit/cohort/pool/retrieval/runtime namespace.

Recommended subdirectories:

- `preflight/`
- `models/`
- `scoring/`
- `decisions/`
- `logs/`

## Stage A — historical selector asset and implementation authentication

Run the committed historical-artifact verifier against the accepted private historical root, expected to be `outputs/mars_full` unless the existing private provenance records an equivalent exact root:

```powershell
python scripts/verify_v2_private_artifacts.py `
  --historical-root outputs/mars_full `
  --output outputs/daa_v2_fresh_v1/prelabel_seal/preflight/private_artifacts.json
```

Require `PASS` and exact hashes from `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`.

In addition, locate and authenticate the historical feature-construction / score-generation implementation that produces the inputs expected by all seven historical estimator binaries plus the three heuristic scores. Bind its source/config hashes in a new preflight provenance file.

Do **not** recreate a merely similar 48-d feature extractor from memory. If the accepted historical scoring path cannot be located and provenance-verified, STOP before fresh feature extraction.

## Stage B — fit/freeze the already specified DAA-V2 meta ensemble on historical development only

Use only the historical 9,000-trace developmentized decision/outcome ledgers already designated as V2 development evidence. The expected source ledger hashes are:

- decisions: `74bd8e45a3bbdb7716a02fc063b5a6e35c6ded8810441d422d964b7633b19cbd`;
- outcomes: `a1862495b6e0c9033c420773da93fe36bd335cd8c04da01825b327477848f2f7`.

Locate the exact private files that match these hashes. Do not substitute a regenerated or filtered copy unless byte identity/hashes are explicitly reconciled.

Run the committed `scripts/fit_v2_ensemble.py` and write:

- `models/daa_v2.joblib`
- `models/daa_v2_manifest.json`

The fit may read historical development outcomes only. It must not read the fresh canonical branch ledger, fresh score ledger, or any fresh label/outcome file as training targets.

Require manifest parameters to exactly match the committed V2 constants. Record the trained bundle SHA-256 before any fresh action selection.

## Stage C — produce the ten fresh label-free base scores

Consume only the immutable canonical branch ledger:

`outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl`

Produce:

`outputs/daa_v2_fresh_v1/prelabel_seal/scoring/v2_base_scores.jsonl`

Each row must contain exactly:

```json
{"dataset":"...","retriever":"...","sample_id":"...","scores":{...}}
```

The `scores` object must contain exactly these ten fields:

1. `state_symmetric_hgb`
2. `state_symmetric_logistic`
3. `no_cross_state`
4. `no_B`
5. `no_evidence_change`
6. `no_answer_form`
7. `ordinary_compact_logistic`
8. `B_rule`
9. `higher_own_likelihood`
10. `likelihood_margin`

Use the exact historical model binaries verified in Stage A and the authenticated historical feature/scoring path. Qwen likelihood computation and BGE answer/evidence embedding operations are allowed only insofar as required by that frozen label-free feature path. Do not generate new answers or repair queries; consume the already frozen branches.

Require:

- exactly 13,500 trace keys;
- exact key set equality with canonical branches;
- no duplicate keys;
- no Gold/outcome-like fields;
- finite numeric values or explicit `null` only where the accepted historical method defines unscorable behavior;
- no quality-based dropping, repair, imputation, winsorization, recalibration, or score normalization beyond the frozen implementation.

Record all model revisions, artifact hashes, versions, call counters, and score-ledger SHA-256.

Do not print score values/distributions to the author.

## Stage D — structural/leakage preflight

Run:

```powershell
python scripts/preflight_v2_fresh.py `
  --selected-ids outputs/daa_v2_fresh_v1/cohort_freeze/selected_fresh_ids.jsonl `
  --branches outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl `
  --v2-score-ledger outputs/daa_v2_fresh_v1/prelabel_seal/scoring/v2_base_scores.jsonl `
  --private-artifact-verification outputs/daa_v2_fresh_v1/prelabel_seal/preflight/private_artifacts.json `
  --output outputs/daa_v2_fresh_v1/prelabel_seal/preflight/fresh_preflight.json
```

Require `PASS` before any actions are written.

## Stage E — seal DAA-V2 and raw-HGB actions

Run exactly:

```powershell
python scripts/score_v2_prelabel.py `
  --branches outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl `
  --score-ledger outputs/daa_v2_fresh_v1/prelabel_seal/scoring/v2_base_scores.jsonl `
  --model outputs/daa_v2_fresh_v1/prelabel_seal/models/daa_v2.joblib `
  --actions-output outputs/daa_v2_fresh_v1/prelabel_seal/decisions/v2_actions.jsonl `
  --seal-output outputs/daa_v2_fresh_v1/prelabel_seal/decisions/v2_seal.json
```

Require:

- trace count = 13,500;
- action rate = 0.05;
- DAA-V2 replace count = **675**;
- raw-HGB replace count = **675**;
- identical eligibility/forced-KEEP rule for later GbV comparison;
- no fresh label/outcome input.

Do not modify the action file after it is sealed.

## Stage F — score GbV prospectively on the same frozen branches

Use exactly the committed published paired-adaptation implementation in `src/verification/gbv_nli.py` and `scripts/score_gbv_fresh_prelabel.py`.

Frozen GbV recipe:

- model: `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`;
- revision: `5a4338ab2151dc8db04ad53b42b6153382bf4f99`;
- hypothesis: `The answer to the question "{q}" is: "{a}"`;
- each evidence passage independently;
- overlength passage split with 20-word overlap, every NLI pair fit-checked;
- branch score: max entailment probability;
- paired margin: `F1 - F0`;
- shared equal/empty eligibility rule;
- dtype: float32;
- device: CUDA;
- tokenizer: slow tokenizer as implemented;
- no fresh labels.

Run:

```powershell
python scripts/score_gbv_fresh_prelabel.py `
  --branches outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl `
  --scores-output outputs/daa_v2_fresh_v1/prelabel_seal/scoring/gbv_scores.jsonl `
  --provenance-output outputs/daa_v2_fresh_v1/prelabel_seal/scoring/gbv_provenance.json `
  --device cuda:0 `
  --batch-size 8 `
  --dtype float32 `
  --local-files-only
```

If the exact pinned model is not already locally available, do not silently change revision/model/tokenizer. A controlled one-time acquisition before scoring is allowed only if provenance and exact revision/cache hashes are recorded; then rerun with local-only mode. If exact revision cannot be established, STOP.

Require the GbV score ledger to contain all 13,500 trace keys, with ineligible/unscorable rows forced KEEP exactly as the committed script defines.

## Stage G — seal the three GbV operating points

Run:

```powershell
python scripts/match_gbv_prelabel.py `
  --v2-actions outputs/daa_v2_fresh_v1/prelabel_seal/decisions/v2_actions.jsonl `
  --gbv-scores outputs/daa_v2_fresh_v1/prelabel_seal/scoring/gbv_scores.jsonl `
  --actions-output outputs/daa_v2_fresh_v1/prelabel_seal/decisions/gbv_actions.jsonl `
  --seal-output outputs/daa_v2_fresh_v1/prelabel_seal/decisions/gbv_seal.json
```

Require:

- `gbv_global_matched`: exactly 675 actions;
- `gbv_stratum_matched`: exactly 675 actions and exact equality to every V2 dataset×retriever action budget;
- `gbv_dev_selected`: transferred unchanged using the committed thresholds:
  - BM25 `0.0473407506942749`
  - Dense `0.01295558363199234`
  - Hybrid `0.4287375956773758`
- no fresh labels or post-hoc threshold changes.

Do not compare which method looks better from any Gold outcome because Gold remains unavailable.

## Stage H — independent pre-label validation

Write an independent validator in the new namespace that does not import the action-selection scripts as its decision oracle. It may read the sealed numeric score/action ledgers and recompute arithmetic/ranking from their frozen inputs.

Independently verify at least:

- all trace-key sets are exactly equal to the canonical branch ledger;
- DAA-V2 model bundle parameter/config manifest matches the committed constants;
- V2 action ranking reproduces exactly 675 replacements;
- raw HGB top-score ranking independently reproduces exactly the sealed 675 replacements;
- GbV margin equals `F1-F0` wherever scored;
- same-total-budget GbV ranking independently reproduces exactly the sealed 675 replacements;
- exact-stratum GbV action sets exactly reproduce V2 stratum budgets;
- historical-threshold GbV actions exactly reproduce the three committed thresholds;
- all equal/empty/unscorable rows are KEEP where required;
- no score/action file contains Gold/correctness/outcome fields;
- all parent hashes remain unchanged;
- no fresh label file has been read or materialized by this task.

Write:

`outputs/daa_v2_fresh_v1/prelabel_seal/independent_validation.json`

Require `PASS`.

## Stage I — combined pre-label gate

Run exactly:

```powershell
python scripts/seal_v2_gbv_prelabel_gate.py `
  --fresh-preflight outputs/daa_v2_fresh_v1/prelabel_seal/preflight/fresh_preflight.json `
  --v2-seal outputs/daa_v2_fresh_v1/prelabel_seal/decisions/v2_seal.json `
  --gbv-provenance outputs/daa_v2_fresh_v1/prelabel_seal/scoring/gbv_provenance.json `
  --gbv-match-seal outputs/daa_v2_fresh_v1/prelabel_seal/decisions/gbv_seal.json `
  --v2-actions outputs/daa_v2_fresh_v1/prelabel_seal/decisions/v2_actions.jsonl `
  --gbv-scores outputs/daa_v2_fresh_v1/prelabel_seal/scoring/gbv_scores.jsonl `
  --gbv-actions outputs/daa_v2_fresh_v1/prelabel_seal/decisions/gbv_actions.jsonl `
  --output outputs/daa_v2_fresh_v1/prelabel_seal/decisions/combined_prelabel_gate.json
```

Require `status = PASS`.

Create a final `PRELABEL_SEAL.json` binding:

- every parent freeze hash;
- historical asset verification hash;
- historical development ledger hashes;
- DAA-V2 model and manifest hashes;
- V2 base-score ledger hash;
- fresh preflight hash;
- V2/raw-HGB action ledger and seal hashes;
- GbV model/cache/revision provenance hash;
- GbV score ledger hash;
- GbV action ledger and seal hashes;
- independent-validation hash;
- combined-gate hash;
- exact action counts;
- explicit `fresh_labels_accessed = 0`;
- explicit `gold_mapping_started = false`;
- explicit `evaluation_started = false`;
- hard-stop statement.

## Stage J — complete-file manifest and HARD STOP

Hash every regular file in `prelabel_seal/`, excluding the manifest itself, into:

`outputs/daa_v2_fresh_v1/prelabel_seal/SHA256_MANIFEST.json`

Reverify all protected parent namespaces after the seal.

Then **STOP THE PROCESS**.

Do not open/map fresh Gold. Do not compute EM/F1/recovery/damage/net. Do not run `evaluate_v2_vs_gbv.py`. Do not create a result table. Do not inspect whether DAA-V2 appears to win or lose.

A PASS in this task only establishes that all prospective label-free scores and actions were fixed before Gold access. Post-seal outcome mapping/evaluation requires a new explicit human instruction.

## Final report to author

Return only:

1. overall pre-label seal PASS/FAIL;
2. canonical trace count and question-cluster count;
3. V2 eligible/scorable count and forced-KEEP counts;
4. V2 action count and raw-HGB action count;
5. V2 dataset×retriever action counts;
6. GbV scored/forced-KEEP counts;
7. GbV global-matched / stratum-matched / historical-dev-selected action counts;
8. all key SHA-256 values;
9. independent validation PASS/FAIL;
10. combined pre-label gate PASS/FAIL;
11. confirmation that fresh-label/Gold/outcome accesses remain exactly zero;
12. confirmation that evaluation has not started and the process stopped at the hard boundary.

Do not include question text, evidence text, answers, per-trace scores, per-trace actions, recovery/damage counts, EM/F1, or any outcome-derived comparison in the author-facing report.
