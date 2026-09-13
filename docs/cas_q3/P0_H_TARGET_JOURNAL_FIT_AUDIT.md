# P0-H target-journal and CAS Q3 fit audit

Audit date: 2026-09-13 (Asia/Shanghai)

Decision: **PENDING_CAS_RULE; NO JOURNAL CERTIFIED.** Publisher/ISSN records
support a bounded candidate order, but the user has stated that the applicable
CAS year, major/minor category and institutional rule are still undecided. The
official CAS platform exposes the journal records only after login in this
session. JCR quartiles, impact factors and third-party partition lists are not
substitutes.

## Required qualification record

A final P0-H PASS requires one row with all fields completed:

| Field | Required value | Current state |
|---|---|---|
| Journal title | Current official title | Pending final selection |
| Print/online ISSN and ISSN-L | Confirmed current identifiers | Available for candidates below |
| CAS partition edition/year | Institution-recognized edition | **Undecided** |
| CAS category | Exact major or minor category | **Undecided** |
| CAS tier | Tier 3 under that exact category/year | **Unverified** |
| Institutional rule | Recognition of title/ISSN changes, online-only titles and submission/acceptance dates | **Undecided** |
| Article type | Official type matching the paper | Candidate-specific below |
| Review/anonymity | Official policy | Candidate-specific below |
| Data/code policy | Satisfiable release plan | P0-G still open |
| Fees/constraints | Affordable and acceptable to authors | Author decision pending where applicable |

The [official CAS partition portal](https://www.fenqubiao.com/) states that it
covers SCIE, SSCI and A&HCI journals and provides both major- and minor-category
systems. Its public page is currently a login screen, so this audit does not
claim access to a journal's official partition record.

## Provisional candidate order

This is a scientific/editorial fit order, not a CAS Q3 certification.

### 1. Discover Computing — strongest empirical-editorial fit, highest identity risk

- Current publisher page: [aims and scope](https://link.springer.com/journal/10791/aims-and-scope).
- Current identifiers: print `2948-2984`, online `2948-2992`, confirmed by the
  [ISSN International Centre record](https://portal.issn.org/resource/ISSN-L/2948-2984);
  the journal is described by Springer as formerly *Information Retrieval
  Journal*.
- Scope explicitly includes artificial intelligence, machine learning and
  natural language processing across computer science.
- The [submission guidelines](https://link.springer.com/journal/10791/submission-guidelines)
  accept Research articles presenting new scientific results, require a data
  availability statement, and use single-anonymous review. The stated review
  standard asks reviewers to focus on accurate reporting and fundamental
  validity rather than significance, which is compatible with the paper's
  controlled empirical and negative-result structure.
- It is fully open access, so APC/funding terms require an author check.

Fit judgment: **provisional first choice if, and only if, the exact current title
and ISSNs are Tier 3 under the institution's applicable CAS rule.** The 2024
title/ISSN transition is a serious partition risk: an old ranking for
*Information Retrieval Journal* cannot be transferred to *Discover Computing*
without an explicit institutional ruling.

### 2. Journal of Intelligent Information Systems — strongest stable subject identity

- Confirmed ISSN-L `0925-9902`; print `0925-9902`, online `1573-7675` in the
  [ISSN International Centre record](https://portal.issn.org/resource/ISSN-L/0925-9902).
- Springer [aims and scope](https://link.springer.com/journal/10844/aims-and-scope)
  explicitly cover intelligent information retrieval, machine learning,
  uncertainty and information-system validation. Research papers and system
  experimentation are in scope.
- The [submission guidelines](https://link.springer.com/journal/10844/submission-guidelines)
  impose a 25-page limit, require LaTeX, require editable sources and a Data
  Availability Statement, and strongly encourage supporting-data deposit.
- The scope also asks papers to improve on strong academic/industrial practice
  and uses “original and state-of-the-art” language.

Fit judgment: **provisional second choice.** The information-retrieval and
uncertainty scope is direct, and the title/ISSN identity is stable. Desk-rejection
risk is material because the current study has no new algorithm, does not show a
joint gain over HGB_ONLY_R, and has not numerically compared against the newest
full systems identified in P0-A.

### 3. Journal of Information Science — stable identity, weaker technical scope

- Print `0165-5515`, online `1741-6485`; confirmed by the
  [ISSN International Centre](https://portal.issn.org/resource/ISSN/1741-6485)
  and publisher issue records.
- The [publisher journal page](https://journals.sagepub.com/home/JIS/) covers
  information science and knowledge-management theory and practice.
- The [submission guidelines](https://journals.sagepub.com/author-instructions/jis)
  specify double-anonymized review, typical 5,000–7,500-word articles, no
  mandatory submission/publication fee under the subscription route, and an
  encouraged data-availability statement.

Fit judgment: **fallback only after an editorial-scope check.** Its stable title
and explicit double-anonymized process are operationally clear, but a technical
RAG selector paper may be judged outside the journal's information-science
audience.

### 4. Natural Language Processing — direct QA scope, title/novelty risk

- Cambridge's [current journal page](https://www.cambridge.org/core/journals/natural-language-processing/information/about-this-journal)
  lists online ISSN `2977-0424`, states that the title was formerly *Natural
  Language Engineering*, and includes information retrieval and question
  answering in scope.
- The same page encourages original studies with novel NLP methods/models.
- The [review policy](https://www.cambridge.org/core/journals/natural-language-processing/information/peer-review-information/review-process)
  is single-anonymous and normally uses at least three external reviewers.
- The [official title history](https://www.cambridge.org/core/journals/natural-language-processing/information/about-this-journal/past-titles)
  separates the current online ISSN from the former title's print/online ISSNs.

Fit judgment: **not preferred for this paper.** Question answering is directly in
scope, but the journal's novel-method emphasis conflicts with the accepted
empirical-only contribution, and its recent title/ISSN change creates the same
CAS continuity problem as Discover Computing.

## Candidate comparison

| Candidate | Subject fit | Empirical/negative-result fit | Identity stability | Main rejection or qualification risk |
|---|---|---|---|---|
| Discover Computing | Broad, adequate | Strongest | Low after title change | Current ISSN may lack recognized CAS Q3 record; APC |
| Journal of Intelligent Information Systems | Strongest | Moderate | High | May expect stronger method/SOTA advance |
| Journal of Information Science | Moderate/uncertain | Moderate | High | Technical RAG paper may be out of scope; double-blind release needed |
| Natural Language Processing | Strong | Weak-to-moderate | Low after title change | Novel-method expectation and CAS continuity |

## Decision rule

1. Query the institution-recognized CAS edition with current title and both
   ISSNs for Discover Computing and Journal of Intelligent Information Systems.
2. Apply the exact major/minor category rule used for evaluation; retain the
   result page or institution-issued evidence.
3. If both are recognized Tier 3, choose Discover Computing for the current
   empirical/soundness framing unless APC is unacceptable; otherwise choose
   Journal of Intelligent Information Systems and accept its higher contribution
   desk risk.
4. If only one is recognized Tier 3, select it only after its release/data policy
   can be met.
5. If neither is recognized, inspect Journal of Information Science, then the
   current Natural Language Processing title. Do not inherit a predecessor
   title's tier without written institutional acceptance.
6. If no candidate both qualifies and accepts the bounded single-reader
   empirical scope, stop this submission route. Do not add experiments or inflate
   Claims to force fit.

## Remaining P0-H evidence

The unresolved items are precise: CAS edition/year; major versus minor category;
institutional treatment of title/ISSN changes; the official Tier-3 record for a
current ISSN; APC acceptability if applicable; and the selected journal's final
review-artifact policy. Once those are supplied, the final qualification can be
completed without new scientific computation.

**CAS Q3 STATUS: NOT READY.** P0-H is not closed. The current provisional leader
is Discover Computing conditional on CAS qualification; Journal of Intelligent
Information Systems is the stable-identity alternative.
