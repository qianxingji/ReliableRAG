# Independent neural-package installation and CPU import acceptance

Research Lead decision, 2026-09-11, before installation or smoke execution.
CAS Q2 STATUS: NOT READY.

The 35 exact official wheels are authenticated under acquisition manifest
`813f7faeb51f015135e6d85d496c359225b234e9692d4eb079e63ba432c8ac89`.
Create a new environment at `E:/paper/ReliableRAG-neural-environment-v1` using
the separately installed CPython 3.10.6 base, without system/user site packages.
Create separate SentencePiece and PyArrow targets beneath
`E:/paper/ReliableRAG-neural-targets-v1`. Refuse existing output or target roots;
preserve any failed installation. Do not modify the original project, current
running venv, accepted CPU replay environment or frozen C3/C4 loaders.

Install the 33 main-environment distributions and two separate target packages
from the acquired local files only. Use isolated pip, `--no-index`,
`--require-hashes`, `--only-binary=:all:`, `--no-cache-dir` and `--no-compile`.
Force reinstall the main lock, including its exact pip/setuptools versions, so
the environment is populated from authenticated selections. Retain the existing
CPython ensurepip bootstrap wheel hashes, every command, installer stdout/stderr
and install reports. Remove inherited Python/pip path/config overrides. Do not
substitute versions, build sources or access an online package index.

Check exact installed distribution versions and role locations, pip dependency
consistency and every nonempty installed RECORD hash/size. Independently compare
installed wheel payload files with official ZIP members, retaining installer
transformations separately: installed RECORD is regenerated, entry-point scripts
may be generated, and wheel data-scheme paths may relocate. Do not simply discard
a mismatching source or binary as installation noise. Inventory all installed
physical files, including generated/unowned files, and freeze them before smoke
execution; all must remain unchanged afterward. The earlier original NumPy
RECORD/cache discrepancy remains preserved and is not repaired by this stage.

## Bounded CPU-only smoke and access evidence

Run a separate process with `-I -B`, the new Python and only the two new target
directories explicitly added. Hide CUDA devices for this smoke process only;
set CPU thread counts to one. Import the core native/runtime libraries and
model factory classes, but instantiate no pretrained model and load no project
tokenizer or model asset. Check a fixed 2-by-2 NumPy/Torch CPU matrix product,
an invented three-row Arrow IPC roundtrip and an invented two-token WordLevel
codec. These are binary/import smoke fixtures, not scientific fits, neural
forwards, actual C4 preflight or performance evidence. Do not call CUDA discovery,
initialize CUDA or use the live C3 GPU. Require Torch CUDA initialization to
remain false before and after the smoke.

Record import paths, loaded library mappings, interpreter/platform metadata and
dependency markers. Guard Python file access against the old project/venv,
engineering checkout, accepted CPU environment and scientific data. Permit only
the new environment/targets, base interpreter, OS files, this smoke script and
its new output/scratch directory. Deny network and later subprocesses. Keep
temporary writes in that output directory; scientific inputs and installed
packages remain read-only. Record any blocked access; no observed old-venv access
does not imply visibility into every OS/native read. Hash mapped binaries when
they belong to the new environment or reused Python base; disclose reused OS
runtime dependencies rather than claiming a fresh OS installation.

Bind the installer, smoke, independent verification source, this contract, the
official acquisition and base/bootstrap inputs before execution. Accept only
exact installed versions, consistent dependencies, authenticated payloads and
unchanged installed files with successful bounded smoke. A PASS closes offline
package installation and CPU import/binary checks only. It does not establish
CUDA execution, pretrained-model equivalence, full C3/C4 replay, arbitrary-root
delivery, another host/OS or historical training reconstruction. Frozen C3 must
finish and pass its original replay/validator before actual C4 GPU stages.

Total scientific fits remain 178. Preserve both historical advancement failures;
fresh results/contribution review and seven upstream fit-time receipts remain
missing. Full CAS Q2 readiness is not established by this environment stage.
