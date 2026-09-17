# Response to Reviewer — JIIS Major Revision R6

Manuscript: *Supervision-Matched Selection of Paired RAG Repairs: An Empirical Study of Accuracy and Damage*

We thank the reviewer for identifying the need to sharpen the empirical contribution and to make the effective training population, fitted parameters, and public reproducibility scope explicit. We revised the manuscript without adding claims that the current evidence cannot support and without changing any scientific result.

## 1. Scope: one reader, one repair operation, and one fixed action allocation

**Comment.** The study is limited to one reader, one repair operation, and a fixed action allocation.

**Response.** We agree. The revised manuscript keeps these limits explicit in the abstract, Sect. 6.1, the conclusion, and Appendix J. It now states more directly that the evidence is conditional on Qwen2.5-3B-Instruct, the rank-5 replacement repair, the realized candidate pairs, and the global 900-action allocation. The stopped Phi and Mistral extensions are not presented as reader-effect evidence.

## 2. No joint advantage over the stronger HGB-only control

**Comment.** The combined policy does not establish a joint accuracy-and-damage advantage over HGB-only.

**Response.** We agree and retain this negative boundary throughout the paper. HGB+GbV_R minus HGB-only_R has an EM difference of +0.0556 percentage points with adjusted range [−0.1556, +0.3167], so the joint rule does not pass even though the Damage endpoint favors the combination. The revised contribution statement describes the finding as directional: HGB adds supported value over GbV-only under the declared rule, whereas the reciprocal GbV addition over the stronger HGB-only head is not established. We make no superiority, equivalence, non-inferiority, or interaction claim.

## 3. Increment beyond prior dual-answer benefit prediction

**Comment.** The additional insight beyond prior dual-answer benefit prediction should be clearer.

**Response.** Page 2 now states that two-answer selection itself is not new. The empirical contribution is a controlled signal-attribution design: candidate pairs, downstream fit/calibration recipe, eligibility, and replacement count are fixed, while EM improvement and harmful replacement reduction are evaluated jointly. This design reveals a comparison-dependent boundary that point accuracy alone hides. We retain prior systems as conceptual comparators and make no numerical superiority claim over their complete methods.

## 4. Effective training size and positive counts

**Comment.** Actual effective training sample size and positive counts are incomplete or inconsistent.

**Response.** Sections 3.3 and Appendix D now distinguish partition populations from numerical fit populations. Each current base head uses 2,572 eligible fitting traces: 2,015 negatives and 557 Recovery positives. Each disjoint Platt calibrator uses 630 eligible traces: 498 negatives and 132 positives. The larger 10,800/2,700 trace counts describe the fit/calibration partitions before eligibility filtering.

## 5. Fitted parameters

**Comment.** Fitted-parameter reporting is insufficient.

**Response.** Appendix D.3 now reports the learned scalar counts. Including the base intercept and the Platt slope/intercept, but excluding stored preprocessing statistics, ROA-FULL, ROA-NOGBV, HGB+GbV_R, HGB-only_R, and GbV-only_R contain 28, 26, 10, 8, and 8 learned scalars, respectively. The public `CURRENT_HEADS.json` file releases every preprocessing value, base coefficient/intercept, Platt parameter, iteration count, target count, and design hash.

## 6. Public reproducibility scope

**Comment.** Data and code availability is not sufficiently complete or uniform.

**Response.** The public repository is now fixed at commit `038d769e96d092a2eec3bbc5df9f45f3c2a17ff0`. In addition to the 18,000-row evaluation bundle and full 20,000-draw statistical reconstruction, it now releases a text-free 13,500-row development bundle with opaque group IDs, numerical inputs, eligibility, frozen fit/calibration roles, and binary EM outcomes. `scripts/reproduce_current_heads.py` performs all ten paper-head fits and exactly reproduces the accepted preprocessing, coefficients, calibrators, iterations, target counts, ranking metadata, and design hashes. `scripts/reproduce_all.py` runs this refit before rebuilding every reported point estimate and interval.

The revised manuscript uses one boundary consistently: the public release reproduces the current logistic heads and reported statistical layer from realized numeric inputs. It does not regenerate retrieval, candidate answers, neural scores, model weights, or historical upstream training, and it does not release benchmark text or original sample IDs.

## Revision integrity

No candidate, action, outcome, point estimate, interval, or scientific conclusion changed in R6. The revision changes interpretation, method disclosure, and the public reproduction package. The paper remains a bounded empirical study and continues to state that the current evidence does not establish cross-reader transfer or a joint advantage over HGB-only_R.
