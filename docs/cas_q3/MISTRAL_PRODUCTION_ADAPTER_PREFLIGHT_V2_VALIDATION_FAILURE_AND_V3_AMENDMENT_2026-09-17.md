# Mistral adapter V2 validation failure and V3 amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `REJECT_V2_DUPLICATE_BOS_AUTHORIZE_V3_NO_EXTRA_SPECIAL_TOKENS`.

V2 completed the invented model process, but its separate no-model validator
rejected the first operation with `PROMPT_IDS:invented:a0`. The saved generation
receipt begins `[1, 1, 3, ...]`; independent reconstruction under the already
accepted tokenizer contract begins `[1, 3, ...]`. The first `1` is the BOS
inside the rendered native chat template. The second was added because the
production generation call used the tokenizer default `add_special_tokens=True`.

V2 is therefore not an accepted adapter gate. Its apparently sensible invented
outputs (`Paris`, `Lyon`, and a nonfallback repair query), seven operation rows,
full-vocabulary arrays and resource measurements remain failure evidence only.
The producer performed one model load and 39 forwards, then unloaded to
33,555,456 allocated CUDA bytes. It read zero project rows, zero Gold and made
zero scientific fits. Its complete namespace remains sealed at
`outputs/cas_q3/mistral_production_adapter_preflight_v2/`; the tracked failure
receipt is `MISTRAL_PRODUCTION_ADAPTER_V2_VALIDATION_FAILURE_2026-09-17.json`.

V3 changes one CPU tokenizer argument in `prepare_generation`:
`add_special_tokens=False`. This directly enforces the accepted tokenizer gate,
which specifies no additional special-token pass after the rendered native chat
template. Likelihood already used `add_special_tokens=False` and is unchanged.
The exact model, revision, asset hashes, quantization, prompts, fixtures,
generation limits, seven operations, numerical/resource thresholds and
zero-scientific-access boundary remain unchanged.

V3 must use a new output namespace and attempt log. It must pass both the model
producer and the unchanged independent validator. V1 and V2 remain immutable;
neither may be called a scientific reader result. This correction was motivated
by an input-contract failure before any project data were exposed, not by answer
quality or benchmark outcomes.
