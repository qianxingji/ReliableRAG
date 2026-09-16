# Mistral production adapter and recovery protocol

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `FROZEN_BEFORE_INVENTED_ADAPTER_VALIDATION`. This protocol closes the
production-adapter, interruption-recovery and compact-witness design. It does
not authorize a scientific result, read Gold, fit a model, or make Mistral an
accepted reader condition. The latest manuscript and public repository remain
unchanged.

## Fixed reader condition

- Reader: `mistralai/Mistral-7B-Instruct-v0.3` at revision
  `c170c708c41dac9275d15a8fff4eca08d52bab71`.
- Deployment: bitsandbytes NF4, double quantization, BF16 compute and BF16
  nonquantized parameters; eager attention; all 224 projection modules are
  `Linear4bit`; no CPU or disk offload.
- Tokenizer: the already accepted fast tokenizer, `legacy=False`, native chat
  template, one user message, no tools/system message, BOS 1, EOS 2, PAD=EOS,
  left padding and no extra special-token pass.
- Generation: greedy, batch size 1, 48 answer tokens or 64 repair-query tokens.
  Every prompt is tokenized and admitted on CPU at at most 8,192 tokens before
  any tensor is sent to CUDA.
- Likelihood: answer-token-only teacher forcing. The complete answer target is
  retained; when necessary only the left side of the prompt is removed, keeping
  the rightmost prompt suffix and a total length of at most 8,192 tokens.
- Prompts, five-document rendering, 16,000-character context budget, parsers,
  same-retriever depth-50 repair and rank-5 replacement remain the Qwen study's
  fixed semantics. Only the reader/deployment condition changes.

The implementation is `src/arbitration/mistral_reader_runtime.py`. Importing it
has zero tokenizer/model/CUDA/project-data side effects. The exact model is
loaded only by an explicit `load()` and released by `close()`.

## Component-sequential execution

The formal development runtime has three durable stages:

1. Load Mistral alone and generate `a0` plus repair query from the accepted
   original evidence for all 13,500 development traces. Close Mistral.
2. Load BGE alone only for dense/hybrid repair-query embeddings; reuse the
   frozen document embeddings/BM25 structures, construct `e1`, and close BGE.
3. Load Mistral alone and generate `a1`; while it remains the sole GPU model,
   compute L00/L01/L10/L11. Close Mistral before any NLI/GbV stage.

Mistral and BGE/NLI may never be resident together. A later scoring executor
must authenticate the empty-Mistral boundary before loading NLI. The accepted
3,675-token resource witness left only about 3.06 GiB free at peak, so concurrent
residency has no accepted safety basis.

## Durable calls and resume

Every generation, repair retrieval and likelihood operation has a stable key
and a SHA-256 binding over its complete input. The append-only journal fsyncs an
`intent` before a call and a `result` after its scientific row is durable.

- A completed key is never regenerated.
- A final interrupted intent may be reissued only with the identical operation,
  key and input hash. A `resume_pending` row is fsynced first. This records an
  extra physical call while retaining one logical result.
- A changed input, noncanonical line, partial line, duplicate key, overlapping
  call or out-of-order result fails closed.
- The run preserves the failure/interrupt receipt and the recovery count. It
  cannot silently discard or overwrite an attempt.

This rule makes long formal execution resumable without using a completed
output twice or changing an input after observing a partial result.

## Compact numerical witness

Before generation, select the first and last development trace in each of the
nine dataset × retriever cells: exactly 18 positions. Selection uses identities
and order only, never output values or Gold.

For those positions save, in addition to ordinary compact receipts:

- the complete 32,768-way FP32 logits for the first generated token of `a0`,
  repair query and `a1`;
- the complete 32,768-way FP32 logits for the first answer target token of each
  L00/L01/L10/L11 cell;
- input/target token IDs, generated IDs, selected-token log probabilities,
  prompt/evidence hashes and all truncation metadata.

The fixed full-vocabulary payload is
`18 × (3 + 4) × 32,768 × 4 = 16,515,072` bytes before container metadata. All
other rows retain generated token IDs and chosen log probabilities, which are
enough to recompute means/minima but do not pretend to be full-softmax witnesses.
An independent validator must reconstruct prompts and targets, verify every
hash and shape, and recompute the sampled softmax values from the full-vocabulary
arrays.

## Development tuning and test isolation

After development branches and scores pass independent validation, run only the
already frozen equal-budget search: three methods, eight configurations each,
three dataset-stratified question-group folds, followed by one selected refit
and calibration fit per method (at most 78 fits). Fit questions remain separate
from calibration questions. Preserve the fixed reference recipe, every searched
configuration, failure and tie decision.

The primary recipe and multiplicity family must be frozen before any Mistral
test outcome is opened. Unsatisfactory development results may motivate another
declared development candidate within the frozen budget. Test results may not
select parameters, action count, reader, seed or endpoint. A change prompted by
test outcomes is exploratory and requires a new uncontaminated confirmation
source.

## Gates

1. **P0 adapter gate:** static tests plus one invented-only exact-model adapter
   run, including generation, repair parsing, likelihood, unload and independent
   witness replay.
2. **P0 development acquisition:** the single component-sequential 13,500-trace
   run and value-blind independent validation. No Gold or fit.
3. **P0 development scoring/tuning:** reader-matched scores, development-only
   fit/cal selection and a frozen test plan.
4. **P1 test:** one frozen 18,000-trace execution, Gold mapping and analysis,
   retaining positive, negative or inconclusive results.
5. **P2:** claim audit, manuscript update and public reproducibility package.

Main rejection risks remain the small and uncertain gain over `HGB_ONLY_R`, one
repair operation, already-seen question identities, rare Damage, deployment
quantization and end-to-end public neural reproducibility. This adapter design
reduces runtime/replay risk; it does not by itself strengthen the scientific
claim.
