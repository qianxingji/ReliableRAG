# P0-I data and code statement revision acceptance

Decision: **PASS_DATA_CODE_POLICY_BOUNDARY_AND_REBUILT_ARTIFACT_EXTERNAL_GATES_OPEN.**

**CAS Q3 STATUS: NOT READY.** This accepts a policy-driven manuscript revision
and rebuilt technical artifacts. It does not close the owner license, persistent
archive, journal selection, author declarations, institutional CAS or final
Astra xhigh gates.

## Accepted change

The former `Data availability` section is now `Data and code availability`.
It preserves the validated anonymous aggregate-package boundary and adds the
facts required by the provisional Discover policy review:

- project-authored code is maintained in a versioned repository;
- no license-bearing archive with a DOI or other persistent identifier has been
  released;
- latest-code and immutable archive links will be supplied only after the owner,
  institution and journal release gates pass;
- private evidence may support confidential review only through a
  journal-approved channel and subject to upstream terms; and
- aggregate verification is not end-to-end public neural reproduction.

No result, comparison, statistic, method, dataset, reader, action allocation,
reference or abstract text changed. The static verifier now passes 129 checks,
including three new availability-boundary predicates. The abstract remains 142
words. The reproducible PDF proxy is 3,948 tokens before References and 4,646
for the full document; it remains a proxy rather than a publisher word count.

## Rebuild and visual acceptance

The journal-neutral manuscript rebuild has 11 pages, zero fatal errors, zero
undefined citations/references, zero overfull or underfull boxes, zero
nonembedded fonts and zero Type 3 fonts. Relative to parent commit `efdf252`,
only page 9 changes at 120 dpi; pages 1--8 and 10--11 are pixel identical. The
supplement source is unchanged and all three rebuilt supplement pages are pixel
identical to the parent artifact. The known nonfatal supplement longtable notice
is unchanged.

All 11 main pages and all 12 pages of the refreshed provisional Discover 12 pt
profile were rendered and reviewed at 100 dpi. Page 9 of the main manuscript and
page 10 of the target profile were also inspected at original rendered
resolution. No clipping, overlap, blank page, missing glyph, unresolved
reference, unreadable table or unreadable figure was observed. The provisional
profile remains a generic technical dry run and is not submission-authorized.

Artifact pins:

| Artifact | Pages/members | SHA-256 |
|---|---:|---|
| `paper/manuscript.tex` | source | `cfd9724b57789c69e36f061adc4637df559412222bfe7ceadd8abf868ed6b837` |
| `output/pdf/manuscript.pdf` | 11 | `b1798bb2fa1ba2fba323f9dfffe0205e9163067bf7bc519a16af43054f839835` |
| `output/pdf/supplement.pdf` | 3 | `4499283483f4efdb50e062482b1d0652f2fa7a3656789f1b0417c60cce7c190e` |
| `output/target_profiles/discover_computing_preflight/manuscript_12pt_preflight.pdf` | 12 | `c19df5f8a9eca8bcee6329427219aa426be17bbc6ea9aaccde266b3d17eba098` |
| `output/target_profiles/discover_computing_preflight/discover_computing_source_preflight.zip` | 8 | `df77a41a3a222c18d32a96507f0b91fa55694c8a9bdedcfcfccdf1dad551271d` |

No scientific payload, model forward, fit, score, Gold reference or bootstrap
draw was read or executed for this revision.
