# C3 full validation failure: Research Lead review

2026-09-12 Asia/Shanghai. **CAS Q2 STATUS: NOT READY.**
This is the Astra xhigh anomaly audit required by MODEL_ROUTING.md.

## Completed acquisition and retained failure

The original canonical executor completed 18,000 traces / 54,000 generations
and 12,000 BGE repair-query forwards. Its native completion manifest is
`4df45c4c68d5961198ab7ecf2857a19efb0d15e1990aad9a3a7dc85b627415c4`;
121 frozen inputs passed the launch-precondition review. The original fixed
180-trace replay completed 540 generations / 120 BGE query forwards with exact
canonical comparisons. Its manifest is
`0597b34a5b0a51b146d6ffd53002b0c96c65579929e22353cb8fbafbb87e1c2d`;
128 frozen inputs passed. Both processes exited successfully. These are native
executor results, pending complete independent validation and final acceptance.

The first complete validation attempt actually ran from commit
`3f09244346ff756486b57fcff7c0dcdc0378409b`. It failed with
`NameError: name 'DATASETS' is not defined`. The original status remains FAIL;
the adapter did not upgrade it. No generation validation completed. The original
control flow reads the first branch/sidecar/generation rows before calling the
failing branch checker; this attempt is not described as zero runtime-data
access. It performed zero neural forwards, fits and fresh Gold reads.

The private attempt at task outputs/c3_bound_validation_v1 is sealed by
`45f6ebc715282c0098538f68d16bb35144a1c58b9a52cfe47e6e008f7b04c8f6`.
Its configuration is
`c63c6b99ba174922aa5dca31aa0f7155dd10883c4b3387738f91511410349e01`.
The failed original INDEPENDENT_VALIDATION.json is 5,505 bytes, SHA-256
`ca90d4d03eca6f6d1620aa9c0c03c9d821dc498c815b3bc5e2a11d7d642442ce`.
Its JSON content agrees with the sealed stdout. Stderr is empty. No final
SEAL.json, SHA256_MANIFEST.json or validation_execution directory was created.
All 14 existing runtime files, 41 C3 sources/configs, 11 controller inputs and
30,823 original environment files passed preservation checks.

## Root cause and coverage gap

The frozen current validator defines DATASETS/RETRIEVERS in its module, but its
load_independent_functions compiles twelve original helper functions into a
separate dictionary. That dictionary omits both constants. Original
validate_branch uses them for the unchanged stratum check. The missing names
therefore arise from source extraction, independently of the length adapter.

The separate read-only diagnostic recursively inspected compiled global-name
reads, including nested comprehensions/lambdas, for all twelve selected helper
functions. Its only unresolved names are DATASETS and RETRIEVERS, both in
validate_branch. Their tuple values agree exactly between the current validator
and the authenticated original runtime_support source. No helper body or current
runtime payload was executed/decoded by that static diagnostic. This finding
does not prove the remaining full validation will pass.

The diagnostic is task outputs/C3_HELPER_SCOPE_AUDIT_V1.json, SHA-256
`04e180e93c1dd97c1b84cc3b3d9205d986473bb9367309c89d3d579d89f0468f`;
its metadata is copied into [the public audit](C3_HELPER_SCOPE_AUDIT_V1.json).
The original helper SHA remains
`12634390df5c76ae30baeb3172778a86fdae87b7ffc06491db4ab57fcb83fd0a`
and current validator SHA remains
`3eb99ad55f93af8beaa0d316d8892ca8747a627bb80671d358312b758638915a`.

The previously accepted fixtures exercised generation checks and finalization,
but did not call original validate_branch. Their successes remain valid within
that scope; they were insufficient evidence for complete integration. No passed
fixture, failed full run or expected hash is rewritten to hide this gap.

## Decision and next work

Authorize the prospectively versioned [V2 correction contract](C3_VALIDATION_V2_CONTRACT.md):
bind only the two authenticated constants in the original helper namespace,
retain every scientific function/check, add branch/scope regression fixtures,
and retain the failed report through an independently verified archival move.
The controller must not overwrite the failure or repeat either neural pass.
Implementation and actual numerical execution return to Sol High. Final
authenticity/integration acceptance returns to Astra xhigh before C4.

P0: V2 fixtures, archival move, complete 54,540-generation validation and client
acceptance, then C4/prelabel/cost/D and contribution review. P1: full neural
delivery and provenance limits. P2: no additional search; CAS recognition and
journal remain undecided. No novel candidate, fresh quality claim or submission
readiness is established. Total scientific fits remain 185.
