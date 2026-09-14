# Reviewer evidence map and reproduction entry points

Decision: **PASS_REVIEWER_EVIDENCE_MAP_WITH_EXTERNAL_RELEASE_GATES.**

**CAS Q3 STATUS: NOT READY.** This map gives a reviewer one ordered path through
the manuscript, aggregate verification, private reproducibility evidence and
preserved failures. It does not authorize distribution of the aggregate ZIP or
replace the missing release review, author declarations, Applied Intelligence
package and institutional CAS Q3 qualification.

## Scientific statement under review

The paper is a bounded single-reader empirical comparison. Under fixed Qwen
candidate pairs, matched development supervision, common eligibility and a
global 900-of-18,000 action allocation, `HGB_GBV_R` jointly improves EM and
Damage relative to `GBV_ONLY_R`. The joint rule does not pass against
`HGB_ONLY_R`, and `ROA-FULL` does not establish advancement. The work does not
claim a new selector algorithm, reader-general transfer, a safety guarantee or
a deployment-cost reduction.

## Six evidence lanes

| Lane | Reviewer entry point | What it proves | What it does not prove |
|---|---|---|---|
| 1. Paper artifact | `output/pdf/manuscript.pdf`, `output/pdf/supplement.pdf`, `paper/COMPILE_RECEIPT.json`, `P0_I_LICENSED_RELEASE_V2_DISCLOSURE_REBUILD_ACCEPTANCE.md`, `P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT_ACCEPTANCE.md`, `P0_I_MANUSCRIPT_LENGTH_VERIFICATION.json` | The 11-page manuscript and 3-page supplement compile, resolve citations, contain the frozen tables, expose the negative results and limitations, and have zero nonembedded or Type 3 fonts. The 155-word abstract and five keywords meet Applied Intelligence's inspected count rules. A reproducible PDF-text proxy counts 3,994 tokens before References and 4,691 in the full document. The selected-target modern `sn-jnl` preflight compiles to 12 font-clean pages with numeric citations and flat authored sources. | A publisher word count, proof that modern `sn-jnl` equals the `smallcondensed` profile named on the journal page, final Astra artifact rebind, complete authorship, release authorization or CAS status. |
| 2. Anonymous aggregate check | Preserved V1 witness SHA-256 `b785890366995c2943007f5635e622814bc7961dc7b3ded4adee0707dfb7ca8d`; corrected Apache-aware V2 candidate SHA-256 `4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8` | The V1 archive preserves the historical arithmetic witness. The V2 archive adds the exact Apache-2.0 text, restricts that license to two project-authored scripts, uses the corrected third-party notice, rebuilds byte-identically twice, passes 125 package checks per build and passes the extracted 129-check reporting verifier. | Bootstrap recomputation, per-question inspection, model rerun, refit, legal approval or public redistribution. Neither archive has a DOI or distribution authorization. |
| 3. Private forensic reproduction | `P0_1_CLIENT_ACCEPTANCE.md`, `ROA_REPLAY_RELEASE_ACCEPTANCE.md`, `ROA_CLEAN_ENVIRONMENT_ACCEPTANCE.md`, `EMPIRICAL_C3_EXECUTION_ACCEPTANCE.md`, `EMPIRICAL_D_ACCEPTANCE.md` | Saved-parameter numerical replay, source/data relocation on the same Windows host, clean numerical-library replay, full Qwen acquisition/replay acceptance and final aggregate analysis acceptance within their recorded scopes. | Original training-event reconstruction, another-host/OS reproduction, full public end-to-end execution or elimination of contamination. |
| 4. Negative and stopped routes | `P0_3_FRESH_RESULT_DECISION.md`, `PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md`, `MISTRAL_EMPIRICAL_EXTENSION_PROTOCOL_GO_STOP_REVIEW.md` | The non-advancement of ROA, terminal Phi semantic validation failure and Mistral stop before engineering are retained rather than converted into positive evidence. | A second-reader effect, method novelty or permission to restart reader/method search. |
| 5. Historical manifest recovery | `P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.md`, its JSON/verifier receipts and Astra xhigh audit | One pre-ROA-named local package contains a complete `mars_full` manifest byte-identical to the current copy; the archive and member hashes are fixed and machine-checked. | An independently certified timestamp, original-fit authentication, any of the seven per-estimator ID/matrix receipts, or an independent original-fit witness. |
| 6. Public continuous audit | `.github/workflows/public-reporting-audit.yml`, `P1_E_PUBLIC_REPORTING_CI.md` | A GitHub-hosted Ubuntu runner verifies the 8 committed table/figure hashes, public Claim boundaries, citations, anonymity, compiled PDFs, length proxy, privacy tests and fail-closed submission state. Two accepted runs are linked in the P1-E record. | The ignored aggregate inputs, 129-check statistical verifier, aggregate rebuild, historical ZIP recovery, private forensic evidence, model execution, fit replay or end-to-end reproduction. |

The exact repository paths and SHA-256 values for every entry above are in
`REVIEWER_EVIDENCE_MAP.json`. The independent verifier authenticates that map
without reading benchmark questions, answers, per-question outcomes, model
weights or bootstrap draws.

The [reviewer cost and failure register](REVIEWER_COST_FAILURE_REGISTER.md)
consolidates the executed workload, every missing deployment measurement, the
three primary comparison outcomes, terminal reader routes and material
fail-closed engineering chronology.

The [Applied Intelligence target audit](P0_H_APPLIED_INTELLIGENCE_TARGET_SELECTION.md)
records the owner's selection, official current title/ISSNs, hybrid publication
route and no-mandatory-APC subscription choice. The
[data/code policy audit](P0_G_APPLIED_INTELLIGENCE_DATA_CODE_POLICY_AUDIT.md)
maps the mandatory Data Availability Statement and conditional-access boundary.
The Apache-2.0 license is present and a corrected candidate is independently
validated, while legal holder/year, institutional review, final release
authorization, persistent identifier and review-channel implementation remain open.

The [third-party terms recheck](P0_G_THIRD_PARTY_TERMS_RECHECK.md) records the
Qwen research-license boundary and the non-`-c` DeBERTa checkpoint's mixed
training-data-license warning. The corrected tracked notice is incorporated in the separately pinned V2
candidate. The V1 witness remains unchanged, and both archives remain
distribution-prohibited.

## Reviewer sequence

1. Read the abstract, Sections 3--7 and the complete nine-policy table in the
   main PDF. Confirm that the HGB-only and ROA non-passes remain visible.
2. Read the supplement for fixed-action sensitivity, dataset/retriever
   breakdowns, metric conventions, provenance, stopped reader routes and cost
   limits. The subgroup tables are descriptive.
3. In a repository checkout, run:

   ```text
   python scripts/verify_cas_q3_public_reporting_surface.py
   python scripts/verify_cas_q3_manuscript.py
   python scripts/verify_cas_q3_compiled_pdfs.py
   python scripts/audit_cas_q3_manuscript_length.py
   python scripts/build_cas_q3_discover_computing_preflight.py
   python scripts/verify_cas_q3_historical_manifest_archive_recovery.py
   python scripts/verify_cas_q3_reviewer_evidence_map.py
   ```

   Expected results are a 49-check public-surface PASS, a 38-check committed
   Applied Intelligence modern-preflight PASS and 139 private-input
   static manuscript checks, a compiled mechanical and font PASS, an explicitly
   non-publisher length proxy of 3,994 pre-reference and 4,691 full-document
   tokens, a non-submittable 12 pt Discover Computing technical-profile PASS,
   and a reviewer-map PASS. The latest complete visual review is
   separate from the mechanical verifier and is documented in
   `P0_I_LICENSED_RELEASE_V2_DISCLOSURE_REBUILD_ACCEPTANCE.md`. The older
   acceptance files remain historical records for their exact artifacts.
4. If the owner and journal later authorize the aggregate ZIP, verify it from
   an isolated extraction using:

   ```text
   python scripts/validate_cas_q3_licensed_release.py --archive <archive> --archive-sha256 4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8 --manifest-sha256 463b26e10ae8724da998033efbea219c26c16be522b52eaaa57cc400f039b4cf
   ```

   Expected output is 125 package checks. The acceptance record separately
   authenticates the fresh-extraction 129-check reporting-verifier PASS. Until
   authorization, use the locally preserved candidate only for internal validation.
5. Request private forensic materials only through a journal-approved channel.
   Their external pins and restoration boundaries are listed in the machine
   map. They are not part of the anonymous aggregate ZIP.

## Claim-to-evidence routing

| Paper statement | First authority | Required negative boundary |
|---|---|---|
| Study size, policies and action allocation | `EMPIRICAL_D_ACCEPTANCE.md`; sealed aggregates | 6,000 question groups are not 18,000 independent questions. |
| Fusion vs GbV-only joint result | `P0_D_STATISTICAL_STATEMENT_VERIFICATION.md`; `INTERVALS.json` | The same rule fails against HGB-only. |
| No ROA advancement | `P0_3_FRESH_RESULT_DECISION.md` | A favorable point estimate is not advancement. |
| Matched five-head comparison | `P0_C_METHOD_FAIRNESS_ACCOUNT.md` | Historical upstream estimators do not have matched total historical label budgets. |
| Workload description | `P0_F_CLAIM_SCOPED_COST_TABLE.md` | K=900 is an action budget, not 5% compute or latency. |
| Reproduction availability | `P0_G_REVIEWER_RELEASE_LICENSE_ANONYMIZATION_AUDIT.md` | Aggregate verification is not full neural reproduction. |

## Open P0 and lower priorities

- **P0:** legal copyright holder/year and institutional release review; complete
  author and declaration fields; institution-recognized CAS edition/year and a
  retained current Applied Intelligence title/ISSN Tier-3 record; target-specific
  source/PDF conversion; final release authorization and persistent identifier.
- **P1:** insert the certified journal's final data/code statement and bind the
  authorized archive plus journal-approved evidence-review route.
- **P2:** new readers, methods, seeds, budgets and benchmarks remain closed.

Primary rejection risks remain the narrow empirical contribution, no joint
advantage over HGB-only, a single accepted 3B reader, incomplete original-fit
provenance, conditional inference, absent standalone deployment timing and high
Applied Intelligence originality/desk risk.
