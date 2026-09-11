# Historical reference and outcome replay: client acceptance

Research Lead acceptance, 2026-09-11. **CAS Q2 STATUS: NOT READY.**

Accepted: `ACCEPTED_FULL_HISTORICAL_REFERENCE_AND_OUTCOME_REPLAY` under the
prospectively frozen [contract](HISTORICAL_OUTCOME_REPLAY_CONTRACT.md).
The original producer and independent validator both completed successfully;
the client separately checked the sealed outputs and source bindings.

## Complete numerical result

All 4,500 historical question IDs are disjoint from the current 6,000 IDs.
This boundary was checked before reference decoding. Unchanged original
selected-reference readers and metric function bodies reconstructed all
13,500 historical rows, preserving order, aliases and all nine strata.
The new ledger is byte-exact to the archived 1,767,807-byte ledger, SHA-256
`2ead94602f5aaf2c63cda7acf87e8ef2aa3d28a2feffb245f3d557be0e250576`.
The selected-reference binding also matches the original
`f31bc4f39f37ebbcb05eff0d15fa568c0c352d3bf8da0c7579397192eb99ebd1`.
Archived numeric values were not used to construct the new ledger.

A separate process reread the selected references and used independent metric
formulas to check all 54,000 new and 54,000 archived metric values. All EM
comparisons are exact; maximum F1 absolute error is **0.0**, within the unchanged
`1e-15` bound. The client rechecked 30 original function/class AST records.
Seven invented fixture cases per process and an independent corrupted-metric
rejection passed. Both stderr logs are empty.

## Actual dependencies and preservation

Both processes loaded PyArrow 20.0.0 from the accepted separate new target;
their actual module paths and ten mapped native binaries were authenticated.
Each process made 14 original row-group/column reads with the original options,
converted 7,405 Hotpot IDs and only the 1,500 selected answer cells to Python.
JSON/JSONL used the original ID-first and selected-span reading behavior.
No raw reference string was written to disk or emitted in tool output.

All 15 used original files, 15 restored files, 21,267 environment/target files,
nine controls and five earlier failure/diagnostic seals remained unchanged.
There were zero new fits, neural forwards or current empirical payload/Gold
reads. Actual takeover fits remain **185**.

Implementation commit: `65e28d9f9b83074f04ef353bfdb17740899df34f`.
Execution freeze: `76e83cab97d0ea566be425b27f3a669df2223011d1d1bf4f889edbc6bb2a26c4`.
Execution seal: `2deedc9104b74f50b242f5fe7e1a1a35e503fb097760ab58a336724476c22408`.
The [results](HISTORICAL_OUTCOME_REPLAY_RESULTS.json) record the independently
checked private archive; original raw sources and installed dependencies remain
external sealed inputs. No private artifact is uploaded.

## Scope and next gate

The processes share the original reference reader; their metric formulas are
independent. Native Arrow pages may decompress unselected rows even though no
unselected answer is converted to Python. These are explicit limitations.
This establishes complete historical source-to-outcome numerical replay with
disclosed IO/path bindings. It does not establish unchanged full CLI execution,
current D execution, full neural replay or reproduction on another host.

The historical HGB model's one-byte reproduction gate stays **FAILED**.
Seven original fit-time receipts and an earlier independent whole-training
manifest pin remain missing. Neither previously rejected contribution gate is
reopened; there is still no accepted novel candidate or fresh outcome evidence.

P0: finish original C3 canonical generation and its fixed neural replay, then
execute the separately accepted complete validation binding and perform client
acceptance before C4, complete prelabel checks, cost/D and contribution review.
P1: BGE and full neural/pipeline execution bindings and reproducibility evidence.
P2: CAS year, institutional category rule and target journal remain undecided;
no additional model, feature, seed or budget search is authorized by this gate.
