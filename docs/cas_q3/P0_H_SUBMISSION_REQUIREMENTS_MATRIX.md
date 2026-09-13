# P0-H candidate-journal submission requirements matrix

Audit date: 2026-09-13 (Asia/Shanghai)

Decision: **PASS_OFFICIAL_SUBMISSION_REQUIREMENTS_MATRIX_ONLY; CAS
QUALIFICATION_AND_FINAL JOURNAL REMAIN PENDING.** This record translates current
publisher instructions into concrete package requirements. It does not certify
any journal as CAS Tier 3, choose an article-processing charge, or authorize
submission.

## Frozen candidate requirements

| Requirement | Discover Computing | Journal of Intelligent Information Systems | Journal of Information Science | Natural Language Processing |
|---|---|---|---|---|
| Intended article type | Research | Original research article | Article | Research article |
| Initial manuscript | Manuscript file through Snapp | LaTeX only; all editable source files | Main anonymous manuscript plus separate title page | PDF with tables/figures embedded; LaTeX strongly encouraged |
| Length | No general Research limit located in the inspected page | **25 pages including references, tables and figures** | Average **5,000–7,500 words**, 8–12 printed pages | No general Research limit frozen here |
| Abstract | **Less than 250 words** | Abstract required; exact limit not frozen here | Normally **no more than 150 words** | Required; exact limit not frozen here |
| Cover letter | Required; explain context, importance and journal fit | Not uniquely specified in the inspected section | Required; explain suitability | Submission-system requirement must be rechecked at final packaging |
| Review identity | **Single-anonymous** | Exact journal-specific mode not located in the inspected guideline | **Double-anonymized** | **Single-anonymous** under the current review page |
| Data statement | Required for every submission | Required for original research; public deposit strongly encouraged, conditional access can be explained | Data sharing encouraged; explain why unavailable where needed | Data availability statement required |
| Other declarations | Funding mandatory; competing interests and authorship supplied through Snapp; ethics if applicable | Author contributions and competing interests through submission interface; other standard declarations | Separate title page holds authors, affiliations, acknowledgements, conflict, funding, ethics and data availability | Conflict, funding, data availability and ethics statements required; AI-use disclosure in acknowledgements if applicable |
| Figures/tables | May be uploaded with supplement/related files | Count toward 25-page limit | Count and word total requested at submission | Embedded in initial PDF; separate editable files after acceptance |
| Access/fee structure | Fully open access; APC/funding decision required | Hybrid/Open Choice optional | Subscription route states no submission/publication fee; optional paid OA | Current fee/funding terms require final author check |
| Current package fit | Compiled journal-neutral source exists and 204-word abstract is below 250; conversion must raise 11 pt text to at least 12 pt, use numeric citations and embed vector fonts; project license remains pending | Current 11-page main plus 3-page supplement is below 25 pages before template conversion; use `smallcondensed`, flatten upload files and recheck the final combined count | Anonymous main and separate title-page template exist; abstract must be reduced from 204 to at most 150 words and Sage style applied | Anonymous source and availability wording exist; current-title conversion and declarations remain, with a material novelty-fit risk |

Official sources:

- [Discover Computing submission guidelines](https://link.springer.com/journal/10791/submission-guidelines)
- [JIIS submission guidelines](https://link.springer.com/journal/10844/submission-guidelines)
- [Journal of Information Science submission guidelines](https://journals.sagepub.com/author-instructions/jis)
- [Natural Language Processing preparation requirements](https://www.cambridge.org/core/journals/natural-language-processing/information/author-instructions/preparing-your-materials)
- [Natural Language Processing review process](https://www.cambridge.org/core/journals/natural-language-processing/information/peer-review-information/review-process)

## One package architecture that covers all four candidates

The journal-neutral source material now exists. Render a journal-specific
surface from it using the following architecture:

1. a self-contained LaTeX manuscript source with all figures and tables;
2. a separable title page containing authors, affiliations, funding,
   acknowledgements, conflicts, ethics and correspondence information;
3. an anonymous main-document mode that removes identity-bearing declarations;
4. a single-blind mode that reinserts the approved title-page data;
5. a bounded Data and Code Availability Statement that points to the aggregate
   verification package and explicitly describes unavailable private scopes;
6. a supplement containing the complete secondary results, provenance limits,
   cost boundaries and terminal Phi/Mistral records; and
7. a journal-specific cover letter and submission checklist.

The existing anonymous aggregate ZIP already satisfies the stricter artifact
identity mode. It must be rebuilt after a project license is selected and after
the target journal's repository/link timing is confirmed.

## Journal-specific blocking items

### Discover Computing

- Verify that the current title and ISSNs, rather than predecessor-title
  records, are recognized as CAS Tier 3 by the user's institution.
- Confirm APC amount, waiver/agreement coverage and author acceptance.
- Raise body text from the current 11 pt to the official minimum 12 pt, convert
  citations to numeric form and embed every vector-figure font.
- Supply author list, affiliations, contributions, funding and competing
  interests for the non-anonymous submission.

### Journal of Intelligent Information Systems

- Verify the institution-recognized CAS Tier and category.
- Confirm the review identity mode in the live submission workflow before
  packaging; the inspected guideline did not state one journal-specific mode.
- Typeset the complete paper within 25 pages including references, figures and
  tables.
- Use the required/recommended Springer source profile recorded on the current
  page: `smallcondensed`, numeric citations, editable source, PDF, and no upload
  subfolders.

### Journal of Information Science

- Verify CAS Tier and obtain confidence from the editor/scope record that a
  technical RAG empirical study is suitable.
- Keep the reviewer manuscript fully anonymous and move every identifying
  declaration to the title page.
- Use the required Sage Vancouver reference style and keep the abstract within
  150 words.

### Natural Language Processing

- Verify the current title/ISSN rather than inheriting the former title's CAS
  record.
- Accept the journal's stronger novel-method expectation despite this study's
  empirical-only contribution, or retain it as a fallback.
- Include the required ethics, funding, conflict and data availability
  statements and any applicable AI-assistance disclosure.

## Final P0-H acceptance command

No software command can establish institutional CAS recognition. P0-H can pass
only after a retained institution-recognized record supplies the edition/year,
major or minor category, current title/ISSN treatment and Tier 3 status. The
selected journal row must then be checked against the package generated under
P0-G.

**CAS Q3 STATUS: NOT READY.** Official submission requirements are now mapped;
CAS qualification, author financial acceptance and final journal selection are
still unresolved.
