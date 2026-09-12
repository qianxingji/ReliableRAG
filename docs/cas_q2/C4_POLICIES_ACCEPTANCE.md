# C4 fixed policies acceptance

**Decision: ACCEPTED for complete C4 independent validation.** The single fixed
CPU policies stage completed over all 18,000 frozen traces, and a separate
client audit reproduced every saved-head score, global ranking, selected member
and action. This authorizes only the complete C4 independent prelabel validator.

## Bound execution and result

- Source commit: `db96260e0cc0ece53b68457cc77b5b5e44a9c96f`
- Scientific manifest: `2ad0d8a6112690ffb096af848cd8c7d50824aa08e9c20483be9f4c7530b146ed`
- External run manifest: `520c7423c818eb8e57e10ea665846b89adae33ac8caace553243dea251aaf4b2`
- Binding config: `cec258a8c9d378b4ad4948cd510431b83acc8a452d94dd8ff24e98c7919453df`
- Client audit manifest: `ec5d86d3a95b37f26fcc6bd5e5ce8ef36d1b32e4c1edb025722fc7ed2cb89d35`

The common eligibility set contains 4,267 traces. The prespecified global
denominator is 18,000, so the fixed five-percent cap is 900. Each of HGB, GbV,
ROA-FULL, ROA-NOGBV, HGB_GBV_R, HGB_ONLY_R, GBV_ONLY_R and V2 has exactly 900
REPLACE actions; Keep has zero. The other 13,733 traces are forced KEEP because
13,732 normalized answer pairs are equal and one original answer is empty.

The audit independently reconstructed all traces, aligned the saved base and
GbV rows, recomputed all base scores, V2 scores and five fixed-head logits and
probabilities, reranked the actual frozen scores with the specified tie break,
and compared all 18,000 rows across nine policies. It performed 392,564 numeric
checks with maximum error `1.27675647831893e-15`. All 17,454 executable inputs
and 30,912 environment files rehash unchanged. HGB `predict_proba` remains the
declared shared dependency on its authenticated saved estimator.

The first audit-controller attempt failed before head validation because the
saved semantic field had not yet been attached to reconstructed traces. It is
preserved with manifest
`041debcc66a00524f71861f90968493276d5751de903aa55131b69e715287593`.
The corrected controller adds only an exact dataset/key-aligned read of the
already sealed base semantic field. The scientific stage was not rerun.

No neural model was loaded, no neural forward or model fit ran, and no fresh
Gold value, retrieval or generation was accessed. This is prelabel/action
arithmetic evidence, not answer-quality or contribution evidence.

**CAS Q2 STATUS: NOT READY.** P0 is the one complete C4 independent validator.
After it passes, P1 is cost reconciliation and four frozen D processes. P2 is
claim/contribution, confirmation and reproducibility closure. Current rejection
risks remain absent fresh outcomes, no cleared candidate, historical receipt
gaps and an undecided CAS journal/category scope.
