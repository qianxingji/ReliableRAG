# Current task: close the Qwen empirical paper for CAS Q3 review

**CAS Q3 STATUS: NOT READY.**

The user's 2026-09-13 steering is to continue this work as a **conditional CAS
Q3 empirical study**. This authorizes target-neutral editorial and packaging
work within the accepted Qwen evidence. It does not reopen reader/method
experiments, relax authenticity or fairness, or imply that a CAS Q3 journal has
already been certified.

The machine-readable
[submission-readiness gate](SUBMISSION_READINESS_GATE.md) independently verifies
the frozen scientific boundary and repository hashes, then fails closed while
P0-G, P0-H and P0-I remain open. Its current decision is
`FAIL_CLOSED_CAS_Q3_NOT_READY_EXTERNAL_OWNER_INSTITUTION_AUTHOR_GATES`; it reads
no scientific payload, performs no fit and executes no model forward.

The remaining owner, institution and author fields are now consolidated in the
[private owner-input intake](OWNER_INPUTS_INTAKE.md). The tracked JSON template
contains no identities; its `.local.json` copy is ignored by Git, and the
verifier never echoes supplied values. Completing that file is an input-stage
advance only: CAS authority, journal policy, license/release implementation,
target artifacts and the final Astra xhigh audit still require independent
evidence.

The ignored local closure workspace is now operational. The preparer preserved
the existing owner-input bytes, created empty institutional CAS and release
placeholders from the tracked templates, and created their private-evidence
directories. A separate institutional manuscript-approval template and
fail-closed verifier now bind eventual approval evidence to the exact approved
manuscript bytes; its local placeholder and evidence directory are also ignored
by Git. The unified verifier now checks all four records together, including
approval status, target journal and exact approved-manuscript digest. It still
fails closed: owner inputs have 6 missing fields and zero errors, the CAS
placeholder has 22 missing fields and zero errors, the release placeholder has
22 missing fields plus five expected conflicts, and the manuscript-approval
placeholder has 17 missing fields plus two expected conflicts. No institutional
evidence or manuscript bytes were read, and placeholders are not received
institutional records.

Latest route decision: the independent GPT-6 Astra xhigh
[target-transition audit](TARGET_TRANSITION_ASTRA_XHIGH_AUDIT.md) sets the unique
recommendation
**`PROCEED_Q3_QWEN_ONLY_EVIDENCE_AND_JOURNAL_FIT_GATE_NO_NEW_EXPERIMENTS`**.
The existing Qwen study is sufficient to serve as the possible scientific core;
it is not yet a complete submission package or an acceptance guarantee.

## Authority and preserved state

The user formally changed the hard target to CAS Journal Ranking Q3 on
2026-09-13. Read [PROJECT_CHARTER.md](PROJECT_CHARTER.md),
[TARGET_TRANSITION.md](TARGET_TRANSITION.md), [CURRENT_METHOD.md](CURRENT_METHOD.md)
and [EVIDENCE_INDEX.json](EVIDENCE_INDEX.json). The complete `../cas_q2` tree is
historical evidence and must remain intact.

Keep the original dirty workspace at `E:/paper/ReliableRAG`, all sealed outputs,
failures and seeds. Continue project work in
`E:/paper/ReliableRAG-cas-q2-p0-1`, branch `work/cas-q2-p0-1`, draft PR #1. The
worktree/branch names are historical. Do not restart Phi, Mistral, RECA or a new
method/reader/seed/budget search.

The user's model routing remains binding: Sol High for routine engineering and
ordinary analysis; GPT-6 Astra xhigh for major method/claim decisions and final
fairness, reviewer and Submission Ready audits.

## Accepted scientific core

- Original saved-parameter numerical replay and source audit are accepted within
  the provenance limits in `../cas_q2/P0_1_CLIENT_ACCEPTANCE.md`. Seven original
  per-estimator fit-time ID/matrix receipts and an independent original-fit
  witness remain missing. A preserved pre-ROA-named archive now supplies a
  byte-identical copy of the complete historical `mars_full` manifest, but no
  external record independently certifies that archive's timestamp; see
  `P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.md`.
  A later [bounded receipt census](P0_E_ORIGINAL_FIT_RECEIPT_CENSUS.md) scanned
  55,373 files, 1,770 metadata candidates and 37 ZIPs. It found only the seven
  original model hashes and their seven static-delivery copies, with no third
  independent copy or original fit-time ID/matrix receipt.
- All three supervised controls and five fixed empirical policies are complete.
  The actual takeover fit count is 185.
- The 6,000-question Qwen study, 18,000 retrieval traces, generation/replay,
  scoring, fixed actions, selected-reference mapping, 20,000-draw analysis and
  independent validators are complete and accepted through
  `../cas_q2/EMPIRICAL_D_ACCEPTANCE.md`.
- HGB_GBV_R jointly beats GBV_ONLY_R on EM/Damage, does not jointly beat
  HGB_ONLY_R, and ROA-FULL does not advance over HGB_GBV_R. No novel candidate is
  cleared; see `../cas_q2/P0_3_FRESH_RESULT_DECISION.md`.
- Shared-inference cost accounting is accepted with explicit missing latency and
  peak-memory measurements in `../cas_q2/EMPIRICAL_COST_ACCEPTANCE.md`.
- Phi V4 runtime/replay evidence is authentic within its stated scope, but its
  semantic validation gate failed terminally. Mistral was selected and then
  stopped before engineering. Neither supplies scientific effect evidence.

## P0: required before credible Q3 submission

1. **P0-A -- CLOSED:** The
   [direct-neighbor audit](P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md) rejects a
   method-novelty Claim and now states the full gain-prediction overlap and exact
   comparison-dependent empirical boundary.
2. **P0-B -- CLOSED:** The
   [complete result/Claim map](P0_B_RESULT_CLAIM_MAP.md) binds all nine policies,
   the original six-endpoint family, fixed-action sensitivity, secondary-table
   rules and negative findings to the accepted Qwen evidence. Both gates are
   closed by the [independent Astra xhigh recheck](P0_A_P0_B_ASTRA_XHIGH_RECHECK.md).
3. **P0-C -- CLOSED:** The
   [method/fairness account](P0_C_METHOD_FAIRNESS_ACCOUNT.md) fixes the exact
   model, candidate/pool/retrieval roles, development/test identities, five
   heads, seven upstream estimators, eligibility, missing values, K=900, ties
   and Gold order.
4. **P0-D -- CLOSED:** The
   [statistical statement verification](P0_D_STATISTICAL_STATEMENT_VERIFICATION.md)
   binds every unit, interval role, multiplicity rule, joint gate and grouped
   top-K bootstrap description to the accepted aggregate analysis and its prior
   independent full-draw validation.
5. **P0-E -- CLOSED:** The
   [frozen disclosure boundary](P0_E_PROVENANCE_CONTAMINATION_ADAPTATION_FAILURE_DISCLOSURES.md)
   records data/cohort provenance, exact contamination limits, GbV adaptation,
   missing original fit evidence and the Phi/Mistral terminal exclusions. Its
   [manifest-recovery addendum](P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.md)
   records the byte-identical packaged copy and the unresolved independent-time
   boundary without changing the P0-E decision. The final
   [Astra xhigh authenticity audit](P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY_ASTRA_XHIGH_AUDIT.md)
   accepts that bounded byte claim and retains every timestamp/original-fit gap.
   The subsequent [accessible-root census](P0_E_ORIGINAL_FIT_RECEIPT_CENSUS.md)
   performs a model-hash, bounded metadata and ZIP-member search over four
   historical roots. Its zero-candidate result strengthens the search record but
   cannot prove absence outside those roots or replace the missing receipts.
6. **P0-F -- CLOSED WITH MEASUREMENT LIMITS:** The
   [claim-scoped cost table](P0_F_CLAIM_SCOPED_COST_TABLE.md) reports the shared
   workload, non-additive timers and saved C4 peaks while retaining every missing
   standalone, canonical peak, end-to-end and FLOP measurement.
7. **P0-G -- PARTIAL PASS / OPEN:** The
   [release audit](P0_G_REVIEWER_RELEASE_LICENSE_ANONYMIZATION_AUDIT.md) now
   freezes a nine-member anonymous aggregate allowlist. Two deterministic builds
   share one archive hash; the independent validator passes 100 checks and the
   extracted verifier passes 129 checks. The candidate remains withheld. The
   owner has selected Apache License 2.0 for project-authored code, and the exact
   license text is now present at repository top level. Legal holder/year,
   institutional NOTICE/review requirements, third-party release review, final
   authorization and persistent archiving of the validated corrected candidate,
   and a journal-accepted private-review route remain open. The historical
   [current license decision packet](P0_G_PROJECT_LICENSE_DECISION_PACKET.md)
   records the implemented Apache choice and remaining holder/year/review
   fields. These facts have a private machine-validated
   intake path shared with P0-H/I.
   The [Applied Intelligence data/code policy audit](P0_G_APPLIED_INTELLIGENCE_DATA_CODE_POLICY_AUDIT.md)
   now governs the selected target. The earlier
   [provisional Discover data/code policy audit](P0_G_DISCOVER_DATA_CODE_POLICY_AUDIT.md)
   now fixes that candidate's official statement, code-testing and persistent-
   archive requirements. It confirms that the aggregate ZIP alone is
   insufficient for final code availability; license-bearing latest and
   immutable archive links plus a permitted review channel remain required.
   The [third-party terms recheck](P0_G_THIRD_PARTY_TERMS_RECHECK.md) also
   corrects the release-source description of the non-`-c` DeBERTa checkpoint:
   its model card labels the foundation model MIT but retains a mixed,
   partly non-commercial training-data warning. The historical aggregate ZIP
   remains an immutable withheld arithmetic witness.
   A corrected Apache-2.0-aware V2 candidate has now been built twice, matched
   byte-for-byte, independently validated, and remains distribution-withheld.
   The [license-state corrigendum](P0_G_LICENSE_STATE_CORRIGENDUM.md) preserves
   the historically accurate pre-license audit while binding the current root
   license and `LICENSE_SCOPE.md`. Its 26-check verifier rejects a return to the
   stale “owner decision required” state and keeps the legal holder, year,
   institutional review, Qwen research-license and non-`-c` DeBERTa gates open.
   A fail-closed [private institutional release-record intake](P0_G_INSTITUTIONAL_RELEASE_RECORD_INTAKE.md)
   now binds any future owner/institution decision to the exact corrected V2
   archive hash. It checks retained evidence bytes, holder/year, release-review
   and NOTICE consistency, the no-weight/no-benchmark-payload boundary, and the
   Qwen/DeBERTa scope decisions without committing private evidence. Its
   structural pass still requires a separate client content audit, explicit
   owner authorization, a persistent identifier and the journal-approved
   restricted-review route; no release record has yet been received.
8. **P0-H -- OWNER TARGET SELECTED / INSTITUTIONAL CAS RECORD PENDING:** The
   [Applied Intelligence target selection](P0_H_APPLIED_INTELLIGENCE_TARGET_SELECTION.md)
   records the owner's target, Hubei University of Technology major-category
   CAS rule, current title/ISSNs, hybrid subscription route and current official
   submission requirements. The fit is plausible but carries high originality
   risk because the study has no new selector architecture, does not pass
   against HGB-only and has one accepted reader. The institution-recognized CAS
   edition/year and retained current-title/ISSN Tier-3 record are still missing.
   The earlier [target-journal audit](P0_H_TARGET_JOURNAL_FIT_AUDIT.md) ranks Discover
   Computing first for empirical editorial fit and Journal of Intelligent
   Information Systems first for stable subject identity. The
   [submission-requirements matrix](P0_H_SUBMISSION_REQUIREMENTS_MATRIX.md)
   freezes each candidate's current article, length, file, review, declaration
   and data-policy constraints. No journal is certified until the applicable CAS
   year/category and institutional title/ISSN rule are supplied. The refreshed
   [owner/institution qualification packet](P0_H_TARGET_JOURNAL_DECISION_PACKET.md)
   now records the fixed Applied Intelligence selection, current publisher-side
   state and exact fields needed to authenticate the institution-recognized CAS
   result. Earlier four-journal comparisons remain historical. The consolidated
   local intake checks field completeness but cannot authenticate the
   institutional record.
   A later [official HBUT policy verification](P0_H_HBUT_CAS_POLICY_ACCEPTANCE.md)
   confirms that the university publicly uses the upgraded CAS basis for SCI
   and SSCI recognition, requires HBUT as first affiliation for reported papers,
   and assigns natural-science paper recognition review to a named office. The
   applicable edition/year and a retained Applied Intelligence current-title,
   ISSN and Computer Science major-category Q3-or-above record remain missing,
   so P0-H is still open.
   A concrete [HBUT institutional verification request](P0_GH_HBUT_INSTITUTIONAL_VERIFICATION_REQUEST_ZH.md)
   is ready for the responsible author to submit. It asks for the CAS edition,
   current title/ISSNs, major-category tier, recognition-date and title-change
   rules together with manuscript approval, code copyright/release and Qwen/
   DeBERTa review. It records `request_sent=false` and cannot substitute for the
   retained institutional response.
   A later [official HBUT college-level secondary-evidence audit](P0_H_HBUT_CAS_EDITION_RULE_SECONDARY_EVIDENCE.md)
   finds a published School of Science rule using the upgraded CAS report from
   the year before publication. It makes 2025 the candidate report year for a
   2026 publication, but does not establish that this college programme rule
   applies university-wide or that Applied Intelligence is Q3; the central
   confirmation remains required. The authoritative CAS partition platform
   publicly lists the 2025 upgraded data as available and supports title/ISSN
   search, but detailed records require institutional or authenticated access;
   no Applied Intelligence record was retrieved or inferred.
   A [public corroboration audit](P0_H_APPLIED_INTELLIGENCE_2025_PUBLIC_CORROBORATION.md)
   separately records that two public detail sources label the 2025 upgraded
   edition Computer Science major category Q3 and Artificial Intelligence minor
   category Q4. An official other-university faculty-page search excerpt also
   labels a 2025 Applied Intelligence item major-category Q3, but direct fetch
   returned HTTP 412 and the edition was not authenticated. A separate university
   library navigation page exposes an unlabeled Q4 value, so the category ambiguity
   is retained. This supports the target's plausibility under the owner's major-
   category rule but does not replace the HBUT-recognized record or close P0-H.
   The responsible author later asserted the 2025 upgraded edition and Computer
   Science major-category Q3 result. The accompanying
   [declared-path check](P0_H_OWNER_2025_CAS_ASSERTION_PATH_CHECK.md) found that
   `compliance/cas_partition/2025/` exists in neither the isolated worktree nor
   the preserved original workspace. The assertion is retained as owner input,
   but no HBUT-issued record or evidence bytes were received and P0-H remains
   open.
   A fail-closed [private institutional-record intake](P0_H_INSTITUTIONAL_CAS_RECORD_INTAKE.md)
   now fixes the future record bytes by SHA-256 and checks the edition, current
   title, both ISSNs, major category, Q1/Q2/Q3 target tier, recognition-date and
   title-change fields without committing the record or local metadata. It
   cannot certify its own transcription: a separate client visual/content audit
   remains mandatory, and no institutional record has yet been received.
   The [Discover Computing APC audit](P0_H_DISCOVER_COMPUTING_APC_AUDIT.md)
   closes the current-price lookup: the official page lists GBP 1,040, USD
   1,520, or EUR 1,140 plus applicable taxes and applies the acceptance-date
   price. It is now historical rather than the active route. Applied
   Intelligence's official page states that its selected subscription route has
   no APC.
9. **P0-I -- SOURCE AND COMPILED DRAFT ACCEPTED / EXTERNAL INPUTS OPEN:** The
   [manuscript preflight](P0_I_MANUSCRIPT_PREFLIGHT.md) freezes journal render
   profiles, the evidence-to-section map, table/figure sources, forbidden Claims,
   author inputs and final audit gates. The user's direct “继续” reply after the
   authorization blocker is recorded in the
   [authorization record](P0_I_MANUSCRIPT_AUTHORIZATION.md). The main manuscript,
   supplement, bibliography, generated tables/figures, title-page template and
   cover-letter template now exist under `paper/`; the independent static
   verifier now passes 139 checks. MiKTeX produced an 11-page main PDF and 3-page
   supplement; mechanical log checks and project-lead review of all pages pass.
   The subsequent [font-embedding corrigendum](P0_I_FONT_EMBEDDING_CORRIGENDUM.md)
   replaces the unembedded Base-14 figure fonts and isolated Type 3 marker; both
   PDFs now have zero nonembedded and zero Type 3 fonts. The supplement retains
   its disclosed nonfatal `longtable` notice; the
   [upstream triage](P0_I_LONGTABLE_NOTICE_TRIAGE.md) binds it to the installed
   2025-10-13 v4.24 package and requires a final target-environment recheck.
   See the [build status](P0_I_MANUSCRIPT_BUILD_STATUS.md) and
   [compiled-artifact acceptance](P0_I_COMPILED_ARTIFACT_ACCEPTANCE.md). The
   Astra xhigh source-level fairness, Claim and simulated-reviewer audit and its
   [compiled-artifact rebind](P0_I_ASTRA_XHIGH_COMPILED_REBIND.md) passed within
   blockers. The subsequent build-path repair was independently reaffirmed in
   the [engineering addendum](P0_I_ASTRA_XHIGH_COMPILED_REBIND_ADDENDUM.md),
   including 14/14 pixel-identical rebuilt pages for that historical artifact.
   The font-clean rebuild changes only main pages 4 and 7 and passed fresh
   project-lead review; it awaits the final Astra xhigh rebind after journal
   conversion. Final Submission Ready remains blocked by incomplete author and
   release inputs and the certified CAS Q3 journal record. The
   [author/declaration intake](P0_I_AUTHOR_DECLARATION_INTAKE.md) now reduces the
   remaining author surface to explicit identity, CRediT, funding, interests,
   ethics, acknowledgements if applicable, AI-assistance, originality and
   approval fields;
   none is guessed. Its 19-check verifier also compiles the placeholder title
   page successfully as a 2-page PDF, closing the template-syntax gate while
   retaining every factual field as pending. The consolidated intake adds a
   privacy-preserving local JSON route for those facts without committing them.
   The owner has now supplied the formal author name, first affiliation and
   department, active corresponding-author email, target journal,
   publication route, project-license choice and CAS category rule. The
   [official HBUT address verification](P0_I_HBUT_AFFILIATION_ADDRESS_ACCEPTANCE.md)
   independently supplies Wuhan and postcode 430068. The department and
   personal contact fields were later supplied directly by the owner and remain
   only in the Git-ignored input. An official Applied Intelligence
   requirement audit has corrected the hard gate from the historical 30-field
   snapshot to a 19-field intermediate snapshot; the first direct owner update
   reduced it to 16, the second response reduced it to 9, and the third response
   plus fail-closed content review leaves 6 real missing fields and zero
   validation errors. The latest accepted facts include all-author approval and
   the requirement for institutional manuscript and release review. Those
   reviews remain pending rather than approved.
   Optional ORCID, a separate corresponding-author postal address and acknowledgements
   are no longer treated as mandatory, while truthful CRediT coverage remains
   required. Correspondence and CRediT are complete. The individual
   copyright-holder and candidate 2025 CAS-edition entries remain owner
   assertions; institutional review outcomes and CAS authority are not inferred.
   A [unified private external-closure preflight](P0_GHI_EXTERNAL_CLOSURE_PREFLIGHT.md)
   now runs the owner, institutional-CAS and institutional-release validators in
   one command and checks their title, ISSN, edition, tier, recognition-rule,
   license, holder/year and review-state agreement. Its current local result is
   fail-closed: 6 owner fields remain missing and the two institutional input
   files are empty template placeholders. Even a future structural pass leaves
   the client content, author-artifact and final Astra xhigh audits open.
   A separate local builder can then produce an ignored title page,
   declarations source and cover-letter draft. It refuses incomplete inputs,
   does not overwrite a prior directory and emits only a redacted build receipt;
   generated drafts remain unverified and submission-unauthorized.
   The journal-neutral abstract is now 155 words and has five keywords, meeting
   Applied Intelligence's inspected count requirements without changing the
   Claim boundary. The rebuilt 11+3 pages passed separate mechanical,
   font and complete project-lead visual review; the mechanical verifier no
   longer self-asserts a human inspection.
   A separate reproducible PDF-length proxy records 3,994 tokens before
   References and 4,691 overall. Applied Intelligence's inspected guidelines
   specify no general full-manuscript word limit; these are reproducible proxy
   counts rather than publisher counts.
   The [Applied Intelligence abstract and keyword acceptance](P0_I_APPLIED_INTELLIGENCE_ABSTRACT_KEYWORD_ACCEPTANCE.md)
   binds that edit, both current PDFs and the complete 14-page visual review
   while retaining the target-template and final Astra gates.
   The subsequent [modern-template preflight](P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_ACCEPTANCE.md)
   authenticates the December 2024 official Springer Nature package and builds
   a clean 12-page `sn-jnl`/numeric-citation PDF plus a flat eight-member
   authored-source ZIP. All 12 pages pass project-lead visual review. This
   remains a partial pass because the journal page's `smallcondensed` request
   has not been proved equivalent to the modern package.
   The later [complete-source transport acceptance](P0_I_APPLIED_INTELLIGENCE_TEMPLATE_TRANSPORT_ACCEPTANCE.md)
   establishes that the current Springer Nature authoring template is an
   officially supported working route and packages the exact authenticated
   class/style with the eight authored files. Two private external builds are
   byte-identical; each passes 56 independent checks and clean compilation, and
   the resulting PDF is byte-identical to the visually accepted 12-page
   preflight. The journal page's legacy `smallcondensed` link returns 404 and
   the current package contains no such profile, so journal-specific
   equivalence remains open. The private transport is anonymous and neither
   submission- nor distribution-authorized.
   The later [official template-route resolution](P0_I_APPLIED_INTELLIGENCE_TEMPLATE_ROUTE_RESOLUTION.md)
   closes the narrower pre-submission route question: Applied Intelligence
   itself encourages the current Springer Nature template, and publisher
   support states that template may be used for any Springer Nature journal.
   The unavailable legacy `smallcondensed` profile is still not claimed to be
   style-equivalent. No Editorial Manager compile or author-populated upload is
   inferred.
   The subsequent [private target-builder acceptance](P0_I_APPLIED_INTELLIGENCE_PRIVATE_SUBMISSION_BUILDER_ACCEPTANCE.md)
   implements the remaining mechanical path from a complete owner-input file
   to an author-populated flat source ZIP, compiled PDF and cover letter. A
   synthetic complete fixture passed the full build and all 13 rendered pages
   passed visual inspection. At that historical synthetic-builder snapshot the
   actual local input remained fail-closed at 30 missing fields; the underlying
   historical receipt is intentionally unchanged. The later
   [official-requirement correction](P0_I_REQUIRED_OWNER_FIELDS_CORRECTION.md)
   reduced the then-current hard gate to 19 real missing fields. The subsequent
   first direct owner update resolved three of those paths and synchronized the
   author-list name. A second response supplied CRediT and several declarations.
   The third confirms all-author approval and required institutional review and
   supplies owner-side holder and 2025-edition assertions. AI wording approval,
   a date-bounded AI-tool record, substantive competing-interests wording, and
   actual institutional approvals/evidence remain open; 6 fields are still
   missing, so no real identity-bearing target package has been generated.
   The current 6 missing paths are rendered into a
   [privacy-safe responsible-author one-reply packet](P0_I_RESPONSIBLE_AUTHOR_ONE_REPLY_PACKET_ZH.md).
   Its generator and regression test prove that already supplied local names,
   email addresses, postal details and declaration text are not serialized into
   the tracked packet or receipt. It now exposes the exact static AI-assistance
   candidate, a truthful no-conflict option, a date-range format and the ignored
   institutional manuscript/release evidence directories so the six open items
   can be reviewed without guessing. The packet only reduces coordination friction;
   it does not complete any declaration or authorize submission.
   The [current private build-gate verification](P0_I_CURRENT_PRIVATE_BUILD_GATE.md)
   also exercises the real Git-ignored owner input. It confirms that the file is
   no longer the empty template while proving that its 6-field failure occurs
   before transport access or output creation. No identity-bearing target
   artifact was created.
   A provisional Discover Computing technical profile now also proves that the
   accepted source can be changed to 12 pt, flattened into a top-level LaTeX
   ZIP and compiled to a font-clean 12-page PDF without changing scientific
   prose or numbers. It is explicitly not a selected-journal or submission
   artifact; author, funding, APC, license, institutional CAS and final Astra
   gates remain open.
   The data-and-code statement now explicitly records the validated corrected
   candidate while retaining the missing persistent identifier, restricted
   private-review route and aggregate-versus-neural reproduction boundary. The
   rebuilt neutral and Applied Intelligence modern-preflight artifacts passed
   mechanical and complete visual review.
   The later historical-manifest disclosure rebuild also passed: the paper now
   records the byte-identical packaged manifest copy while retaining the lack
   of independent timestamp certification and all missing original-fit evidence.

## P1: material competitiveness improvements

- **P1-A -- CLOSED:** The
  [reviewer evidence map](REVIEWER_EVIDENCE_MAP.md) gives one ordered path
  through the compiled paper, anonymous aggregate package, private forensic
  scopes and preserved Phi/Mistral/ROA failures. Its independent verifier
  authenticates 141 repository records plus preserved withheld archive
  generations, the private target transport and the synthetic author-populated
  package in 982 checks, without
  scientific payload reads, fits or model forwards.
- **P1-B -- CLOSED:** The
  [reviewer cost and failure register](REVIEWER_COST_FAILURE_REGISTER.md)
  consolidates executed workload, non-additive timers and peaks, every missing
  deployment measurement, the distinction between 5% actions and full
  candidate-acquisition cost, primary negative results, stopped reader routes
  and material fail-closed engineering corrections.
- **P1-C -- CLOSED:** The manuscript, supplement and reviewer register retain
  ROA/HGB-only non-passes, the terminal Phi validation failure and the Mistral
  pre-engineering stop with explicit separation between technical status and
  scientific effect evidence.
- **P1-D -- CLOSED:** Frozen dataset and retriever breakdowns are present only
  in the supplement, use their 6,000-trace cell denominators, and are explicitly
  descriptive with no subgroup superiority Claim.
- **P1-E -- CLOSED IN PUBLIC-REPORTING SCOPE:** The
  [public CI acceptance](P1_E_PUBLIC_REPORTING_CI.md) records the preserved first
  failure, the corrected 49-check committed-surface verifier and the 38-check
  committed Applied Intelligence modern-preflight verifier. GitHub push and
  pull-request runs pass through the current owner-gate correction, portable
  LaTeX-lookup repair, official-template route and authoritative CAS-platform
  boundary; the latest retained successful head is `bc88219`. The exposed
  Ubuntu `LOCALAPPDATA` failure and its successful repair are retained in the
  CI acceptance record. Private aggregate/statistical,
  historical-manifest and end-to-end neural reproduction remain explicitly
  outside this CI.

## P2: optional and currently closed

- Any new reader, method, feature, head, seed, budget curve or benchmark.
- New neural replay or experiments intended to improve significance.
- Cosmetic expansion before the P0 evidence/claim/journal gates close.

Primary rejection risks are a narrow empirical contribution, no new algorithm,
failure against HGB_ONLY_R, single accepted reader condition, incomplete original
fit provenance, incomplete standalone deployment cost and high Applied
Intelligence originality/desk risk.
