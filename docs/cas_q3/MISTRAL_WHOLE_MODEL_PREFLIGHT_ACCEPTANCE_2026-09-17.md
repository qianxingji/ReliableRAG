# Mistral whole-model NF4 preflight acceptance

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PASS_BOUNDED_MISTRAL_NF4_WHOLE_MODEL_PREFLIGHT`.

The single attempt authorized by
`MISTRAL_WHOLE_MODEL_PREFLIGHT_PROTOCOL_2026-09-17.md` completed and its saved
witness passed a separate no-model validator. This closes the short-input model
load and invented-path gate. It does not constitute a scientific reader
experiment or a second accepted reader condition.

## Exact execution result

- Model loads: 1.
- Quantized projections: 224/224 expected transformer projections.
- Quantization: NF4, nested/double quantization, BF16 compute.
- Nonquantized embedding and language-model head: BF16.
- Device map: the entire model on CUDA device 0; no CPU, disk or meta parameter.
- Ordinary linear modules outside the quantized set: `lm_head` only.
- Attention: eager; batch size one; deterministic algorithms and TF32-off
  environment matched the prospective protocol.
- `model.get_memory_footprint()`: 4,027,064,576 bytes.

The answer fixture generated `Paris` in two tokens in both repetitions, with
identical token IDs and identical full-vocabulary FP32 processed scores. The
repair fixture generated 29 tokens and produced both required lines:

```text
Missing fact: The birth city of Ada is located in which country?
Search query: In which country is Northport located?
```

The teacher-forced `Paris` target used two tokens. Its two forwards produced
exactly identical full-vocabulary FP32 answer-position logits and chosen-token
log probabilities `[-11.877450942993164, 0.0]`. The independent validator
recomputed these values from the saved logits in float64; it did not trust a
reported summary.

## Resource result

- GPU total: 17,102,864,384 bytes.
- GPU free before load: 15,908,995,072 bytes.
- Peak CUDA allocated: 7,248,023,552 bytes.
- Peak CUDA reserved: 7,392,460,800 bytes, below the frozen 12 GiB limit.
- Available host RAM before load: 12,494,147,584 bytes.
- Minimum sampled available host RAM: 7,369,728,000 bytes, above the frozen
  4 GiB floor.
- Process peak working set: 5,909,372,928 bytes, below the 20 GiB limit.
- Producer wall time: 30.2879 seconds, below the 20-minute limit.
- Witness size: 1,814,658 bytes, below the 8 MiB limit.

These figures cover short invented prompts only. They are not a worst-case
8,192-token memory or throughput measurement.

## Authenticity and independent validation

The producer report is
`MISTRAL_WHOLE_MODEL_PREFLIGHT_2026-09-17.json`, SHA-256
`0fe4ba64da06fa5b51b8723ac22e3365d9bf4aec8e2d7a55b9b8ec742f56e13c`.
The compressed full-vocabulary witness is
`MISTRAL_WHOLE_MODEL_PREFLIGHT_WITNESS_2026-09-17.npz`, SHA-256
`7a240d0f7be41823609a5dfdbe0905eb987518431f37fcc56cf9624c0c00baed`.

The independent validation report is
`MISTRAL_WHOLE_MODEL_PREFLIGHT_VALIDATION_2026-09-17.json`, SHA-256
`83cff69255862d1413dca997f9ba3e41c152504b33b1f51a5ff777b4746ec29c`.
It passes 95 checks. It reloads only the tokenizer, reconstructs both prompts,
decodes both outputs, proves every generated token is the score argmax,
recomputes answer-position log probabilities, checks all array hashes and
resource limits, and validates the reported quantized module-name set. It
performs zero model loads, generations or neural forwards.

The external append-only attempt log contains exactly one start and one
completion event, with no failure or retry. Its SHA-256 is
`777729f94e761b02de023b0c367f625e6f008a4366de3f13f3c60b6cf436bea7`.
Both events state zero project rows, zero Gold and zero scientific fits.

The producer, validator and protocol retain their prospectively committed
hashes:

- producer: `02b6892c01a964c144b14be925f5000a074f555980953126788937e33e354550`;
- validator: `e0049d85fd61a14707eb1df83547ccc58e53da35c226ec3c8573a3321990f801`;
- protocol: `bde63c4e7ca8da5a668a0cd9008b72aad4fb88bd6a2de44d0c85c1f76667626e`.

## Remaining P0 before formal reader execution

1. Bind the exact accepted Qwen development/test IDs, retrieval artifacts,
   prompt inputs and label isolation into a Mistral-specific immutable input
   manifest without reading test Gold.
2. Implement and validate the production adapter using this exact tokenizer,
   quantization and device contract; preserve shared retrieval, repair and GbV
   semantics rather than substituting Phi failure artifacts.
3. Predefine compact generation, likelihood and GbV/NLI replay witnesses,
   numerical comparisons, cache keys, failure/eligibility rules and storage
   ceilings. Full-vocabulary arrays are limited to sampled witnesses, not all
   18,000 traces.
4. Measure worst observed input lengths before model execution and run a bounded
   longest-invented/input-shape resource gate. The current short preflight alone
   cannot establish 8,192-token feasibility.
5. Freeze the full-workload wall-time, disk, interruption/resume and archival
   protocol, followed by development-only tuning selection and the primary
   test comparison family. No test-guided configuration choice is allowed.

Main rejection risks remain the weak/uncertain increment over HGB-only, only one
currently accepted reader, one repair operation, already-viewed question set,
rare Damage events and incomplete end-to-end public neural reproducibility.
This preflight reduces execution risk; it does not yet reduce the empirical
Claim risk.
