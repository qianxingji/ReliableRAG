# C4 Jinja execution binding V2: CPU acceptance

Date: 2026-09-12. Client Research Lead review: Sol High.
CAS Q2 STATUS: **NOT READY**.

Decision: **ACCEPTED_C4_JINJA_EXECUTION_BINDING_V2_CPU_ONLY**. One complete
V2 invented GPU preflight is authorized under the frozen correction contract.
This is engineering/identity acceptance; it is not GPU or fresh-result evidence.

The producer ran the complete `test_empirical*.py` discovery set: 125 tests,
exit zero, every recorded line `ok`, with raw stdout/stderr retained. The tests
include the original C4 integration, neural-witness, durable-stage, predecessor,
read/write, fit, forward and policy checks. Seven new V2 tests cover:

- cold authenticated Jinja compile/render under the exact binding and the
  original guard's reproduced rejection in a separate process;
- exact rendered prompt and token-ID equality for the real pinned Qwen tokenizer
  in separate guarded and unguarded CPU processes, with no model weights;
- standalone, method, forged-path, unauthorized direct-Jinja and nested
  `generate` rejection, plus fit/retrieval/file/network/process/forward denials;
- all five fixed stage paths, shared aliases, config pin, V1 immutability,
  V2 no-overwrite and versioned result/control extension.

Every profile-based denial ran in a separate process because CPython clears the
profile after a callback exception. Audit-hook denials remain distinct and were
also isolated. The nested test admits the exact outer compiler event but rejects
an invented descendant `generate`, establishing that the exemption does not
propagate down the call stack.

The producer rehashed all 30,912 environment files before and after the tests,
14 frozen controls, 82 accepted C3 runtime files and five V1 failure artifacts.
It recorded zero model-weight loads, model forwards, scientific fits, current
benchmark payload reads and fresh Gold values. Producer task manifest:
`42872b7b7f0b56a7b22eddf5bb6de75ec1a61c1a0e11eff241bc11c175e86517`.

The client independently parsed all 125 raw success lines, reran the seven V2
tests, rehashed the environment and controls, and reopened every member of the
producer task archive. Client manifest:
`9529abbb046a86f50bbad90550f9dc1192682169722f21424e4fb394ff2e1e74`.
Private archive:
`8675ea66f91dcea5002396c1e07b86cc141187b9473e93f99a22db6666766d9d`.

The first client audit parser used a CRLF-sensitive regex and stopped before an
acceptance result; it is preserved under manifest
`511fa1be641abef450bf5fe7ef7a31f9e05fa15c011e5985697fb4856e721ebb`.
It had no scientific or GPU effect.

Next, build a commit-bound V2 execution config and external controller with raw
logs, confirm V1 remains sealed and the V2 namespace absent, then execute the
complete original invented GPU protocol once. Preserve any V2 failure. On PASS,
independently audit its models, counters, witnesses, bindings, manifests and
unchanged inputs before authorizing base scoring.

P0 remains C4 completion, prelabel acceptance, cost/D execution and contribution
assessment. P1 remains complete cost/provenance/release fidelity. P2 remains CAS
year/category/target-journal qualification without extra empirical search.
