# JIIS R6 Major-Revision Acceptance

Date: 2026-09-16

## Decision

**CAS Q3 STATUS: NOT READY**

The supplied reviewer comment has been addressed in manuscript R6 and in a point-by-point response. The revision is mechanically accepted and the public reproduction upgrade is real: external users can now refit all five current Recovery heads from a text-free development bundle and reconstruct the full reported statistical layer. No scientific result changed.

This is not yet final submission acceptance. A final Astra xhigh scientific/claim audit and author review remain required. Institutional and other compliance closure remains deferred under the owner's instruction.

## Accepted changes

- The contribution is stated as controlled empirical signal attribution, not a new two-answer selector architecture.
- The manuscript preserves the non-passing HGB+GbV_R versus HGB-only_R joint result.
- Effective current-head fit size is reported as 2,572 eligible traces: 557 positive and 2,015 negative.
- Effective disjoint calibration size is reported as 630 eligible traces: 132 positive and 498 negative.
- Learned scalar counts are reported as 28, 26, 10, 8, and 8 for ROA-FULL, ROA-NOGBV, HGB+GbV_R, HGB-only_R, and GbV-only_R, excluding preprocessing statistics.
- Public commit `038d769e96d092a2eec3bbc5df9f45f3c2a17ff0` releases the accepted current-head parameter records and a text-free 13,500-row development bundle.
- The public workflow performs ten exact paper-head fits, reconstructs the nine-policy point estimates, and repeats the full 20,000-draw bootstrap. GitHub Actions run 35057594179 passed.
- Data/code availability wording is consistent across the manuscript and repository: current-head fitting and the statistical layer are publicly reproduced; neural acquisition and historical upstream training are not.

## Major rejection risks

1. Evidence breadth remains limited to one Qwen2.5-3B-Instruct reader, one rank-5 replacement repair, three multi-hop datasets, and one global 900-action operating point.
2. The combined policy does not establish joint accuracy-and-damage superiority over the stronger HGB-only_R control.
3. The novelty is empirical design and evidence discipline rather than a standalone method innovation. Reviewers seeking a new architecture may still reject the paper.
4. Historical upstream HGB lacks original per-estimator fit-time ID/matrix receipts and an independent original-fit witness.
5. Public reproduction starts from realized numeric development/evaluation inputs and does not regenerate retrieval, candidates, or neural scores.

## Missing evidence

- successful independent reader replication;
- a second repair operator or operating-point family evaluated prospectively;
- unseen-domain validation;
- end-to-end public neural acquisition;
- independent authentication of the original historical HGB training event.

## Priority tasks

### P0

- Run the final Astra xhigh scientific and claim-boundary audit on R6 and the response letter.
- Conduct author review of the 21-page R6 PDF and approve the response wording.
- Keep all reported negative boundaries unchanged unless new prospective evidence is run.

### P1

- If the editor explicitly requests broader evidence, design a new prospective reader or repair-operator study before any implementation. Do not reinterpret the failed Phi validation or stopped Mistral protocol as robustness evidence.
- Prepare a persistent archive snapshot of public commit `038d769...` when compliance closure resumes.

### P2

- Improve typography by rebuilding the authoritative R6 content from a single editable journal source rather than PDF replacement, if the submission schedule allows.
- Add an optional compact table of released artifacts and reproducibility levels to the supplement.

## Artifacts

- Manuscript: `output/pdf/JIIS_Manuscript_R6_Major_Revision.pdf`
- Response: `paper/JIIS_R6_RESPONSE_TO_REVIEWER.md`
- Verification: `paper/JIIS_R6_MAJOR_REVISION_VERIFICATION.json`
- Public repository: https://github.com/qianxingji/ReliableRAG-Code
