# Phi reader development runtime contract

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

This contract implements the next stage of
`PHI_READER_REPLICATION_PROTOCOL_V1.md` after the accepted compatibility and
value-blind input gates. It authorizes the fixed 4,500-question development
runtime only. It does not authorize the 6,000-question test runtime, scientific
head fitting, test Gold, outcome analysis or claims.

The sealed failed namespace `phi_reader_development_runtime_v1` is immutable
and may never be resumed or reused. The only prospective corrected names are
`phi_reader_development_runtime_v2`,
`phi_reader_development_runtime_replay_v2` and
`phi_reader_development_runtime_validation_v2`.

## Exact scope and inputs

Use the original accepted `outputs/daa_v2_fresh_v1` label-free development
assets: 13,500 canonical traces, with 1,500 questions in each dataset and all
three BM25/dense/hybrid siblings. Preserve the accepted 3,600-fit/900-calibration
question roles but do not read their target labels in this stage. Original
evidence is the sealed Top-5; original-question retrieval is forbidden.

Use only `microsoft/Phi-3.5-mini-instruct` revision
`2fe192450127e6a83f7441aef6e3ca586c338b77` in CUDA BF16 and the fixed BGE
revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` for newly emitted repair
queries. Use the unchanged prompts, all-five-header 16,000-character renderer,
greedy 48-token answer cap, greedy 64-token repair-query cap, same-retriever
depth-50 repair and rank-5 replacement. Batch size and active reader instances
are one. Do not reuse any Qwen answer or Qwen repair query.

For every trace, execute in order: Phi original answer (`a0`), Phi repair query,
fixed repair retrieval, then Phi repaired answer (`a1`). The planned total is
40,500 logical Phi generations and 13,500 repair retrievals; BGE query forwards
occur only for the dense and hybrid siblings. Save the same four private ledgers
as the authenticated original runtime: generation receipts, repair bindings,
branch provenance and canonical branches. Add guard-admission counts and CUDA
peak allocation without changing prompt, generation, parsing or retrieval
semantics.

## Binding token and failure boundary

Before installing the scientific IO audit, authenticate `source_paths`, every
input record and every predecessor manifest.  Then import and configure the
accepted torch/transformers framework and assemble the already authenticated
native runtime definitions, without constructing or loading a model.  The
runtime freeze and final receipt must record that exact audit-boundary start.
The boundary is installed before either Phi or BGE is loaded, before the CUDA
device-start query, and before runtime trace or dataset content is interpreted.
Framework directory scans under the original or implementation `.venv` are
environment operations and are allowed; all other project-directory scans
remain limited to authenticated member parents.

Wrap the exact tokenizer used by the authenticated reader so the same tensor
batch returned to the original `_generate` method is checked before its CUDA
transfer and `model.generate`. Each `a0`, `repair_query` and `a1` call must have
one row, an aligned all-one mask and at most 9,472 input tokens. The wrapper may
observe and reject; it may not change a token, mask, prompt or generation kwarg.
Record the exact admitted length and require it to equal the native generation
capture. The dynamic `a1` path has no exemption.

Any unexpected model/tokenizer revision, non-deterministic setting, malformed
trace, asymmetric failure, overlength prompt, missing document, model error or
boundary denial stops the stage. Preserve the output namespace, completed
durable journal rows, stderr and exact phase. Do not restart completed calls,
shorten prompts, drop a trace or switch models. A process interruption may
resume only the same namespace after validating its executable freeze and every
completed journal row; no completed generation may run again.

## Replay and validation gates

After all 13,500 canonical traces finish, execute the already selected 180-trace
development replay subset, 20 per dataset/retriever cell. Require byte-identical
saved rows for all four ledgers. This is a real 540-generation replay and must be
counted separately.

A separate independent validator must load no reader, BGE or NLI model. It must
reconstruct trace order, prompt/token metadata from saved witnesses, repair
invariants, branch/provenance hashes, role membership, counts, guard admissions,
input/source hashes and exact replay equality. Client acceptance follows that
validator. Development scoring, development target mapping and the ten fits
remain closed until this complete runtime gate passes.
