# P0-I institutional manuscript-approval intake

Decision: **PASS_PRIVATE_MANUSCRIPT_APPROVAL_INTAKE_PREPARED_APPROVAL_EVIDENCE_MISSING**.

**CAS Q3 STATUS: NOT READY.**

The responsible author stated that institutional manuscript approval is
required. The tracked
`INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD_TEMPLATE.json` contains placeholders
only. Its `.local.json` counterpart and all supporting evidence under
`evidence/private/institutional_manuscript_approval/` are ignored by Git.

Run the public template check with:

```text
python scripts/verify_cas_q3_institutional_manuscript_approval_record.py --check-template
```

After an actual approval record has been retained, populate the ignored local
record and run:

```text
python scripts/verify_cas_q3_institutional_manuscript_approval_record.py
```

The real-input preflight requires an institution-issued or authenticated
record, its recomputed SHA-256, the approving office, the approval date, an
`APPROVED` decision, and the exact approved manuscript file and SHA-256. It
rejects a pending decision, a different target journal, a substituted
manuscript hash, evidence outside the private evidence directory, and symbolic
links.

Even a structural pass does not certify the record's authority or meaning and
does not close P0-I. Client content review, consistency checks against the owner
record and generated submission package, and the final GPT-6 Astra xhigh audit
remain required. No approval evidence has been received, and submission is not
authorized.
