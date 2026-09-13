# P0-G project-license decision packet

Status: **OWNER DECISION REQUIRED; RECOMMEND APACHE-2.0 FOR PROJECT-AUTHORED CODE AND DOCUMENTATION.**

**CAS Q3 STATUS: NOT READY.** This packet reduces the license gate to a concrete
owner choice. It does not add a license, authorize distribution or assert that
the project owner holds rights that have not been confirmed.

## Recommended option

Choose **Apache License 2.0** for project-authored source code and documentation
if the copyright holder permits an open-source release. The official license is
published by the Apache Software Foundation at
<https://www.apache.org/licenses/LICENSE-2.0.txt>; SPDX identifier:
`Apache-2.0`. The official application guidance says to place the full text in
a top-level `LICENSE` and maintain an appropriate `NOTICE` when applicable:
<https://www.apache.org/legal/apply-license.html>.

This is the preferred option for ReliableRAG because it is permissive, retains
copyright/license notices, requires modified files to state changes, and
contains an express patent grant and termination provisions. Those terms are
useful for research software that may be reused or extended. They do not grant
rights to third-party datasets, model weights or dependencies.

Owner inputs required before implementation:

1. exact legal copyright holder;
2. copyright year or year range;
3. confirmation that the holder may license all project-authored tracked code
   and documentation; and
4. any institutional NOTICE wording or technology-transfer review requirement.

## Alternative options

| Option | When it fits | Consequence for the reviewer package |
|---|---|---|
| Apache-2.0 — recommended | The owner wants permissive reuse with an express patent license and change notices. | Add exact official `LICENSE`, owner-specific `NOTICE`, SPDX metadata and rebuild the aggregate candidate. |
| MIT | The owner prioritizes a shorter permissive license and accepts that it has no express patent-license section comparable to Apache-2.0. Official OSI text: <https://opensource.org/license/mit>. | Add the exact text with real year/holder, update package metadata and rebuild. |
| No public code license yet | Institutional ownership or release approval is unresolved. | Keep the repository and aggregate ZIP distribution-withheld; arrange journal-approved confidential review access if allowed. |

Copyleft licensing is not recommended as the default for this package because
the current goal is a small reviewer-facing research release and the repository
does not redistribute third-party source or model/data payloads. A copyleft
choice remains possible only if the owner deliberately wants its downstream
source-sharing conditions and confirms compatibility for every distributed
component.

## Fixed third-party boundary

The project license would cover only material the project owner is entitled to
license. The current aggregate candidate deliberately excludes:

- HotpotQA, 2WikiMultiHopQA and MuSiQue questions, contexts and answers;
- Qwen, BGE and DeBERTa weights/tokenizer assets;
- third-party wheels and copied dependency source;
- generated answers, per-question outcomes and private reproduction archives.

The existing `release/cas_q3_aggregate/THIRD_PARTY_NOTICES.md` retains upstream
links, exact model revisions and the action applied to each material. Adding a
top-level license must not replace or weaken those separate terms.

## Implementation after owner selection

After a signed owner decision, perform one prospective release-only change:

1. add the exact chosen license at the repository top level and any required
   notice/metadata;
2. replace `PENDING_OWNER_SELECTION` and `distribution_authorized=false` only
   in a new version of the aggregate packager/manifest after target-journal
   policy review;
3. keep benchmark text, model assets, private ledgers and identity-bearing
   forensic receipts excluded;
4. build two fresh destinations and require byte-identical archive hashes;
5. rerun the independent archive validator, extraction round trip, 129-check
   aggregate verifier and identity/path scanners; and
6. update the manuscript data/code statement, cover letter and evidence index.

Do not retroactively edit the currently sealed withheld archive or its receipt.
Its `PENDING_OWNER_SELECTION` state is historical evidence of the pre-license
gate.

## Owner decision record to supply

```text
Selected option: Apache-2.0 / MIT / distribution withheld
Copyright holder: <exact legal name>
Copyright year or range: <year>
Institutional NOTICE/review requirement: <text or none>
```

P0-G remains open until this decision and the target journal's release/data/code
policy are both known and the newly licensed candidate passes the same
deterministic and independent checks.
