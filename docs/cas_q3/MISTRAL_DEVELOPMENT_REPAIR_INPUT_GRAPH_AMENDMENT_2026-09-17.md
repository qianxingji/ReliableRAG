# Mistral development repair input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running and before any development repair
namespace existed. It changes no question, trace, reader output, retrieval
algorithm, repair position, depth, BGE model, action budget, label, endpoint or
tuning rule. It closes an execution-provenance gap in the not-yet-run repair
stage.

## Gap

The initial repair implementation verified the accepted `a0_query` manifest and
the three historical runtime/pool/retrieval manifest hashes before use, but its
own executable freeze recorded only those manifest files rather than every
member they authenticated. It also identified the BGE revision at runtime but
did not freeze the six exact model files already authenticated by the accepted
synthetic BGE preflight. A member mutation after the initial check could
therefore evade the repair stage's final input rehash.

## Prospective correction

Before any repair execution, the producer must now:

1. verify and record all 220 payload members plus three manifests in the
   historical runtime, pool and retrieval freezes;
2. allow only generated `__pycache__/*.pyc` files outside those legacy
   manifests and reject every other extra file;
3. verify and record every member of the accepted Mistral input freeze, BGE
   synthetic preflight and completed `a0_query` stage, plus the stage's
   root-level `EXECUTABLE_FREEZE.json`;
4. verify and record the six exact BGE snapshot files authenticated by the
   accepted preflight;
5. freeze the `a0_query` independent acceptance, repair producer, independent
   validator, imported a0 validator, canonical runtime, Python executable,
   protocol and this amendment; and
6. rehash every recorded input after BGE unload and before writing a PASS
   receipt.

The independent validator separately reconstructs every required path, requires
exact equality with the executable freeze, checks exact manifest coverage and
BGE asset identity, and reconciles the producer's output-file records and
operational counters. This supersedes the earlier subset-only condition in the
same prospective amendment; no repair execution occurred between the two.

Six focused repair tests pass, including executable tests for full legacy
payload binding, the narrow generated-pyc allowance and exact current-manifest
coverage. The complete Mistral suite passes 191 tests. The real historical
manifests currently authenticate 56 runtime paths, 59 pool paths and 108
retrieval paths including each manifest; the accepted BGE preflight contributes
three paths and six separately frozen model assets.

No repair stage, BGE model load, benchmark embedding forward, Gold access, test
access or fit occurred while making or testing this amendment. The active
`a0_query` source and all 31 of its frozen inputs remain unchanged.
