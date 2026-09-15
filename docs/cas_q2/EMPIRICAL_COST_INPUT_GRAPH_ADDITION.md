# Cost input graph exact metadata addition

The first postlabel-V2 cost attempt passed the accepted C4 path binding, then
failed before creating the scientific namespace because one file already named
by the unchanged cost reconciler was absent from its authenticated input graph:
`outputs/cas_q2/empirical_retrieval_gpu_preflight_v1/GPU_PREFLIGHT.json`.
The file is 477,790 bytes with SHA-256
`0efc5dc0c56dd1807cff1e779ae3d3a434b7ea89958856844b39c88faebf0ad8`.
The failed external run remains sealed under manifest
`f83b17730a1b2a2eba507075d87f7d04253cb9d787b9e65e3a5336a4686c664f`.

This is existing C2 synthetic GPU-preflight metadata used only for the cost
report's verification-overhead count. The corrected cost config must add this
exact file as a hash-bound control. The postlabel V2 wrapper then includes it in
the new cost executable freeze and decoded metadata allowlist. No other missing
file exists in the independently enumerated set difference.

This addition does not authorize raw references, canonical answer text, C4
score/action payloads, model files, inference, fitting, generation, retrieval or
network access. It changes no existing source, result, manifest or cost formula.
The cost scientific namespace remains absent and fresh Gold remains zero.

**CAS Q2 STATUS: NOT READY.** Retry cost once after this evidence is committed,
preserve any failure, and require a separate complete client audit before using
the cost report.
