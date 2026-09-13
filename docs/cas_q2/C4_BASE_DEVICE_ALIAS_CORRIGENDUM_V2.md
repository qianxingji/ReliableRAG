# C4 base CUDA device-alias corrigendum V2

**CAS Q2 STATUS: NOT READY.** This prospective correction was authorized by the
Astra xhigh P0-1 base-authenticity audit before GbV execution. It does not alter
the sealed base namespace, its receipt, the original validator, model source,
scores, witnesses or hashes.

The sealed BGE and Qwen sources construct `torch.device("cuda")` and serialize
that object as metadata string `cuda`. Their pre-forward hook independently
records every actual `input_ids.device` as `cuda:0`. The original final validator
instead requires the metadata string itself to equal `cuda:0`; it would reject
before numerical validation despite the actual single-GPU forward ledger.

The V2 correction is exact and base-specific. It accepts only scientific
manifest `6cbc051be274617e26f548f4b51b5a6ec3cddeb5e1caf6761f00fa8301913cab`,
receipt `6a8fba007045a2eba50db74ca14e6bc216cc337681836240d4e9c9da58ba1989`,
source commit `842f2c2f20294a997bd7bcc73bae3cc5ae249be0`, metadata `cuda`, and actual
forward device list `["cuda:0"]` with the exact BGE/Qwen call, row and token
counts. It does not accept arbitrary CUDA aliases. Counter changes, CPU,
multiple devices, another index, metadata `cuda:0`, schema extensions or another
base hash fail closed.

`validate_roa_empirical_scoring_v2.py` retains the complete original validation
logic and changes only the two inconsistent metadata equality checks. It calls
the hash-bound correction before all neural-witness and policy validation and
records the correction in the final independent report. The original validator
remains byte-identical. `run_roa_empirical_scoring_bound_v3.py` selects V2 only
for the future independent stage; base, GbV and policy scientific modules remain
unchanged.

This gate can authorize GbV only after its producer tests and separate client
audit pass with all frozen inputs unchanged. It supplies no Gold, model-quality,
fairness, contribution or Submission Ready evidence.
