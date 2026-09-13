# CAS Q3 submission-readiness gate

**CAS Q3 STATUS: NOT READY.**

`scripts/verify_cas_q3_submission_readiness.py` is the fail-closed top-level
gate for the active CAS Q3 route. It reads only public audit metadata, verifies
the repository files pinned by the evidence index, preserves the frozen
positive and negative conclusions, and exits with code 2 while any P0 gate is
open. It does not read scientific payloads, fit a model or perform a model
forward.

The current machine decision is
`FAIL_CLOSED_CAS_Q3_NOT_READY_EXTERNAL_OWNER_INSTITUTION_AUTHOR_GATES`:

- P0-A through P0-F are closed within their stated limits.
- P0-G remains open for the owner license, legal holder/year, institutional
  release requirement, final selected-journal release policy, reviewer access,
  license-bearing latest and persistent archived code links, and a newly
  validated licensed archive. The provisional Discover policy mapping is
  complete but does not implement these release gates.
- P0-H remains open for the institution-recognized CAS edition/category/title/
  ISSN/date rule, final target journal and owner-confirmed publication-charge
  route. The current Discover Computing price/date-rule lookup is complete;
  payer, institutional coverage or a waiver remains unconfirmed.
- P0-I remains open for real author/declaration facts, target-specific source
  and PDF conversion, and the final GPT-6 Astra xhigh audit.
- P1-A through P1-D are closed. P2 remains frozen under the Qwen-only route.

The [consolidated owner-input intake](OWNER_INPUTS_INTAKE.md) provides one
ignored local JSON file for the P0-G/H/I facts. Its verifier emits field paths
and counts only; it never prints supplied personal values. A complete intake is
still self-attested and therefore advances only to independent CAS-authority,
journal-policy, license/release and artifact verification. It cannot set
`submission_ready=true`.

## Promotion rule

Do not edit the current failure receipt to create a pass. After the responsible
owner supplies P0-G/H/I facts, create versioned decision records and target
artifacts, independently verify them, add their paths and hashes to the evidence
index, and extend this verifier with exact positive predicates. Only a fresh
run that proves every P0 item may emit `submission_ready=true`. The final gate
must also require an artifact-bound GPT-6 Astra xhigh fairness, Claim,
simulated-reviewer and Submission Ready decision.

The historical worktree and branch names containing `cas-q2` do not set the
active target. They remain unchanged to preserve provenance.
