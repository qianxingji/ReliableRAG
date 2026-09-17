# Mistral production-adapter invented preflight acceptance

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PASS_MISTRAL_PRODUCTION_ADAPTER_INVENTED_PREFLIGHT`.

V3 executed the exact pinned Mistral NF4 adapter and passed an unchanged,
separate no-model validator. This closes the production adapter's invented
generation, likelihood, transaction-journal, compact-witness and unload gate.
It does not make Mistral an accepted scientific reader condition and does not
authorize any claim about Recovery, Damage or `HGB_ONLY_R`.

## Accepted result

- Exact model/revision: `mistralai/Mistral-7B-Instruct-v0.3` at
  `c170c708c41dac9275d15a8fff4eca08d52bab71`.
- One NF4/double-quant/BF16/eager CUDA-only model load and one unload.
- Three invented generation operations: `a0`, repair query and `a1`.
- Four answer-token likelihood operations: L00, L01, L10 and L11.
- 51 physical model forwards; seven logical operation receipts.
- Correct native chat prefix after the V3 correction: one BOS, then `[INST]`;
  no second special-token pass.
- All seven intent/result journal pairs bind the exact operation input and
  durable receipt hash.
- Seven finite 32,768-way FP32 first-token witnesses were saved. The independent
  validator reconstructed the prompts and targets, checked greedy first tokens,
  and recomputed all seven first-token softmax values.
- Independent validator checks: 105; model loads/forwards in the validator: 0.

The invented `a0` output was `insufficient evidence`, `a1` was `Lyon`, and the
repair query was `What is the name of the city where Ada was born?` without
parser fallback. These values are retained as path witnesses, not as quality
evidence or tuning signals.

## Resources and release boundary

- Wall time: 32.4210 seconds.
- Peak CUDA allocated/reserved: 7,248,023,552 / 7,419,723,776 bytes.
- CUDA allocated after `close()`: 33,555,456 bytes.
- Process peak working set: 5,903,687,680 bytes.
- Compressed seven-vector witness: 397,466 bytes.
- Project rows, Gold values and scientific fits: all zero.

The producer report SHA-256 is
`96a3e15f823ffe45f802c4d65d0029643a08438391143c7a475558ca898b1a3e`;
the sealed namespace manifest is
`19b92adc235c17d3b45ff528769853f7549755ebb398a7d3dc0b74019d81a659`.
The witness SHA-256 is
`c77dbe952935697cca82067830ca04e5e70d0ef9cecd36d8f4e0f6165af99372`,
and the independent validation report SHA-256 is
`0b9fec93c50f2943c8b2adea5d024323d8fc5b7a636b80bfa21d48c29f2e2591`.
The external V3 attempt log contains one start and one pass event and hashes to
`3290a04d20bcb7dcf6f7e3b3d59a983186e34b85d76f4537a29875908418cff4`.

## Preserved failures

V1 failed before model construction because the integer CUDA device had not
been initialized before peak-stat reset. V2 completed invented inference but
failed independent prompt reconstruction because generation prepended a second
BOS. Both namespaces and attempt records remain immutable. V3 fixes only those
two independently diagnosed engineering defects; no output quality or project
result was used to choose either correction.

## Next P0 gate

Implement the formal component-sequential development executor and its
independent validator. It must use the accepted Qwen label-free development
input chain directly, keep Mistral and BGE/NLI nonconcurrent, use the exact
durable journal and 18 value-blind witness positions, reject dynamic `a1`
prompts above 8,192 tokens before CUDA, and expose zero Gold/fit access during
branch acquisition. Formal 13,500-trace generation has not begun.
