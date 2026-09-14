# P0-G Applied Intelligence data/code policy audit

Audit date: 2026-09-14 (Asia/Shanghai)

Decision: **PASS_OFFICIAL_APPLIED_INTELLIGENCE_POLICY_MAPPED_RELEASE_AND_REVIEW_ACCESS_GATES_OPEN**.

**CAS Q3 STATUS: NOT READY.** Applied Intelligence requires a Data Availability
Statement for original research. Its current guidelines strongly encourage
sharing relevant data and depositing supporting data in a public repository.
When public sharing is impossible, the statement must explain how data can be
accessed and the conditions for reuse. Authors must hold the necessary rights
for material they deposit. The declarations summary also covers Data, Material
and/or Code availability.

Official source: <https://link.springer.com/journal/10489/submission-guidelines>
(Research Data Policy and Data Availability Statements; checked 2026-09-14).

## Project mapping

The top-level Apache License 2.0 text now covers the owner-designated
project-authored code. It does not change the terms of HotpotQA,
2WikiMultiHopQA, MuSiQue, Qwen, BGE, DeBERTa, Python packages or any other
third-party material.

The existing anonymous aggregate candidate contains no question text, Gold,
generated answer, model weight, per-question outcome, local path or identity.
Its earlier immutable ZIP remains a withheld historical witness because its
manifest says `PENDING_OWNER_SELECTION` and its third-party notice predates the
accepted correction. It must not be edited or relabeled.

Before public release or submission, P0-G still requires:

1. confirmation of the exact legal copyright holder and year/range;
2. a decision on institutional release review and any required NOTICE text;
3. institutional review of the intended Qwen and non-`-c` DeBERTa use/release
   boundary;
4. a new license-bearing aggregate package built from the corrected source;
5. two-build byte identity, independent archive validation, extraction replay
   and identity/path scans;
6. a versioned latest-code URL plus an immutable archive DOI or unique
   identifier; and
7. a reviewer-access route for restricted private evidence accepted by the
   journal or handling editor.

The selected subscription publication route concerns article access and APCs;
it does not weaken the journal's data-statement requirement or authorize code,
data or model redistribution.
