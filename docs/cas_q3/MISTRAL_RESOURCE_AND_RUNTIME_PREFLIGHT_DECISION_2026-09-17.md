# Mistral resource and NF4 runtime preflight decision

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PARTIAL_PASS_NF4_KERNEL_ONLY_MODEL_PREFLIGHT_STILL_REQUIRED`.

This stage resolves whether an isolated, pinned 4-bit CUDA kernel can execute on
the current host. It does not load Mistral, read project data, generate an answer,
fit a scientific head or authorize a full reader experiment.

## Preserved and isolated environments

The existing neural runtime remains at
`E:/paper/ReliableRAG-neural-environment-v1`. Without an overlay it still cannot
import `bitsandbytes` or `accelerate`; neither package was installed into it.
It supplies Python 3.10.6, PyTorch 2.7.1+cu128 and Transformers 4.53.2.

The new overlay is outside the Git worktree at
`E:/paper/ReliableRAG-mistral-runtime-v1/site-packages`. Its wheelhouse is a
sibling directory. The two exact wheel files were compared with the SHA-256
values returned by official PyPI metadata before installation:

| Package | Wheel | SHA-256 |
|---|---|---|
| Accelerate 1.8.1 | `accelerate-1.8.1-py3-none-any.whl` | `c47b8994498875a2b1286e945bd4d20e476956056c7941d512334f4eb44ff991` |
| bitsandbytes 0.50.2 | `bitsandbytes-0.50.2-py3-none-win_amd64.whl` | `c697963c8fda3dcd0d7ebd9b5211ae4067feef7cd06e0350d4e816a434fe683d` |

The tracked lock is
`requirements/mistral-reader-nf4-overlay-win-cp310.lock`. The PyPI wheel was
downloaded through the configured Tsinghua mirror, then matched byte-for-byte to
the official PyPI digest; mirror origin is not represented as official hosting.
The current official bitsandbytes installation table reports a Windows x86-64,
CUDA 12.8 build containing `sm120`:
<https://huggingface.co/docs/bitsandbytes/installation>.

## Host observation and executed kernel check

The host was an NVIDIA GeForce RTX 5060 Ti with 17,102,864,384 total GPU bytes,
CUDA runtime 12.8, compute capability 12.0 and BF16 support. The observation
preceding execution showed 15,956 MiB free GPU memory, about 12.8 GiB free
physical RAM, about 24.7 GiB free virtual memory and 232,842,989,568 free bytes
on E:. These are time-local observations, not reserved resources.

`scripts/preflight_mistral_nf4_runtime.py` constructed a 128-to-64
`bitsandbytes.nn.Linear4bit` layer, copied deterministic weights, converted it
to CUDA NF4 with compressed statistics, and executed the same 3-by-128 BF16
input twice. Both outputs were finite and bitwise equal after conversion to the
same BF16 tensor. The saved little-endian FP32 output SHA-256 is
`1cf0636bfb4067accdb2f46cacfa0b08b9eaca0424505dc28206e3e0e4a3da81`.
Peak PyTorch reserved memory was 2,097,152 bytes; this tiny layer says nothing
about whole-model memory.

The separate `scripts/validate_mistral_nf4_runtime_preflight.py` imports no
producer code. It rehashes the producer, report and wheels, verifies package
origins and versions, reconstructs the CUDA layer and input, and obtains the
same output hash. All 37 checks pass.

Evidence:

- `MISTRAL_NF4_RUNTIME_PREFLIGHT_2026-09-17.json`, SHA-256
  `92de500f3709d528d7e932002d3d988fdbe645edbbb52337bb096b3364b28e23`;
- `MISTRAL_NF4_RUNTIME_PREFLIGHT_VALIDATION_2026-09-17.json`, SHA-256
  `6ad542cb47df3c6b98e4933283a11140dcba8fb7664d22ffedc0e30d3246a160`;
- producer script SHA-256
  `54bfaf678ab3b2263f517a12efee2883d432d3aef166affddc4686ed4a87713c`;
- validator script SHA-256
  `b64e562207633e48b16b9fbc8e3fd39a9883868fe0a38609fdf1549154ea572d`.

Both runs record zero model load, reader generation, project row, scientific fit
and Gold-label access. No manuscript or accepted Qwen/Phi evidence changed.

## What is now closed and what remains open

Closed for this exact host and package set:

- official-wheel identity and isolated import origins;
- CUDA 12.8 / `sm120` NF4 kernel availability;
- BF16 compute availability and exact replay of the bounded deterministic
  kernel witness.

Still open before a Mistral model preflight or scientific run:

1. Acquire and hash the exact model revision
   `mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`.
2. Bind every asset path and byte, tokenizer implementation, chat template,
   padding/EOS/attention behavior, generation arguments and deterministic
   decoding contract.
3. Load the complete 4-bit model once under an explicit memory cap and measure
   weights, transient load peak, shortest and frozen worst-length generation,
   likelihood scoring, KV cache, host RAM/commit, disk and wall time.
4. Define independently reconstructable generation and scoring witnesses and
   their finite storage bounds. The old unresolved all-token/full-vocabulary
   branch cannot be inherited.
5. Complete semantic fixtures, numerical tolerances derived before project
   outputs, watchdog behavior, replay acceptance and full-workload time/storage
   ceilings.
6. Freeze the development tuning and final statistical roles before reading new
   reader test outcomes.

Therefore this partial PASS removes one genuine runtime uncertainty but does not
close the old Mistral STOP as a whole. It is not evidence that 7B fits, that the
reader is scientifically valid, or that fusion outperforms HGB-only.
