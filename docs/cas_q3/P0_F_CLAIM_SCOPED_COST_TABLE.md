# P0-F claim-scoped cost table

Decision: **PASS_SHARED_STUDY_COST_WITH_EXPLICIT_MISSING_DEPLOYMENT_MEASUREMENTS.**
The table reports the accepted shared Qwen study graph. It supports workload and
limitation disclosure only. It does not support a policy speedup, a 5% compute
Claim, standalone deployment ranking or end-to-end latency comparison.

## Shared executed workload

All nine policies consume the same already acquired answer pairs and precomputed
score graph in this study. No policy-specific inference run was executed.

| Stage | Accepted observed workload | Role in the paper |
|---|---|---|
| Original retrieval C2 | 18,000 logical retrievals; 12,000 BM25 components; 12,000 dense components; 15,422 embedding forwards; 54,716 embedded document rows | Shared candidate acquisition |
| Repair retrieval C3 | 18,000 logical repair retrievals; 12,000 BGE query forwards; zero document re-embedding | Shared candidate acquisition |
| Qwen generation | 54,000 generation receipts over 18,000 traces; 51,901,556 prompt tokens; 826,362 generated tokens and output score-step forwards | Three generated outputs per trace: original answer, repair query and repaired answer |
| C4 base scoring | 2,250 answer-embedding forwards; 16,932 likelihood forwards; 136 likelihood cache hits | Shared HGB and historical score inputs |
| C4 GbV scoring | 8,534 NLI forwards over 42,946 premise/hypothesis pairs | Shared paired GbV input |
| Policy allocation | Eight switching policies each select 900 actions; Keep selects zero | CPU-side fixed-batch output choice after all candidates/scores exist |

The bounded 180-trace replay contains 540 generation receipts, 518,966 prompt
tokens and 8,441 generated tokens/forwards. It is a reproducibility witness, not
an independent workload estimate or latency benchmark.

## Preserved stage timers

| Receipt boundary | Wall time (s) | Allowed interpretation |
|---|---:|---|
| C2 | 1,096.562 | Timer for its own retrieval-stage boundary |
| Canonical C3 | 45,216.887 | Timer for its own repair acquisition boundary |
| C4 base scoring | 5,337.573 | Timer for its own base-score boundary |
| C4 GbV scoring | 3,523.022 | Timer for its own verifier-score boundary |
| Fixed allocation | 157.658 | Timer for the shared policy-allocation process |

These boundaries include different setup, cache, I/O, audit-hook and rehash
work. They must be printed as separate receipt timers and must not be summed or
renamed end-to-end latency. They do not provide per-question latency or a fair
standalone comparison among HGB_ONLY_R, GBV_ONLY_R and HGB_GBV_R.

## Saved memory observations

| C4 allocator receipt | Peak bytes | Scope |
|---|---:|---|
| Base scoring | 8,153,970,176 | Saved C4 allocator peak only |
| GbV scoring | 2,956,706,304 | Saved C4 allocator peak only |

The two peaks arise from different stage executions and cannot be added into a
simultaneous system peak. No canonical C2 or C3 CUDA allocator peak was recorded.
The historical C3 synthetic peak is not a replacement for the missing canonical
measurement.

## Policy dependency and Claim boundary

The experiment precomputes the complete shared graph to make the policy
comparison fair. A hypothetical deployment could prune dependencies for some
policies, but no such deployment was built or timed.

| Policy family | Logical signal dependency after candidate acquisition | Measured standalone deployment? |
|---|---|---|
| Keep | No switching score required to retain `a0` | No |
| Raw HGB / HGB_ONLY_R | HGB path; HGB_ONLY_R also applies its fitted calibration head | No |
| Raw GbV / GBV_ONLY_R | Paired GbV NLI path; GBV_ONLY_R also applies its fitted calibration head | No |
| HGB_GBV_R | Both HGB and paired GbV plus the two-input fitted head | No |
| ROA-FULL / ROA-NOGBV | Their frozen multi-input score sets and fitted heads | No |
| V2 | Its sealed historical score recipe | No |

This dependency table is architectural bookkeeping. It is not a latency or
energy estimate. The primary scientific comparison remains accuracy and Damage
under a fixed **action allocation**. `K=900` means that 5% of trace outputs are
switched after both candidates and every score already exist; it does not mean
5% of retrieval, generation, scoring, latency, memory, token or FLOP cost.

## Missing measurements that must remain visible

- canonical C2 and C3 CUDA allocator peaks;
- per-generation latency and per-trace latency distributions;
- separately timed standalone policy deployments;
- a uniform end-to-end wall-time boundary;
- C2/C3 BGE token totals;
- generation input-token touches per autoregressive forward;
- energy use and FLOPs; and
- a simultaneous whole-system peak-memory measurement.

Generated-token counts and prompt-token receipts are not FLOP estimates.
Missing measurements must be shown as “not measured,” not zero, not applicable
or inferred from stage timers.

## Failure and audit scope

The accepted cost process performed no new inference. It validated preserved
receipts and token/mask arrays, while a client audit checked aggregate fields,
227 deterministic full-array samples, 18,306 executable inputs and 30,912
environment files. Two prerequisite-resolution failures are preserved; both
stopped before a scientific namespace and neither read Gold, fit a model or ran
inference.

Primary authorities: `../cas_q2/EMPIRICAL_COST_ACCEPTANCE.md` and
`../cas_q2/EMPIRICAL_COST_RESULTS.json`.

**CAS Q3 STATUS: NOT READY.** P0-F is closed within these measurement limits.
P0-G through P0-I remain.
