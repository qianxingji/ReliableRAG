# P1 clean public code repository candidate acceptance

Signed date: 2026-09-15 (Asia/Shanghai). Reviewer: client-side Research
Project Lead.

**DECISION: PASS_CLEAN_PUBLIC_REPOSITORY_CANDIDATE_PUBLICATION_WITHHELD.**

**CAS Q3 STATUS: NOT READY.** The clean repository candidate is technically
ready for public creation, but this record does not replace the required
institutional release review or authorize public distribution.

## Candidate identity

| Field | Value |
|---|---|
| Local repository | `E:/paper/ReliableRAG-Code` |
| Intended GitHub repository | `qianxingji/ReliableRAG-Code` |
| Branch | `main` |
| Commit | `55b65a835cbea3d49185fe5212a11eba06fe0a55` |
| Commit count | 1 |
| Tracked files | 33 |
| Total tracked bytes | 180,158 |
| License | Apache License 2.0 for project-authored code; explicit scope file included |
| Public creation attempted | false |

The candidate is a new independent Git repository. It does not contain the
private project's Git history, forensic receipts, benchmark payloads, generated
answers, per-question outcomes, model weights, learned estimators, local paths,
or private execution artifacts.

## Fresh-clone acceptance

The repository was cloned with `git clone --no-local` into the previously absent
directory
`E:/paper/ReliableRAG-cas-q2-p0-1/tmp/public_repo_clean_checkout_20260915_b`.
All checks were executed from that clone with the accepted project Python
environment.

| Check | Result |
|---|---|
| Public code unit tests | 6 passed |
| Aggregate reporting verification | `PASS_CAS_Q3_STATISTICAL_STATEMENT_VERIFICATION`, 129 checks |
| Repository audit | `PASS_CLEAN_PUBLIC_REPOSITORY`, 162 checks |
| Scientific fits during verification | 0 |
| Model forwards during verification | 0 |
| Fresh-clone working tree | clean |
| Fresh-clone HEAD | `55b65a835cbea3d49185fe5212a11eba06fe0a55` |
| Historical HGB source SHA-256 | `3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717` |
| Secret and absolute-user-path scan | pass |

The first fresh-clone test invocation was launched from the private project's
working directory and therefore imported that project's `src` package. It
failed before testing the public clone. This invocation error was preserved in
the client task log. The test was then executed from the clone root with hard
exit-code checks and all six tests passed. No repository file changed between
the two invocations.

## Reproducibility boundary

The candidate publishes the authenticated HGB source, paired GbV scoring,
selection and analysis kernels, sealed aggregate outputs, and verification
tests. It supports independent verification of the aggregate reporting layer.
It does not claim to regenerate the accepted 18,000 neural traces from raw
benchmark inputs. The README, code-availability statement, data statement,
third-party notices, and reproduction guide state this boundary explicitly.

## Remaining release gates

- retain written institutional release-review approval;
- obtain the responsible author's final action-time authorization to create the
  public GitHub repository;
- create and push the exact accepted commit without rewriting its history;
- verify the public GitHub Actions run and record the resulting URL and commit;
- archive the accepted public release under a persistent identifier when the
  manuscript submission package is finalized.

Public distribution remains withheld until the applicable release authorization
is recorded. Passing this engineering acceptance must not be represented as
full end-to-end neural reproducibility or as submission readiness.
