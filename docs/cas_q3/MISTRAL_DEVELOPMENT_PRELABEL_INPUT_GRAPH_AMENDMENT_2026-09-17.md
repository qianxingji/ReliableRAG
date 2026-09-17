# Mistral development common-prelabel input-graph amendment

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

This prospective amendment was committed while the formal development
`a0_query` producer was still running and before common-prelabel execution. It
changes no method, feature order, eligibility rule, forced-Keep rule, label,
action budget, endpoint or tuning rule. It strengthens only the provenance
boundary immediately before development Gold may be opened.

## Gap

The initial implementation authenticated HGB and GbV manifests and their
independent validations, but its executable freeze recorded only manifest files
rather than every predecessor payload member. It also pinned the legacy runtime
manifest without binding all of its authenticated files. The independent
validator checked the two validation receipts but did not reconstruct the exact
direct input set.

## Prospective correction

Before constructing any common-eligibility row, the producer must now:

1. verify and record all 55 historical runtime payload members and the runtime
   manifest, allowing only generated `__pycache__/*.pyc` extras;
2. verify and record every member of the accepted Mistral input freeze, HGB
   stage and paired-GbV stage, plus both independent validation receipts;
3. record the producer and independent validator, acquisition/scoring helpers,
   imported manifest helper, frozen scoring protocol, this amendment and the
   canonical trace ledger; and
4. rehash every recorded input before the PASS receipt and before downstream
   development Gold access.

The independent no-model validator reconstructs the identical path set,
requires exact equality with the executable freeze, validates exact recursive
manifest coverage, independently rebuilds all 13,500 shared prelabel rows, and
retains the exact producer binding for `PRELABEL_ROWS.jsonl`.

Nine focused prelabel tests cover fixed method/feature order, independent row
reconstruction, native and NLI forced-Keep cases, mismatch failures, validator
independence, exact input-graph requirements and rejection of an unexpected
manifest file. The complete Mistral suite passes 166 tests.

No Gold access, model load, model forward, scientific fit or test access
occurred while making or testing this amendment. The active `a0_query`
executable, source commit and all 31 frozen inputs remain unchanged.
