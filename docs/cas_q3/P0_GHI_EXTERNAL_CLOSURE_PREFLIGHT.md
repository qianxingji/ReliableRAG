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

## Local workspace execution on 2026-09-14

`python scripts/prepare_cas_q3_private_closure_workspace.py` was executed in the
isolated worktree. It preserved the existing owner-input file byte-for-byte and
created the two original institutional `.local.json` files from their empty
templates. The preparer now also covers the separate institutional manuscript-
approval placeholder and its private-evidence directory. It prints paths and
state labels only; it prints no private values.

The unified verifier can now read all three files, but the two newly created
files are placeholders, not institutional records. After the responsible
author supplied a third input batch, the owner input remains at 6 missing
fields and zero validation errors. The all-author approval and both
institutional-review-required flags are recorded, along with owner assertions
about the copyright holder and candidate 2025 CAS edition. Unapproved AI
wording, an undated AI-tool entry, a label-only competing-interests entry and
the two required institutional approvals stay open; no supplied value is
emitted in this record. The CAS placeholder has 22 missing
fields and zero validation errors. The release placeholder has 22 missing fields
and five expected fail-closed placeholder conflicts. No institutional evidence
bytes were read, no cross-record inconsistency was observed, and the command
returned exit code 2 with
`FAIL_CLOSED_PRIVATE_EXTERNAL_CLOSURE_INPUTS_INCOMPLETE_INVALID_OR_INCONSISTENT`.
P0-G, P0-H and P0-I therefore remain open.

Its strongest possible decision is
`PASS_PRIVATE_EXTERNAL_CLOSURE_INPUTS_STRUCTURALLY_COMPLETE_PENDING_CLIENT_CONTENT_ARTIFACT_AND_ASTRA_AUDITS`.
That result does not certify the meaning or authority of either retained record.
Separate client content audits, the author-populated target build, explicit
archive authorization and the final Astra xhigh audit remain mandatory.
