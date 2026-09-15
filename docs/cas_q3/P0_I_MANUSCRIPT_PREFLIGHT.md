# P0-I manuscript preflight and evidence-to-section map

Status: **PASS_PREFLIGHT_READY_TO_DRAFT_ON_EXPLICIT_AUTHORIZATION; MANUSCRIPT
NOT STARTED.** This is a planning and acceptance record, not manuscript prose.
It does not contain an abstract, introduction, related-work narrative, method
section, results narrative or conclusion.

The working title remains:

> Supervision-Matched Selection of Paired RAG Repairs: An Empirical Study of
> Accuracy and Damage

## Drafting profiles

Use one evidence source and maintain journal-specific render profiles:

- **Discover Computing profile:** Research article; abstract under 250 words;
  single-anonymous author surface; mandatory cover letter, funding and Data
  Availability Statement.
- **JIIS profile:** complete paper at or below 25 pages including references,
  tables and figures; LaTeX-only source; mandatory Data Availability Statement.
- **JIS fallback profile:** 5,000–7,500-word anonymous main manuscript,
  abstract at or below 150 words, separate identity/title page and Sage
  Vancouver references.
- **NLP fallback profile:** initial PDF with embedded figures/tables, final
  LaTeX source and required ethics, funding, conflict and Data Availability
  Statements.

No profile is active until P0-H certifies the target journal.

## Evidence-to-section map

| Planned section | Authoritative evidence | Required content boundary | Forbidden overstatement |
|---|---|---|---|
| Problem and contribution | `PROJECT_CHARTER.md`, `P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md` | Empirical audit of post-generation Keep/Repair choice under matched supervision and fixed action allocation | New selector architecture, first selective RAG, first paired intervention, state-of-the-art method |
| Related work | `P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md` | Directly compare gain prediction, post-generation arbitration, corrective RAG, adaptive retrieval and retrieval-harm studies | Omitting the 2026 gain-prediction overlap or treating task differences as method novelty |
| Study design | `P0_C_METHOD_FAIRNESS_ACCOUNT.md`, `CURRENT_METHOD.md` | Exact reader/revisions, three dataset-specific pools, 6,000 questions, 18,000 traces, three retrievers, candidate acquisition, eligibility and K=900 | Calling HGB the top-level model; describing three pools as one mixed corpus; hiding acquisition cost |
| Policies and supervision | `P0_C_METHOD_FAIRNESS_ACCOUNT.md` | All nine policies, five matched fitted heads, seven upstream estimators, fit counts, missing values, ties and Gold order | Calling HGB_GBV_R a novel architecture; omitting the HGB_ONLY_R comparator |
| Outcomes and statistics | `P0_B_RESULT_CLAIM_MAP.md`, `P0_D_STATISTICAL_STATEMENT_VERIFICATION.md` | EM/F1 definitions, Recovery/Damage/Net, 20,000 grouped draws, six-endpoint adjustment, strict joint rule and fixed-action sensitivity | Independent-trace inference, confidence guarantee, favorable subgroup promotion |
| Main results | `POINT_ESTIMATES.json`, `INTERVALS.json`, `P0_B_RESULT_CLAIM_MAP.md` | Full nine-policy table and all three ordered primary comparisons | Claiming superiority over HGB_ONLY_R or advancement of ROA-FULL |
| Cost | `P0_F_CLAIM_SCOPED_COST_TABLE.md` | Shared workload counts, separate stage timers and saved C4 peaks | Summing non-additive timers; standalone latency, full peak, FLOPs or speedup claim |
| Provenance and threats | `P0_E_PROVENANCE_CONTAMINATION_ADAPTATION_FAILURE_DISCLOSURES.md` | ID separation, semantic/pretraining contamination limits, missing historical fit receipts, GbV adaptation | Clean-data guarantee, literal original training replay, replacing missing evidence with later receipts |
| Negative and stopped extensions | Q2 Phi/Mistral acceptance records indexed by `EVIDENCE_INDEX.json` | Phi semantic validation failed; Mistral stopped before engineering | Treating either as a reader-effect result or robustness experiment |
| Availability | `P0_G_REVIEWER_RELEASE_LICENSE_ANONYMIZATION_AUDIT.md`, aggregate candidate README | Aggregate verification scope, private canonical evidence, project-license status | End-to-end public reproducibility or public distribution before license selection |
| Limitations and conclusion | All P0-A through P0-H records | One reader, empirical-only contribution, comparison-dependent support and deployment-cost gaps | General reader/domain transfer, formal risk control, production readiness |

`POINT_ESTIMATES.json` and `INTERVALS.json` above refer to the exact sealed files
under `outputs/cas_q2/empirical_analysis_v1/`; their accepted hashes are pinned
in `P0_D_STATISTICAL_STATEMENT_VERIFICATION.md` and the aggregate candidate.

## Planned tables and figures

| Item | Role | Source | Placement rule |
|---|---|---|---|
| Table 1 | Population, reader, retrievers, pools, supervision and allocation | P0-C | Main text |
| Table 2 | All nine policy point estimates: actions, Recovery, Damage, Net, EM and F1 | Sealed point estimates | Main text; no policy omitted |
| Table 3 | Three primary ordered comparisons with adjusted EM/Damage ranges and joint decision | Sealed intervals | Main text; preserve signs, units and zero-touching rule |
| Table 4 | Dataset/retriever fixed-action breakdowns | Sealed point estimates | Supplementary/secondary only; no subgroup Claim |
| Table 5 | Shared workload, non-additive timers, memory observations and missing deployment metrics | P0-F | Main or supplement according to page limit |
| Table 6 | Provenance, contamination and stopped-extension disclosure matrix | P0-E and terminal records | Supplement, with concise main-text pointer |
| Figure 1 | Fixed candidate-acquisition and post-generation policy pipeline | P0-C | Conceptual diagram only; label costs before selection |
| Figure 2 | Recovery versus Damage for all nine policies at the fixed allocation | Sealed point estimates | Descriptive visualization; no interval inference beyond Table 3 |

No figure or table has been rendered under this preflight. Drafting
authorization must precede the creation of manuscript artifacts.

## Author inputs that cannot be inferred

- final author names, order, affiliations and corresponding author;
- author contributions and approval from all authors/institution where needed;
- funding statement and grant identifiers;
- competing-interest declaration;
- ethics/IRB applicability statement approved by the responsible authors;
- acknowledgements and any required disclosure of writing/AI assistance;
- project license selection;
- APC/waiver acceptance if Discover Computing is selected; and
- institution-recognized CAS edition, category and title/ISSN rule.

These inputs must be stored outside the anonymous main manuscript and inserted
only in the appropriate journal profile.

## Draft completion gates

After explicit authorization, P0-I requires all of the following:

1. complete LaTeX source, bibliography, figures, tables and supplement;
2. journal-specific main manuscript, title page, cover letter and declarations;
3. every numeric cell traced to a sealed aggregate or accepted cost receipt;
4. all citations checked against primary papers/publisher metadata;
5. no prohibited Claim from the map above;
6. anonymous artifact rebuilt after license and journal-policy insertion;
7. ordinary compile, link, reference and package checks;
8. Astra xhigh final authenticity/fairness and Claim-sufficiency audit;
9. Astra xhigh simulated-reviewer audit with every major concern resolved or
   explicitly retained as a limitation; and
10. Astra xhigh final Submission Ready decision under the verified CAS Q3
    journal record.

**CAS Q3 STATUS: NOT READY.** The manuscript preflight is ready, but manuscript
authorization, final journal qualification, author inputs, actual manuscript
files and final Astra xhigh audits are missing.
