# Phi development runtime V2 launch-failure acceptance

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

The second formal canonical Phi development invocation used source commit
`fffa0953ec40e0c80bb0042687a495252145ee58` and the single-use namespace
`outputs/cas_q2/phi_reader_development_runtime_v2`. It failed closed during the
`freeze` phase after the BGE and Phi checkpoint loads but before any trace or
scientific call. While constructing the device receipt, the sole
`platform.platform()` call invoked the Windows version subprocess. Opening
`os.devnull` with read/write flags was correctly rejected as a write outside
the selected output namespace.

The V2 receipt predates explicit model-load counters, so `1` BGE / `1` Phi /
`0` NLI loads are an audit inference, not direct receipt fields. The fixed
control flow and preserved traceback place the platform failure after both
`_ensure_loaded()` calls; the two-shard checkpoint-loading log and CUDA peaks
corroborate that ordering. No model forward or generation call occurred.

The preserved namespace has exact manifest SHA-256
`cb25a8c17d782d041c0d4c736fcfdefad3f03194d129f678ee1db38cc4efa682`.
It records zero completed traces, zero model forwards or generation calls, zero
repair retrievals, zero Gold reads and zero scientific fits. Peak CUDA allocated
and reserved bytes were respectively `7868907520` and `7881097216`. This is a pre-scientific launch failure, not a
scientific result, and it does not change CAS readiness or reader-axis evidence.

V2 is immutable and must never be resumed, reused, repaired in place or
deleted. The prospective corrected namespaces are fixed as
`phi_reader_development_runtime_v3`,
`phi_reader_development_runtime_replay_v3` and
`phi_reader_development_runtime_validation_v3`. They may be used only after the
prospective implementation correction is committed and accepted.
