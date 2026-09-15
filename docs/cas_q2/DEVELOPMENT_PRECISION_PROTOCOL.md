# Research Lead: conditional precision audit, 2026-09-11

CAS Q2 STATUS: NOT READY. This is a read-only development analysis, frozen
before its resampling outputs. It neither changes the two failed advancement
rules nor authorizes a final fit, fresh sample selection or confirmation.

The current empirical-study route needs an estimate of how much the available
paired evidence can resolve. Means over five overlapping repetitions are not
five independent replications. Nor can small observed differences establish
equivalence. Estimate conditional sampling variation from the actual opened
question-level records, with batch reallocation, before deciding whether further
confirmation is scientifically useful.

Use only the sealed HGB-only study's aggregate predictions, actions, splits and
results (manifest cec3d2c2f085225c3995792a7839f6acbec6fac8b75edd8463ac18b9e2a75a8e)
and the original opened numeric outcomes (already authenticated by ROA).
No model training, coefficient changes, threshold changes or new data access.

Retain every seed 20260917..20260921 separately and every outer fold. Never pool
scores from differently calibrated fold models into a single ranking. All three
retriever traces belonging to a question move together. Resample with replacement
within each original dataset-by-outer-test-fold stratum, preserving its question
count. Use the same multiplicities for every compared method. For every fold and
draw, recompute its cap with Python round(0.05 * all resampled trace rows), rank
eligible rows by the original calibrated scores and (dataset,retriever,sample_id),
and select copies using the validated weighted_top_k kernel. Aggregate totals
over folds within a repetition. This conditional procedure does not refit models
and does not represent uncertainty of a newly fitted deployment model.

Freeze these three paired differences and two endpoints:

1. ROA-FULL minus HGB_GBV_R: EM gain and Damage rate, in percentage points.
2. HGB_GBV_R minus HGB_ONLY_R: the same endpoints.
3. HGB_GBV_R minus GBV_ONLY_R: the same endpoints.

Damage denominator is all traces, consistent with EM gain; raw event differences
are also retained. Positive Damage differences are harmful. Reconstruct the
unresampled action membership exactly from each original action ledger and
reconcile point estimates with sealed five-repetition totals before resampling.

Run exactly 2,000 draws per repetition using NumPy default_rng with integer
seed 2026092300 + repetition index (0..4); record NumPy version and source hashes.
Save all draws locally and report the unresampled point, draw standard deviation
(ddof=1), and 2.5/97.5 percentiles with NumPy's linear quantile method. Label these
conditional exploratory bootstrap ranges, with no multiplicity-adjusted
superiority, noninferiority or equivalence declaration. Do not select a seed,
pick the narrowest interval or use these outcomes to modify a model or budget.
Do not combine five ranges as independent evidence.

The analysis excludes LODO resampling: it adds no domain-generalization claim and
leaves all existing LODO gate results untouched. It provides a planning limitation,
not a numerical prescription for fresh sample size. A final sample size requires
a separately reviewed single-model recipe, primary estimands, scientifically
justified minimum effects/margins and assumptions about the future population.

Implementation must use a new output directory, read only authenticated files,
preserve failures and record zero new scientific fits/inference/outcome acquisition.
Validate the replicated-batch allocation against explicit copy expansion on a
fixed first draw for each of the 25 folds. That check must compare selected trace
multiplicities, not just summary numbers.
