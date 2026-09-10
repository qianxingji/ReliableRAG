# Codex task — DAA-V2 combined pre-label seal V2 after metadata-sidecar clarification

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` and branch `v2-arbitration-high-standard`.

A previous combined pre-label attempt stopped correctly at the canonical-only input-contract boundary before any scientific fresh scoring or action selection. This task supersedes only that blocked execution attempt. It implements the explicit prospective clarification in:

`docs/V2_PROTOCOL_AMENDMENT_PRELABEL_METADATA_SIDECAR.md`

The task is the **last fresh-label-free execution before outcome mapping**.

It must complete:

1. protected-parent and blocked-attempt verification;
2. exact canonical/sidecar metadata binding projection;
3. historical private-artifact and feature-implementation authentication;
4. frozen DAA-V2 ensemble fit from historical development only;
5. ten-field fresh label-free base-score extraction;
6. structural/leakage preflight;
7. DAA-V2 and raw-HGB action sealing at the frozen 5% budget;
8. prospective GbV NLI scoring on the same canonical branches;
9. GbV same-total-budget, exact-stratum-budget, and historical-threshold action sealing;
10. independent recomputation/validation;
11. combined pre-label gate;
12. complete namespace hash seal;
13. HARD STOP before fresh Gold/outcome access.

No fresh Gold, correctness, answer aliases, supporting-fact labels, EM, F1, recovery, damage, preference/outcome labels, or quality-based filtering is authorized.

Do not change the cohort, candidate pools, original retrieval, runtime branches, feature list, historical estimator binaries, DAA-V2 lambda/alpha/folds/seed/action rate, GbV model/recipe/thresholds, eligibility rule, tie-breaks, or statistical plan.

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
- `docs/V2_PROTOCOL_AMENDMENT_PRELABEL_METADATA_SIDECAR.md`
- `docs/CODEX_TASK_DAA_V2_COMBINED_PRELABEL_SEAL.md`
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

Also authenticate the private historical feature/scoring implementation actually used by the accepted historical experiment. Do not reimplement it from memory.

## Preserve the blocked attempt

The namespace:

`outputs/daa_v2_fresh_v1/prelabel_seal/`

is immutable blocked diagnostic evidence.

Verify and record these accepted blocked-attempt hashes before proceeding:

- `BLOCKING_INPUT_CONTRACT_REPORT.md`: `f0c3dc25aa3541afee35d42404536d21d117a87a853877773e243af58ac1979c`
- `BLOCKING_INPUT_CONTRACT_VALIDATION.json`: `248e23158c3df76908204294c835a3278a428b94ab44edba069f9e682585f03c`
- `logs/input_contract_tests.log`: `963bbeb1cd90a09ec2007dd5031f226fe6f0d75389f764b041cc8943641fca4e`
- blocked artifact manifest if present: preserve and record its actual SHA-256; do not rewrite it.

Require the blocked validation to state:

- status `BLOCKED_CANONICAL_ONLY_INPUT_CONTRACT`;
- 13,500 traces / 4,500 clusters;
- fresh labels accessed = 0;
- V2 fit/scoring not started;
- HGB/V2/GbV action selection not started;
- Gold mapping/evaluation not started.

Do not reuse draft score/action scripts from the blocked namespace as scientific outputs unless their source is explicitly revalidated and copied into the new namespace. Never reuse any blocked output as if it were a completed seal.

## New output namespace

Create only:

`outputs/daa_v2_fresh_v1/prelabel_seal_v2/`

Recommended subdirectories:

- `preflight/`
- `binding/`
- `models/`
- `scoring/`
- `decisions/`
- `logs/`

No prior namespace may be mutated.

## Immutable parent anchors

Before any model forward or estimator scoring, verify:

- selected fresh-ID ledger SHA-256: `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`;
- cohort freeze SHA-256: `0e02d187a379a730f70b24ef33033dbbe93e72c1860fb9b2f20b42b744e7f7f4`;
- candidate-pool freeze SHA-256: `bbcf1e6110607fc0cf65cdcc2647385a0d50d8aa0645812d82509a82e8b0cded`;
- retrieval freeze SHA-256: `606d6148af431313c86477d22d9c235a72fc236257c5c120772aa495dca3ddca`;
- runtime config freeze SHA-256: `9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9`;
- canonical branches SHA-256: `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`;
- branch provenance sidecar SHA-256: `4d0ce2c89bb96c33e76d4d1879add655cd79e9c4bd3b9f0545197254ad759b20`;
- repair bindings SHA-256: `efe03e0da6c522e8f635b3071f5b7f8cc03a05b8a132745d6f2c8554440aab4a`;
- runtime independent validation SHA-256: `d401ffdfd835b8ece9d13b040d81bccdcc3e245a5f6b67cb167bf630ef56d1f1`;
- runtime branch freeze SHA-256: `af0bbbbd96d9629155dac1adf35e68c78e7e74dfca49b8c31fa2ed93d62a7b09`.

Require 13,500 unique traces, exactly 1,500 in each of nine dataset × retriever strata, and zero prior fresh-label access.

## Stage A — canonical/sidecar metadata binding projection

This stage implements the amendment and must finish before any likelihood/base-estimator score is computed.

Inputs:

- canonical truth source: `outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl`
- metadata sidecar: `outputs/daa_v2_fresh_v1/runtime_branch_freeze/branch_provenance.jsonl`

Authority rule:

- canonical file is authoritative for trace membership/order, dataset, retriever, sample_id, question, a0, a1, evidence0/evidence1 text and position;
- sidecar may supply only the hash-bound metadata required by the authenticated historical feature/scoring path.

Build a narrow projection:

`binding/canonical_metadata_binding.jsonl`

The projection must contain only trace identifiers plus the minimum per-position metadata needed by the historical implementation. Allowed semantics are document ID, title, rank/position, retrieval score, content hash/identity, and evidence-state indicator.

Fail closed unless all checks in `V2_PROTOCOL_AMENDMENT_PRELABEL_METADATA_SIDECAR.md` pass, including:

- exact 13,500 trace-key equality;
- exact one-to-one e0/e1 position binding;
- exactly five evidence items per state;
- canonical text/hash consistency at every position;
- no missing or duplicate metadata bindings;
- no default scores;
- no fabricated IDs/titles;
- no fuzzy joins;
- no sidecar override of canonical text/order;
- no Gold/evaluation fields.

Write:

- `binding/BINDING_VALIDATION.json`
- `binding/BINDING_MANIFEST.json`

Perform an independent second implementation of the join/binding checks. Do not let the builder validate itself.

Any mismatch: STOP before Stage B/C scientific scoring.

## Stage B — authenticate historical private artifacts and scoring implementation

Run the committed verifier against `outputs/mars_full` and require PASS:

```powershell
python scripts/verify_v2_private_artifacts.py `
  --historical-root outputs/mars_full `
  --output outputs/daa_v2_fresh_v1/prelabel_seal_v2/preflight/private_artifacts.json
```

Require exact historical artifact hashes from `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`.

Additionally authenticate the exact local implementations/definitions used to reconstruct:

- state-symmetric feature records;
- evidence-change terms;
- reader likelihood prompts/scores;
- answer/evidence embedding features;
- the seven learned estimator inputs;
- B_rule;
- higher_own_likelihood;
- likelihood_margin.

Do not substitute zero/default metadata or a new feature extractor.

## Stage C — fit/freeze the fixed DAA-V2 meta ensemble on historical development only

Use only the accepted historical development ledgers with SHA-256:

- decisions: `74bd8e45a3bbdb7716a02fc063b5a6e35c6ded8810441d422d964b7633b19cbd`;
- outcomes: `a1862495b6e0c9033c420773da93fe36bd335cd8c04da01825b327477848f2f7`.

Run `scripts/fit_v2_ensemble.py` unchanged and write:

- `models/daa_v2.joblib`
- `models/daa_v2_manifest.json`

The fit must use only historical development outcome labels. No fresh outcome file may be read.

Require the committed fixed parameters:

- lambda_damage = 1.0
- meta_alpha = 2.0
- action_rate = 0.05
- group folds = 5
- committed group seed
- exact ten frozen score features
- no dataset-ID feature.

Hash the model bundle and manifest before fresh action selection.

## Stage D — produce ten fresh label-free base scores

Inputs are exactly:

1. canonical branch text/answers from `canonical_branches.jsonl`;
2. the sealed narrow metadata projection from Stage A;
3. frozen historical model/feature assets from Stage B.

Do not read the raw sidecar directly inside downstream estimator code after the binding projection is sealed unless strictly necessary for authenticated historical behavior; if necessary, record and justify each additional read and require equality to the projection.

Produce:

`scoring/v2_base_scores.jsonl`

Each row must contain exactly:

```json
{"dataset":"...","retriever":"...","sample_id":"...","scores":{...}}
```

with exactly these ten score names:

- `state_symmetric_hgb`
- `state_symmetric_logistic`
- `no_cross_state`
- `no_B`
- `no_evidence_change`
- `no_answer_form`
- `ordinary_compact_logistic`
- `B_rule`
- `higher_own_likelihood`
- `likelihood_margin`

Require 13,500 exact keys, no duplicates, no Gold/outcome-like fields, finite numeric values or only historically defined nulls, and no row dropping/imputation/recalibration.

Record model revisions, call counts, feature implementation hashes and ledger SHA-256. Do not report score distributions to the author.

## Stage E — structural/leakage preflight

Run the committed `scripts/preflight_v2_fresh.py` against the sealed canonical branches and fresh base-score ledger.

Require PASS before actions are written.

## Stage F — seal DAA-V2 and raw HGB

Run `scripts/score_v2_prelabel.py` unchanged.

Require:

- trace count = 13,500;
- action rate = 0.05;
- DAA-V2 replace count = 675;
- raw-HGB replace count = 675;
- same frozen eligibility rule;
- zero fresh label/outcome input.

Do not modify the action ledger after sealing.

## Stage G — score GbV on the same canonical branches

Use exactly:

- model `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`;
- revision `5a4338ab2151dc8db04ad53b42b6153382bf4f99`;
- slow tokenizer;
- float32 CUDA;
- published paired hypothesis template;
- each evidence passage independently;
- 20-word-overlap overlength chunking;
- max entailment aggregation;
- margin F1-F0;
- frozen shared eligibility rule.

Run `scripts/score_gbv_fresh_prelabel.py` against the canonical branch ledger. The metadata sidecar is not an input to GbV unless the committed GbV implementation explicitly requires it; the current committed scorer uses canonical question/answer/evidence text only.

Require 13,500 keys and zero fresh labels.

## Stage H — seal GbV operating points

Run `scripts/match_gbv_prelabel.py` unchanged.

Require:

- global same-total-budget actions = 675;
- exact-stratum-budget actions = 675 and stratum counts exactly equal to V2;
- historical dev-selected thresholds transferred unchanged:
  - BM25 0.0473407506942749
  - Dense 0.01295558363199234
  - Hybrid 0.4287375956773758.

No fresh-label threshold changes.

## Stage I — independent pre-label validation

Create an independent validator that does not use the action-selection scripts as its oracle. Recompute and verify at least:

- all trace-key sets;
- canonical/metadata binding hash and one-to-one positional integrity;
- model bundle parameters/manifests;
- DAA-V2/HGB action counts and deterministic ranking/tie-breaks;
- GbV global/stratum/historical-threshold action logic;
- shared eligibility/forced-KEEP behavior;
- all parent hashes and immutability;
- absence of fresh labels/Gold/outcomes.

Write:

`independent_validation.json`

Require PASS.

## Stage J — combined pre-label gate

Run the committed `scripts/seal_v2_gbv_prelabel_gate.py` and write:

`decisions/combined_prelabel_gate.json`

Require status PASS.

Then create:

`PRELABEL_SEAL.json`

binding:

- all parent freeze hashes;
- blocked-diagnostic hashes;
- amendment/task commit hashes;
- metadata binding projection and validation hashes;
- private-artifact verification;
- DAA-V2 model bundle and manifest;
- V2 base-score ledger;
- fresh preflight;
- V2/HGB action ledger and seal;
- GbV score ledger and provenance;
- GbV action ledger and seal;
- independent validation;
- combined pre-label gate;
- fresh_labels_accessed = 0;
- gold_mapping_started = false;
- evaluation_started = false.

Create a complete recursive SHA-256 manifest over the new namespace, excluding only the manifest itself.

## Author-facing report

Return only:

- PASS/FAIL;
- parent/amendment/binding hashes;
- trace/scorable/forced-KEEP counts;
- V2 action count (must be 675);
- raw-HGB action count (must be 675);
- GbV global/stratum/dev-threshold action counts;
- model IDs/revisions and artifact hashes;
- independent-validation and combined-gate status/hashes;
- explicit confirmation that fresh Gold/outcome access remained zero.

Do not expose per-trace scores, example questions/answers/evidence, or any outcome interpretation.

## HARD STOP

STOP after `PRELABEL_SEAL.json`, `combined_prelabel_gate.json`, independent validation, and the complete-file manifest are written and verified.

A PASS authorizes **nothing beyond sealed label-free actions**. Do not load fresh Gold, map outcomes, evaluate, compute EM/F1/recovery/damage, inspect which method wins, or alter any score/model/action/budget artifact. A new explicit human instruction is required for post-seal evaluation.
