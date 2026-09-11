# Offline third-party numerical environment for original ROA replay

Scope: the unchanged original saved-parameter replayer, on Windows x64 with
CPython 3.10.6. The current host's separate CPython installation is reused;
fresh NumPy/SciPy/scikit-learn/joblib/threadpoolctl packages are installed into a
new isolated virtual environment. No neural packages or models are installed.
This is not a complete fresh empirical pipeline environment or training replay.

The exact five-package wheel lock is
[roa-replay-win-cp310.lock](../../requirements/roa-replay-win-cp310.lock).
Official PyPI version metadata, compatible wheel bytes, published SHA-256 and
sizes, package metadata and license copies are preserved in the private wheel
acquisition namespace. The lock uses those published digests without alteration.
No source build, alternate version or unpinned dependency is permitted.

## Kit and externally authenticated checkpoints

The private offline kit contains the previously accepted source/data review ZIP,
five official wheels (63,378,499 bytes), the wheel acquisition and installation
receipts, complete new-environment replay receipts, acceptance scripts, this
runbook and the contract. Copies of the existing CPython-bundled pip/setuptools
wheels are included to document the bootstrap. It does not contain an OS or
CPython installer, a distributable installed `.venv`, neural model weights, or
fresh evaluation outcomes. Authenticate the whole kit using the external digest
in the acceptance record before executing any contained code.

Important manifest pins:

- Wheel acquisition:
  `bf30b0bf3d97156484f27005cc7b4435f3b5aac30f3281527ec56857149acdc1`.
- Offline installation:
  `2115a44cf582c515142ec8f76e135cb85f74e454a4604186cb732f4e4777a547`.
- Full new-environment numerical acceptance:
  `44b87939aed4f39cf83e9d3907d476cd544765228fe6431b4b818d44be6dd9cf`.
- Original accepted source/data package:
  `77cb08f879595c9da47aff52c9ed6531453ab961ee330f3d13d1b814ab537c73`.

The historical source snapshot is commit
`73f8158c2570e77998d944fac6e5bc9afe4fe6eb`; later acceptance documents are separate
from that tested snapshot. Preserve the prior rejected package and preflight
records. The original numerical modules/replay wrapper remain byte-identical;
the documented generic-verifier Git LF / original worktree CRLF distinction
continues to apply without changing any artifact digest.

## Tested installation sequence

Choose new directories outside all original projects. Extract and authenticate
the source/data review ZIP, then restore its source/data as described in the
[release runbook](ROA_REPLAY_RELEASE_RUNBOOK.md). Keep its 2,821 data files intact.
Never launch a package's archived `.venv` authentication files as an environment.

Using the separate CPython 3.10.6 base interpreter, create a fresh virtual
environment with `-I -B -m venv --copies <new-environment>`. Its `pyvenv.cfg` must
say `include-system-site-packages = false`. The observed bundled bootstrap is
pip 22.2.1 and setuptools 63.2.0; their original wheel bytes are recorded in the
installation freeze and copied into the kit. The observed base `python.exe`
SHA-256 is `32ce1d2650ea8b9d394f5b8f94677d27888dccdc3713365bf903a8c465c9d776`.
This is provenance of the actual host, not a claim about an untested installer.

Call the **new environment's** Python executable with these arguments:

```text
-I -B -m pip --isolated install --no-index --no-cache-dir --require-hashes --only-binary=:all: --no-compile --find-links <wheel-directory> --requirement <hash-lock-file> --report <new-install-report.json>
-I -B -m pip --isolated check
-I -B -m pip --isolated list --format=json --disable-pip-version-check
```

Installation must use only local wheel URLs and produce exactly the five locked
packages plus the two bundled bootstrap packages. Save complete logs and exit
codes. Verify imported package paths and all reported numerical backends lie
under the new environment. User/system site packages must be disabled. The
new numerical environment does not need Torch and its absence was verified.

For child processes, the tested controller removes inherited `PYTHON*` and
`PIP_*` variables, then sets `PYTHONNOUSERSITE=1` and
`PYTHONDONTWRITEBYTECODE=1`. Do not let an activated old environment inject
Python package paths. The private `acceptance_scripts/` preserve the exact
executed commands and path checks; their original host paths are audit records,
not portable defaults that should overwrite another user's directories.

## Full numerical acceptance

From restored `source/`, run its existing `scripts.replay_roa_relocated` module
with the new interpreter, `-B -s`, the restored `--project-root`, separate new
`--output` directories, and `--mode primary` / `--mode independent`. Provide both
the original project and engineering worktree with repeated `--deny-root`.
The new `sys.prefix` exception must not permit reads under the old `.venv`.
Archive both full reports and `RELOCATION_ACCESS.json` files. Retain all failed
outputs; do not retry the same namespace or change hashes/tolerances.

Acceptance requires the original full numeric/action gates, correct package and
backend paths, zero observed old-environment accesses, and unchanged installed
environment/release inputs before and after both processes. Imports, package
checks or a single successful mode alone do not establish this result. Python
file-open audit events are not an OS sandbox. This procedure does not prove a
different OS/host, new CPython installation, original model training, or the
unfinished empirical neural stack.
