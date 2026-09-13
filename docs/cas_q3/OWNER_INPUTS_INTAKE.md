# Consolidated owner-input intake for P0-G, P0-H and P0-I

**CAS Q3 STATUS: NOT READY.**

This intake consolidates the remaining owner, institution and author facts into
one local machine-readable file. It does not make a self-attested journal tier,
copyright claim or author declaration independently verified, and it cannot by
itself authorize distribution or submission.

## Use

1. Copy `docs/cas_q3/OWNER_INPUTS_TEMPLATE.json` to
   `docs/cas_q3/OWNER_INPUTS.local.json`.
2. Fill the local copy. The exact local filename is ignored by Git so personal
   details are not committed accidentally.
3. Run:

   ```text
   python scripts/verify_cas_q3_owner_inputs.py --input docs/cas_q3/OWNER_INPUTS.local.json
   ```

The verifier prints only field paths, counts and a decision. It never echoes
names, email addresses, postal addresses, declaration text or other supplied
values, and it writes no receipt containing those values.

`null` means unanswered. Use an explicit factual value when the answer is
negative: for example, `NONE` for no acknowledgement, `NONE_DISCLOSED` for no
overlapping work, or `NONE_NOT_SUPPLIED` for an author ORCID. Every author entry
must have this shape:

```json
{
  "name": "Publishing name",
  "affiliation_ids": ["aff1"],
  "orcid": "0000-0000-0000-0000"
}
```

Every affiliation entry must have this shape:

```json
{
  "id": "aff1",
  "institution": "Institution",
  "department": "Department",
  "city": "City",
  "postal_code": "Postal code",
  "country": "Country"
}
```

The accepted project-license choices are `Apache-2.0`, `MIT`, and
`NO_PUBLIC_CODE_LICENSE_YET`. If institutional release review is required, its
status must be `APPROVED` and the evidence field must identify the retained
record before a public release can proceed. Otherwise use `NOT_REQUIRED`.

The journal block requires the institution-recognized CAS edition/year, exact
major or minor category basis, category name, current title and ISSNs, Q3
result, title/ISSN-change treatment, recognition-date rule and a retained
authority. `verified_tier` must be `Q3`; JCR quartiles do not satisfy this
field. `publication_charge_route` accepts `ACCEPTED`, `WAIVER_CONFIRMED`, or
`NO_MANDATORY_APC`.

The CRediT map may use an empty list only for a role that did not occur, but
every named contributor must be an author in `authors_in_order`. At least one
author must be assigned to Conceptualization, Methodology, Software, Validation,
Formal analysis, Writing - original draft, Writing - review and editing,
Supervision and Project administration. The responsible authors must approve
the AI-assistance statement or replace it with target-compliant truthful wording
before setting its approval field to `true`.

## Promotion boundary

A complete local file produces
`PASS_OWNER_INPUTS_COMPLETE_PENDING_INDEPENDENT_EVIDENCE_AND_ARTIFACT_GATES`.
That result means only that the factual intake is structurally complete. The
project lead must still verify the retained CAS authority and journal policy,
implement the authorized license/release decision, populate the manuscript and
submission forms, build the target-specific artifacts, and obtain the final
artifact-bound GPT-6 Astra xhigh audit. Until those records pass, the top-level
readiness gate must remain fail-closed.
