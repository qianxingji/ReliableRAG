# P0-I Applied Intelligence private submission builder acceptance

Decision: **PASS_SYNTHETIC_COMPLETE_INPUT_TO_PRIVATE_APPLIED_INTELLIGENCE_PACKAGE_PIPELINE_FINAL_FACTS_AND_AUDITS_OPEN**.

**CAS Q3 STATUS: NOT READY.** The target-specific private packaging path is now
implemented and exercised end to end with synthetic identity and declaration
data. The real owner-input file remains incomplete, so no real author-populated
submission candidate has been built.

## Implemented path

`scripts/build_cas_q3_applied_intelligence_private_submission.py` performs the
following fail-closed sequence:

1. validate every owner, institution, license, CAS and declaration field;
2. require Applied Intelligence as the selected target;
3. authenticate the anonymous ten-member complete-source transport by SHA-256
   and exact member allowlist;
4. replace exactly one anonymous front-matter anchor and exactly one declaration
   placeholder;
5. render ordered authors, affiliation mapping, corresponding email and postal
   address, CRediT roles, funding, interests, ethics, acknowledgements, AI-use
   disclosure, overlap/preprint statement and ORCIDs where supplied;
6. retain the HGB-only negative result, no-new-architecture statement and
   distribution-withheld boundary;
7. create a flat ten-member private source ZIP, compile through pdfLaTeX,
   BibTeX and two further pdfLaTeX passes, and inspect log, references, page
   count and fonts; and
8. emit a private cover letter and a redacted receipt containing hashes and
   counts but no personal values.

The builder refuses incomplete input, a non-Applied-Intelligence target, a
wrong transport hash, a changed allowlist, ambiguous replacement anchors and an
existing output directory. It always leaves CAS authority, publisher-template
acceptance, final Astra review, distribution and submission authorization
false.

## End-to-end synthetic execution

A complete synthetic one-author fixture was used only to test mechanics. Its
names, address, email, declarations and authority values are fabricated test
data and are not assertions about the real author.

The accepted second synthetic build is external at
`E:/paper/ReliableRAG-applied-intelligence-private-synthetic-20260914-b`:

- source ZIP SHA-256:
  `7f0c7e233945aa150b1aa2c68e6918d45f18f7c7531a92a004fe07d5c60da15e`;
- compiled PDF SHA-256:
  `ebcd5f9214aeeebde352f0bb0eb62bc93142f23a17642e95439c187141656878`;
- cover-letter SHA-256:
  `ae982b6ad7fc3df70e14062056310fac7950759c9a24a88b43ad74ee33eb00a2`;
- 10 flat source members and 13 compiled pages; and
- zero fatal compile errors, unresolved references, overfull boxes,
  nonembedded fonts, Type 3 fonts, visible unresolved markers or public
  placeholders.

All 13 pages were rendered at 110 dpi and inspected. The author front matter,
figures, tables, declarations and references are readable; no clipping,
overlap, blank-page anomaly or broken glyph was observed. The extra page versus
the anonymous preflight is the expected consequence of adding complete
declarations, not a scientific-content change.

## AI-disclosure boundary

Springer Nature's current policy requires transparent declaration when
generative AI helps structure or draft content, identifies human oversight and
accountability as mandatory, and does not permit an AI tool to replace
authorship or independently create scholarly conclusions. The builder renders
the already tracked disclosure only after the responsible author has approved
it and supplied tool/version/use-date details. It does not mark that approval
itself.

Official policy checked on 2026-09-14:
<https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation>.

## Remaining boundary

The ignored real input still has 30 missing fields. A real package cannot be
built until those facts and approvals pass the owner-input verifier. After a
real build, the resulting identity-bearing source, PDF and cover letter must
remain private, receive complete author review, publisher-template-path
acceptance and a final artifact-bound GPT-6 Astra xhigh fairness, Claim,
reviewer and Submission Ready audit. This synthetic acceptance authorizes none
of those later steps and performs zero model forwards and zero scientific fits.
