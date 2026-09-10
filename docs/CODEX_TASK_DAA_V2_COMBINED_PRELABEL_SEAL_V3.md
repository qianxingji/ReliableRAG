# Codex task — DAA-V2 combined pre-label seal V3 after GbV resolver correction

## Scope and hard stop

Work against the full private project at `E:\paper\ReliableRAG` on branch `v2-arbitration-high-standard`.

Two previous combined pre-label attempts stopped correctly before scientific fresh scoring:

1. `prelabel_seal/` stopped on the canonical-only metadata input-contract gap.
2. `prelabel_seal_v2/` validated the metadata binding successfully, then stopped on a GbV entailment-label resolver compatibility bug before V2 fitting, fresh scientific scoring, or action selection.

This task resumes only after the reviewed prospective implementation correction in:

- `docs/V2_PROTOCOL_AMENDMENT_PRELABEL_METADATA_SIDECAR.md`
- `docs/V2_PROTOCOL_AMENDMENT_GBV_LABEL_RESOLVER_FIX.md`

The branch must include commit `e7c5003ac56333de0bfd5d9bbc403006baa5ffde` or a descendant containing the exact reviewed resolver correction and regression tests.

This is the **last fresh-label-free scientific execution before outcome mapping**.

It must complete the frozen pipeline through the combined pre-label gate and then stop. No fresh Gold, correctness, aliases, supporting-fact labels, EM, F1, recovery, damage, preference/outcome values, or result-based tuning is authorized.

## Preserve all prior evidence

Treat these namespaces as immutable inputs:

- `outputs/daa_v2_fresh_v1/prelabel_seal/`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v2/`

Do not delete, rewrite, rename, or convert either blocked attempt into a PASS.

Verify at minimum the first blocked attempt anchors:

- `BLOCKING_INPUT_CONTRACT_REPORT.md` SHA-256: `f0c3dc25aa3541afee35d42404536d21d117a87a853877773e243af58ac1979c`
- `BLOCKING_INPUT_CONTRACT_VALIDATION.json` SHA-256: `248e23158c3df76908204294c835a3278a428b94ab44edba069f9e682585f03c`
- `logs/input_contract_tests.log` SHA-256: `963bbeb1cd90a09ec2007dd5031f226fe6f0d75389f764b041cc8943641fca4e`
- blocked artifact manifest SHA-256: `0f7138aeb8afc7ce00a4aaf423228fa831745e0f124366ef389ddeebb23c8bf8`

Verify the second blocked attempt anchors:

- `binding/BINDING_VALIDATION.json` SHA-256: `1ff235e99f7408b9e01dcf8d965f64433614eaa4bdbc1678ca348e9b3baaa684`
- `binding/canonical_metadata_binding.jsonl` SHA-256: `66a264216f1c3a9e474b68502d30e278412117d4a1d3ff4cc76bb86f97434cf3`
- `preflight/GBV_LABEL_RESOLUTION_COMPATIBILITY.json` SHA-256: use the actual preserved local hash and require its status to be `FAIL` / `BLOCKED_GBV_LABEL_RESOLUTION_COMPATIBILITY`
- `BLOCKED_VALIDATION.json` SHA-256: `5cc11f62349fd17ae4dc3ccaf76e64de43da06dca5c2fdbef7848402d9ee2ed3`
- second blocked namespace manifest: preserve and record its actual SHA-256
- fresh labels accessed = 0
- V2 fit started = false
- estimator/model scientific scoring calls = 0
- combined pre-label gate = NOT_RUN

If these facts do not hold, stop.

## Output namespace

Create only:

`outputs/daa_v2_fresh_v1/prelabel_seal_v3/`

All scientific outputs for this attempt must live there. Prior parent namespaces are read-only.

## Stage A — verify the reviewed GbV resolver correction before any scientific score

Read the exact pinned GbV config already authenticated in the private baseline package:

`outputs/published_baseline_gbv_nli_v1/infrastructure/model_snapshot/config.json`

Require:

- model ID `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`
- revision `5a4338ab2151dc8db04ad53b42b6153382bf4f99`
- exact `id2label` semantic mapping containing positive `entailment` and negative `not_entailment`
- `resolve_entailment_index(id2label) == 0`

Run the committed `tests/test_gbv_nli.py`. The suite must include regression coverage for:

- three-class `ENTAILMENT/NEUTRAL/CONTRADICTION`;
- pinned binary `entailment/not_entailment` -> index 0;
- reversed binary `not_entailment/entailment` -> the actual positive index;
- generic `LABEL_0/LABEL_1` -> fail closed;
- negative `not_entailment` alone must never count as positive entailment.

No monkeypatch, runtime override, model-config edit, or local copy of a different resolver is permitted. Scientific scoring must import the corrected committed `src/verification/gbv_nli.py` directly.

Write a compatibility receipt under `prelabel_seal_v3/preflight/` and require PASS before continuing.

## Stage B — reverify immutable parent anchors

Require the already frozen scientific parents:

- selected fresh-ID ledger SHA-256: `a6e5055380e0cb50318b22df5ec4c1eaeda607040762e8819863783d683592ff`
- cohort freeze SHA-256: `0e02d187a379a730f70b24ef33033dbbe93e72c1860fb9b2f20b42b744e7f7f4`
- candidate-pool freeze SHA-256: `bbcf1e6110607fc0cf65cdcc2647385a0d50d8aa0645812d82509a82e8b0cded`
- retrieval freeze SHA-256: `606d6148af431313c86477d22d9c235a72fc236257c5c120772aa495dca3ddca`
- runtime branch freeze SHA-256: `af0bbbbd96d9629155dac1adf35e68c78e7e74dfca49b8c31fa2ed93d62a7b09`
- canonical branch ledger SHA-256: `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`
- branch provenance sidecar SHA-256: `4d0ce2c89bb96c33e76d4d1879add655cd79e9c4bd3b9f0545197254ad759b20`
- runtime independent validation SHA-256: `d401ffdfd835b8ece9d13b040d81bccdcc3e245a5f6b67cb167bf630ef56d1f1`
- trace count = 13,500
- question clusters = 4,500
- exact 1,500 traces in every dataset x retriever stratum
- runtime Gold/outcome access = 0

Any mismatch is a hard stop.

## Stage C — reuse the already validated metadata binding, without expanding its authority

The second blocked attempt produced a valid label-free binding:

`outputs/daa_v2_fresh_v1/prelabel_seal_v2/binding/canonical_metadata_binding.jsonl`

Frozen SHA-256:

`66a264216f1c3a9e474b68502d30e278412117d4a1d3ff4cc76bb86f97434cf3`

Its validation is:

`outputs/daa_v2_fresh_v1/prelabel_seal_v2/binding/BINDING_VALIDATION.json`

Frozen SHA-256:

`1ff235e99f7408b9e01dcf8d965f64433614eaa4bdbc1678ca348e9b3baaa684`

Reverify the hashes and require validation status PASS, 13,500 traces, 135,000 evidence positions, missing bindings = 0, duplicate bindings = 0, text/metadata mismatches = 0, defaults/fabrication/fuzzy joins = false, fresh labels accessed = 0.

Do not regenerate a different metadata projection unless the preserved projection fails an integrity hash check. If it fails, stop rather than silently repair it.

`canonical_branches.jsonl` remains sole authority for trace membership/order, question, a0/a1 and evidence text. The sidecar binding may supply only the metadata explicitly authorized in `V2_PROTOCOL_AMENDMENT_PRELABEL_METADATA_SIDECAR.md`.

## Stage D — historical artifact and feature-path authentication

Run the committed historical artifact verifier:

```powershell
python scripts/verify_v2_private_artifacts.py `
  --historical-root outputs/mars_full `
  --output outputs/daa_v2_fresh_v1/prelabel_seal_v3/preflight/private_artifacts.json
```

Require PASS and exact required model hashes.

Authenticate the historical feature/likelihood construction path used by the accepted experiment. Do not recreate similar features from memory. No Gold/outcome is permitted in the fresh feature path.

## Stage E — fit the frozen DAA-V2 ensemble from historical development only

Locate exact historical ledgers with hashes:

- decisions: `74bd8e45a3bbdb7716a02fc063b5a6e35c6ded8810441d422d964b7633b19cbd`
- outcomes: `a1862495b6e0c9033c420773da93fe36bd335cd8c04da01825b327477848f2f7`

Run the committed `scripts/fit_v2_ensemble.py` exactly once for this scientific attempt and write:

- `prelabel_seal_v3/models/daa_v2.joblib`
- `prelabel_seal_v3/models/daa_v2_manifest.json`

Historical outcome access is allowed only for this frozen development fit. Fresh labels/outcomes are not allowed.

Require the committed constants: five grouped folds, frozen group seed, `lambda_damage=1.0`, `meta_alpha=2.0`, action rate `0.05`, exact ten feature names, no dataset-ID feature.

## Stage F — extract the ten frozen label-free fresh base scores

Use:

- canonical branch ledger for question/a0/a1/evidence text and trace order;
- the exact validated metadata binding from Stage C for the allowed document metadata only;
- authenticated historical Qwen/BGE likelihood/embedding/feature implementation;
- exact verified historical estimator binaries.

Write:

`outputs/daa_v2_fresh_v1/prelabel_seal_v3/scoring/v2_base_scores.jsonl`

Each row must contain exactly `dataset`, `retriever`, `sample_id`, `scores`, and `scores` must contain exactly:

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

Require exactly 13,500 unique trace keys. No Gold/outcome-like field or quality-based filtering/imputation/recalibration is allowed.

Record model revisions, exact artifacts, call counters and output SHA-256. Do not expose fresh per-trace score distributions to the author before the final combined gate.

## Stage G — run the structural/leakage preflight

Run the committed `scripts/preflight_v2_fresh.py` against:

- frozen selected IDs;
- frozen canonical branches;
- new V3 base-score ledger;
- new V3 private-artifact verification.

Write `prelabel_seal_v3/preflight/fresh_preflight.json` and require PASS.

## Stage H — seal DAA-V2 and raw HGB at the frozen primary budget

Run the committed `scripts/score_v2_prelabel.py`.

Require:

- trace count = 13,500
- action rate = 0.05
- DAA-V2 replace count = 675
- raw HGB replace count = 675
- equal/empty normalized answer pairs forced KEEP according to the committed shared eligibility rule
- no Gold/outcome input

Write only into `prelabel_seal_v3/decisions/` and freeze hashes immediately.

## Stage I — prospectively score GbV on the exact same canonical branches

Run the committed corrected `scripts/score_gbv_fresh_prelabel.py` importing the corrected committed `src/verification/gbv_nli.py`.

Frozen recipe remains unchanged:

- model `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`
- revision `5a4338ab2151dc8db04ad53b42b6153382bf4f99`
- slow tokenizer
- float32 CUDA
- hypothesis `The answer to the question "{q}" is: "{a}"`
- each evidence passage independently
- 20-word overlap overlength chunking, every pair fit-checked
- max entailment probability
- margin `F1-F0`
- same shared pair eligibility

Use local-only model assets after verifying exact cache/model file provenance.

Require entailment index = 0 in the saved provenance.

Write:

- `prelabel_seal_v3/scoring/gbv_scores.jsonl`
- `prelabel_seal_v3/scoring/gbv_provenance.json`

No Gold/outcome input.

## Stage J — seal all frozen GbV operating points

Run committed `scripts/match_gbv_prelabel.py`.

Require:

- primary `gbv_global_matched` = exactly 675 actions
- secondary `gbv_stratum_matched` = exactly 675 actions and exact equality to every DAA-V2 dataset x retriever action budget
- historical-policy thresholds exactly:
  - BM25 `0.0473407506942749`
  - Dense `0.01295558363199234`
  - Hybrid `0.4287375956773758`

No threshold retuning, calibration or action-budget change.

## Stage K — independent scientific pre-label validation

Create a V3 independent validator that does not use the action scripts as its oracle. Independently recompute from frozen numeric ledgers:

- all trace-key sets and counts;
- shared answer-pair eligibility;
- V2/raw-HGB replacement counts;
- V2 and raw-HGB stable ranking/tie-break consistency;
- GbV global same-budget selection;
- exact-stratum GbV budgets;
- transferred historical GbV thresholds;
- all recorded artifact hashes;
- no fresh Gold/outcome fields or reads.

It may inspect scores because this is a pre-label integrity validator, but it must not compare them to fresh outcomes or make quality claims.

Require PASS.

## Stage L — combined pre-label gate

Run the committed `scripts/seal_v2_gbv_prelabel_gate.py` using only V3 artifacts.

Require:

- combined gate status PASS;
- DAA-V2 replace count 675;
- raw-HGB replace count 675;
- GbV global matched count 675;
- GbV exact-stratum count 675;
- all exact stratum budgets equal V2 budgets;
- frozen historical GbV thresholds exact;
- `fresh_label_access_authorized=false`;
- `post_seal_evaluation_started=false`.

Write:

`outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/combined_prelabel_gate.json`

## Stage M — final pre-label seal and complete manifest

Write `PRELABEL_SEAL.json` binding:

- both prior blocked namespace manifests/hashes;
- both prospective correction documents;
- corrected source/test commit/hash provenance;
- all parent cohort/pool/retrieval/runtime hashes;
- metadata-binding hashes;
- historical development/model hashes;
- DAA-V2 model manifest/hash;
- V2 base-score ledger/hash;
- V2/HGB action ledger/seal hashes;
- GbV score/provenance hashes and entailment index 0;
- GbV action ledger/seal hashes;
- independent validation hash;
- combined gate hash;
- all execution call counters and package/model versions;
- explicit confirmation that fresh labels accessed = 0 and Gold mapping/evaluation not started.

Then write a complete recursive SHA-256 manifest excluding only the manifest itself.

## Author-facing completion report

Return only counts, hashes, configuration/provenance and integrity status. Do not show example questions, answers, evidence, per-trace scores, margins, or action-ranked examples.

At minimum report:

- resolver compatibility PASS and entailment index 0;
- metadata binding PASS;
- historical authentication PASS;
- base score trace count;
- DAA-V2 eligible/scorable and forced-KEEP counts;
- DAA-V2 action count = 675;
- raw-HGB action count = 675;
- GbV scored/forced-KEEP counts;
- GbV global matched = 675;
- GbV exact-stratum matched = 675;
- GbV historical-threshold action count (descriptive only);
- independent validation status;
- combined pre-label gate status;
- fresh label access = 0;
- final seal and manifest hashes.

## HARD STOP

After the combined gate, final pre-label seal and complete manifest are written, **STOP**.

Do not load, map or evaluate fresh Gold/outcomes in the same execution. Do not run `evaluate_v2_vs_gbv.py`. Do not reveal which method is better. A separate explicit responsible-human authorization is required for post-seal Gold mapping and evaluation.
