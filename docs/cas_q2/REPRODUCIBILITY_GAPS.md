# Reproducibility gap record

## Latest host review — 2026-09-11

The historical access failures below described the prior host. On the original
machine, 216/216 ROA payloads now authenticate and both full replay paths pass
with zero maximum error. Fourteen upstream manifests and 16,291 unique files
were checked. The two supervised controls and one subsequent HGB-only control
were executed and independently validated. See P0_1_CLIENT_ACCEPTANCE.md,
P0_2_CONTRIBUTION_REVIEW.md and P0_3_RESEARCH_DECISION.md for exact scope.

Remaining historical gaps: no original per-estimator fit-time ID/matrix receipts
for seven upstream models; no earlier independent pin for the full mars_full
manifest. Training membership is source/ledger reconstruction, with zero observed
overlap with ROA questions. No pretraining decontamination or original upstream
training replay is claimed. Final-candidate/confirmation and scientific-contribution
gaps remain; CAS Q2 STATUS: NOT READY.

## Historical prior-host notes (retained verbatim)

## Verified in this continuation

- A source checkout at cd066597 is available.
- The uploaded ROA manifest authenticates to
  0921b3b15be2a58b7863911e60cd4ce10cb2b063055dda9823508c3ab2e6a8d6.
- It inventories 216 payload files, 54,435,934 bytes, excluding the manifest itself.
- The separately supplied independent-validation JSON matches the manifest entry
  4a809efaf38de9c14e7df696d803a88bf4bab1d1226a688f08813810d90206b7.
- Current source checkout does not contain that private runtime/model/prediction
  namespace. Protocols and PASS reports are available; full replay inputs are not.

## Remaining blockers

| Gap | Required evidence | Current status |
|---|---|---|
| Original runtime | Hash-matching design/learning/metrics/prepare/execute/independent files and imports | Not present on this host |
| Model/prediction replay | 56 models across 28 contexts, preprocessing, splits, scores and saved outputs | Not run here |
| Upstream provenance | Original model training IDs and all parent score/outcome manifests | Not fully traced here |
| Environment | Exact fit/runtime dependency records, numerical backend, command | Must recover from original receipts |
| Deployment definition | Final fit/calibration recipe and batch allocation | Not frozen |
| Fair supervised controls | Two models in CONTROLS_PROTOCOL.md | Not executed |
| New confirmation | Frozen candidate and genuinely untouched evaluation cohort | Not selected or executed |

This change implements an artifact integrity check only. It does not replace
the original numerical validator or claim that the scientific results were
independently rerun in Work.

## Engineering validation, 2026-09-10

`python -m unittest tests.test_roa_artifacts -v`: 10 tests passed. These use
synthetic byte-integrity fixtures only, with zero scientific fits. They check
read-only success, missing/tampered payloads, manifest trust, extra files and
case aliases, traversal/duplicates, incomplete seals, symlinks, copied manifests,
and report destination protections. `git diff --check` also passed.

The CLI was exercised against the authentic uploaded manifest and this checkout:
exit 2, integrity FAIL, 216 expected payloads, 0 verified; all 216 payloads,
the original namespace manifest and the namespace itself are unavailable.
This is an availability failure on this host, not evidence that the original
experiment files were corrupted. Numeric replay remains NOT_RUN; CAS Q2 status
remains NOT READY. No retrieval, generation, base scoring or scientific fitting
was run in this continuation.

## Subsequent autonomous preparation

The original AUTHOR_REPORT.md was obtained separately and its pinned hash
matched. All 40 aggregate rows were rechecked; the paired five-repetition
mean/sample-standard-deviation summary is in REPORT_RECHECK.json. This checks
reported arithmetic only and does not reconstruct F1 from predictions.

The local-only ZIP packager has five synthetic-fixture tests in addition to the
ten existing integrity tests. Round-trip authentication and refusal to overwrite
files or package changed artifacts passed. A future batch-reallocation arithmetic
kernel has four tests, including comparison against 100 explicitly replicated
toy batches. These 19 tests are engineering evidence; there are still zero new
scientific fits, retrieval/generation calls or ROA numerical replays.

Source inspection also identified that the old V2 ID availability loop omits
datasets with no available IDs, and its bootstrap retains old action selections.
The confirmation design documents these reuse boundaries; historical source and
results were not changed. Final confirmation is not executable until its data,
deployment recipe and complete analysis protocol are frozen.

The authoritative private source remains E:/paper/ReliableRAG on the original
experiment machine, subject to matching hashes. Public source should contain the
reusable implementation and manifest references; private predictions or raw
data are not automatically authorized for public upload.
