# P0-H institution-recognized CAS record intake

**Decision:** `PASS_PRIVATE_RECORD_INTAKE_PATH_PREPARED_AUTHORITY_CONTENT_STILL_MISSING`

**CAS Q3 STATUS: NOT READY.**

The project now has a fail-closed local intake for the institution-recognized
CAS record that is still required for Applied Intelligence. It is designed for
an authenticated CAS-platform screenshot/export or a formal HBUT record. The
record bytes and completed metadata stay outside Git; the verifier emits only
missing/error field paths, byte count and Boolean decisions.

This intake does not turn a responsible-author transcription into independent
evidence. Even after the local structure and SHA-256 pass, its strongest
decision is
`PASS_PRIVATE_INSTITUTIONAL_CAS_RECORD_INTEGRITY_PREFLIGHT_PENDING_CLIENT_CONTENT_AUDIT`.
The project lead must inspect the retained record itself and issue a separate,
hash-bound, redacted acceptance before P0-H can close.

## Local use after the authoritative record is obtained

1. Copy `docs/cas_q3/INSTITUTIONAL_CAS_RECORD_TEMPLATE.json` to the Git-ignored
   `docs/cas_q3/INSTITUTIONAL_CAS_RECORD.local.json`.
2. Put the screenshot, PDF, export, email or letter under the Git-ignored
   `evidence/private/institutional_cas_record/` directory.
3. Fill the local JSON from the visible record. The accepted target identity is
   Applied Intelligence, Print ISSN `0924-669X`, Electronic ISSN `1573-7497`,
   Computer Science major category, and tier Q1, Q2 or Q3.
4. Compute the evidence file's SHA-256 and enter it in the local JSON.
5. Run `python scripts/verify_cas_q3_institutional_cas_record.py`.
6. Provide the retained bytes to the project lead for a separate visual/content
   audit. A structural pass alone does not close P0-H or authorize submission.

The record must also state the recognized CAS edition/year, the institutional
recognition-date rule, the treatment of title/ISSN changes and applicability to
an HBUT-first-affiliation output. JCR quartiles, unofficial ranking sites and a
record that omits the current title or both ISSNs are insufficient.

At preparation time no local institution-recognized record had been received.
No evidence bytes were read, and no CAS tier was inferred.
