# Client Research Lead acceptance — 2026-09-11

**CAS Q2 STATUS: NOT READY.**

Decision: **ACCEPTED_FOR_BOUNDED_DEVELOPMENT_CONTROLS**. This is the client's
Research Lead decision under the user's explicit delegation. No external Work
approval is required. It accepts authenticated cached inputs and full saved-
parameter replay for the two controls already frozen in CONTROLS_PROTOCOL.md;
it does not accept submission readiness, new confirmation, a final deployment
model, complete historical fit reconstruction or pretraining decontamination.

## Evidence actually executed

- Original workspace: `E:/paper/ReliableRAG`, historical branch at `cd066597`;
  uncommitted edits and all sealed outputs preserved. Engineering worktree:
  `E:/paper/ReliableRAG-cas-q2-p0-1`, continuing `ca71e77` without reset.
- ROA integrity: 216/216 payloads, 54,435,934 bytes, pinned manifest
  `0921b3b15be2a58b7863911e60cd4ce10cb2b063055dda9823508c3ab2e6a8d6`.
- Byte-preserving local review ZIP: SHA-256
  `62af0b191f7e4bb25f452b4832aeb981ad43aafdb4ffc128f24f7c61ad27a2e3`.
- Parameter replay implementation commit `8ecba4cd2ef388e782fea5b06171d61e9e8b42a5`:
  28 contexts, 56 bundles, 38,424 eligible model-prediction rows; max logit,
  probability and metric error 0; exact selected membership in all contexts.
- Separate process running byte-authenticated original `independent.py`:
  2,744,203 checks, max numerical error 0 at unchanged tolerance 1e-10.
  All 67,500 primary and 13,500 LODO rows in each aggregate prediction/action
  ledger, fit-only transforms, fit-call design/target hashes, group splits,
  subgroup summaries, calibration ranking and development decision verified.
- Both replay reports bind clean source commit, command, package versions,
  numerical libraries, original source hashes, model hashes and post-run
  original-payload verification. No original executor was run; new scientific
  fits, retrieval, generation and base-score extraction were all zero.
- Upstream audit commit `7e1b9e9`: 14 complete anchored namespaces verified,
  including prior blocked attempts; 16,291 unique files / 11,266,850,841 bytes
  additionally checked across upstream artifacts and model inventories.
  One technical adapter failure on nested cache-copy records is retained as
  `p0_1_upstream_v1`; corrected execution is `p0_1_upstream_v2`. No data,
  expected hashes or numerical tolerances were changed.

## Provenance judgment and its limits

The seven historical learned inputs come from the pinned `mars_full/models`
estimators, not from any of the ROA outer-test folds. The original, authenticated
`freeze_method` source fits final estimators on informative preference pairs.
Reading the preserved ledgers reconstructs 601 fit traces / 518 question groups
from a 7,200-trace / 4,800-question development universe (train, calibration,
opened pilot, MuSiQue development). All 4,800 historical question groups belong
to the authenticated exclusion union and have zero overlap with the 4,500 ROA
development questions. The V2 comparison model used 3,000 earlier questions,
also with zero overlap. GbV is a frozen pretrained NLI model with no local task
fit. Reader, encoder, verifier revisions and bytes were checked.

This is source/ledger reconstruction of historical training membership. No
original per-estimator training-ID execution receipt was recovered. The complete
old `mars_full` manifest is locally self-consistent (363 payloads); its full hash
has no independently recovered earlier pin. The seven model hashes themselves
are pinned by the authenticated V2 requirements. These distinctions remain in
UPSTREAM_PROVENANCE.json; an original historical training run is **not** claimed
to have been replayed or conclusively witnessed. Unknown unlogged activity and
pretraining overlap are not asserted absent.

This evidence is sufficient to run the prespecified, development-only controls
on the identical cached features and grouped splits. It is not a waiver of the
remaining reproducibility limitations in the paper/release review. The LODO
claim must be narrowed: only the ROA head holds out a dataset; upstream models
previously saw other questions from all three datasets. No end-to-end unseen-
domain or baseline-independence claim follows.

## Next work and rejection risks

- P0: execute only GBV_ONLY_R and HGB_GBV_R (112 counted scientific fit calls),
  independently validate, retain every seed and failure, then review attribution.
- P0: establish a defensible contribution, final candidate/deployment recipe,
  untouched confirmation population and complete pre-outcome analysis design.
  Historical provenance limitations remain visible at final release review.
- P1: current-method cost/error analysis and appropriately scoped transfer.
- P2: no broader model/feature/budget search or larger-model expansion.

The leading rejection risk remains that a simple supervised verifier matches
the full stack. Method optimality/risk guarantees are unsupported; the fresh
confirmation and complete current-method cost evidence do not yet exist.
