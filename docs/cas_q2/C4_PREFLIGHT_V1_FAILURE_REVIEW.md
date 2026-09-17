# C4 preflight V1 failure: client anomaly review

Reviewer: Research Project Lead, Astra xhigh. Date: 2026-09-12.
CAS Q2 STATUS: **NOT READY**.

**Accept the diagnosis and preservation; the preflight remains FAILED.**
The scientific namespace `outputs/cas_q2/empirical_scoring_gpu_preflight_v1`
remains in place with manifest
`c03555a4a3562be34345bd79b35abb11c8b6bb913a4c812e24837cfb8c88f3b6`.
Do not move, overwrite, resume or reseal it.

## Evidence and finding

The authentic receipt records two top-level BGE forwards for 22 invented answer
texts. At the first likelihood preparation, Qwen had loaded its weights but
attempted no forward. Its forward ledger is empty; no NLI stage began. The
430 nested module-forward events are internal BGE calls, not 430 top-level
inferences. Fitting, answer generation, new retrieval and fresh Gold counters
remain zero. Source commit is `2b12a742b70e254340c062dfe5987012dba0f399`.

The traceback follows `ReaderLikelihoodScorer._prepare`, the pinned tokenizer's
chat template, Jinja `Environment._generate`, and `jinja2.compiler.generate`.
The unchanged guard rejects every Python function named `generate` without
considering code identity. This Jinja function compiles a template AST into
Python source; it is not a neural answer-generation call.

An independent CPU-only process rendered invented text without the guard and
reproduced the exact rejection with the original composed stage guard. Both
loaded Jinja functions matched code recompiled from their authenticated source
bytes. No model or benchmark was used in this probe. Existing guard tests covered
fit/read/write/forward restrictions, but did not exercise cold Jinja compilation.
The preflight therefore exposed an untested package integration condition.

The client rehashed all five manifested scientific files and verified the exact
six-file namespace, all 428 frozen inputs and all 30,912 inventory files. It
archived and reopened the six original files. The original scientific process
console was streamed to the tool and was not saved as independent raw stdout/
stderr files; this limitation is explicit. Newly captured probe logs are actual
subprocess bytes. No reconstructed transcript is presented as an original log.

Audit manifest:
`cbb9911c17c7c1b3f65f31d36b79814383bbba42a4cf4477b483ab1d9b2efc13`.
Private archive:
`d4c3b1a62046dff39ee47b9cd4c4a2e71ddfd80232b2aa64f2843da74a01d97b`.
Machine-readable record: [results](C4_PREFLIGHT_V1_FAILURE_RESULTS.json).

## Decision and remaining work

Permit a prospectively frozen execution binding that recognizes only the exact
authenticated Jinja compiler function entered by its exact original direct
caller. No generic module/path/name exemption is accepted. Preserve the original
guard and scientific source bytes and use a new V2 preflight namespace. The
[correction contract](C4_JINJA_EXECUTION_BINDING_V2_CONTRACT.md) defines the
positive/negative CPU gate and full original GPU fixture scope.

CPython disables profiling after a profile callback raises. This was observed
in the independent rejection probe. Each negative fixture must therefore use a
fresh guarded process; an experiment must abort after any denial and can never
continue scientific work by catching it. Every nested call below an allowed
Jinja entry remains subject to the original guard.

P0: accept the correction's CPU gate, then complete the original GPU preflight,
C4 scoring and prelabel validation before cost/D and contribution assessment.
P1: preserve complete cost accounting, historical provenance limits and delivery
evidence. P2: journal/CAS qualification remains pending, without extra model or
dataset search. Current result/novelty evidence remains insufficient for submission.
