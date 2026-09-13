# Bounded tokenizer-length timing diagnostic

Research Lead scope, 2026-09-11. CAS Q2 STATUS: NOT READY.

The unchanged selected historical validator has not emitted its first 1,500-row
checkpoint after several minutes, whereas the producer completed all 41,040
receipts in about four minutes. It calls len(tokenizer) once per generated ID.
Do not infer a backend complexity claim without measurement. Keep that process
and its original functions unchanged while diagnosing.

In a separate single-thread CPU process, authenticate the five restored Qwen
configuration/tokenizer files and the v2 guard. Load only that local tokenizer.
Measure exactly five calls to len(tokenizer), one get_vocab call, and the ordinary
length of its returned vocabulary. Preserve every duration and returned value.
No historical/current ledgers, model weights, fits, forward, generation or Gold
may be read/run. Freeze the diagnostic controller and input hashes before loading.
This is an infrastructure measurement only, not a scientific replay or a reason
to change token IDs, matching rules, source hashes or the running validator.
Any subsequent optimization needs a separate prospective decision with explicit
semantic equivalence conditions and a new output namespace.
