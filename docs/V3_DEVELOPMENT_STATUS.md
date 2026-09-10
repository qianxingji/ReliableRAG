# DAA-V3 development status after the completed DAA-V2 fresh confirmation

## Status

DAA-V2 prospective confirmation is complete and immutable. The execution/integrity pipeline passed, but the predeclared scientific superiority target against the primary same-total-budget GbV comparator did not pass.

The completed DAA-V2 fresh cohort may now be used as **development evidence for a future DAA-V3 method only**. It may never again be described as unseen/fresh/confirmatory evidence for any method whose design is influenced by these results.

Any future DAA-V3 confirmatory claim requires a new cohort of previously untouched IDs selected and sealed only after DAA-V3 development is closed.

## Immutable DAA-V2 result anchors

The following completed artifacts are development inputs for V3 and must not be rewritten:

- `outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl`
  - SHA-256 `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`
- `outputs/daa_v2_fresh_v1/final_evaluation/primary/v2_vs_gbv.json`
  - SHA-256 `43eaa9e99ad1f40e46f0568ddb9dcf720ae09dd1968c10ef976e7e0e22fe9bdd`
- `outputs/daa_v2_fresh_v1/final_evaluation/independent/FINAL_EVALUATION_VALIDATION.json`
  - SHA-256 `ec1fef059d5680b0e8e10f178cb25e87dd6ff1c0cee982d02d23e424e8ed83d5`
- `outputs/daa_v2_fresh_v1/final_evaluation/FINAL_EVALUATION_SEAL.json`
  - SHA-256 `c1aa720afdee0f816fe0c043125d460e42786d740001b6fc501e01acd0d6132d`
- `outputs/daa_v2_fresh_v1/final_evaluation/SHA256_MANIFEST.json`
  - the preserved local manifest must remain byte-identical; record its actual SHA-256 before V3 analysis.

The pre-label scientific inputs also remain immutable:

- V2 actions `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- GbV actions `7dd95ed3bfdec07cacc00321bdacbb68e4fe7e18712861f8371cc0b3507ed07e`
- V2 base scores `d3842c514224354206846edb7e96b7296765d67050b131b552f469d0c64fa609`
- GbV scores `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`
- DAA-V2 model `8fbb5b825c67e574ff623629c1b3c4688ad23b10dcbbef14e839c8d585cad334`
- canonical branches `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`

## Frozen DAA-V2 scientific conclusion

The primary same-total-budget comparison used 675 actions per method.

DAA-V2 achieved:

- recovery 296;
- damage 23;
- net 273;
- EM 20.222222%;
- F1 25.403624%.

GbV global same-budget achieved:

- recovery 259;
- damage 15;
- net 244;
- EM 20.007407%;
- F1 25.281763%.

The primary DAA-V2 minus GbV EM difference was `+0.214815` percentage points with paired question-cluster 95% CI `[-0.066667, +0.496296]`. The predeclared formal primary superiority criterion therefore failed.

The secondary exact dataset × retriever budget-matched GbV comparison produced a positive EM difference of `+0.288889` percentage points with 95% CI `[+0.014815, +0.562963]`. This remains secondary evidence and must not be promoted retroactively to the primary test.

DAA-V2 versus raw global HGB at the same 675-action budget produced only `+0.059259` EM percentage points with 95% CI `[-0.074074, +0.192593]`, while DAA-V2 incurred 23 damages versus raw HGB's 20. Thus the V2 meta correction did not establish a clear fresh advantage over its HGB backbone.

The frozen five-rate secondary grid also did not satisfy the development engineering frontier criterion: DAA-V2 had higher net correction with no more damage than GbV at `0/5` rates.

## V3 development question

V3 development must focus on the failure mode actually observed:

**DAA-V2 increased recovery relative to same-budget GbV, but did not suppress damage enough, and its incremental benefit over raw HGB was small.**

The next question is not "which V2 threshold looks best after Gold?" It is:

> Can a new arbitration design preserve the recovery strength of the HGB/V2 ranking while introducing a genuinely effective damage-control mechanism that generalizes across datasets and retrievers?

Potential structural directions may include, but are not yet chosen:

- a two-stage safe-set / damage-veto architecture;
- explicit recovery and damage heads with risk-constrained selection;
- cross-retriever question-level consistency signals;
- retriever-aware calibration without dataset-ID leakage.

No V3 architecture is frozen by this document.

## Development evidence boundary

For V3, the following may be used as development evidence:

1. the historical 9,000-trace / 3,000-question cohort already designated as V2 development evidence;
2. the completed 13,500-trace / 4,500-question DAA-V2 fresh cohort, now opened and therefore development-only for V3.

Do not naively concatenate cohorts without checking distribution shift, source-split differences, candidate-pool differences, and retriever-conditioned behavior. Any V3 model-development protocol must use question-grouped validation and explicitly account for cohort identity during validation; cohort identity itself should not automatically become a runtime feature.

## Hard boundary

The immediate next task is failure analysis and design audit only.

Do not yet:

- fit or tune DAA-V3;
- search V3 hyperparameters;
- select a new V3 primary action budget;
- choose a new confirmatory cohort;
- run new retrieval/generation;
- reuse the opened V2 fresh cohort as V3 confirmation;
- hide, rewrite, or supersede the failed DAA-V2 primary result.

DAA-V2 remains a valid completed experiment with a negative/inconclusive primary comparison and informative secondary/development evidence.