# Current task: research reassessment after authenticated replay and controls

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
