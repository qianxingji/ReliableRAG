# ReliableRAG project charter
Effective 2026-09-10, from the user's explicit project-goal update.

2026-09-12 reader-axis update: the fixed Qwen empirical study is complete but
clears no novel candidate. A read-only availability/literature audit froze one
Phi-3.5-mini-instruct replication on the same 6,000-question cohort. Its unique
invented-only compatibility producer and independent validation now pass with a
binding memory limit: the long generation witness used 93.48% of nominal GPU
memory. No Phi benchmark inference, new fit or Gold read has begun. A separate
value-blind full-input/implementation freeze is required next; see
`PHI_READER_PREFLIGHT_ACCEPTANCE.md` and `PHI_READER_REPLICATION_PROTOCOL_V1.md`.

## Goal and authority

Deliver a paper competitive for a CAS Journal Ranking Q2 journal. This means the
Chinese Academy of Sciences journal partition, not JCR Q2. The previous CAS Q1
ambition is no longer a hard acceptance criterion. Verify the journal's year,
ISSN, major/minor category and institutional recognition rule before submission.

Work is Research Project Lead: priorities, research decisions, task contracts,
review and stage acceptance. ChatGPT handles research/method/experiment design
and argument. Codex implements reviewed designs, tests, runs experiments and
prepares PRs. The user's 2026-09-11 model policy fixes formal experiments,
replay and ordinary analysis to Sol High (`gpt-5.6-sol`, `high`; routine code
and tests may use Medium). P0-3 design/novelty and core Method/Claim argument use
Astra High; final authenticity, fairness, claim, reviewer and Submission Ready
audits, conflicting results and major method decisions use Astra xhigh
(`gpt-6-astra`, `xhigh`), followed by a return to Sol High. See the complete
[model routing](MODEL_ROUTING.md). These role labels do not claim that separate
external model sessions have been started.

The user's current instructions supersede old goal text. Preserve historical
protocols and outcomes rather than changing their thresholds retrospectively.

## Scientific requirements

- A meaningful research question and a specific, evidenced contribution.
- Clearly distinguish the project, method, components, baselines and ablations.
- Competitive comparisons, including negative results and the strongest relevant controls.
- Match data, preprocessing, evaluation, tuning/label budgets and action budgets.
  Action-count matching does not establish retrieval/LLM/NLI cost equality.
- Keep all seeds and failures; no test-label tuning or selective publication.
- Trace each important number to commit/config/seed/environment/script/prediction.
- Match every claim to evidence from that exact method/version/population.
- Experiments are chosen for scientific need; do not mechanically add modules or seeds.

## Stage acceptance

Output exactly one overall status: `CAS Q2 STATUS: NOT READY` or
`CAS Q2 STATUS: SUBMISSION READY`. Technical integrity, numerical replay,
development support and submission readiness are separate judgments.

NOT READY reports must cover: leading rejection risk; missing core evidence;
method, baseline, experimental-completeness and argument issues; next priorities.
P0 blocks credible submission, P1 materially improves competitiveness, P2 is optional.

## Current decision

2026-09-12 latest execution state: the fixed-policy empirical replication
scientific design is frozen in EMPIRICAL_REPLICATION_PROTOCOL_V1.md. Five fixed
comparison models and the 6,000-question ID-only cohort passed independent
acceptance; see EMPIRICAL_AB_ACCEPTANCE.md and the separate sample-size prose
corrigendum. Stage C1's guarded native runtime projections and candidate pools
passed independent acceptance (EMPIRICAL_C1_ACCEPTANCE.md). C2 original retrieval
also passed independent acceptance (EMPIRICAL_C2_ACCEPTANCE.md). C3's frozen
trace/replay inputs and joint GPU preflight passed; canonical reader/repair
generation and fixed neural replay completed under EMPIRICAL_C3_EXECUTION_ACCEPTANCE.md.
The first full independent validation failed due to two missing helper-scope
constants. Separate V2 code/fixtures corrected those, and the V1 report is
preserved in its accepted failure directory. V2 then failed on one observed
dense component score after 18,026 generation checks. The complete census and
Astra xhigh audit now establish exact current-native-default 12-thread
reconstruction for every saved repair field and 507 one-thread score-only rows,
with no membership/order/replacement change. Historical acquisition threads are
still unrecorded and V2 stays failed. C3_VALIDATION_V3_CONTRACT.md and its
prospective V3.1 numerical-runtime amendment freeze the single permitted route
to complete validation. The V3.1 invented-only gate and V2 failure relocation
are client-accepted. A preserved V3.1 pre-config import failure is independently
audited, and the bootstrap-only V3.2 gate is accepted. The unique full V3.2 run
and Astra xhigh authenticity audit now accept complete C3: all 18,180 signatures,
30,912 environment files and 66 controls were independently rechecked, and the
actual C4 GPU-preflight predecessor gate passed. Frozen C4 scoring/prelabel
sealing and outcome analysis remain pending. Total control/panel fits: 178.
Seven historical final-fit reproduction calls
bring actual takeover fits to 185; their strict HGB byte failure remains in
HISTORICAL_TRAINING_REPLAY_REVIEW.md. The C3 validation binding has separate
engineering acceptance in C3_VALIDATION_BINDING_ACCEPTANCE.md; complete current
C3 is accepted in C3_VALIDATION_V3_2_FINAL_ACCEPTANCE.md. Later fresh
scoring/outcome stages remain pending. Historical
reference/outcome replay is separately accepted in HISTORICAL_OUTCOME_REPLAY_ACCEPTANCE.md;
current Gold stays closed.
Both historical method-advancement failures remain unchanged.

C4 GPU preflight V1 subsequently failed on a Jinja compiler `generate` name
collision in its guard. The independently accepted failure audit preserves the
directory, all 428 inputs and all 30,912 inventory files. The exact-code and
direct-caller correction is prospectively frozen in
C4_JINJA_EXECUTION_BINDING_V2_CONTRACT.md; Sol High CPU implementation is next.
No base scoring or current Gold read is authorized until its prerequisite gates.

The user confirmed that CAS partition year, institutional major/minor-category
recognition and target journal are undecided. Record them as pending, not as an
experimental blocker or a verified journal qualification.

Earlier post-control decision, retained as history:

2026-09-11 superseding execution state: saved-parameter replay passed and the
prespecified controls are complete. ROA-FULL's complexity criterion and the
subsequent minimal-fusion advancement criterion both failed. No final candidate
is cleared. Follow P0_3_RESEARCH_DECISION.md for the bounded research reassessment;
the earlier candidate rationale below is historical, not permission to ignore
these results or start confirmation.

Historical pre-control decision: keep ROA-FULL as the sole candidate pending contribution controls and final
confirmation. Its label is GBV_AUGMENTED_ONLY. Do not resume risk-gate, dual-head,
MILP or sibling searches without a new Research Lead design. Preserve V2's
failed primary comparison. The shortest credible next step uses cached scores.

Current overall status: **NOT READY**.
