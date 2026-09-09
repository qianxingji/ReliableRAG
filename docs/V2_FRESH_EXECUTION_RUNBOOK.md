# DAA-V2 fresh confirmatory execution runbook

This runbook is designed for the full private project at `E:\paper\ReliableRAG`. The public GitHub branch contains the V2 decision/evaluation layer, while the already validated private project contains the retrieval, generation, likelihood-feature, source-projection, and historical-model runtime required to build a new fresh cohort.

## Non-negotiable rule

There are two different executions:

1. **Gold-free execution to the combined pre-label gate.**
2. **Separately authorized post-seal outcome mapping/evaluation.**

The first execution must terminate after the combined gate passes. Never place a fresh Gold/outcome file on the command line of a pre-label script.

## Stage 0 — immutable starting point

Work in a new namespace such as:

`outputs/daa_v2_fresh_v1/`

Do not modify historical `outputs/mars_full/` or any accepted Phase10 namespace.

Snapshot and hash:

- current source tree;
- Python interpreter and environment;
- historical `method_freeze.json` and model files;
- existing Phase10 source-projection controls;
- raw source files by SHA-256.

Run:

```powershell
python scripts/verify_v2_private_artifacts.py `
  --historical-root outputs/mars_full `
  --output outputs/daa_v2_fresh_v1/preflight/private_artifacts.json
```

Expected result: `PASS`. Any missing/mismatched artifact is a hard stop.

## Stage 1 — identifier-only availability audit

Use the already audited Phase10 source-projection machinery to create **ID-only** JSONL inventories containing exactly:

```json
{"dataset":"hotpotqa","sample_id":"..."}
```

Create separate source inventories for:

- HotpotQA distractor validation;
- 2WikiMultiHopQA corrected dev;
- MuSiQue train.

Export ID-only forbidden ledgers for every previously used question ID, including main development/calibration, main confirmatory, operator transfer, earlier evaluation/robustness/reader studies, and previous Fresh-ID evaluation. For the strictest primary freshness definition, also include the previous Fresh extension's corpus-only contributor IDs in the forbidden-evaluation ledger.

Audit availability first:

```powershell
python scripts/select_v2_fresh_ids.py `
  --source outputs/daa_v2_fresh_v1/ids/hotpot_source.jsonl `
  --source outputs/daa_v2_fresh_v1/ids/2wiki_source.jsonl `
  --source outputs/daa_v2_fresh_v1/ids/musique_train_source.jsonl `
  --forbidden outputs/daa_v2_fresh_v1/ids/all_forbidden_ids.jsonl `
  --per-dataset 0 `
  --selected-output outputs/daa_v2_fresh_v1/ids/audit_empty.jsonl `
  --manifest-output outputs/daa_v2_fresh_v1/ids/availability_audit.json
```

Preferred target is 1,500 evaluation questions per dataset. If any source has fewer than 1,500 eligible IDs, **STOP**. Do not run a smaller cohort automatically.

If the audit passes, select once:

```powershell
python scripts/select_v2_fresh_ids.py `
  --source ... `
  --forbidden ... `
  --per-dataset 1500 `
  --seed 20260910-v2-fresh `
  --selected-output outputs/daa_v2_fresh_v1/ids/selected_fresh_ids.jsonl `
  --manifest-output outputs/daa_v2_fresh_v1/ids/selection_manifest.json
```

Freeze both files before retrieval/generation.

## Stage 2 — build shared candidate pools and completed branches

Reuse the validated Phase10 runtime components rather than reimplementing retrieval/generation.

Frozen components:

- BM25, Dense and Hybrid/RRF definitions from the accepted experiment;
- Dense model `BAAI/bge-base-en-v1.5` revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`;
- reader `Qwen/Qwen2.5-3B-Instruct` revision `aa8e72537993ba99e69dfaafa59ed015b17504d1`;
- deterministic decoding, BF16 CUDA, batch size 1;
- Top-5 evidence, 16,000-character evidence budget;
- fixed missing-information repair query;
- first depth-50 document outside original Top-5 replaces rank 5.

Gold/supporting-fact/alias/correctness fields remain forbidden from runtime projection.

Save candidate-pool fingerprints and one canonical branch ledger with exactly these fields:

- dataset
- retriever
- sample_id
- question
- a0
- a1
- evidence0
- evidence1

Each selected question must have exactly BM25, Dense and Hybrid rows. Do not produce different branches for V2 and GbV: both methods consume the **same** canonical ledger.

## Stage 3 — historical base scores and V2 model

Use the exact historical model binaries verified in Stage 0 to produce the ten required label-free score fields listed in `docs/V2_REQUIRED_PRIVATE_ARTIFACTS.json`.

The fresh base-score ledger contains only:

- dataset
- retriever
- sample_id
- scores

No Gold/correctness/outcome field is allowed.

Fit the fixed V2 cross-fitted ensemble only from the historical 9,000-trace developmentized cohort:

```powershell
python scripts/fit_v2_ensemble.py `
  --decisions <historical_nonoracle_decision_ledger> `
  --outcomes <historical_numeric_outcome_ledger> `
  --model-output outputs/daa_v2_fresh_v1/models/daa_v2.joblib `
  --manifest-output outputs/daa_v2_fresh_v1/models/daa_v2_manifest.json
```

This historical outcome access is permitted because these 9,000 traces are now V2 development evidence. It must occur before any fresh-label access. The fixed V2 parameters remain lambda=1.0, alpha=2.0, action rate=5.0%.

Run the structural/leakage gate:

```powershell
python scripts/preflight_v2_fresh.py `
  --selected-ids outputs/daa_v2_fresh_v1/ids/selected_fresh_ids.jsonl `
  --branches outputs/daa_v2_fresh_v1/runtime/canonical_branches.jsonl `
  --v2-score-ledger outputs/daa_v2_fresh_v1/scoring/v2_base_scores.jsonl `
  --private-artifact-verification outputs/daa_v2_fresh_v1/preflight/private_artifacts.json `
  --output outputs/daa_v2_fresh_v1/preflight/fresh_preflight.json
```

Expected result: PASS.

## Stage 4 — seal DAA-V2 actions

```powershell
python scripts/score_v2_prelabel.py `
  --branches outputs/daa_v2_fresh_v1/runtime/canonical_branches.jsonl `
  --score-ledger outputs/daa_v2_fresh_v1/scoring/v2_base_scores.jsonl `
  --model outputs/daa_v2_fresh_v1/models/daa_v2.joblib `
  --actions-output outputs/daa_v2_fresh_v1/decisions/v2_actions.jsonl `
  --seal-output outputs/daa_v2_fresh_v1/decisions/v2_seal.json
```

At 4,500 questions there are 13,500 traces, so 5.0% corresponds to 675 V2 replacement actions. The script computes the budget from actual trace count; do not hard-code 675 in runtime code.

## Stage 5 — independently score and seal GbV

Install the prospective GbV environment before scoring and record exact runtime package/CUDA versions. The model recipe itself is fixed in code.

```powershell
python scripts/score_gbv_fresh_prelabel.py `
  --branches outputs/daa_v2_fresh_v1/runtime/canonical_branches.jsonl `
  --scores-output outputs/daa_v2_fresh_v1/scoring/gbv_scores.jsonl `
  --provenance-output outputs/daa_v2_fresh_v1/scoring/gbv_provenance.json `
  --device cuda:0 `
  --batch-size 8 `
  --dtype float32
```

Then match GbV to V2 without labels:

```powershell
python scripts/match_gbv_prelabel.py `
  --v2-actions outputs/daa_v2_fresh_v1/decisions/v2_actions.jsonl `
  --gbv-scores outputs/daa_v2_fresh_v1/scoring/gbv_scores.jsonl `
  --actions-output outputs/daa_v2_fresh_v1/decisions/gbv_actions.jsonl `
  --seal-output outputs/daa_v2_fresh_v1/decisions/gbv_seal.json
```

This produces:

- primary GbV actions with the exact same total replacement budget as V2;
- secondary GbV actions with exact V2 dataset x retriever budgets.

## Stage 6 — combined pre-label gate and mandatory stop

```powershell
python scripts/seal_v2_gbv_prelabel_gate.py `
  --fresh-preflight outputs/daa_v2_fresh_v1/preflight/fresh_preflight.json `
  --v2-seal outputs/daa_v2_fresh_v1/decisions/v2_seal.json `
  --gbv-provenance outputs/daa_v2_fresh_v1/scoring/gbv_provenance.json `
  --gbv-match-seal outputs/daa_v2_fresh_v1/decisions/gbv_seal.json `
  --v2-actions outputs/daa_v2_fresh_v1/decisions/v2_actions.jsonl `
  --gbv-scores outputs/daa_v2_fresh_v1/scoring/gbv_scores.jsonl `
  --gbv-actions outputs/daa_v2_fresh_v1/decisions/gbv_actions.jsonl `
  --output outputs/daa_v2_fresh_v1/decisions/combined_prelabel_gate.json
```

Required status: PASS.

**STOP THE PROCESS HERE.** Archive/hash the namespace. Do not open Gold and do not run evaluation in the same authorized execution.

## Stage 7 — separately authorized Gold mapping and evaluation

Only after the responsible human author explicitly authorizes post-seal evaluation should the fresh Gold be projected into a separate numeric outcome ledger containing IDs plus `a0_em`, `a1_em`, `a0_f1`, `a1_f1`.

Then run exactly the predeclared evaluator:

```powershell
python scripts/evaluate_v2_vs_gbv.py `
  --v2-actions outputs/daa_v2_fresh_v1/decisions/v2_actions.jsonl `
  --gbv-actions outputs/daa_v2_fresh_v1/decisions/gbv_actions.jsonl `
  --outcomes <separately_authorized_fresh_numeric_outcomes.jsonl> `
  --output outputs/daa_v2_fresh_v1/evaluation/v2_vs_gbv.json
```

No score, model, action, budget, source, or cohort file may change after the combined pre-label gate.

## Interpretation

- The primary published-method comparison is the same-total-budget `gbv_global_matched` result.
- `gbv_stratum_matched` is a secondary ranking-only fairness analysis.
- Formal primary superiority is based on the predeclared paired EM cluster interval.
- The stronger multi-condition gate is an engineering success target, not familywise inference.
- If the formal or high-standard targets fail, retain the result and do not rerun with new hyperparameters.
