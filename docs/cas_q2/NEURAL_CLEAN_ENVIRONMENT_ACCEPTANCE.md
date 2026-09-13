# Offline neural-package environment: client Lead acceptance

**CAS Q2 STATUS: NOT READY.** Accept offline installation, official installed
payload verification and bounded CPU import/binary smoke only. CUDA execution,
pretrained inference, full pipeline relocation and another-host reproduction
remain untested. See NEURAL_CLEAN_ENVIRONMENT_RESULTS.json for current receipts,
artifact hashes and the live C3 checkpoint.

The prospective contract was committed at `1c476d6`; its local IPv6 probe
refinement at `77992e1`. The initial installation namespace and failed smoke
remain unchanged, with manifest
`6f31eabcdaf4e1ddb286cf72736806595f8f82d506d164d099cf712e90a1a09b`.
The separate corrected acceptance is
`9ee936df3f2e3e2370991b3dcefccaba96de263a54abc7bb1b412c8c97c734f8`.
There was one installation; the environment was not rebuilt to obtain this pass.

## Verified result

All 33 main distributions and two separate target distributions were installed
offline from the 35 authenticated official wheels. Names, versions, target
locations and pip dependency consistency pass. The separate verifier compared
21,139 installed files / 6,227,247,823 bytes with official wheel payloads and
verified 21,225 nonempty installed RECORD hashes. There are no installed RECORD
size/digest errors or duplicate paths in this new environment. Installer-generated
metadata/launchers and the relocated SymPy manual file are explicitly accounted
for. These results do not change the original environment's retained discrepancy.

The bounded CPU fixtures passed: exact 2-by-2 NumPy/Torch products, an invented
three-row Arrow IPC roundtrip and an invented two-token WordLevel codec. Core
imports use the new venv or the two new target directories, and the pretrained
factory classes import without instantiating a model. The process recorded 3,146
loaded Python modules with file paths and 248 mapped binaries: 174 new-environment,
five new-target, 26 reused-base-Python and 43 reused-Windows files. The first three
binary groups are hashed. Reused Windows libraries are disclosed, not represented
as a freshly installed or completely packaged OS.

The file guard observed no old-project/venv access during the smoke. One local
IPv6 capability bind by the authenticated urllib3 `_has_ipv6` function was allowed
under the prospectively fixed exception and verified closed. There were no blocked
events in the revised run. No external connection, DNS request or later subprocess
was permitted. This is Python-audit and loaded-module evidence, not visibility
into every native/OS file operation. Torch CUDA initialization remained false;
no project model/tokenizer, fresh answer/score or Gold was loaded.

All 21,267 installed files / 6,231,699,885 bytes remain unchanged after smoke.
All 30,823 original environment/target files, 217 initial installation inputs
and 28 v2 acceptance inputs also remain unchanged. The old failed smoke and its
diagnostic are preserved. Existing engineering suite remains 151 tests, 149 pass
and two Windows skips; that suite was not repeated for this environment stage.

## Boundaries and remaining work

The [offline package runbook](NEURAL_OFFLINE_PACKAGE_RUNBOOK.md) documents the
actual procedure and its scope. The current host and CPython base are reused;
another computer/OS and a fresh Python installation have not been validated.
The new package environment has not executed C3/C4 neural models. Frozen original
root, target-package and predecessor path bindings remain constraints on delivery.
The original live C3 process must finish its fixed replay and independent gate
before actual C4 GPU stages. No accepted scientific stage was rerun here.

P0: complete C3, then C4/full prelabel, cost reconciliation, D and actual
contribution review. P1: design and verify full pipeline delivery/path bindings,
and preserve comparison/training/contamination limits. P2: no model, feature,
seed or budget search. Main rejection risks remain unestablished contribution,
both failed historical advancement rules, incomplete fresh empirical evidence
and seven missing original per-estimator fit-time ID/matrix receipts.
