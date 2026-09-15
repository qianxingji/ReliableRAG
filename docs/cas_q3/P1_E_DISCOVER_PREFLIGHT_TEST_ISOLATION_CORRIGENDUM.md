# P1-E Discover preflight test-isolation corrigendum

Decision: **PASS_DISCOVER_PREFLIGHT_TEST_ISOLATION_CORRIGENDUM**.

**CAS Q3 STATUS: NOT READY.**

On 2026-09-15, the first complete CAS Q3 test discovery after adding the
external-image audit ran 123 tests and retained one failure. The Discover
Computing preflight test called the production builder with its repository
defaults, which overwrote three tracked historical preflight artifacts before
the later Submission Readiness test checked their pinned hashes:

- `docs/cas_q3/P0_I_DISCOVER_COMPUTING_PREFLIGHT.json`;
- `output/target_profiles/discover_computing_preflight/discover_computing_source_preflight.zip`;
- `output/target_profiles/discover_computing_preflight/manuscript_12pt_preflight.pdf`.

The PDF changed from the pinned SHA-256
`4211f946e1b5ce7469c1e8cf8244eafdf592712a3faec0c8c26f538d7a7e38dd`
to the test-generated
`580799d6c63e407b1631c18f81c0fff8e98de08da34ca902cd0034b0056e98ef`.
The Submission Readiness verifier correctly failed instead of accepting the
replacement bytes.

All three tracked files were restored from the current accepted Git revision.
The test now patches only the builder's output and receipt locations to a unique
temporary directory under the worktree, checks the generated files while that
directory exists and relies on deterministic cleanup. It no longer writes any
tracked artifact. The isolated two-test module passes and leaves the three
historical files unchanged.

The subsequent complete CAS Q3 discovery run passes all 123 tests. The reviewer
map verifier passes 1,267 checks over 176 repository records, and the Submission
Readiness verifier completes 728 checks over 210 pinned repository hashes while
retaining its required `NOT READY` exit status. No Discover preflight artifact
appears in the final worktree diff.

This is a test-isolation correction, not a new Discover Computing artifact or
scientific result. It changes no manuscript source, experimental result, model,
Claim or selected Applied Intelligence route and authorizes no submission.
