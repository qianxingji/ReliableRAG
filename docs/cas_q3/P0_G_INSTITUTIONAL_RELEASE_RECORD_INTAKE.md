# P0-G institutional release-record intake

**Decision:** `PASS_PRIVATE_RELEASE_RECORD_INTAKE_PREPARED_EXTERNAL_DECISIONS_MISSING`

**CAS Q3 STATUS: NOT READY.**

The project now has a fail-closed private intake for the owner and institutional
evidence needed to resolve the remaining P0-G release boundary. The retained
record may be a formal HBUT email/letter/system record, legal-review memo, or a
ZIP evidence bundle. Its bytes and completed metadata stay outside Git.

The intake binds the exact Apache-2.0 choice and corrected aggregate V2 SHA-256
`4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8`.
It requires a legal holder and year/range, a consistent institutional-review and
NOTICE decision, explicit treatment of the Qwen research-license and non-`-c`
DeBERTa caveat, and confirmation that no model weights, benchmark payloads,
answers or per-question records are in the intended release.

A structural and byte-integrity pass does not interpret legal advice or
authorize publication. Its strongest possible result remains
`PASS_PRIVATE_INSTITUTIONAL_RELEASE_RECORD_INTEGRITY_PREFLIGHT_PENDING_CLIENT_AND_OWNER_DECISIONS`.
The project lead must inspect the retained evidence, and the owner must later
authorize the exact validated archive. A persistent identifier and the
journal-accepted private-review route also remain separate gates.

## Local use after the evidence is obtained

1. Copy `docs/cas_q3/INSTITUTIONAL_RELEASE_RECORD_TEMPLATE.json` to the
   Git-ignored `docs/cas_q3/INSTITUTIONAL_RELEASE_RECORD.local.json`.
2. Put the retained PDF, screenshot, email, letter or ZIP evidence bundle under
   `evidence/private/institutional_release_record/`.
3. Fill the local JSON using only actual owner/institution decisions. If review
   is required, the status must be `APPROVED`; otherwise it must be
   `NOT_REQUIRED` with retained evidence for that conclusion.
4. Compute the evidence file SHA-256 and run
   `python scripts/verify_cas_q3_institutional_release_record.py`.
5. Provide the same fixed bytes for a separate client content audit.

At preparation time no such evidence bundle had been received. No private
release evidence or scientific payload was read, and distribution remains
unauthorized.
