# P0-G/H/I accessible external-evidence census

Decision: **PASS_BOUNDED_ACCESSIBLE_EXTERNAL_CLOSURE_EVIDENCE_CENSUS_NO_RECOVERY_AFTER_TRIAGE**.

**CAS Q3 STATUS: NOT READY.**

On 2026-09-14, a read-only scan covered the original workspace, the preserved
private historical root and the old `ReliableRAG_Codex.zip`. It did not scan the
active worktree, so current project documents could not satisfy the search.

The scan saw 465,460 ordinary files, read 454,115 text files no larger than
5,000,000 bytes, inspected 39 ZIP archives and read 1,448 bounded text members.
It skipped 26 oversized ordinary text files and 12 oversized ZIP text members.
No archive member matched and no read error occurred. Archives were not
extracted and no file was executed.

The deliberately broad Chinese marker initially returned three ordinary-text
candidates. Manual line-level inspection classified all three as false
positives: the word “分区” referred to experimental data, fit/calibration/test,
OOF or LODO partitions, not CAS journal partitions, institutional approval or
release review.

| SHA-256 | Preserved source | Triage |
|---|---|---|
| `184cb2491837ac6fac7f2373af840ab7c907f6ef402083e18e0ba98e4f84f015` | `outputs/daa_v3_development/dual_head_constrained_v1/AUTHOR_REPORT.md` | Experimental model/data partition report |
| `bad7f809566f13aa0e0eb1fb0f3873e707fc2dee9d4f3077a72accbe4a7e6f3` | `outputs/daa_v3_development/risk_gated_policy_v1/AUTHOR_REPORT.md` | Experimental policy partition report |
| `f10b14f7744f9728ce3b32ab9c2c21c85cd4723d2619d477f039a78da2a79c31` | `outputs/daa_v3_development/risk_head_comparison_v1/AUTHOR_REPORT.md` | Experimental OOF/LODO partition report |

This is a bounded negative result. It does not prove absence outside the three
roots, within unsupported binary formats, or inside skipped oversized members.
The three experimental reports are not institutional records. No HBUT CAS
record, manuscript approval or code-release approval was recovered, so P0-G,
P0-H and P0-I remain open. The scan performed no model forward, scientific fit,
bootstrap recomputation or scientific-payload interpretation and does not
authorize submission or distribution.
