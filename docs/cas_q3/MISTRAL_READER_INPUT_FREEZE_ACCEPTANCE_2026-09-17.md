# Mistral reader value-blind input-freeze acceptance

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `ACCEPTED_VALUE_BLIND_MISTRAL_INPUT_FREEZE`.

The corrected module-mode producer and a separate non-importing validator both
pass. This accepts exact development/test membership, original-evidence prompt
identity and deterministic input lengths for `a0` and repair-query generation.
It also fixes the mandatory dynamic `a1` guard. It does not authorize formal
reader generation, fitting, test Gold or a scientific claim.

## Complete scope and result

- Development: 4,500 question groups / 13,500 traces, with 3,600 fit and 900
  calibration questions.
- Test: 6,000 question groups / 18,000 traces.
- Deterministic prompt rows: 31,500.
- Exact tokenizations: 63,000.
- Maximum deterministic prompt: 3,675 tokens, a development 2Wiki dense
  repair-query prompt at canonical position 8,698.
- Headroom to the 8,192-token guard: 4,517 tokens.
- Context truncation: 0 rows.
- Batch size and concurrent reader instances: one.

The maximum prompt SHA-256 is
`224afb725f7c4d61392adb74605f0e061db48a15d08cbfd164d6610daac894f7`;
its canonical token-ID-list SHA-256 is
`02b6aa705f82f6513b8d4ba9d6a80a406a339de52256c7397236140f7eaf20d2`.
The future repaired-answer prompt remains dynamic because it includes the newly
generated Mistral repair query. The production runtime must tokenize and reject
any `a1` prompt above 8,192 tokens before CUDA/model access. Generation prompts
are never silently truncated.

## Provenance and access boundary

The source chain is the accepted Qwen label-free development/test inputs:
questions, original Top-5 evidence, canonical trace order and development roles.
No Phi artifact appears in the producer allowlist or result ancestry.

The producer audit boundary recorded 98 Python-environment files and no denied
read, write, weight, network or process event. Both producer and validator state
zero model loads, neural forwards, generations, scientific fits, existing-answer
reads and Gold reads.

The producer namespace is
`outputs/cas_q3/mistral_reader_input_freeze_v1`:

- recursive manifest SHA-256:
  `588b4d86fb6048ade1bba52731829496772d62fd522a260a7a4c60ec584586ca`;
- build receipt SHA-256:
  `d619e024d55be7d5623a96943c5ad60a0ca109ad06963cb55e0bbdcd7c5a96f7`;
- executable freeze SHA-256:
  `7e4cbd7be1f1be4d5c84759733cdb423e68f00499dd2c8d53b5f8e91eb5e8030`;
- 27,763,173-byte private ledger SHA-256:
  `538970511fe517a21ef7baee4dc5eb216ce748b2c2222b3960c356a53a12f8ac`.

The independent validator rehashed every producer input, reconstructed all
31,500 rows and all 63,000 tokenizations, and exactly reproduced every
stratum maximum and the global maximum. Its namespace is
`outputs/cas_q3/mistral_reader_input_freeze_validation_v1`:

- recursive manifest SHA-256:
  `d6d97158a3662b84bf3da81592fe86fc9e11a3251db2e9aeeb593d70d7460917`;
- validation receipt SHA-256:
  `4e7cce9f0d54b06bc0c1029c3b070d061de26956300be3258ef8e84532d1424e`.

The tracked summary is
`MISTRAL_READER_INPUT_FREEZE_RESULTS_2026-09-17.json`. The external attempt log
SHA-256 is
`79d4e2d035af9394f317607183cb51a4dcfc74b97839f56a109b48cadaee69d4`.
It retains the initial zero-access direct-script import failure, corrected
launch start/completion and independent validation completion.

## Next gate and remaining risk

The next P0 gate is a one-load resource preflight using invented token content
at the accepted longest observed shape, followed by production-adapter and
compact replay/storage validation. The current 3,675-token census substantially
narrows the earlier 8,192-token uncertainty but does not itself prove that
prefill plus generation fits.

No new reader answer, recovery, damage or HGB-only comparison exists yet. The
main rejection risks remain the uncertain increment over HGB-only, only one
scientifically accepted reader, one repair action, previously observed question
set, rare Damage events and incomplete public end-to-end neural reproduction.
