# Next confirmation: design and unresolved preflight — 2026-09-10

Research Lead design work. **NOT AN EXECUTABLE FREEZE.** No new IDs, final fits,
test outcomes or scientific results are authorized by this document alone.
This advances preparation while original-artifact replay is unavailable; it does
not waive replay or the contribution controls. Existing historical protocols,
decisions and confidence intervals remain unchanged.

## Candidate and comparator decision before new outcomes

Run the already frozen GBV_ONLY_R and HGB_GBV_R study first. If the full stack
is not supported, analyze that result and revise the contribution before spending
on confirmation; do not automatically nominate whichever method has the largest
opened-data metric. If ROA-FULL survives that review, freeze one deployment
recipe retaining its original logistic and disjoint-calibration structure.
Do not quietly deploy a five-model ensemble, refit after calibration, or change
the 5% batch cap. Upstream score models and their training provenance must be
included in the final method definition.

Confirmation should retain Keep, raw HGB, the GbV paired adaptation, both
supervised controls and ROA-NOGBV. Freeze the primary comparison hierarchy
before new labels: external verifier comparison and the strongest relevant
supervised control both matter. No primary-baseline selection after confirmation.
The final hierarchy, multiplicity treatment and deployment split require the
control results and are explicitly unresolved here.

## Freshness and resource plan

Inventory IDs only, excluding every historical fit, calibration, development,
evaluation, prompt-selection and inspection cohort. Include the opened V2 fresh
cohort now used for V3 development. Parent model-training sets must be traced.
Question groups retain all three retrievers. Record actual availability for
HotpotQA, 2WikiMultiHopQA and MuSiQue, including zero-availability datasets.

Reuse the strict ID-field reader from scripts/select_v2_fresh_ids.py, but do
not blindly run the old selector as a V3 protocol: it writes V2 status fields,
allows output replacement, and its availability loop omits datasets with zero
remaining IDs. A new adapter must require all three declared datasets and never
overwrite ledgers. No source-ID ledgers are available on this host yet.

The previous 1,500-question-per-dataset design is a compute reference, not a
power calculation for ROA. Neither five-seed standard deviations nor a median
development advantage determine confirmation sample size. Freeze sample size
only after an availability inventory and a question-level variance/planning
analysis from already opened data. Never enlarge or replace confirmation after
seeing its outcomes. Do not claim pretraining contamination has been ruled out.

Reuse the existing bounded retrieval setting if its construction is valid and
clearly described. Full-corpus or end-to-end unseen-domain claims require their
own evidence. Shared generation/repair outputs are computed once for all paired
arbitrators. Account separately for retrieval, generation, likelihood passes,
NLI/verifier passes and CPU scoring; a 5% switch cap is not a 5% compute budget.

## Statistical estimand: fixed actions versus a new batch

The V2 cluster_bootstrap function in scripts/evaluate_v2_vs_gbv.py resamples
question groups with their original actions fixed. Preserve that historical
analysis and describe its conditional scope. ROA is a batch top-K allocation
policy, so a new-batch analysis must also account for changed batch composition.

The proposed future analysis uses dataset-stratified paired question-cluster
resampling, retaining each question's three retriever siblings and all methods
on the same draw. The frozen model scores are never refitted. For each draw:

1. Draw question multiplicities within each dataset, preserving its question count.
2. Copy each question's multiplicity to all three trace rows.
3. Recompute K=round(0.05*N_all_resampled_traces), with the original Python rounding.
4. For each method, rank only eligible rows by its frozen scores and canonical
   tie-break; select up to K copies. Never use outcome labels to allocate actions.
5. Compute paired EM/F1 differences and Recovery/Damage/Net with multiplicities.

With rows already in score/tie order, if w_i is a row's multiplicity, the selected
multiplicity is s_i=min(w_i,max(0,K-sum_{j<i}w_j)). Duplicate copies of the same
trace share its score and outcome. This equals explicitly duplicating and sorting
the sampled batch, while avoiding large replicated ledgers. A tested arithmetic
kernel is in src/evaluation/batch_allocation.py. It is not a finished statistical
pipeline or a model-replay result.

The point estimate always uses the original once-only batch, with one copy of
each trace. Intervals from reallocating sampled batches concern this fixed model
under resampled batch composition; they still do not include model-training
uncertainty or establish broad domain transfer. Report fixed-action sensitivity
separately if retained; never choose the narrower interval after viewing results.
Bootstrap settings, interval construction and primary multiplicity control must
be frozen with the complete executable design before outcomes are opened.

## Final prelabel contract still required

Final fit/calibration recipe; source/model/config/environment hashes; complete
ID exclusions and available counts; sample size and planning assumptions;
retriever/pool/reader/generation settings; exact candidate and baseline policies;
cost budgets; primary estimands, comparisons, uncertainty method and decision
rules; all fixed secondary analyses; action seals before numeric outcome mapping.

No numerical significance result can be produced from the current aggregate
reports alone: joint per-question outcomes and method decisions are missing.
No universal numerical threshold constitutes CAS Q2 readiness. A final success
judgment must also assess contribution, fair comparisons, limitations and paper
claim consistency. **CAS Q2 STATUS: NOT READY.**
