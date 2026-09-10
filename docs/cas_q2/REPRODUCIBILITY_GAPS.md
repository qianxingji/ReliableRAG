# Reproducibility gap record

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

The authoritative private source remains E:/paper/ReliableRAG on the original
experiment machine, subject to matching hashes. Public source should contain the
reusable implementation and manifest references; private predictions or raw
data are not automatically authorized for public upload.
