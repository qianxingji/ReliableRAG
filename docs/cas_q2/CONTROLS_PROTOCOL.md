# Supervision-matched recovery controls, version 1
Research Lead design, 2026-09-10. DEVELOPMENT ONLY; not yet executed.

## Question

Does ROA-FULL provide stable value beyond supervised use of GbV alone, or a
minimal HGB+GbV combination? This checks contribution attribution without adding
a new candidate architecture or spending new retrieval/generation compute.

## Preconditions and authority

The user's project-lead delegation and "continue" instruction authorize this
bounded next design. Execution requires authenticated local artifacts and the
P0-1 numerical replay; these are evidence dependencies, not a request to repeat
the user's permission. Codex must follow this design and report discrepancies.

Before any scientific fit, record the commit and byte hashes of this protocol,
executable files, environment and the authenticated input manifests. Require
zero prior fits in the new namespace
`outputs/cas_q2/supervision_matched_controls_v1/`.
If that namespace already has scientific results, reconcile and reuse its
valid sealed execution; do not overwrite it or run a duplicate search.

## Exactly two new controls

| Name | Numeric fields | Missing flags | Retriever indicators |
|---|---|---|---|
| GBV_ONLY_R | gbv_margin | one | BM25, Dense, Hybrid |
| HGB_GBV_R | state_symmetric_hgb, gbv_margin | two | BM25, Dense, Hybrid |

Full ROA and NOGBV are sealed reference methods, not new search candidates.
Use the same eligible/scorable universe as ROA. R=1 iff normalized EM changes
0 to 1; no raw text, Gold support, dataset ID, sample ID, action membership or
sibling signals as predictors. IDs only join/group/tie-break.

Both controls use the original ROA fitting recipe unchanged: fit-only numeric
median imputation, fit-only population mean/std, unscaled binary indicators,
L2 LogisticRegression(C=1, solver=lbfgs, class_weight=None, max_iter=5000).
Disjoint Platt logistic(C=1e6, solver=lbfgs, class_weight=None, max_iter=2000)
on base logits. Reuse authenticated original handling of empty-feature or
zero-variance cases; if that behavior cannot be determined before fitting, stop
and report it rather than improvising. Require both classes in fit and
calibration; no redraw or class rebalancing.

## Population and exact splits

Only the already opened 4,500 question / 13,500 trace development cohort;
3,202 eligible/scorable rows. Use (dataset,sample_id) question groups and keep
all retriever siblings together.

Primary seeds: 20260917, 20260918, 20260919, 20260920, 20260921.
Outer fold:
`sha256("v3-dhc-outer-v1|<seed>|<dataset>|<sample_id>") mod 5`.
For outer fold f, split its outer-training pool:
`sha256("v3-dhc-outer-cal-v1|<seed>|<f>|<dataset>|<sample_id>") mod 5`;
0 is calibration, 1..4 fitting.

Require exact correspondence to the authenticated ROA SPLIT_MANIFEST and
membership records, including UTF-8 encoding and full-digest integer conversion.
No new seeds; no inner hyperparameter search; outer test outcomes never enter
fitting, imputation, scaling or calibration.

LODO is mandatory secondary development evidence, after primary outputs seal.
H is exactly musique, 2wikimultihopqa or hotpotqa. Fit/calibrate on the other two:
`sha256("v3-dhc-lodo-final-cal-v1|20260922|<H>|<dataset>|<sample_id>") mod 5`;
0 calibration, others fitting. Apply once to H.

Two controls x (25 primary + 3 LODO) = 56 base fits + 56 Platt fits = 112
scientific fit calls. Do not refit ROA references. Count any synthetic test fits
separately; a technical retry must preserve failure records and its cause.

## Frozen policy

K=round(0.05*N_all_trace_rows_in_partition), Python nearest/ties-to-even.
Rank calibrated recovery probabilities descending among eligible rows, with
(dataset,retriever,sample_id) stable ties. Select min(K,eligible_count);
otherwise Keep. No dataset quota, abstention, Damage head, MILP, threshold,
feature search or alternative action rate.

Use the same partition/cap for ROA, GBV_ONLY_R, HGB_GBV_R, raw HGB and raw GbV.
Reuse and authenticate saved ROA-FULL/NOGBV probabilities and actions.
Record monotonicity/ties of Platt calibration without replacing the calibrated
ranking. Preserve fold-rounding totals of 675/676.

Seal all action memberships before held-out metric computation.

## Metrics and attribution

For every fold and repetition:
actions, Recovery, Damage, Neutral, Net, EM/F1 change versus Keep;
ROA-FULL minus each new control; all datasets/retrievers/nine crossed cells.
Actions=R+D+Neutral; Net=R-D; delta EM pp=100*Net/N_all.
Pool folds only within a repetition; never treat repetitions as independent
confirmatory samples. Report all five repetitions, mean/sample std and median;
the std describes partition sensitivity, not a confidence interval on new data.

Predeclared secondary allocation sensitivity (no new fits): rank each control
inside each dataset x retriever stratum using exactly ROA-FULL's action counts
in that stratum. Freeze these actions before their metrics. Report separately
to distinguish within-stratum ranking from global allocation. Never replace the
primary same-total-cap comparison with the favorable secondary comparison.

Development attribution rule, evaluated against EACH of the two new controls:
- Success in a repetition requires ROA Net strictly higher AND Damage no higher.
- Strong support requires >=4/5 successes for each control, median EM difference
  >0 for each, and no LODO EM difference versus either below -0.10 pp.
- If all hold: COMPLEXITY_SUPPORTED_FOR_CONFIRMATION.
- Otherwise: SIMPLER_CONTROL_COMPETITIVE_REVIEW_CONTRIBUTION.

This is a new prospectively recorded development decision rule, not a CAS Q2
journal rule or a significance test. The second label is not proof of equivalence.
No outcome authorizes expanding features/models or choosing a favorable budget.
A competitive simple control triggers Research Lead review of the contribution
before costly final confirmation.

## Validation and outputs

Write only to the new namespace. Preserve all parent artifacts byte-for-byte.
Independent code must verify group membership, fit-only transforms, 56 saved
models and calibrators, predictions, actions, all reported arithmetic and the
decision. Do not import the main experiment executor as its oracle.

Required: INPUT_VERIFICATION.json, PROTOCOL_FREEZE.json, FEATURE_SCHEMA.json,
SPLIT_MANIFEST.json, MODEL_FIT_MANIFEST.json, saved model files,
PREDICTIONS_PRIVATE.jsonl, ACTIONS_PRIVATE.jsonl, PRIMARY_ACTION_SEAL.json,
OUTER_RESULTS.json, ALLOCATION_SENSITIVITY.json, LODO_TRANSPORT.json,
DEVELOPMENT_DECISION.json, AUTHOR_REPORT.md, INDEPENDENT_VALIDATION.json,
SEAL.json and SHA256_MANIFEST.json.

No new retrieval, generation, repair, likelihood/base-score extraction, raw Gold
access, confirmatory IDs or final full-development deployment fit. Cached numeric
outcomes are development labels only. Stop after sealing this bounded experiment.
