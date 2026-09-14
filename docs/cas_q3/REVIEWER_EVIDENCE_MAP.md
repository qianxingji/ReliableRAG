# Reviewer evidence map and reproduction entry points

Decision: **PASS_REVIEWER_EVIDENCE_MAP_WITH_EXTERNAL_RELEASE_GATES.**

**CAS Q3 STATUS: NOT READY.** This map gives a reviewer one ordered path through
the manuscript, aggregate verification, private reproducibility evidence and
preserved failures. It does not authorize distribution of the aggregate ZIP or
replace the missing project license, author declarations, target journal and
institutional CAS Q3 qualification.

## Scientific statement under review

The paper is a bounded single-reader empirical comparison. Under fixed Qwen
candidate pairs, matched development supervision, common eligibility and a
global 900-of-18,000 action allocation, `HGB_GBV_R` jointly improves EM and
Damage relative to `GBV_ONLY_R`. The joint rule does not pass against
`HGB_ONLY_R`, and `ROA-FULL` does not establish advancement. The work does not
claim a new selector algorithm, reader-general transfer, a safety guarantee or
a deployment-cost reduction.

## Five evidence lanes

| Lane | Reviewer entry point | What it proves | What it does not prove |
|---|---|---|---|
| 1. Paper artifact | `output/pdf/manuscript.pdf`, `output/pdf/supplement.pdf`, `paper/COMPILE_RECEIPT.json`, `P0_I_MANUSCRIPT_LENGTH_VERIFICATION.json`, `P0_I_DISCOVER_COMPUTING_PREFLIGHT.json` | The 11-page manuscript and 3-page supplement compile, resolve citations, contain the frozen tables, expose the negative results and limitations, and have zero nonembedded or Type 3 fonts. The 142-word abstract meets both inspected candidate ceilings. A reproducible PDF-text proxy counts 3,951 tokens before References and 4,649 in the full document. A provisional Discover Computing dry run also compiles a flat 12 pt source profile to 12 font-clean pages without scientific-content changes. The data/code statement exposes the missing license-bearing persistent archive and bounded review channel. | A publisher word count, final journal-specific formatting, final Astra artifact rebind, authorship, licensing or CAS status. The current draft is below JIS's published 5,000--7,500-word average, which is a fit risk rather than a stated hard-minimum failure. The provisional Discover profile does not apply the final Springer template or authorize submission. |
| 2. Anonymous aggregate check | Withheld archive `paired_rag_repair_aggregate_candidate.zip`; SHA-256 `b785890366995c2943007f5635e622814bc7961dc7b3ded4adee0707dfb7ca8d` | Nine-policy arithmetic, sealed aggregate hashes, primary directions and the frozen 20,000-draw reporting description; clean anonymous allowlist and round trip. | Bootstrap recomputation, per-question inspection, model rerun, refit or public redistribution. Its notice predates the DeBERTa training-data caveat correction, so this immutable ZIP is an arithmetic witness rather than a release-ready artifact. |
| 3. Private forensic reproduction | `P0_1_CLIENT_ACCEPTANCE.md`, `ROA_REPLAY_RELEASE_ACCEPTANCE.md`, `ROA_CLEAN_ENVIRONMENT_ACCEPTANCE.md`, `EMPIRICAL_C3_EXECUTION_ACCEPTANCE.md`, `EMPIRICAL_D_ACCEPTANCE.md` | Saved-parameter numerical replay, source/data relocation on the same Windows host, clean numerical-library replay, full Qwen acquisition/replay acceptance and final aggregate analysis acceptance within their recorded scopes. | Original training-event reconstruction, another-host/OS reproduction, full public end-to-end execution or elimination of contamination. |
| 4. Negative and stopped routes | `P0_3_FRESH_RESULT_DECISION.md`, `PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md`, `MISTRAL_EMPIRICAL_EXTENSION_PROTOCOL_GO_STOP_REVIEW.md` | The non-advancement of ROA, terminal Phi semantic validation failure and Mistral stop before engineering are retained rather than converted into positive evidence. | A second-reader effect, method novelty or permission to restart reader/method search. |
| 5. Historical manifest recovery | `P0_E_HISTORICAL_MANIFEST_ARCHIVE_RECOVERY.md`, its JSON/verifier receipts and Astra xhigh audit | One pre-ROA-named local package contains a complete `mars_full` manifest byte-identical to the current copy; the archive and member hashes are fixed and machine-checked. | An independently certified timestamp, original-fit authentication, any of the seven per-estimator ID/matrix receipts, or an independent original-fit witness. |

The exact repository paths and SHA-256 values for every entry above are in
`REVIEWER_EVIDENCE_MAP.json`. The independent verifier authenticates that map
without reading benchmark questions, answers, per-question outcomes, model
weights or bootstrap draws.

The [reviewer cost and failure register](REVIEWER_COST_FAILURE_REGISTER.md)
consolidates the executed workload, every missing deployment measurement, the
three primary comparison outcomes, terminal reader routes and material
fail-closed engineering chronology.

The [Discover Computing APC audit](P0_H_DISCOVER_COMPUTING_APC_AUDIT.md)
records the official 2026-09-14 current prices, acceptance-date price rule,
tax boundary and funding/waiver routes. It leaves payer acceptance,
institutional coverage and any waiver unconfirmed.

The [Discover data/code policy audit](P0_G_DISCOVER_DATA_CODE_POLICY_AUDIT.md)
shows that the validated aggregate ZIP supports reporting verification but does
not replace reviewer-testable project code, a latest-code link, or a persistent
archived version. The manuscript states this boundary; license, archive and
review-channel implementation remain open.

The [third-party terms recheck](P0_G_THIRD_PARTY_TERMS_RECHECK.md) records the
Qwen research-license boundary and the non-`-c` DeBERTa checkpoint's mixed
training-data-license warning. The corrected tracked notice is for the next
owner-authorized archive. The current pinned ZIP remains unchanged and
distribution-prohibited.

## Reviewer sequence

1. Read the abstract, Sections 3--7 and the complete nine-policy table in the
   main PDF. Confirm that the HGB-only and ROA non-passes remain visible.
2. Read the supplement for fixed-action sensitivity, dataset/retriever
   breakdowns, metric conventions, provenance, stopped reader routes and cost
   limits. The subgroup tables are descriptive.
3. In a repository checkout, run:

   ```text
   python scripts/verify_cas_q3_manuscript.py
   python scripts/verify_cas_q3_compiled_pdfs.py
   python scripts/audit_cas_q3_manuscript_length.py
   python scripts/build_cas_q3_discover_computing_preflight.py
   python scripts/verify_cas_q3_historical_manifest_archive_recovery.py
   python scripts/verify_cas_q3_reviewer_evidence_map.py
   ```

   Expected results are 135 static manuscript checks including a 150-word
   abstract ceiling, a compiled mechanical and font PASS, an explicitly
   non-publisher length proxy of 3,951 pre-reference and 4,649 full-document
   tokens, a non-submittable 12 pt Discover Computing technical-profile PASS,
   and a reviewer-map PASS. The latest complete visual review is
   separate from the mechanical verifier and is documented in
   `P0_I_ABSTRACT_COMPRESSION_ACCEPTANCE.md` and
   `P0_I_DISCOVER_COMPUTING_PREFLIGHT_ACCEPTANCE.md`. The later data/code
   statement rebuild is recorded in `P0_I_DATA_CODE_STATEMENT_ACCEPTANCE.md`.
4. If the owner and journal later authorize the aggregate ZIP, verify it from
   an isolated extraction using:

   ```text
   python scripts/validate_cas_q3_aggregate_release.py --archive <archive> --archive-sha256 b785890366995c2943007f5635e622814bc7961dc7b3ded4adee0707dfb7ca8d --manifest-sha256 6c8ca3a4d0a9d70ade6a09b7194337390ee74ab1f46c79d862e918418a341a1c
   ```

   Expected output is 100 package checks and an extracted 129-check reporting
   verifier PASS. Until authorization, use the locally preserved candidate only
   for internal validation.
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

- **P0:** owner-selected project license and release policy; real author and
  declaration fields; certified journal title/ISSN and applicable institutional
  CAS Q3 year/category rule; owner-confirmed publication-charge route;
  target-specific source/PDF conversion. The provisional Discover current-price
  lookup is complete, but no payer, agreement or waiver is confirmed.
- **P1:** insert the certified journal's data/code statement, rebuild the
  allowlisted archive under the selected license, and rerun deterministic and
  independent package validation.
- **P2:** new readers, methods, seeds, budgets and benchmarks remain closed.

Primary rejection risks remain the narrow empirical contribution, no joint
advantage over HGB-only, a single accepted 3B reader, incomplete original-fit
provenance, conditional inference and absent standalone deployment timing.
