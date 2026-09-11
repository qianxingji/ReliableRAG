# Neural runtime inventory: client Lead review

CAS Q2 STATUS: NOT READY. The current dependency/model/path inventory is
complete with a preserved installed-RECORD discrepancy. **No clean neural
environment acceptance is granted.** See NEURAL_RUNTIME_INVENTORY_RESULTS.json
for sealed manifests and the current byte-count-only C3 checkpoint.

## Actual coverage and findings

The v2 inventory authenticates 30,912 unique inputs / 13,873,730,901 bytes;
all hashes and sizes remain unchanged on the final pass. The original venv
contains 33 distributions and 30,032 physical files. Separately targeted
SentencePiece 0.2.1 and PyArrow 20.0.0 add two distributions and 791 files.
These targets are real loader obligations and are missing from an ordinary
venv-only requirements export. No scientific library/model/tokenizer was
loaded, no neural forward was added, and no fresh answer/score/Gold was decoded.

All 38 active dependency requirements are satisfied on the observed Windows
amd64 CPython 3.10.6 target. Another 899 declarations are inactive platform or
extra branches. This describes the current environment, not every supported
platform, every extra, or a minimal dependency set. In particular, the observed
`platform_machine` marker value is `AMD64`; retain actual marker semantics.

The 30,707 RECORD declarations include 21,201 hashes and 9,506 unhashed entries.
One NumPy cache has duplicate declarations: an empty entry and a hashed entry
for the official wheel's 8,278-byte cache. The installed cache is 8,284 bytes,
so both size and digest checks fail for that hashed declaration. The other
21,200 hashed declarations match. Both caches compile exactly from the same
official NumPy source when their respective embedded filenames are used;
neither code object was executed in diagnosis. This explains the observed
content relationship without inventing an installation history or changing
the failed RECORD checks. Original cache and RECORD remain untouched.

Another 117 physical files lack installed-RECORD ownership: seven venv launcher/
configuration/activation files and 110 caches whose filenames specify CPython
3.12 (97) or 3.13 (13). All are retained and hashed. Their presence is current
state evidence, not evidence of historical execution by this CPython 3.10 run.

The original accepted manifests authenticate all 22 Qwen/BGE/NLI asset files,
7,494,996,533 bytes, including their configuration/tokenizer files. They were
read as opaque bytes. Authentication does not constitute another model forward
or independently establish an earlier unrecorded environment.

## Frozen path and historical limits

Three active original support modules bind `ROOT` literally to
`E:/paper/ReliableRAG`; the current C4 source bridge checks that exact root.
C3/C4/D/cost freezes respectively contain 121/243/1,054/1,065 absolute input
records across the original project, engineering worktree and task workspace.
These counts overlap across stages and must not be summed as unique files.
Arbitrary `--project-root` relocation is not supported by these frozen loaders.
Keep the current C3/C4 path strategy unchanged; design any independent delivery
mapping prospectively and distinguish it from original execution.

Original runtime metadata names eight package versions and original scoring
metadata names six. The new 35-distribution inventory cannot retroactively
authenticate their other dependencies at historical generation or training
time. The same-host independent numerical environment/replay remains accepted;
it is narrower than full neural-pipeline reconstruction. Seven upstream models
still lack original per-estimator fit-time ID/matrix receipts. Original upstream
training and semantic/pretraining decontamination are not established.

## Preserved failures and next gate

Keep the v1 platform-probe guard failure, both NumPy diagnostic records and the
v2 inventory with reported issues. The marker probe was moved before the strict
guard; scientific-import, later process/network and outside-write restrictions
were retained. The metadata resolver's overly narrow Torch hostname check also
failed: the authentic official index links to `download-r2.pytorch.org`.
Preserve that v1 result and the separate pre-output parser variable-shadowing
failure. The corrected resolution reuses the retained index and all 34 successful
PyPI responses; it changes no published hash and makes no replacement request.

Exact official wheel availability is now established for all 35 distributions.
Binary-acquisition receipts and role-specific hash locks are separate evidence
reported in NEURAL_RUNTIME_INVENTORY_RESULTS.json. Neither wheel availability
nor acquisition is a clean installation, neural preflight or neural replay.

P0: finish original C3 canonical generation, fixed bounded replay and independent
acceptance, then actual C4/full prelabel acceptance, cost reconciliation and D.
P1: separately reconstruct the neural environment from the now acquired official
wheels and design delivery paths; preserve provenance/comparison limits.
P2: no new model/feature/seed/budget search. Principal rejection risks remain
unestablished contribution, two failed historical advancement rules, incomplete
fresh empirical results and missing historical training evidence. Engineering
test counts remain 151/149 pass/two existing skips; no suite was repeated here.
