# Research Lead: empirical route and evidence limits, 2026-09-11

**CAS Q2 STATUS: NOT READY.**

Decision: **METHOD_NOVELTY_ROUTE_NOT_SUPPORTED; EMPIRICAL_REPLICATION_REQUIRES_DESIGN**.
No final model is cleared. Keep the original full-stack and minimal-fusion
advancement failures unchanged. A descriptive study is worth designing, but
renaming the same logistic model or relabeling opened outcomes as confirmation
would not supply a contribution.

## What the new audits establish

The cost audit at `a8d29b1` authenticated and reconciled the actual acquisition
receipts reused by every current paired policy. It read no numeric outcomes and
performed no new model inference. The precision protocol was committed at
`ae99ace` before implementation/execution at `93f90c4`. It resampled only opened
development questions; no scientific fit or fresh outcome was acquired.

The precision audit retained all five repetitions, 25 original test folds and
three retriever siblings. It ran 2,000 draws per repetition, independently
reallocated the fixed 5% budget in each fold, and passed 100 exact checks against
explicitly copied/sorted batches. Every original action and Net/Damage total
matched the sealed ledgers before resampling.

| Seed | FULL minus fusion EM point [conditional 95% range], pp | Fusion minus HGB-only EM point [range], pp | Fusion minus GbV-only EM point [range], pp |
|---|---:|---:|---:|
| 20260917 | 0.0815 [-0.0667, 0.2074] | 0.3926 [0.2000, 0.6074] | 0.4000 [0.2296, 0.5704] |
| 20260918 | 0.0444 [-0.0741, 0.2222] | 0.3556 [0.1556, 0.5556] | 0.3926 [0.2222, 0.5556] |
| 20260919 | 0.0074 [-0.1037, 0.1926] | 0.3778 [0.1852, 0.5704] | 0.3852 [0.2000, 0.5259] |
| 20260920 | 0.0519 [-0.0889, 0.1926] | 0.3407 [0.1333, 0.5333] | 0.3556 [0.2000, 0.5185] |
| 20260921 | 0.0667 [-0.0741, 0.2370] | 0.4074 [0.1926, 0.6000] | 0.4296 [0.2222, 0.5630] |

These are exploratory percentile ranges conditional on the existing OOF model
panel and dataset-by-fold composition. They omit training uncertainty and do not
establish multiplicity-adjusted superiority, equivalence, noninferiority or a
new single deployment model's performance. Repetitions overlap in questions and
training data; five favorable ranges are not five independent confirmations.

The FULL-versus-fusion differences remain unresolved at this scale. This is not
evidence of equivalence. Fusion's positive mixed-data Net differences are more
substantial, but its Damage difference versus supervised GbV includes zero in
every repetition's range (one upper endpoint equals zero). The existing 2Wiki
LODO floor failure remains in force. Neither result supports a general low-harm
or transport guarantee. Complete Damage results and all 10,000 draws are retained.

## Cost: switching happens after expensive acquisition

The saved canonical 13,500-trace acquisition includes:

| Component | Verified historical work |
|---|---:|
| Original retrieval | 13,500 logical retrievals; 43,164 document embedding rows; 9,000 query embedding rows |
| Original answer generation | 13,500 calls; 12,982,104 input and 68,603 output tokens |
| Repair-query generation | 13,500 calls; 13,265,691 input and 479,369 output tokens |
| Repair retrieval | 13,500 logical retrievals; 9,000 query embeddings |
| Repaired answer generation | 13,500 calls; 12,981,753 input and 70,573 output tokens |
| Shared historical base-score extraction | 27,000 answer embedding texts; 12,808 likelihood-cell requests, including 112 cache hits |
| GbV scoring | 32,174 NLI chunk/answer pairs; 6,404 forward batches across 3,202 eligible traces |

Original retrieval includes hybrid logical calls; do not silently equate a
logical hybrid call with one underlying retrieval component. Token totals are
native accounting, not FLOP estimates. Input prefix tokens are not multiplied
by autoregressive forward counts.

Measured historical stage durations were 818.96 s (retrieval build including
index work), 33,259.80 s (canonical runtime), 3,680.95 s (shared base-scoring
internal timer), and 2,201.30 s (GbV executor). Their boundaries differ. They are
not additive standalone current-policy latency measurements or predicted fresh
run times. Base execution retained an original diagnostic FAIL from prevented
CPU-discovery subprocesses, followed by a separate pre-action control
reconciliation; the original FAIL was not erased or relabeled.

HGB_GBV_R and ROA-FULL share the paired candidate generation, HGB likelihood/
answer-embedding inputs and GbV verifier. The reduced top-level model avoids
several other historical estimators in a possible implementation, but there is
no measured end-to-end speedup. GBV_ONLY_R requires no HGB score path in principle;
the joint evaluation still acquired that path to serve all policies. Distinguish
shared experimental acquisition from a separately timed deployment pipeline.
A 5% switch cap is not a 5% inference-cost budget.

## Focused prior-work assessment

These are our scope judgments from the cited primary sources, not a comprehensive
novelty certificate.

| Source | Relevant boundary | Consequence for the contribution |
|---|---|---|
| [Generate but Verify](https://aclanthology.org/2025.ijcnlp-long.56/) | Couples answer generation with faithfulness assessment for downstream use. | Faithfulness verification is prior work; our paired margin is an adaptation. EM recovery is a different supervision target. |
| [TrustMargin, section 3 and appendix C](https://arxiv.org/html/2606.08397v1) | Selects existing Direct/RAG candidates using question-only, question-plus-context and context-only likelihoods; discusses the cost of candidate generation and scoring. | Posterior arbitration, likelihood margins and sparse replacement are prior ideas. Our E0/E1 likelihood matrix cannot reproduce its three views or original candidate domain. |
| [Pair-ID, sections 2–3 and 6](https://arxiv.org/html/2608.08944v1) | Studies known failed traces under gold-support addition and verified nonsupport deletion, with matched shams and reader replication. It distinguishes offline response characterization from runtime control. | A paired-evidence narrative is insufficient novelty. Our oracle-free fixed repair pair and all-trace switching population differ, but that difference alone proves no methodological advance. |
| [Doctor-RAG](https://arxiv.org/abs/2604.00865) | Diagnoses failed agentic trajectories and repairs locally with prefix reuse. | Its failure-conditioned acquisition task is not an exact fixed-pair, all-trace baseline. A renamed adaptation must not be called a reproduction. |

The defensible prospective question is whether apparent gains from a complex
recovery stack survive supervision-matched single-signal and fusion controls,
and how the Net/Damage tradeoff changes with the evaluation population. The
current evidence answers this only for one opened cohort and one reader.
Ordinary logistic fusion is an empirical object here, not a new algorithm.

## Consequence for the next design

Do not spend fresh-confirmation compute to seek a small FULL-versus-fusion win.
No equivalence margin has scientific justification, and these conditional ranges
cannot supply one retrospectively. Do not choose a favorable seed or loosen the
LODO floor. The failed robustness-based advancement route stays failed.

A proposed empirical replication must define a different claim explicitly:
reproduce an attribution/tradeoff observation, regardless of which fixed method
wins, rather than establish a universally superior new model. It must retain
FULL, NOGBV, both single-signal controls, fusion, raw HGB/GbV and Keep; fix one
development fit/calibration partition for every supervised comparison; and report
every prespecified population, including adverse transport results.

Before any such run, the Research Lead must freeze a single-model recipe,
independent-question sample size, primary comparison/multiplicity scheme, and
an uncertainty analysis that respects the new batch. The current OOF precision
audit only constrains planning. It is not power for that as-yet unfitted model.
At least one independent replication axis must be justified by the claim rather
than automatically adding a larger model; reader dependence and a genuinely
unopened population are separate questions.

This is a route assessment, not an executable replication contract. The next
authorized engineering work remains read-only provenance/availability and
reproducibility preparation until that scientific design is complete.

## Remaining rejection risks and priorities

- P0: the contribution is not yet sufficient for a CAS Q2 submission; no accepted
  final candidate, frozen confirmation, new confirmatory evidence or submission
  package exists. Historical upstream fit-time receipts remain unrecovered.
- P0: exact journal title/ISSN, CAS year and category, and institutional recognition
  are not certified. The [official partition site](https://www.fenqubiao.com/)
  currently exposes login, not journal records, to this session. Do not substitute
  JCR or another ranking. A live publisher check also finds that Information
  Retrieval Journal is now [Discover Computing](https://link.springer.com/journal/10791/aims-and-scope);
  old-name rankings must not be transferred without checking the current ISSN.
- P1: justify independent replication, exact external-comparator adaptation,
  standalone cost measurement and a releasable artifact package. The two audits
  improve evidence discipline but do not by themselves establish novelty.
- P2: no feature/budget/seed search, architecture expansion, cosmetic renaming or
  manuscript drafting before a coherent claim and evidence plan are accepted.
