# Current task: fixed-policy empirical replication after failed advancement gates

## Superseding execution contract — fixed empirical replication

Latest execution checkpoint (2026-09-11): original retrieval is complete and
independently accepted in [EMPIRICAL_C2_ACCEPTANCE.md](EMPIRICAL_C2_ACCEPTANCE.md).
All 18,000 traces passed 18,173 independent checks with exact saved-array
BM25/dense/RRF scores, rankings and Top-5 bindings. Canonical retrieval performed
15,422 BGE forwards and took 1,096.56 seconds. This is not a second full encoder
replay. Aggregate evidence: EMPIRICAL_C2_RESULTS.json.

C3 preparation and joint GPU preflight passed. The 18,000 complete trace inputs
and 180-trace replay membership were fixed before reader generation; two
invented answer generations replayed exactly. Canonical generation is now
running from commit cc304ee in outputs/cas_q2/empirical_runtime_v1 under
EMPIRICAL_C3_EXECUTION_ACCEPTANCE.md. Inspect process/receipts first; never
launch a duplicate pass. A missing BUILD_RECEIPT while the process runs is not
completion or a failure. Keep all durable partial ledgers on any failure.

Next P0: finish 54,000 canonical generations, execute the fixed 540-generation
bounded replay and full independent validator, then accept candidate-pair
acquisition. Prepare authenticated scoring while acquisition runs, without
reading generated answers for quality. Actual scoring/actions/prelabel sealing
and Gold outcome analysis remain pending. Total fits remain 178; both prior
advancement failures remain unchanged and no final novel-method candidate is
cleared. Historical upstream fit-time receipts are still incomplete.

Scoring preparation: EMPIRICAL_C4_SCORING_CONTRACT.md is frozen before scoring;
its read-only input audit passed 73 files / 880,110,248 bytes with zero model
loads or fresh branch reads. Subsequent CPU model compatibility passed:
EMPIRICAL_C4_CPU_ACCEPTANCE.md accepts seven saved upstream estimators, V2 and
five fixed parameter heads after 102 invented-input checks (max error
2.220446049250313e-16). Preserve the first import-cache failure and the separate
source-only IO correction. Likelihood/GbV witness and common-budget kernels are
implemented; the full repository suite passed 80/82 tests with two Windows
capability skips. Complete neural scoring adapters, real GPU preflights and
independent integration before fresh scoring; do not compete with running C3.
The latest timestamped snapshot is EMPIRICAL_C4_CPU_RESULTS.json (1,140 complete
candidate pairs at 2026-09-11 04:51:59 UTC), not a completion receipt.

P1: comparison fidelity, complete inference cost, contamination boundaries and
reproducible release. P2: no automatic feature/model/seed/budget search. CAS year,
institutional category rule and target journal are undecided by user choice;
this does not block experiments. CAS Q2 STATUS: NOT READY.

Earlier A/B acceptance entry, retained chronologically:

Read EMPIRICAL_REPLICATION_PROTOCOL_V1.md, EMPIRICAL_PANEL_ACCEPTANCE.md,
EMPIRICAL_AB_ACCEPTANCE.md and EMPIRICAL_SAMPLE_SIZE_CORRIGENDUM.md first.
Stages A/B are complete: five fixed comparison model bundles, ten additional
fits (178 takeover total), 57,388 independent checks with zero numeric error;
then 6,000 fresh ID-only questions with 111 independent checks and zero overlap
with 18,600 known exclusions. No fresh runtime/Gold outcomes have been projected
or evaluated. Original advancement failures remain unchanged.

Next: complete stage C's native gold-free projection/pool adapter and independent
validator, then retrieval/runtime/frozen scoring/prelabel sealing in new namespaces.
Value-blind source preflight is separate from actual projection or inference.
The scientific sample/model/statistical design is frozen; stage C/D executable
input freezes still require implementation and client Lead acceptance. Do not
blindly run old V2 executors with hardcoded roots and 1,500-question counts.
No external Work approval is awaited. CAS Q2 STATUS: NOT READY.

The earlier review state below is retained chronologically, not an instruction
to redo the closed work or ignore the new bounded scientific freeze.

## Current accepted state — 2026-09-11

**CAS Q2 STATUS: NOT READY.** P0-1 full saved-parameter replay passed; P0-2's
two controls and the subsequently frozen HGB-only attribution control are
complete and independently sealed. Total new scientific fits: 168. No new
retrieval/generation, final deployment fit or confirmation-ID selection occurred.

Read [P0_1_CLIENT_ACCEPTANCE.md](P0_1_CLIENT_ACCEPTANCE.md),
[P0_2_CONTRIBUTION_REVIEW.md](P0_2_CONTRIBUTION_REVIEW.md), and
[P0_3_RESEARCH_DECISION.md](P0_3_RESEARCH_DECISION.md) before choosing work.
The full-stack and two-signal advancement criteria both failed. Do not rerun
either sealed experiment, loosen its criteria, or start confirmation.

Read [EMPIRICAL_ROUTE_REVIEW.md](EMPIRICAL_ROUTE_REVIEW.md) for the completed
read-only cost and conditional precision audits and their scientific decision.
The method-novelty route is unsupported. An empirical replication requires a
complete claim-specific design; it is not automatically cleared for execution.
Next: design assessment for that bounded replication, plus read-only
provenance/availability and reproducibility preparation. No accepted final
deployment candidate or executable confirmation freeze exists. The engineering
worktree is `E:/paper/ReliableRAG-cas-q2-p0-1`; original data remain read-only at
`E:/paper/ReliableRAG`. All new private experiment namespaces are ignored by Git.

## Historical execution contract below (completed; retained for reproducibility)

Read PROJECT_CHARTER.md, CURRENT_METHOD.md, EVIDENCE_INDEX.json and
REPRODUCIBILITY_GAPS.md. Preserve all existing worktree edits and sealed outputs.
Chinese local execution and return instructions:
[LOCAL_CODEX_HANDOFF_ZH.md](LOCAL_CODEX_HANDOFF_ZH.md).

## P0-1: authenticate and replay the original implementation

Run on the machine containing the original project artifacts:

```powershell
python -m scripts.verify_roa_artifacts --project-root E:/paper/ReliableRAG
```

Optionally add `--output E:/paper/roa_artifact_check.json` with a new filename
outside the sealed namespace. Exit 0 means hashes/coverage matched only;
exit 2 means a missing, changed, unsafe or invalid artifact. Do not repair hashes,
overwrite parent files, or substitute same-named files.

After integrity passes:
1. Read the authenticated original design.py, learning.py, metrics.py, execute.py, independent.py
   and their local imports before extracting reusable implementation.
2. Follow INPUT_VERIFICATION.json / EXECUTABLE_CONFIG_FREEZE.json to parent
   score/outcome files and environment. Verify their full original manifests.
   The new checker covers the ROA namespace only, not all upstream dependencies.
3. Trace every learned base score to its training IDs, artifact and historical
   cohort role. Any unknown overlap remains a provenance gap.
4. Preserve the original namespace byte-for-byte. Port necessary code into
   versioned src/scripts using the original algorithms, not a protocol-only
   reimplementation claimed as equivalent.
5. In a separate output directory replay saved model coefficients/calibrators,
   preprocessing, group splits, probabilities and actions; no scientific refit.
   Cover every row required by the original validator across all 28 partition
   contexts and both variants. A sampled check is not full replay acceptance.
6. Use a second implementation to compare numeric outputs at the existing
   1e-10 tolerance and exact action membership. Explain platform issues; do not
   silently alter scores, tolerances or ties to force a pass.
7. Bind actual source commit, dependency versions, model/input hashes, command,
   outputs and limitations in REPLAY_VALIDATION.json.

Do not run archived execute.py or run_stage.py blindly: they may refit models or
write to the sealed namespace. Inspect them and build a read-only replay path.

Deliver a code PR and replay report. If the host cannot access the artifacts,
report that boundary; do not fabricate a replacement dataset or a replay PASS.

## P0-2: execute the reviewed control design

Follow CONTROLS_PROTOCOL.md after P0-1 integrity and numerical replay are accepted.
This protocol is the Research Lead's bounded development design. It permits the
two control fits, not final-model fitting or fresh-ID selection. Authenticate
the original split manifest; preserve its exact namespaces and seeds.

## Stage report

CAS Q2 STATUS: NOT READY, unless all project-wide submission criteria actually pass.
Report method/baseline/experiment/argument gaps separately.

Immediate priorities:
- P0: acquire/authenticate/replay private runtime and scores, then compare the two controls.
- P0: final-candidate confirmation after a frozen design and contribution review.
- P1: targeted external validation and current-method cost/error analysis.
- P2: no larger models, broader searches or cosmetic expansion at this stage.
