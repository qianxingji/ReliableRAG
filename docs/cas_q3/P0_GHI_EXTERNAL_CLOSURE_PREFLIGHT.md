# P0-G/H/I private external-closure preflight

Decision: **PASS_PRIVATE_EXTERNAL_CLOSURE_PREFLIGHT_PREPARED_REAL_INPUTS_AND_AUDITS_OPEN**.

**CAS Q3 STATUS: NOT READY.**

The project now has one privacy-safe command that validates the responsible-
author input, institution-recognized CAS record and institutional release record
together. It also checks that target title, ISSNs, edition, major-category tier,
recognition rules, Apache-2.0 choice, legal holder/year and institutional review
state agree across the three private records.

Run:

```text
python scripts/verify_cas_q3_external_closure_inputs.py
```

The command outputs decisions, missing/error counts and field paths only. It
does not print names, email addresses, declarations, evidence text, holder names
or other supplied values. The three local inputs and their evidence remain
Git-ignored.

Its strongest possible decision is
`PASS_PRIVATE_EXTERNAL_CLOSURE_INPUTS_STRUCTURALLY_COMPLETE_PENDING_CLIENT_CONTENT_ARTIFACT_AND_ASTRA_AUDITS`.
That result does not certify the meaning or authority of either retained record.
Separate client content audits, the author-populated target build, explicit
archive authorization and the final Astra xhigh audit remain mandatory.
