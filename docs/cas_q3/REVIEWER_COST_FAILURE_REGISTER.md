# Reviewer cost and failure register

Decision: **PASS_COMPLETE_REVIEWER_COST_AND_MATERIAL_FAILURE_REGISTER_WITH_MEASUREMENT_LIMITS.**

**CAS Q3 STATUS: NOT READY.** This register consolidates the workload actually
executed, the measurements that do not exist, and every submission-relevant
negative or stopped route. It reports accepted receipts without rerunning a
model or converting technical failures into scientific outcomes.

## Shared executed workload

All nine policies use the same previously acquired candidates and score graph.
There was no separately deployed or timed policy implementation.

| Stage | Accepted executed workload | Interpretation |
|---|---:|---|
| Original retrieval C2 | 18,000 logical retrievals; 12,000 BM25 and 12,000 dense components; 15,422 embedding forwards; 54,716 document rows embedded | Shared original candidate acquisition |
| Repair retrieval C3 | 18,000 logical repair retrievals; 12,000 BGE query forwards; zero document re-embedding | Shared repair candidate acquisition |
| Qwen generation | 54,000 receipts; 51,901,556 prompt tokens; 826,362 generated tokens/score-step forwards | Original answer, repair query and repaired answer for every trace |
| C4 base scoring | 2,250 answer-embedding forwards; 16,932 likelihood forwards; 136 cache hits | Shared HGB and historical score inputs |
| C4 GbV scoring | 8,534 NLI forwards over 42,946 premise/hypothesis pairs | Shared paired GbV input |
| Policy allocation | Eight switching policies select 900 actions each; Keep selects zero | CPU-side selection after all candidates and scores exist |
| Bounded neural replay | 180 traces; 540 generation receipts; 518,966 prompt tokens; 8,441 generated tokens/forwards | Reproducibility witness, not an independent workload estimate |

`K=900` is exactly 5% of 18,000 trace decisions. It is an **action allocation**,
not 5% of retrieval, generation, scoring, tokens, wall time, memory, energy or
FLOPs. Candidate acquisition and all scores had already been computed before
any policy selected its 900 actions.

## Timers and memory receipts

| Receipt boundary | Observed value | Prohibited interpretation |
|---|---:|---|
| C2 timer | 1,096.562 s | Per-query or end-to-end latency |
| C3 timer | 45,216.887 s | Standalone repair-policy latency |
| C4 base-scoring timer | 5,337.573 s | HGB-only deployment latency |
| C4 GbV-scoring timer | 3,523.022 s | GbV-only deployment latency |
| Allocation timer | 157.658 s | Total system runtime |
| C4 base allocator peak | 8,153,970,176 bytes | Simultaneous whole-system peak |
| C4 GbV allocator peak | 2,956,706,304 bytes | Value to add to the base peak |

The five timers have different setup, cache, I/O and audit boundaries and must
not be summed. The two allocator peaks came from different stage executions and
must not be added.

## Measurements that remain unavailable

| Missing evidence | Required reporting text |
|---|---|
| Standalone HGB-only, GbV-only and fusion deployment timing | Not measured; no speed ranking or latency Claim |
| Uniform end-to-end wall-time boundary and per-trace distribution | Not measured; stage timers remain separate |
| Canonical C2/C3 accelerator peaks and simultaneous system peak | Not measured; the two C4 peaks are non-additive |
| C2/C3 BGE token totals and generation input-token touches per decode step | Not measured; prompt receipts are not FLOPs |
| FLOPs and energy | Not measured; do not infer from tokens or action count |

## Scientific negative results and stopped reader routes

| Event | Final status | Permitted interpretation |
|---|---|---|
| Historical ROA development advancement gates | Failed and retained | Historical candidate support did not clear an advancement rule. |
| Fresh `ROA-FULL` vs `HGB_GBV_R` | Joint rule not met | A favorable EM point estimate is not advancement. |
| `HGB_GBV_R` vs `HGB_ONLY_R` | Joint rule not met | The negative Damage endpoint does not establish joint superiority because EM crosses zero. |
| `HGB_GBV_R` vs `GBV_ONLY_R` | Joint rule met | The only primary joint positive; it cannot be generalized to all baselines. |
| Phi V4 reader extension | `FAIL_P0_1_PHI_DEVELOPMENT_AUTHENTICITY` | Acquisition/replay artifacts are authentic, but the frozen semantic norm gate failed; there is no Phi effect result. |
| Mistral reader extension | `STOP_MISTRAL_EXTENSION_BEFORE_ENGINEERING` | No model execution, fit, score or outcome exists; it is not a negative reader result. |

## Preserved engineering failures

| Failure class | Resolution and evidence boundary |
|---|---|
| Historical seven-model byte gate | One HGB `_bin_mapper.n_threads` field differed (6 versus 1); learning arrays, trees, scores and actions matched. The failed byte gate remains and cannot be relabelled exact model-byte replay. |
| C3 validation V1/V2 | Both failed under their frozen validators; the prospectively versioned V3.2 route later passed. Earlier namespaces remain sealed and are not overwritten by the later PASS. |
| C4 invented preflight V1 | The name-only guard rejected the authenticated Jinja `generate` compiler before Qwen/NLI execution. A separately frozen direct-caller V2 correction passed; V1 remains failed. |
| Cost prerequisite attempts | Two attempts stopped before a scientific namespace because prerequisite binding/graph files were unresolved. The third versioned attempt passed after prospective exact-path/hash additions. |
| Aggregate release candidate V1 | An overbroad absolute-path scanner treated URL schemes as drive paths and stopped before archive creation. The scanner was prospectively corrected and regression-tested; empty failed destinations remain preserved. |

These engineering failures demonstrate fail-closed behavior and versioned
correction. They do not add or subtract scientific effect evidence. The full
forensic chronology remains in `docs/cas_q2/`; this table is the
submission-relevant index rather than a replacement for those immutable files.

## Authorities

- `docs/cas_q3/P0_F_CLAIM_SCOPED_COST_TABLE.md`
- `docs/cas_q3/P0_E_PROVENANCE_CONTAMINATION_ADAPTATION_FAILURE_DISCLOSURES.md`
- `docs/cas_q2/P0_3_FRESH_RESULT_DECISION.md`
- `docs/cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md`
- `docs/cas_q2/MISTRAL_EMPIRICAL_EXTENSION_PROTOCOL_GO_STOP_REVIEW.md`
- `docs/cas_q3/P0_G_AGGREGATE_RELEASE_CANDIDATE_FAILURE_V1.md`

Primary rejection risks remain the absence of an independent algorithmic
contribution, no joint advantage over HGB-only, one accepted reader, missing
original fit-time provenance and missing standalone deployment measurements.
