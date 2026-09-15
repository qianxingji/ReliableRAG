# P1 clean public code repository candidate acceptance

Signed date: 2026-09-15 (Asia/Shanghai). Reviewer: client-side Research
Project Lead.

**DECISION: PASS_CLEAN_PUBLIC_REPOSITORY_PUBLISHED_USER_AUTHORIZED_INSTITUTIONAL_RECORD_PENDING.**

**CAS Q3 STATUS: NOT READY.** The responsible author authorized public creation
in the client task and the accepted repository is now public. This record does
not establish or replace the separately required institutional release review.

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
| Public repository | `https://github.com/qianxingji/ReliableRAG-Code` |
| Public creation completed | true |

The candidate is a new independent Git repository. It does not contain the
private project's Git history, forensic receipts, benchmark payloads, generated
answers, per-question outcomes, model weights, learned estimators, local paths,
or private execution artifacts.

## Public activation

The GitHub repository was created as public and the accepted local commit was
pushed without rewriting it. Git and the GitHub public API independently report
`main` at `55b65a835cbea3d49185fe5212a11eba06fe0a55`. GitHub identifies the
repository as public, the default branch as `main`, and the detected license as
Apache-2.0.

GitHub Actions run
`https://github.com/qianxingji/ReliableRAG-Code/actions/runs/34968615526`
completed successfully for the same commit. A second clone from the public
GitHub URL into
`E:/paper/ReliableRAG-cas-q2-p0-1/tmp/public_repo_github_checkout_20260915`
passed all six unit tests, all 129 aggregate-reporting checks, and all 162
repository checks. Its HGB source hash matched the authenticated historical
hash.

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

## Remaining project gates

- retain written institutional release-review approval;
- archive the accepted public release under a persistent identifier when the
  manuscript submission package is finalized.

The repository is publicly distributed under the responsible author's explicit
authorization. Institutional release-review evidence remains pending and must
be retained before submission. Passing this engineering acceptance must not be
represented as full end-to-end neural reproducibility or as submission
readiness.
