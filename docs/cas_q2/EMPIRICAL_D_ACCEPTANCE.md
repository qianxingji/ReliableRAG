# Complete frozen empirical D acceptance

**Decision: ACCEPTED COMPUTATIONALLY.** The frozen analysis and its separate
independent validator complete the 18,000-trace D chain. A client final audit
accepts the execution, storage, input and no-mutation evidence. Scientific
claims still require the separate Research Lead review in
[P0_3_FRESH_RESULT_DECISION.md](P0_3_FRESH_RESULT_DECISION.md).

## Bound execution

- Source commit: `97406e92f477a9bba2f413c4b1bbf7201afb1cd0`
- Analysis manifest: `498b83e75538032de3711bd6ce190eac049631d8393c875744d83aa0318097f6`
- Analysis external manifest: `ec17db22f3c17eb0f92503bfbc4332094dd759c9e38c8f0033d6db76582c54e2`
- Analysis-validation manifest: `f9b38dd518f10be2cf22533dc0216fe15afa7f58f4fb3bbd3cde0735d59f7e36`
- Validation external manifest: `c129d6483e64128fbc52acfd0c6aa539e920f11df85cc80f172d233400f16a44`
- Client final audit: `27a0274add337fe12e51478e3e39fcbc934dd8271f6d8da13e059afe0527099f`

The analysis reads the independently accepted numeric outcomes and fixed C4
actions only. It retains all nine policies, 18,000 traces and 6,000 question
groups. With `numpy.default_rng(20260926)`, it completes 20,000 stratified
question-cluster draws, reallocates each non-Keep policy under the fixed global
900-action budget, and stores the complete `20000 x 6000` multiplicity matrix as
240,000,000 little-endian uint16 bytes. The sealed weight and draw-receipt hashes
are `2839a77841f9dea83a68d1b4604bac8b67eafdf22360b229733d481359ea9650`
and `440bb3964335f49b56bfb68bab10e63ccd012ec34e540f3fdacf86687ff3221f`.

The separate validator regenerates every RNG draw, checks every stored weight,
explicitly expands and sorts eligible row copies, and verifies 180,000 policy
allocations plus 180,000 fixed-action sensitivities. Its 2,973,210 checks confirm
every integer event count, point/cell report and all six multiplicity-adjusted
primary intervals. It imports neither the analysis executor nor its aggregation
module. Both analysis stages have zero action modifications, reference-string
reads, fits, model forwards, retrievals, generations, boundary denials and
forbidden calls.

The client final audit independently checks all 400 progress records, all 20,000
draw-receipt schemas, six fixed weight rows across all datasets, bulk-file hashes,
the two seals/configurations and the complete predecessor chain. It rehashes
18,327 unique executable inputs and 30,912 environment files. Its metadata
archive intentionally does not duplicate the 263 MB bulk draw artifacts; their
full hashes and original sealed files remain authoritative.

The bootstrap intervals condition on the fixed trained models and realized
bounded candidate pools. The scientific validator shares the pinned NumPy RNG
and quantile implementation with the producer, while using independent explicit
allocation math. This is not a model-training uncertainty interval, an exact
finite-sample coverage guarantee, an equivalence test or a Submission Ready gate.

**CAS Q2 STATUS: NOT READY.** P0 is the contribution/final-candidate decision
and a justified independent replication design. P1 is robustness, comparator
fidelity, provenance/contamination and public reproducibility closure. P2 is
paper/Claim consistency and journal-scope verification.
