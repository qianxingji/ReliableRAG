# Mistral longest-observed-shape resource preflight protocol

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `FROZEN_BEFORE_SINGLE_LONGEST_SHAPE_MODEL_LOAD`.

The accepted value-blind input census found a maximum fixed generation prompt
length of 3,675 tokens. This protocol authorizes one model load and one
invented-content resource witness at exactly that prompt length followed by 64
decode steps. It reads the tracked accepted length summary only; it does not
read the private prompt ledger or submit any project question/evidence token to
the model.

## Fixed model and invented token shape

Reuse without modification the exact model, revision, tokenizer, NF4 nested
quantization, BF16 compute/nonquantized dtype, eager attention, CUDA-only device
map, package versions, deterministic flags and offline environment accepted in
`MISTRAL_WHOLE_MODEL_PREFLIGHT_ACCEPTANCE_2026-09-17.md`.

The input sequence is exactly 3,675 tokens at batch size one:

- native BOS token 1;
- native `[INST]` token 3;
- 3,672 repetitions of fixed ordinary vocabulary token 1,000;
- native `[/INST]` token 4.

This sequence is an invented resource surrogate. Its content has no benchmark
meaning. Greedy generation is forced to exactly 64 new tokens by disabling EOS
only for this resource upper-bound witness. This does not change the production
generation contract, which retains EOS and the accepted 48/64 caps.

Save the complete FP32 processed-score vector for all 64 steps, generated IDs,
prompt IDs and hashes in a compressed witness capped at 12 MiB. A no-model
validator must prove the prompt construction, length, score shape, finite
values and per-step greedy argmax.

## Admission and stop limits

Before loading: one RTX 5060 Ti, BF16 and compute capability 12.0; at least 15
GiB total and 14 GiB free GPU memory; at least 8 GiB available host RAM; at
least 30 GiB free E-drive space.

During/after execution: all 224 expected projections remain NF4 nested/double
quantized on CUDA 0, no CPU/disk/meta parameter, peak CUDA reserved memory at
or below 14 GiB, process peak working set at or below 20 GiB, sampled available
host RAM at or above 4 GiB and wall time at or below 20 minutes.

Any exception, OOM, nonfinite score, short decode, offload, module mismatch or
threshold violation is a failed preflight. Preserve the attempt and partial
files; do not reduce length/steps, change attention/precision, enable offload or
retry automatically.

PASS closes only the longest observed fixed-prompt shape on this host. Dynamic
`a1` remains subject to the 8,192-token pre-CUDA guard. Production adapter,
interruption/resume, compact replay/storage, development generation and
scientific analysis remain separate gates.
