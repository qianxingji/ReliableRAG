# Preflight source checkout difference, before numerical relocation

2026-09-11. CAS Q2 STATUS: NOT READY.

The accepted v2 data archive restored all 2,821 files exactly. Its Git bundle
restored a clean checkout of 73f8158 with `core.autocrlf=false`. The first external
relocation precheck then stopped before creating an acceptance directory or
starting either numerical mode. Its source equality check found that the generic
`scripts/verify_roa_artifacts.py` has 199 CRLF line endings in the engineering
worktree, while the committed Git blob and restored file use LF.

Preserved worktree SHA-256:
`918abb8d8a82f6e13c4041a2ce41ed8eef02da681f00ed3a1dbe6ecd06d9e50a`.
Restored file / original commit-blob SHA-256:
`cbdcf008de6d11722e224b179a51984ed1b78ec83cbb8f70f369297ad38155c1`.
The only byte difference is CRLF to LF. Neither source file is changed. The
original replay wrapper and all five original numerical/control modules are
already byte-identical between the old worktree and restored source.

The initial external runner assumed every helper's working-tree bytes would
equal a Git checkout, beyond the contract's unchanged numerical-code requirement.
Preserve that runner and `ROA_RELOCATION_PREFLIGHT_V1_REJECTION.json`. No numerical
run failed or was retried, and no saved parameter, artifact digest or tolerance
was changed.

Prospective runner v2 keeps exact old-worktree byte equality for the original
replayer and five original modules. For this generic artifact-verification
helper alone, require exact equality with the existing 73f8158 Git blob and
separately require that its sole difference from the old worktree is CRLF to LF.
Record both different digests and line-ending counts. Continue to require every
restored data/environment artifact's original digest unchanged. Freeze the
restored helper's actual LF bytes for post-run equality. This authenticates two
known representations explicitly; it does not change the stored expected hashes
or present them as identical.

Use a new acceptance namespace. Keep the same already restored source/data,
whose bytes have not changed, and run each original numerical mode once. All
numeric/action gates, no-original-data-fallback checks and scope limits remain.
