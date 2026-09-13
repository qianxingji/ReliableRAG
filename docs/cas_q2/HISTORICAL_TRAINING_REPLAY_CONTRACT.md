# Seven-estimator historical final-fit replay

Research Lead design, 2026-09-11. CAS Q2 STATUS: NOT READY.
Freeze this design before implementing or executing any new fit.

## Question and evidence boundary

Can the seven final saved mars_full estimators be reproduced using the original
fitting functions, ordered development ledgers, original feature schemas,
configuration and per-model seeds? This is a deterministic reproduction check,
not model selection, a fresh experiment or evidence of a new contribution.

The accepted upstream audit reconstructs 601 informative traces / 518 question
groups from 1,539 feature pairs and 7,200 development label records / 4,800
questions. Those development roles include original train, calibration, opened
pilot and MuSiQue development; none is newly designated untouched confirmation.
Seven original fit-time ID/matrix receipts remain absent. The old complete
mars_full manifest is self-consistent, with no independently recovered earlier
whole-manifest pin. The seven model bytes have separate authenticated V2 pins.
A successful new fit cannot supply missing chronological evidence or prove
the absence of unknown unlogged training or pretraining overlap.

Authenticate the existing upstream receipt (SHA-256
d368dc747ec8dbc6d2208e97e7bd2da8ecbebf1dcdda080f02d2317661c1ad47),
and the accepted static graph/restoration. Two training ledgers are absent from
that declared static graph; explicitly copy them byte-for-byte into a new
single-use stage input directory, without changing any sealed restoration root:

- features/development/pair_records.jsonl: 6,390,307 bytes,
  71bda250a6de3fa58aea98a578e02e66b86a9a3f1e13962d0219e42f10c54e5d.
- evaluation_only/development_labels.jsonl: 1,621,623 bytes,
  360510b18ebb6a132342895c702c20d269d4853296eec1633105957a69649ddb.

Both are relative to original outputs/mars_full. Their pins are the accepted
local-manifest/ledger reconstruction, not a newly discovered historical anchor.
All other used source/config/model bytes come from the accepted restored roots.

## Fixed source and fits

Original src/mars/full_experiment.py hashes to
65713509ef6c8d094bb44ad2c47b0238ceade607616d3e729b31c56096326d50;
src/mars/state_symmetric.py hashes to
3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717;
configs/mars_full.yaml hashes to
521d0b04cb1540460dfbee3718fc0264130c8d2e4117017fb2a8e7857bed6c8d.

Select the unchanged original matrix, selector, fitting and schema definitions
under their original module identities. Record every selected AST hash. Reuse
_fit_model without editing its body. Do not call the whole freeze_method CLI,
which would also repeat grouped CV, threshold selection and output writes.
Only its original final-fit invocation is in scope. Disclose selected-definition
assembly and physical input bindings instead of claiming unchanged full CLI.

Preserve pair-file order. Join labels by the original four-part _key; reject
duplicates, missing joins, nonfinite inputs, invalid schemas or changed counts.
Select precisely preference_label in (0,1). No shuffle, resampling or filtering
based on a new score. Seven fits, in MODEL_SPECS insertion order:

| Index | Model | Seed |
|---|---|---|
| 0 | state_symmetric_logistic | 20261829 |
| 1 | no_cross_state | 20261830 |
| 2 | no_B | 20261831 |
| 3 | no_evidence_change | 20261832 |
| 4 | no_answer_form | 20261833 |
| 5 | state_symmetric_hgb | 20261834 |
| 6 | ordinary_compact_logistic | 20261835 |

Seeds are original config seed 20260829 + 1000 + model_index. Use original
logistic_max_iter=4000, hgb_max_iter=300 and hgb_max_leaf_nodes=15. Original
functions determine augmentation (X,-X and y,1-y), scaling, intercept, class
weights, solver, HGB learning rate/l2 and library defaults. No parameter search.

Use the accepted new neural-package environment's authenticated numerical
libraries, one CPU thread and CUDA_VISIBLE_DEVICES=-1. Do not import neural
packages, construct pretrained models or occupy C3's GPU. A separately frozen
guard may permit only the seven declared top-level _fit_model invocations and
their nested sklearn fitting, logging model index, seed and actual input data
before each fit. The independent process must prohibit every fit. Keep the
accepted narrow Windows bootstrap and cleared-module-name guard handling.

Save ordered selected IDs/labels, all per-model raw design matrices and their
shapes/dtypes/hashes before fitting. Record each attempted top-level fit, seed,
parameters, source identity and completion/failure. Internal scaler/pipeline/
estimator calls are recorded separately; they are not additional scientific
model fits. A completed seven-model run adds seven actual reproduction fits
to the previous total 178. Count attempts honestly even if a run fails.

Save all seven returned models with original joblib.dump(..., compress=0) in
new output paths. Compare bytes directly against the seven original model pins;
never replace those expected hashes. Preserve each new model and the complete
comparison result even on mismatch. This byte check is deliberately strict:
failure alone does not establish a prediction or learned-parameter discrepancy.

## Independent acceptance and failure reporting

A separate process reconstructs membership, order, labels and every per-model
matrix directly from the two ledgers and the frozen schema. It must not call
the fitting producer or native matrix builder. Check complete unmodified source,
feature names, seeds and all seven attempted/completed fit receipts. Independently
hash original/new models. Load each authenticated original and new model under
its original class identity and compare scores on all 1,539 development feature
pairs: 10,773 comparisons. Require finite values, absolute error <= 1e-12 and
exact array shape/order; report actual maximum error. No action or threshold
selection is performed. Model-byte equality is a separate explicit requirement
for the full literal-artifact replay acceptance in this version.

Use invented/in-memory counterfeit records to verify rejection of reordered
training rows, changed design values and changed model bytes; no toy fits.
New receipts are not original historical records. The independent process
shares the original estimator implementation, not an independent tree learner.

Before/after, hash every original/relocated input, all 21,267 accepted environment
and target files, controllers and commands. Retain every partial output, stderr
and failure. Unexpected warnings, undeclared reads/writes or fit counts fail the
gate. On byte or numerical mismatch, do not retry with different seeds, row
orders, thread settings, libraries or tolerances; record the outcome and design
a separate diagnostic before any further execution. Do not overwrite this run.

Historical development label values are explicitly allowed solely for this
reconstruction and fitting. No historical test-label or current empirical
answer/score/Gold file is opened. The original C3 source, process and inputs
remain unchanged. P0 remains C3/replay/acceptance, C4/full prelabel, then cost/D
and contribution review. P1 adds this bounded training check plus remaining
BGE/predecessor/full neural delivery. P2 permits no search or manuscript work.
No possible result of this gate alone establishes CAS Q2 Submission Ready.
