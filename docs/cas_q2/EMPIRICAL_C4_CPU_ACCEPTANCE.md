# Client Lead acceptance: C4 CPU model compatibility and engineering kernels

CAS Q2 STATUS: NOT READY. Effective 2026-09-11.

Accept empirical_saved_scoring_preflight_v2 at source commit
79613a0c7f78e72d102fa6affcdf066d58d2a864 for CPU compatibility only. Its manifest
is 65bfe79a80974c67204eb1dd792d420ffc974b4e9e6be95d3496ae2b86aa0ceb.
Seven original upstream estimator artifacts and the original five-member V2
ensemble loaded without fitting. The five fixed JSON parameter heads also
scored the three invented inputs. The 102 independent downstream numeric checks
passed at the unchanged 1e-10 threshold; maximum error was
2.220446049250313e-16. Missing-value preprocessing, retriever indicators and
native eligibility were checked. No fresh branch or Gold row was read, and no
pretrained neural model was loaded or forwarded.

The assembled feature AST records exactly match the sealed original base-score
provenance. There are 34 selected definition records including the additional
original V2 scoring definitions. Direct checks bypass selector wrappers for
logistic preprocessing/arithmetic, V2 softmax/empirical CDFs and panel Platt
outputs. HGB checks still call the saved sklearn tree estimator; this is not
independent tree traversal or fresh neural replay. It establishes neither answer
quality nor empirical contribution.

The v1 failure and separate diagnostic are preserved under their original
manifests. EMPIRICAL_C4_IMPORT_CORRECTION.md documents the nonexistent .pyc probe
that was blocked before source execution/model loading. v2 changes only the
source-loading IO bridge; no original files, learned parameters, guards, scoring
definitions or tolerances were changed to pass the tests.

Additional kernels implement the already frozen contract: native likelihood
forward observers bind every answer token, aggregate and current-run cache hit;
GbV observers bind native chunk/token/logit/probability batches and branch maxima;
the nine-policy allocator preserves N_all, one common mask, global Python-rounded
5% cap, canonical ties, negative scores and min(cap,eligible_count). The invented
18,000-row allocation test confirms 900 global switches without dataset quotas.
Missing policy rows, inconsistent masks, nonfinite scores and inherited caches
without current-run witnesses are rejected.

The observers return no replacement neural output and add no model forward.
They repeat token preparation and compute sidecar reductions; actual future
timings must include this instrumentation overhead and distinguish it from
model-only time. Native likelihood forward latency now includes its observing
hook's work; it must not be compared as an identical historical timer boundary.
These observer tests used CPU dummy logits with the original scoring methods.
Real pinned-model GPU preflights and complete acquisition/scoring integration
and independent validation remain pending.

The full repository regression command was
`python -B -m unittest discover -s tests -v`: 82 tests ran, 80 passed and two
Windows filesystem-capability cases were skipped. No scientific fit was added;
the takeover total remains 178. The separate original 22-test CPU runtime fixture
run and earlier selected runtime suite remain historical evidence, not new fits.

P0: complete the running C3 pass, its fixed replay and independent acceptance;
finish C4 adapters and real GPU preflights, score and independently seal all
prelabel actions before any Gold mapping, then execute the frozen empirical
analysis. Both historical advancement failures, original training-receipt gaps
and absence of a cleared novel candidate remain. P1 covers baseline/cost/release
fidelity and contamination scope. P2 introduces no new search. CAS journal year,
institutional category rule and target remain undecided by the user.
