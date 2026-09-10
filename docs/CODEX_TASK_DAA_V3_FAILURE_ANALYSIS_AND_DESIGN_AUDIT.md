# Codex task — DAA-V3 failure analysis and design audit only

## Scope and branch

Work against the full private project at `E:\paper\ReliableRAG` on branch:

`v3-risk-constrained-arbitration`

Read `AGENTS.md` and `docs/V3_DEVELOPMENT_STATUS.md` first.

The completed DAA-V2 fresh evaluation is now **development evidence for V3**. This task is diagnostic/design work only. It may use the already opened numeric Gold outcomes, but it must not train, tune, select, or claim a new V3 method.

The objective is to determine, from saved evidence, **why DAA-V2 gained recovery but failed to control damage and failed to establish a clear improvement over raw HGB**, then produce a small set of falsifiable V3 design hypotheses.

## Hard prohibitions

Do not:

- modify any DAA-V2 cohort, source, candidate pool, retrieval, branch, score, action, outcome, seal, or final-result artifact;
- rerun generation or retrieval;
- refit DAA-V2 or any historical estimator;
- train a DAA-V3 model;
- sweep lambda/alpha/action rate/thresholds/features;
- choose a new primary budget from the opened outcomes;
- select future confirmatory IDs;
- present any post-hoc V3 simulation as fresh/confirmatory evidence;
- delete or rewrite the negative/inconclusive DAA-V2 primary result.

If an input hash differs from the accepted anchors, STOP.

## Read-only scientific inputs and anchors

Verify at minimum:

### Final opened V2-fresh development evidence

- `outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl`
  - SHA-256 `2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`
- `outputs/daa_v2_fresh_v1/final_evaluation/primary/v2_vs_gbv.json`
  - SHA-256 `43eaa9e99ad1f40e46f0568ddb9dcf720ae09dd1968c10ef976e7e0e22fe9bdd`
- `outputs/daa_v2_fresh_v1/final_evaluation/independent/FINAL_EVALUATION_VALIDATION.json`
  - SHA-256 `ec1fef059d5680b0e8e10f178cb25e87dd6ff1c0cee982d02d23e424e8ed83d5`
- `outputs/daa_v2_fresh_v1/final_evaluation/FINAL_EVALUATION_SEAL.json`
  - SHA-256 `c1aa720afdee0f816fe0c043125d460e42786d740001b6fc501e01acd0d6132d`
- final evaluation manifest: preserve and record its actual hash; do not rewrite it.

### Frozen pre-label inputs

- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/v2_actions.jsonl`
  - SHA-256 `2ca4c82db8581648c7c6ad2bfb79b07eea4f4723d56ac135ac1149c38740f065`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/decisions/gbv_actions.jsonl`
  - SHA-256 `7dd95ed3bfdec07cacc00321bdacbb68e4fe7e18712861f8371cc0b3507ed07e`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/scoring/v2_base_scores.jsonl`
  - SHA-256 `d3842c514224354206846edb7e96b7296765d67050b131b552f469d0c64fa609`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/scoring/gbv_scores.jsonl`
  - SHA-256 `c4cc54d7ec3e6d8d4663f57ecbc1ff52e15b3448bf0f9cee76404f03a49e42ca`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v3/models/daa_v2.joblib`
  - SHA-256 `8fbb5b825c67e574ff623629c1b3c4688ad23b10dcbbef14e839c8d585cad334`
- `outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl`
  - SHA-256 `ac83f029e53f1e5b80eb00b8cbcc609edc07cef1ccde4b57fb17210888f81a09`

### Historical development evidence

Use the already designated historical development files only when needed for distribution-shift analysis:

- decisions SHA-256 `74bd8e45a3bbdb7716a02fc063b5a6e35c6ded8810441d422d964b7633b19cbd`
- outcomes SHA-256 `a1862495b6e0c9033c420773da93fe36bd335cd8c04da01825b327477848f2f7`

Do not mutate or regenerate them.

## Accepted frozen V2 result to reproduce before analysis

Independently re-derive these headline facts from the ledgers before deeper diagnostics:

- trace count 13,500;
- question clusters 4,500;
- DAA-V2 actions 675, recovery 296, damage 23, net 273;
- GbV global matched actions 675, recovery 259, damage 15, net 244;
- raw HGB actions 675, recovery 285, damage 20, net 265;
- DAA-V2 minus GbV primary EM `+0.214815` pp, 95% CI `[-0.066667, +0.496296]`;
- DAA-V2 minus raw HGB EM `+0.059259` pp, 95% CI `[-0.074074, +0.192593]`;
- exact-stratum secondary DAA-V2 minus GbV EM `+0.288889` pp, 95% CI `[+0.014815, +0.562963]`;
- five-rate frontier success `0/5` under the frozen criterion.

If these cannot be reproduced exactly within numerical tolerance, STOP.

## Output namespace

Create only:

`outputs/daa_v3_development/failure_audit_v1/`

Recommended outputs:

- `INPUT_VERIFICATION.json`
- `TRANSITION_CENSUS.json`
- `SELECTION_OVERLAP.json`
- `DAMAGE_RECOVERY_DIAGNOSTICS.json`
- `V2_PROBABILITY_DIAGNOSTICS.json`
- `CROSS_RETRIEVER_DIAGNOSTICS.json`
- `COHORT_SHIFT_DIAGNOSTICS.json`
- `ALLOCATION_DIAGNOSTICS.json`
- `V3_DESIGN_CANDIDATES.md`
- `INDEPENDENT_VALIDATION.json`
- `FAILURE_AUDIT_SEAL.json`
- `SHA256_MANIFEST.json`

No raw benchmark text should be copied into public-facing reports. Internal temporary processing may read canonical branch text as needed for deterministic features, but the final reports should contain aggregate statistics and hashes only.

## Stage A — transition census

Using the sealed outcome ledger, classify every trace strictly from normalized EM transitions:

- recovery: `a0_em=0, a1_em=1`;
- damage: `a0_em=1, a1_em=0`;
- neutral: all other states, while separately retaining `00` and `11` counts where useful.

Report:

- total counts and rates;
- eligible/scorable-only counts using the frozen answer-pair eligibility rule;
- counts by dataset × retriever;
- counts by dataset and retriever marginally;
- initially-correct denominator and damage rates.

No semantic relabeling is allowed.

## Stage B — exact method-selection overlap

Construct the sealed action sets for:

- DAA-V2 (`V`);
- raw HGB (`H`);
- GbV global matched (`G`);
- GbV exact-stratum matched (`S`);
- GbV historical-dev-selected (`D`).

For V/H/G, all are 675-action primary-scale sets.

Compute:

- pairwise intersections, unions, Jaccard coefficients;
- `V∩H`, `V\H`, `H\V`;
- `V∩G`, `V\G`, `G\V`;
- the full V/H/G 3-set partition;
- for every nonempty partition region: count, recovery, damage, neutral, net, action recovery %, action damage %;
- the same summary by dataset and retriever for the important exclusive regions.

This stage must answer numerically:

1. Where do the 37 extra DAA-V2 recoveries over global GbV come from?
2. Where do DAA-V2's 8 extra damages over global GbV come from?
3. What changed relative to raw HGB: which V2-added actions create the +11 recoveries and +3 damages relative to HGB's totals, and what was lost among HGB-only actions?

Do not infer causality from overlap alone.

## Stage C — damage versus recovery score/feature diagnostics

For the 3,202 frozen eligible/scorable traces, join outcomes to:

- the ten V2 base-score fields;
- sealed `v2_score`;
- sealed `hgb_score`;
- sealed `gbv_margin`.

For each of these groups:

- DAA-selected recovery;
- DAA-selected damage;
- DAA-selected neutral;
- DAA-not-selected recovery;
- raw-HGB-selected damage/recovery;
- GbV-global-selected damage/recovery;

report robust aggregate diagnostics only:

- count;
- median, quartiles, 10th/90th percentiles for each score/feature;
- within-scorable rank percentile distributions;
- dataset/retriever breakdowns;
- standardized median difference or another clearly defined robust effect summary between DAA-selected recovery and DAA-selected damage.

Do not conduct a broad p-value fishing exercise. The aim is failure localization, not retrospective hypothesis significance.

Explicitly identify whether DAA damages are concentrated near the 675-action cutoff or also occur among high-ranked actions.

## Stage D — reconstruct the frozen DAA-V2 probability heads

Load the sealed DAA-V2 bundle only for diagnostic inference. Do not refit it.

Reconstruct, for all 3,202 scorable traces, the ensemble's predicted:

- `p(recovery)`;
- `p(damage)`;
- `p(neutral)`;
- utility `p(recovery)-p(damage)`;
- final fused score.

First verify the recomputed fused scores reproduce the sealed `v2_score` values within a strict numeric tolerance. If they do not, stop this stage and report the mismatch.

Then report development-only diagnostics:

- predicted probability distributions by true transition state;
- Brier score for recovery and damage heads;
- fixed-bin reliability tables for recovery and damage (use a predeclared simple binning such as 10 equal-width bins; do not search binning);
- ECE with the same fixed bins;
- actual damage rate across deciles of predicted damage probability and fused-score rank;
- DAA-selected damage cases' p(damage) distribution versus DAA-selected recovery cases.

This stage is specifically to test whether the damage head is underestimating risk in the fresh cohort.

## Stage E — cross-retriever question-level diagnostics

Group the 13,500 traces into the 4,500 frozen question clusters with exactly BM25, Dense and Hybrid siblings.

Without fitting a new model, quantify:

- the 3-way transition-state pattern per question;
- how often repair recovery/damage is shared across multiple retrievers versus isolated to one retriever;
- for each DAA-selected damage, the sibling retrievers' true transition states and sealed pre-label score ranks;
- for each DAA-only recovery versus GbV, whether sibling traces provide concordant pre-label evidence;
- answer-change agreement across retrievers using the already frozen normalization, reported only as aggregate counts;
- whether DAA damage is enriched among questions with cross-retriever disagreement.

Also compute question-level selection multiplicity for V, H, and G: 0/1/2/3 selected traces per question, with recovery/damage/net summaries.

Do not construct or evaluate a new gate yet. This is descriptive evidence for deciding whether cross-retriever information deserves to enter V3.

## Stage F — retriever/dataset allocation diagnostics

Compare the sealed V2 action allocation to GbV global and exact-stratum allocations.

Report:

- action counts per 9 strata;
- recovery/damage/net per selected action stratum;
- primary DAA-V2 minus GbV-global EM point differences by dataset/retriever;
- exact-stratum comparison outcomes;
- the change in the DAA-minus-GbV contrast when switching only the comparator from global-budget allocation to exact V2 stratum budgets.

Describe this as an **allocation-constrained comparison difference**, not a causal decomposition.

Pay particular attention to the observed development pattern that BM25 was favorable while Hybrid and MuSiQue were weaker in the primary comparison.

## Stage G — cohort-shift diagnostics versus historical V2 development

Use only saved historical development ledgers and the current opened V2-fresh development cohort.

Compare at minimum:

- recovery/damage/neutral base rates;
- the ten base-score distributions where semantically identical fields exist;
- HGB score distribution and selected-region transition composition;
- dataset/retriever-conditioned differences;
- answer-change / eligibility rates;
- DAA-V2's predicted damage probabilities versus realized damage rates in historical OOF development and current V2-fresh development, if exact historical OOF probabilities can be reconstructed without refitting.

Use descriptive distribution-shift measures such as median/IQR differences, KS statistic, and PSI with a fixed definition. Do not select features by significance alone.

Clearly flag differences in source split / candidate-pool construction that make direct pooling risky.

## Stage H — evidence-backed V3 design candidates

Create `V3_DESIGN_CANDIDATES.md` with at most **three** architecture candidates. Each candidate must include:

- the failure evidence it directly addresses;
- exact runtime inputs it would require;
- whether it adds any new model or only changes arbitration;
- expected compute under the 16 GB RTX 5060 Ti constraint;
- leakage/generalization risks;
- why it is scientifically more than a threshold retune;
- one or more falsifiable development criteria;
- what evidence would cause the candidate to be rejected.

The candidate list should consider, but not assume, these directions:

1. **two-stage safe-set + damage veto**: preserve a strong recovery ranker but use a separately cross-fitted damage-risk gate before final ranking;
2. **explicit constrained dual-head selection**: optimize recovery subject to an explicit predicted-damage/risk budget rather than only subtracting a fixed lambda-weighted damage probability;
3. **cross-retriever question-level arbitration**: use sibling BM25/Dense/Hybrid pre-label signals to suppress isolated risky repairs and exploit concordance.

Do not train any of them in this task.

End the file with one recommended candidate or hybrid architecture **only if the diagnostics support it**. If evidence is mixed, say so and recommend the smallest next experiment needed to distinguish them.

## Stage I — independent validation

Use an independent implementation that does not import the main failure-analysis script as its oracle.

Independently verify:

- all input hashes;
- 13,500 trace / 4,500 cluster structure;
- exact frozen V/H/G action counts;
- headline recovery/damage/net counts;
- pairwise action-set overlaps;
- the full V/H/G partition sums back to 13,500 and to each 675-action set;
- transition census totals;
- no parent artifacts changed;
- no V3 model was trained or fit;
- no new retrieval/generation occurred;
- no future cohort was selected.

Require status PASS before writing the final seal.

## Stage J — seal and HARD STOP

Write `FAILURE_AUDIT_SEAL.json` containing:

- status;
- branch/commit state;
- all source hashes;
- all output hashes;
- current cohort explicitly marked `V3_DEVELOPMENT_ONLY`;
- `v3_training_started=false`;
- `v3_hyperparameter_search_started=false`;
- `new_confirmatory_selection_started=false`;
- `new_retrieval_or_generation_started=false`;
- independent-validation status;
- explicit hard stop.

Write a recursive SHA-256 manifest excluding only the manifest itself.

**HARD STOP after the failure analysis/design audit.**

The next human-reviewed step will define a bounded V3 model-development protocol. No V3 candidate may be promoted directly from this audit to a new fresh test without development validation and a new prospective freeze.