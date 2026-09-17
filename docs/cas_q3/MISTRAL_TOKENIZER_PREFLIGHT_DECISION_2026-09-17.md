# Exact Mistral tokenizer preflight and independent replay

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PASS_EXACT_MISTRAL_TOKENIZER_SEMANTICS_NO_MODEL_LOAD`.

The exact tokenizer route for
`mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`
is now executable and independently replayed. This closes tokenizer identity,
native chat rendering, padding, prompt/target alignment and bounded length
semantics only. It does not establish whole-model loading, generation/scoring
correctness, resource fit, throughput, scientific effect or a second accepted
reader condition.

## Frozen route

- `AutoTokenizer(..., use_fast=True, legacy=False, local_files_only=True,
  trust_remote_code=False)`.
- Official `tokenizer.json` is used with the native model chat template.
- Exactly one user message, no system message, no tools, and
  `add_generation_prompt=True`.
- No extra special tokens are added after chat-template rendering.
- BOS is `<s>` / 1; EOS is `</s>` / 2; PAD is explicitly set equal to EOS;
  padding is left-sided.
- Generation prompt guard is 8,192 tokens. An over-guard prompt is rejected
  before a model forward; generation prompt tokens are not silently truncated.
- Answer generation is capped at 48 new tokens and repair-query generation at
  64 new tokens.
- Likelihood input is capped at 8,192 total tokens. All answer target tokens are
  preserved and only the left side of the prompt is removed when necessary.

The selection was made before any reader-model output. The official asset
contains `tokenizer.json`, and default `AutoTokenizer` resolves to the same
`LlamaTokenizerFast` class. The slow `LlamaTokenizer` route is retained only as
an equivalence witness.

## Runtime dependencies and failure preservation

The preserved base neural environment lacked the optional dependency chain.
Three failed attempts are retained in
`E:/paper/ReliableRAG-mistral-runtime-v1/TOKENIZER_PREFLIGHT_ATTEMPTS.jsonl`,
SHA-256
`d114afe02c48c486c78d7e96d42661277bb6b1fe30bc0d3040c59ca34f3d8882`:

1. default fast construction failed while entering slow conversion;
2. explicit slow construction failed because SentencePiece was absent;
3. the existing isolated SentencePiece target then failed because protobuf was
   absent.

No model or project data were accessed in any attempt. The isolated Mistral
overlay now adds only the missing pinned packages:

- `sentencepiece==0.2.1`, wheel SHA-256
  `e52144670738b4b477fade6c2a9b6af71a8d0094514c9853ac9f6fc1fcfabae7`;
- `protobuf==7.36.1`, wheel SHA-256
  `51139351435d9b43d88a55eaa49fb6f737fbb478fb0cbf2cf694d1a04a9d3363`.

Both hashes were matched to official PyPI metadata before installation. The
base environment remains unchanged. The updated overlay lock SHA-256 is
`99ee0525c0017ea46f56460397ca6612023c98ed407897b638a2d268cce9fed0`.

## Evidence

The producer report is
`MISTRAL_TOKENIZER_PREFLIGHT_2026-09-17.json`, SHA-256
`47f3f2f04ed324e7be8051a594224bfdca8fc244133c14d5aeef028db24d1b5a`.
It binds five tokenizer assets, both prompt templates, package versions and
origins, three invented fixtures, the native chat-template hash, all token IDs,
and a 36,076-token invented boundary case. Fast, slow and default routes agree
on every ordinary fixture.

The independent replay is
`MISTRAL_TOKENIZER_PREFLIGHT_VALIDATION_2026-09-17.json`, SHA-256
`9ce321aaaa4f58f9fccee8a7e989ee3ee57fc4432fab8b0734a3704547ec4946`.
It passes 102 checks and independently reconstructs every fixture and boundary
hash. Three static prospective contract tests also pass.

Producer source SHA-256:
`9f381df37f73f17103c6fd7ac9cb26fcb47c427032d9d0988177da221bb20c46`.
Validator source SHA-256:
`b34340f6c7011dbe92979588612c3a37ea837af5b8427806ccc533c485f7956a`.

All evidence states zero model loads, neural forwards, reader generations,
project rows, scientific fits and Gold reads.

## Remaining gate

Before any project-data or formal reader run, the complete NF4 model must pass
one prospectively bounded load-only and invented-input preflight. That gate must
reject CPU/disk offload, verify actual quantized module coverage and dtypes,
measure peak GPU and host memory, validate a short deterministic generation and
answer-token likelihood witness, and preserve every failure. Full-workload
input binding, replay witnesses, storage ceilings and the final analysis family
remain open after that model preflight.
