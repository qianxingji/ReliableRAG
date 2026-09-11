# Project: Reliable RAG Research

## Goal
This repository implements experiments for a research project on:

**Runtime Paired Evidence Interventions for Reliable RAG under Retrieval-State Lock-In.**

Target: a submission-ready paper competitive for CAS Journal Ranking Q2
(Chinese Academy of Sciences journal partition, not JCR Q2). The user's
2026-09-10 goal update supersedes the earlier Q1/CCF target.
This repository is for experimental research code only. Do NOT write the paper manuscript unless explicitly requested.

## Current execution entry point (2026-09-11)

Latest static delivery: STATIC_DELIVERY_ACCEPTANCE.md and STATIC_DELIVERY_RESULTS.json.
The 21-seed graph passes 17,617 files / 21,118 edges, zero issues and 36 exact
namespace checks. Its 17,595 non-pretrained files are in a new private archive;
the existing 22-asset archive supplies the external members. A separate process
restored all 17,617 files to three fresh roots. All originals/restored files and
15 support files were rehashed unchanged; no scientific payload was decoded.
Use STATIC_DELIVERY_OFFLINE_RUNBOOK.md and the exact evidence-companion controls.
This closes declared static byte delivery, not arbitrary source IO, live C3/future
stage outputs, package/predecessor execution bindings or full pipeline replay.
Do not repeat the accepted audit/package/restoration; keep all namespaces sealed.

Earlier asset delivery: PRETRAINED_ASSET_DELIVERY_ACCEPTANCE.md and
PRETRAINED_ASSET_DELIVERY_RESULTS.json.
All 22 original BGE/Qwen/GbV NLI snapshot files (7,494,996,533 bytes) are packaged
and independently restored from the private archive. Every original/restored
file matches prior audit hashes; Qwen's index closes over exactly two shards.
The validator has zero old-project content reads, model loads, forwards or Gold
access. Use the exact controls and freeze in the small evidence companion and
PRETRAINED_ASSET_OFFLINE_RUNBOOK.md. This gate closes pretrained asset delivery;
the later static gate adds declared learned-policy/data/sealed-output bytes.
Do not repeat accepted packaging or restoration; preserve all earlier failures.

Previous native delivery gate: EMPIRICAL_DELIVERY_ASSEMBLY_ACCEPTANCE.md and
EMPIRICAL_DELIVERY_ASSEMBLY_RESULTS.json.
The separate v2 adapter/v4 probe passed two fresh source/config-only processes,
including spaces/Chinese paths: 46 runtime and 34 scoring AST records, unchanged
existing generation boundary, 21 explicit Path bindings, 83 unchanged files per
root and 21,267 unchanged environment files. Thirteen path tests pass; no model,
forward, fit or fresh outcome access. Preserve all three failed attempts and
explicit OS/optional-import refinements. This is native assembly only, not full
pipeline delivery or neural replay. Do not repeat the accepted assembly gate.

Latest environment acceptance: NEURAL_CLEAN_ENVIRONMENT_ACCEPTANCE.md and
NEURAL_CLEAN_ENVIRONMENT_RESULTS.json. The 35 exact official wheels are now
installed as 33 main distributions plus separate SentencePiece/PyArrow targets.
All 21,139 installed official payload files match; 21,225 RECORD hashes pass.
Fixed CPU import/binary fixtures pass in an isolated process: no pretrained
model, CUDA initialization or observed old-venv access. All 21,267 new files and
30,823 original environment files remain unchanged. Preserve the first smoke
failure and its diagnostic; v2 permits only the authenticated local IPv6
capability bind and requires that socket closed. The original NumPy RECORD
discrepancy remains untouched. This is package/CPU acceptance, not CUDA execution,
full neural replay, arbitrary-root delivery or another-host/OS reproduction.
A complete private offline package kit is built and verified; no private upload.
Do not repeat accepted wheel acquisition, installation or CPU smoke.

The separate CPU numerical environment and full original saved-parameter replay
remain accepted with zero error and no observed old-venv access. Do not repeat
accepted replay, release or runtime inventory. Original P0-1 replay and all three
supervised controls are complete. Both historical advancement rules failed;
no final novel-method candidate is cleared. Five fixed policies, 6,000 new IDs
and accepted C1/C2 inputs define the empirical design. Total scientific fits: 178.
C3 remains its original canonical process from cc304ee, PID 55688: 11,182 pairs
at 11:49:29 UTC. Recheck live process/receipts; never duplicate or restart it.
Finish canonical generation, fixed 180-trace replay and independent acceptance,
then actual C4 preflight/base/GbV/policies/full prelabel validation. Only complete
C4 acceptance permits the implemented cost auditor and four real D processes.
Fresh Gold reads remain zero. The earlier full engineering run: 151 tests, with
149 pass and two Windows capability skips; that suite was not repeated here.

Next independent work: prospectively design and verify restored learned-object,
package and predecessor bindings; later add completed-stage output dependencies
and execute relocated pipeline replay. Declared static byte delivery and native
source assembly are accepted, but
C4 root/package-path checks and absolute predecessor bindings remain constraints;
do not silently modify active loaders or redirect the running C3 process.
Historical fit-time receipts and fresh result/contribution remain missing.
CAS Q2 STATUS: NOT READY. CURRENT_TASK.md is the consolidated active handoff;
linked immutable records and Git history preserve earlier checkpoints.

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
