# Research Lead scientific freeze: fixed-policy empirical replication v1

Effective 2026-09-11. **CAS Q2 STATUS: NOT READY.**

## Decision and change of research claim

Approve a bounded empirical replication of supervision/complexity attribution,
not advancement of a novel algorithm. This is the client's Research Lead design
under the user's project mandate. It follows EMPIRICAL_ROUTE_REVIEW.md and
supersedes its prohibition on fitting/selection only for the stages below.
The ROA-FULL and minimal-fusion advancement failures remain final historical
decisions. No new result can retroactively pass them.

The question is: on new questions with a fixed repaired-answer acquisition
pipeline, what incremental EM and Damage differences remain between the complete
stack, two-score fusion and supervision-matched single scores? Every sign and
inconclusive interval is reportable. No model is renamed. HGB_GBV_R is the focal
empirical policy, not a newly invented method or a cleared universally robust
deployment recommendation. A replication does not by itself establish CAS Q2
novelty or submission readiness.

## A. One fixed development fit, then immutable models

Use all 4,500 already opened questions / 13,500 traces and the 3,202 eligible
pairs, from the authenticated original ROA numeric feature file and original
fresh_numeric_outcomes.jsonl (now development data). Preserve the feature order
and all original parent hashes. Exclude no failed/equal/empty pair from the
all-trace population. Only eligible pairs enter supervised fitting, as before.

Within each dataset, sort its 1,500 (dataset,sample_id) groups by ascending
SHA256 of UTF-8 `cas-q2-empirical-fit-v1|20260924|<dataset>|<sample_id>`, then
sample_id. First 300 groups are calibration; remaining 1,200 are fitting.
All three retrievers remain together. Thus exactly 3,600 fit and 900 calibration
questions. No label stratification, favorable seed choice or alternative split.
Require both Recovery classes in eligible fit and calibration; otherwise fail
without redraw. There is no internal test subset or held-out performance claim.

Fit exactly five heads, each with one base and one disjoint Platt fit:

| Policy | Original numeric indices | Final width |
|---|---|---:|
| ROA-FULL | 0..10 | 25 |
| ROA-NOGBV | 0..9 | 23 |
| HGB_GBV_R | 0,10 | 7 |
| HGB_ONLY_R | 0 | 5 |
| GBV_ONLY_R | 10 | 5 |

Use the original base and calibration recipe exactly: fit-only median, mean
and population std (zero std -> 1), missing flags and unscaled three retriever
indicators; L2 logistic C=1, lbfgs, max_iter=5000, tol=1e-4, no class weights;
Platt C=1e6, lbfgs, max_iter=2000, tol=1e-4 on calibration logits only. Recovery
is a0_em=0 and a1_em=1. No dataset ID, answer/outcome text, sample ID or action
membership is a predictor. No refit on fit+cal, ensemble, added features,
parameter tuning or upstream model retraining.

Count exactly ten new scientific fit calls. Any synthetic fit is forbidden in
preflight tests; use contract and arithmetic fixtures. Existing 168 fits remain
in the project ledger. Historical learned inputs keep their authenticated model
bytes and documented reconstructed training provenance; their missing original
fit-time receipts do not become resolved by these new head receipts.

Save the explicit fit/calibration IDs, feature and target matrix hashes, call
events, coefficients, transforms, calibration parameters, versions and command
before any fresh-ID selection. A labeled `probe` may score all opened development
features solely to independently replay the saved parameters. It deliberately
overlaps fit/cal; it is not a test fold. Do not calculate probe quality metrics,
select actions on it, or compare the five new models by development performance.
Keep every fitted model independent, never average their scores.

Single-use namespace: outputs/cas_q2/empirical_fixed_panel_v1 in the isolated
worktree. A separate validator must import neither executor nor fitting module,
reconstruct every input transform/matrix/target hash and every eligible probe
logit/probability from saved coefficients, verify exact group separation and all
ten call receipts, using the existing 1e-10 numeric tolerance. Original and prior
control artifacts remain unchanged. Model selection on fresh results is forbidden.

## B. Fresh ID-only cohort and sample-size rationale

After A passes independent acceptance, select exactly 2,000 IDs per dataset
(6,000 questions, 18,000 eventual retriever traces). Reuse the authenticated
source-ID ledgers from COHORT_FREEZE.json and exclude the complete 14,100-question
historical union plus all 4,500 newly developmentized questions. Verify complete
source/exclusion hashes and the cohort-freeze anchor against the accepted
upstream audit; do not trust an unpinned local replacement manifest.

Sort available IDs by SHA256 of UTF-8
`cas-q2-empirical-fresh-v1|20260925|<dataset>|<sample_id>`, then sample_id; select
the first 2,000. This is a prospectively fixed deterministic hash sample, not a
claimed randomized probability sample. Inventory/selection uses ID fields only.
No replacement reserve, post-outcome enlargement, favorable stratum filtering,
reader-success screening or second draw. Keep failures in their original rows.
If availability falls below 2,000 in any dataset, stop and preserve the failure.

The balanced maximum is constrained by 2,105 remaining HotpotQA IDs; 2,000 is
the largest multiple of 100 below that limit. The decision prioritizes one
bounded measurement study over sequentially searching for significance. The
opened-data precision audit provides planning SDs, not final-model power. Report
normal-approximation sensitivity at n=6,000 using each endpoint's worst SD across
all five repetitions, scaled by sqrt(4500/6000), and uncertainty multipliers
1 and 1.5. Use z_(1-0.05/(2*6)) for the six primary interval endpoints. This is
a transparent planning approximation conditional on score stability, not a
promised power or achieved precision. The finite available frame, new model and
new retrieval pool can change variance/effect size. No equivalence/noninferiority
margin or minimum detectable effect is retrofitted to the observed means.

## C. Fixed acquisition and comparison policies

This scientific design fixes acquisition before any new outcomes. Stage C may
start only after its engineering adapter passes value-blind schema checks,
source/model/prompt/environment hashing, protected-file checks and a complete
executable freeze. A and B do not authorize blindly executing old V2 scripts.

Build one dataset-specific deduplicated candidate pool from the 2,000 selected
questions' supplied public contexts, using the authenticated native gold-free
projection and pooled-corpus builder. HotpotQA uses the full validation runtime
projection; 2Wiki dev and MuSiQue train use the previously authenticated source
bytes and projection parser. Materialize only ID/question/document fields.
Gold answers/support/decomposition remain inaccessible to runtime. No gold-based
pool filtering, support injection, per-method pool or full-Wikipedia claim.
Changing pool contributor count from 1,500 to 2,000 is explicit; the result
concerns a new bounded benchmark-derived pool, not identical retrieval outputs.

Use the exact existing native BM25, BGE dense and hybrid RRF configuration from
runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json and its retrieval parent, with
all non-cohort scientific parameters unchanged. Pin BGE revision
a5beb1e3e68b9ab74eb54cfd186867f64f240e1a and Qwen2.5-3B-Instruct revision
aa8e72537993ba99e69dfaafa59ed015b17504d1, the existing answer/repair prompts,
greedy decoding, 48 answer/64 repair-query token caps and 16,000 character
context budget. Shared original/repair candidate acquisition runs once for all
policies. Use the same four likelihood cells, BGE answer embedding and historical
score definitions. GbV keeps its exact published paired adaptation, chunking,
resolved entailment label and pinned DeBERTa revision
5a4338ab2151dc8db04ad53b42b6153382bf4f99. Never call an E0/E1 margin TrustMargin.

Compare Keep; raw HGB; paired GbV; the five newly fixed supervised policies;
and the existing sealed V2 comparator, without refitting it. The five-head panel
shares the same development labels/split/recipe, and every policy uses the same
candidate pairs. Pin every upstream model before scoring. Label budgets and
inference dependencies differ for raw/pretrained references and must be stated.

For the primary balanced 18,000-trace batch, use K=round(.05*N_all)=900; rank
eligible pairs by each frozen score, canonical (dataset,retriever,sample_id)
ties; select min(K,eligible_count), otherwise Keep. Keep selects no switches.
No positive-score threshold, dataset quota or per-model eligibility. The total
cap and all primary actions are sealed before outcome mapping. Score/pair
failures use the prior common fail-closed eligibility rule, remain in N_all and
must not produce method-specific deletions. Unexpected score asymmetry stops
the prelabel stage for a documented technical correction, not scientific tuning.

Record retrieval components, generation calls/tokens, likelihood/NLI forwards,
cache state and stage timers. Logical switch budget is not compute budget.
Historical scaled wall times are scheduling references only; record actual
new costs. No second reader or additional benchmark is silently added.

## D. Outcome mapping and frozen analysis

Only after all prelabel inputs, fixed model artifacts, complete predictions,
eligibility and exact actions pass an independent audit and are sealed may a
separate process map selected IDs to the same normalized EM/token-F1 evaluator.
It cannot change acquisition, scores or actions. All selected questions and
three retrievers remain in the analysis. Unexpected incomplete generation/data
is an engineering failure to reconcile, not permission to drop hard examples.

Primary paired comparisons: FULL minus HGB_GBV_R; HGB_GBV_R minus HGB_ONLY_R;
HGB_GBV_R minus GBV_ONLY_R. Each reports EM difference and Damage-rate difference
in percentage points with denominator all traces: six prespecified endpoints.
Positive EM is favorable; positive Damage is unfavorable. Report point estimates,
Recovery/Damage/Neutral/Net counts, and the complete six-interval family.

Use 20,000 NumPy default_rng(20260926) bootstrap draws, sampling 2,000 question
groups with replacement within each dataset, carrying all three siblings and
all policies together. Hold models and realized candidate pools fixed; never
refit or rebuild a pool within a draw. Reallocate top-K over each resampled whole
batch with Python rounding and calibrated score/canonical ties. Use the tested
weighted-copy kernel and independent explicit-copy checks. Primary intervals
are linear percentile [0.05/(2*6), 1-0.05/(2*6)] for each of six endpoints, a
Bonferroni adjustment with approximate bootstrap coverage, not an exact finite-
sample guarantee. Also report unadjusted 95% ranges, visibly secondary.

Directional claims require the relevant adjusted range to exclude zero in that
direction. Joint Net-improvement/Damage-reduction claims require both endpoints;
otherwise report the tradeoff/inconclusive result. Do not interpret failure to
reject as equivalence. No single statistical gate yields Submission Ready.

Fixed secondary outputs: all-policy EM/F1 and transition counts; dataset and
retriever cells under the primary globally allocated actions; allocation counts;
and fixed-action bootstrap sensitivity using exactly the same draws. Never pick
the narrower interval. No new budget curve, LODO refits, subgroup-based model
selection or exploratory hypothesis promoted to primary. Existing LODO failures
remain separate development findings; this design does not claim unseen-domain
or reader transfer. Its inference is conditional on the fixed trained panel,
realized bounded pool and the sampled batch construction.

## Execution and acceptance ledger

A and B are implementable now under this scientific freeze. Implement and test
their exact adapters, commit, then run once into new namespaces. Do not run C/D
until their complete engineering input freeze exists and passes client Lead
acceptance; this is an evidence dependency, not an external permission request.
Any new scientific amendment after A/B is a new version with rationale and
chronology; never rewrite this protocol or erase previous results.

P0 still includes actual fresh replication, credible contribution, original
upstream receipt limitations, official CAS journal identity/category/year and
institutional recognition, and a claim-consistent submission package. P1 is
external comparison fidelity, cost/release quality and justified replication
breadth. P2 excludes automatic model/feature/seed/budget expansion.
