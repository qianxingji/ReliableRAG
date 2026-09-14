# P0-I licensed-release V2 disclosure rebuild acceptance

Acceptance date: 2026-09-14 (Asia/Shanghai)

Decision: **PASS_LICENSED_RELEASE_V2_DISCLOSURE_REBUILD_WITH_EXTERNAL_RELEASE_TEMPLATE_AND_FINAL_AUDIT_GATES_OPEN**.

**CAS Q3 STATUS: NOT READY.**

The manuscript data/code statement now records the exact engineering state:
Apache License 2.0 is present for project-authored code, a corrected
license-aware aggregate candidate was built and independently validated, and
public distribution remains withheld. It does not describe the candidate as a
DOI-bearing public archive or as end-to-end neural reproduction.

This edit changes no scientific result, interval, table, figure, comparison,
reader condition, method decision or Claim boundary. The manuscript static
verifier passes 139 checks with a 155-word abstract and 22 bibliography entries.
The PDF-text length proxy is 3,994 tokens before References and 4,691 in the
complete document; it remains a reproducible proxy rather than a publisher word
count.

## Accepted artifacts

| Artifact | SHA-256 | Result |
|---|---|---|
| `paper/manuscript.tex` | `79c50351be84ac37d6f29d308724e9b7ec2755ecf3fb702b34d88ab87f81933c` | corrected release state, anonymous source |
| `output/pdf/manuscript.pdf` | `c185360689726b757007ee215e30709846015511ae51cc7981c9b09eb0eb4016` | 11 pages, zero nonembedded and zero Type 3 fonts |
| `output/pdf/supplement.pdf` | `3ce088ddac0064d4066a10c0376cbf19bc2f4ee4e0accd2b1ea75f0fa4ba072c` | 3 pages, zero nonembedded and zero Type 3 fonts |
| Applied Intelligence modern-preflight PDF | `f423cdeb634d66e4315d56a8f4c3dda8807ef0b4fe79235e13b698c20d185ea4` | 12 pages, numeric citations, font clean |
| Applied Intelligence authored-source ZIP | `0333248977211b4d8920ffb8ecd9ed4e53b977c3ef89795d566f680de725f24f` | 8 flat authored-source members, no template dependency |

Project-lead visual inspection covered all 11 main-manuscript pages, all 3
supplement pages and all 12 target-preflight pages rendered at 110 dpi. No
clipping, overlap, missing content, anomalous blank page or unreadable table was
observed. The mechanical verifier does not self-certify this inspection.

The modern target preflight uses the authenticated December 2024 Springer
Nature `sn-jnl` package. The journal page's `smallcondensed` instruction has not
been proved equivalent to that package. Author/declaration completion,
institutional CAS evidence, release authorization and persistent identifier,
publisher-resolved target package, and the final GPT-6 Astra xhigh
artifact/fairness/Claim/reviewer audit remain open. No submission or
distribution is authorized by this acceptance.

Scientific payloads read: **no**. Model forwards: **0**. Scientific fits: **0**.
