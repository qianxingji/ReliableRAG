# P1-E public aggregate-reporting CI

Decision: **PASS_PORTABLE_PUBLIC_REPORTING_CI_WITH_PRIVATE_REPRODUCTION_EXCLUDED**.

Remote acceptance: **CLOSED** on commit
`cd11cbf46f6b759eb102e1c5a44d201c082e366d`. Both the
[push run](https://github.com/qianxingji/ReliableRAG/actions/runs/34804142574)
and the
[pull-request run](https://github.com/qianxingji/ReliableRAG/actions/runs/34804144674)
completed successfully on 2026-09-14.
The first corrected public-surface acceptance also remains retained in push run
[34801833707](https://github.com/qianxingji/ReliableRAG/actions/runs/34801833707)
and pull-request run
[34801836852](https://github.com/qianxingji/ReliableRAG/actions/runs/34801836852).

The Apache-aware aggregate V2 and rebuilt Applied Intelligence disclosure were
accepted on commit `e81c278636f4eebf0f68ad23f460eae7d74893b2` by push run
[34806104442](https://github.com/qianxingji/ReliableRAG/actions/runs/34806104442)
and pull-request run
[34806106663](https://github.com/qianxingji/ReliableRAG/actions/runs/34806106663).
Both completed successfully on 2026-09-14. The workflow authenticates the
committed public reporting surface and fail-closed release wording; the
withheld V2 archive and its private-input tests remain outside the runner.
The acceptance-record follow-up commit
`9d646fb60a92a594f26eee8d47070266539d0551` also passed push run
[34806236165](https://github.com/qianxingji/ReliableRAG/actions/runs/34806236165)
and pull-request run
[34806238427](https://github.com/qianxingji/ReliableRAG/actions/runs/34806238427).

The Applied Intelligence complete-source transport safety addition was
accepted on commit `250cd5af9b24e75a06915b6dc5d107185bca868d` by push run
[34807538106](https://github.com/qianxingji/ReliableRAG/actions/runs/34807538106)
and pull-request run
[34807539860](https://github.com/qianxingji/ReliableRAG/actions/runs/34807539860).
Both completed successfully on 2026-09-14. The added portable unit tests cover
flat-path rejection and deterministic ZIP construction with temporary
synthetic bytes. The private transport ZIP, publisher template ZIP and
scientific inputs remain outside the public runner.

**CAS Q3 STATUS: NOT READY.** The workflow
`.github/workflows/public-reporting-audit.yml` gives the draft PR a portable,
reviewer-visible check over committed aggregate and manuscript artifacts. It is
not an end-to-end scientific reproduction workflow.

## Executed public scope

The Ubuntu job performs the following operations:

- verify hashes for all eight committed table/figure assets against the tracked
  aggregate-only asset receipt, while checking the two private aggregate hashes
  as declarations rather than reading or authenticating the ignored files;
- verify citations, anonymity and the frozen positive/negative Claim boundary
  across the committed manuscript and public claim summary;
- inspect the committed main and supplement PDFs for page count, text markers,
  embedded fonts, Type 3 fonts and build-log failures;
- rerun the documented Poppler text-length proxy;
- run the 38-check verifier for the committed 12-page Applied Intelligence modern `sn-jnl` preflight,
  its font state, Claim boundaries and flat eight-member authored-source ZIP;
- verify the bounded public 2025 Applied Intelligence major-Q3 corroboration
  record while retaining its non-authoritative and institutional-access limits;
- run the owner-input privacy/fail-closed, manuscript-length, target-preflight
  transformation, institutional-CAS-record intake, institutional-release-record
  intake, unified cross-record closure preflight, complete-source transport and
  private target-builder safety tests;
  these tests use temporary synthetic values and do not require or
  publish the private target ZIP, identity-bearing output or official publisher
  package; and
- require the top-level submission gate to exit with code 2 and retain
  `submission_ready=false`, zero fits, zero model forwards and no scientific
  payload reads.

The final `git diff --exit-code` check requires all regenerated tracked receipts
to match the committed bytes.

The owner-gate correction at commit
`07ea5ce7754771177e0826df7d3fa340cac97fbb` exposed a Windows-only fallback in
the newly admitted private-packet safety test: when `pdflatex` was absent on
Ubuntu, executable discovery indexed the unavailable `LOCALAPPDATA` variable.
That portable-engineering failure is retained in push run
[34812220477](https://github.com/qianxingji/ReliableRAG/actions/runs/34812220477)
and pull-request run
[34812222762](https://github.com/qianxingji/ReliableRAG/actions/runs/34812222762).
Commit `53c9e3deade01c1d268c4bc3169a73ac9dfab102` replaced the direct environment
index with a guarded Windows fallback and added a no-`LOCALAPPDATA` regression
test. Push run
[34812422447](https://github.com/qianxingji/ReliableRAG/actions/runs/34812422447)
and pull-request run
[34812424983](https://github.com/qianxingji/ReliableRAG/actions/runs/34812424983)
then completed successfully. This failure and repair changed no paper result,
model execution or scientific fit.

Subsequent public-evidence continuity is retained through commit
`79d6f65b4ca4e679d313db4197011264b0d06b88`. The official-template route commit
`13c3247b3d8b8cf4778ed23162a7036ef07948d4` passed push run
[34813538336](https://github.com/qianxingji/ReliableRAG/actions/runs/34813538336)
and pull-request run
[34813542720](https://github.com/qianxingji/ReliableRAG/actions/runs/34813542720).
The HBUT evidence refinement at
`347c7b06e9d421e430dad2ef500be203eae5686c` passed push run
[34814218658](https://github.com/qianxingji/ReliableRAG/actions/runs/34814218658)
and pull-request run
[34814221769](https://github.com/qianxingji/ReliableRAG/actions/runs/34814221769).
The authoritative 2025 CAS-platform boundary at
`79d6f65b4ca4e679d313db4197011264b0d06b88` passed push run
[34814508417](https://github.com/qianxingji/ReliableRAG/actions/runs/34814508417)
and pull-request run
[34814511106](https://github.com/qianxingji/ReliableRAG/actions/runs/34814511106).
Each run completed successfully on 2026-09-14 and retained `NOT READY`.

The private institutional release-record intake at
`ca4196ea81df55c0b3df42ea307487a4dd6885e4` passed push run
[34817939287](https://github.com/qianxingji/ReliableRAG/actions/runs/34817939287)
and pull-request run
[34817942528](https://github.com/qianxingji/ReliableRAG/actions/runs/34817942528).
Both completed successfully on 2026-09-14. They validate the public template
and synthetic fail-closed cases only; no private institutional evidence was
present on the runner and distribution remained unauthorized.

The consolidated HBUT request and external-closure handoff at
`bc8821984ff0e17fa71e531b98eb0c607d302290` passed push run
[34820858483](https://github.com/qianxingji/ReliableRAG/actions/runs/34820858483)
and pull-request run
[34820862475](https://github.com/qianxingji/ReliableRAG/actions/runs/34820862475).
Both completed successfully on 2026-09-14 and retained the institutional CAS,
release, author-package and final-audit gates.

The first bounded external-evidence census commit
`2552b042ec6103ed81a29c4bf98f61f91df673a1` passed all Windows checks but
failed push run
[34854850909](https://github.com/qianxingji/ReliableRAG/actions/runs/34854850909)
and pull-request run
[34854858306](https://github.com/qianxingji/ReliableRAG/actions/runs/34854858306).
The scanner compared exclusion names against every component of an absolute
path. Linux temporary-test roots therefore inherited the `/tmp` component and
were excluded before three positive/skip assertions could execute. Commit
`4da3c290f58c8150ca356e0d6dc6db68f9e87940` limits pruning to descendant
directories inside each supplied root and passed push run
[34855553266](https://github.com/qianxingji/ReliableRAG/actions/runs/34855553266)
and pull-request run
[34855558071](https://github.com/qianxingji/ReliableRAG/actions/runs/34855558071).
The repair changes traversal portability only. It does not alter the retained
Windows census, recover institutional evidence or close a P0 gate.

The oversized streaming extension at
`3062bd855e544c4afb4913c739e871df0225e346` passed push run
[34857250304](https://github.com/qianxingji/ReliableRAG/actions/runs/34857250304)
and pull-request run
[34857255190](https://github.com/qianxingji/ReliableRAG/actions/runs/34857255190).
Both runs execute the 79-test portable suite and retain the fail-closed
Submission Ready gate. The runner verifies the committed receipt and streaming
implementation with synthetic files; it does not possess or rescan the three
external Windows evidence roots.

The PDF text-layer census at
`512b3ee40624abf8c19785a607c641e67e0585a5` passed push run
[34859398928](https://github.com/qianxingji/ReliableRAG/actions/runs/34859398928)
and pull-request run
[34859404889](https://github.com/qianxingji/ReliableRAG/actions/runs/34859404889).
Both execute the 83-test portable suite and retain the fail-closed submission
gate. CI verifies the committed zero-candidate receipt and parser boundary with
synthetic PDF inputs; the 238 external PDFs remain a host-local read-only scan.

The deduplicated PDF structure and attachment hardening at
`140fadb6d09ec51645604dede6688dbdd971636f` passed push run
[34860901978](https://github.com/qianxingji/ReliableRAG/actions/runs/34860901978)
and pull-request run
[34860908583](https://github.com/qianxingji/ReliableRAG/actions/runs/34860908583).
The 84-test suite verifies fail-closed low-text and attachment cases. The
committed host receipt records 35 unique PDF hashes with usable text layers,
35 completed attachment inventories and zero attachment.

The PDF-structure CI acceptance record at
`ebde5811069b1d118abdf1d84cd8d2d3e0223901` passed push run
[34861285829](https://github.com/qianxingji/ReliableRAG/actions/runs/34861285829)
and pull-request run
[34861291749](https://github.com/qianxingji/ReliableRAG/actions/runs/34861291749).
This record-only commit changes no scanner behavior or scientific result.

The common document-container inventory at
`bb4127b76be67271e16bad4e65d1f0879e94911d` passed push run
[34862502586](https://github.com/qianxingji/ReliableRAG/actions/runs/34862502586)
and pull-request run
[34862514582](https://github.com/qianxingji/ReliableRAG/actions/runs/34862514582).
The 87-test suite verifies metadata-only ordinary-file and ZIP-member counting.
The committed host receipt records 100 ordinary PDFs and 138 ZIP PDF members,
zero files or members under the listed Office, OpenDocument, RTF and MSG
extensions, and zero inventory errors. Missing, incorrect or unknown extensions
remain outside the inventory, and this result closes no P0 gate.

The first-level nested-archive census at
`eaccb7e828956b3535153863d307175220afe4ae` passed push run
[34865788136](https://github.com/qianxingji/ReliableRAG/actions/runs/34865788136)
and pull-request run
[34865794285](https://github.com/qianxingji/ReliableRAG/actions/runs/34865794285).
The 93-test suite verifies nested-archive discovery, marker detection, strict
header mismatches, deeper-archive rejection and size-cap refusal. The committed
host receipt covers all four ZIP-valued members, 301 direct members, 234 text
members and 32 PDF occurrences, with no candidate, skip, deeper archive or
error. CI authenticates the committed receipt and synthetic boundaries only;
it does not possess the three external Windows roots.

The ordinary-file document-magic census at
`4bd8e55abf429fabebfbd3564f877396e7779547` passed push run
[34866887798](https://github.com/qianxingji/ReliableRAG/actions/runs/34866887798)
and pull-request run
[34866890594](https://github.com/qianxingji/ReliableRAG/actions/runs/34866890594).
The 97-test suite verifies strict PDF/RTF/OLE signatures, OOXML/ODF ZIP-family
classification, disguised-document rejection and source-literal false-positive
handling. The committed host receipt covers 465,460 ordinary files and records
no document-signature/extension mismatch or scan error. CI authenticates that
receipt and its synthetic boundaries without rescanning the external roots.

The unique-PDF page-text coverage audit at
`f6b0bdb07e788a16fa76951d871ff051b6cac8e6` passed push run
[34868397670](https://github.com/qianxingji/ReliableRAG/actions/runs/34868397670)
and pull-request run
[34868404532](https://github.com/qianxingji/ReliableRAG/actions/runs/34868404532).
The 101-test suite verifies cross-scope PDF deduplication, first-level nested-PDF
inclusion, low-text fail-closed behavior and oversize refusal. The committed
host receipt reduces 270 occurrences to 35 hashes and reports 446/446 pages
above the text threshold, including 15 pages with raster images. CI does not
rerun the three-root host scan or claim OCR of image-internal text.

The external raster-image audit and Discover preflight test-isolation correction
at `80f3affb84f8dd6ecb2dde148ecd5fc0daff299c` passed push run
[34923431850](https://github.com/qianxingji/ReliableRAG/actions/runs/34923431850)
and pull-request run
[34923434886](https://github.com/qianxingji/ReliableRAG/actions/runs/34923434886).
The public workflow executes the six synthetic image-audit tests and authenticates
the committed 104-occurrence/43-hash host receipt, 7,796-path junction disclosure,
176-record reviewer map and 210-hash fail-closed submission receipt. It does not
possess or rescan the external Windows roots and does not infer the 43-image
manual visual review. A separate complete local discovery passed all 123 tests
after the Discover builder test was isolated from tracked artifacts.

The bounded AI-tool use-date evidence at
`2d64878e06f403f8a6a158291980c38432aa6748` passed push run
[34924995292](https://github.com/qianxingji/ReliableRAG/actions/runs/34924995292)
and pull-request run
[34924997925](https://github.com/qianxingji/ReliableRAG/actions/runs/34924997925).
The workflow adds three tests that prevent a routing-rule date from being
promoted to an actual use date and require the exact first/last dates to remain
unresolved pending author confirmation. The public Submission gate checks 214
pinned repository hashes in 741 checks and remains fail-closed. A separate local
reviewer-map run authenticates 180 repository records in 1,295 checks; the
withheld archives remain outside public CI. The project dependency environment
also passed the complete 400-test repository discovery with two platform skips.

The local Codex session-metadata audit at
`fdd90a17d7a34f78caae582a19b33f7a702ab5ea` passed push run
[34926007624](https://github.com/qianxingji/ReliableRAG/actions/runs/34926007624)
and pull-request run
[34926009687](https://github.com/qianxingji/ReliableRAG/actions/runs/34926009687).
CI runs three synthetic privacy/scope tests and authenticates the committed
fixed-cutoff aggregate; it does not possess or scan the originating local Codex
session files. The current bounded surface passes 129 CAS Q3 tests, a separate
project-environment discovery passes 403 tests with two platform skips, the
reviewer map authenticates 184 records in 1,334 checks, and the Submission gate
checks 218 hashes in 755 checks while remaining NOT READY.

The current Springer Nature AI-policy alignment at
`aa17a04a058e38c438f2abfaf4ce7e6a0722d270` passed push run
[34927816944](https://github.com/qianxingji/ReliableRAG/actions/runs/34927816944)
and pull-request run
[34927820531](https://github.com/qianxingji/ReliableRAG/actions/runs/34927820531).
The workflow adds three policy-mapping tests and exercises the target builder's
Methods-placement logic without real author facts or external transport. Local
validation separately clean-compiled and reviewed all 13 pages of a
synthetic-identity target PDF. The current bounded surface passes 132 CAS Q3
tests and 406 repository tests with two platform skips; the reviewer map
authenticates 188 records in 1,384 checks, and the Submission gate checks 222
hashes in 769 checks while remaining NOT READY. CI does not approve the AI
statement, supply its final date, build a real author package or authorize
submission.

The private prompt-traceability snapshot at
`9fc56414a3d4d2229f77f6eecec14faf7143b837` passed push run
[34928736267](https://github.com/qianxingji/ReliableRAG/actions/runs/34928736267)
and pull-request run
[34928739266](https://github.com/qianxingji/ReliableRAG/actions/runs/34928739266).
The workflow adds three synthetic selection, redaction and fail-closed tests.
The public runner authenticates only the tracked content-free receipt; it does
not possess the local Codex sessions or the Git-ignored redacted ledger. Local
validation passes 135 CAS Q3 tests, the reviewer map authenticates 192 records
in 1,424 checks, and the Submission gate checks 226 hashes in 783 checks while
remaining NOT READY. Neither CI run exposes prompt content or supplies author
or editor authorization.

The first CI-evidence record commit, `4e34f0abae4ca806da5ca2f949df74671ceb1c53`,
is retained as a failed portability check. Push run
[34929268521](https://github.com/qianxingji/ReliableRAG/actions/runs/34929268521)
and pull-request run
[34929271440](https://github.com/qianxingji/ReliableRAG/actions/runs/34929271440)
both rejected the submission gate because the evidence index pinned the
Windows CRLF working-tree digest of `REVIEWER_EVIDENCE_MAP.json`, while Git's
declared `eol=lf` policy committed LF bytes. No scientific result or prior
receipt was changed to conceal this failure. Correction commit
`1ac9ce4afc2c2ecf4c586bbd113e7135580c2f04` pins the committed LF digest and
passed push run
[34929458917](https://github.com/qianxingji/ReliableRAG/actions/runs/34929458917)
and pull-request run
[34929463056](https://github.com/qianxingji/ReliableRAG/actions/runs/34929463056).
The correction changes one digest only; the reviewer-map decision, open gates,
scientific exclusions and NOT READY status are unchanged.

The Applied Intelligence data/code-policy refresh at
`136bac11b8994a1661006a3d5752ed14ea825544` passed push run
[34931815342](https://github.com/qianxingji/ReliableRAG/actions/runs/34931815342)
and pull-request run
[34931817346](https://github.com/qianxingji/ReliableRAG/actions/runs/34931817346).
The refresh corrects the public-repository, final-revision, persistent-archive
and request-bound restricted-evidence wording; rebuilds the committed base and
target PDFs; and exercises the refreshed private transport and synthetic target
builder outside CI. Local validation passes all 135 CAS Q3 tests and all 409
repository tests with two Windows platform skips. The reviewer map authenticates
194 records in 1,472 checks, and the fail-closed Submission gate authenticates
228 repository hashes in 819 checks while retaining `NOT_READY`. The first
local reviewer-map run exposed a stale historical-transport equality assertion;
that failed run and its correction are retained in the versioned refresh
acceptance. Neither successful CI run reads the private transport or synthetic
author package, supplies institutional evidence, or authorizes distribution or
submission.

## Supply-chain and permission boundary

The workflow grants only `contents: read`. Official `actions/checkout@v7.0.1`
and `actions/setup-python@v7.0.0` are pinned to commits
`3d3c42e5aac5ba805825da76410c181273ba90b1` and
`5fda3b95a4ea91299a34e894583c3862153e4b97`, respectively. The job installs
Ubuntu `poppler-utils` only for PDF inspection and does not install model,
training or neural-inference packages.

## Explicit exclusions

The public runner does not possess the original dirty workspace, private static
or pretrained archives, historical ZIP recovery source, model weights, raw
question/answer ledgers or selected Gold. It therefore does not run or claim:

- the 129-check aggregate statistical-statement verifier, either aggregate-
  package rebuild/test suite or the 141-check full manuscript verifier, all of
  which require ignored aggregate inputs;
- the 30-check same-host historical-manifest archive verifier;
- reviewer-map verification that requires the withheld aggregate archive;
- original saved-parameter or historical-training replay;
- retrieval, generation, embedding, likelihood or NLI execution;
- another-host restoration of private evidence;
- original-fit authentication, contamination exclusion or reader transfer; or
- release authorization, CAS Q3 qualification or Submission Ready status.

The institutional-release-record checks authenticate only the public placeholder
schema and fail-closed behavior with temporary synthetic evidence. The ignored
owner/institution record and its evidence bytes are absent from the runner, so
this CI does not interpret a legal or institutional decision and cannot authorize
distribution.

The workflow improves continuous checking of the public reporting surface only.
Private forensic reproduction remains governed by the existing hashed runbooks
and journal-approved access boundary.

The first public run at commit `020f3cd2ba17e76a76b5767cafccb4d37438e8dc`
failed because the original workflow invoked the private aggregate verifier on
a checkout where the ignored aggregate inputs do not exist. That failure is
retained in runs
[34801428340](https://github.com/qianxingji/ReliableRAG/actions/runs/34801428340)
and
[34801428452](https://github.com/qianxingji/ReliableRAG/actions/runs/34801428452).
The correction did not copy, download or publish those private inputs; it added
a separate 49-check verifier for the committed public surface. P1-E is closed
only for this bounded public-reporting scope. The later target-preflight check
authenticates committed technical artifacts; it does not download a publisher
template or resolve the journal-page `smallcondensed` discrepancy.
