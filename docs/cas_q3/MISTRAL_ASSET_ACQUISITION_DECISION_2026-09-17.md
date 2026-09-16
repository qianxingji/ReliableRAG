# Exact Mistral asset acquisition and independent validation

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PASS_EXACT_MISTRAL_ASSETS_NO_MODEL_LOAD`.

The exact selected reader assets now exist locally and pass independent byte and
structure validation. This closes asset identity only. It does not authorize a
scientific reader run or establish that the complete quantized model fits.

## Identity and selected serialization

- Repository: `mistralai/Mistral-7B-Instruct-v0.3`.
- Requested and resolved revision:
  `c170c708c41dac9275d15a8fff4eca08d52bab71`.
- Official model metadata: public, not gated, Apache-2.0.
- Asset directory:
  `E:/paper/ReliableRAG-mistral-runtime-v1/assets/mistralai--Mistral-7B-Instruct-v0.3--c170c708c41dac9275d15a8fff4eca08d52bab71`.
- Selected files: 14; total bytes: 14,499,392,853.
- Selected weights: the three Transformers safetensors shards plus their index.
- Excluded duplicate: `consolidated.safetensors`, 14,496,078,512 bytes,
  SHA-256 `76d5729be995fb6510c7f103c5b8825d3d82f8126ac949db6be367a638694d1f`.

The excluded file is the repository's second full-precision serialization. It
is not needed by the frozen Transformers route; retaining both would nearly
double storage without adding a second model. Config, generation config, README,
both tokenizer-model names, tokenizer JSON/config and small repository metadata
are retained.

The external producer manifest SHA-256 is
`0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18`.
Every selected file hash is repeated in the tracked independent validation
report `MISTRAL_ASSET_VALIDATION_2026-09-17.json`, SHA-256
`c0109423528437fd31aebf2831aaa5c0eb53432e7862aee85315bafa1dff205a`.

## Failure preservation and successful transfer

The first regular-HTTP attempt started at 2026-09-16T16:17:08Z. After about 531
seconds, its two large incomplete files were still zero bytes and only localhost
proxy connections remained. The owned process was interrupted; all partial
files remained. That failure is retained in
`E:/paper/ReliableRAG-mistral-runtime-v1/ASSET_ACQUISITION_ATTEMPTS.jsonl`.

The second attempt used official-digest-matched `hf-xet==1.6.0` from the isolated
overlay and resumed the same directory. It completed at 2026-09-16T16:30:54Z.
The attempt log contains two starts, one explicit interrupted-failure event and
one completion; its final SHA-256 is
`a44e59f194e5dfd682aaddfcab083aa9ba93e485a7f2661665d227f3dd7b0189`.
No failure record or partial artifact was rewritten as a success.

The additional Windows wheel is
`hf_xet-1.6.0-cp38-abi3-win_amd64.whl`, SHA-256
`fb4fadde1b2b70bf4c0c14a6dccbe7194b1c28947fefd5bbe3fed9d940676c3b`;
it matches official PyPI metadata. The tracked overlay lock contains this pin.
Hugging Face documents Xet as its chunked content-addressed transfer route:
<https://huggingface.co/docs/huggingface_hub/guides/download>.

## Independent validation

`scripts/validate_mistral_reader_assets.py` does not import the acquisition
script. It re-queries the exact official revision, verifies the remote file set,
license and access state, streams SHA-256 over all 14 local files, verifies LFS
hashes or Git blob identities, and confirms the duplicate consolidated file is
absent.

It independently parses every safetensors header without loading a tensor. The
three shards contain 291 distinct BF16 tensors, 7,248,023,552 parameters and
14,496,047,104 tensor bytes. Header offsets are contiguous and exactly cover
each shard payload; tensor names match all 291 weight-index entries. The config
binds the Mistral architecture, 32 layers, 4,096 hidden width, 14,336
intermediate width, 32 attention heads, 8 KV heads, vocabulary 32,768 and BF16
source dtype. The 1,295 independent checks all pass.

Producer source: `scripts/acquire_mistral_reader_assets.py`, SHA-256
`51896998aef459de8f7aeb117c1049139bc71f51efec31af7f4f0cc80c7f57cc`.
Independent validator source SHA-256:
`2b5185782d18006224a601d8f749daf181720d00fb4fd42dbf2c03aa864942ef`.

## Remaining gate

Asset identity is closed. The next bounded stage must still freeze and verify:

1. fast/slow tokenizer choice, exact chat template, BOS/EOS/pad/attention and
   deterministic decoding behavior;
2. full 4-bit model load with NF4, compressed statistics and BF16 compute,
   including weight replacement coverage and no unintended CPU/disk offload;
3. peak GPU and host memory during load, frozen shortest and worst-length
   generation, answer likelihood, KV cache, wall time and watchdog behavior;
4. semantic fixtures and independently reconstructable scoring/generation
   witnesses with finite storage bounds;
5. full-workload affordability and the final pre-test analysis contract.

This PASS does not close the old Mistral STOP in full. Model loads, reader
generations, project-row reads, scientific fits and Gold-label reads remain zero.
