# Mistral test action-seal input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before formal action sealing or test
outcome access. It changes no feature, fitted parameter, calibration formula,
tie rule, action cap, method or endpoint. Test Gold and numeric outcomes remain
forbidden, and the action budget remains fixed at 900.

## Gap

The action producer and validator fully checked the accepted development tuning
and test prelabel manifests, but the executable freeze recorded only the two
manifest files and validation receipts. The producer then read member payloads
that were content-addressed by those manifests. Because the members themselves
were absent from the post-execution input recheck, a mutation between initial
manifest validation and payload reading was not directly closed. The independent
validator also required only the two validation receipts to appear in the
freeze, rather than proving exact input-path equality.

## Prospective correction

The producer now freezes every member plus the manifest of both predecessor
namespaces, both independent validation receipts, every direct production and
independent formula/runtime source, the Python executable, the protocol and this
amendment. All paths are rehashed after the action ledger is written.

The independent validator reconstructs the same two recursive namespaces and
direct controls, then requires exact set equality before probability or action
reconstruction. It also verifies the exact Python executable/version and NumPy
version stored by the producer. The production and independent arithmetic paths
remain separate.

Ten focused invented-only tests cover probability/action equivalence, fixed-cap
edge cases, ties, numerical stability, hidden-label and mutation failures,
dependency isolation, recursive-manifest integrity, exact input closure and
unexpected-file rejection. No formal action ledger, test Gold value, test
outcome, model fit or neural forward was produced while making or testing this
amendment.
