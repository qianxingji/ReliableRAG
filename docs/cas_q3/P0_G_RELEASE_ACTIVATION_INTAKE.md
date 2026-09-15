# P0-G final release-activation intake

**Decision:** `PASS_FAIL_CLOSED_RELEASE_ACTIVATION_INTAKE_PREPARED_ACTIVATION_NOT_ATTEMPTED`

**CAS Q3 STATUS: NOT READY.**

The institutional release-record intake authenticates the approval evidence and
the intended aggregate scope. It does not yet bind the approval to the exact
submission revision, published repository reference, permanent archive record,
or an editor-requested restricted-review delivery. This intake closes that
engineering gap without performing any publication or distribution action.

`RELEASE_ACTIVATION_RECORD_TEMPLATE.json` is deliberately incomplete. A private
copy can become structurally complete only after it records all of the following:

- a client-audited institutional/owner release decision;
- the exact frozen Git commit and its immutable commit URL;
- the exact retained archive bytes and manifest hash, bound to the validated
  aggregate V2 candidate or an explicitly reviewed successor;
- a resolving DOI or other persistent identifier whose landing record binds the
  exact archive hash;
- either an actual editor-designated/accepted restricted-review delivery or the
  explicit fact that no such delivery was requested; and
- a manual comparison of the authorization, commit, archive and persistent
  landing record.

The verifier does not fetch URLs, publish a tag or release, upload an archive,
interpret an approval, or authorize distribution. Even a structurally complete
record can produce only
`PASS_RELEASE_ACTIVATION_RECORD_STRUCTURALLY_COMPLETE_PENDING_CLIENT_CONTENT_FINAL_ARTIFACT_AND_ASTRA_AUDITS`.
Client content review, final artifact rebinding and the required Astra xhigh
submission audit remain mandatory.

## Use after approvals and archive creation

1. Run `python scripts/prepare_cas_q3_private_closure_workspace.py`; it creates
   the ignored local activation file and evidence directory without overwriting
   any existing bytes.
2. Retain the exact release archive under
   `evidence/private/release_activation/` and fill only observed values in
   `docs/cas_q3/RELEASE_ACTIVATION_RECORD.local.json`.
3. Run `python scripts/verify_cas_q3_release_activation_record.py`.
4. Perform separate client content and artifact audits. Escalate the frozen
   result to Astra xhigh for the final P0-G/submission decision.

No real authorization, tag, release, archive deposit, DOI or restricted delivery
was created during this preparation.

## Validation

The CAS Q3 test family passes 143 tests. The complete repository suite passes
417 tests with two documented Windows platform skips when run through the
project environment at `E:/paper/ReliableRAG/.venv/Scripts/python.exe`.
The reviewer map authenticates 203 repository records through 1,539 checks, and
the fail-closed top gate verifies 235 repository hashes through 852 checks.

One failed engineering run is retained: the first full-suite command used the
system Python 3.10 interpreter, which lacks `torch`, `scipy`, `sklearn` and
`threadpoolctl`. It therefore reported eight import errors and two dependent
failures across 387 discovered tests, with two skips. Re-running the same suite
in the established project environment passed; the failed run did not read or
change scientific payloads and is not treated as an experimental result.
