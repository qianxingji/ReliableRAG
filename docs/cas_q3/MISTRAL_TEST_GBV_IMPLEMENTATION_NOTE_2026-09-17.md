# Mistral test paired-GbV implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

The paired test GbV producer and independent tokenizer/logit validator are
implemented but have not been run. They are blocked on independent acceptance
of the formal test HGB-signal stage and every earlier test predecessor.

## Frozen operation

The producer uses
`MoritzLaurer/deberta-v3-large-zeroshot-v2.0@5a4338ab2151dc8db04ad53b42b6153382bf4f99`
in FP32 on CUDA 0 with batch size 8. For each pair that passes the common answer
eligibility rule, it scores `a0/E0` before `a1/E1`. Every model forward is bound
to its exact tokenizer fields and saved as explicit little-endian float32 logits
of width two. `F0` and `F1` are independently reconstructed from the maximum
entailment probability across all premise chunks, and `gbv_margin=F1-F0` only
when both branches are valid.

Only the two historically frozen deterministic context-window errors may create
an `nli_unscorable` forced-Keep row. A CUDA OOM, source mutation, nonfinite
value, unexpected tokenizer error or any other failure terminates and seals the
stage. If `a0/E0` was valid but `a1/E1` is unscorable, the valid F0 receipt is
retained while the pair remains forced Keep.

The execution freeze binds the accepted HGB stage and all earlier acquisition
stages, test trace/input freeze, pool and retrieval records, exact model assets,
the 17-file SentencePiece package and its provenance, code, validator and
protocol. Mistral/BGE loads, project/test Gold, test outcomes, fitting and tuning
are forbidden and have explicit counters.

The independent validator imports no producer or neural model class. It loads
only the pinned slow tokenizer, reconstructs every NLI premise/hypothesis pair
and token batch, reads the raw logits, applies an independent float64 softmax,
and recomputes every branch score and final GbV row. It also proves exact logit
file coverage and journal/receipt binding with zero model forward.

Eight contract tests cover model identity, batch width, independent softmax,
the exact error whitelist, partial-branch retention, raw-logit recomputation,
hidden-data rejection and validator independence. The complete Mistral suite
passes 145 tests. No formal test GbV namespace, score or outcome was produced.

## Remaining gates and risks

- **P0:** finish and independently accept the full development chain and the
  equal-budget 84-fit development-only selection.
- **P1:** execute the frozen test acquisition and scoring chain once; implement
  and accept the common test prelabel freeze before probability prediction and
  action sealing.
- **P2:** open numeric test outcomes only after action-ledger acceptance, then
  update the paper and public bundle from accepted results.

The primary scientific risk is unchanged: fusion may fail to improve both
accuracy and damage over `HGB_ONLY_R`. Paired GbV supplies the second signal for
that fair comparison but is not by itself evidence of an incremental benefit.
