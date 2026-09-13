# Private ROA saved-parameter replay release

This package is scoped by [the prospective contract](ROA_REPLAY_RELEASE_CONTRACT.md).
It contains original ROA and required parent files, including negative results,
plus committed source history. It is private and has not been uploaded. It does
not establish a new method, reconstruct original training, or package the fresh
empirical experiment. CAS Q2 STATUS: NOT READY.

Use the external SHA-256 manifest pin from the release acceptance record. A
manifest stored inside a downloaded archive cannot authenticate itself. Keep
every archive and output directory from a failed attempt; choose a new version
only after diagnosing and recording the failure.

## Restore without source-network access

The package directory contains `SOURCE.bundle`, `DATA_PRIVATE.zip`,
`DATA_INVENTORY_PRIVATE.json`, `ENVIRONMENT.json`, `BUILD.json` and its manifest.
Verify the external manifest pin and each listed byte hash before using code.
From an existing checkout of the release commit, run:

```powershell
python -B -m scripts.restore_roa_replay_release --package <package-directory> --manifest-sha256 <external-pin> --destination <new-directory>
```

The restore tool verifies the complete package, archive members and extracted
bytes; creates `data/`; and clones `SOURCE.bundle` into `source/` at the exact
saved commit with `core.autocrlf=false`. No Git network access is needed. It
never creates an environment or installs dependencies. Check `RESTORE.json`.
If no checkout exists, first clone the authenticated Git bundle with
`git clone --no-checkout --config core.autocrlf=false <SOURCE.bundle> <bootstrap>`
and `git -C <bootstrap> checkout --detach <source-commit>`, then run the restore
tool from that bootstrap source using an existing compatible Python.

## Existing runtime and full saved-parameter checks

Use Python 3.10.6 with NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.7.2 and
threadpoolctl 3.6.0, as recorded in the existing accepted replay. The observed
host is Windows x64. The six `.venv` files under restored data are frozen
authentication artifacts, not a usable Python installation. A new installation,
another host/OS and numerical-library portability have not been verified.

From restored `source/`, use two new output directories outside `data/`:

```powershell
python -B -m scripts.replay_roa_relocated --project-root <restored-data> --output <new-primary-output> --mode primary --deny-root <original-project> --deny-root <engineering-worktree>
python -B -m scripts.replay_roa_relocated --project-root <restored-data> --output <new-independent-output> --mode independent --deny-root <original-project> --deny-root <engineering-worktree>
```

The wrapper only adds a Python file-open guard and calls the unchanged original
replay entrypoint. The host's `sys.prefix` runtime is the sole permitted exception
under denied roots. `RELOCATION_ACCESS.json` records that exception and any denied
attempt. It is not an OS sandbox. Inspect both `REPLAY_VALIDATION.json` reports,
the complete independent result and post-run data checks; a restored archive or
one successful mode alone does not pass relocation acceptance. The primary gate
requires all 28 contexts, 56 saved models, 38,424 prediction rows, original 1e-10
tolerance and exact action membership. This operation fits no models.

## Unresolved broader release requirements

The fresh empirical C3 process is still running. Its eventual C4/D seals, neural
assets and absolute-path freeze records need their own complete release design
after results exist. The current package does not close seven original upstream
estimators' missing fit-time ID/matrix receipts or provide a clean install test.
Do not relabel this bounded saved-parameter result as full pipeline reproduction.
