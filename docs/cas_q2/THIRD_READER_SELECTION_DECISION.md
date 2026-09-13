# Prospective third-reader selection decision

Date: 2026-09-13
Research-decision route: GPT-6 Astra High independent reassessment
Decision: **select Mistral-7B-Instruct-v0.3 conditionally; do not execute it now**
**CAS Q2 STATUS: NOT READY.**

## Selection

The one prospective third reader is fixed at:

`mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`

It is preferred because its 7.248B-parameter scale, model family, tokenizer and
developer lineage add more capacity and implementation breadth than the
approximately 2.53B Granite alternative while remaining materially more
executable than the examined Granite 8B option. This is a prospective selection,
not evidence that Mistral performs better.

The comparison considered:

| Option | Decision |
|---|---|
| no third reader | scientifically defensible conservative scope, but less reader breadth |
| `ibm-granite/granite-3.3-2b-instruct@707f574c62054322f6b5b04b6d075f0a8f05e0f0` | valid low-resource alternative; about 2.53B parameters, not rejected as inherently too small |
| selected Mistral 7B | best balance of capacity breadth and conditional executability |
| `ibm-granite/granite-3.3-8b-instruct@51dd4bc2ade4059a6bd87649d68aa11e4fb2529b` | viable reserve only; heavier offload and output-boundary risks |

All three model candidates report Apache-2.0 licensing in their official model
cards. Different developer lineages do not establish independent pretraining
data or architectural orthogonality, and public training descriptions cannot
exclude benchmark contamination.

## Scope and limits

The third reader is a P1 reader-family/capacity extension on the same fixed
6,000-question cohort and retrieval assets. It is not an independent question
population, a new algorithm, a repair-method contribution, or a cure for the
failed ROA-FULL advancement rule. It cannot restore the Qwen comparison against
HGB_ONLY_R, and a significant result for one reader but not another is not by
itself evidence of reader interaction.

If eventually authorized, it must retain the same question/retriever grouping,
prompt content, Keep/Repair actions, five reader-matched supervised heads,
fit/calibration split, global `K=900`, four primary endpoints, 20,000 grouped
bootstrap draws and the two predeclared comparisons. The seven upstream feature
estimators remain fixed, so the scope is reader-specific heads under the existing
upstream feature system rather than full-system zero-shot transfer.

## Feasibility and execution gate

Mistral's indexed BF16 weights occupy about 13.50 GiB. The existing conservative
Mistral+BGE+KV lower-bound estimate is about 92.37% of the 16 GiB-class device
before activations, temporary logits and CUDA context. A static prediction that
offloading the last three layers reduces the estimate to about 84.71% is not an
actual preflight PASS.

No duration estimate is accepted before an invented-only throughput and memory
witness. The prospective workload includes at least 94,500 logical canonical
generations plus replay, likelihood, NLI and audits, and CPU offload may dominate
runtime.

No Mistral asset download, tokenizer run, model load, forward, fit, benchmark or
Gold read is authorized by this document. Before execution, one project-committed
protocol must prospectively bind the exact asset hashes, prompt/token limits,
placement/offload hooks, dynamic migration prohibition or accounting, joint
Mistral+BGE memory gate, replay positions, failure behavior and independent
validator. A failed gate remains visible and does not trigger result-driven model
replacement.

The current Phi P0-1 terminal failure keeps this P1 route closed pending a new
research-governance decision. The selection can be prepared and reviewed without
turning it into an experiment.

The independent Astra High reselection receipt is stored outside the repository
at `C:/Users/qianx/Documents/Codex/2026-09-10/reliablerag-research-project-lead-submission-ready/GPT6_ASTRA_HIGH_THIRD_READER_RESELECTION_2026-09-13.md`,
SHA-256
`7d760913231ab248f4ad759692f390d11e0719d66739189835f1082febbbf1ba`.
That review completed independently while the final Phi audit was still pending;
this committed decision applies its model choice and claim limits together with
the later terminal Phi gate above.

The external metadata, preweight feasibility and static placement records have
SHA-256 values `ed9ddbe3d195b8ad72e8798a5e71af06e68f5b8bf369f86758e33ea9d7a23152`,
`439e9c5b0aa3bc5c6758b179eda70baae3662fde52e11d732312ef6455c9f355`
and `7bd5c9e0eac00c0527a1e46c413a0a6f763dd883e1f7b0a483eb90de35d9e17b`.
They are metadata-only evidence and do not certify runtime feasibility.
