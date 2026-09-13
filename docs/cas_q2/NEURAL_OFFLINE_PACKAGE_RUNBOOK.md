# Offline neural-package installation: verified scope and reuse

The accepted result is package installation and CPU import/binary smoke on the
current Windows amd64 CPython 3.10.6 host. It does not authorize execution of
frozen C3/C4 controllers at a different root or replace actual GPU-stage gates.
CAS Q2 STATUS: NOT READY.

## Available inputs

`NEURAL_OFFLINE_PACKAGE_KIT_V1_PRIVATE.zip` contains the 35 authenticated official
wheels, existing CPython ensurepip bootstrap wheels, four hash locks, private
inventory metadata, original installation/failure/diagnostic/acceptance receipts,
the exact audit scripts and contracts. Check its published SHA-256 in
NEURAL_CLEAN_ENVIRONMENT_RESULTS.json before unpacking into a new private folder.
The installer/model payload distinction matters: this kit contains package
binaries, not pretrained model weights, datasets, a Python installer or Windows.

| Lock file | Role | Distributions |
|---|---|---:|
| `neural-original_venv-win-cp310.lock` | Main isolated environment | 33 |
| `neural-sentencepiece_target-win-cp310.lock` | Separate native SentencePiece target | 1 |
| `neural-pyarrow_target-win-cp310.lock` | Separate original-reference reader target | 1 |
| `neural-all-win-cp310.lock` | Combined exact inventory; retain role separation | 35 |

The main environment uses Torch 2.7.1+cu128 and Transformers 4.53.2, with all
leaf dependencies pinned. SentencePiece is 0.2.1 and PyArrow is 20.0.0. Do not
substitute a CPU Torch wheel, a newer package or a source build to obtain a pass.
The accepted original NumPy environment discrepancy remains in its historical
inventory. The new installation independently matches the official payloads.

## Installation procedure and evidence

Use new absolute environment/target/output paths; refuse existing directories.
The archived scripts contain this host's explicit paths and single-use namespace
checks. They are audit receipts, not a claim that arbitrary roots have already
been tested. Do not rerun them against the accepted directories.

1. Verify the complete acquired-wheel manifest and all 35 payload hashes. The
   acquisition manifest is
   `813f7faeb51f015135e6d85d496c359225b234e9692d4eb079e63ba432c8ac89`.
2. With the authenticated CPython 3.10.6 base, create a venv using
   `-I -B -m venv --copies`. Disable system/user packages and inherited Python/
   pip path/config overrides; confine temporary writes to the new output root.
3. Use the new venv's Python and isolated pip with `--no-index`,
   `--require-hashes`, `--only-binary=:all:`, `--no-cache-dir`, `--no-compile`
   and `--find-links` pointing to the local wheels. Install the main 33-package
   lock with `--force-reinstall`, then each one-package target lock using its
   own `--target` directory. Preserve installer reports and logs. All 35 reported
   download origins in the accepted installation are local `file:` URLs.
4. Check exact names/versions/roles and pip dependencies. Verify installed RECORD
   hashes/sizes and compare official wheel members with installed payloads.
   Record generated RECORD/entry-point files and relocated data paths separately.
   A same-version metadata match alone is insufficient. Freeze the full installed
   file set before any smoke operation.
5. The accepted revised smoke uses only CPU fixtures, `-I -B`, two explicit new
   target paths, hidden CUDA devices and one CPU thread. Its exact access guard
   denies old-project data, remote connections, DNS, other binds and processes.
   One authenticated urllib3 local IPv6 capability bind is recorded and closed;
   see NEURAL_CPU_SMOKE_IPV6_REFINEMENT.md. Preserve failures and do not simply
   disable the guard. Rehash all new installed and original environment files
   afterward, plus the bound installer inputs.

Actual accepted directories are `E:/paper/ReliableRAG-neural-environment-v1` and
`E:/paper/ReliableRAG-neural-targets-v1`. The separate numerical replay environment
and original live C3 environment remain unchanged. Do not switch C3 to the new
Python or rerun canonical generation.

The next release step needs an explicit path-binding design: three original
support modules use a literal original root, C4 checks that root and its native
SentencePiece location, and phase freezes retain absolute predecessor paths.
Any IO adaptation must preserve and authenticate original scientific definitions,
disclose its scope and pass the appropriate replay; it must not silently alter
those frozen sources or be presented as already completed neural reproduction.
