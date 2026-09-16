# Mistral development tuning input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running and before any project-data scientific
fit. It changes no row, role, eligibility mask, target, feature, method,
candidate, fold, selection metric, tie rule, fixed reference, action budget or
test boundary.

## Gap

The initial tuning implementation required independently accepted common
prelabels and development outcomes, but its executable freeze recorded only
their two manifest files. It therefore did not directly freeze every payload
member authenticated by those manifests. The independent full-refit validator
verified both namespaces and their acceptance receipts, but only required the
two receipts to be members of the frozen set; it did not reject extra or missing
paths in that set.

## Prospective correction

Before reading numeric development outcomes or attempting a fit, the producer
must now:

1. verify and record every current member of the accepted `prelabel` and
   `development_outcomes` namespaces, including each namespace manifest;
2. record both independent validation receipts;
3. record the producer, non-importing independent refit validator, tuning core,
   acquisition and scoring helpers, validator read/hash helper, empirical
   dataset contract, canonical serializer, Python executable, frozen tuning
   policy, scoring/tuning protocol and this amendment; and
4. rehash every recorded input after all result and event files are written and
   before emitting the PASS receipt.

The independent validator reconstructs the same path set from the current
manifests and fixed controls and requires exact equality with the frozen set
before any audit refit. It retains the existing independent reconstruction of
all folds, fits, pooled losses, tie-breaking, selected heads, fixed-reference
heads and Platt calibration, together with exact output-ledger binding.

The authorized development procedure remains eight candidates per method,
three question-group folds, 78 search fits and six fixed-reference fits in the
producer. The validator repeats 84 fits only as an audit. All unsuccessful
candidates and fit events remain in the durable result and event ledgers. Search
expansion, action-budget tuning and all test access remain forbidden.

Eight focused tuning tests cover scope and common eligibility, source binding,
producer-versus-independent numerical agreement, the complete event journal,
validator independence, test/action-budget closure, exact input-graph
requirements and rejection of an unexpected manifest file. The complete
Mistral suite passes 170 tests. No project Gold,
test value, scientific fit, neural model load or neural model forward was used
while making or testing this amendment.
