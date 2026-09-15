# Phi development runtime V3 interrupted-acquisition acceptance

Effective when committed, 2026-09-13. **CAS Q2 STATUS: NOT READY.**

The single V3 canonical acquisition used source commit
`5aec9dd95df83bba04d762b90f9cb3da218e38fd`. It reached 9,540 complete
traces and began position 9,540 (`musique`, `bm25`,
`3hop1__161080_158722_35358`). The durable prefix contains 28,622 completed
Phi-generation receipts and 9,541 completed repair-retrieval receipts. Its last
call record is an `a1` intent without a completion or scientific receipt. The
original process disappeared without recoverable terminal output or a failure
receipt, so whether that last `a1` model call started or finished is unknown and
the external interruption cause is **NOT PROVEN**.

The pre-failure external snapshot has SHA-256
`ae59c168136ac1cec0ff6a46d20fde069a5dbeb73be1820941477f57293df677`.
It records exact ledger counts and hashes without changing the runtime
namespace. Its then-proposed next action, resuming only the unmatched `a1`, was
generic advice and conflicted with the frozen executor's ambiguity rule. That
advice is withdrawn here; the original snapshot remains unchanged.

One formal `--resume` invocation was made against the same V3 namespace. It
loaded one BGE and one Phi instance, then correctly failed closed at the
unpaired intent before runtime-prefix semantic validation or any new scientific
call. The diagnostic was `unpaired durable call intent; resume forbidden`.
The resulting immutable failure receipt has SHA-256
`03dd84467c965636242b96605393b7d31c4ca02e9da2fba3860f2269b10875f1`;
the exact recursive namespace manifest has SHA-256
`be4339f85e1691cd9582a711405b10c7b5899bea60db8d6a47a90ffc68a081cd`.
The receipt's zero completed traces and empty call counters describe only that
failed resume process. They do not erase or authenticate the inherited V3
prefix.

A separate read-only client audit rehashed all seven manifest members, verified
exact directory coverage and canonical JSONL framing, and bound all 38,163
completed intent/completion pairs to the original scientific-ledger row bytes.
The completed operation counts are 9,541 `a0`, 9,541 repair-query, 9,541 repair
retrieval and 9,540 `a1` calls. This authenticates preservation and the local
write-ahead structure only. It is not full prompt, tokenizer, retrieval,
canonical-branch or provenance semantic validation, and V3 is not an accepted
runtime result.

V3 is permanently excluded from fitting, calibration, scoring and outcome
analysis. Never delete, edit, resume, reuse, splice or choose individual V3 rows
for a later result. Preserve its executable freeze, five ledgers, failure
receipt, manifest, external interruption snapshot and available client terminal
evidence. The unmatched `a1` remains an unknown attempted-call count; never
report it as zero or completed.

The only permitted next acquisition is the prospective V4 attempt defined in
`PHI_READER_DEVELOPMENT_RUNTIME_V4_ACQUISITION_AMENDMENT.md`. No V4 work is
authorized until both documents and the bound execution source are committed.

