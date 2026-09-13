# Prospective C4 Jinja identity binding V2

Research Lead decision: Astra xhigh, 2026-09-12, before implementation or corrected
GPU execution. CAS Q2 STATUS: **NOT READY**.

## Scientific invariants and failed namespace

All three C4 scientific, neural-validation and execution contracts retain their
models, sample IDs, eligibility, seeds, precisions, batching, checks, tolerances,
failure rules, counters and original scientific bodies. This is a disclosed
execution/namespace binding, not literal unchanged CLI replay. The V1 preflight
manifest `c03555a4a3562be34345bd79b35abb11c8b6bb913a4c812e24837cfb8c88f3b6`
and all six files remain in place and FAILED. Preserve the independent failure
audit manifest `cbb9911c17c7c1b3f65f31d36b79814383bbba42a4cf4477b483ab1d9b2efc13`.

The only replacement output is `outputs/cas_q2/empirical_scoring_gpu_preflight_v2`.
It starts empty and executes the complete original invented fixture protocol:
22 semantic texts/two batches; 12 likelihood requests/eight forwards/four cache
hits and native 8192-token truncation; five completed NLI branches and the exact
second-hypothesis preparation failure. The two BGE forwards from failed V1 remain
counted as unsuccessful-preflight overhead. Do not splice their vectors into V2.
Unexpected failure in V2 aborts and preserves the directory.

## Exact compiler exception

Keep `empirical_scoring_guard.py` and `empirical_scoring_stage_guard.py` unchanged.
Add a separate binding in `scripts/empirical_scoring_jinja_binding_v2.py` that
installs the original composed guard, captures its profile callback, and routes
all events to that callback except this single Python call event:

- `frame.f_code` is the captured, source-authenticated
  `jinja2.compiler.generate.__code__` object;
- its module globals are the actual authenticated compiler module dictionary,
  with the original function still bound under `generate`;
- the direct caller's code object and globals are the source-authenticated
  `jinja2.environment.Environment._generate` and its original environment module;
- the caller's `self` is the callee's `environment`, and the environment module's
  `generate` reference still identifies the same compiler function.

Authenticate both modules before guard installation from the original environment
inventory, including these exact source pins and resolved paths:

| Source under `E:/paper/ReliableRAG/.venv/Lib/site-packages/` | SHA256 |
| --- | --- |
| `jinja2/compiler.py` | `f51a42425e57f3c0479652623ec1cf876f791e1d2e029bf0149350baeb542de3` |
| `jinja2/environment.py` | `f6786b3fb0a1f8d6c65f4d30bf2af8cb2fae84d1ead8e09ceb48201ab9e2fdf9` |

Use Jinja 3.1.6. Recompile these source bytes without execution and compare the
corresponding function code objects with the loaded originals; a claimed name,
path or `__module__` alone is insufficient. Freeze the source records and the
result of this comparison. Record the actual number of admitted compiler calls.
No model, tokenizer, template text or Jinja function is patched or prewarmed to
avoid an observed event. The bound profile remains installed for every nested
call; a call made from inside compilation gains no inherited exemption.

Every other `generate`, `fit`, `partial_fit`, `fit_transform`, retrieval, forward,
read/write, weight, import, network and subprocess event receives the existing
checks. Keep the existing stage-specific forward counters. Preserve the original
audit hooks. Never catch a denial and continue scientific execution: a callback
exception disables CPython profiling. Each negative test uses a new subprocess.

## Entry, freeze and predecessor continuity

Implement a separately named module entry
`scripts/run_roa_empirical_scoring_bound_v2.py`. Use repository-root `python -B
-X utf8 -m ...`; record full argv, interpreter, cwd and environment in external
run controls with captured raw stdout/stderr. The entry requires a pinned
per-stage binding config and a clean committed checkout. Check original CPU
acceptance/input source pins before making any in-memory bindings.

The permitted in-memory changes are limited to:

1. Change the shared `empirical_scoring_stage_io.STAGES['gpu_preflight']` value
   from the fixed V1 path to the fixed V2 path before `StageRun` or prerequisite
   resolution; require the old value is exactly V1. Base, GbV, policies and
   independent output paths remain as originally frozen. All later C4 invocations
   use the same bound entry, so original predecessor checks consume accepted V2.
2. Bind `empirical_scoring_stage_run.guard` to the exact-identity wrapper above.
3. Use a small versioned `StageRun` subclass at the selected original entry's
   `StageRun` name to append binding/config/test/failure-audit/Jinja controls to
   the original input records before `prepare`, and add a separate binding
   receipt before original finalization. Invoke unchanged parent lifecycle
   bodies and unchanged selected entry `main`/scientific loops. Do not alter or
   subclass model/tokenizer code. Do not import executor or witness modules into
   the independent validation entry merely to bind paths.

The binding config records the full before/after path map, source/contract pins,
original failed preflight and failure-audit pins, actual command and accepted
C3 manifest `dc2905224798b07302db8950f68db228de1faff9042c44dbaee7111ba107878f`.
No supplied arbitrary output override is permitted. Include all added controls
in each stage's original executable freeze and final file manifest. The binding
receipt must name altered globals and demonstrate original function/source
identity and intact predecessor validation. Check active profile identity before
success finalization; then let the original finalizer remove profiling normally.
Do not write a prelabel seal in an individual scoring stage.

## Required CPU acceptance before any V2 GPU run

Implement `tests/test_empirical_scoring_jinja_binding_v2.py` and a single-use
invented-only fixture controller with real raw logs, immutable source/input
freeze and a reviewed result. These tests must use original guard composition:

- Cold Jinja compile/render succeeds with exact invented output and a nonzero
  admitted-compiler count; original guard reproduces the failure separately.
- The actual pinned Qwen tokenizer's cold `apply_chat_template` returns identical
  prompt text and token IDs under the bound guard and an unguarded reference in
  separate CPU processes. No weights, benchmark text or model forward is loaded.
- Reject standalone, object-method and project/model-named `generate` functions
  before a sentinel side effect. Reject wrong code with forged module/path and
  changed source pins; reject direct calls to the actual Jinja compiler from an
  unauthorized caller. Reject a nested invented generation call during otherwise
  admitted template compilation, proving descendants are still checked.
- In fresh processes, retain fit/partial_fit/fit_transform, raw benchmark,
  unlisted input, external write, network/subprocess, wrong-stage weight and
  CPU-stage forward denials. Assert each denial reason and that its body did not
  run. Do not aggregate profile exceptions in one continuing process.
- Test all five stages' fixed path map, same-object aliases, immutable V1 failure,
  rejection of wrong/missing predecessor hashes, unchanged C3/full predecessor
  checks, config pin mismatch and existing-output no-overwrite. These gate tests
  may use invented manifests for nonexistent downstream stages; do not claim
  actual future-stage acceptance from them.
- Verify the added controls appear in the executable/final manifests, and that
  binding metadata is added without modifying original scientific result fields.
  Verify original source bytes and source/code identities before/after tests.

Sol High implements and runs this bounded CPU work. Only a reviewed complete
CPU PASS authorizes one full V2 GPU preflight. New anomalous results return to
Astra xhigh; normal successful execution/analysis remains Sol High. Complete
C4 independent/fairness acceptance is still required before any current Gold.
