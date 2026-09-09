# DAA-V2 fresh confirmatory sample-size and source plan

## Status

**Prospective planning document. Not yet the final preregistration.** The exact fresh IDs and final question count must be frozen only after an identifier-only availability audit has passed.

## Why 3,000 question clusters are borderline

The historical same-budget Conservative-minus-GbV comparison used 3,000 question clusters and reported an EM difference of -0.044 pp with a 95% question-cluster interval of [-0.344, +0.267] pp. The interval width gives an empirical half-width proxy of approximately 0.306 pp.

Using only the conventional 1/sqrt(n) scaling as a planning approximation (not a formal prospective power guarantee):

| Unique question clusters | Approx. EM half-width proxy | If true V2-GbV = +0.60 pp, approximate lower bound |
|---:|---:|---:|
| 3,000 | 0.306 pp | +0.294 pp |
| 3,600 | 0.279 pp | +0.321 pp |
| 4,500 | 0.249 pp | +0.351 pp |
| 6,000 | 0.216 pp | +0.384 pp |

The high-standard design target is an EM point advantage >= +0.60 pp and a 95% lower confidence bound >= +0.30 pp. Therefore 3,000 clusters are approximately on the boundary under the historical variance proxy.

## Preferred target

**Preferred fresh confirmatory cohort: 4,500 unique questions = 1,500 per dataset, each with BM25, Dense, and Hybrid traces = 13,500 retriever-conditioned traces.**

This is deliberately larger than the old 3,000-question main experiment. If identifier-only source audit shows that any dataset cannot supply 1,500 genuinely unused questions under the rules below, stop before generation. Do not silently reduce the cohort. Any revised sample size must be documented as a prospective protocol amendment before inference.

## Freshness definition

A primary fresh evaluation question must not have appeared previously as:

- a development/training/calibration question for the accepted selector;
- a main confirmatory evaluation question;
- an operator-transfer evaluation question;
- a Fresh-ID evaluation question whose Gold was later opened;
- a robustness or second-reader evaluation question if its outcome was inspected.

For the strongest freshness claim, previously used corpus-only contributor IDs should also be excluded from the new evaluation-ID set. If they are reused only as corpus contributors, this must be declared separately and they must never be counted as fresh evaluation questions.

## Source strategy

- **HotpotQA:** use genuinely unused distractor-validation IDs. The currently audited local projection contains only 4,000 rows; expand the identifier/runtime projection from the official validation source before selection if fewer than 1,500 unused IDs remain. Gold fields remain structurally forbidden from the runtime projection.
- **2WikiMultiHopQA:** use genuinely unused IDs from the corrected `dev.json`; the audited source contains 12,576 rows, so availability is expected to be ample after exclusion.
- **MuSiQue:** do **not** try to obtain 1,500 new evaluation IDs from the already heavily used 2,417-row answerable dev source. Use genuinely unused IDs from `musique_ans_v1.0_train.jsonl`, excluding the historical 600-question MuSiQue development set and every other previously evaluated ID. This is an intentional source-split transfer and must be stated in the manuscript.

## Candidate-pool rule

All methods in the fresh comparison must see exactly the same original/repaired branches. Candidate-pool construction must be frozen before generation, and pool fingerprints must be recorded. The primary V2-vs-GbV claim concerns post-repair arbitration on the same completed branches, so any change in pool size or source split must be shared by both methods and reported transparently.

## Statistical unit

The statistical unit remains `dataset:question_id`. All BM25/Dense/Hybrid traces for a question remain together in bootstrap resampling. Dataset-level point estimates are reported without post-result subgroup deletion.

## Planning boundary

The 0.306-pp historical half-width is an empirical planning proxy from a different method contrast, not a guaranteed variance for V2-GbV. The final analysis uses the sealed fresh actions and the predeclared question-cluster bootstrap; negative or inconclusive findings are retained.
