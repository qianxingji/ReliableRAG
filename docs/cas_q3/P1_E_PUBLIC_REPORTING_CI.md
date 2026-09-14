# P1-E public aggregate-reporting CI

Decision: **PASS_PORTABLE_PUBLIC_REPORTING_CI_WITH_PRIVATE_REPRODUCTION_EXCLUDED**.

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
- run the owner-input privacy/fail-closed tests and manuscript-length tests; and
- require the top-level submission gate to exit with code 2 and retain
  `submission_ready=false`, zero fits, zero model forwards and no scientific
  payload reads.

The final `git diff --exit-code` check requires all regenerated tracked receipts
to match the committed bytes.

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

- the 129-check aggregate statistical-statement verifier, aggregate-package
  rebuild/tests or the 135-check full manuscript verifier, all of which require
  ignored aggregate inputs;
- the 30-check same-host historical-manifest archive verifier;
- reviewer-map verification that requires the withheld aggregate archive;
- original saved-parameter or historical-training replay;
- retrieval, generation, embedding, likelihood or NLI execution;
- another-host restoration of private evidence;
- original-fit authentication, contamination exclusion or reader transfer; or
- release authorization, CAS Q3 qualification or Submission Ready status.

The workflow improves continuous checking of the public reporting surface only.
Private forensic reproduction remains governed by the existing hashed runbooks
and journal-approved access boundary.

**P1-E is closed when the workflow file passes local command-equivalent checks
and GitHub reports a successful run for the pushed commit.** Until that remote
run completes, the implementation is present but remote acceptance is pending.
