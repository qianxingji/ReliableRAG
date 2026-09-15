# Accepted empirical selected-outcome mapping and validation

**Decision: ACCEPTED.** The first fresh-Gold mapping and a separate method-blind
outcome validator completed on the fixed 6,000-question cohort. The resulting
18,000-row numeric ledger is authorized for the frozen analysis. No policy was
selected or compared during either process.

## Bound result

- Source commit: `710d4cf7159f0de8999b1b5d0fc38dd71881a697`
- Mapping scientific manifest: `34dfcd2e5e43e20a1dd7eeb84d81a110dbac8bb65cd00aea4582dceb1b5bc23d`
- Mapping external manifest: `f54c6b7ac76788ba17bc8dee442ef0ac07fd58a46a6575d7f98164ffd1579798`
- Outcome-validation scientific manifest: `e0f3321c88d1561ab3daa281280713fcd65c820672bd392e036e5f5df39c1953`
- Outcome-validation external manifest: `12bf9825a8265e00e209bd65f6d1c8c88dcd2a935b33e27b135eb82768318e06`
- Numeric ledger: `e8ad8addee644bdd1ef2f620895f1ba1abf32ac0568d514872ed6776e7059408`
- Independent validation: `94d3448495394e40b388f5c19c0f8606f226d02c3c44b5a135e377568fe614fa`
- Client audit: `68c5eac62225f10244e32d97d8168193854bcc6aedfc97eecc53601dd26ca595`

The mapper reads only the fixed cohort IDs, canonical a0/a1 answer strings and
the three authenticated original reference sources. It materializes labels for
6,000 selected questions, containing 6,863 reference strings under the frozen
dataset-specific alias rules, and decodes 36,000 canonical answers. It writes
exactly 18,000 seven-field numeric rows. It decodes no method input, writes no
reference string, performs no quality analysis, model forward, fit, retrieval
or generation, and records no boundary denial or forbidden call.

The independent process rereads the same 6,000 selected labels from the source
bytes, independently recomputes all 72,000 EM/F1 scalar values, and obtains an
exact accepted match under the frozen `1e-15` F1 bound. The reference-set binding
is `535727faaba3578cbeaaf6b15441ec032e621e36f9db64c5b2918c6dd264247b`.
Each dataset contributes 2,000 questions and every question has the three fixed
retriever siblings. Both processes report zero unselected reference values
materialized in Python; the disclosed HotpotQA selected-column Parquet read may
physically decompress pages containing unselected rows.

The client audit checks the two scientific namespaces and external controllers,
the predecessor chain, exact V2 path binding, validation seal, reference/source
bindings and all 18,000 numeric rows without performing a third Gold read. It
checks 144,003 ledger schema/identity constraints, rehashes 18,304 unique
executable inputs and 30,912 environment files, and reopens the metadata archive.

**CAS Q2 STATUS: NOT READY.** P0 is now the frozen 20,000-draw analysis, its
complete independent validator and real-result/Claim review. P1 remains fair
comparison, robustness, contamination/provenance and reproducible-release
closure. P2 remains final Method/Claim, paper and journal-scope readiness. Major
rejection risks remain no cleared novel contribution, unknown current policy
results until analysis, historical fit-time provenance gaps, incomplete full
neural relocation replay and undecided CAS year/category/target journal.
