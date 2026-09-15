# Dependency release and same-host relocation accepted

Research Lead acceptance, 2026-09-11. **CAS Q2 STATUS: NOT READY.**

The original namespace-only review ZIP was insufficient for numerical replay.
A new private package now supplies all required original artifacts and source;
its restored source/data passed the unchanged primary and independent replayers.
This closes the measured ROA input-delivery gap for saved-parameter replay on
this Windows host. It does not reconstruct training or establish submission
readiness. Aggregate evidence: [ROA_REPLAY_RELEASE_RESULTS.json](ROA_REPLAY_RELEASE_RESULTS.json).

## What actually passed

| Check | Observed result |
|---|---:|
| Original data/authentication files packaged and restored | 2,821 |
| Original file bytes, before compression | 344,547,677 |
| Accepted original parent-receipt records covered exactly | 2,601 |
| Primary contexts / saved models / prediction rows | 28 / 56 / 38,424 |
| Primary maximum logit / probability / metric error | 0 / 0 / 0 |
| Changed action memberships | 0 |
| Independent checks / maximum numeric error | 2,744,203 / 0 |
| Pre/post relocation input files unchanged | 6,755 |
| Rejected old-data/code fallback reads during actual replay | 0 |
| Latest engineering tests / pass / existing Windows skips | 151 / 149 / 2 |
| Engineering inputs unchanged | 1,087 |

Source commit: `73f8158c2570e77998d944fac6e5bc9afe4fe6eb`. The data package
contains all five original namespaces, the four separately bound direct
score/action/outcome inputs, protocol files and six original environment-byte
artifacts. Source restored from its self-contained Git bundle is clean. The
original numerical/control modules and replay wrapper match the engineering
worktree byte for byte. Numerical gates and action rules are unchanged.

The external Python open-event guard denied access to the old project data/code
and engineering worktree. It allowed only the existing original `.venv` runtime
under those roots and recorded those accesses. No model fit, retrieval/generation
or fresh Gold read occurred. The current host/environment was reused: this is
not a clean installation, different-host/OS test, or OS sandbox proof.

## Preserved problems and fixes

The first new package omitted the separately bound V2 actions file. Its archive
bytes passed, but dependency coverage did not; its internal PASS is explicitly
overruled. The entire first package remains intact. The v2 implementation adds
all four direct inputs and requires exact coverage of the accepted original
parent receipts. See [the prospective dependency correction](ROA_REPLAY_RELEASE_DEPENDENCY_CORRECTION.md).

The first relocation precheck stopped because the generic artifact verifier's
Git blob uses LF while its original worktree uses CRLF. No numerical mode had
started. The prospective second runner separately authenticates both known
representations; it changes no bytes, original digest or numerical requirement.
See [the exact line-ending record](ROA_REPLAY_RELOCATION_LINE_ENDINGS.md).
Both rejected prechecks, old implementations and all original files remain.

## External pins and local delivery

- Accepted v2 package manifest:
  `77cb08f879595c9da47aff52c9ed6531453ab961ee330f3d13d1b814ab537c73`.
- Full relocation acceptance manifest:
  `4f0acd5432dd4b4e37ad4246c75b7168f188f05e7d9bbe583da4c95977f99299`.
- Latest engineering manifest:
  `4b29382b94bee2b8c1de3ba6232fb424bb4e809d6fdf1ab65196c327475335c2`.
- Local combined `ROA_REPLAY_RELEASE_V2_PRIVATE.zip`: 55,259,271 bytes,
  51 verified members; SHA-256
  `052219db01230c5a5ea0031cfdde56e6ae23f14c2bda63097c75c21b3e9f17a2`.

The combined archive contains the accepted data/source package, primary and
independent replay receipts, engineering seals, failure records, acceptance
scripts and contracts. The rejected v1 archive itself remains separately on
disk; its manifest, inventory, build result and rejection are included for
review. No private data or archive was uploaded. Use the [runbook](ROA_REPLAY_RELEASE_RUNBOOK.md)
with the **v2 package and external pin above**, and the line-ending qualification.
The restored numerical checkpoint intentionally predates this acceptance doc.

## Continuing research work

C3's original process continues. The 08:23:57 UTC non-atomic byte snapshot has
6,355/18,000 canonical pairs and 19,065/54,000 generation receipts; all 41 frozen
runtime source/config files remain unchanged. Completion, fixed 180-trace replay
and full independent C3 acceptance still gate C4. D and cost executors remain
implemented but unexecuted until complete C4 prelabel acceptance. Total scientific
fits remain 178; fresh Gold reads remain zero.

The main rejection risks remain absent validated novelty after both failed
historical advancement rules, incomplete fresh empirical evidence, and seven
missing original per-estimator fit-time ID/matrix receipts. The current release
does not include all neural assets or the unfinished fresh pipeline's outputs;
absolute-path freeze relocation and clean environment reconstruction remain.
The cost and published-comparator limitations already documented also remain.

P0: complete C3, C4 and D in order; reconcile accepted-prelabel costs and review
the contribution from actual results. P1: complete fresh-pipeline delivery,
environment reconstruction and accurate comparison/provenance claims. P2: no
additional model, feature, seed or budget search. CAS year, institutional category
rule and journal remain user-undecided; no journal qualification is asserted.
