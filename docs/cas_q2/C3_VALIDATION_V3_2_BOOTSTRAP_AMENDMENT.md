# C3 V3.2: isolated-mode bootstrap amendment

Research Lead decision, Astra xhigh, 2026-09-12 Asia/Shanghai.  
**CAS Q2 STATUS: NOT READY.** This prospective amendment follows an independently
audited V3.1 launch failure. It changes only the Python entry bootstrap. The V3.1
binding, entry, runtime config, data, helpers, thresholds, literal comparisons,
environment identities and expected hashes remain unchanged.

## Preserved V3.1 failure

The first full V3.1 controller launched the entry by absolute filename under
Python `-I`. The entry imported `scripts.validate_roa_empirical_runtime_bound_v2`
at module load, before it could read its config and insert the authenticated
repository root into `sys.path`. It therefore exited at line 10 with
`ModuleNotFoundError: No module named 'scripts'`.

The failure task manifest is
`ea708bac7c7d5c323327b55bd738324a20459435c581dce930f5e11e41413c1a`.
The independent audit manifest is
`8c096f320c6c839cfc56fcb519ccef3addcb41c2d27b6739241db376781f0bde`.
That audit confirms the child did not read the configuration or any runtime
payload and performed zero generation checks, Gold reads, neural forwards and
fits. The standard runtime remained its fourteen original files; both prior
failure siblings and all 30,823 environment files were unchanged.

This is a literal V3.1 failure and remains preserved. It is not evidence about
repair arithmetic, generation receipts or any scientific endpoint.

## Sole correction

Add a new bootstrap file that uses only Python standard-library modules before
inserting the exact repository root derived from its own authenticated path.
Under isolated mode it must verify the expected repository path, insert that
path once, and execute the unchanged V3.1 entry as `__main__`. It must contain no
scientific helper, payload reader, model call, fit, environment modification or
fallback path.

Before another full launch, a fresh two-case gate must execute the bootstrap
from a directory outside the repository with the exact `-I -B -X utf8` flags.
`--help` must exit zero without stderr. A frozen invented invocation with a
deliberately wrong config hash must reach and fail at `V3_BINDING_CONFIG_PIN`,
showing that repository import succeeded while stopping before config parsing or
payload access. The gate must inspect the bootstrap AST and preserve the V3.1
entry/binding hashes. A separate client audit must accept all of this evidence.

Only after that acceptance may one V3.2 launch execute the unchanged V3.1
validator. Bind the V3.1 launch failure and audit, bootstrap gate and audit, all
earlier V1/V2/V3/V3.1 failures and every previous control in the execution
freeze. Any later failure is retained and stops C3; no automatic retry follows.

The correction is scientifically permissible because no current payload or
numeric outcome was observed by the failed child and no scientific code or
acceptance rule changes. It does not erase the V3.1 failure or create historical
thread provenance.
