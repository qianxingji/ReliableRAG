# Project: Reliable RAG Research

## Goal
This repository implements experiments for a research project on:

**Runtime Paired Evidence Interventions for Reliable RAG under Retrieval-State Lock-In.**

Target: a submission-ready paper competitive for CAS Journal Ranking Q2
(Chinese Academy of Sciences journal partition, not JCR Q2). The user's
2026-09-10 goal update supersedes the earlier Q1/CCF target.
This repository is for experimental research code only. Do NOT write the paper manuscript unless explicitly requested.

## Current execution entry point (2026-09-11)

Latest acceptance: ROA_CLEAN_ENVIRONMENT_ACCEPTANCE.md and
ROA_CLEAN_ENVIRONMENT_RESULTS.json. Five official, hash-locked numerical wheels
were installed offline into a new isolated environment. Full original primary
and independent replay pass with zero error and no observed old-venv access;
12,017 checked inputs, including 5,214 new environment files, remain unchanged.
This reuses the current Windows host and separate CPython 3.10.6 installation;
it is not full neural-pipeline, another-host or original-training reproduction.
The accepted source/data package has 2,821 files; all earlier failure records
and archives are preserved. Do not repeat these accepted release/environment runs.

Original P0-1 replay and all three supervised controls are complete. Both
historical advancement rules failed; no final novel-method candidate is cleared.
The frozen empirical design has five fitted policies, 6,000 new question IDs,
accepted C1 native pools and C2 original retrieval. Total scientific fits: 178.
C3 continues in its original canonical process from cc304ee, with 6,837 pairs
at 08:44:58 UTC. Recheck live process/receipts; never duplicate or restart it.
Finish canonical generation, the fixed 180-trace replay and independent C3
acceptance, then actual C4 preflight/base/GbV/policies/full prelabel validation.
C4, D and cost executors are already implemented and CPU-accepted. Only full
prelabel acceptance permits the cost audit and four real D processes.
Fresh Gold reads remain zero. Engineering tests: 151, with 149 pass and two
existing Windows capability skips; no scientific quality is implied.

Next independent work: complete neural-runtime environment/dependency and
source-path reconstruction, plus remaining comparison/provenance review.
Historical fit-time receipts and the fresh empirical result/contribution are
still missing. CAS Q2 STATUS: NOT READY. CURRENT_TASK.md is the consolidated
active handoff; prior checkpoint prose remains in Git history and the linked
immutable acceptance/protocol records, not as instructions to redo closed work.

Read `docs/cas_q2/CURRENT_TASK.md`, `PROJECT_CHARTER.md`, `CURRENT_METHOD.md`,
and `EVIDENCE_INDEX.json` in that directory before choosing work.

- Work is Research Project Lead; ChatGPT pro 6 owns research design and
  scientific argument; Codex GPT-6 Astra implements the reviewed design.
- Historical candidate: ROA-FULL, originally development-supported and
  GbV-augmented only. Subsequent attribution gates failed; no current candidate
  is cleared. Five fixed empirical comparison models now exist; they do not
  establish fresh quality, universal robustness or a new algorithm contribution.
- Preserve completed V2, risk-gate, dual-head and ROA experiments. Do not restart
  Phase 0, reopen rejected searches, or promote development results to confirmation.
- Start with artifact authentication and replay. A hash PASS is not a replay PASS
  and neither means submission readiness.
- Core algorithms, feature/model searches and confirmatory protocols require a
  concrete Research Lead design before implementation; do not optimize for a win.
- End each important stage with `CAS Q2 STATUS: NOT READY` or
  `CAS Q2 STATUS: SUBMISSION READY`. If not ready, report rejection risks, missing
  evidence, method/baseline/experiment/argument problems and P0/P1/P2 priorities.

The research-question/component/phase sections below preserve the original
research plan. They are historical context, not an instruction to repeat completed
phases or to present their hypotheses as current established contributions.

## Hardware Constraints
Primary machine:
- NVIDIA RTX 5060 Ti
- 16 GB VRAM
- Single GPU
- Do not train large language models.
- Prefer inference-only methods.
- Small classifiers/lightweight models may be trained.
- LoRA only if clearly necessary.
- Prefer 4-bit quantized 3B–8B generators.
- Never assume more than 16 GB GPU memory.

All experiments must be runnable on this machine.

## Research Constraints
Use public datasets only.
Primary datasets:
1. HotpotQA
2. 2WikiMultiHopQA
3. MuSiQue

Start with HotpotQA and 2WikiMultiHopQA.

Do not fabricate results, dataset statistics, or experimental outputs.
Every reported number must come from an actual saved experiment result.
Use fixed random seeds whenever possible.

## Research Question
We study whether RAG failures caused by missing evidence, distracting evidence, or retrieval-state lock-in can be diagnosed and repaired through runtime evidence interventions.

Given initial evidence E00, construct:
- E00 = original evidence
- E10 = original evidence + targeted additional evidence
- E01 = original evidence - dominant/suspicious evidence
- E11 = original evidence - dominant evidence + targeted additional evidence

Generate answers under the four evidence states and analyze the actual response to interventions.

## Core Research Components
### Component 1: Gap-Targeted Evidence Addition
Identify missing evidence requirements and construct targeted micro-queries.
Compare against generic query rewriting, multi-query retrieval, and random evidence addition.

### Component 2: Dominant Retrieval-State Masking
Detect evidence clusters or retrieval anchors dominating the retrieved context and perform counterfactual masking.
Compare against random deletion, lowest-score deletion, highest-score deletion, and MMR/diversity filtering.

### Component 3: Intervention-Aware Arbitration
Use observed responses under E00/E10/E01/E11 to decide whether to keep the original answer, use a repaired answer, or abstain.
Consider evidence support, evidence coverage, contradiction, intervention response, and answer stability.
Compare against majority vote, support-only selection, self-consistency, and no-abstention.

## Experimental Phases
Proceed incrementally.
- Phase 0: Environment and dataset verification.
- Phase 1: Baseline RAG.
- Phase 2: Oracle intervention headroom audit.
- Phase 3: Oracle-free evidence addition.
- Phase 4: Oracle-free evidence masking.
- Phase 5: Intervention response matrix and arbitration.
- Phase 6: Risk gating.
- Phase 7: Full ablations and cross-model experiments.

Do not begin a later phase until the previous phase produces valid saved outputs.

## Phase 2 Go/No-Go Rule
Before implementing the full method, run an oracle headroom audit.
For baseline-error samples, evaluate Oracle Add, Oracle Delete, and Oracle Joint.
If very few baseline errors are recoverable by oracle evidence intervention, stop and report the finding instead of blindly implementing later stages.

## Baseline Retrieval
Implement:
- BM25
- dense retrieval
- hybrid retrieval via Reciprocal Rank Fusion

Dense retriever should use a practical public embedding model such as BGE or E5.
Use FAISS unless there is a strong technical reason not to.
A cross-encoder reranker may be included later.

## Generator
Generator must be replaceable through a common interface.
Default target:
- open-source instruction model
- approximately 3B–8B
- 4-bit inference when needed

Do not hard-code one LLM throughout the codebase.
Cache generation outputs.

## Evaluation
At minimum support:
Answer metrics:
- Exact Match
- Token F1

Retrieval metrics:
- Recall@K
- supporting-fact recall

Reliability metrics:
- selective accuracy
- risk-coverage curve
- AURC

Research-specific metrics:
- Intervention Recovery Rate
- Unnecessary Intervention Rate

Efficiency:
- retrieval calls
- generation calls
- token usage when available
- runtime
- peak GPU memory when practical

## Reproducibility
Every experiment must save:
- configuration
- timestamp
- random seed
- model name
- retrieval parameters
- predictions
- metrics

Prefer YAML configuration files. Avoid hard-coded experiment parameters.

## Coding Standards
Use Python. Prefer modular code. Avoid giant scripts.
Separate dataset loading, retrieval, generation, evidence verification, intervention logic, and evaluation.
Add type hints where useful. Functions should have clear docstrings. Use logging instead of print statements for pipelines.

## Testing
Before declaring a component complete:
1. Run unit/smoke tests.
2. Run a tiny dataset subset.
3. Confirm output files exist.
4. Inspect several predictions manually.
5. Report failures or suspicious behavior.

## Critical Gold-Label Rule
Gold supporting facts may be used only for:
- evaluation
- controlled stress-test construction
- oracle upper bounds

The deployable runtime method must never access gold supporting facts.
When uncertain whether something causes gold-label leakage, stop and flag it.

## Scientific Integrity Rule
If a requested scientific assumption appears invalid based on actual results, report it rather than changing the experiment to force a positive result.
