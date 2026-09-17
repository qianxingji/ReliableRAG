# Full empirical delivery: explicit path design and first assembly gate

Research Lead decision, 2026-09-11, before implementing the path adapter.
CAS Q2 STATUS: NOT READY.

Offline numerical replay and the separate neural-package/CPU environment are
accepted. Full empirical delivery still needs immutable input/output closure,
model assets, the completed stage receipts and a tested mapping of stored paths.
The live C3 namespace cannot yet be packaged as a completed accepted experiment.
Keep canonical C3 and original C4/D controllers unchanged and follow their gates.

## Full delivery requirements

Preserve original metadata/source/payload bytes and their existing digests. Give
each delivered file a logical original identity and a separate physical location.
Distinguish original-project, engineering-worktree and task-workspace roots;
never infer identity from filename alone or rewrite paths inside original JSON
to create matching manifests. Resolve only declared records, require exact
digest/size agreement and reject traversal, aliases, root-prefix confusion,
unknown files, symlinks/reparse points and collisions. A new delivery manifest
describes transport; it does not replace any historical manifest's authority.

Later full closure must include every bound scientific input, model/tokenizer
asset, accepted static source and completed stage output, plus all failed runs
needed to interpret the results. Libraries use the separate authenticated wheel
locks and environment receipts. Historical installed-package artifacts, including
old caches, must remain distinguishable from newly installed runtime packages.
Do not silently satisfy a frozen package-path check with a different environment.
Final replay requires its own prospective gate after the original stage gates;
definition identity or saved-file authentication alone is insufficient.

## First implementation: authenticated native source assembly

Implement a separate source/path adapter. It is not connected to the active
canonical process or frozen stage controllers. Copy the exact original source
and config metadata needed to assemble retrieval, reader/repair, base features
and V2 score definitions into new isolated roots. Bind copies to the accepted
acquisition/scoring inventories and native CPU-test metadata. Do not copy/read
fresh answers, score rows or Gold for this gate, load a model, fit an estimator,
perform a neural forward, regenerate retrieval or start a canonical stage.

Only the following already observed Path-valued support globals may be rebound,
after source authentication and execution, before any native assembly call:

| Original support | Explicit globals |
|---|---|
| retrieval_support.py | ROOT, OUT, POOL, COHORT, CACHE, SNAPSHOT |
| runtime_support.py | ROOT, OUT, RET, POOL, COHORT, CACHE, HIST |
| v3_support.py | ROOT, OUT, OLD, V2, RUNTIME, HIST, BASELINE, BINDING |

Require each original value to equal its prospectively declared path. Bind only
the new physical root plus the exact same relative suffix. Record every old/new
value. Leave model revisions, seeds, thresholds, feature names, source hashes,
generation boundaries and scientific function objects unchanged. Reject unknown
Path globals or changed expected bindings. The existing import_file utility is
the only function binding that may be replaced, by an authenticated source-only
loader that repeats this same policy for each supported native module. Bypass
bytecode caches explicitly; do not modify the source file or scientific bodies.

The native wrappers keep their own original source checks and AST extraction.
Compare their complete definition-identity records and generation-boundary record
with the already accepted native engineering receipts, not with a freshly
invented expected digest. Preserve all other support globals and function
identities. Record package namespace paths created by the original wrappers;
none may resolve to the old project. Permit only the packaged source/config
files, the new environment/base interpreter and a new audit output. Deny model
loads, estimator fits, neural forwards, raw-data reads and writes to source
copies. No fresh outcome access is authorized.

## Validation and limitations

Test actual traversal/prefix/collision/hash refusals and a supported path binding
with unchanged functions. Test that an unexpected source digest is rejected
before any module side effect. Run the real authenticated native assembly in two
separate fresh Python processes and different physical roots, including a root
with spaces and non-ASCII characters. Rehash every copied input after each run
and retain failure namespaces. No fallback to old project content is allowed.

A first-gate PASS means only that the unchanged native definitions and their
explicit IO path bindings assemble from authenticated relocated source/config
copies. It does not certify complete data closure, C3/C4 numerical/neural replay,
the D Gold boundary at runtime, library-path rebinding, another OS/host or full
submission readiness. Do not rename it as original unadapted controller replay.
Keep those remaining requirements visible in CURRENT_TASK and the evidence index.

P0 remains original C3 completion/fixed replay/acceptance, C4/full prelabel,
cost/D execution and contribution review. This P1 adapter addresses a real
delivery constraint without changing scientific design or the live experiment.
No P2 model/feature/seed/budget search is authorized.
