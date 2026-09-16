# Current task: reader extension design and HGB-only contribution diagnosis

**CAS Q3 STATUS: NOT READY.**

## Latest research steering (2026-09-16)

The user now requests an additional reader and identifies the weak contribution
of the fusion over the stronger HGB-only control. This reopens reader research
design and bounded feasibility preparation, superseding the previous Qwen-only
editorial priority. Read
[the research decision](READER_AND_HGB_INCREMENT_RESEARCH_DECISION_2026-09-16.md).
Formal neural execution still needs a prospective executable protocol; the old
Mistral STOP and all Phi FAIL records remain preserved, not waived.

The user also authorizes tuning if results are unsatisfactory. The
[development tuning policy](READER_DEVELOPMENT_TUNING_POLICY_2026-09-16.md)
specifies eight logistic-head configurations per main method, three shared
question-group folds within the 3,600-question fit partition, and a separate
900-question calibration partition. The bounded search costs 78 planned fits;
six additional fixed-reference fits make the formal producer total 84. None has
run on project data. Fusion, HGB-only and
GbV-only receive identical search budgets. Final configuration selection and
the primary comparison family must be fixed before new reader test results.
Disappointing test results remain evidence, not tuning targets.

The reusable development-only tuner is now implemented in
`src/arbitration/reader_development_tuning.py`. Its interface accepts only
`fit` and `cal` roles, uses the frozen eight-candidate grid and deterministic
three-fold dataset-stratified question grouping, and emits no test prediction.
Four synthetic contract tests pass. No project data were fit and no Mistral
model was loaded; implementation readiness is not experiment completion.

The bounded NF4 runtime check is also complete. A new isolated overlay supplies
official-digest-matched Accelerate 1.8.1 and bitsandbytes 0.50.2 while leaving
the accepted neural environment unchanged. A producer and independent validator
execute the same deterministic BF16/NF4 CUDA witness on the RTX 5060 Ti and
match its output SHA-256; 37 independent checks pass. Read
`MISTRAL_RESOURCE_AND_RUNTIME_PREFLIGHT_DECISION_2026-09-17.md`. This is a
kernel-only partial PASS.

The exact Mistral revision has now also been acquired. Fourteen selected files
totaling 14,499,392,853 bytes pass an independent 1,295-check validation. The
three sharded BF16 weight files contain 291 indexed tensors and 7,248,023,552
parameters; the duplicate consolidated serialization was prospectively excluded.
The initial no-payload HTTP attempt is preserved and the Xet retry completed.
Read `MISTRAL_ASSET_ACQUISITION_DECISION_2026-09-17.md`. No model was loaded;
whole-model memory, semantic model-output, replay and workload contracts remain
open.

The exact tokenizer gate is now independently accepted. The isolated overlay
adds official-hash-matched SentencePiece 0.2.1 and protobuf 7.36.1. Explicit
fast, slow and default routes agree on three invented fixtures; the fast route,
native chat template, special-token handling, left padding, 8,192-token guards
and answer/query caps are frozen. An independent validator passes 102 checks,
including a 36,076-token invented boundary case. Three earlier dependency
failures remain in the external attempt log. Read
`MISTRAL_TOKENIZER_PREFLIGHT_DECISION_2026-09-17.md`. The stage used zero model
loads, neural forwards, project rows, fits or Gold. Whole-model NF4 load and
invented-output validation are the next gate; no scientific reader experiment
has begun.

The one allowed whole-model gate is now complete. All 224 expected projections
loaded as NF4/double-quant/BF16 on CUDA 0 with no offload. The answer fixture
returned `Paris`, the repair fixture produced both required lines, and two
teacher-forced likelihood forwards repeated exactly. Peak CUDA reserved memory
was 7,392,460,800 bytes and the run took 30.29 seconds. The 1,814,658-byte
full-vocabulary witness passed 95 independent no-model checks. Read
`MISTRAL_WHOLE_MODEL_PREFLIGHT_ACCEPTANCE_2026-09-17.md`. This remains
invented-input execution only: full input binding, longest-shape resource,
production adapter, replay/storage and analysis gates are still open, and no
scientific reader experiment has begun.

The value-blind input freeze is now prospectively committed in
`MISTRAL_READER_INPUT_FREEZE_PROTOCOL_2026-09-17.md`. Its producer directly
binds the accepted Qwen development/test traces, questions, original Top-5
evidence and role ledger; it explicitly has no Phi artifact predecessor. It is
limited to 31,500 ledger rows / 63,000 tokenizer calls, with zero model, answer,
outcome or Gold access. The independent validator reconstructs every row without
importing producer/common code. Four static contract tests pass; the unique
input-freeze namespace has not yet been created at this freeze point.

The first direct-script launch then failed before import/main with
`ModuleNotFoundError: No module named 'scripts'` because `PYTHONPATH` contained
only the overlay. It created no namespace and accessed no tokenizer, project
row, model or Gold. The failure is preserved externally. The committed
`MISTRAL_READER_INPUT_FREEZE_LAUNCH_AMENDMENT_2026-09-17.md` authorizes exactly
one module-mode launch with the repository root added to `PYTHONPATH`; scientific
code and thresholds are unchanged.

The corrected producer and independent reconstruction now both pass. They bind
31,500 development/test rows and independently reproduce all 63,000 prompt
tokenizations from the direct accepted Qwen label-free source chain. The maximum
fixed prompt is a 3,675-token development 2Wiki dense repair-query prompt, with
4,517 tokens of headroom; no context was truncated and every access counter for
model, answer, fit and Gold remains zero. Read
`MISTRAL_READER_INPUT_FREEZE_ACCEPTANCE_2026-09-17.md`. The next gate is an
invented longest-observed-shape resource preflight and production-adapter/replay
validation; formal development generation has not started.

The one-load longest-shape resource protocol is now committed in
`MISTRAL_LONGEST_SHAPE_PREFLIGHT_PROTOCOL_2026-09-17.md`. It uses a fully
invented `[BOS, INST, repeated token 1000, END_INST]` sequence at exactly 3,675
tokens and forces 64 greedy decode steps solely to bound memory. It retains the
same NF4/BF16/eager/CUDA-only model contract and saves full FP32 step scores for
a no-model validator. Two static contract tests pass; this resource run has not
yet executed at the prospective-freeze point.

The longest-shape gate has now passed exactly once. A 3,675-token invented
prompt completed 64 decode steps in 33.89 seconds; peak CUDA reserved memory was
12,561,940,480 bytes, and all 64 × 32,768 saved FP32 score rows independently
reconstruct their greedy tokens. Read
`MISTRAL_LONGEST_SHAPE_PREFLIGHT_ACCEPTANCE_2026-09-17.md`. Because only about
3.06 GiB remained free at peak, Mistral must be the sole GPU component and must
be unloaded before BGE/NLI. Production adapter, journal/resume, compact replay,
component-sequential scoring and the formal development run remain open.

The production adapter and recovery design is now prospectively frozen in
`MISTRAL_PRODUCTION_ADAPTER_PROTOCOL_2026-09-17.md`. The implementation at
`src/arbitration/mistral_reader_runtime.py` fixes CPU-side 8,192-token admission,
NF4/double-quant/BF16/eager CUDA-only loading, exact parsers, target-preserving
likelihood truncation, explicit unload, fsync call journals and value-blind
18-position full-vocabulary witnesses. Four new unit tests plus six accepted
input/resource tests pass under unittest. Two attempted pytest launches stopped
before test collection because those Python environments do not include pytest;
they are engineering launcher records, not scientific failures. The next P0
gate is one invented-only exact-model adapter execution and an independent
no-model witness validator. Formal 13,500-trace development generation, Gold
access and scientific fitting have not started.

The first invented adapter launch failed before model construction at
`torch.cuda.reset_peak_memory_stats(0)`: this Windows/PyTorch process had not
initialized the concrete integer CUDA device. Its namespace and external
start/failure log are preserved, with zero project rows, model calls, Gold and
fits. The committed V2 amendment adds only
`torch.cuda.get_device_properties(0)` plus the accepted GPU identity check
before the reset. V2 must use a fresh namespace/log and still precedes any
formal development execution. Read
`MISTRAL_PRODUCTION_ADAPTER_PREFLIGHT_V1_FAILURE_AND_V2_AMENDMENT_2026-09-17.md`.

V2 then completed one invented model load, 3 generations, 4 likelihoods and 39
forwards, but its independent validator correctly failed at the first prompt
identity. The saved generation IDs begin `[1, 1, 3, ...]` instead of the frozen
`[1, 3, ...]`: generation had applied tokenizer special tokens to a native chat
template that already contained BOS. V2 is rejected and preserved despite its
plausible invented answers. The committed V3 correction sets only
`add_special_tokens=False` for generation CPU tokenization; likelihood already
used that rule. Seventeen focused/static tests now pass. V3 still requires a
fresh exact-model run and unchanged independent validation before development.
Read `MISTRAL_PRODUCTION_ADAPTER_PREFLIGHT_V2_VALIDATION_FAILURE_AND_V3_AMENDMENT_2026-09-17.md`.

V3 now passes. It performed one exact NF4 model load/unload, three invented
generations, four answer-token likelihood calls and 51 forwards. The unchanged
independent validator passes 105 checks, reconstructs the single-BOS prompts,
binds all seven journal transactions and recomputes seven full-vocabulary
first-token softmax values without loading a model. Peak CUDA reserved memory
was 7,419,723,776 bytes and post-close allocation was 33,555,456 bytes. Read
`MISTRAL_PRODUCTION_ADAPTER_PREFLIGHT_ACCEPTANCE_2026-09-17.md`. This closes the
invented adapter gate only. The next P0 work is the formal component-sequential
development executor/validator; no 13,500-trace Mistral acquisition, Gold read
or scientific fit has begun.

The formal development acquisition is now prospectively frozen in
`MISTRAL_DEVELOPMENT_ACQUISITION_PROTOCOL_2026-09-17.md`: 27,000 `a0`/query
generation operations, 13,500 separate repair operations, then 13,500 `a1`
generations plus 54,000 likelihood calls, with Mistral and BGE never resident
together. A distinct fixed 18-position replay will save 126 compact
full-vocabulary first-token witnesses. The no-model common implementation now
passes four additional durable-recovery and compaction tests (21 focused tests
total). The stage executor and independent validator remain to be implemented
and accepted before any formal call is allowed.

The formal `a0_query` executor and full-source independent validator are now
implemented. The executor pins the accepted Qwen runtime/pool/retrieval
manifests, Mistral input freeze and all 14 model assets; it produces fsynced
compact receipts for exactly 27,000 operations and supports exact-hash resume.
The validator imports neither the producer nor adapter, loads no model, and
reconstructs every question/evidence prompt, token sequence, parser result,
journal hash and frozen input identity from the original sources. Three new
stage tests and all prior focused tests passed (24 total) before the formal run
started. The run remains development-only with zero Gold, fit and test access.

The formal `a0_query` stage has now started from committed source `cd80cad` in
the new `mistral_development_acquisition_v1` namespace. It passed input/model
asset authentication, loaded the exact NF4 reader and is writing two fsynced
operations per trace. Early observed throughput is about 10 traces per 30
seconds, implying roughly 11--12 hours for this stage if sustained. No second
instance or concurrent BGE stage is permitted. The repair-stage executor and
its independent saved-vector reconstruction validator are now implemented and
pass six focused tests, but they remain blocked on `a0_query` completion and
independent acceptance. Before repair execution, a prospective input-graph
amendment now requires full member-level freezing of the historical
runtime/pool/retrieval artifacts, the Mistral input freeze, accepted `a0_query`,
the BGE preflight and its six exact model assets. The independent validator
reconstructs that graph and the producer rehashes every member at finalization.
This closes a manifest-only time-of-check gap without changing any scientific
operation. The `a1_likelihood` executor and its independent tokenizer-only
validator are also implemented. They reconstruct the dynamic E1, the `a1`
prompt and all four answer-token teacher-forcing cells from prior sealed inputs.
A prospective A1 input-graph amendment now requires all 220 historical payload
members and three manifests, every current predecessor-stage member, both
independent predecessor acceptances, the root A0 executable freeze, all 15
Mistral asset paths and every direct control file. The producer rehashes the
complete set at finalization and the independent validator requires exact path
equality. Six focused A1 tests and the complete 156-test Mistral suite pass.
This stage remains blocked on repair acceptance. The final 18-position witness-replay producer and
independent tokenizer-only validator are also implemented. They require all
three independently accepted canonical stages, reproduce the exact canonical
receipts, save 126 complete 32,768-way FP32 first-token vectors (16,515,072 raw
bytes), and independently recompute the selected-token log-softmax. Four new
tests and the complete 36-test focused suite pass. Witness replay is blocked on
`a1_likelihood` acceptance. No Gold, fit, test, a1, likelihood or NLI work has run.

The subsequent development scoring/tuning order is now frozen before any such
work in `MISTRAL_DEVELOPMENT_SCORING_AND_TUNING_PROTOCOL_2026-09-17.md`: BGE
answer semantics, fixed transferred HGB, paired GbV, common prelabel freeze,
development-only outcomes, then the equal 78-fit search plus six non-search
fixed-reference fits. The selected grid winner is the primary Mistral recipe;
the original `C=1` recipe is a secondary sensitivity. Test inputs and outcomes
remain closed until parameters, allocation and the four-endpoint family are
sealed.

The first post-acquisition scoring stage is now implemented but has not run.
`run_mistral_development_answer_semantics.py` fixes canonical dataset order and
1,689 batches, saves all 27,000 normalized BGE vectors as raw float32 bytes, and
binds each of the 13,500 answer-pair dot products to the accepted acquisition
chain. Its separate tokenizer-only validator reconstructs every batch input,
checks every vector file and recomputes every dot product without loading a
model. A generic append-only scoring journal and 48 Mistral-focused tests now
pass. This stage remains blocked on independent witness-replay acceptance; BGE
has not been loaded for it, and no HGB/GbV score, Gold value, fit or test result
has been produced. Development tuning remains limited to the already frozen
eight-candidate grid. No search expansion or test-result tuning is authorized.

The next CPU-only fixed-HGB stage is also implemented but has not run. It loads
the exact 639,652-byte historical `state_symmetric_hgb` artifact, reconstructs
the authenticated 48-feature state-symmetric record for every eligible Mistral
development pair, and performs inference without refitting. Its independent
validator uses the separate `empirical_feature_independent.py` formulas and
directly recomputes the HGB positive/negative symmetry calculation instead of
calling the producer's selector method. Native and independent feature/score
paths agree on invented fixtures, and the full Mistral-focused suite passes 53
tests. This stage remains blocked on accepted answer semantics. It has produced
no project HGB score, Gold access, fit, neural forward or test result.

The paired-GbV stage is now implemented but has not run. It requires the
independently accepted HGB stage, scores `a0/E0` before `a1/E1` with exact
`MoritzLaurer/deberta-v3-large-zeroshot-v2.0@5a4338ab2151dc8db04ad53b42b6153382bf4f99`
in FP32, and durably saves every raw two-logit forward plus tokenizer fields.
Its independent validator imports neither the producer nor the model class and
reconstructs token batches, softmax values, branch maxima and row margins from
the sealed logits. The initial slow-tokenizer smoke check failed before any
scientific output because the original virtual environment did not itself expose
SentencePiece. The hash-bound recovery in
`MISTRAL_GBV_SENTENCEPIECE_DEPENDENCY_RECOVERY_2026-09-17.md` uses the exact
historical 0.2.1 package copy, validates all 17 package files and provenance,
and performs no environment installation. Eight focused GbV tests and the complete
61-test Mistral suite pass. The stage remains blocked on HGB acceptance and has
produced no GbV score, Gold access, fit, test result or NLI model forward.

The common prelabel-freeze producer and an independently implemented validator
are now also complete but have not run. They require both accepted HGB and GbV
stages, reconstruct all 13,500 development identities, and emit the fixed feature
orders `HGB_GBV_R=[HGB,GbV]`, `HGB_ONLY_R=[HGB]`, and
`GBV_ONLY_R=[GbV]` under one shared eligibility mask. Native ineligible pairs and
deterministic NLI context failures force Keep for all three heads; any successfully
completed first GbV branch remains recorded for diagnosis without becoming a
policy-specific eligible row. Seven focused tests and the complete 68-test
Mistral suite pass. This stage remains blocked on independent GbV acceptance and
has read no Gold or test value, loaded no model, and performed no fit.

The development-outcome producer and its independent validator are now
implemented but have not run. They require the independently accepted common
prelabel freeze before opening Gold, then materialize only the 4,500 selected
development question labels and emit 13,500 numeric a0/a1 EM/F1 rows with exact
answer-receipt and prelabel-row bindings. Raw references are never written; the
failure receipt withholds exception text after Gold access to avoid accidental
reference leakage. The validator separately rereads the same authenticated
development references and recomputes normalized EM and token F1 with an
independent formula. Seven focused tests and the complete 75-test Mistral suite
pass. This stage remains blocked on independent prelabel acceptance and has read
no Gold or test value, loaded no model, and performed no fit.

The equal-budget development tuner and a separate full-refit validator are now
also implemented but have not run on project outcomes. The producer requires
accepted prelabel and development-outcome stages, then applies the frozen eight
candidate grid and three question-group folds identically to all three methods.
It durably records every fit start and terminal event, with exactly 84 producer
fit attempts and 168 journal rows: 78 search fits plus six fixed-reference fits.
The validator imports neither the producer nor the tuning core; it independently
reconstructs folds, preprocessing, all CV fits, pooled log losses, tie-breaking,
selected refits, fixed-reference heads and Platt fits, adding 84 audit refits
rather than a second selection search. A complete
three-method synthetic replay shows agreement within the fixed `1e-10` numerical
tolerance. Six focused tests and the complete 81-test Mistral suite pass. Test
access and action-budget tuning remain forbidden. This stage is blocked on
independent development-outcome acceptance and has performed no scientific fit.

The one-time Mistral test route is now prospectively frozen in
`MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md`. It binds the exact 6,000-question
/ 18,000-trace label-blind population, development predecessor gates,
component-sequential acquisition, action sealing before Gold, global `K=900`,
the four primary endpoints and 20,000 dataset-stratified question-cluster draws
with `default_rng(20260930)` and adjusted quantiles 0.00625/0.99375. This is a
protocol only: no test generation, score, action, outcome or bootstrap exists.

The result-independent test arithmetic and a non-importing explicit-copy audit
are now implemented in `scripts/mistral_test_analysis_math.py` and
`scripts/mistral_test_analysis_independent.py`. They cover the selected and
fixed-C recipes, exact point estimates, action overlaps, global top-K
reallocation on every draw, four-endpoint intervals and durable draw replay. The
first invented-only run exposed an incorrect test assertion that limited
resampled copies by the number of unique eligible source rows; that assertion
was corrected because bootstrap multiplicity can repeat one eligible row. No
analysis code or scientific rule changed. Seven focused tests and the complete
88-test Mistral suite pass. No benchmark outcome was read.

The label-blind test prediction and action-seal core is now also implemented in
`src/arbitration/reader_test_prediction.py`. It accepts only the exact test
prelabel schema and frozen development model records, reconstructs selected and
fixed-C probabilities, and seals all six score-based policies under the common
mask and canonical global action cap. The separate pure-Python audit in
`scripts/mistral_test_prediction_independent.py` imports neither the producer
nor an allocation kernel. Its first test run had one false-positive dependency
assertion caused by a module name in explanatory prose; the assertion was
narrowed to actual import statements without changing production code. Six
focused tests and the complete 94-test Mistral suite pass. No test label,
outcome, model fit or action ledger was produced.

The formal single-use action-seal executor and its independent validator are now
implemented in `scripts/run_mistral_test_action_seal.py` and
`scripts/validate_mistral_test_action_seal.py`. They require the accepted
development 84-fit result plus its 84-refit audit and a future independently
accepted 18,000-row test prelabel freeze. The executor writes only a canonical
label-blind action ledger; the validator independently recomputes every
probability and action within `1e-12`. Eight focused tests and the complete
96-test Mistral suite pass. The required test acquisition/scoring/prelabel
predecessors do not yet exist, so the formal namespace has not been created.

The final downstream analysis wrappers are now implemented in
`scripts/run_mistral_test_analysis.py` and
`scripts/validate_mistral_test_analysis.py`. After independently accepted action
and numeric-outcome stages, the producer will save all 20,000 dataset-stratified
question multiplicities and draw receipts, point estimates and four-endpoint
intervals. The validator reconstructs every RNG draw and explicit-copy top-K
allocation without importing the producer arithmetic. Nine focused tests and
the then-complete 98-test Mistral suite pass. No production draw or test outcome
has been read.

The numeric-only test-outcome producer and independent validator are now
implemented in `scripts/run_mistral_test_outcomes.py` and
`scripts/validate_mistral_test_outcomes.py`. Before any test Gold access, both
paths require the accepted 18,000-row action seal and independently accepted
test `a0_query` and `a1_likelihood` answer receipts. The producer then writes
exactly 18,000 rows with only identity plus `a0_em`, `a1_em`, `a0_f1` and
`a1_f1`; the validator separately rereads authenticated Gold and recomputes all
72,000 metric values without importing the producer. Raw references are never
written, and failure text is withheld after Gold access. Nine focused tests and
the complete 107-test Mistral suite pass on invented fixtures. The test
acquisition and neural-scoring predecessors do not exist, so no formal outcome
namespace was created and test Gold remains closed.

The first test-acquisition component is now implemented in
`scripts/run_mistral_test_a0_query.py`, with a separate tokenizer-only audit in
`scripts/validate_mistral_test_a0_query.py`. It binds the authenticated test
trace, candidate-pool and Mistral input-freeze manifests; reconstructs all
18,000 label-blind questions and ordered five-document evidence sets directly;
and plans exactly 36,000 durable `a0`/repair-query generations under the same
GPU mutex and resume semantics as development. A real no-model source smoke
reconstructed all 18,000 frozen traces and 6,000 groups without Gold access.
Six focused tests and the complete 113-test Mistral suite pass. The executor has
not run; its implemented downstream stages are documented below.

The test repair executor and a separate no-model replay validator are now
implemented in `scripts/run_mistral_test_repair.py` and
`scripts/validate_mistral_test_repair.py`. They require accepted test
`a0_query`, bind the accepted retrieval arrays and BGE synthetic preflight, and
fix 18,000 same-retriever depth-50 repairs with exactly 12,000 dense/hybrid
query forwards. Document re-embedding, Mistral, NLI, Gold and fitting are
forbidden; rank 5 is the only replacement position. The validator reconstructs
the rankings from stored query vectors with zero model load. A real label-blind
source smoke restored all three retrieval datasets and checked first/last
evidence identities in each. Five focused tests and the complete 118-test
Mistral suite pass. No formal repair was executed.

The test `a1_likelihood` executor and independent tokenizer-only validator are
now implemented in `scripts/run_mistral_test_a1_likelihood.py` and
`scripts/validate_mistral_test_a1_likelihood.py`. They require independently
accepted test `a0_query` and repair stages, bind every predecessor member, and
fix 18,000 `a1` generations plus 72,000 `L00/L01/L10/L11` likelihoods. BGE,
NLI, Gold, fitting and tuning are forbidden. The validator reconstructs all
90,000 prompts, targets, journal entries and likelihood summaries with zero
model load. The initial source smoke without the pinned dependency overlay
failed before tokenizer construction because SentencePiece/protobuf were not on
`PYTHONPATH`; that failure is retained. The corrected pinned-overlay smoke bound
all 18,000 test traces and passed six synthetic first/last-dataset `E1` prompt
checks with zero model forwards and zero Gold access. Five focused tests and the
complete 123-test Mistral suite pass. No formal test `a1_likelihood` execution
was started.

The test witness replay executor and independent tokenizer-only vector audit are
now implemented in `scripts/run_mistral_test_witness_replay.py` and
`scripts/validate_mistral_test_witness_replay.py`. They require accepted test
`a0_query`, repair and `a1_likelihood`, then select the first and last trace in
each of nine dataset-by-retriever cells. The fixed workload is 18 positions by
seven operations: 126 exact receipt replays and 126 raw 32,768-element FP32
first-token vectors totaling 16,515,072 bytes. The validator independently
recomputes target-token identity and float64 log-softmax without importing the
producer or loading a model. Five focused tests and the complete 128-test
Mistral suite pass. No formal witness replay was executed because its accepted
test predecessors do not exist yet.

The label-blind test answer-semantics producer and independent tokenizer-only
validator are now also implemented without executing the formal stage. They fix
18,000 test pairs, 36,000 normalized BGE vectors, 2,250 batches and 110,592,000
explicit little-endian FP32 bytes. The validator reconstructs every batch
identity, tokenization, vector norm and pairwise dot product without importing
the producer or loading a model. Four new contract tests and the complete
132-test Mistral suite pass. This stage remains blocked on the complete accepted
development chain and accepted test
acquisition/witness predecessors. Test HGB, GbV and the common prelabel freeze
remain the next engineering gaps; no test Gold, outcome, fit or tuning access
occurred.

The following test HGB-signal stage is now implemented but has not run. It
reconstructs all 18,000 test E0/E1 evidence pairs from authenticated pool and
retrieval arrays, applies the exact historical 48-feature state-symmetric HGB
without refitting, and retains explicit forced-Keep reasons for ineligible
pairs. Its independent validator uses the separate feature formulas and directly
recomputes the positive/negative probability symmetry instead of calling the
producer selector. Five new contract tests pass. Neural loads/forwards, project
or test Gold, test outcomes, fitting and tuning remain forbidden; the complete
Mistral suite now passes 137 tests. This stage is
blocked on accepted test answer semantics; test GbV and common prelabel remain
the next engineering gaps.

The paired test GbV producer and independent tokenizer/logit validator are now
implemented but have not run. They pin the exact DeBERTa NLI revision, FP32,
batch size 8 and `a0/E0` before `a1/E1` order, save every two-logit forward as
explicit little-endian bytes, and retain a valid F0 if F1 later has one of the
two frozen deterministic context-window failures. The validator loads no model,
reconstructs every token batch and float64 softmax, and proves exact logit-file
coverage. Eight new contract tests and the complete 145-test Mistral suite pass.
Mistral/BGE loads, Gold, outcomes, fitting and tuning remain forbidden. This
stage is blocked on accepted test HGB.

The common test prelabel producer and independent validator are now implemented
but have not run. They require independently accepted test HGB and GbV, bind the
complete authenticated test trace/pool/retrieval/input-freeze chain, and merge
all 18,000 rows into one common eligibility mask for `HGB_GBV_R`, `HGB_ONLY_R`
and `GBV_ONLY_R`. The validator independently reconstructs every row without
importing the producer. Seven focused tests and the complete 152-test Mistral
suite pass. No model was loaded, no fit or tuning was performed, and no project
Gold, test Gold or test outcome was read. The label-blind test scoring/action
implementation chain is now complete; execution remains blocked on the accepted
development chain and sequential acceptance of every formal test predecessor.

Completed this turn: a hash-bound descriptive decomposition of all 18,000 public
Qwen numeric rows. Both policies select 506 common replacements and 394 unique
replacements each. Fusion-only choices yield 109 Recovery / 10 Damage; HGB-only
choices yield 114 / 25. Totals reconcile exactly with the accepted result map.
See `HGB_FUSION_DISAGREEMENT_2026-09-16.json` and
`scripts/describe_hgb_fusion_disagreement.py`. This is post-hoc accounting, with
zero new fit, neural forward, bootstrap or test-guided tuning.

The research choice remains pinned Mistral-7B-Instruct-v0.3, with a prospective
4-bit deployment design to be checked on the local 16GB GPU. It would be the
second scientifically valid reader condition, not evidence that Phi passed.
The question is whether the change in recovery and harmful replacement recurs
under this condition; there is no presumption of superiority. Next P0 is the
resource/numerical contract and scientific design closure; P1 is the fixed reader
experiment and full reporting; P2 is manuscript/release synchronization after
valid results. Compliance closure stays deferred at the user's request.

## Current superseding milestone (2026-09-16)

The current target is **Journal of Intelligent Information Systems (JIIS)**.
The author designated `JIIS_Final_With_Declarations.pdf` as the latest source.
Its byte-identical 22-page project copy is
`output/pdf/JIIS_Final_With_Declarations_2026-09-16.pdf`, SHA-256
`60d9528b3d4a89fa8f704d6f831340b5c3d024ae14a37ddcffae5361c6a46a8f`.
It retains Zhigang Xu, Xingji Qian, and Xinhua Dong; Hubei University of
Technology, Wuhan, 430068, Hubei, China; Xinhua Dong as first corresponding
author (`xhdong@hbut.edu.cn`); and Xingji Qian as second corresponding author
(`102511283@hbut.edu.cn`). It includes funding, competing interests, author
contributions, author approval, and data/code availability statements. Use this
PDF as the current baseline. All prior PDFs and receipts remain preserved.
`paper/LATEST_MANUSCRIPT.json` records the current artifact, and
`paper/JIIS_FINAL_DECLARATIONS_20260916_IDENTITY_VERIFICATION.json` records the
31-check identity/mechanical PASS. Exact scientific and declaration audits are
still pending for these bytes; no experiment or refit ran during registration.

The new manuscript cites the clean public repository
<https://github.com/qianxingji/ReliableRAG-Code> at commit
`038d769e96d092a2eec3bbc5df9f45f3c2a17ff0`. Its development, parameter, and
evaluation bundle hashes match the local public checkout. The earlier R6
release verification covers current-head refitting and full statistical
reconstruction; see `JIIS_R6_MAJOR_REVISION_ACCEPTANCE.md`. Registration of
the new PDF is an identity/mechanical check, not final scientific acceptance.
Its exact claims and the prior R6 response letter still need to be reviewed
against these new bytes; no experiments or refits were run during registration.

The older Applied Intelligence route records below remain historical evidence;
they do not override the later JIIS target selection. Remaining work is a
JIIS-specific scientific/editorial audit and the required Astra xhigh final
Claim-sufficiency and Submission Ready acceptance. Public current-head refitting
and per-question numeric selection/bootstrap reconstruction were verified for
the cited release. End-to-end retrieval, generation, neural scoring, and
historical upstream fitting remain outside the release.

The user's earlier 2026-09-13 steering was to continue this work as a **conditional CAS
Q3 empirical study**. This authorizes target-neutral editorial and packaging
work within the accepted Qwen evidence. It does not reopen reader/method
experiments, relax authenticity or fairness, or imply that a CAS Q3 journal has
already been certified. The newer 2026-09-16 research steering above reopens
reader design while preserving the accepted empirical evidence boundary.

The machine-readable
[submission-readiness gate](SUBMISSION_READINESS_GATE.md) independently verifies
the frozen scientific boundary and repository hashes, then fails closed while
P0-G, P0-H and P0-I remain open. Its current decision is
`FAIL_CLOSED_CAS_Q3_NOT_READY_EXTERNAL_OWNER_INSTITUTION_AUTHOR_GATES`; it reads
no scientific payload, performs no fit and executes no model forward.

The remaining owner, institution and author fields are now consolidated in the
[private owner-input intake](OWNER_INPUTS_INTAKE.md). The tracked JSON template
contains no identities; its `.local.json` copy is ignored by Git, and the
verifier never echoes supplied values. Completing that file is an input-stage
advance only: CAS authority, journal policy, license/release implementation,
target artifacts and the final Astra xhigh audit still require independent
evidence.

The ignored local closure workspace is now operational. The preparer preserved
the existing owner-input bytes, created empty institutional CAS and release
placeholders from the tracked templates, and created their private-evidence
directories. A separate institutional manuscript-approval template and
fail-closed verifier now bind eventual approval evidence to the exact approved
manuscript bytes; its local placeholder and evidence directory are also ignored
by Git. The unified verifier now checks all four records together, including
approval status, target journal and exact approved-manuscript digest. It still
fails closed: owner inputs have 5 missing fields and zero errors, the CAS
placeholder has 22 missing fields and zero errors, the release placeholder has
22 missing fields plus five expected conflicts, and the manuscript-approval
placeholder has 17 missing fields plus two expected conflicts. No institutional
evidence or manuscript bytes were read, and placeholders are not received
institutional records.

A read-only accessible-evidence census scanned the original workspace, the
preserved private historical root and the old repository ZIP. It read 454,115
bounded ordinary text files and 1,448 bounded text members across 39 ZIPs.
Three broad-marker candidates were historical experiment reports in which
“分区” meant data or training partitions. No HBUT CAS, manuscript-approval or
code-release record was recovered. A separate streaming extension then covered
all 26 oversized ordinary text files and all 12 oversized ZIP text members,
1,489,169,218 bytes in total, with zero candidate, skip or error. Unsupported
binary formats were then inventoried: the roots contain 100 ordinary PDFs and
138 PDF members across the 39 ZIPs, but no Word, Excel, PowerPoint, RTF, MSG or
ODF document under the explicit extension inventory. Poppler extracted all 238
PDF text layers and searched 3,448,238
text bytes with zero candidate, skip or error. The 238 occurrences reduce to 35
unique hashes; all have at least 20 non-whitespace extracted-text bytes and all
35 have zero embedded attachment under `pdfdetach`. Page-image OCR, unknown
binary formats and locations outside the three roots remain outside these
negative results' scope. A recursive follow-up then materialized all four
ZIP-valued members (269,975,228 bytes), scanned all 301 direct members and
confirmed that none contains a deeper archive. It searched all 234 recognized
text members and 858,962,287 bytes, plus 32 PDF occurrences representing 14
unique hashes within the nested scope. Both passes returned zero candidate,
skip or error; every nested PDF had usable extracted text and zero attachment.
This closes the first-level nested-ZIP omission only. Ordinary-file magic beyond
the extension inventory and page-image OCR remained open boundaries at that
stage. A subsequent strict ordinary-file header pass covered all 465,460 files
and 631,242,643 leading bytes. It found only 39 ZIPs named `.zip` and 100 PDFs
named `.pdf`, no OOXML/ODF package in the ZIPs, no RTF/OLE header, no mismatch
and no error. Three loose `%PDF-` matches were retained as source-code literals
in two `.js` and one `.ts` file rather than misclassified as hidden PDFs.
The page-level follow-up then deduplicated all 270 ordinary, direct-ZIP and
nested-ZIP PDF occurrences to the same 35 hashes and inspected all 446 pages.
Every page has at least 20 non-whitespace extracted-text bytes; 15 pages contain
raster-image objects but none is textless or low-text. This rules out wholly
textless scanned pages among the known PDFs. Text inside images on otherwise
text-bearing pages was not OCRed. Unknown binary formats and locations outside
the roots remain open boundaries.

Latest route decision: the independent GPT-6 Astra xhigh
[target-transition audit](TARGET_TRANSITION_ASTRA_XHIGH_AUDIT.md) sets the unique
recommendation
**`PROCEED_Q3_QWEN_ONLY_EVIDENCE_AND_JOURNAL_FIT_GATE_NO_NEW_EXPERIMENTS`**.
The existing Qwen study is sufficient to serve as the possible scientific core;
it is not yet a complete submission package or an acceptance guarantee.

## Authority and preserved state

The user formally changed the hard target to CAS Journal Ranking Q3 on
2026-09-13. Read [PROJECT_CHARTER.md](PROJECT_CHARTER.md),
[TARGET_TRANSITION.md](TARGET_TRANSITION.md), [CURRENT_METHOD.md](CURRENT_METHOD.md)
and [EVIDENCE_INDEX.json](EVIDENCE_INDEX.json). The complete `../cas_q2` tree is
historical evidence and must remain intact.

Keep the original dirty workspace at `E:/paper/ReliableRAG`, all sealed outputs,
failures and seeds. Continue project work in
`E:/paper/ReliableRAG-cas-q2-p0-1`, branch `work/cas-q2-p0-1`, draft PR #1. The
worktree/branch names are historical. Do not restart Phi, Mistral, RECA or a new
method/reader/seed/budget search.

The user's model routing remains binding: Sol High for routine engineering and
ordinary analysis; GPT-6 Astra xhigh for major method/claim decisions and final
fairness, reviewer and Submission Ready audits.

## Accepted scientific core

- Original saved-parameter numerical replay and source audit are accepted within
  the provenance limits in `../cas_q2/P0_1_CLIENT_ACCEPTANCE.md`. Seven original
  per-estimator fit-time ID/matrix receipts and an independent original-fit
  witness remain missing. A preserved pre-ROA-named archive now supplies a
  byte-identical copy of the complete historical `mars_full` manifest, but no
  external record independently certifies that archive's timestamp; see
  `P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.md`.
  A later [bounded receipt census](P0_E_ORIGINAL_FIT_RECEIPT_CENSUS.md) scanned
  55,373 files, 1,770 metadata candidates and 37 ZIPs. It found only the seven
  original model hashes and their seven static-delivery copies, with no third
  independent copy or original fit-time ID/matrix receipt.
- All three supervised controls and five fixed empirical policies are complete.
  The actual takeover fit count is 185.
- The 6,000-question Qwen study, 18,000 retrieval traces, generation/replay,
  scoring, fixed actions, selected-reference mapping, 20,000-draw analysis and
  independent validators are complete and accepted through
  `../cas_q2/EMPIRICAL_D_ACCEPTANCE.md`.
- HGB_GBV_R jointly beats GBV_ONLY_R on EM/Damage, does not jointly beat
  HGB_ONLY_R, and ROA-FULL does not advance over HGB_GBV_R. No novel candidate is
  cleared; see `../cas_q2/P0_3_FRESH_RESULT_DECISION.md`.
- Shared-inference cost accounting is accepted with explicit missing latency and
  peak-memory measurements in `../cas_q2/EMPIRICAL_COST_ACCEPTANCE.md`.
- Phi V4 runtime/replay evidence is authentic within its stated scope, but its
  semantic validation gate failed terminally. Mistral was selected and then
  stopped before engineering. Neither supplies scientific effect evidence.

## P0: required before credible Q3 submission

1. **P0-A -- CLOSED:** The
   [direct-neighbor audit](P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md) rejects a
   method-novelty Claim and now states the full gain-prediction overlap and exact
   comparison-dependent empirical boundary.
2. **P0-B -- CLOSED:** The
   [complete result/Claim map](P0_B_RESULT_CLAIM_MAP.md) binds all nine policies,
   the original six-endpoint family, fixed-action sensitivity, secondary-table
   rules and negative findings to the accepted Qwen evidence. Both gates are
   closed by the [independent Astra xhigh recheck](P0_A_P0_B_ASTRA_XHIGH_RECHECK.md).
3. **P0-C -- CLOSED:** The
   [method/fairness account](P0_C_METHOD_FAIRNESS_ACCOUNT.md) fixes the exact
   model, candidate/pool/retrieval roles, development/test identities, five
   heads, seven upstream estimators, eligibility, missing values, K=900, ties
   and Gold order.
4. **P0-D -- CLOSED:** The
   [statistical statement verification](P0_D_STATISTICAL_STATEMENT_VERIFICATION.md)
   binds every unit, interval role, multiplicity rule, joint gate and grouped
   top-K bootstrap description to the accepted aggregate analysis and its prior
   independent full-draw validation.
5. **P0-E -- CLOSED:** The
   [frozen disclosure boundary](P0_E_PROVENANCE_CONTAMINATION_ADAPTATION_FAILURE_DISCLOSURES.md)
   records data/cohort provenance, exact contamination limits, GbV adaptation,
   missing original fit evidence and the Phi/Mistral terminal exclusions. Its
   [manifest-recovery addendum](P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.md)
   records the byte-identical packaged copy and the unresolved independent-time
   boundary without changing the P0-E decision. The final
   [Astra xhigh authenticity audit](P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_ASTRA_XHIGH_AUDIT.md)
   accepts that bounded byte claim and retains every timestamp/original-fit gap.
   The subsequent [accessible-root census](P0_E_ORIGINAL_FIT_RECEIPT_CENSUS.md)
   performs a model-hash, bounded metadata and ZIP-member search over four
   historical roots. Its zero-candidate result strengthens the search record but
   cannot prove absence outside those roots or replace the missing receipts.
6. **P0-F -- CLOSED WITH MEASUREMENT LIMITS:** The
   [claim-scoped cost table](P0_F_CLAIM_SCOPED_COST_TABLE.md) reports the shared
   workload, non-additive timers and saved C4 peaks while retaining every missing
   standalone, canonical peak, end-to-end and FLOP measurement.
7. **P0-G -- PARTIAL PASS / OPEN:** The
   [release audit](P0_G_REVIEWER_RELEASE_LICENSE_ANONYMIZATION_AUDIT.md) now
   freezes a nine-member anonymous aggregate allowlist. Two deterministic builds
   share one archive hash; the independent validator passes 100 checks and the
   extracted verifier passes 129 checks. The candidate remains withheld. The
   owner has selected Apache License 2.0 for project-authored code, and the exact
   license text is now present at repository top level. Legal holder/year,
   institutional NOTICE/review requirements, third-party release review, final
   authorization and persistent archiving of the validated corrected candidate,
   and an operational private-review delivery route remain open. Springer
   Nature's current policy now establishes that reasonable third-party licence
   restrictions are permitted and that editors/reviewers may request non-public
   data or code; it does not pre-approve a particular transfer channel. The
   public GitHub location exists, while the final submission revision and
   permanent archive identifier remain unfrozen. The historical
   [current license decision packet](P0_G_PROJECT_LICENSE_DECISION_PACKET.md)
   records the implemented Apache choice and remaining holder/year/review
   fields. These facts have a private machine-validated
   intake path shared with P0-H/I.
   The [Applied Intelligence data/code policy audit](P0_G_APPLIED_INTELLIGENCE_DATA_CODE_POLICY_AUDIT.md)
   now governs the selected target. The earlier
   [provisional Discover data/code policy audit](P0_G_DISCOVER_DATA_CODE_POLICY_AUDIT.md)
   now fixes that candidate's official statement, code-testing and persistent-
   archive requirements. It confirms that the aggregate ZIP alone is
   insufficient for final code availability; license-bearing latest and
   immutable archive links plus a permitted review channel remain required.
   The [third-party terms recheck](P0_G_THIRD_PARTY_TERMS_RECHECK.md) also
   corrects the release-source description of the non-`-c` DeBERTa checkpoint:
   its model card labels the foundation model MIT but retains a mixed,
   partly non-commercial training-data warning. The historical aggregate ZIP
   remains an immutable withheld arithmetic witness.
   A corrected Apache-2.0-aware V2 candidate has now been built twice, matched
   byte-for-byte, independently validated, and remains distribution-withheld.
   The [license-state corrigendum](P0_G_LICENSE_STATE_CORRIGENDUM.md) preserves
   the historically accurate pre-license audit while binding the current root
   license and `LICENSE_SCOPE.md`. Its 26-check verifier rejects a return to the
   stale “owner decision required” state and keeps the legal holder, year,
   institutional review, Qwen research-license and non-`-c` DeBERTa gates open.
    A fail-closed [private institutional release-record intake](P0_G_INSTITUTIONAL_RELEASE_RECORD_INTAKE.md)
   now binds any future owner/institution decision to the exact corrected V2
   archive hash. It checks retained evidence bytes, holder/year, release-review
   and NOTICE consistency, the no-weight/no-benchmark-payload boundary, and the
   Qwen/DeBERTa scope decisions without committing private evidence. Its
    structural pass still requires a separate client content audit, explicit
    owner authorization, a persistent identifier and the journal-approved
    restricted-review route; no release record has yet been received.
    A separate fail-closed [final release-activation intake](P0_G_RELEASE_ACTIVATION_INTAKE.md)
    now binds those future decisions to the exact frozen Git commit, immutable
    commit URL, retained release-archive and manifest hashes, resolving
    persistent identifier, and the observed editor-request/review-channel
    state. Its verifier never fetches, uploads or publishes anything and cannot
    authorize distribution. Even a structurally complete record remains pending
    client content review, final artifact rebinding and the required Astra xhigh
    audit. No real activation value, tag, release, deposit or DOI exists yet.
    A later [external raster-image audit](P0_GHI_EXTERNAL_IMAGE_EVIDENCE.md)
    checks common image magic across the same logical roots, all direct ZIP
    members and all first-level nested ZIP members. It reduces 104 occurrences
    to 43 hashes and records a complete project-lead visual review: 14 hashes are
    old manuscript figures and 29 are shared-runtime icons or format fixtures;
    none is an institutional closure record. Its companion
    [logical-root reparse disclosure](P0_GHI_LOGICAL_ROOT_REPARSE_DISCLOSURE.md)
    corrects the earlier physical-boundary wording: 7,796 logical paths resolve
    through one Windows junction into a shared runtime. That superset does not
    invalidate the bounded negative search, but exact counts are host-local and
    the shared-runtime bytes are not preserved project evidence.
8. **P0-H -- OWNER TARGET SELECTED / INSTITUTIONAL CAS RECORD PENDING:** The
   [Applied Intelligence target selection](P0_H_APPLIED_INTELLIGENCE_TARGET_SELECTION.md)
   records the owner's target, Hubei University of Technology major-category
   CAS rule, current title/ISSNs, hybrid subscription route and current official
   submission requirements. The fit is plausible but carries high originality
   risk because the study has no new selector architecture, does not pass
   against HGB-only and has one accepted reader. The institution-recognized CAS
   edition/year and retained current-title/ISSN Tier-3 record are still missing.
   The earlier [target-journal audit](P0_H_TARGET_JOURNAL_FIT_AUDIT.md) ranks Discover
   Computing first for empirical editorial fit and Journal of Intelligent
   Information Systems first for stable subject identity. The
   [submission-requirements matrix](P0_H_SUBMISSION_REQUIREMENTS_MATRIX.md)
   freezes each candidate's current article, length, file, review, declaration
   and data-policy constraints. No journal is certified until the applicable CAS
   year/category and institutional title/ISSN rule are supplied. The refreshed
   [owner/institution qualification packet](P0_H_TARGET_JOURNAL_DECISION_PACKET.md)
   now records the fixed Applied Intelligence selection, current publisher-side
   state and exact fields needed to authenticate the institution-recognized CAS
   result. Earlier four-journal comparisons remain historical. The consolidated
   local intake checks field completeness but cannot authenticate the
   institutional record.
   A later [official HBUT policy verification](P0_H_HBUT_CAS_POLICY_ACCEPTANCE.md)
   confirms that the university publicly uses the upgraded CAS basis for SCI
   and SSCI recognition, requires HBUT as first affiliation for reported papers,
   and assigns natural-science paper recognition review to a named office. The
   applicable edition/year and a retained Applied Intelligence current-title,
   ISSN and Computer Science major-category Q3-or-above record remain missing,
   so P0-H is still open.
   A concrete [HBUT institutional verification request](P0_GH_HBUT_INSTITUTIONAL_VERIFICATION_REQUEST_ZH.md)
   is ready for the responsible author to submit. It asks for the CAS edition,
   current title/ISSNs, major-category tier, recognition-date and title-change
   rules together with manuscript approval, code copyright/release and Qwen/
   DeBERTa review. It records `request_sent=false` and cannot substitute for the
   retained institutional response.
   A deterministic [HBUT review-request packet](P0_GHI_HBUT_REVIEW_REQUEST_PACKET_ACCEPTANCE.md)
   now places that request beside the current anonymous manuscript/supplement,
   proposed Apache-2.0 materials and third-party review inputs. Two independent
   11-member builds are byte-identical and each passes 99 checks without
   extraction. The packet remains unsent, contains no institutional response or
   local owner input, and any later manuscript approval must be rebound to the
   exact final author-populated artifact.
   A deterministic [sender-free HBUT email draft](P0_GHI_HBUT_EMAIL_DRAFT_ACCEPTANCE.md)
   now wraps the authenticated request packet as its sole attachment. Two
   independent `.eml` builds are byte-identical and each passes 43 checks. The
   draft contains no sender identity or transport headers and has not been
   sent; it therefore supplies no institutional response, approval or P0 pass.
   A later [official HBUT college-level secondary-evidence audit](P0_H_HBUT_CAS_EDITION_RULE_SECONDARY_EVIDENCE.md)
   finds a published School of Science rule using the upgraded CAS report from
   the year before publication. It makes 2025 the candidate report year for a
   2026 publication, but does not establish that this college programme rule
   applies university-wide or that Applied Intelligence is Q3; the central
   confirmation remains required. The authoritative CAS partition platform
   publicly lists the 2025 upgraded data as available and supports title/ISSN
   search, but detailed records require institutional or authenticated access;
   no Applied Intelligence record was retrieved or inferred.
   A [public corroboration audit](P0_H_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION.md)
   separately records that two public detail sources label the 2025 upgraded
   edition Computer Science major category Q3 and Artificial Intelligence minor
   category Q4. An official other-university faculty-page search excerpt also
   labels a 2025 Applied Intelligence item major-category Q3, but direct fetch
   returned HTTP 412 and the edition was not authenticated. A separate university
   library navigation page exposes an unlabeled Q4 value, so the category ambiguity
   is retained. This supports the target's plausibility under the owner's major-
   category rule but does not replace the HBUT-recognized record or close P0-H.
   A 2026-09-15
   [HBUT public target-record recheck](P0_H_HBUT_PUBLIC_TARGET_RECORD_RECHECK.md)
   then inspects the official HBUT pages most likely to be mistaken for target
   qualification evidence. Their Applied Intelligence entries are historical
   article listings labelled only “SCI 2区” or have no tier; a 2014 assessment
   rule is also too old and target-unspecific. None binds the 2025 upgraded
   edition, Computer Science major category, current title and both ISSNs. The
   bounded public search does not prove absence from internal or authenticated
   systems and therefore leaves the institutional record requirement open.
   The responsible author later asserted the 2025 upgraded edition and Computer
   Science major-category Q3 result. The accompanying
   [declared-path check](P0_H_OWNER_2025_CAS_ASSERTION_PATH_CHECK.md) found that
   `compliance/cas_partition/2025/` exists in neither the isolated worktree nor
   the preserved original workspace. The assertion is retained as owner input,
   but no HBUT-issued record or evidence bytes were received and P0-H remains
   open.
   A fail-closed [private institutional-record intake](P0_H_INSTITUTIONAL_CAS_RECORD_INTAKE.md)
   now fixes the future record bytes by SHA-256 and checks the edition, current
   title, both ISSNs, major category, Q1/Q2/Q3 target tier, recognition-date and
   title-change fields without committing the record or local metadata. It
   cannot certify its own transcription: a separate client visual/content audit
   remains mandatory, and no institutional record has yet been received.
   The [Discover Computing APC audit](P0_H_DISCOVER_COMPUTING_APC_AUDIT.md)
   closes the current-price lookup: the official page lists GBP 1,040, USD
   1,520, or EUR 1,140 plus applicable taxes and applies the acceptance-date
   price. It is now historical rather than the active route. Applied
   Intelligence's official page states that its selected subscription route has
   no APC.
9. **P0-I -- SOURCE AND COMPILED DRAFT ACCEPTED / EXTERNAL INPUTS OPEN:** The
   [manuscript preflight](P0_I_MANUSCRIPT_PREFLIGHT.md) freezes journal render
   profiles, the evidence-to-section map, table/figure sources, forbidden Claims,
   author inputs and final audit gates. The user's direct “继续” reply after the
   authorization blocker is recorded in the
   [authorization record](P0_I_MANUSCRIPT_AUTHORIZATION.md). The main manuscript,
   supplement, bibliography, generated tables/figures, title-page template and
   cover-letter template now exist under `paper/`; the independent static
   verifier now passes 141 checks. MiKTeX produced an 11-page main PDF and 3-page
   supplement; mechanical log checks and project-lead review of all pages pass.
   The subsequent [font-embedding corrigendum](P0_I_FONT_EMBEDDING_CORRIGENDUM.md)
   replaces the unembedded Base-14 figure fonts and isolated Type 3 marker; both
   PDFs now have zero nonembedded and zero Type 3 fonts. The supplement retains
   its disclosed nonfatal `longtable` notice; the
   [upstream triage](P0_I_LONGTABLE_NOTICE_TRIAGE.md) binds it to the installed
   2025-10-13 v4.24 package and requires a final target-environment recheck.
   See the [build status](P0_I_MANUSCRIPT_BUILD_STATUS.md) and
   [compiled-artifact acceptance](P0_I_COMPILED_ARTIFACT_ACCEPTANCE.md). The
   Astra xhigh source-level fairness, Claim and simulated-reviewer audit and its
   [compiled-artifact rebind](P0_I_ASTRA_XHIGH_COMPILED_REBIND.md) passed within
   blockers. The subsequent build-path repair was independently reaffirmed in
   the [engineering addendum](P0_I_ASTRA_XHIGH_COMPILED_REBIND_ADDENDUM.md),
   including 14/14 pixel-identical rebuilt pages for that historical artifact.
   The font-clean rebuild changes only main pages 4 and 7 and passed fresh
   project-lead review; it awaits the final Astra xhigh rebind after journal
   conversion. Final Submission Ready remains blocked by incomplete author and
   release inputs and the certified CAS Q3 journal record. The
   [author/declaration intake](P0_I_AUTHOR_DECLARATION_INTAKE.md) now reduces the
   remaining author surface to explicit identity, CRediT, funding, interests,
   ethics, acknowledgements if applicable, AI-assistance, originality and
   approval fields;
   none is guessed. Its 19-check verifier also compiles the placeholder title
   page successfully as a 2-page PDF, closing the template-syntax gate while
   retaining every factual field as pending. The consolidated intake adds a
   privacy-preserving local JSON route for those facts without committing them.
   The owner has now supplied the formal author name, first affiliation and
   department, active corresponding-author email, target journal,
   publication route, project-license choice and CAS category rule. The
   [official HBUT address verification](P0_I_HBUT_AFFILIATION_ADDRESS_ACCEPTANCE.md)
   independently supplies Wuhan and postcode 430068. The department and
   personal contact fields were later supplied directly by the owner and remain
   only in the Git-ignored input. An official Applied Intelligence
   requirement audit has corrected the hard gate from the historical 30-field
   snapshot to a 19-field intermediate snapshot; the first direct owner update
   reduced it to 16, the second response reduced it to 9, and the third response
   plus fail-closed content review left 6 real missing fields and zero
   validation errors. The latest accepted facts include all-author approval and
   the requirement for institutional manuscript and release review. Those
   reviews remain pending rather than approved.
   A fourth owner update supplies an AI-tool range beginning 2026-07-10 and
   planned through 2026-09-20. Because the planned end is later than the current
   2026-09-15 validation date, final end-date confirmation remains open; the
   structural owner deficit is now 5 fields with zero validation errors.
   Optional ORCID, a separate corresponding-author postal address and acknowledgements
   are no longer treated as mandatory, while truthful CRediT coverage remains
   required. Correspondence and CRediT are complete. The individual
   copyright-holder and candidate 2025 CAS-edition entries remain owner
   assertions; institutional review outcomes and CAS authority are not inferred.
   A [unified private external-closure preflight](P0_GHI_EXTERNAL_CLOSURE_PREFLIGHT.md)
   now runs the owner, institutional-CAS and institutional-release validators in
   one command and checks their title, ISSN, edition, tier, recognition-rule,
   license, holder/year and review-state agreement. Its current local result is
   fail-closed: 5 owner fields remain missing and the two institutional input
   files are empty template placeholders. Even a future structural pass leaves
   the client content, author-artifact and final Astra xhigh audits open.
   A separate local builder can then produce an ignored title page,
   declarations source and cover-letter draft. It refuses incomplete inputs,
   does not overwrite a prior directory and emits only a redacted build receipt;
   generated drafts remain unverified and submission-unauthorized.
   The journal-neutral abstract is now 155 words and has five keywords, meeting
   Applied Intelligence's inspected count requirements without changing the
   Claim boundary. The rebuilt 11+3 pages passed separate mechanical,
   font and complete project-lead visual review; the mechanical verifier no
   longer self-asserts a human inspection.
   A separate reproducible PDF-length proxy records 4,048 tokens before
   References and 4,745 overall. Applied Intelligence's inspected guidelines
   specify no general full-manuscript word limit; these are reproducible proxy
   counts rather than publisher counts.
   The [Applied Intelligence abstract and keyword acceptance](P0_I_APPLIED_INTELLIGENCE_ABSTRACT_KEYWORD_ACCEPTANCE.md)
   binds that edit, both current PDFs and the complete 14-page visual review
   while retaining the target-template and final Astra gates.
   The subsequent [modern-template preflight](P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_ACCEPTANCE.md)
   authenticates the December 2024 official Springer Nature package and builds
   a clean 12-page `sn-jnl`/numeric-citation PDF plus a flat eight-member
   authored-source ZIP. All 12 pages pass project-lead visual review. This
   remains a partial pass because the journal page's `smallcondensed` request
   has not been proved equivalent to the modern package.
   The later [complete-source transport acceptance](P0_I_APPLIED_INTELLIGENCE_TEMPLATE_TRANSPORT_ACCEPTANCE.md)
   establishes that the current Springer Nature authoring template is an
   officially supported working route and packages the exact authenticated
   class/style with the eight authored files. Two private external builds are
   byte-identical; each passes 56 independent checks and clean compilation, and
   the resulting PDF is byte-identical to the visually accepted 12-page
   preflight. The journal page's legacy `smallcondensed` link returns 404 and
   the current package contains no such profile, so journal-specific
   equivalence remains open. The private transport is anonymous and neither
   submission- nor distribution-authorized.
   The later [official template-route resolution](P0_I_APPLIED_INTELLIGENCE_TEMPLATE_ROUTE_RESOLUTION.md)
   closes the narrower pre-submission route question: Applied Intelligence
   itself encourages the current Springer Nature template, and publisher
   support states that template may be used for any Springer Nature journal.
   The unavailable legacy `smallcondensed` profile is still not claimed to be
   style-equivalent. No Editorial Manager compile or author-populated upload is
   inferred.
   The subsequent [private target-builder acceptance](P0_I_APPLIED_INTELLIGENCE_PRIVATE_SUBMISSION_BUILDER_ACCEPTANCE.md)
   implements the remaining mechanical path from a complete owner-input file
   to an author-populated flat source ZIP, compiled PDF and cover letter. A
   synthetic complete fixture passed the full build and all 13 rendered pages
   passed visual inspection. At that historical synthetic-builder snapshot the
   actual local input remained fail-closed at 30 missing fields; the underlying
   historical receipt is intentionally unchanged. The later
   [official-requirement correction](P0_I_REQUIRED_OWNER_FIELDS_CORRECTION.md)
   reduced the then-current hard gate to 19 real missing fields. The subsequent
   first direct owner update resolved three of those paths and synchronized the
   author-list name. A second response supplied CRediT and several declarations.
   The third confirms all-author approval and required institutional review and
   supplies owner-side holder and 2025-edition assertions. AI wording approval,
   final confirmation of the supplied planned AI-use end date, substantive competing-interests wording, and
   actual institutional approvals/evidence remain open; after the fourth
   date-range update, 5 fields are still
   missing, so no real identity-bearing target package has been generated.
   The current 5 missing paths are rendered into a
   [privacy-safe responsible-author one-reply packet](P0_I_RESPONSIBLE_AUTHOR_ONE_REPLY_PACKET_ZH.md).
   Its generator and regression test prove that already supplied local names,
   email addresses, postal details and declaration text are not serialized into
   the tracked packet or receipt. It now exposes the exact static AI-assistance
   candidate, a truthful no-conflict option, a date-range format and the ignored
   institutional manuscript/release evidence directories so the five open items
   can be reviewed without guessing. The packet only reduces coordination friction;
   it does not complete any declaration or authorize submission.
   The subsequent [AI-tool date evidence audit](P0_I_AI_TOOL_DATE_EVIDENCE.md)
   authenticates retained model-specific records without turning a
   routing instruction into use evidence. It proves only that GPT-Sol and
   GPT-Astra both have retained use records by 2026-09-12. The actual first and
   last use dates remain unknown and require author confirmation, so the
   repository-only date audit cannot close P0-I. The later fourth owner update
   supplies 2026-07-10 as the start and 2026-09-20 as the planned end; because
   the latter is still in the future at validation time, final confirmation
   remains open.
   A stronger [local Codex session-metadata audit](P0_I_AI_TOOL_SESSION_METADATA.md)
   parses only project-task `session_meta` and `turn_context` rows at a fixed
   cutoff. Across 6 selected sessions and 379 target-model contexts, it verifies
   `gpt-6-astra` high/xhigh and `gpt-5.6-sol` high, and supports a project-task
   start date of 2026-09-10. The last observed date is 2026-09-15, but the work
   remains active, so no final end date is manufactured and the declaration
   remains owner-confirmed and open.
   The [current private build-gate verification](P0_I_CURRENT_PRIVATE_BUILD_GATE.md)
   also exercises the real Git-ignored owner input. It confirms that the file is
   no longer the empty template while proving that its 6-field failure occurs
   before transport access or output creation. No identity-bearing target
   artifact was created.
   A [current Springer Nature AI-policy alignment audit](P0_I_SPRINGER_NATURE_AI_POLICY_ALIGNMENT.md)
   now applies the publisher's 2026-09-10 risk-based policy and the
   Applied Intelligence journal-specific Methods-placement rule. The former
   candidate wording was incomplete because it omitted methodological-option
   review, statistical and numerical checking, interpretation stress-testing
   and prompt scope. A fuller candidate now records those uses and the retained
   human-verification boundary. The private target builder inserts an approved
   version into a Study-design Methods subsection rather than relying on a
   declarations-only paragraph. A fresh synthetic-identity build clean-compiled
   to 13 pages with zero nonembedded or Type 3 fonts; all 13 pages passed
   project-lead visual review. The candidate remains unapproved, its final use
   end date is unset, category-level prompt disclosure does not claim a complete
   verbatim transcript, and no real author-populated artifact was generated.
   P0-I therefore remains open.
   A subsequent [private root-user prompt-record snapshot](P0_I_AI_PROMPT_RECORD.md)
   reads only the one root user session at a fixed cutoff. It excludes all five
   subagent sessions, system/developer and assistant messages, tool I/O, 269
   automatic goal-context chunks, seven plugin-list chunks and 17 environment
   chunks. The resulting Git-ignored ledger contains 47 retained user-prompt
   chunks, 37 unique exact hashes and 9,785 raw characters; it stores redacted
   text, time, length and raw hashes, while the public receipt contains no
   prompt text, session identifier or absolute session path. One owner/email
   value was replaced. The private ledger is identity-minimized rather than
   anonymous because unaffected prompts can remain verbatim and may contain
   public project identifiers. It is a non-final snapshot: responsible-author
   content review, release approval, an editor-approved access route and the
   final use end date remain open, so it does not close P0-I.
   A provisional Discover Computing technical profile now also proves that the
   accepted source can be changed to 12 pt, flattened into a top-level LaTeX
   ZIP and compiled to a font-clean 12-page PDF without changing scientific
   prose or numbers. It is explicitly not a selected-journal or submission
   artifact; author, funding, APC, license, institutional CAS and final Astra
   gates remain open.
   The data-and-code statement now explicitly records the validated corrected
   candidate while retaining the missing persistent identifier, restricted
   private-review route and aggregate-versus-neural reproduction boundary. The
   rebuilt neutral and Applied Intelligence modern-preflight artifacts passed
   mechanical and complete visual review.
   The subsequent
   [data/code policy refresh acceptance](P0_I_DATA_CODE_POLICY_REFRESH_ACCEPTANCE.md)
   corrects the remaining publication-state wording: the public GitHub repository
   exists, while the final submission revision and permanent archive identifier
   remain unfrozen; restricted evidence is supplied only if requested through a
   channel designated or accepted by the handling editor. The current base PDFs
   pass 141 static checks and complete 14-page visual review. The current 12-page
   target preflight, two byte-identical ten-member private transports, and a
   13-page synthetic-only author-package build all pass their mechanical, font
   and complete visual checks. The selected transport archive is now
   `d55ffb74cb8f88a9ec261c9a414219f511d92bd10eb4d888f5dbaa185d1c681e`.
   The prior `f4279c...` transport and earlier synthetic builds remain immutable
   historical records. No real author package, release approval or submission
   authorization was created, so P0-G and P0-I remain open.
   The later historical-manifest disclosure rebuild also passed: the paper now
   records the byte-identical packaged manifest copy while retaining the lack
   of independent timestamp certification and all missing original-fit evidence.

## P1: material competitiveness improvements

- **P1-A -- CLOSED:** The
  [reviewer evidence map](REVIEWER_EVIDENCE_MAP.md) gives one ordered path
  through the compiled paper, anonymous aggregate package, private forensic
  scopes and preserved Phi/Mistral/ROA failures. Its independent verifier
  authenticates 196 repository records plus preserved withheld archive
  generations, the private target transport and the synthetic author-populated
  package in 1,491 checks, without
  scientific payload reads, fits or model forwards.
- **P1-B -- CLOSED:** The
  [reviewer cost and failure register](REVIEWER_COST_FAILURE_REGISTER.md)
  consolidates executed workload, non-additive timers and peaks, every missing
  deployment measurement, the distinction between 5% actions and full
  candidate-acquisition cost, primary negative results, stopped reader routes
  and material fail-closed engineering corrections.
- **P1-C -- CLOSED:** The manuscript, supplement and reviewer register retain
  ROA/HGB-only non-passes, the terminal Phi validation failure and the Mistral
  pre-engineering stop with explicit separation between technical status and
  scientific effect evidence.
- **P1-D -- CLOSED:** Frozen dataset and retriever breakdowns are present only
  in the supplement, use their 6,000-trace cell denominators, and are explicitly
  descriptive with no subgroup superiority Claim.
- **P1-E -- CLOSED IN PUBLIC-REPORTING SCOPE:** The
  [public CI acceptance](P1_E_PUBLIC_REPORTING_CI.md) records the preserved first
  failure, the corrected 49-check committed-surface verifier and the 38-check
  committed Applied Intelligence modern-preflight verifier. GitHub push and
  pull-request runs pass through the current owner-gate correction, portable
  LaTeX-lookup repair, official-template route and authoritative CAS-platform
  boundary; the latest retained successful functional head is `136bac1`. The
  exposed Ubuntu `LOCALAPPDATA` and absolute-`/tmp` traversal failures and their
  successful repairs are retained in the CI acceptance record. Private aggregate/statistical,
  historical-manifest and end-to-end neural reproduction remain explicitly
  outside this CI. The later
  [Discover preflight test-isolation corrigendum](P1_E_DISCOVER_PREFLIGHT_TEST_ISOLATION_CORRIGENDUM.md)
  preserves a 123-test/one-failure run in which the test rebuilt three tracked
  historical artifacts and the Submission gate rejected their changed hashes.
  The test now uses a cleaned temporary output root; the accepted tracked bytes
  were restored before further verification, and the subsequent complete CAS Q3
  discovery passes all 129 tests.

## P2: optional and currently closed

- Any new reader, method, feature, head, seed, budget curve or benchmark.
- New neural replay or experiments intended to improve significance.
- Cosmetic expansion before the P0 evidence/claim/journal gates close.

Primary rejection risks are a narrow empirical contribution, no new algorithm,
failure against HGB_ONLY_R, single accepted reader condition, incomplete original
fit provenance, incomplete standalone deployment cost and high Applied
Intelligence originality/desk risk.
