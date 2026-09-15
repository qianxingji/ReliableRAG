# C3 V3.1: numerical runtime boundary amendment

Research Lead decision, Astra xhigh, 2026-09-12 Asia/Shanghai.  
**CAS Q2 STATUS: NOT READY.** This prospective amendment was frozen before any
full V3/V3.1 validation. It supersedes only the start/end threadpool clause in
`C3_VALIDATION_V3_CONTRACT.md`; every scientific source, helper, datum, prompt,
model, seed, threshold, literal comparison, expected hash and execution count
remains unchanged.

## Trigger and preserved failures

The V3 invented-only gate exposed two literal failures. Fixture v1 treated every
`threadpoolctl` entry as a BLAS pool and failed after PyTorch loaded two OpenMP
runtimes. After limiting that implementation to `user_api == "blas"`, fixture
v2 still failed because loading the frozen tokenizer also loads a distinct SciPy
OpenBLAS 0.3.28 DLL. Both failure namespaces and manifests remain immutable.

An independent read-only audit, manifest SHA-256
`bb4f4f04a8a96759edfade612bc32a12dbf6a7f6df17f194a4e24fc1fdd8a4db`,
reproduced the transition with zero current-runtime payload reads, Gold values,
neural forwards or fits. Before tokenizer loading the process has only the
authenticated NumPy OpenBLAS 0.3.29 pool. Afterwards it has that same pool plus
four frozen auxiliary entries: two PyTorch OpenMP DLLs, sklearn `vcomp140.dll`,
and SciPy OpenBLAS 0.3.28. All five report their native-default thread counts,
and all DLL paths, sizes and hashes are present in the previously authenticated
30,823-file environment inventory.

## Corrected boundary

The repair operation under audit is the unchanged NumPy expression
`state["matrix"] @ vector`. The complete arithmetic census authenticated the
NumPy-linked OpenBLAS 0.3.29 DLL for that expression. It did not authenticate
the SciPy DLL as the repair arithmetic backend.

V3.1 therefore requires:

1. all three thread override variables remain absent;
2. NumPy is exactly 2.2.6;
3. at start, exactly one threadpool entry exists: the census-authenticated
   NumPy OpenBLAS 0.3.29 SkylakeX pthreads DLL at 12 threads;
4. at end, that exact target entry still exists once and is unchanged;
5. every other end entry exactly matches the four-entry frozen auxiliary
   allowlist in API, implementation, thread count, version, threading layer,
   architecture, path, size and SHA-256; no missing, duplicate or unknown entry
   is accepted.

This is a stricter description of the process that the original V3 contract
mistakenly assumed contained one global OpenBLAS pool. It does not treat the
SciPy pool as census evidence, permit a different NumPy target, or allow a
floating set of extra libraries. Negative fixtures must reject a missing or
duplicate NumPy target, any target identity change, an auxiliary pool at start,
any missing/extra auxiliary pool at end and every auxiliary identity change.

## Execution boundary

Implement V3.1 in new source and fixture files. Preserve V3 sources and both
failed fixture namespaces as evidence. Sol High may execute the new invented-only
gate. A separate client audit must accept its sources, exact five-library end
state, negative cases and preservation evidence before the single full
validation authorized by the parent contract. Any V3.1 fixture or full-run
failure is retained; there is no automatic retry or further protocol change.
