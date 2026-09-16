# Mistral input-freeze pre-namespace launch amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Decision: `AUTHORIZE_ONE_MODULE_LAUNCH_AFTER_ZERO_ACCESS_IMPORT_FAILURE`.

The first command after the prospective input-freeze commit exited before the
producer module could import its common helper:

```text
ModuleNotFoundError: No module named 'scripts'
```

The command directly invoked `scripts/freeze_mistral_reader_inputs.py` while
`PYTHONPATH` contained only the isolated Mistral overlay. Direct script mode set
the import root to the `scripts` directory itself, so the package-qualified
`scripts.mistral_reader_input_freeze_common` import could not resolve.

This was a launcher-path failure, not a tokenizer, data, resource or scientific
failure. `main()` was never entered. The unique output namespace does not exist.
Counts are zero for tokenizer loads, prompt tokenizations, model loads, neural
forwards, generations, fits, project rows and Gold reads. The failure is
retained as sequence 1 in
`E:/paper/ReliableRAG-mistral-runtime-v1/MISTRAL_INPUT_FREEZE_ATTEMPTS.jsonl`.

One corrected launch is authorized with both changes fixed here:

1. invoke the committed producer as module
   `python -m scripts.freeze_mistral_reader_inputs`;
2. prepend the unchanged isolated overlay and committed repository root to
   `PYTHONPATH`.

Producer/common/validator/test/protocol bytes, output namespace, input hashes,
tokenizer semantics, 8,192-token guard and every zero-access rule remain
unchanged. No alternate source, threshold, row or scientific route is
authorized. The corrected command must append its start/completion or failure to
the same external attempt log before acceptance is written.
