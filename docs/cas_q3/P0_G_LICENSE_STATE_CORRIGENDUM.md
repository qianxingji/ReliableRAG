# P0-G current license-state corrigendum

**Decision:** `PARTIAL_PASS_OWNER_SELECTED_APACHE2_ROOT_LICENSE_AND_SCOPE_BOUND_THIRD_PARTY_AND_INSTITUTIONAL_GATES_OPEN`

**CAS Q3 STATUS: NOT READY.**

The early reviewer-release audit correctly recorded that no top-level license
existed at the time it was written. Commit `020f3cd` later added the exact
Apache License 2.0 text, and the owner subsequently selected Apache-2.0 for
project-authored ReliableRAG code. The historical audit remains unchanged. The
current decision packet has been replaced so it no longer presents license
selection or root-license creation as pending.

The current root `LICENSE` has SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
`LICENSE_SCOPE.md` states the repository boundary. No project-specific NOTICE
or copyright line has been invented because the legal holder, year/range and
institutional review requirement remain unanswered.

The pinned [Qwen2.5-3B-Instruct license](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/aa8e72537993ba99e69dfaafa59ed015b17504d1/LICENSE)
is the Qwen Research License Agreement and limits its grant to non-commercial
purposes, with separate redistribution and notice conditions. The pinned
[non-`-c` DeBERTa model card](https://huggingface.co/MoritzLaurer/deberta-v3-large-zeroshot-v2.0)
labels the foundation model MIT while warning that its broader training mix
contains data with non-commercial licenses and that legal interpretations
differ. Both model-weight payloads remain excluded from the aggregate candidate.
This technical inventory is not legal or institutional approval.

P0-G remains open for the legal holder/year, institutional release/NOTICE
decision, explicit review of both model boundaries, final archive authorization,
journal-accepted restricted-evidence route and persistent archive identifier.
