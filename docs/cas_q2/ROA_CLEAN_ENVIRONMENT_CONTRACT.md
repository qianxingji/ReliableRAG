# Prospective independent numerical-environment reconstruction

Research Lead decision, 2026-09-11. CAS Q2 STATUS: NOT READY.

The accepted source/data relocation still imports third-party libraries from
the original project's `.venv`. A reviewer cannot reproduce the numerical
environment from the six archived authentication files. Close that concrete
remaining requirement for the original saved-parameter replay, without touching
the live C3 process or claiming a new empirical result.

## Fixed scope, before installation or numerical execution

Create a new isolated Windows x64 virtual environment outside both projects,
with system site packages disabled. Use the separately installed CPython 3.10.6
base interpreter to create it; record that existing interpreter and bundled
bootstrap packages. This tests a fresh third-party numerical-library installation
on the current OS, not installation of the OS or CPython itself on another host.

Freeze the versions observed in the accepted original runtime: NumPy 2.2.6,
SciPy 1.15.3, scikit-learn 1.7.2, threadpoolctl 3.6.0 and joblib 1.5.3. These five
packages close the non-extra runtime dependencies of this original replay.
Archive official PyPI version metadata and exact compatible wheel files, verify
each wheel against its published SHA-256 and size, and generate an explicit
hash-locked requirements file before installation. Do not substitute a version
or rebuild a binary when an artifact is unavailable; preserve the failure.

Install from the local wheel directory with no package index, binary wheels
only and hash checking. Record full commands, exit codes, package dependency
checks, installed versions, package paths and numerical backend details. Exclude
the old `.venv`, user site packages and externally injected Python paths. Save
wheel metadata/licenses and package records needed to reconstruct this scope.
Do not load any neural model, allocate GPU work or read fresh outcomes.

## Original full replay, one check for this different environment

Reuse the already authenticated source/data restored from the accepted v2 release
(`77cb08f879595c9da47aff52c9ed6531453ab961ee330f3d13d1b814ab537c73`). Do not edit its
source, models, outputs or manifest. In separate new output directories/processes,
run the unchanged primary and independent modes once using the new interpreter
and existing relocation guard. Deny old original-project and engineering-worktree
reads; because `sys.prefix` now points to the new environment, the old `.venv`
must no longer receive a permitted-runtime exception. Retain all failures.

Require all original gates: 28 contexts, 56 models, 38,424 primary predictions,
zero changed action membership, original 1e-10 numerical limit, 2,744,203 independent
checks, no old data/code/runtime fallback and unchanged original/release inputs.
The recorded Git LF / worktree CRLF generic-verifier distinction remains;
original numerical/control code and replay wrapper retain exact byte identity.
Do not add tolerances or modify package/artifact digests to obtain a pass.

Acceptance must separately identify authenticated wheels, successful offline
installation and full numerical replay under the new third-party environment.
Install-only or synthetic import success does not satisfy the full gate. A
manifest from the new environment does not retroactively authenticate the old
training environment. No new scientific fit or retrieval/generation is allowed.

## Remaining project-level obligations

This is the CPU numerical prerequisite for reproducible saved-parameter evidence.
It does not install the full neural C3/C4 stack or relocate absolute-path empirical
freezes; those need their own complete dependency evidence and actual execution.
It does not supply the seven missing historical fit-time ID/matrix receipts,
pass the failed method-advancement rules or establish fresh empirical quality.
C3 completion/replay/acceptance, C4 prelabel and D analysis remain P0. Complete
fresh-pipeline delivery and environment reconstruction remain P1. Preserve all
seeds/failures and continue to report NOT READY while those requirements remain.
