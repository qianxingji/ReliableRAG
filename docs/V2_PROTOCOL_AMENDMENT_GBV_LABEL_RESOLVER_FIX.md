# DAA-V2 prospective implementation correction — GbV entailment-label resolver

## Status

**Prospective implementation correction recorded after two blocked, zero-scoring pre-label attempts and before any fresh V2/HGB/GbV scientific score, arbitration action selection, fresh-label access, Gold mapping, or evaluation.**

The first blocked attempt exposed a canonical-only metadata input-contract gap. The second blocked attempt successfully validated the sealed metadata binding but then stopped before scientific scoring because the committed GbV label resolver is incompatible with the exact pinned model configuration.

Both blocked namespaces remain immutable evidence and must not be relabeled as successful executions.

## Observed bug

The frozen GbV model is:

- model: `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`
- revision: `5a4338ab2151dc8db04ad53b42b6153382bf4f99`

The exact pinned model configuration defines:

```text
id2label = {0: "entailment", 1: "not_entailment"}
label2id = {"entailment": 0, "not_entailment": 1}
```

The previously committed `resolve_entailment_index` normalized labels by removing nonletters and selected every normalized label containing the substring `"entail"`. This incorrectly treats both `entailment` and `notentailment` as positive entailment labels, yielding two matches and a fail-closed exception.

This is an implementation defect in resolving the already-defined positive entailment class. It is not a model-selection, threshold-selection, score-calibration, or scientific-method change.

## Authorized correction

Correct `resolve_entailment_index` so that, after the existing lowercase/nonletter normalization, it selects only an **exact positive entailment label**:

```text
normalized_label == "entailment"
```

Require exactly one such label; otherwise fail closed as before.

For the exact pinned model this resolves entailment index `0`.

Do not add heuristic fallbacks for generic `LABEL_0`, `LABEL_1`, substring matches, prefix matches, or inferred binary polarity. Unknown or ambiguous label maps must continue to raise an error.

## Required tests

Before any scientific GbV scoring, committed tests must include and pass at least:

1. three-class `{ENTAILMENT, NEUTRAL, CONTRADICTION}` resolves the entailment index;
2. exact pinned binary `{0: entailment, 1: not_entailment}` resolves index `0`;
3. reversed-index binary `{0: not_entailment, 1: entailment}` resolves index `1`;
4. generic `{LABEL_0, LABEL_1}` fails closed;
5. no configuration produces multiple matches solely because a negative label contains the word `entailment`.

The exact pinned `config.json` must also be loaded in a compatibility regression check and must resolve index `0` before tokenizer/model initialization for scoring.

## Scientific invariants preserved

This correction does not change:

- GbV model identity or revision;
- slow tokenizer requirement;
- NLI hypothesis text;
- evidence passage unit;
- 20-word-overlap overlength chunking;
- maximum entailment aggregation;
- paired margin `F1-F0`;
- answer-pair eligibility/forced-KEEP rule;
- dtype, device, or batch-size protocol;
- DAA-V2 architecture, features, lambda, alpha, action rate, or model;
- raw HGB comparator;
- GbV historical development thresholds;
- fresh cohort, candidate pools, retrieval outputs, runtime branches, or metadata binding;
- statistical analysis or success criteria.

No fresh score or outcome was observed before this correction was specified.

## Preservation of blocked evidence

Preserve both prior blocked namespaces byte-for-byte:

- `outputs/daa_v2_fresh_v1/prelabel_seal/`
- `outputs/daa_v2_fresh_v1/prelabel_seal_v2/`

The second blocked attempt already established a valid 13,500-trace canonical/metadata binding. That binding may be reused only after its hashes and `BINDING_VALIDATION.json` PASS are reverified. Reuse is an engineering optimization, not permission to alter the binding.

## Hard boundary

This amendment authorizes only the narrow resolver correction and its tests. It does not itself authorize fresh scientific scoring, action selection, Gold access, or evaluation. Those require the separately committed execution task that cites this amendment.
