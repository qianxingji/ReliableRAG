# Client review: original final-fit replay and HGB byte discrepancy

CAS Q2 STATUS: NOT READY. **The frozen seven-model byte gate remains failed.**
Six files are exact; the seventh differs only in the persisted bin-mapper thread
count. Full development score comparison and learning-state observations match.

The [training contract](HISTORICAL_TRAINING_REPLAY_CONTRACT.md) preceded
implementation 3160704. The failed run remains sealed at
`e85024fc8e697cf9f69220d90c85a944027f14a9cef3c7624f463ff75981cc84`. No seed, expected hash, input order or tolerance was changed.
No model was retrained after the failure, and original models remain in use.

## Actual reproduction

The seven original final-fit calls completed on 601 ordered informative traces /
518 question groups, reconstructed from 1,539 historical feature pairs and 7,200
development labels. Seeds are 20261829 through 20261835 in original MODEL_SPECS
order. These are original train/calibration/opened-pilot/MuSiQue-development
records, not newly untouched confirmation. Seven reproduction fits bring the
takeover total to 185 (178 control/panel fits plus these seven); nested scaler,
label-encoder, pipeline and estimator calls are recorded separately.

The independent process verifies all seven input matrices / 140,033 scalar
values, ordered membership, labels, schemas and actual per-fit records. It
checks all 10,773 original/new scores on the complete 1,539-pair development
universe, plus 10,773 new/producer scores. Both maximum errors are zero at the
unchanged 1e-12 tolerance. Three counterfeit checks reject reordered rows,
changed matrix values and changed model bytes. Six logistic-family artifacts
match their original hashes exactly; HGB alone does not.

All 13 original/relocated used inputs, 21,267 environment/target files and eight
controls remain unchanged. Both fit/validation stderr logs are empty. All 15
selected source AST records in each process were rechecked by the client.
The new environment uses NumPy 2.2.6, SciPy 1.15.3, sklearn 1.7.2 and joblib
1.5.3; one CPU thread is explicitly fixed. No neural forward or fresh/historical
test Gold access occurs. Historical development labels are read only within
the prospectively permitted training scope. No CV or threshold search repeats.

## Separately completed HGB diagnosis

The [read-only diagnostic contract](HISTORICAL_HGB_BYTE_DIAGNOSTIC_CONTRACT.md)
authorizes no fit, prediction, scoring or ledger read. Both HGB files are
639,652 bytes. Independent client byte comparison finds exactly one differing
offset, 4820: 6 versus 1. Complete pickle-state observation visits 136,341
values, 312 objects and 4,856 arrays per model. The only state difference is
`model._bin_mapper.n_threads`: original 6, reproduction 1. All observed learning
arrays, raw array hashes, named tree fields and other state values match exactly.
The client independently compared both complete state JSON files and all 15
diagnostic source AST records; it did not rerun training or scores.

Authenticated installed sklearn source explains this field: gradient_boosting.py
line 643 obtains the effective OpenMP thread count; lines 713-718 pass it to the
bin mapper. binning.py line 171 stores it, and lines 235/287 use it for binning
work. The difference records an execution setting. This observation does not
rewrite either model or waive the original literal-byte criterion; it is not
evidence of a learned-parameter difference or a guarantee for unseen inputs.
The two source hashes and complete state/byte observations are in the private
client review and [release results](HISTORICAL_TRAINING_REPLAY_RESULTS.json).

Diagnostic v4 seal: `b1330d58e74e7d2d1376644bce33987b6e588ab741f0ecf0319b75653a451084`. Its two artifacts, source inputs,
21,267 environment files and eight controls remain unchanged. It makes two
model loads and zero fit/score calls; stderr is empty. Three failed observers
are preserved: v1 lacked slots support; v2 could not identify an extension
callable; v3 rejected the native loss class's reported _loss alias. The
[state](HISTORICAL_HGB_STATE_OBSERVER_REFINEMENT.md),
[global reference](HISTORICAL_HGB_GLOBAL_REFERENCE_REFINEMENT.md) and
[exact native loss identity](HISTORICAL_HGB_NATIVE_LOSS_IDENTITY_REFINEMENT.md)
refinements were each frozen before their respective implementations. No
scientific model, parameter, score or original byte was changed to resolve them.

## Research judgment and next gates

This is new original-function final-fit reproduction with explicit source
assembly and IO/thread bindings. It improves evidence for the reconstructed
training recipe. It does not recover seven original fit-time ID/matrix receipts,
an earlier independent whole-mars_full manifest pin, unknown unlogged activity
or pretraining overlap. The two supplementary training ledgers remain supported
by the earlier local-manifest reconstruction, not a recovered historical anchor.
No original full CLI, historical CV selection or complete neural pipeline is
claimed replayed. Keep the original HGB/comparators and current fixed panel.

Main rejection risks: no cleared novel candidate, unfinished fresh empirical
results and these provenance limits. Both prior advancement failures remain.
P0: finish original C3, fixed replay/acceptance, actual C4/full prelabel, then
cost/D and contribution review. P1: remaining BGE/predecessor/full neural
delivery; report the literal byte difference explicitly. Do not refit merely
to force identical thread metadata. P2: no model/feature/seed/budget search;
CAS year, institutional category and journal remain user-undecided.
