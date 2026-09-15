# Phi reader invented-only compatibility preflight contract

2026-09-12. **CAS Q2 STATUS: NOT READY.**

This is the engineering gate required by `PHI_READER_REPLICATION_PROTOCOL_V1.md`.
It authorizes one committed GPU preflight using invented text only, followed by
a separate tokenizer-only validator. It authorizes no benchmark projection,
generation, score, fit, action, answer or Gold access.

The producer must load the pinned Phi revision sequentially in the authenticated
original generation adapter and original answer-token likelihood scorer. It must
run exactly four invented generations: two identical short answers, one repair
query and one 16,000-character-boundary answer. It must run exactly two neural
teacher-forced likelihood forwards plus one cache hit: one short answer, its
exact repeat and one sequence truncated to the fixed 8,192-token scoring length.
Save prompt/input/generated IDs, parsing output, selected target logits, per-token
log normalizers and reductions. Hooks may observe outputs but never alter them.

Require CUDA BF16, deterministic algorithms, seed 20260830, disabled TF32,
greedy decoding and the local offline snapshot. Record both sequential model
loads, forwards, peak allocation, package versions, source/model/prompt hashes,
execution boundary and durable output manifest. A failure stays sealed and is
not repeated under this version.

The independent process imports no producer or original executor. It may load
the pinned tokenizer only, with weight reads prohibited. It independently
renders both evidence cases, applies the chat template, reconstructs every
prompt/input/answer token and generation decode, repeats answer/query parsing,
and derives each saved token log probability from chosen logit minus saved
log-normalizer. It verifies cache identity/reductions and every producer/source
hash. Passing this bounded gate establishes interface compatibility only. It
does not authorize benchmark execution until a separate development/test
implementation and input freeze are committed and accepted.

