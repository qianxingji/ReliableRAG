# Mistral development HGB-signal input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running and before HGB-signal execution. It
changes no HGB artifact, feature formula, eligibility rule, prediction formula,
label, endpoint, candidate grid or tuning rule. It strengthens only the input
and executable provenance of the not-yet-run fixed-model inference stage.

## Gap

The initial implementation pinned the historical HGB artifact and several
source files, but it recorded only the legacy/runtime and predecessor manifest
files rather than every payload member they authenticated. The independent
validator checked frozen rows and the semantics validation receipt but did not
reconstruct the complete direct path set or bind the producer receipt to both
saved HGB ledgers. Because this stage reconstructs evidence and likelihood
features from original sources and three acquisition stages, that boundary was
too narrow.

## Prospective correction

Before loading the fixed HGB artifact, the producer must now:

1. verify and record all 220 historical runtime, pool and retrieval payload
   members plus their three manifests, allowing only generated
   `__pycache__/*.pyc` extras in those legacy namespaces;
2. verify and record every member of the accepted Mistral input freeze,
   answer-semantics stage, `a0_query`, repair and `a1_likelihood`, plus the
   independent semantics validation receipt;
3. record the pinned historical preflight, method freeze, 639,652-byte HGB
   artifact, answer-normalization source and state-symmetric feature source;
4. record the producer, independent validator, acquisition/scoring helpers,
   independent feature formulas, evaluation package sources, frozen scoring
   protocol, this amendment and required native runtime files; and
5. rehash every recorded input before writing the PASS receipt.

The independent formula-level validator reconstructs the identical path set,
requires exact equality with the executable freeze, validates exact recursive
manifest coverage, independently rebuilds every feature row and HGB symmetry
score, and binds the producer receipt to `HGB_FEATURE_ROWS.jsonl` and
`HGB_SIGNAL_ROWS.jsonl`.

Seven focused HGB tests cover exact model identity, independent feature and score
formulas, prerequisite/zero-neural guards, exact input-graph requirements and
rejection of an unexpected manifest file. The complete Mistral suite passes 162
tests.

No HGB project inference, HGB fit, neural model load or forward, Gold access or
test access occurred while making or testing this amendment. The active
`a0_query` executable, source commit and all 31 frozen inputs remain unchanged.
