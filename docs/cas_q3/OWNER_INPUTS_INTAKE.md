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

To convert the current missing paths into a single Chinese response form without
publishing any already supplied values, run:

```text
python scripts/build_cas_q3_owner_reply_packet.py
```

The tracked reply packet and its verification receipt contain missing paths,
counts and static instructions only. They must never contain values copied from
the ignored local intake. The packet is an intake aid, not an authorization or
an independently verified declaration.

After the local intake passes, generate a new versioned private draft directory:

```text
python scripts/build_cas_q3_private_submission_packet.py --input docs/cas_q3/OWNER_INPUTS.local.json --output output/private_submission/v1
```

The output tree is ignored by Git because its title page, declarations and
cover-letter draft contain personal facts. The builder refuses incomplete
inputs and an existing output directory. Its console/JSON receipt contains only
file hashes and author/affiliation counts, and always records that independent
CAS authority, target formatting, release and submission authorization remain
open.

For the selected Applied Intelligence route, the complete target-specific
private builder is:

```text
python scripts/build_cas_q3_applied_intelligence_private_submission.py --input docs/cas_q3/OWNER_INPUTS.local.json --output output/private_submission/applied_intelligence_v1
```

It authenticates the private anonymous complete-source transport, injects the
validated author/declaration facts, creates a flat ten-member source ZIP,
compiles the author-populated PDF and writes a private cover letter plus a
redacted receipt. The output directory must be new. A successful build remains
submission-unauthorized until publisher-template acceptance and the final
Astra xhigh audit pass.

`null` means unanswered. Use an explicit factual value when the answer is
negative: for example, `NONE_DISCLOSED` for no overlapping work or
`NONE_NOT_SUPPLIED` for an author ORCID. ORCID is optional because the target
journal says “if available” and recommends rather than requires it; `null` is
also accepted. Every author entry has this shape:

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
`NO_MANDATORY_APC`. The adjacent
`publication_charge_evidence_or_acknowledgement` field must identify the
retained current price/date-rule acknowledgement and payer or funding route,
the confirmed waiver/agreement evidence, or the official no-mandatory-APC
source. For Discover Computing, the 2026-09-14 official-page snapshot is
recorded in `P0_H_DISCOVER_COMPUTING_APC_AUDIT.md`; its listed prices are not a
future quote because the publisher applies the acceptance-date price.

The CRediT map uses an empty list for every role that did not occur, and every
named contributor must be an author in `authors_in_order`. Each listed author
must have at least one truthful role; the validator does not force Supervision,
Project administration or any other role that did not occur. A separate
corresponding-author postal address and acknowledgements are optional. The
responsible authors must approve
the AI-assistance statement or replace it with target-compliant truthful wording
before setting its approval field to `true`.

## Promotion boundary

A complete local file produces
`PASS_OWNER_INPUTS_COMPLETE_PENDING_INDEPENDENT_EVIDENCE_AND_ARTIFACT_GATES`.
That result means only that the factual intake is structurally complete. The
project lead must still verify the retained CAS authority and journal policy,
implement the authorized license/release decision, populate the manuscript and
submission forms from the private drafts, build the target-specific artifacts,
and obtain the final artifact-bound GPT-6 Astra xhigh audit. Until those records
pass, the top-level readiness gate must remain fail-closed.
