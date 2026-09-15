# C3 validation execution issue found before launch

Research Lead observation, 2026-09-11. CAS Q2 STATUS: NOT READY.

The current C3 validator imports the original `validate_generation` function
through `load_independent_functions`. That original function checks each saved
output token with `0 <= x < len(tokenizer)`. The source pins are:

- `scripts/validate_roa_empirical_runtime.py`:
  `3eb99ad55f93af8beaa0d316d8892ca8747a627bb80671d358312b758638915a`.
- Original `runtime_branch_freeze/independent_validate.py`:
  `12634390df5c76ae30baeb3172778a86fdae87b7ffc06491db4ab57fcb83fd0a`.

The earlier [length diagnostic](QWEN_TOKENIZER_LENGTH_DIAGNOSTIC.md) measured
five original length calls at about 47–54 ms each on this host. The accepted
[historical cardinality refinement](QWEN_TOKENIZER_CARDINALITY_REFINEMENT.md)
preserves the original helper ASTs and all token checks with an explicitly
disclosed fixed-tokenizer length binding and complete vocabulary rechecks.
These measurements came from the historical/new-environment gate, not the
unexecuted current C3 validator. Substantial current validation overhead is an
inference from the identical source operation; no current completion-time
estimate or current output-token count has been measured here.

Resolve this execution issue prospectively before launching full current C3
independent validation. Do not launch the known expensive operation merely to
collect another timing failure. Any binding adapter needs a separate concrete
design, exact source and tokenizer pins, invented full-equivalence/rejection
fixtures, repeated vocabulary/cardinality checks, and recorded execution
provenance included in the accepted predecessor chain. Preserve the original
validator, all 41 active source/config inputs, numerical criteria and every
current runtime receipt. Do not reduce validation coverage or silently change
the runtime namespace, global builtins, manifest or expected hashes.

This note is a source observation and priority decision, not an implemented or
accepted C3 validator adapter. The original canonical process continues, and
its fixed 180-trace neural replay remains the immediate next runtime operation.
No current answer, generated token, score or Gold payload was decoded for this
observation. Prior historical tokenizer acceptance does not itself authorize
claiming the current C3 validation complete.
