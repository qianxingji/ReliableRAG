# P0-I Applied Intelligence required-owner-field correction

**Decision:** `PASS_APPLIED_INTELLIGENCE_OWNER_GATE_CORRECTION_19_REAL_MISSING_ZERO_ERRORS`

**CAS Q3 STATUS: NOT READY.**

The current [Applied Intelligence submission
guidelines](https://link.springer.com/journal/10489/submission-guidelines) state
that ORCID is supplied “if available” and separately recommend author IDs. They
require author affiliations and an active corresponding-author email, without
listing a second postal-address field as an independent mandatory item.
Acknowledgements are conditional on there being people, grants or funds to
acknowledge. Author-contribution statements are recommended, with examples of
free text and CRediT, but the journal does not mandate that every paper populate
a fixed set of nine CRediT roles.

The previous local validator therefore imposed four unsupported constraints:

- mandatory ORCID or an explicit no-ORCID sentinel;
- a separate corresponding-author postal address even when the affiliation
  address is already present;
- a mandatory acknowledgement placeholder when no acknowledgement applies;
- mandatory population of nine named CRediT roles, including Supervision and
  Project administration even when those roles may not have occurred.

The corrected validator keeps those schema fields available but makes the first
three optional. It now requires every listed author to appear in at least one
truthful contribution role and does not force any particular role. This removes
twelve old missing paths and adds one truthful per-author contribution path, a
net reduction of eleven. The real ignored intake moves from 30 to **19 missing
fields with zero validation errors**.

Funding, competing interests, ethics, AI-assistance disclosure and approval,
originality, exclusive submission, all-author approval, responsible-authority
approval evidence, code holder/year/release review and the institutional CAS
edition remain hard gates. The private builders omit absent optional fields
instead of rendering the string `None`.

The earlier synthetic private-builder receipt remains unchanged: its 30-field
count is an accurate historical snapshot under the former validator. No real
identity-bearing package has been built, and neither submission nor distribution
is authorized by this correction.
