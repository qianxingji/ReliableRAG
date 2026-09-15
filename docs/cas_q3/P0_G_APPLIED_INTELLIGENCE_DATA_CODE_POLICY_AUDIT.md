# P0-G Applied Intelligence data/code policy audit

Audit date: 2026-09-15 (Asia/Shanghai)

Decision: **PASS_OFFICIAL_APPLIED_INTELLIGENCE_POLICY_MAPPED_RELEASE_AND_REVIEW_ACCESS_GATES_OPEN**.

**CAS Q3 STATUS: NOT READY.** Applied Intelligence requires a Data Availability
Statement for original research. Its current guidelines strongly encourage
sharing relevant data and depositing supporting data in a public repository.
When public sharing is impossible, the statement must explain how data can be
accessed and the conditions for reuse. Authors must hold the necessary rights
for material they deposit. The declarations summary also covers Data, Material
and/or Code availability.

Springer Nature's current company policy adds a distinct code obligation:
submission implies that relevant newly developed code will be made freely
available to researchers, and articles will carry a Code Availability section.
A stable public repository, documentation and a permanent identifier are
encouraged. Its research-data policy permits reasonable restrictions for data
obtained under third-party licence terms, but editors and reviewers may request
access to non-public underlying data and code. These statements establish that
the proposed restricted-evidence boundary is policy-compatible in principle;
they do not approve a particular private link, waive third-party terms or
guarantee that an editor will find the supplied evidence sufficient.

Official source: <https://link.springer.com/journal/10489/submission-guidelines>
(Research Data Policy and Data Availability Statements; checked 2026-09-15).

Additional official sources checked 2026-09-15:

- <https://www.springernature.com/gp/authors/research-data-policy>
- <https://www.springernature.com/gp/authors/research-data-policy/data-policy-faqs>
- <https://support.springernature.com/en/support/solutions/articles/6000237619-software-and-code-sharing>

## Project mapping

The top-level Apache License 2.0 text now covers the owner-designated
project-authored code. It does not change the terms of HotpotQA,
2WikiMultiHopQA, MuSiQue, Qwen, BGE, DeBERTa, Python packages or any other
third-party material.

The GitHub repository is already public and every commit has a versioned URL.
That satisfies the current-public-location part of the code plan, but the
submission version has not yet been frozen and a Git commit URL is not claimed
to be the requested permanent archive identifier. A final release or archive
must bind the accepted code, documentation, Code Availability text and exact
manuscript version after institutional release review.

The existing anonymous aggregate candidate contains no question text, Gold,
generated answer, model weight, per-question outcome, local path or identity.
Its earlier immutable ZIP remains a withheld historical witness because its
manifest says `PENDING_OWNER_SELECTION` and its third-party notice predates the
accepted correction. It must not be edited or relabeled.

A separate Apache-2.0-aware V2 candidate has now been built twice from the
corrected source and independently validated. Its archive SHA-256 is
`4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8`.
The manifest scopes Apache-2.0 to two project-authored scripts and does not
relicense documentation or aggregate evidence. This closes the candidate-build
engineering items, while distribution and persistent-archive gates remain open.

Before public release or submission, P0-G still requires:

1. confirmation of the exact legal copyright holder and year/range;
2. a decision on institutional release review and any required NOTICE text;
3. institutional review of the intended Qwen and non-`-c` DeBERTa use/release
   boundary;
4. final authorization of the validated V2 candidate or a required successor;
5. a frozen final versioned-code URL plus an immutable archive DOI or other
   permanent identifier; and
6. operational delivery details for restricted private evidence if the editor
   or reviewers request it. General policy compatibility is established, but
   no particular private link or transfer channel has been accepted.

The selected subscription publication route concerns article access and APCs;
it does not weaken the journal's data-statement requirement or authorize code,
data or model redistribution.
