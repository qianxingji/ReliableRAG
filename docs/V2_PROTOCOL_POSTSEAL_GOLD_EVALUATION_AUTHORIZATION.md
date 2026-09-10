# DAA-V2 post-seal fresh Gold mapping and confirmatory evaluation authorization

## Status

This document records the **prospective transition from the completed label-free pre-label seal to the single confirmatory fresh-outcome evaluation**. It is created only after the V3 combined pre-label gate, independent validation, and final pre-label namespace seal have passed, and before any fresh Gold mapping or evaluation has begun.

The scientific methods, action selections, comparison hierarchy, bootstrap plan, success criteria, fresh cohort, candidate pools, retrieval outputs, runtime branches, V2 model, HGB comparator, GbV scores and all action ledgers are now immutable.

## Accepted pre-label anchors

The authorized post-seal evaluation must first reverify these exact artifacts:

- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/PRELABEL_SEAL.json`
  - SHA-256 `0d5d593f2d84c5c219ccbddaed257eb3c4e3243478d9cdedda07a2cd3d14e201`
  - status `PASS`
  - fresh labels accessed `0`
  - Gold mapping started `false`
  - evaluation started `false`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/SHA256_MANIFEST.json`
  - SHA-256 `0a5246a6d270ee01674d099b970a577936bd95d6200a53e1aa3e2ce524857bfd`
  - status `PASS`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/independent_validation.json`
  - SHA-256 `f6fbe43e1c851f21362aa16a70407e65f31c0802577fc7926bad96f5f8898c8d`
  - status `PASS`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/combined_prelabel_gate.json`
  - SHA-256 `bad43503ca58df2f1f8cfd287c6b1f45310c965947c482ce0e16763bc76c7006`
  - stage `DAA_V2_GBV_COMBINED_PRELABEL_GATE`
  - status `PASS`

The sealed decision inputs are:

- DAA-V2/raw-HGB action ledger SHA-256 `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- GbV action ledger SHA-256 `7dd95ed3bfdec07cacc00321bdacbb68e4fe7e18712861f8371cc0b3507ed07e`
- GbV score ledger SHA-256 `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`
- canonical branch ledger SHA-256 `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`

The primary total action budget is immutable at 675 actions for DAA-V2, raw HGB, GbV global matched, and GbV exact-stratum matched. The transferred historical-development GbV policy has 1,242 actions and remains a secondary published-policy contrast.

## Fresh Gold source authority

Gold mapping must use only the already frozen source families corresponding to the selected 4,500 question IDs:

- HotpotQA: the same complete distractor-validation source established and equivalence-validated in the Hotpot full-validation audit;
- 2WikiMultiHopQA: the same corrected development source used in the identifier-only availability audit;
- MuSiQue: the same accepted train source used prospectively for the fresh cohort, with the source-split difference retained and disclosed.

Before decoding selected Gold values, reverify the raw/source fingerprints against the accepted audit/source-provenance artifacts. Do not substitute a mirror, alternate split, changed dataset revision, reprocessed source, or manually corrected answer.

## Metric authority

Before fresh outcome mapping, authenticate the exact answer normalization, EM, and token-F1 implementation used by the accepted project evaluation path. Do not implement a new metric from memory and do not change answer-alias handling after fresh outcomes are visible.

The mapper must use one frozen metric policy for all methods because all methods share the same `a0` and `a1` branch answers. If source-specific answer/alias semantics cannot be authenticated unambiguously before mapping, stop before exposing fresh outcome values.

## Separation of mapping from method actions

The fresh outcome-mapping process must not read DAA-V2, HGB, or GbV action/score ledgers. It may read only:

- the frozen selected question IDs;
- the frozen canonical branch ledger;
- the authorized raw Gold sources;
- authenticated metric code/configuration;
- provenance/hash controls.

Its only scientific output is a numeric outcome ledger containing exactly:

`dataset, retriever, sample_id, a0_em, a1_em, a0_f1, a1_f1`

There must be exactly 13,500 unique trace rows, 4,500 question clusters, and 1,500 questions per dataset with exactly BM25/Dense/Hybrid rows per selected question. No Gold answer string, alias string, supporting-fact field, method action, V2 score, HGB score, or GbV score may appear in that numeric outcome ledger.

## One-way boundary after Gold is opened

Once selected fresh Gold is decoded or the numeric outcome ledger is created, the experiment crosses a one-way boundary. After that point:

- do not change the cohort, source, branch ledger, candidate pools or retrieval;
- do not regenerate `a0`, repair queries, repair evidence, or `a1`;
- do not refit DAA-V2;
- do not alter any V2/HGB/GbV score;
- do not alter feature definitions, lambda, alpha, folds, seed, eligibility, tie-breaks, threshold or action budget;
- do not choose a different primary operating point;
- do not enlarge or replace the fresh cohort based on results;
- do not suppress negative, tied, inconclusive, dataset-specific, or retriever-specific outcomes.

Technical fixes after Gold access are permitted only for an objectively demonstrated implementation defect that does not alter any scientific choice; the failed execution and correction must be preserved and disclosed. Such a fix must never be chosen because it improves the result.

## Confirmatory analysis order

The first inferential output must be the frozen primary evaluation from `scripts/evaluate_v2_vs_gbv.py` using the sealed action ledgers and the sealed numeric outcome ledger. The script's predeclared settings remain:

- 10,000 paired question-cluster bootstrap draws;
- bootstrap seed `20260920`;
- cluster unit `dataset:sample_id`, retaining all three retriever rows;
- primary published-method contrast: DAA-V2 minus GbV global same-total-budget;
- formal primary superiority: lower endpoint of the 95% paired EM difference interval is greater than zero.

The predeclared high-standard engineering targets remain unchanged: EM point advantage at least +0.60 pp, EM 95% lower bound at least +0.30 pp, F1 point advantage at least +0.50 pp, F1 lower bound greater than zero, DAA-V2 damage no higher than GbV, positive dataset-level DAA-V2-minus-GbV EM points on all three datasets, and positive DAA-V2 net correction for BM25/Dense/Hybrid. These are not familywise-controlled hypothesis tests.

Only after the primary result file has been written and hashed may the fixed secondary budget grid be evaluated using `scripts/evaluate_v2_budget_curve.py` at exactly 1%, 2.5%, 5%, 7.5%, and 10%. The 5% operating point remains primary regardless of the curve.

## Reporting rule

Report the complete primary result, exact-stratum secondary comparison, historical-development-selected GbV comparison, raw-HGB key ablation, dataset/retriever breakdowns, fixed budget curve, confidence intervals, damage/recovery/net counts, and every predeclared success flag.

If DAA-V2 does not beat GbV, or beats it only on some criteria, retain and report that result. No post-Gold retuning or replacement experiment is authorized by this protocol.
