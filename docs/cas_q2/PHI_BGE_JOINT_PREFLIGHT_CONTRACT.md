# Phi/BGE joint-memory invented preflight contract

Effective when committed, 2026-09-12. **CAS Q2 STATUS: NOT READY.**

The accepted Phi-only preflight observed 93.48% of nominal CUDA capacity at the
9,472-token generation witness. The development runtime also needs the fixed BGE
query encoder for dense and hybrid repair. Before any benchmark generation,
this contract authorizes one additional invented-only process that loads the
pinned BGE and Phi revisions concurrently and measures their joint peak.

Use the authenticated original assemblies, CUDA BF16, deterministic controls,
single-row batching and the committed pre-CUDA token guard. With both models
resident, execute exactly one invented repair-query generation, one invented BGE
query encoding and one invented long-answer generation at the same 16,000-
character / 9,472-token witness used by the accepted Phi preflight. Save token
admissions, generation captures, embedding shape/norm, forward counts, model
revisions and CUDA allocated/reserved peaks. No likelihood scoring is included.

The process may read only pinned source/config/preflight controls and the exact
Phi/BGE snapshots. Raw data, benchmark/output artifacts, existing answers, Gold,
scientific fits, network access and output writes outside the new namespace are
forbidden. A CUDA OOM or any boundary/config mismatch is preserved and stops
development execution. Passing establishes joint engineering capacity only; it
does not authorize the test benchmark or provide scientific evidence.
