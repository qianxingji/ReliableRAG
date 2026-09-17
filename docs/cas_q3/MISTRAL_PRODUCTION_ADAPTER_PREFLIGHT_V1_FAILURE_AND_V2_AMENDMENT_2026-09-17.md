# Mistral production-adapter preflight V1 failure and V2 amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `PRESERVE_V1_PREMODEL_FAILURE_AUTHORIZE_V2_CONTEXT_INITIALIZATION`.

The prospectively committed V1 invented-only adapter preflight failed before
the tokenizer/model constructor, project data, generation, likelihood, Gold or
fit. PyTorch 2.7.1 on this Windows host rejected
`torch.cuda.reset_peak_memory_stats(0)` with `RuntimeError: Invalid device
argument` because the concrete CUDA device had not yet been initialized in the
new process. The exact traceback is sealed under
`outputs/cas_q3/mistral_production_adapter_preflight_v1/`; the external V1
attempt log retains one start and one failure event. Its counters are zero for
project rows, Gold and scientific fits, and no operation journal was created.

V2 changes only the pre-model resource-meter initialization sequence:

1. call `torch.cuda.get_device_properties(0)`;
2. require the accepted `NVIDIA GeForce RTX 5060 Ti` identity;
3. then clear the cache and reset peak-memory statistics.

The model, revision, assets, tokenizer, prompts, NF4/BF16/eager configuration,
fixtures, seven operations, numerical checks, resource ceilings and scientific
zero-access boundary are unchanged. V2 must use a new output namespace and a
new append-only attempt log. V1 may not be overwritten or relabeled. This is a
prospective engineering correction to reach the already frozen scientific gate;
it is not parameter tuning and cannot affect a benchmark result.
