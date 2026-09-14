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
- run the owner-input privacy/fail-closed, manuscript-length, target-preflight
  transformation, institutional-CAS-record intake, institutional-release-record
  intake, complete-source transport and private target-builder safety tests;
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
  package rebuild/test suite or the 139-check full manuscript verifier, all of
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
