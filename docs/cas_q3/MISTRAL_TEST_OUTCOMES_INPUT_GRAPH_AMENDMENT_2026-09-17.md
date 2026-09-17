# Mistral test numeric-outcome input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before formal test Gold access. It
changes no selected identity, answer, reference, metric, action, fitted
parameter, budget or endpoint. It adds no new Gold exposure and produces no
numeric result.

## Gap

The outcome producer fully checked the action, a0 and a1 manifests but recorded
only their manifest files and independent validation receipts in its executable
freeze. It then read action and answer member payloads. Those payloads were
content-addressed by the manifests, but they were absent from the post-output
rehash, leaving a mutation window after initial validation. The independent
validator also checked only that the three validation receipts appeared in the
freeze instead of proving exact input-path equality.

## Prospective correction

Before writing the Gold-access marker, the producer now freezes every member and
manifest of the accepted action, a0 and a1 namespaces, their three independent
validation receipts, the complete authenticated original Gold/metric/PyArrow
path set, all direct runtime and metric sources, the Python executable, protocol
and this amendment. Every frozen path is rehashed after numeric-only outcomes
are written.

Before rereading references, the independent validator reconstructs the same
three recursive namespaces, authenticates the complete opaque original path set
without deserializing references, and requires exact set equality. It also
checks the recorded Python and NumPy identities before reference materialization.

Eleven focused invented-only tests cover population balance, duplicate/missing
rows, metric edge cases, answer selection, numeric-only schema, action-before-
Gold ordering, failure-text withholding, validator independence, exact input
closure and unexpected-file rejection. No test reference, metric value, model
fit, neural forward or formal outcome row was read or produced while making or
testing this amendment.
