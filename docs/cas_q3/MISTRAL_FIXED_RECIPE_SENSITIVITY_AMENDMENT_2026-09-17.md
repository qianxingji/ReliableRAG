# Mistral fixed-recipe sensitivity fit amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `FROZEN_BEFORE_DEVELOPMENT_GOLD_OR_SCIENTIFIC_FIT`.

## Reason for the amendment

The frozen Mistral protocol designates the development-selected logistic head
as primary and the original `C=1.0, class_weight=None` recipe as a descriptive
sensitivity. The first implementation executed all cross-validation candidates
but retained an all-fit plus calibration model only for the selected candidate.
If another candidate won, that implementation could not produce the promised
fixed-recipe test sensitivity from a model fitted on the prescribed full fit and
calibration partitions.

This mismatch was found during engineering review before any Mistral project
Gold value was opened and before any scientific head fit ran. The active
`a0_query` acquisition is label-free and cannot inform this change.

## Frozen correction

The correction does not change the hyperparameter search:

- three methods use the same eight candidates and the same three question-group
  folds;
- 72 cross-validation fits, three selected full-fit base refits and three
  selected-model Platt fits remain the complete 78-fit search workload;
- after selection, each method also fits the already fixed
  `C=1.0, class_weight=None` base on the identical full fit rows and one Platt
  layer on the identical calibration rows;
- these six fixed-reference fits do not contribute to candidate loss,
  tie-breaking, primary-model selection or action-budget selection.

The formal producer therefore performs 84 fit attempts and emits 168 ordered
start/terminal events. The independent validator reconstructs and repeats all
84 fits as numerical audit work, making 168 producer-plus-validator attempts.
All failed and successful attempts remain in the journal.

## Interpretation lock

The development-selected recipe remains primary. The fixed recipe remains a
labelled descriptive sensitivity outside the four-endpoint confirmatory family.
It cannot replace the primary recipe after test inspection. The candidate grid,
folds, development roles, common eligibility mask, test allocation and
multiplicity family are unchanged. Test inputs, test outcomes and test action
budgets remain inaccessible during development tuning.

The corrected core, producer and independent validator pass their focused tests
and the complete 81-test Mistral suite. Those are engineering checks only; they
are not scientific evidence and do not change the current submission status.

## Stage accounting

- P0: implementation and prospective protocol amendment complete; formal
  development acquisition and ordered validators remain in progress.
- P1: after accepted development inputs, run the 84 producer fits and 84
  independent audit refits, retain all development results, then seal the test
  execution contract.
- P2: update the manuscript and public release only from independently accepted
  scientific results.

Primary rejection risks remain a small or uncertain increment over
`HGB_ONLY_R`, rare Damage, one repair operator, known question identities,
transferred historical HGB provenance and public neural reproduction cost.
