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
- P0-G has an owner-selected Apache-2.0 project-code license and a corrected,
  deterministic, independently validated aggregate V2 candidate. It remains
  open for institutional release approval, independent legal-holder/year confirmation, final release
  authorization, operational reviewer access if requested, a frozen final
  versioned-code link and immutable archive DOI or identifier. The public
  GitHub location exists. Springer Nature policy permits reasonable
  third-party licence restrictions and lets editors/reviewers request
  non-public data or code, but it does not pre-approve a particular delivery
  channel or authorize release. The upstream-terms
  recheck preserves the Qwen research-license and non-`-c` DeBERTa
  training-data caveats; owner/institutional review for the intended release
  remains open.
- P0-H records Applied Intelligence, the subscription/non-OA route and the
  owner's 2025 major-category Q3 assertion. Its declared evidence path is absent
  from both project workspaces. P0-H remains open for institutional confirmation
  of the CAS edition/category/title/ISSN/date rule and a retained record for the
  current title and ISSNs.
- P0-I has a deterministic private complete-source transport using the
  authenticated current Springer Nature class/style; both independent builds
  clean-compile to the exact visually accepted 12-page PDF. It remains open for
  six remaining declaration/approval fields, an author-populated final package and the final
  GPT-6 Astra xhigh audit. The official publisher and journal guidance now
  establish the current `sn-jnl` package as an accepted submission route. Exact
  style equivalence to the unavailable legacy `smallcondensed` profile remains
  unproved and disclosed, but is no longer treated as a separate route blocker.
  The fail-closed private target builder has completed a 13-page synthetic
  end-to-end test, so no additional manual source-splicing step is required
  after the remaining real inputs pass. This synthetic result is not a real
  author package or an authorization.
  A 2026-09-15 recheck of Springer Nature's updated AI policy rejects the old
  short disclosure candidate as incomplete for this project's actual use. The
  revised, still-unapproved candidate covers methodological-option review,
  code work, statistical/numerical checking, interpretation stress-testing,
  drafting and prompt categories. The private builder now places it in a
  Study-design Methods subsection. A new 13-page synthetic-identity build
  passed compilation, font checks and complete visual review, but neither that
  build nor the policy mapping supplies author approval, a final use date or a
  real target artifact.
  A later data/code policy refresh rebuilt the 11-page manuscript, 3-page
  supplement, 12-page target preflight, two deterministic private transports
  and one 13-page synthetic author package. The base verifier now passes 141
  static checks; every one of the 14 base pages, 12 target pages and 13
  synthetic pages passed project-lead visual inspection. The current transport
  SHA-256 is
  `d55ffb74cb8f88a9ec261c9a414219f511d92bd10eb4d888f5dbaa185d1c681e`;
  the former `f4279c...` transport remains a preserved historical build. This
  refresh changes no scientific result and supplies no owner or institutional
  approval, real author package, release authorization or permanent archive.
  A fixed-cutoff private prompt ledger now retains 47 root-user prompt chunks
  after excluding subagents and automatically injected context. The tracked
  receipt exposes only counts and hashes. The ledger is Git-ignored,
  identity-minimized rather than anonymous, and neither author-reviewed nor
  approved for editor access. It improves traceability but does not complete
  the final prompt/use range or close P0-I.
- P1-A through P1-E are closed. P2 remains frozen under the Qwen-only route.

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
