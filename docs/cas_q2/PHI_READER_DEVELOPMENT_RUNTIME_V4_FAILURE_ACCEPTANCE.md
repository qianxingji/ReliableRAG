# Phi V4 development-runtime terminal failure acceptance

Date: 2026-09-13
Decision authority: client Research Lead after independent GPT-6 Astra xhigh audit
Decision: **`FAIL_P0_1_PHI_DEVELOPMENT_AUTHENTICITY`**
**CAS Q2 STATUS: NOT READY.**

## What is accepted as authentic evidence

The blank V4 canonical acquisition completed 13,500/13,500 traces, including
40,500 generation completions, 13,500 repair bindings and 108,000 durable call
events. The fixed replay completed 180/180 traces and reports exact replay
identity. Both namespaces have complete manifests and no runtime-failure marker.
The runtime source commit is
`3d6c060cad47a09cce49927fad3dbda80f2a0fc0`.

Independent read-only work rehashed eight relevant namespaces, parsed all ten
canonical/replay JSONL ledgers, checked the complete row counts and reconstructed
cross-ledger trace bindings. The external forensic continuation also rebuilt
41,040 prompts/tokenizations and 13,680 repair rankings. These checks support that
the model ran, the ledgers are internally coherent, and the fixed replay matches
the saved canonical rows. They found no new evidence of fabrication, mutation,
Gold leakage or historical Qwen-answer reuse.

## Why P0-1 fails

The original frozen validator terminated at `independent render/guard
reconstruction` because its independent render omitted `text`. The result-blind
corrigendum preserved that failure and authorized one corrected semantic run.
After a separately preserved pre-namespace commit-hash-width launch failure, the
unique corrected semantic validator ran and terminated at `saved dense query
vector normalization`.

Independent recomputation covers all 9,120 saved 768-dimensional query vectors.
It finds 6,573 outside the frozen `1e-3` unit-norm tolerance; the maximum absolute
deviation is `0.0041683525287623535`. Every vector lies within `5e-3`, which is
consistent with normalization in BF16 followed by FP32 storage, but `5e-3` was
observed after the outcome. It cannot replace the frozen threshold.

Neither validator namespace contains a successful
`EXECUTABLE_VALIDATION_FREEZE.json` or `INDEPENDENT_VALIDATION.json`. The
post-hoc forensic wrapper explicitly skipped the failed norm assertion, so its
positive checks are supplementary evidence and not a frozen-validator PASS.

The independent Astra xhigh decision receipt is stored outside the repository at
`C:/Users/qianx/Documents/Codex/2026-09-10/reliablerag-research-project-lead-submission-ready/PHI_V4_P0_1_ASTRA_XHIGH_AUTHENTICITY_DECISION_2026-09-13.md`,
SHA-256
`c2f38467aefe1c965afef57c29a75f706d9406a194704ff4e1477911aa75ef14`.
Its read-only machine attachment has SHA-256
`2d050f95c5952563ddd19e08db6f8585da9a239c0a6106b5ba5d50986ed77796`.

Core sealed evidence:

| Evidence | SHA-256 |
|---|---|
| canonical manifest | `d368b866d7434f82ad5980cbd36359938204a1484f592c492d4347010e560b30` |
| canonical receipt | `2ccb66a9f3c9fe8ff0994c2041c826beffd56c90d146938556abfad05661bfd7` |
| replay manifest | `cb6682f12fcfee974e4ced270b958a2ebb715f4cdb49698396c0d3883d51c274` |
| replay receipt | `56dc0540c9266a9c4e85d0653bfbfb8e005d3ceb774e536784ce58ed410c16b2` |
| original validator failure manifest | `fa63d1fe59aff313643c5d809efd9bd0e6e5c66049005e40f3e767301650cc67` |
| corrected validator failure manifest | `b93c603ee0a4eca6cfabd73d6da7c1c6b34e99e6d5b79ba060817fa2a5059c05` |
| dense-vector norm audit | `1b51ad7cdeea7ca64af1223c72be75731c876a0e5109aa901528f8606f4ad8c7` |
| forensic continuation manifest | `94393e88530cf0cc1854eafccf01264825a94a89d819489b359192806479a961` |
| cross-ledger V3 evidence | `7b2006919e96be7f5f2753de34423fbfba76f556911395ebcb51f5e3d88468ac` |
| mechanical forensic V2 | `269ab9eb73749aa9d9342287c41426e4e3aab13541bc6d6a85cfb02e297edf6c` |

## Binding consequence

Preserve V1 through V4, both validator failures, the failed launch, forensic
records and every seed in place. Do not repeat canonical or replay, run another
semantic validator, create V5, change the tolerance, rewrite vectors or hashes,
or use V3/V4 Phi rows for fitting, scoring or scientific claims.

Phi test generation, reader-specific scientific fits, policy scoring, Gold
mapping and post-validation engineering remain unauthorized. A future route
would require a new prospective governance and scientific-design decision that
keeps this terminal failure visible; it cannot be presented as a correction of
the failed V4 acceptance.

The historical saved-parameter replay remains accepted within its recorded
provenance limits. Seven original per-estimator fit-time ID/matrix receipts and
an independent original-fit witness remain missing.
