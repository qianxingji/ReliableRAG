# P0-I Applied Intelligence template transport acceptance

Decision: **PARTIAL_PASS_OFFICIAL_SN_JNL_ALLOWED_COMPLETE_PRIVATE_TRANSPORT_VALIDATED_SMALLCONDENSED_LEGACY_CONFLICT_RETAINED**.

**CAS Q3 STATUS: NOT READY.** This acceptance closes the missing-dependency
engineering question for an anonymous working package. It does not resolve the
journal page's legacy `smallcondensed` instruction, populate author facts, or
authorize submission or distribution.

## Official-source boundary

The Applied Intelligence submission page checked on 2026-09-14 recommends the
current Springer Nature LaTeX template and also retains older text asking for
the Springer macro package with the `smallcondensed` option. The linked legacy
ZIP returned HTTP 404. Springer Nature's current LaTeX support page says that
its authoring template may be used for any Springer Nature journal, while also
stating that journal-specific instructions still apply. The support article
directs authors to the journal page for journal-specific template links and to
contact the journal when a required template is unavailable.

Official sources:

- <https://link.springer.com/journal/10489/submission-guidelines>
- <https://www.springernature.com/gp/authors/campaigns/latex-author-support>
- <https://support.springernature.com/en/support/solutions/articles/6000081241-templates-and-style-files-for-journal-article-preparation>

The authenticated Version 3.1 December 2024 package has SHA-256
`812e76dcaa9c28dc1bff1fb6065d51729b67d4ea140552a05088317414a3ecae`.
Its 18 members contain no `smallcondensed` string. These facts establish the
modern `sn-jnl` package as an officially supported working profile. They do not
prove that `sn-jnl` is journal-specifically equivalent to the missing legacy
profile.

## Private complete-source transport

The new builder combines the frozen eight-member authored-source ZIP with the
exact authenticated `sn-jnl.cls` and `sn-basic.bst`. It writes a flat,
ten-member anonymous ZIP to a new external directory, refuses directory reuse,
and fixes member order, timestamps, permissions and compression settings.

Two independent builds produced the same bytes:

- `E:/paper/ReliableRAG-applied-intelligence-transport-candidate-20260914-a/applied_intelligence_complete_source_transport_candidate.zip`
- `E:/paper/ReliableRAG-applied-intelligence-transport-candidate-20260914-b/applied_intelligence_complete_source_transport_candidate.zip`
- archive SHA-256: `f4279cf38aa09a1ddc212b9b295e0c73b78a67b7262845e72a6df584edeb8fdd`

Each build independently passed 56 validation checks after fresh extraction.
The checks authenticate every authored member, both official template files,
the flat allowlist, anonymity, the HGB-only negative result and the no-new-
architecture boundary. Each extracted package passed pdfLaTeX, BibTeX and two
additional pdfLaTeX passes, producing 12 pages with no fatal error, unresolved
citation, overfull box, nonembedded font or Type 3 font.

The clean-compiled PDF SHA-256 is
`f423cdeb634d66e4315d56a8f4c3dda8807ef0b4fe79235e13b698c20d185ea4`,
exactly matching the already rendered and project-lead-reviewed 12-page modern
preflight PDF. The earlier all-page visual acceptance therefore transfers by
byte identity; no new visual inference is needed.

## Remaining gate

P0-I still requires complete author/declaration facts and an author-populated
source/PDF package. Before submission, the responsible author must also retain
publisher or Editorial Manager acceptance of the modern `sn-jnl` route, or
obtain a working journal-specific legacy package. A final artifact-bound GPT-6
Astra xhigh fairness, Claim, reviewer and Submission Ready audit remains
mandatory.

The transport ZIPs remain external and private. They are not tracked, uploaded,
submitted, assigned a DOI, or authorized for distribution. This work read no
scientific payload, performed zero model forwards and performed zero fits.
