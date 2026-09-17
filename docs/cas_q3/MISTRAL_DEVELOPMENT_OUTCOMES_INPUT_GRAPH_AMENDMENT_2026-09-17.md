# Mistral development outcomes input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running and before any Mistral development Gold
access. It changes no selected question, reference source, metric definition,
role allocation, label, endpoint, candidate grid or tuning rule. It strengthens
the final provenance boundary before the one authorized development-label read.

## Gap

The initial outcomes implementation already authenticated the historical
reference sources, metric/parser/reader definitions, controlled PyArrow package
and runtime environment. Its executable freeze nevertheless recorded only the
prelabel, A0, A1 and Mistral-input manifest files rather than all members those
manifests authenticated. The independent validator checked the frozen rows and
prelabel acceptance but did not reconstruct the entire direct path set.

## Prospective correction

Before writing the Gold-access marker, the producer must now:

1. verify and record every member of the accepted common-prelabel, `a0_query`,
   `a1_likelihood` and Mistral input-freeze namespaces plus the independent
   prelabel validation receipt;
2. retain the existing exact authentication of 785 original paths: the
   final-evaluation manifest, selected-reference sources, native
   metric/parser/readers, Python executable and 770 controlled PyArrow package
   files;
3. record the producer and independent validator, native and independent
   outcome formulas, pool/artifact safety helpers, acquisition/scoring helpers,
   imported A0 helper, canonical serializer, frozen scoring protocol and this
   amendment; and
4. rehash every recorded input after numeric outcome emission and before the
   PASS receipt.

The independent validator performs the same metadata-only authentication before
opening development Gold, reconstructs the identical direct path set, and
requires exact equality with the producer's executable freeze. It retains the
existing independent reread of exactly 4,500 selected development labels,
recomputation of all 54,000 EM/F1 values, zero test access and exact binding of
`DEVELOPMENT_OUTCOMES.jsonl`.

Nine focused outcome tests cover exact cohort/role scope, sibling failures,
native-versus-independent metric agreement, invalid inputs, validator
independence, explicit Gold/test boundaries, exact input-graph requirements and
rejection of an unexpected manifest file. The complete Mistral suite passes 168
tests.

No development Gold, test label, model load, model forward or scientific fit
was accessed while making or testing this amendment. The active `a0_query`
executable, source commit and all 31 frozen inputs remain unchanged.
