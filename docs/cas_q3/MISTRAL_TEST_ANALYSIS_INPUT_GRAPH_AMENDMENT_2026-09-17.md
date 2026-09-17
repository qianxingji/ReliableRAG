# Mistral test analysis input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed before formal test analysis. It
changes no action, outcome, point estimator, bootstrap seed or draw count,
cluster unit, top-K allocation, multiplicity encoding, confidence interval,
family adjustment or endpoint.

## Gap

The analysis producer fully checked the accepted action and numeric-outcome
manifests but recorded only their manifest files and independent validation
receipts in its executable freeze. It then read member payloads. Those members
were content-addressed by the manifests but absent from the post-analysis input
rehash. The independent validator also required only the two validation receipts
to appear in the freeze rather than proving exact input-path equality.

## Prospective correction

The producer now freezes every member plus the manifest of both accepted
predecessor namespaces, both independent validation receipts, all production
and independent arithmetic/storage sources, the weighted top-K kernel, Python
executable, NumPy version, protocol and this amendment. Every path is rehashed
after all 20,000 draws and interval outputs are written.

The independent validator reconstructs the same recursive namespaces and direct
controls, verifies Python and NumPy identity, and requires exact path equality
before reading actions, outcomes or bootstrap artifacts. Its explicit-copy
allocation and independently regenerated RNG stream remain separate from the
producer arithmetic.

Ten focused invented-only tests cover point reports, all-draw equivalence,
four-endpoint adjustment, sparse eligibility, schema and hidden-field failures,
durable draw reconstruction, dependency isolation, recursive-manifest integrity
and exact input closure. No formal draw, test outcome access, model fit, neural
forward or scientific result was produced while making or testing this
amendment.
