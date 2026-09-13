# Phi development validation V4 failure and validator-only corrigendum

Date: 2026-09-13 (Asia/Shanghai)  
Decision level: GPT-6 Astra xhigh anomalous-result audit  
Status: **V4 FAILURE PRESERVED; ONE CORRECTED VALIDATION AUTHORIZED**  
CAS Q2 status: **NOT READY**

## Observed terminal facts

The blank Phi V4 canonical acquisition completed 13,500 traces and sealed with
`PASS_PHI_DEVELOPMENT_RUNTIME`. Its fixed 180-trace replay separately sealed
with `PASS_PHI_DEVELOPMENT_REPLAY` and `replay_exact_match=true`. The first
independent validator invocation then failed in the immutable namespace
`phi_reader_development_runtime_validation_v4` with diagnostic
`independent render/guard reconstruction`.

The failed namespace and its external execution evidence must remain unchanged:

| Evidence | Bytes | SHA-256 |
|---|---:|---|
| `VALIDATION_FAILURE.json` | 2,282 | `57448f853d9062a66da92daeac4e516f3ba673af7dcdaf637b05c56dd8dddeb8` |
| failed validation `SHA256_MANIFEST.json` | 282 | `fa63d1fe59aff313643c5d809efd9bd0e6e5c66049005e40f3e767301650cc67` |
| V4 launch metadata | 2,358 | `d77f7a75734f61a883ac309f170b2c19ea4a0044419be77e867430151e2f8383` |
| V4 stdout | 46 | `fee80c7a04f3004359a1c4cf84419ebe0244d2a4db1dcd7de24f02199bd4a876` |
| V4 stderr | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| stopped postcanonical result | 362 | `3de152fe4a845afa8dd3e8aa69e6931b1ebfc649031cafe8da70dd48e26487e0` |
| stopped evidence-collector result | 344 | `0dd81df9f1bff4143d62e05d5c1d55c54a35b165c87567de607fbd65f8673307` |

The validator source that failed has SHA-256
`2f2d7b6b20dccefad800da913247b89d78426dea1e6e9c3dcfdc3dbf2057c411`
at runtime source commit `3d6c060cad47a09cce49927fad3dbda80f2a0fc0`.

## Root cause

This is a validator-only schema omission. Every producer generation receipt
stores a `render` object containing five fields: `text`,
`context_truncated`, `context_budget_characters`,
`ordered_passed_document_ids`, and `per_document_truncated`. The independent
validator reconstructed the same rendered text and used it to recreate the
prompt, prompt SHA-256, complete input-token sequence, input length and attention
mask. Those checks passed immediately before the failing assertion. However,
its reconstructed `render` object returned only the four metadata fields and
omitted `text`, then compared that four-field object for equality with the
producer's five-field object. The comparison therefore fails even when the
rendered text is identical.

The correction adds the independently reconstructed `text` value to the
validator's `render` object. This does not relax an assertion. It makes the
existing whole-object equality check cover the complete producer schema,
including the rendered evidence text. A regression test must prove that a
changed `render.text` is rejected.

## Prospective execution boundary

Exactly one corrected validation is authorized in the new single-use namespace
`phi_reader_development_runtime_validation_v4_corrigendum_v1`, after this
corrigendum, validator source and tests are committed and the worktree is clean.
The command must bind two different commits explicitly:

- immutable runtime source commit:
  `3d6c060cad47a09cce49927fad3dbda80f2a0fc0`;
- corrected validator source commit: the clean commit containing this file.

The validator must continue to rehash the exact sealed canonical and replay
manifest pins. Its executable input freeze must include this corrigendum and
record both commits. All other validation logic, tokenizer-only model boundary,
counts, prompt reconstruction, retrieval reconstruction, byte-identity checks,
Gold/fit/forward prohibitions and fail-closed behavior remain unchanged.

The canonical acquisition and fixed replay must not be rerun, edited, copied or
resealed. No new Phi reader acquisition namespace is authorized. A corrected
validator failure is terminal and does not authorize another correction or
retry. Test generation, scientific fitting, action scoring, Gold access and the
Mistral reader remain closed until the corrected validation, external gates and
Astra xhigh P0-1 authenticity audit all pass.

**CAS Q2 STATUS: NOT READY.**
