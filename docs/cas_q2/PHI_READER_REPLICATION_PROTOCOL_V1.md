# Frozen Phi reader-axis replication protocol v1

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

This protocol authorizes implementation and bounded execution only after each
preceding engineering/independent gate passes. It freezes a second-reader
replication of the empirical policy procedure. It does not authorize feature,
model-class, prompt, budget, seed or subgroup search, and it does not authorize
a new method name.

## 1. Estimand and fixed replication axis

The estimand is the paired change in normalized EM and Damage rate caused by a
5%-budget batch selector when the reader is Phi-3.5-mini-instruct, conditional
on the fixed benchmark-derived population, retrieval assets, repair procedure,
upstream scorers and reader-specific supervised fitting recipe below.

Use exactly the already selected 2,000 HotpotQA, 2,000 2WikiMultiHopQA and 2,000
MuSiQue IDs in `empirical_fresh_cohort_v1`, retaining all three BM25/dense/hybrid
siblings. There is no new sampling, replacement reserve or post-result
enlargement. These IDs are outcome-opened for Qwen and are not claimed as a new
question sample; their Phi answers, Phi scores, Phi actions and Phi outcomes do
not yet exist. The independent axis is reader family.

Use exactly `microsoft/Phi-3.5-mini-instruct` revision
`2fe192450127e6a83f7441aef6e3ca586c338b77`, its pinned tokenizer/chat template
and local official files audited in `P0_3_READER_AXIS_AVAILABILITY.md`. Do not
download a newer revision or substitute another Phi/Qwen model after a failure.

## 2. Development fitting and fixed components

Use exactly the 4,500 existing fixed-panel development question groups and the
same role assignment: 3,600 fit and 900 disjoint calibration questions, with all
three retrievers together. Build Phi-specific candidate traces and labels for
those IDs. Require both Recovery classes in the eligible fit and calibration
sets; otherwise stop without redrawing or changing the split.

Fit exactly the same five reader-specific heads and ten scientific fit calls as
the Qwen empirical panel: ROA-FULL, ROA-NOGBV, HGB_GBV_R, HGB_ONLY_R and
GBV_ONLY_R. Preserve each feature index, missing flag, retriever indicator,
fit-only transform, L2 logistic recipe and disjoint Platt calibration from
`EMPIRICAL_REPLICATION_PROTOCOL_V1.md`. Do not refit on fit+cal, tune a
regularizer, add reader identity, average heads or search thresholds.

Keep the seven authenticated historical upstream score estimators byte-fixed.
They are transported components with documented reconstructed training
provenance; do not present them as Phi-trained or baseline-independent. Compute
their required likelihood features with the Phi reader. Keep BGE revision
`a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` and DeBERTa NLI revision
`5a4338ab2151dc8db04ad53b42b6153382bf4f99` fixed. The paired GbV adaptation,
normalization, eligibility and failure rules are unchanged.

Primary fairness uses the five newly fitted Phi heads plus raw HGB, raw GbV and
Keep on the same Phi pairs. Apply the Qwen five-head panel and sealed V2 bundle
to Phi features only as a visibly secondary parameter-transport diagnostic.
They receive no primary interval, cannot replace a reader-matched control and
cannot be selected after outcomes.

## 3. Acquisition, prompts and action sealing

Reuse the accepted C1 candidate pools and C2 original retrieval arrays for the
same 6,000 test IDs. For development, reuse the authenticated historical source,
pool and original-retrieval assets bound to the 4,500 fixed-panel IDs. No source
answer, support annotation, decomposition or test metric enters retrieval,
generation, scoring or action selection.

Keep the existing answer and repair prompt text, 16,000-character context
budget, greedy decoding, 48 answer-token cap and 64 repair-query-token cap.
Render those prompts with the pinned Phi chat template. Generate all three
reader-dependent calls per trace: original answer, repair query and repaired
answer. Never reuse the Qwen repair query or either Qwen answer as a Phi input.
Retrieval pools/configuration remain fixed; the repaired retrieval result may
change only because the Phi repair query changes.

The development batch is for fitting only and produces no test claim. After its
five bundles pass independent coefficient, transform and prediction replay,
score all 18,000 fixed test traces. Reconcile a single common eligibility mask.
For every policy, set `K=round(0.05*18000)=900`, rank only eligible rows by the
fixed score and canonical `(dataset,retriever,sample_id)` tie break, and seal all
actions before any Phi test outcome mapping. No positive-score threshold,
dataset quota, reader-specific budget or per-method deletion is allowed.

## 4. Failure and execution boundaries

Before benchmark execution, one invented-only compatibility preflight must test
the exact local revision, tokenizer template, greedy generation, teacher-forced
likelihood extraction, maximum configured prompt boundary, durable journal and
GPU device recording. It may call Phi only on invented text. The independent
validator must reconstruct token inputs and saved logits without importing the
executor. A failed preflight is preserved and corrected only through a new
hash-bound protocol amendment; benchmark data remain closed.

Benchmark execution uses single-use versioned namespaces and resumable durable
journals. A process interruption may resume the same planned calls after exact
receipt validation; it cannot restart completed calls to seek different text.
Empty/equal answers and deterministic score failures remain forced Keep in
`N_all`. Any unexpected model, tokenizer, schema or asymmetric score error stops
the stage. Do not drop a row, change a prompt, increase a token cap or substitute
a model. Preserve every failed namespace and stderr.

The maximum authorized scope is 31,500 question-retriever traces across
development and test, hence 94,500 logical Phi generations: 40,500 on development
and 54,000 on test. It authorizes ten reader-specific scientific fits. Likelihood
work is at most four Phi teacher-forced cells per native eligible pair; GbV work
is at most two NLI branches per native eligible pair. There is no second seed,
reader or budget. Record actual tokens, forwards, peak CUDA allocation, stage
wall time, cache state and disk use. Qwen's measured 18,000-trace generation time
of 45,216.9 seconds scales to about 22.0 hours at 31,500 traces only as a scheduling
reference; it is not a Phi runtime promise.

## 5. Outcome boundary and primary analysis

No Phi test Gold/reference reader may run until the complete Phi test action
ledger, all upstream/model/config/environment hashes and an independent prelabel
validation are sealed. The mapping process may materialize only the 6,000 fixed
labels and normalized EM/token-F1 values. It cannot modify pairs, scores,
eligibility or actions. A separate validator must reread the same selected
references and independently recompute every metric. Raw references are never
written.

Primary ordered comparisons are:

1. HGB_GBV_R minus HGB_ONLY_R.
2. HGB_GBV_R minus GBV_ONLY_R.

Each has EM difference and Damage-rate difference in percentage points, for four
primary endpoints. Positive EM and negative Damage are favorable. Use 20,000
NumPy `default_rng(20260930)` dataset-stratified paired question-cluster draws,
carrying three retriever siblings and all policies together. Recompute the
top-`K` allocation on every resampled whole batch using the accepted weighted
copy kernel and an independent explicit-copy audit. Models and pools stay fixed.

For each endpoint, report the point estimate, unadjusted 95% percentile range
and Bonferroni-adjusted linear-percentile range at quantiles
`0.05/(2*4)` and `1-0.05/(2*4)`. The four adjusted endpoints form one family.
Also report Recovery, Damage, Neutral, Net, all-policy EM/F1, fixed-action
sensitivity on the same draws, dataset/retriever cells and action counts as
secondary outputs. ROA-FULL minus HGB_GBV_R is a secondary complexity audit with
an unadjusted 95% range and no superiority claim. Cross-reader difference of
effects and Qwen-panel parameter transport are descriptive diagnostics only.

Directional claims require the relevant adjusted range to exclude zero in the
specified direction. A joint comparison passes only when its EM lower bound is
above zero and its Damage upper bound is below zero. Failure to reject is not
equivalence. Do not select a fixed-action result, subgroup or alternative
interval because it is favorable.

## 6. Claim and stopping rules

- If fusion versus GBV_ONLY_R passes jointly for Phi, it replicates the already
  passed Qwen result across the two named readers. The allowed claim remains
  conditional on these datasets, retrievers, repair process and 5% batch budget.
- Fusion versus HGB_ONLY_R can be called positive for Phi only if its two adjusted
  endpoints pass. Because Qwen did not pass this joint comparison, no two-reader
  superiority-over-both claim is possible from this study alone.
- If the GbV-only comparison is null, mixed or reversed, report reader dependence
  and withdraw the cross-reader replication claim. Do not add data or a reader.
- ROA-FULL cannot be reinstated by a favorable secondary result. HGB_GBV_R remains
  a simple empirical policy, not a novel algorithm or universally optimal model.

Stop after the one frozen analysis and independent validation, irrespective of
significance. Preserve all signs, seeds, failures and raw sealed files. An Astra
xhigh final fairness/Claim audit is required before manuscript drafting. Even a
positive replication does not by itself make the project CAS Q2 Submission
Ready; contribution framing, full limitations, release replay, journal identity
and institutional CAS recognition remain separate gates.

