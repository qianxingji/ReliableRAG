# Mistral reader value-blind input-freeze protocol

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `FROZEN_BEFORE_UNIQUE_TOKENIZER_ONLY_INPUT_FREEZE`.

This protocol authorizes one tokenizer-only construction of the exact Mistral
development/test generation inputs. It reads question text and frozen retrieval
evidence, but no reference answer, existing generated answer, outcome, score,
action or Gold. It performs no model load, neural forward, generation or fit.

## Direct accepted source chain

The freeze binds directly to the accepted Qwen study's label-free inputs. Phi
outputs, repair queries, answers, scores, failed validators and input-freeze
artifacts are not predecessors.

- Development trace manifest:
  `E:/paper/ReliableRAG/outputs/daa_v2_fresh_v1/runtime_branch_freeze/trace_manifest.jsonl`,
  SHA-256 `723cefe8817f5ff07fa81b06d71f59d9f28fe37d5e6b62ff94184e20bcdcf8e3`.
- Development runtime configuration SHA-256:
  `9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9`.
- Test trace manifest SHA-256:
  `87d5aff0bc77da76624b541326c523d41b00fa6c84ecefd4d6a050de66b25a29`;
  accepted preparation-manifest SHA-256:
  `7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258`.
- Test label-free candidate-pool manifest SHA-256:
  `4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98`.
- Development role ledger SHA-256:
  `40992a860943bc553fe9da6ad541181cb46958c56dc14a96621007449d0382ec`.

The exact three datasets, three retrievers and original Top-5 document order are
retained. Development contains 4,500 question groups / 13,500 traces, with
3,600 fit and 900 calibration questions. Test contains 6,000 question groups /
18,000 traces. No row is selected, replaced or reordered.

## Tokenizer and prompt contract

Use the already accepted exact Mistral tokenizer and native chat template:

- `mistralai/Mistral-7B-Instruct-v0.3` revision
  `c170c708c41dac9275d15a8fff4eca08d52bab71`;
- `LlamaTokenizerFast`, `use_fast=True`, `legacy=False`, local-only and no
  remote code;
- one user message, no system/tools, `add_generation_prompt=True`;
- tokenize the rendered chat with `add_special_tokens=False` because the native
  template already emits BOS;
- PAD=EOS=2 and left padding;
- unchanged `baseline_v1.txt` and `repair_missing_v1.txt` prompts;
- unchanged order-preserving five-document rendering and 16,000-character
  evidence budget.

For every one of the 31,500 fixed traces, tokenize the original-answer (`a0`)
and repair-query prompts, producing 63,000 deterministic prompt checks. Write
only trace identity, role, Top-5 hash, prompt hash, token-ID hash, token count,
context length and truncation flags. Do not write question/evidence text or token
IDs to the ledger.

The generation prompt guard is 8,192 tokens at batch size one. Any deterministic
`a0` or repair-query prompt above the guard fails the unique run. Repaired-answer
(`a1`) prompts depend on future Mistral repair queries and therefore cannot be
precomputed; the production runtime must run the same guard before CUDA/model
access for every `a1`. No truncation is permitted for generation prompts.

## Access and validation boundary

The producer installs an audit hook after resolving the clean committed source:
network/process creation is denied; model-weight extensions are denied; reads
are limited to the explicit source/control/tokenizer allowlist and Python
environment roots; writes are limited to the unique ignored output namespace
`outputs/cas_q3/mistral_reader_input_freeze_v1`.

The producer must record every explicit input and actually read environment
file, seal a recursive SHA-256 manifest and state zero model loads, forwards,
generations, fits, existing-answer reads and Gold reads. A separate script that
does not import the producer/common implementation must rehash the namespace and
all producer inputs, reconstruct all 31,500 ledger rows and 63,000 tokenizations,
and reproduce every aggregate and maximum in
`outputs/cas_q3/mistral_reader_input_freeze_validation_v1`.

Any failure or boundary denial remains sealed. There is no automatic retry,
alternate tokenizer, larger guard, prompt edit, row deletion or Phi-derived
substitution. PASS authorizes only the next longest-shape resource and
production-adapter gates; it does not authorize development/test generation,
Gold, tuning, claims or manuscript changes.
