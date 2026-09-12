# Phi development runtime V1 launch-failure acceptance

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

The first formal canonical Phi development invocation used source commit
`460b7405db446a6b091cf031666930764fd40888` and the single-use namespace
`outputs/cas_q2/phi_reader_development_runtime_v1`.  It failed closed during
the `freeze` phase when Python's import machinery scanned
`E:/paper/ReliableRAG/.venv/Lib/site-packages/torch` after the runtime IO audit
had been installed.  The guard rejected that authenticated environment scan as
an unlisted project-directory scan.

The preserved namespace has exact manifest SHA-256
`42152a3c237bd0c1ade6d25d6a57d07e774d2377322803a471a815e037c9dbe5`.
Its failure receipt records zero completed traces, zero model calls or loads,
zero repair retrievals, zero Gold reads and zero scientific fits.  The failure
therefore contains no scientific result and changes no CAS readiness or reader
axis conclusion.

V1 is immutable and must never be resumed, reused, repaired in place or
deleted.  The prospective corrected namespaces are fixed as
`phi_reader_development_runtime_v2`,
`phi_reader_development_runtime_replay_v2` and
`phi_reader_development_runtime_validation_v2`.  They may be used only after
the implementation correction is committed and accepted.
