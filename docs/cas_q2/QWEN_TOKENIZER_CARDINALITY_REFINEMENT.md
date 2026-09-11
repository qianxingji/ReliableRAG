# Explicit constant-cardinality binding for historical validation

Research Lead decision, 2026-09-11. CAS Q2 STATUS: NOT READY.

The sealed timing diagnostic 1a95168f94600462f2c20441a28d02c307aa7678437e7c1dc5b2005b9a7d810f
measures five len(tokenizer) calls at 0.0468-0.0540 seconds each; each returns
151,665. The original validator calls it once per generated ID. Extrapolating
627,012 such calls is roughly 8-9 hours for this operation alone; this is a
timing estimate, not a completed runtime or a backend complexity proof.

The v1 full producer result remains numerically valid; its independent run is
incomplete and its shutdown defect prevents complete lifecycle acceptance.
Stop only that new historical validator after recording its exact PID, creation
time, command and reason. Let its parent preserve a failure seal. Never stop,
restart or change the original live empirical C3 process.

The new v2 full run must use the separately frozen shutdown correction. Producer,
IO adapter, historical inputs, tokenizer version/assets, scientific function ASTs,
all exact expectations, sample universe and limits remain unchanged. A new v2
validator may specialize only its selected original namespace's global len:
for the one fixed tokenizer object, return its initially measured cardinality;
for every other object, call the ordinary Python built-in len. Do not monkeypatch
the tokenizer or packages. This is an explicit execution binding change, not
literal unchanged invocation of the old validator or whole CLI.

Freeze tokenizer.get_vocab() canonical hash and cardinality before any receipt
validation. Prohibit scientific changes or vocabulary mutation; the code performs
no token additions. Recheck the complete vocabulary hash and ordinary tokenizer
cardinality at every 1,500 canonical traces and at both mode endings. Record
the number of specialized len calls and reconcile it to every archived generated
ID checked. Preserve source AST hashes and record the one injected global and its
exact scope. Full historical input IDs/masks/strings/counts still match exactly.

Add three bounded rejection checks using in-memory copies of the first archived
receipt: wrong prompt hash, changed input ID, out-of-vocabulary generated ID.
Require the original specific failure reason in each case. Retain their results
and exclude their extra cardinality calls from full-ledger coverage counts.
Never edit the archived row or present these rejection fixtures as new samples.

Require both new full processes to finish, no unexpected stderr, all original
independent checks and exact producer comparisons, and full before/after input
and environment preservation. The lifecycle diagnostic
40be35afd5f5cf6ac1943eba0dcba5c0e74c306a704b59b818488dde0b9268b6
supports the new guard; retain its two failed diagnostic predecessors too.
All v1 files and failed/partial results remain immutable. Public acceptance must
name the cardinality binding and shared tokenizer implementation; no claim of
neural replay, unchanged original CLI or Submission Ready is permitted.
