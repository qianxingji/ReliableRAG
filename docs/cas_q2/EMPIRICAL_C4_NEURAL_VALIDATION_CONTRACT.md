# Prospective C4 neural-witness validation contract

CAS Q2 STATUS: NOT READY. Effective before any fresh C4 neural scoring or
scoring-path GPU preflight. The running C3 protocol and all earlier freezes stay
unchanged. This specifies validation of saved neural observations, not another
neural forward replay and not a change to the scientific scoring functions.

An independent implementation must import neither the scoring executor nor its
feature/semantic/likelihood/GbV witness builders. Tokenizers are an explicit
shared dependency, authenticated from the fixed model assets. It may load those
tokenizers on CPU and recompute deterministic token preparation. Neural weights,
generation, fitting, raw benchmarks and outcome values remain unavailable to
the independent validator. Original native source and model configuration hashes
must still be checked by the calling executable boundary.

## Exact bindings and reductions

Answer semantics: preserve all canonical a0,a1 strings, including equal/empty
answers, per-dataset vector row order and complete batch coverage. Reconstruct
document-mode tokens with no query prefix, batch size 16 and cap 512. Match every
saved token field, text hash, forward ordinal and float32 embedding row binding.
Recompute every paired dot product from the saved float32 vectors exactly.
This establishes the saved-array calculation, not that the vectors independently
reproduce BGE's forward pass or its internal CLS normalization.

Likelihood: independently render the ordered five passages with the historical
16,000-character budget, apply the pinned chat template and prove full prompt
token-prefix alignment before native left prompt truncation to 8,192 total
tokens. Rebuild question/prompt/answer/evidence/model/cache hashes and every
answer prediction position. Validate the four-cell L00/L01/L10/L11 request order,
all saved token log probabilities and the exact Python sum/mean/min reductions.
Reconstruct cache availability at the start of each four-cell request: initially
empty, current-run reuse only, and all misses determined before that call's
forwards. Require contiguous forward ordinals and requests = misses + hits.
Cache hits must refer to an already observed current-run witness and have native
zero latency. Finite nonnegative timing remains operational data, not a score.
No full vocabulary logits are added: saved token log probabilities cannot prove
the complete vocabulary softmax or independently reproduce Qwen's forward pass.

GbV: independently format the original hypothesis and reproduce the fit-checked
word windows with 20-word overlap, including exact unmodified short passages,
all words, forward progress and the original binary-search chunk boundaries.
Reconstruct each paired-token batch with no truncation, batch size 8 and effective
context 512. Verify complete ordered passage/chunk coverage, token fields,
contiguous forward ordinals, two-class logits and the unique positive entailment
label at index 0. Recompute the softmax independently using stable float64 CPU
arithmetic from the saved float32 logits. Compare the observed float32
probabilities under the prospective bound below. Branch maxima, F1-F0 margins,
common masks, reasons and actions must match the actual saved probabilities
exactly. Do not replace them with the CPU recomputation.

Only the two documented deterministic NLI preparation failures may justify an
unscorable pair. Reproduce the failure with the independent tokenizer/chunker,
including its branch position and exact reason. Earlier successful branch
witnesses and forwards remain counted; no later branch is executed after the
first failure. Unknown errors, nonfinite values, missing observations or a
purported preparation failure after a forward abort validation.

## Prospective floating-point gate

The new independent GbV softmax check permits an absolute probability difference
of at most 8 * float32 epsilon = 9.5367431640625e-7, with no relative tolerance.
Every saved logit/probability must be a finite exactly representable float32
value, probabilities must lie in [0,1], and their sum must differ from 1 by no
more than 2 * float32 epsilon. This small fixed engineering allowance addresses
different FP32 GPU/CPU reduction implementations; it is not asserted as a theorem
bounding all possible kernels. Any exceedance in invented GPU preflight or the
real run fails and is preserved for diagnosis. Do not enlarge it after observing
a failure or use it to change a score, rank or eligibility decision.

This gate did not previously exist: the earlier note explicitly left neural
softmax validation outstanding. It does not replace or relax the existing 1e-10
saved-head replay tolerance, exact likelihood aggregations, exact saved-array
semantic values, exact NLI maxima/margins or exact policy actions. The gate and
its rationale are fixed before implementation and before scoring-path GPU output.

## Completion boundary

First verify meaningful CPU fixtures using the original native scoring functions
with explicitly invented logits; include corruption of tokens, cache chronology,
chunk coverage, class index, probabilities, maxima, margins and failure reasons.
Complete committed adapters, protected executor and immutable input/environment
freeze before invented-only pinned-model GPU preflights. Do not compete with C3
on the single GPU. After C3 is independently accepted, validate all actual C4
witnesses and downstream policies before prelabel sealing and any Gold mapping.
Synthetic tests alone do not accept real scoring, fresh quality or submission.
