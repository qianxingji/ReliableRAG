# Client Lead acceptance: reader acquisition execution

CAS Q2 STATUS: NOT READY. Effective 2026-09-11 before benchmark generation.

Accept the C3 native reader/repair adapter at commit
373887e04ae72e1b4c12bfd165ce1117fa9b7232 for the unchanged scientific design in
EMPIRICAL_C3_RUNTIME_CONTRACT.md. C2's complete original retrieval passed the
independent acceptance in EMPIRICAL_C2_ACCEPTANCE.md. Its manifest SHA-256 is
81b9c7163adf669a828bd2ef772e14fecbda727cf596bced45856a1e699a354d.

The preparation manifest is
7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258.
Its 18,000 complete trace bindings and the prospective 180-trace replay subset
were additionally recomputed without importing the preparation implementation;
both match exactly. The complete nine strata contain 2,000 traces each; the
fixed replay contains 20 per stratum. No reader output informed membership.

The joint GPU preflight manifest is
050efac3a47c4c5cc8a9ffb82284dc8a60b8b480cf4561e6aa8788db504ab5f8.
Status: PASS_JOINT_READER_GPU_SYNTHETIC_ONLY. The exact pinned Qwen and BGE
models loaded concurrently in CUDA BF16 with SDPA, deterministic algorithms,
TF32 disabled and runtime seed 20260828. Native inherited generation configs
and tokenizer chat template match the original freeze. Exactly two invented
answer generations used four Qwen forwards and zero BGE forwards; their token
and scientific capture records match exactly. Peak allocated CUDA memory was
6,574,814,720 bytes. No benchmark generation, fit or Gold value access occurred;
the execution boundary recorded no denied access. This short synthetic case
does not guarantee memory sufficiency or determinism for every real context.

The separately sealed original CPU fixture run passed 22/22 tests using dummy
models/tensors. The project engineering suite ran 47 tests: 45 passed and two
Windows filesystem-capability skips. The native restricted assembly's 46 AST
nodes and generation-prefix boundary match the authenticated original runtime.
Neither new source adaptation nor these checks constitute a full reader replay.

Authorize one canonical 18,000-trace acquisition into empirical_runtime_v1,
then the already fixed 180-trace replay, using both preparation and joint GPU
manifest pins above. The executor binds complete source/input hashes before
model loading and rejects changed preflight inputs. Every scientific ledger is
append-only with per-record durable writes. Any failure is preserved and stops
that pass; this acceptance does not authorize an automatic retry or cohort change.

Completion still requires exactly 54,000 canonical generations, 18,000 repair
retrievals, 12,000 repair query BGE forwards, zero document re-embedding, the
separately costed 540-generation replay and a full independent tokenizer/ranking/
evidence/receipt validator. Only then may candidate-pair acquisition be accepted.
Scoring, common eligibility, nine-policy actions, prelabel sealing and outcome
mapping are later stages. Fit total remains 178; no new-model contribution or
fresh performance claim is cleared. Original attribution failures, historical
fit-time receipt gaps and undecided CAS journal qualification remain P0 risks.
P1 covers comparison/cost/release fidelity; P2 adds no model/feature/budget search.
