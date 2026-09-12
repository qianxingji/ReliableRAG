# P0-3 reader-axis availability and provenance decision

2026-09-12. **CAS Q2 STATUS: NOT READY.**

Decision: **freeze a same-cohort Phi-3.5-mini-instruct reader-axis
replication, subject to an invented-only compatibility preflight.** This is a
reader robustness study of a fixed empirical procedure. It does not revive
ROA-FULL, create a novel method, or turn HGB_GBV_R into a cleared deployment
model.

## Read-only evidence

The client audit passed without loading a model, running a forward pass, fitting
a model, reading Gold, or decoding an answer. Its accepted external namespace is
`outputs/phi_reader_axis_availability_v2` under the client task root; manifest
SHA-256 is `c9324f6ef3b3daf212b4482f07b262429eb2e17006f451f4ac791c28034c0d5c`.
The V1 audit stopped before scientific output because it confused safetensors
physical bytes with tensor-payload bytes. That failure is preserved separately;
V2 parses data offsets and verifies their sum against the index.

The local official snapshot is
`microsoft/Phi-3.5-mini-instruct@2fe192450127e6a83f7441aef6e3ca586c338b77`.
It contains 20 files / 7,644,702,484 physical bytes. The two expected weight
shards contain 7,642,159,104 tensor bytes, exactly matching the safetensors
index; their physical overhead is 22,776 bytes. The official revision page also
identifies this revision, 7.64 GB tree, Phi3 architecture and MIT license:
[Microsoft Phi-3.5 snapshot](https://huggingface.co/microsoft/Phi-3.5-mini-instruct/tree/2fe192450127e6a83f7441aef6e3ca586c338b77).
The local GPU is an NVIDIA GeForce RTX 5060 Ti with 16,311 MiB. Availability is
established; actual generation compatibility is not.

The three ID-only opened sets are mutually disjoint: 14,100 historical IDs,
4,500 fixed-panel development IDs and the current 6,000-question Qwen cohort,
for a 24,600-ID union. Remaining source-frame counts are:

| Dataset | Source IDs | Historical | Fixed panel | Current cohort | Remaining |
|---|---:|---:|---:|---:|---:|
| HotpotQA | 7,405 | 3,800 | 1,500 | 2,000 | 105 |
| 2WikiMultiHopQA | 12,576 | 3,800 | 1,500 | 2,000 | 5,276 |
| MuSiQue | 19,938 | 600 | 1,500 | 2,000 | 15,838 |

Only 105 untouched HotpotQA IDs remain. A new balanced three-dataset sample of
useful size is therefore unavailable. Selecting only the large remaining
frames would change the dataset mixture while changing the reader, weakening
causal attribution and creating another discretionary sample. The current
6,000 IDs are already outcome-opened for Qwen but have never been generated or
scored with Phi. Reusing their fixed IDs and retrieval assets makes reader
family the independent replication axis and creates no new selection choice.

## Statistical feasibility

The audit re-read only accepted draw-level event differences, not labels or
answers. At 6,000 questions, a four-endpoint Bonferroni family has
`z=2.4977054744`. Using the completed Qwen bootstrap SDs as planning references,
the approximate 80% power minimum detectable differences are:

| Comparison | EM, pp | Damage rate, pp | EM with 1.5x SD | Damage with 1.5x SD |
|---|---:|---:|---:|---:|
| HGB_GBV_R − HGB_ONLY_R | 0.3005 | 0.1114 | 0.4507 | 0.1671 |
| HGB_GBV_R − GBV_ONLY_R | 0.2296 | 0.0747 | 0.3444 | 0.1120 |

These are normal approximations conditional on Qwen variance, not achieved Phi
power or promised effects. The study can meaningfully attempt to replicate the
Qwen fusion-versus-GbV result. It is underpowered for a fusion-versus-HGB EM
effect as small as the observed Qwen point estimate. That endpoint remains
primary because removing it after seeing Qwen would bias the research question.
An inconclusive result will be retained and will not trigger more IDs, seeds,
budgets or readers.

## Literature and claim boundary

The nearest work makes a reader-axis test scientifically necessary and further
narrows novelty. [Generate but Verify](https://aclanthology.org/2025.ijcnlp-long.56/)
already formalizes coupled answer generation and faithfulness assessment.
[TrustMargin](https://arxiv.org/abs/2606.08397) already treats completed-answer
choice as posterior arbitration and uses multiple likelihood margins across
three LLaMA scales. [SURE-RAG](https://arxiv.org/abs/2605.03534) already
aggregates verifier evidence for calibrated selective answering.
[Doctor-RAG](https://arxiv.org/abs/2604.00865) performs diagnosed local repair,
and [Pair-ID](https://arxiv.org/abs/2608.08944) reports reader-conditioned paired
evidence responses. Most directly,
[Preference Is Not Intervention](https://arxiv.org/abs/2608.17781) reports that
signed evidence effects vary materially by reader and that stable reader
preferences do not guarantee intervention transfer.

ReliableRAG therefore has no credible algorithm-novelty claim from logistic
HGB/GbV fusion. Its defensible route is a controlled empirical attribution
study: under a fixed 5% batch action budget, determine whether adding HGB to a
paired verifier reduces harmful switches while improving EM, and whether that
tradeoff repeats for two named reader families. The exact executable design is
frozen in `PHI_READER_REPLICATION_PROTOCOL_V1.md` before any Phi model call.

## Risks and task priority

- P0: implement and independently validate the invented-only Phi compatibility
  preflight, then execute the frozen development and 6,000-question reader-axis
  study exactly once.
- P0 rejection risk: HGB_GBV_R is ordinary supervised fusion; a second reader
  can strengthen empirical scope but cannot supply method novelty. Failure to
  reproduce the GbV-only result leaves only a reader-specific or negative study.
- P1: full Phi runtime packaging, model-card/pretraining-contamination limits,
  another-host reproduction and standalone deployment timing remain absent.
- P2: manuscript and target-journal work remain gated on the reader-axis result
  and the still-undecided institutional CAS year/category/target journal.

