# Mistral whole-model NF4 preflight protocol

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `FROZEN_BEFORE_FIRST_WHOLE_MODEL_LOAD`.

This protocol authorizes one bounded load of the already authenticated
`mistralai/Mistral-7B-Instruct-v0.3` revision
`c170c708c41dac9275d15a8fff4eca08d52bab71`, followed only by invented-input
generation and likelihood witnesses. It does not authorize project data,
development labels, test Gold, head fitting, benchmark execution or a formal
reader result.

## Exact loading contract

- Preserved base: Python 3.10.6, PyTorch 2.7.1+cu128, Transformers 4.53.2.
- Isolated additions: Accelerate 1.8.1, bitsandbytes 0.50.2,
  SentencePiece 0.2.1 and protobuf 7.36.1.
- Offline and local-only loading; `trust_remote_code=False` and
  `use_safetensors=True`.
- Process environment fixes `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`,
  `TOKENIZERS_PARALLELISM=false`, `PYTHONHASHSEED=0` and
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`; random seed is 20260917, TF32 is disabled,
  and deterministic PyTorch algorithms are required.
- `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
  bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)`.
- Nonquantized parameters use BF16. Attention implementation is explicitly
  `eager`. Batch size is one.
- The complete device map is CUDA device 0. CPU and disk offload are forbidden.
- All 224 transformer projection modules must be `Linear4bit`: seven named
  projections in each of 32 layers. `lm_head` is the only ordinary linear
  module allowed.
- Every quantized module must have an initialized NF4 state with nested/double
  quantization and BF16 compute. No parameter may remain on `meta` or CPU.

## Result-blind invented witnesses

The accepted tokenizer route from
`MISTRAL_TOKENIZER_PREFLIGHT_DECISION_2026-09-17.md` is reused unchanged.

1. Answer fixture: invented evidence explicitly states that Paris is the
   capital of France. Greedy decoding is run twice with at most eight new
   tokens. Token IDs and every FP32 processed score must repeat exactly. The
   normalized output must be `Paris`; this predicate was fixed before loading.
2. Repair fixture: an invented question supplies a birth city but omits its
   country. One greedy decode with at most 32 new tokens must produce nonempty
   `Missing fact:` and `Search query:` lines. Their exact wording is not a gate.
3. Likelihood fixture: the answer prompt and target `Paris` must be exact-prefix
   aligned. Two no-cache teacher-forced forwards must produce exactly repeated,
   finite FP32 answer-position logits. Only answer target positions are scored.

The producer stores full-vocabulary FP32 score arrays for these short witnesses
in a compressed NPZ. An independent CPU validator must reconstruct greedy
tokens, the chosen-token log probabilities and all report hashes without
loading the model. Witness size is capped at 8 MiB.

## Resource admission and stop rules

Before loading, all of the following must hold:

- CUDA is available on exactly one RTX 5060 Ti with BF16 support and compute
  capability 12.0;
- total GPU memory is at least 15 GiB and free GPU memory is at least 12 GiB;
- available host RAM is at least 8 GiB;
- free E-drive space is at least 30 GiB.

During the process, peak CUDA reserved memory must remain at or below 12 GiB,
process peak working set at or below 20 GiB, and sampled system-available RAM at
or above 4 GiB. Total producer wall time is capped at 20 minutes. Any violated
threshold, nonfinite value, semantic-fixture failure, offload, module mismatch,
quantization mismatch or exception is a failed preflight. The attempt log and
all partial files remain; the script does not retry, change precision, enable
offload, relax a predicate or switch readers.

## Acceptance and remaining scope

PASS requires the producer report, witness and independent validator to agree,
with exactly one model load, no project row, no Gold and no scientific fit. A
PASS proves that this particular short NF4 execution path is viable on this
machine. It does not prove 8,192-token worst-case memory, full-workload
throughput, end-to-end retrieval/GbV/NLI integration, replay storage,
development tuning, fair test analysis or a paper claim. Those remain separate
prospective gates.
