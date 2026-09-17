# Mistral test execution and analysis protocol

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `FROZEN_ACTION_OUTCOME_ANALYSIS_TEST_LABEL_BLIND_CHAIN_IMPLEMENTED_PRELABEL_PENDING_EXECUTION`.
This document fixes the one-time Mistral test route prospectively. The pure
analysis kernel, label-blind action seal, numeric-only outcome executor, formal
20,000-draw analysis executor and their independent audit paths are implemented
on invented rows. The test `a0_query`, repair, `a1_likelihood` and witness replay
executors plus their no-model validators are also implemented. The first neural
scoring stage, BGE answer semantics, its tokenizer-only validator, the fixed HGB
transfer, paired GbV, common prelabel freeze and their independent audits are
now implemented but have not run. This document neither
opens test outcomes nor authorizes test execution.
Formal test
acquisition may start only after the complete development chain, selected models
and fixed reference models pass their producer, independent-validator and client
gates.

## Authenticated label-blind population

The test population is exactly 6,000 question groups and 18,000 retriever
traces: 2,000 questions from each of HotpotQA, 2WikiMultihopQA and MuSiQue, with
one BM25, dense and hybrid sibling per question. No question is resampled,
replaced or excluded before acquisition. The frozen label-blind sources are:

- `outputs/cas_q2/empirical_runtime_preparation_v1/TRACE_MANIFEST_PRIVATE.jsonl`,
  7,341,125 bytes, SHA-256
  `87d5aff0bc77da76624b541326c523d41b00fa6c84ecefd4d6a050de66b25a29`;
- its preparation manifest, SHA-256
  `7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258`;
- `outputs/cas_q2/empirical_candidate_pool_v2/SHA256_MANIFEST.json`, SHA-256
  `4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98`;
- the accepted 31,500-row Mistral input freeze, whose private ledger SHA-256 is
  `538970511fe517a21ef7baee4dc5eb216ce748b2c2222b3960c356a53a12f8ac`.

Every row must have `cohort=test` and `role=test`. Test identities and prompts
are permitted for executor construction because they are label blind. Test
answers, reference strings, EM/F1 values and all outcome-derived counts remain
closed until the action ledger is independently accepted.

## Mandatory predecessor gate

Before test launch, one immutable execution freeze must bind:

1. accepted development `a0_query`, repair, `a1_likelihood` and witness replay;
2. accepted development answer semantics, transferred HGB, paired GbV, common
   prelabel freeze and numeric outcomes;
3. accepted development tuning with exactly 84 producer fits and 84 independent
   audit refits;
4. the three selected primary base/Platt models and the three fixed
   `C=1.0, class_weight=None` reference base/Platt models, including transforms,
   coefficients, eligible fit/cal identities and hashes;
5. committed test executors, independent validators, invented fixtures, source
   hashes, package/runtime identity, output namespaces and resource ceilings.

Any missing, rejected or mutated predecessor blocks the test. Development
selection may choose only from the already frozen eight-candidate grid. It may
not change reader, prompt, feature, split, seed, action budget or endpoint
family. The fixed recipe remains descriptive and cannot replace the selected
primary recipe.

## Component-sequential acquisition

The test runtime repeats the accepted development semantics on the 18,000 test
traces, with one neural component resident at a time:

1. **`a0_query`**: Mistral alone; 18,000 `a0` generations plus 18,000 repair
   query generations, for 36,000 generation operations.
2. **`repair`**: Mistral absent and BGE alone; exactly 18,000 same-retriever
   depth-50 repairs, with rank 5 replaced.
3. **`a1_likelihood`**: Mistral alone; 18,000 `a1` generations plus 72,000
   teacher-forced L00/L01/L10/L11 likelihood operations.
4. **`witness_replay`**: after no-model validation, replay the first and last
   canonical test trace in each of the nine dataset by retriever cells. Save 126
   complete FP32 first-token vocabulary vectors: three generation and four
   likelihood witnesses at each of 18 positions.

Canonical acquisition totals are 54,000 generations, 72,000 likelihood calls,
18,000 repairs and 126,000 model operations before witness replay. Batch size is
one. The exact Mistral revision, NF4/double-quant/BF16 configuration, prompts,
token limits, parser, retrieval settings, likelihood semantics and deterministic
environment are identical to accepted development. There is no fallback reader,
prompt, quantization or retry seed. Durable intent/result journaling, exact-hash
resume and failure preservation follow the accepted development contract.

The implemented test `a0_query` executor binds the authenticated 18,000-row
test trace, candidate-pool and input-freeze manifests, reconstructs the frozen
question and ordered five-document evidence directly from label-blind sources,
and uses the same GPU mutex as development acquisition. Its independent
validator imports no neural reader and reconstructs all 36,000 prompts and
receipts with the tokenizer only. The formal namespace has not been created and
this implementation statement is not an execution result.

The implemented test repair executor requires accepted test `a0_query`, loads
only the pinned BGE model, reuses sealed document vectors and BM25 structures,
and performs exactly 18,000 same-retriever depth-50 repairs. BM25 rows make no
dense query forward; dense and hybrid rows make one each, for 12,000 forwards.
It preserves ranks 1--4 and replaces only rank 5. The no-model validator replays
all rankings from the saved 768-dimensional query vectors. The formal repair
namespace has not been created.

The implemented test `a1_likelihood` executor requires independently accepted
test `a0_query` and repair stages. It reconstructs repaired evidence from the
sealed inserted-document identity, loads only the pinned Mistral reader, and
performs exactly 18,000 `a1` generations plus 72,000 teacher-forced
`L00/L01/L10/L11` likelihood operations. BGE, NLI, Gold, fitting and tuning are
forbidden. Its independent validator loads only the pinned tokenizer and
reconstructs all 90,000 prompts, target token sequences, journal records and
summary arithmetic. The formal namespace has not been created.

The implemented witness executor independently requires accepted `a0_query`,
repair and `a1_likelihood` stages. It chooses the first and last canonical test
position in each of the nine dataset-by-retriever cells, exactly 18 positions,
and replays `a0`, repair query, `a1` and the four likelihood cells. It requires
receipt equality and saves 126 raw 32,768-element FP32 first-token vectors
(16,515,072 bytes). The independent tokenizer-only validator recomputes the
selected token and float64 log-softmax from every vector. The formal witness
namespace has not been created.

## Label-blind scoring and action seal

After accepted acquisition and replay, execute and independently validate these
stages in order while test outcomes remain closed:

1. BGE answer semantics for all 36,000 answers;
2. the frozen transferred HGB estimator without refitting;
3. paired GbV using the pinned NLI model;
4. one common eligibility mask for `HGB_GBV_R`, `HGB_ONLY_R` and
   `GBV_ONLY_R`;
5. primary selected-model probabilities and descriptive fixed-recipe
   probabilities for all three methods;
6. global action allocation and an immutable action ledger.

The answer-semantics producer and independent validator are implemented. The
fixed workload is 2,250 document-mode BGE batches of 16 answers, yielding 36,000
normalized 768-dimensional vectors and 110,592,000 explicit little-endian FP32
bytes. The validator loads only the pinned tokenizer and independently checks
all batch inputs, vector files, norms and 18,000 pairwise dot products. The
formal namespace has not been created.

The fixed-HGB producer and independent validator are also implemented. They
reconstruct the historical 48-feature state-symmetric record for all eligible
test pairs and apply the pinned 639,652-byte HGB artifact without refitting. The
validator rebuilds every feature tree through the separate independent formulas
and recomputes the positive/negative probability symmetry directly. Neural
loads/forwards, Gold, outcomes, fitting and tuning remain forbidden. Formal HGB
output does not exist.

The paired-GbV producer and independent validator are implemented as well. The
producer runs the pinned DeBERTa NLI model in FP32 and batch size 8, always scores
`a0/E0` before `a1/E1`, and saves every two-logit forward as explicit
little-endian FP32 bytes. The validator loads only the tokenizer and independently
reconstructs all premise/hypothesis chunks, token fields, float64 softmax values,
branch maxima and margins. Only the two frozen deterministic context-window
errors can force Keep; all other failures fail closed. Formal GbV output does
not exist.

The common test prelabel producer and independent validator are implemented.
They require accepted HGB and GbV validations, reconstruct all 18,000 test
identities, and emit the same eligibility mask and ordered feature vectors for
`HGB_GBV_R`, `HGB_ONLY_R` and `GBV_ONLY_R`. The freeze recursively binds the
test trace, pool, retrieval, native-runtime tests, input freeze, both complete
signal stages and their acceptance records. It loads no model, performs no fit
or tuning, and forbids project Gold, test Gold and test outcomes. The validator
independently reconstructs every row without importing the producer. Formal
prelabel output does not exist.

For each recipe and method, sort eligible rows by descending calibrated recovery
probability and then ascending `(dataset, retriever, sample_id)`. Select exactly
`min(900, N_eligible)` rows. Every ineligible row is forced Keep, remains in the
18,000-row denominator and retains its reason. `K=900` is 5% of all traces and
is not selected from test performance. The action seal records all scores,
actions, overlap categories, source/model hashes and zero test-outcome access.

Only after the primary and fixed-reference action ledgers independently pass may
the numeric test-outcome stage read authenticated references. It emits only
`a0_em`, `a1_em`, `a0_f1` and `a1_f1` bound to the sealed identities and answer
receipts. Raw reference strings are never copied into result artifacts.

## Primary estimands and multiplicity family

The primary recipe is the development-selected recipe. Let `z_pi` be the sealed
action for policy `p`, and let `y0_i,y1_i` be normalized EM. For all 18,000 rows:

- `EM_p = 100/N sum[y0_i + z_pi(y1_i-y0_i)]`;
- `Damage_p = 100/N sum[z_pi y0_i(1-y1_i)]`;
- `Recovery_p = 100/N sum[z_pi(1-y0_i)y1_i]`;
- `Net_p = Recovery_p - Damage_p`.

The four confirmatory endpoints are fixed:

- `HGB_GBV_R - HGB_ONLY_R`: EM difference and Damage-rate difference;
- `HGB_GBV_R - GBV_ONLY_R`: EM difference and Damage-rate difference.

Positive EM and negative Damage favor fusion. A comparison passes the joint
gate only when its adjusted EM lower bound is strictly above zero and its
adjusted Damage upper bound is strictly below zero. A bound equal to zero fails.
The two comparisons remain separate; success for one cannot rescue the other.

## Frozen bootstrap and secondary reporting

Use NumPy `default_rng(20260930)` for exactly 20,000 draws. Within each dataset,
sample its 2,000 question groups with replacement; all three retriever siblings
and all policies receive the same multiplicity. Every draw therefore contains
6,000 groups and 18,000 rows. Models, transforms, scores, candidate pairs and
retrieval outputs remain fixed. Reallocate global top-K on each draw from the
frozen score/canonical order, with K remaining 900.

Use NumPy linear quantiles `[0.00625, 0.99375]`, corresponding to Bonferroni
0.05/(2 x 4), for the four primary endpoints. Also report unadjusted
`[0.025, 0.975]` ranges as secondary. A separate explicit-copy validator must
reconstruct every stored question multiplicity and top-K allocation without
importing the weighted allocation kernel.

Mandatory descriptive outputs are complete-population Recovery, Damage,
Neutral, Net, EM and token F1; eligibility and class counts; selected parameters;
and action-overlap decompositions for fusion versus each comparator overall and
in all nine dataset by retriever cells. The fixed-C sensitivity uses the same
draws but stays outside the confirmatory family. Fixed-action intervals are a
secondary sensitivity. No budget curve, favorable cell selection, seed panel,
reader interaction claim or post-test subgroup is permitted.

## Failure and interpretation lock

A resource failure, invalid row, source mutation, nonfinite score, incomplete
common mask, independent-validator rejection or unexpected outcome access fails
closed and remains recorded. It is not converted into an exclusion. Negative,
mixed or inconclusive results are retained. No test-driven parameter, K, prompt,
reader, seed, feature or eligibility change is allowed. Any later design change
is explicitly exploratory and requires a genuinely uncontaminated evaluation.

This test uses the same question identities whose Qwen results informed the
project, so it estimates a different reader/deployment condition on a known
benchmark cohort rather than an independent new-question confirmation.

## Stage accounting

- P0: this prospective contract is frozen; development acquisition and all
  ordered acceptances remain incomplete.
- P1: implement test scoring without opening outcomes, then execute the full
  frozen chain once after the complete
  development gate passes.
- P2: update the manuscript, supplement and public numeric reproduction package
  only from independently accepted results.

Main rejection risks are an uncertain fusion increment over `HGB_ONLY_R`, rare
Damage, one repair operator, known question identities, transferred HGB
provenance and the cost of end-to-end public neural reproduction.
