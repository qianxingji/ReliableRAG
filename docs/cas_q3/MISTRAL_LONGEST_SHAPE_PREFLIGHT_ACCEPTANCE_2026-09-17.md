# Mistral longest-observed-shape resource acceptance

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PASS_MISTRAL_LONGEST_OBSERVED_SHAPE_RESOURCE_PREFLIGHT`.

The single prospectively authorized model load completed the exact 3,675-token
invented prompt shape and all 64 forced decode steps. A separate no-model
validator passed 49 checks. This closes the maximum observed fixed-prompt shape
for the reader alone on this host; it is not a benchmark result.

## Result

- Prompt shape: batch 1 × 3,675 tokens.
- Invented token construction: `[1, 3] + [1000] * 3672 + [4]`.
- Decode steps: exactly 64, with EOS disabled only to force the resource
  upper-bound witness.
- Quantized modules: all 224 expected projections, NF4 nested/double quantized
  with BF16 compute.
- Parameters: CUDA 0 only; no CPU, disk or meta placement.
- Model memory footprint: 4,027,064,576 bytes.
- Producer wall time: 33.8919 seconds.
- Peak CUDA allocated: 9,189,349,376 bytes.
- Peak CUDA reserved: 12,561,940,480 bytes (about 11.70 GiB), below the frozen
  14 GiB limit.
- Minimum sampled GPU free memory: 3,282,042,880 bytes.
- Process peak working set: 5,907,988,480 bytes.
- Minimum sampled available host RAM: 7,147,470,848 bytes.

The 64 × 32,768 FP32 processed-score matrix is finite, and every saved generated
token is independently the row argmax. The compressed 3,796,483-byte witness is
below its 12 MiB limit.

## Evidence

- Producer report:
  `MISTRAL_LONGEST_SHAPE_PREFLIGHT_2026-09-17.json`, SHA-256
  `d81b5334522ce3fe937683886cb8f34978a671ba4aae72a71f47cf9af045ff5a`.
- Full-score witness:
  `MISTRAL_LONGEST_SHAPE_WITNESS_2026-09-17.npz`, SHA-256
  `caf91522e2394c1dd6834dea3a547be79073a6b22e838d11c33f4be713f65b76`.
- Independent validation:
  `MISTRAL_LONGEST_SHAPE_VALIDATION_2026-09-17.json`, SHA-256
  `9dfae6630bd7aa4cc136a5d6a141bbcaa4b3b9447a42e52aa1720d40fbd27f04`.
- External append-only attempt log SHA-256:
  `425b4b912a330096ca97605f4c796f60b61135bb7a9d3886b78409081b12e5b3`.

The attempt log contains one start and one completion, with zero project-content
tokens, Gold and scientific fits. The validator performs zero model loads or
neural forwards.

## Production implication

Only about 3.06 GiB remained free at the observed peak. The formal runtime must
therefore treat Mistral as an exclusive GPU component. It must complete and
seal generation plus reader-likelihood work, release the model and clear its
CUDA allocations before loading BGE or NLI components. Concurrent Mistral+BGE
or Mistral+NLI execution is not authorized by this preflight.

The reader remains subject to the 8,192-token pre-CUDA guard for every dynamic
`a1` prompt. The 3,675-token pass does not prove an unseen longer dynamic prompt
will fit; an over-guard row fails rather than truncates or expands the budget.

P0 still requires the production adapter, durable journal/resume contract,
compact sampled replay witnesses, component-sequential scoring, full-workload
time/storage ceiling and development/test isolation. No Mistral answer,
Recovery, Damage or comparison with HGB-only exists yet.
