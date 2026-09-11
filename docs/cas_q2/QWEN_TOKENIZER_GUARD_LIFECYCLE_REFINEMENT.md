# Prospective tokenizer guard shutdown correction

Research Lead decision, 2026-09-11. CAS Q2 STATUS: NOT READY.

The v1 Qwen producer completed every historical comparison, but its stderr then
recorded an ignored ResourceTracker.__del__ exception in the profiling callback:
AttributeError: 'NoneType' object has no attribute 'startswith'. The callback
assumed frame globals always contain a string __name__. Python interpreter
finalization can clear that name to None. A zero process exit code and the
producer's pre-finalization PASS receipt are insufficient for complete lifecycle
acceptance. Preserve v1 sources, full rows, receipts, logs and automatic seal even
if its original controller later reports PASS. Its client acceptance is pending
the separate lifecycle review; do not call it an exception-free full run.

Diagnose in isolated CPU processes with the authenticated v1 guard and a separate
v2 guard. The only prospective v2 change is to normalize a false/None module name
to the empty string before testing the existing module-name prefixes. Preserve
every other event, path, function and pretrained/CUDA/network prohibition.
Use an in-memory synthetic cleared-name frame to test the exact failure and a
separate ordinary joblib ResourceTracker import/exit to test real finalization.
Keep all commands, stdout/stderr and module/guard hashes. No historical/current
scientific payload, tokenizer/model, fit, forward or Gold access in this diagnostic.

Only after the diagnostic succeeds, execute a new v2 full historical gate under
the unchanged frozen tokenizer contract, producer, IO helper and independent
validator. Bind the separately frozen v2 guard and a fresh output namespace.
This repeat is justified by the observed lifecycle defect; no scientific body,
historical hash, matching rule, token IDs, parser or scope changes. Require both
complete processes, exact comparisons and empty unexpected stderr, plus all
input/environment preservation checks. Keep v1 even if numerically identical.
The corrected full run must not be claimed before it actually completes.
